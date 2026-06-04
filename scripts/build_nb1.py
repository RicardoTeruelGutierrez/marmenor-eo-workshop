"""Build notebook 01: Satellite data extraction (Sentinel-2 + Sentinel-3).

Structure (see item 11 of the review):
  Section A — synthetic / cached data, fully reproducible offline in class
  Section B — optional real-data workflow against CDSE / STAC
  Section C — instructor figures from real Sentinel-2 GeoTIFFs (needs download)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from nb_builder import Notebook

OUT = ROOT.parent / "notebooks" / "01_satellite_data_extraction.ipynb"

nb = Notebook()

# ===========================================================================
# HEADER
# ===========================================================================
nb.md(r"""# Module 1 — Satellite Data Extraction for the Mar Menor

**Earth-Observation Workshop · Mar Menor coastal lagoon (Murcia, Spain) · NYU PhD**
*Duration: ~75 min*

---

## Learning objectives

By the end of this module you will be able to:

1. Authenticate against the **Copernicus Data Space Ecosystem (CDSE)** and query the Sentinel catalogue programmatically (Section B).
2. Tell apart Sentinel-2 **L1C** (top-of-atmosphere) from **L2A** (surface reflectance), and know why this matters in coastal waters.
3. Derive **chlorophyll-a** proxies (NDCI, B05/B04) from Sentinel-2 red-edge bands.
4. Work with the **Sea-Surface-Temperature (SST)** cube from Sentinel-3 SLSTR and connect a marine heatwave to the dissolved-oxygen collapse.
5. Read and visualise real Sentinel-2 imagery so the lagoon outline is pixel-perfect (Section C).

## How this notebook is organised

Open the **Table of contents** (the ☰ icon, top-left in Colab / Jupyter) to jump between parts.

| Section | Content | Needs internet? |
|---------|---------|-----------------|
| **A — Synthetic cached data** | Reproducible classroom analysis from `data/` (12-point chl-a series, SST cube). | No |
| **B — Real-data workflow (CDSE/STAC)** | The patterns to query and download real Sentinel data. Shown, not executed in class. | (Yes, with a free account) |
| **C — Instructor figures (real GeoTIFFs)** | True-Colour / NDCI / zone maps from real Sentinel-2 scenes. | Yes (one-off download) |

## Glossary of local terms (ES → EN)

| Spanish | English / meaning |
|---------|-------------------|
| **Mar Menor** | "Lesser Sea" — Europe's largest hypersaline coastal lagoon (~135 km²) |
| **La Manga** | the 22 km sand bar separating the lagoon from the Mediterranean |
| **El Estacio / Las Encañizadas** | the narrow inlets connecting lagoon and open sea |
| **Campo de Cartagena** | the intensive-agriculture watershed NW of the lagoon (nitrate source) |
| **DANA** (*Depresión Aislada en Niveles Altos*) | cut-off cold drop — extreme convective rainfall over SE Spain |
""")

# ---------------------------------------------------------------------------
# HOW TO RUN + COLAB BOOTSTRAP
# ---------------------------------------------------------------------------
nb.md(r"""---
## ▶️ How to run this notebook

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RicardoTeruelGutierrez/marmenor-eo-workshop/blob/main/notebooks/01_satellite_data_extraction.ipynb)

1. **In Colab:** click the badge above, then **Runtime → Run all**. The first cell installs everything (~30 s). That's it.
2. **On your laptop:** `pip install -r requirements.txt`, then run the cells top to bottom.
3. **Run the cells in order** — each one builds on the previous.
4. **What you need:** nothing for Sections A & C; a free CDSE account only for the live parts of Section B.

**Cell labels you'll see in this notebook:**

| Label | Meaning |
|-------|---------|
| 🟢 **RUN** | Just run it — produces a figure or result. |
| ✏️ **EDIT** | Change a value (a date, your credentials) before running. |
| ⏭️ **OPTIONAL** | Pattern/reference — safe to skip; won't break later cells. |

*Run the bootstrap cell below first (it does nothing on a local install).*
""")

nb.code(r'''# Colab bootstrap (no-op on a local install)
import sys, os
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB and not os.path.exists("/content/workshop"):
    print("Running in Colab - bootstrapping (~30s)...")
    !git clone -q https://github.com/RicardoTeruelGutierrez/marmenor-eo-workshop.git /content/workshop
    !pip install -q -r /content/workshop/requirements.txt
    !python /content/workshop/scripts/generate_datasets.py
if IN_COLAB:
    %cd /content/workshop/notebooks
    print("Ready - run the cells below.")
''')

nb.code(r'''# Colab bootstrap (no-op on a local install)
import sys, os
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB and not os.path.exists("/content/workshop"):
    print("Running in Colab - bootstrapping (~30s)...")
    !git clone -q https://github.com/RicardoTeruelGutierrez/marmenor-eo-workshop.git /content/workshop
    !pip install -q -r /content/workshop/requirements.txt
    !python /content/workshop/scripts/generate_datasets.py
if IN_COLAB:
    %cd /content/workshop/notebooks
    print("Ready - run the cells below.")
''')

# ---------------------------------------------------------------------------
# SETUP + DEPENDENCY CHECK (item 4)
# ---------------------------------------------------------------------------
nb.md(r"""---
## Setup

