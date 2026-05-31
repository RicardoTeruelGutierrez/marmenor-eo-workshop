"""
Download real Sentinel-2 imagery for the Mar Menor workshop (Module 1, Section C)
=================================================================================

This script fetches four cloud-free Sentinel-2 L2A scenes over the Mar Menor and
writes them to ``../data/`` as Cloud-Optimised-GeoTIFF crops on a common WGS84
grid, plus a lagoon outline extracted from the near-infrared band.

Why a separate script (not generate_datasets.py)?
  - generate_datasets.py builds the *synthetic* teaching datasets (Sections A/B).
    Those run with no network and no credentials.
  - This script downloads *real* satellite pixels (Section C, "instructor"
    figures). It needs internet but NO credentials: the data come from the
    public AWS Open-Data COG mirror of Sentinel-2 L2A.

Outputs written to ../data/:
  - s2_<scene>_TCI.tif                 True-Colour 3-band composite (uint8)
  - s2_<scene>_{B02,B03,B04,B05,B08}.tif   individual bands (uint16)
  - lagoon_contour_wgs84.npy           lagoon outline (Nx2 lon/lat), from NIR

  where <scene> in {baseline, bloom, peak, recovery}.

Usage:
    python scripts/download_sentinel2.py

Notes on scene selection:
  We measured, *over the lagoon water only*, both the valid coverage (was the
  AOI fully imaged or only clipped by a swath edge?) and the real cloud fraction.
  The four scenes below were chosen as full-coverage and clear; e.g. 2021-07-14
  was rejected (only 5.5 % coverage, a swath edge) despite a low nominal cloud %.
"""
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.crs import CRS

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)

# Public AWS Open-Data COG mirror of Sentinel-2 L2A (anonymous, no credentials)
BASE = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs"

# Validated full-coverage, clear scenes over the Mar Menor (MGRS tile 30SXG)
SCENES = {
    "baseline": "30/S/XG/2020/2/S2A_30SXG_20200210_0_L2A",   # 10 Feb 2020 — clear winter baseline
    "bloom":    "30/S/XG/2021/8/S2B_30SXG_20210818_0_L2A",   # 18 Aug 2021 — bloom onset, 100% cover
    "peak":     "30/S/XG/2021/9/S2A_30SXG_20210912_0_L2A",   # 12 Sep 2021 — crisis peak, 0% cloud
    "recovery": "30/S/XG/2022/3/S2A_30SXG_20220301_0_L2A",   # 01 Mar 2022 — partial recovery
}
BANDS = ["B02", "B03", "B04", "B05", "B08"]

# Common WGS84 output grid (every file shares this exact extent + size)
DST_CRS = CRS.from_epsg(4326)
W, E, S, N = -0.882, -0.700, 37.598, 37.812
OUT_W, OUT_H = 1800, 2140
DST_TRANSFORM = from_bounds(W, S, E, N, OUT_W, OUT_H)


def fetch(tile, asset, label, n_bands=1, dtype="uint16"):
    """Read an asset COG, reproject the AOI window onto the common grid, save."""
    url = f"{BASE}/{tile}/{asset}.tif"
    out = DATA / f"s2_{label}_{asset}.tif"
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
    print(f"    {out.name:28s} {out.stat().st_size // 1024:6d} KB")


def extract_lagoon_contour():
    """Derive the lagoon outline from the peak-scene NIR band (water absorbs NIR)."""
    try:
        from scipy.ndimage import binary_fill_holes, binary_erosion, binary_dilation
        from skimage import measure
        from rdp import rdp
    except ImportError:
        print("  [skip] contour extraction needs scikit-image + rdp "
              "(pip install scikit-image rdp)")
        return
    with rasterio.open(DATA / "s2_peak_B08.tif") as src:
        b08 = src.read(1).astype(float)
        transform = src.transform
    water = (b08 > 0) & (b08 < 400)          # low NIR = water
    water = binary_fill_holes(water)
    water = binary_erosion(water, iterations=2)
    water = binary_dilation(water, iterations=2)
    labeled = measure.label(water)
    regions = measure.regionprops(labeled)
    main = max(regions, key=lambda r: r.area)
    mask = labeled == main.label
    contour = max(measure.find_contours(mask.astype(float), 0.5), key=len)
    lonlat = np.array([(transform.c + c * transform.a, transform.f + r * transform.e)
                       for r, c in contour])
    simplified = rdp(lonlat, epsilon=0.0005)
    np.save(DATA / "lagoon_contour_wgs84.npy", simplified)
    print(f"  lagoon_contour_wgs84.npy   {len(simplified)} vertices")


def main():
    print("Downloading real Sentinel-2 scenes (public AWS COG mirror, no login)...")
    for label, tile in SCENES.items():
        print(f"  [{label}]  {tile.split('/')[-1]}")
        fetch(tile, "TCI", label, n_bands=3, dtype="uint8")
        for b in BANDS:
            fetch(tile, b, label, n_bands=1, dtype="uint16")
    print("Extracting lagoon outline from NIR...")
    extract_lagoon_contour()
    print("Done. Real-imagery files written to", DATA)


if __name__ == "__main__":
    main()
