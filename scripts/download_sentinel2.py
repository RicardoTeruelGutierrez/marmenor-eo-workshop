"""
Download real Sentinel-2 imagery for the Mar Menor workshop
============================================================

Pulls Sentinel-2 L2A bands from the public AWS Open-Data COG mirror (no
credentials needed) and saves them to ../data/ as Cloud-Optimised GeoTIFFs
cropped to the Mar Menor on a common WGS84 grid.

Quick examples
--------------
    # Default: the four workshop scenes used by Module 1 Section C
    python scripts/download_sentinel2.py

    # Every clear scene in a date range (great for time-series work)
    python scripts/download_sentinel2.py --range 2022-06-01:2022-09-30

    # The nearest clear scene to a target date
    python scripts/download_sentinel2.py --date 2024-08-15

    # A whole month of clear scenes
    python scripts/download_sentinel2.py --month 2023-08

    # Only TCI + the red-edge bands, very-low cloud
    python scripts/download_sentinel2.py --range 2022-06-01:2022-08-31 \\
        --bands TCI,B04,B05 --max-cloud 5

File naming
-----------
- Workshop default mode (no args):  s2_{baseline|bloom|peak|recovery}_{band}.tif
- Date/range/month modes:           s2_YYYY-MM-DD_{band}.tif

Why no credentials?
-------------------
Sentinel-2 L2A is mirrored on AWS Open Data and searchable via the public
Earth Search STAC catalogue — both anonymous. For server-side processing
(C2RCC, on-demand products) you need a free Copernicus account; see
Notebook 3 §1.5.
"""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.crs import CRS

# ── Constants ───────────────────────────────────────────────────────────
DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)

# Public AWS Open-Data COG mirror + public STAC search (anonymous)
BASE_COG = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs"
STAC_URL = "https://earth-search.aws.element84.com/v1/search"
STAC_COLLECTION = "sentinel-2-l2a"

# Mar Menor MGRS tile + AOI bbox (WGS84)
TILE = "30SXG"
BBOX = (-0.882, 37.598, -0.700, 37.812)

# Common WGS84 output grid — every file shares this exact extent and size,
# so any two scenes are pixel-aligned and stack-able with no resampling.
DST_CRS = CRS.from_epsg(4326)
OUT_W, OUT_H = 1800, 2140
DST_TRANSFORM = from_bounds(BBOX[0], BBOX[1], BBOX[2], BBOX[3], OUT_W, OUT_H)

# Workshop reference scenes (4 cloud-free, full-coverage; ground truth for Module 1)
WORKSHOP_SCENES = {
    "baseline": ("30/S/XG/2020/2/S2A_30SXG_20200210_0_L2A", "2020-02-10"),
    "bloom":    ("30/S/XG/2021/8/S2B_30SXG_20210818_0_L2A", "2021-08-18"),
    "peak":     ("30/S/XG/2021/9/S2A_30SXG_20210912_0_L2A", "2021-09-12"),
    "recovery": ("30/S/XG/2022/3/S2A_30SXG_20220301_0_L2A", "2022-03-01"),
}

ALL_BANDS = ["TCI", "B02", "B03", "B04", "B05", "B08"]


# ── Core operations ─────────────────────────────────────────────────────
def fetch(tile_path: str, asset: str, label: str) -> Path | None:
    """Read one asset COG, reproject the AOI window onto the common grid, save.

    Returns the output path on success, or None if the asset failed.
    """
    if asset == "TCI":
        n_bands, dtype = 3, "uint8"
    else:
        n_bands, dtype = 1, "uint16"
    url = f"{BASE_COG}/{tile_path}/{asset}.tif"
    out = DATA / f"s2_{label}_{asset}.tif"
    try:
        with rasterio.open(url) as src:
            arr = np.zeros((n_bands, OUT_H, OUT_W), dtype=dtype)
            for i in range(1, n_bands + 1):
                reproject(
                    rasterio.band(src, i), arr[i - 1],
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=DST_TRANSFORM, dst_crs=DST_CRS,
                    resampling=Resampling.bilinear,
                )
            profile = dict(driver="GTiff", dtype=dtype, count=n_bands,
                           width=OUT_W, height=OUT_H, crs=DST_CRS,
                           transform=DST_TRANSFORM, nodata=0, compress="deflate")
            with rasterio.open(out, "w", **profile) as dst:
                dst.write(arr)
    except Exception as e:
        print(f"    [fail] {out.name}: {e}")
        return None
    print(f"    {out.name:32s} {out.stat().st_size // 1024:6d} KB")
    return out


def search_clear_scenes(start: str, end: str, max_cloud: float = 15.0):
    """Find scenes over the Mar Menor tile in [start, end] with cloud < max_cloud.

    Uses Earth Search STAC v1 (RFC3339 datetimes required).
    Returns a list of (tile_path, date_iso) pairs ordered chronologically.
    """
    body = {
        "collections": [STAC_COLLECTION],
        "bbox": list(BBOX),
        "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
        "limit": 100,
    }
    r = requests.post(STAC_URL, json=body, timeout=30)
    r.raise_for_status()
    out, seen = [], set()
    for f in r.json().get("features", []):
        sid = f["id"]
        if TILE not in sid:                       # restrict to our MGRS tile
            continue
        date = f["properties"]["datetime"][:10]
        if date in seen:                          # one scene per date is enough
            continue
        seen.add(date)
        # Derive the COG tile path from the visual asset href.
        # Example href: .../sentinel-s2-l2a-cogs/30/S/XG/2024/9/<sid>/TCI.tif
        href = f["assets"]["visual"]["href"]
        tile_path = href.split("sentinel-s2-l2a-cogs/")[1].rsplit("/", 1)[0]
        out.append((tile_path, date))
    out.sort(key=lambda x: x[1])
    return out