Run this cell first. It checks dependencies, loads colour maps and defines the
study area and the lagoon outline. The outline is loaded from
`lagoon_contour_wgs84.npy` if present (extracted from a real Sentinel-2 NIR band
by `scripts/download_sentinel2.py`); otherwise a hand-digitised fallback polygon
is used so Sections A and B still work with no downloaded imagery.
""")

nb.code(r'''# ── Dependency check (fail early with a clear message) ────────────────────
import importlib.util
_required = ["numpy", "pandas", "pyarrow", "xarray", "matplotlib", "scipy"]
_missing  = [p for p in _required if importlib.util.find_spec(p) is None]
if _missing:
    raise ImportError(
        "Missing packages: " + ", ".join(_missing) +
        "\nRun:  pip install -r requirements.txt"
    )

import warnings, json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.path import Path as MplPath
from scipy.interpolate import RBFInterpolator

# Optional niceties
try:
    import cmocean.cm as cmo
    HAS_CMOCEAN = True
except ImportError:
    HAS_CMOCEAN = False
try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

warnings.filterwarnings("ignore")
plt.rcParams.update({
    "figure.dpi": 130, "axes.grid": False, "font.family": "sans-serif",
    "axes.spines.top": False, "axes.spines.right": False,
})

DATA = Path("../data").resolve()
assert DATA.exists(), f"Data folder not found: {DATA}"

# Area of interest (WGS84) — matches the common grid of the real GeoTIFFs
AOI = dict(lon_min=-0.882, lon_max=-0.700, lat_min=37.598, lat_max=37.812)
S2_EXT = [AOI["lon_min"], AOI["lon_max"], AOI["lat_min"], AOI["lat_max"]]

# ── Lagoon outline: real NIR-derived contour, with a fallback ─────────────
_contour = DATA / "lagoon_contour_wgs84.npy"
if _contour.exists():
    LAGOON_POLY = np.load(_contour)
    _src = f"real Sentinel-2 NIR contour ({len(LAGOON_POLY)} vertices)"
else:
    # Hand-digitised fallback (~50 vertices) so Sections A/B work offline
    LAGOON_POLY = np.array([
        [-0.856, 37.808], [-0.847, 37.810], [-0.834, 37.810], [-0.821, 37.809],
        [-0.808, 37.807], [-0.795, 37.803], [-0.782, 37.800], [-0.770, 37.799],
        [-0.758, 37.796], [-0.748, 37.791], [-0.737, 37.784], [-0.727, 37.775],
        [-0.719, 37.764], [-0.714, 37.752], [-0.710, 37.739], [-0.708, 37.726],
        [-0.707, 37.712], [-0.708, 37.698], [-0.710, 37.684], [-0.713, 37.671],
        [-0.716, 37.658], [-0.719, 37.646], [-0.720, 37.635], [-0.721, 37.624],
        [-0.721, 37.616], [-0.724, 37.612], [-0.732, 37.610], [-0.742, 37.610],
        [-0.753, 37.612], [-0.763, 37.615], [-0.773, 37.618], [-0.784, 37.623],
        [-0.795, 37.628], [-0.807, 37.634], [-0.819, 37.640], [-0.830, 37.647],
        [-0.840, 37.653], [-0.849, 37.660], [-0.856, 37.668], [-0.860, 37.676],
        [-0.862, 37.686], [-0.862, 37.697], [-0.860, 37.709], [-0.859, 37.722],
        [-0.859, 37.735], [-0.858, 37.748], [-0.858, 37.760], [-0.857, 37.772],
        [-0.857, 37.783], [-0.857, 37.794], [-0.856, 37.808],
    ])
    _src = f"hand-digitised fallback ({len(LAGOON_POLY)} vertices)"

CMAP_CHLA = cmo.algae if HAS_CMOCEAN else plt.cm.YlGn
CMAP_ANOM = cmo.balance if HAS_CMOCEAN else plt.cm.RdBu_r
CMAP_SST  = cmo.thermal if HAS_CMOCEAN else plt.cm.inferno

print("Setup complete.")
print(f"  cmocean   : {'yes' if HAS_CMOCEAN else 'no (using matplotlib maps)'}")
print(f"  rasterio  : {'yes' if HAS_RASTERIO else 'no (Section C disabled)'}")
print(f"  Lagoon    : {_src}")
''')

# ---------------------------------------------------------------------------
# SANITY CHECK (item 10)
# ---------------------------------------------------------------------------
nb.md(r"""### Data sanity check

Before anything else, confirm the synthetic datasets are present. If this cell
raises, run `python scripts/generate_datasets.py` (or copy the `data/` folder).
""")

nb.code(r'''EXPECTED = [
    "stations.csv",
    "insitu_buoys_2016_2025.parquet",
    "s2_sampling_points.csv",
    "sentinel2_waterquality.parquet",
    "sentinel3_sst_cube.nc",
    "watershed_forcing.csv",
]
missing = [f for f in EXPECTED if not (DATA / f).exists()]
if missing:
    raise FileNotFoundError(
        "Missing required data files:\n  " + "\n  ".join(missing) +
        "\nRun:  python scripts/generate_datasets.py"
    )
print("All required (synthetic) files found.")

# Real Sentinel-2 GeoTIFFs are optional (Section C only)
_real = list(DATA.glob("s2_*_TCI.tif"))
REAL_IMAGES_AVAILABLE = HAS_RASTERIO and len(_real) >= 4
print(f"Real Sentinel-2 imagery for Section C: "
      f"{'available' if REAL_IMAGES_AVAILABLE else 'NOT downloaded'}")
if not REAL_IMAGES_AVAILABLE:
    print("  -> to enable Section C: python scripts/download_sentinel2.py")
''')

# ===========================================================================
# SECTION A — SYNTHETIC CACHED DATA
# ===========================================================================
nb.md(r"""---
## SECTION A — Synthetic cached data (reproducible in class)

Everything in Section A runs **offline** from `data/`. The datasets are
*synthetic*, generated by `scripts/generate_datasets.py` with statistics
calibrated against the published Mar Menor literature (Soriano-González et al.
2022; Sola et al. 2023; Pedrera et al. 2024). The documented crises (2016, 2019,
2021, 2025) appear in the right months with realistic magnitudes. **They are for
teaching only — not real measurements.**

### A.1 Why standard ocean-colour algorithms fail here (Case-2 waters)

Open-ocean (**Case-1**) algorithms such as OC4/OC3M assume phytoplankton
dominates optical variability. The Mar Menor breaks that assumption:

- **Suspended sediment** (max depth 7 m, wind-stirred) raises blue/green reflectance → OC4 over-estimates chl-a
- **CDOM** (coloured dissolved organics from agricultural runoff) absorbs in the blue
- **Macrophytes** (*Cymodocea*, *Caulerpa*) cover the bottom and add NIR signal

The operational fix is the **C2RCC** atmospheric correction (Case-2 Regional
Coast Color; Brockmann et al. 2016), a neural net trained on Case-2 water that
estimates remote-sensing reflectance (*Rrs*) robust to these confounders. On top
of *Rrs* one applies a locally-calibrated index. The most-used one for the
lagoon (Soriano-González et al. 2022):

$$\text{Chl-}a \;\propto\; \frac{R_{rs}(B05)}{R_{rs}(B04)} = \frac{R_{rs}(705\,\text{nm})}{R_{rs}(665\,\text{nm})}$$

Physically: chlorophyll *absorbs* in the red (B04) and *reflects* in the
red-edge (B05), so the ratio grows with concentration.

> **Important caveat (do not over-claim).** The cached values below are
> *synthetic* and merely *imitate* a C2RCC-style *Rrs* product. In a real
> pipeline, Sentinel-2 **L2A / Sen2Cor** surface reflectance is a *land*
> atmospheric correction and must **not** be confused with an aquatic C2RCC
> correction. For quantitative water work you would run C2RCC (e.g. in SNAP or
> via the Sentinel Hub evalscript) rather than use L2A directly.

### A.2 Load the pre-processed Sentinel-2 water-quality table
""")

nb.code(r'''s2 = pd.read_parquet(DATA / "sentinel2_waterquality.parquet").assign(
    date=lambda d: pd.to_datetime(d["date"])
)
points = pd.read_csv(DATA / "s2_sampling_points.csv")

print(f"{len(s2):,} cloud-free Sentinel-2 observations")
print(f"  Sampling points : {s2.point_id.nunique()}")
print(f"  Period          : {s2.date.min():%Y-%m-%d}  ->  {s2.date.max():%Y-%m-%d}")
s2.head(3)
''')

nb.md(r"""**Column dictionary**

| Column | Units | Description |
|--------|-------|-------------|
| `date` | — | Sentinel-2 acquisition date (cloud-free) |
| `point_id` | — | Sampling-point ID (S2_P01 … S2_P12) |
| `chla_mg_m3` | mg/m³ | Chl-a from the calibrated B05/B04 index |
| `turbidity_FNU` | FNU | Turbidity (nephelometric) |
| `Rrs_B03/B04/B05` | sr⁻¹ | Remote-sensing reflectance (green / red / red-edge) |

#### A.3 Lagoon-wide chlorophyll time series

We average the 12 points to a lagoon-wide weekly mean and overlay the documented crises.
""")

nb.code(r'''weekly = (s2.set_index("date")["chla_mg_m3"]
            .resample("W").mean()
            .rolling(4, min_periods=1).mean())

fig, ax = plt.subplots(figsize=(13, 4))
ax.fill_between(weekly.index, weekly.values, alpha=0.35, color="#2a9d8f")
ax.plot(weekly.index, weekly.values, color="#264653", lw=1.2)

crises = [
    ("2016 crisis (nutrients)",  "2016-05-01", "2016-09-30", "#e76f51"),
    ("2019 DANA (runoff)",       "2019-09-10", "2019-11-15", "#f4a261"),
    ("2021 anoxia (fish-kill)",  "2021-07-15", "2021-10-15", "#e63946"),
    ("2025 resurgence",          "2025-06-01", "2025-09-30", "#9d4edd"),
]
for name, s, e, c in crises:
    ax.axvspan(s, e, color=c, alpha=0.20, label=name)

ax.set(title="Lagoon-mean chlorophyll-a - Sentinel-2 (calibrated synthetic data)",
       ylabel="Chl-a (mg m$^{-3}$)")
ax.legend(loc="upper left", fontsize=8, ncol=2)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.tight_layout()
plt.show()

for name, s, e, c in crises:
    v = s2.query(f"'{s}' <= date <= '{e}'")["chla_mg_m3"]
    print(f"{name[:24]:24s}  median={v.median():.1f}  max={v.max():.1f} mg/m3")
''')

# --- A.4 SST cube ---------------------------------------------------------
nb.md(r"""### A.4 Sentinel-3 SLSTR — Sea-Surface Temperature

Sentinel-3 carries **OLCI** (300 m ocean colour) and **SLSTR** (1 km SST). The
cached cube `sentinel3_sst_cube.nc` holds a daily lagoon SST field (2017–2025).
""")

nb.code(r'''ds = xr.open_dataset(DATA / "sentinel3_sst_cube.nc")
print(ds)
print("\nCloud-free days:", int(ds.sst.notnull().any(dim=("lat", "lon")).sum()))
''')

nb.md(r"""#### A.5 Day-of-year climatology and inter-annual anomaly

The classic EO anomaly approach: build a **day-of-year climatology** (mean over
all years for each day 1–365) and subtract it. What remains is the *anomaly*.
""")

nb.code(r'''sst_lagoon = ds.sst.mean(dim=("lat", "lon"), skipna=True)
df_sst = sst_lagoon.to_dataframe(name="sst").dropna().reset_index()
df_sst["doy"] = df_sst["time"].dt.dayofyear

clim = df_sst.groupby("doy")["sst"].agg(["mean", "std"])
df_sst = df_sst.join(clim, on="doy", rsuffix="_clim")
df_sst["anomaly"] = df_sst["sst"] - df_sst["mean"]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
ax1.plot(df_sst["time"], df_sst["sst"], color="#0077b6", lw=0.6,
         label="Lagoon-mean SST")
ax1.fill_between(df_sst["time"], df_sst["mean"] - df_sst["std"],
                 df_sst["mean"] + df_sst["std"], color="#caf0f8", alpha=0.6,
                 label="Climatology +/- 1 sigma")
ax1.plot(df_sst["time"], df_sst["mean"], color="#03045e", lw=0.9, ls="--",
         label="Day-of-year climatology")
ax1.axvspan("2021-07-15", "2021-10-15", color="#e63946", alpha=0.12,
            label="2021 anoxia event")
ax1.set_ylabel("SST (degC)"); ax1.legend(loc="upper left", fontsize=8, ncol=2)
ax1.set_title("Sentinel-3 SLSTR - Mar Menor lagoon-mean SST")

colors = np.where(df_sst["anomaly"] > 0, "#d62828", "#0077b6")
ax2.bar(df_sst["time"], df_sst["anomaly"], color=colors, width=2)
ax2.axhline(0, color="k", lw=0.7)
ax2.set_ylabel("Anomaly (degC)"); ax2.set_xlabel("Year")
fig.tight_layout(); plt.show()

aug = df_sst.query("'2021-07-01' <= time <= '2021-10-15'")
print(f"Mean anomaly Jul-Oct 2021 : +{aug['anomaly'].mean():.2f} degC")
print(f"Max anomaly               : +{aug['anomaly'].max():.2f} degC")
''')

nb.md(r"""#### A.6 The August-2021 marine heatwave and the oxygen connection