def extract_lagoon_contour() -> None:
    """Derive the lagoon outline from the peak-scene NIR band (water absorbs NIR)."""
    peak_b08 = DATA / "s2_peak_B08.tif"
    if not peak_b08.exists():
        return                                         # not in workshop default mode
    try:
        from scipy.ndimage import (binary_fill_holes, binary_erosion,
                                   binary_dilation)
        from skimage import measure
        from rdp import rdp
    except ImportError:
        print("  [skip] contour extraction needs scikit-image + rdp")
        return
    with rasterio.open(peak_b08) as src:
        b08 = src.read(1).astype(float)
        transform = src.transform
    water = (b08 > 0) & (b08 < 400)                    # low NIR = water
    water = binary_fill_holes(water)
    water = binary_erosion(water, iterations=2)
    water = binary_dilation(water, iterations=2)
    labeled = measure.label(water)
    main = max(measure.regionprops(labeled), key=lambda r: r.area)
    contour = max(measure.find_contours((labeled == main.label).astype(float), 0.5),
                  key=len)
    lonlat = np.array([(transform.c + c * transform.a, transform.f + r * transform.e)
                       for r, c in contour])
    np.save(DATA / "lagoon_contour_wgs84.npy", rdp(lonlat, epsilon=0.0005))
    print(f"  lagoon_contour_wgs84.npy   {len(np.load(DATA / 'lagoon_contour_wgs84.npy'))} vertices")


# ── Mode handlers ───────────────────────────────────────────────────────
def mode_workshop(bands):
    """Default: the four reference scenes used by Module 1 Section C."""
    print(f"Workshop mode: {len(WORKSHOP_SCENES)} reference scenes, "
          f"bands = {','.join(bands)}")
    for label, (tile_path, date) in WORKSHOP_SCENES.items():
        print(f"  [{label}]  {date}")
        for b in bands:
            fetch(tile_path, b, label)
    print("Extracting lagoon outline from NIR...")
    extract_lagoon_contour()


def mode_scenes(scenes, bands):
    """Generic mode: download a list of (tile_path, date) scenes."""
    if not scenes:
        print("No scenes matched the request (try widening --max-cloud or the range).")
        return
    print(f"Found {len(scenes)} clear scenes; downloading {len(bands)} bands each:")
    for tile_path, date in scenes:
        print(f"  [{date}]")
        for b in bands:
            fetch(tile_path, b, date)


# ── CLI ─────────────────────────────────────────────────────────────────
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Download real Sentinel-2 L2A imagery over the Mar Menor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Quick examples")[1].split("File naming")[0])
    g = p.add_mutually_exclusive_group()
    g.add_argument("--range", metavar="START:END",
                   help="Date range, e.g. 2022-06-01:2022-09-30")
    g.add_argument("--date", metavar="YYYY-MM-DD",
                   help="Nearest clear scene to this date")
    g.add_argument("--month", metavar="YYYY-MM",
                   help="All clear scenes in a calendar month")
    p.add_argument("--max-cloud", type=float, default=15.0,
                   help="Max %% cloud cover (default: 15)")
    p.add_argument("--bands", default="TCI,B02,B03,B04,B05,B08",
                   help="Comma-separated band list, or 'all' "
                        "(default: TCI,B02,B03,B04,B05,B08)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    bands = ALL_BANDS if args.bands == "all" else [b.strip() for b in args.bands.split(",")]
    for b in bands:
        if b not in ALL_BANDS:
            print(f"Unknown band: {b}. Allowed: {', '.join(ALL_BANDS)}")
            sys.exit(1)

    if args.range:
        start, end = args.range.split(":")
        scenes = search_clear_scenes(start, end, args.max_cloud)
        mode_scenes(scenes, bands)
    elif args.month:
        y, m = map(int, args.month.split("-"))
        start = f"{y:04d}-{m:02d}-01"
        end_dt = (datetime(y, m, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        scenes = search_clear_scenes(start, end_dt.strftime("%Y-%m-%d"), args.max_cloud)
        mode_scenes(scenes, bands)
    elif args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d")
        win = timedelta(days=15)
        scenes = search_clear_scenes(
            (target - win).strftime("%Y-%m-%d"),
            (target + win).strftime("%Y-%m-%d"),
            args.max_cloud)
        if not scenes:
            print("No clear scene within ±15 days; try a higher --max-cloud.")
            return
        scenes.sort(key=lambda s: abs((datetime.strptime(s[1], "%Y-%m-%d") - target).days))
        mode_scenes(scenes[:1], bands)
    else:
        mode_workshop(bands)

    print("Done. Files in", DATA)


if __name__ == "__main__":
    main()