The 2021 marine heatwave was a trigger of the fish-kill. The mechanism is direct
and quantifiable:

$$\text{warmer water} \;\longrightarrow\; \text{less dissolved O}_2 \text{ at saturation} \;\longrightarrow\; \text{bottom hypoxia}$$

We show (1) the SST field clipped to the **real lagoon outline**, (2) its
anomaly, and (3) the **physical O₂-solubility curve** (Benson & Krause): how the
jump from ~27.5 °C (normal year) to ~30.5 °C (2021) cuts the oxygen the water can
hold, just as the bloom consumes it at night.
""")

nb.code(r'''# Fields, clipped to the REAL lagoon outline (no pixels spilling outside)
heat21   = ds.sst.sel(time=slice("2021-08-01", "2021-08-31")).mean("time")
clim_aug = ds.sst.sel(time=ds["time"].dt.month == 8).mean("time")
anom_fld = heat21 - clim_aug

slon, slat = np.meshgrid(ds.lon.values, ds.lat.values)
sst_mask = MplPath(LAGOON_POLY).contains_points(
    np.column_stack([slon.ravel(), slat.ravel()])).reshape(slon.shape)
def clip(field):
    return np.ma.array(field.values, mask=~sst_mask)

ext_sst = [float(ds.lon.min()), float(ds.lon.max()),
           float(ds.lat.min()), float(ds.lat.max())]

fig = plt.figure(figsize=(19, 7), dpi=140)
fig.patch.set_facecolor("#0d1b2a")
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.1], wspace=0.22)
fx = [pe.withStroke(linewidth=2.5, foreground="black")]

ax0 = fig.add_subplot(gs[0]); ax0.set_facecolor("#0d1b2a")
im0 = ax0.imshow(clip(heat21), extent=ext_sst, origin="lower", cmap=CMAP_SST,
                 vmin=28.5, vmax=31.5, aspect="equal", interpolation="bilinear")
ax1 = fig.add_subplot(gs[1]); ax1.set_facecolor("#0d1b2a")
im1 = ax1.imshow(clip(anom_fld), extent=ext_sst, origin="lower", cmap=CMAP_ANOM,
                 vmin=-2.6, vmax=2.6, aspect="equal", interpolation="bilinear")
for ax, im, lab, title in [(ax0, im0, "SST (degC)", "Mean SST - Aug 2021"),
                           (ax1, im1, "Anomaly (degC)", "Anomaly vs 2017-2025")]:
    ax.add_patch(mpatches.Polygon(LAGOON_POLY, closed=True, facecolor="none",
                 edgecolor="white", linewidth=1.4, alpha=0.7))
    ax.set_xlim(ext_sst[0], ext_sst[1]); ax.set_ylim(ext_sst[2], ext_sst[3])
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_edgecolor("#80d4ff")
    ax.set_title(title, color="white", fontsize=11, path_effects=fx)
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(lab, color="white", fontsize=10)
    plt.setp(cb.ax.yaxis.get_ticklabels(), color="white", fontsize=9)
    cb.outline.set_edgecolor("white")

def o2_sat(T, S=37.0):
    """O2 saturation (mg/L) - Benson & Krause approximation for seawater."""
    Tk = T + 273.15
    lnC = (-139.34411 + 1.575701e5/Tk - 6.642308e7/Tk**2
           + 1.243800e10/Tk**3 - 8.621949e11/Tk**4
           - S*(0.017674 - 10.754/Tk + 2140.7/Tk**2))
    return np.exp(lnC)

ax2 = fig.add_subplot(gs[2]); ax2.set_facecolor("#0d1b2a")
T = np.linspace(24, 33, 200)
ax2.plot(T, o2_sat(T), color="#48cae4", lw=2.5)
for Tp, yr, col in [(27.46, "Aug 2020", "#90e0ef"), (30.50, "Aug 2021", "#e63946")]:
    o2 = o2_sat(Tp)
    ax2.plot([Tp, Tp], [0, o2], color=col, ls="--", lw=1.5)
    ax2.plot([24, Tp], [o2, o2], color=col, ls="--", lw=1.5)
    ax2.scatter([Tp], [o2], color=col, s=80, zorder=5, edgecolor="white")
    ax2.annotate(f"{yr}\n{Tp:.1f} degC -> {o2:.2f} mg/L", (Tp, o2),
                 xytext=(Tp-3.2, o2+0.18), color=col, fontsize=9.5,
                 fontweight="bold", path_effects=fx)
drop = o2_sat(27.46) - o2_sat(30.50)
ax2.set_xlabel("Water temperature (degC)", color="white", fontsize=10)
ax2.set_ylabel("O$_2$ at saturation (mg/L)", color="white", fontsize=10)
ax2.set_title(f"Less O$_2$ as it warms\n(-{drop:.2f} mg/L from 2020 to 2021)",
              color="white", fontsize=11, path_effects=fx)
ax2.tick_params(colors="white"); ax2.grid(alpha=0.15); ax2.set_xlim(24, 33)
for sp in ax2.spines.values(): sp.set_edgecolor("#80d4ff")

fig.suptitle("Marine heatwave and its oxygen effect - Sentinel-3 SLSTR + O$_2$ physics",
             color="white", fontsize=13, y=1.03)
plt.show()
print(f"Mean lagoon SST Aug 2021 : {float(heat21.mean()):.2f} degC")
print(f"Mean anomaly Aug 2021    : +{float(anom_fld.mean()):.2f} degC")
print(f"O2 saturation drop       : -{drop:.2f} mg/L (27.5 -> 30.5 degC)")
print("With the bloom consuming O2 at night, this loss is enough for bottom anoxia.")
''')

# ===========================================================================
# SECTION B — REAL-DATA WORKFLOW (CDSE / STAC)
# ===========================================================================
nb.md(r"""---
## SECTION B — Optional real-data workflow (CDSE / STAC)

> ⏭️ **OPTIONAL** — this whole section is reference patterns. Nothing here needs
> to run for the rest of the notebook; skim it now, use it for your own project.

This section shows **how** to find and download real Sentinel data. The code is
*shown as patterns*; we do not run the authenticated parts in class (credentials
are personal). Section C then works with images already downloaded by
`scripts/download_sentinel2.py`.

### B.1 The Copernicus Data Space Ecosystem

The EU/ESA **Copernicus** programme provides free, open Sentinel data. For the
Mar Menor the relevant missions are:

| Mission | Instrument | Resolution | Revisit | Main use |
|---------|-----------|------------|---------|----------|
| **Sentinel-2** A/B | MSI (13 bands, 443–2190 nm) | 10/20/60 m | ~5 days | Water quality, vegetation |
| **Sentinel-3** A/B | OLCI (21 bands) | 300 m | ~2 days | Ocean colour (synoptic) |
| **Sentinel-3** A/B | SLSTR (9 bands) | 0.5–1 km | ~1 day | Sea-surface temperature |

Since Nov 2023 the old *Open Access Hub* (`scihub.copernicus.eu`) is retired. The
current entry point is **CDSE**, with OData, STAC, Sentinel Hub and openEO APIs.

#### B.1.1 OAuth2 token handshake (pattern only — do not run in class)

```python
import requests

def cdse_token(username: str, password: str) -> str:
    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token",
        data={"client_id": "cdse-public", "grant_type": "password",
              "username": username, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]

# token = cdse_token(os.environ["CDSE_USER"], os.environ["CDSE_PASS"])
# headers = {"Authorization": f"Bearer {token}"}
```

### B.2 Catalogue search via OData

OData filters by collection, AOI polygon, date range and attributes
(`cloudCover`, `productType`). Product types: `S2MSI1C` (L1C / TOA) and
`S2MSI2A` (L2A / surface) — **use L2A** for water work.
""")

nb.code(r'''def build_odata_query(aoi, start, end, collection="SENTINEL-2",
                      product_type="S2MSI2A", max_cloud=20):
    """Build a CDSE OData catalogue query URL (no auth needed to *build* it)."""
    poly = (f"POLYGON(({aoi['lon_min']} {aoi['lat_min']},"
            f"{aoi['lon_max']} {aoi['lat_min']},"
            f"{aoi['lon_max']} {aoi['lat_max']},"
            f"{aoi['lon_min']} {aoi['lat_max']},"
            f"{aoi['lon_min']} {aoi['lat_min']}))")
    f = [f"Collection/Name eq '{collection}'",
         f"OData.CSC.Intersects(area=geography'SRID=4326;{poly}')",
         f"ContentDate/Start ge {start}T00:00:00.000Z",
         f"ContentDate/Start le {end}T23:59:59.999Z"]
    if product_type:
        f.append("Attributes/OData.CSC.StringAttribute/any("
                 f"d:d/Name eq 'productType' and d/Value eq '{product_type}')")
    if max_cloud is not None:
        f.append("Attributes/OData.CSC.DoubleAttribute/any("
                 f"d:d/Name eq 'cloudCover' and d/Value lt {max_cloud})")
    return ("https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
            f"$filter={' and '.join(f)}&$orderby=ContentDate/Start&$top=50")

print(build_odata_query(AOI, "2021-08-01", "2021-08-31")[:300], "...")
''')

nb.md(r"""### B.3 Catalogue search via STAC (recommended)

STAC (*SpatioTemporal Asset Catalog*) is the modern standard with mature Python
clients. **Prefer STAC for new code.**

> ⚠️ **Updated endpoint (Nov 2025).** The old `catalogue.dataspace.copernicus.eu/stac`
> was deprecated on 17 Nov 2025. The current CDSE STAC root is
> **`https://stac.dataspace.copernicus.eu/v1/`** and collections use lowercase
> IDs like **`sentinel-2-l2a`** (not `SENTINEL-2`).

```python
from pystac_client import Client

# Current CDSE STAC endpoint (v1)
cat = Client.open("https://stac.dataspace.copernicus.eu/v1/")

search = cat.search(
    collections=["sentinel-2-l2a"],           # lowercase collection ID
    datetime="2021-08-01/2021-08-31",
    bbox=[AOI["lon_min"], AOI["lat_min"], AOI["lon_max"], AOI["lat_max"]],
    query={"eo:cloud_cover": {"lt": 20}},
    max_items=20,
)
items = list(search.items())
# each item: item.id, item.datetime, item.assets, item.properties["eo:cloud_cover"]
```

### Sentinel-2 band reference (for water quality)

| Band | λ central | Resolution | Use |
|------|-----------|------------|-----|
| B03 | 560 nm (green) | 10 m | Turbidity |
| B04 | 665 nm (red) | 10 m | Chl-a absorption |
| B05 | 705 nm (red-edge) | 20 m | Chl-a fluorescence, bloom |
| B08 | 842 nm (NIR) | 10 m | Water/land contrast, macrophytes |

### B.4 Downloading without credentials — the public AWS COG mirror

For *this workshop* we avoid the auth dance entirely: Sentinel-2 L2A is also
mirrored as **Cloud-Optimised GeoTIFFs (COG)** on AWS Open Data, searchable via
the public **Earth Search** STAC and readable anonymously. `rasterio` can read
just the AOI window from each COG — no need to download the full ~800 MB scene.

```python
import requests, rasterio
from rasterio.windows import from_bounds

# 1) Public STAC search (no login)
r = requests.post("https://earth-search.aws.element84.com/v0/search", json={
    "collections": ["sentinel-s2-l2a-cogs"],
    "bbox": [AOI["lon_min"], AOI["lat_min"], AOI["lon_max"], AOI["lat_max"]],
    "datetime": "2021-09-01/2021-09-30",
    "query": {"eo:cloud_cover": {"lt": 10}}, "limit": 5})
item = r.json()["features"][0]
tci_url = item["assets"]["visual"]["href"]   # True-Colour COG on S3

# 2) Read only the AOI window from the COG
with rasterio.open(tci_url) as src:
    win = from_bounds(AOI["lon_min"], AOI["lat_min"],
                      AOI["lon_max"], AOI["lat_max"], transform=src.transform)
    rgb = src.read(window=win)
```

> This exact workflow is implemented, with rigorous scene selection (full
> coverage **and** low cloud over the lagoon), in **`scripts/download_sentinel2.py`**.
> Run it once to populate `data/` with the GeoTIFFs that Section C uses.
""")

# ===========================================================================
# SECTION C — INSTRUCTOR FIGURES FROM REAL GEOTIFFS
# ===========================================================================
nb.md(r"""---
## SECTION C — Instructor figures from real Sentinel-2 GeoTIFFs

These figures use **real** Sentinel-2 scenes downloaded by
`scripts/download_sentinel2.py`. If the GeoTIFFs are not present the cells below
print a notice and skip — Sections A and B are unaffected.

Four cloud-free, full-coverage scenes (MGRS tile 30SXG) span the 2021 crisis:

| Phase | Date | Coverage | Cloud over lagoon |
|-------|------|----------|-------------------|
| Baseline | 10 Feb 2020 | 100 % | 0.6 % |
| Bloom onset | 18 Aug 2021 | 100 % | 1.4 % |
| **Crisis peak** | 12 Sep 2021 | 100 % | 1.1 % |
| Recovery | 01 Mar 2022 | 100 % | 1.0 % |

> Scene selection matters: a scene can show "1 % cloud" in the catalogue yet only
> clip a swath **edge** over our AOI. We measured *both* valid coverage and real
> cloud over the lagoon water; e.g. 14 Jul 2021 was rejected (only 5.5 % coverage).

### C.1 Helpers and True-Colour images
""")

nb.code(r'''# Helpers shared by Section C
def load_tci(path):
    """Load a True-Colour GeoTIFF (common WGS84 grid) -> (H,W,3) uint8 image."""
    with rasterio.open(path) as src:
        return np.moveaxis(src.read(), 0, -1), S2_EXT

def load_band(path):
    """Load a single band (common WGS84 grid) as float32."""
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)

# Water mask in image coordinates (origin="upper": row 0 = North)
_H, _W = 2140, 1800
_rows = np.linspace(AOI["lat_max"], AOI["lat_min"], _H)
_cols = np.linspace(AOI["lon_min"], AOI["lon_max"], _W)
_CC, LAT2D = np.meshgrid(_cols, _rows)
WATER_MASK = MplPath(LAGOON_POLY).contains_points(
    np.column_stack([_CC.ravel(), LAT2D.ravel()])).reshape(_H, _W)

BAND_SCENES = {
    "Baseline\n10 Feb 2020":   "baseline",
    "Bloom onset\n18 Aug 2021": "bloom",
    "Crisis peak\n12 Sep 2021": "peak",
    "Recovery\n01 Mar 2022":    "recovery",
}

def compute_ndci(key):
    """Per-pixel NDCI over the lagoon, clouds masked (B04 > 800 DN)."""
    b05 = load_band(f"../data/s2_{key}_B05.tif")
    b04 = load_band(f"../data/s2_{key}_B04.tif")
    valid = WATER_MASK & (b04 > 30) & (b05 > 30) & (b04 < 800)
    ndci = np.where(valid, (b05 - b04) / np.maximum(b05 + b04, 1), np.nan)
    return np.ma.array(ndci, mask=~valid)

if not REAL_IMAGES_AVAILABLE:
    print("Section C skipped - real GeoTIFFs not found.")
    print("Run: python scripts/download_sentinel2.py")
else:
    fig, axes = plt.subplots(1, 4, figsize=(20, 8), dpi=140,
                             gridspec_kw={"wspace": 0.03})
    fig.patch.set_facecolor("#0d1b2a")
    for ax, (label, key) in zip(axes, BAND_SCENES.items()):
        img, ext = load_tci(f"../data/s2_{key}_TCI.tif")
        ax.imshow(img, extent=ext, origin="upper", aspect="equal",
                  interpolation="lanczos")
        ax.add_patch(mpatches.Polygon(LAGOON_POLY, closed=True, facecolor="none",
                     edgecolor="yellow", linewidth=1.4, linestyle="--", alpha=0.85))
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(label, color="white", fontsize=10, pad=6,
                     path_effects=[pe.withStroke(linewidth=2.5, foreground="black")])
        for sp in ax.spines.values(): sp.set_edgecolor("#80d4ff")
    fig.text(0.5, 0.01, "True Colour  |  R=B04 (665nm)  G=B03 (560nm)  B=B02 (490nm)"
             "  |  10 m/pixel  |  ESA Copernicus / AWS COG",
             ha="center", color="#aad4e8", fontsize=9)
    fig.suptitle("Sentinel-2 L2A - real True-Colour image of the Mar Menor",
                 color="white", fontsize=13, y=1.01)
    plt.show()
''')

nb.md(r"""### C.2 NDCI — the chlorophyll index that actually measures the bloom

The **NDCI** (Normalized Difference Chlorophyll Index; Mishra & Mishra 2012) is
the standard index for Case-2 waters:

$$\text{NDCI} = \frac{R_{rs}(B05) - R_{rs}(B04)}{R_{rs}(B05) + R_{rs}(B04)}$$

Computed **per pixel** over the ~1.3 million lagoon water pixels (clouds masked,
B04 > 800 DN). Real Mar Menor values run from about **−0.30** (clear winter
water) to **+0.05** (summer bloom) — a large, measurable jump.
""")

nb.code(r'''if not REAL_IMAGES_AVAILABLE:
    print("Section C skipped - run scripts/download_sentinel2.py")
else:
    VMIN, VMAX = -0.32, 0.10
    fig, axes = plt.subplots(1, 4, figsize=(20, 8.5), dpi=140,
                             gridspec_kw={"wspace": 0.04})
    fig.patch.set_facecolor("#0d1b2a")
    _imgs = []
    for ax, (label, key) in zip(axes, BAND_SCENES.items()):
        ndci = compute_ndci(key)
        tci, _ = load_tci(f"../data/s2_{key}_TCI.tif")
        grey = np.mean(tci / 255.0, axis=2) * 0.5
        ax.imshow(np.dstack([grey]*3), extent=S2_EXT, origin="upper",
                  aspect="equal", zorder=0)
        im = ax.imshow(ndci, extent=S2_EXT, origin="upper", aspect="equal",
                       cmap=plt.cm.turbo, vmin=VMIN, vmax=VMAX,
                       interpolation="bilinear", zorder=2)
        _imgs.append(im)
        ax.add_patch(mpatches.Polygon(LAGOON_POLY, closed=True, facecolor="none",
                     edgecolor="white", linewidth=1.0, alpha=0.7, zorder=3))
        med = float(np.ma.median(ndci))
        ax.set_title(f"{label}\nNDCI median = {med:+.3f}", color="white",
                     fontsize=10, pad=6,
                     path_effects=[pe.withStroke(linewidth=2.5, foreground="black")])
        ax.set_xlim(S2_EXT[0], S2_EXT[1]); ax.set_ylim(S2_EXT[2], S2_EXT[3])
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_edgecolor("#80d4ff")
    cb = fig.colorbar(_imgs[2], ax=axes, orientation="horizontal",
                      fraction=0.045, pad=0.05, aspect=50)
    cb.set_label("NDCI = (B05 - B04)/(B05 + B04)      blue = clear water  ->  red = intense bloom",
                 color="white", fontsize=11)
    plt.setp(cb.ax.xaxis.get_ticklabels(), color="white", fontsize=9)
    cb.outline.set_edgecolor("white")
    fig.suptitle("Chlorophyll index NDCI - real Sentinel-2, per-pixel (20 m)\n"
                 "Same colour range across the 4 dates: summer 2021 stands out",
                 color="white", fontsize=12.5, y=1.03)
    plt.show()
''')

nb.md(r"""### C.3 Where does the bloom hit hardest? Zone analysis

The NW shore receives runoff from the Campo de Cartagena (agricultural nitrate),
so we expect higher chlorophyll in the **north**. We split the lagoon into three
latitude bands and compare the median NDCI of each through the crisis cycle.
""")

nb.code(r'''if not REAL_IMAGES_AVAILABLE:
    print("Section C skipped - run scripts/download_sentinel2.py")
else:
    ZONES = {"North\n(>37.72)": LAT2D > 37.72,
             "Centre\n(37.66-37.72)": (LAT2D <= 37.72) & (LAT2D > 37.66),
             "South\n(<37.66)": LAT2D <= 37.66}
    ZCOL = ["#e76f51", "#e9c46a", "#2a9d8f"]
    zone_data = {z: [] for z in ZONES}
    labels = []
    for label, key in BAND_SCENES.items():
        labels.append(label.replace("\n", " "))
        ndci = compute_ndci(key)
        for z, m in ZONES.items():
            sel = m & ~ndci.mask
            zone_data[z].append(float(np.ma.median(ndci[sel])) if sel.sum() else np.nan)

    fig = plt.figure(figsize=(18, 7), dpi=140)
    fig.patch.set_facecolor("#0d1b2a")
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.5], wspace=0.18)
    fxx = [pe.withStroke(linewidth=2.5, foreground="black")]

    ax0 = fig.add_subplot(gs[0])
    ndci_peak = compute_ndci("peak")
    tci, _ = load_tci("../data/s2_peak_TCI.tif")
    ax0.imshow(np.dstack([np.mean(tci/255., axis=2)*0.5]*3), extent=S2_EXT,
               origin="upper", aspect="equal", zorder=0)
    ax0.imshow(ndci_peak, extent=S2_EXT, origin="upper", aspect="equal",
               cmap=plt.cm.turbo, vmin=-0.32, vmax=0.10, zorder=1)
    for (z, m), col in zip(ZONES.items(), ZCOL):
        lat_hi = LAT2D[m].max()
        ax0.axhline(lat_hi, color=col, lw=1.5, ls="--", zorder=4)
        ax0.text(-0.872, (LAT2D[m].min()+LAT2D[m].max())/2, z.split("\n")[0],
                 color=col, fontsize=11, fontweight="bold", rotation=90,
                 va="center", path_effects=fxx)
    ax0.add_patch(mpatches.Polygon(LAGOON_POLY, closed=True, facecolor="none",
                  edgecolor="white", linewidth=1.0, alpha=0.7, zorder=3))
    ax0.set_xlim(S2_EXT[0], S2_EXT[1]); ax0.set_ylim(S2_EXT[2], S2_EXT[3])
    ax0.set_xticks([]); ax0.set_yticks([])
    ax0.set_title("Analysis zones\n(NDCI, crisis peak Sep 2021)", color="white",
                  fontsize=10.5, path_effects=fxx)
    for sp in ax0.spines.values(): sp.set_edgecolor("#80d4ff")

    ax1 = fig.add_subplot(gs[1]); ax1.set_facecolor("#0d1b2a")
    x = np.arange(len(labels)); bw = 0.25
    for j, (z, col) in enumerate(zip(ZONES, ZCOL)):
        ax1.bar(x + (j-1)*bw, zone_data[z], bw, label=z.split("\n")[0],
                color=col, edgecolor="white", linewidth=0.6)
    ax1.axhline(0, color="white", lw=0.8)
    ax1.set_xticks(x); ax1.set_xticklabels(labels, color="white", fontsize=10)
    ax1.set_ylabel("Median NDCI per zone", color="white", fontsize=11)
    ax1.tick_params(colors="white")
    ax1.legend(title="Zone", facecolor="#16263a", edgecolor="#80d4ff",
               labelcolor="white", title_fontsize=10, fontsize=10)
    ax1.set_title("NDCI evolution by lagoon zone", color="white", fontsize=12)
    ax1.grid(axis="y", alpha=0.15)
    for sp in ax1.spines.values(): sp.set_edgecolor("#80d4ff")

    fig.suptitle("Where does the bloom hit hardest? - NDCI by Mar Menor zone",
                 color="white", fontsize=13, y=1.02)
    plt.show()
    print("Reading the real data:")
    for z in ZONES:
        base, _, peak_v, _ = zone_data[z]
        print(f"  {z.split(chr(10))[0]:7s}: winter={base:+.3f}  ->  summer 2021={peak_v:+.3f}")
''')

nb.md(r"""### C.4 Synthetic sampling points over the real image

A final composite: the 12 synthetic sampling points (Section A) drawn over the
real True-Colour scene of the crisis peak — the lagoon outline is the actual
satellite coastline, not an approximation.
""")

nb.code(r'''if not REAL_IMAGES_AVAILABLE:
    print("Section C skipped - run scripts/download_sentinel2.py")
else:
    img_peak, ext_peak = load_tci("../data/s2_peak_TCI.tif")
    peak = s2.query("'2021-07-15' <= date <= '2021-10-15'")
    ppoint = (peak.groupby("point_id")["chla_mg_m3"].mean()
                  .to_frame().merge(points, on="point_id"))

    fig, ax = plt.subplots(figsize=(10, 13), dpi=140)
    fig.patch.set_facecolor("#0d1b2a")
    ax.imshow(img_peak, extent=ext_peak, origin="upper", aspect="equal",
              interpolation="lanczos", zorder=0)
    vmax_val = max(ppoint["chla_mg_m3"].max(), 1.0)
    sizes = 120 + 400 * (ppoint["chla_mg_m3"] / vmax_val)
    sc = ax.scatter(ppoint["lon"], ppoint["lat"], c=ppoint["chla_mg_m3"], s=sizes,
                    cmap=CMAP_CHLA, norm=mcolors.Normalize(0, vmax_val),
                    edgecolors="white", linewidths=1.5, zorder=3, alpha=0.95)
    fx = [pe.withStroke(linewidth=3, foreground="black")]
    for _, row in ppoint.iterrows():
        ax.text(row.lon + 0.003, row.lat + 0.003, row.point_id.replace("S2_", "P"),
                fontsize=9, fontweight="bold", color="white", path_effects=fx, zorder=4)
    for glon_, glat_, name in [(-0.718, 37.750, "La Manga"), (-0.720, 37.622, "El Estacio"),
                               (-0.842, 37.748, "Los Alcazares"), (-0.845, 37.810, "San Javier / CARM")]:
        ax.text(glon_, glat_, name, fontsize=8.5, color="#ffe082", ha="center",
                style="italic", path_effects=[pe.withStroke(linewidth=2.5, foreground="#0d1b2a")], zorder=5)
    ax.set_xlim(ext_peak[0], ext_peak[1]); ax.set_ylim(ext_peak[2], ext_peak[3])
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_edgecolor("white")
    cb = plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("Mean chl-a (mg m$^{-3}$)  Jul-Oct 2021", color="white", fontsize=10)
    plt.setp(cb.ax.yaxis.get_ticklabels(), color="white", fontsize=9)
    cb.outline.set_edgecolor("white")
    ax.set_title("Synthetic sampling points on the real Sentinel-2 scene\n"
                 "Background: True Colour, 12 Sep 2021 (crisis peak)",
                 color="white", fontsize=11, pad=10)
    plt.show()
''')

# ===========================================================================
# EXERCISE + WRAP-UP
# ===========================================================================
nb.md(r"""---
## Exercise (~10 min)

**Q1.** Compute the **monthly-mean NDCI** of the lagoon across 2021 by downloading
one clear scene per month (use `compute_ndci` + the Section B STAC pattern). Plot
the time series. In which month does the bloom take off? Does it match the
documented Aug–Sep 2021 fish-kill?

**Q2.** Repeat the zone analysis (C.3) but split the lagoon **East (near La Manga)
vs West (agricultural shore)** instead of North/South. Which gradient is stronger?
What does that say about where the nutrients come from?

**Q3 (advanced).** Why does NDCI saturate at very dense blooms (> 30 mg/m³)?
Explain in terms of optical penetration depth and red-edge reflectance.

---
## Wrap-up of Module 1

- **CDSE** is the current access point (STAC at `stac.dataspace.copernicus.eu/v1`, collection `sentinel-2-l2a`), not SciHub.
- The Mar Menor is a **Case-2** water — atmospheric-correct with C2RCC; never blindly trust L2A reflectance as an aquatic product.
- **NDCI** from real pixels cleanly separates clear water from active bloom, and reveals the **N–S gradient** tied to agricultural inputs.
- A **+2 °C marine heatwave** cuts O₂ solubility by ~0.3 mg/L — enough, with the bloom's night-time respiration, to drive the 2021 bottom anoxia.

Continue with **Module 2: in-situ integration + ML / anomaly detection**.
""")

nb.save(str(OUT))
print(f"Notebook 1 written to {OUT}")
