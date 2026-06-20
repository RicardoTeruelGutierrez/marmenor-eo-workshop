"""
Mar Menor Workshop - Synthetic Dataset Generator
=================================================

Builds realistic but synthetic datasets for the workshop, calibrated against
published values from peer-reviewed literature on the Mar Menor lagoon:

  - Erena et al. (2019) -- IMIDA buoy network
  - Soriano-Gonzalez et al. (2022) -- Sentinel-2 + Landsat-8 monitoring
  - Sola et al. (2023) -- macroalgal bloom ML detection
  - Pedrera et al. (2024) -- Copernicus services assessment
  - arXiv:2510.09736 (2025) -- C2RCC chl-a mapping

All values are SYNTHETIC. They reproduce the documented temporal patterns
(2016 first crisis, 2019 DANA flooding, August 2021 fish-kill, 2025 surge)
without representing any specific real measurement.

Outputs are written to ../data/
"""

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path

# Reproducibility
RNG = np.random.default_rng(42)

# Mar Menor bounding box (WGS84)
LON_MIN, LON_MAX = -0.86, -0.71
LAT_MIN, LAT_MAX = 37.61, 37.80

# Documented crisis events ----------------------------------------------------
CRISES = {
    "2016-summer": ("2016-05-01", "2016-09-30", 3.0),   # First eutrophication crisis
    "2019-DANA":   ("2019-09-10", "2019-11-15", 4.0),   # Catastrophic flooding event
    "2021-anoxia": ("2021-07-15", "2021-10-15", 4.5),   # Mass fish-kill August 2021
    "2025-surge":  ("2025-06-01", "2025-09-30", 3.2),   # Recent bloom resurgence
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) Five in-situ monitoring stations (mimics IMIDA / CARM buoy network)
# ---------------------------------------------------------------------------

STATIONS = pd.DataFrame({
    "station_id": ["MM01", "MM02", "MM03", "MM04", "MM05"],
    "name":       ["Los Alcazares", "Los Urrutias", "El Estacio",
                   "La Manga Sur", "Punta Brava"],
    "lon":        [-0.838, -0.823, -0.741, -0.728, -0.793],
    "lat":        [37.741, 37.685, 37.755, 37.640, 37.715],
    "depth_m":    [4.5, 6.2, 5.1, 3.8, 5.7],
})
STATIONS.to_csv(DATA_DIR / "stations.csv", index=False)
print(f"[1/5] stations.csv  ({len(STATIONS)} stations)")


def _crisis_amplitude(date, base_amp=1.0):
    """Return per-day multiplicative amplitude given documented crises."""
    amp = base_amp
    for _, (start, end, mag) in CRISES.items():
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        if s <= date <= e:
            # Bell-shaped within window
            center = s + (e - s) / 2
            sigma = (e - s).days / 4
            bell = np.exp(-((date - center).days ** 2) / (2 * sigma ** 2))
            amp += (mag - 1) * bell
    return amp


def _seasonal_temp(date):
    """Annual SST cycle for Mar Menor (Mediterranean coastal lagoon)."""
    doy = date.dayofyear
    return 19.0 + 9.5 * np.sin(2 * np.pi * (doy - 110) / 365)


def _seasonal_chla(date):
    """Background chl-a -- lagoons show spring + autumn maxima."""
    doy = date.dayofyear
    spring = 1.8 * np.exp(-((doy - 110) ** 2) / 2000)
    autumn = 1.2 * np.exp(-((doy - 290) ** 2) / 2500)
    return 0.6 + spring + autumn


# ---------------------------------------------------------------------------
# 2) In-situ daily time series per station (2016-2025)
# ---------------------------------------------------------------------------

dates = pd.date_range("2016-01-01", "2025-12-31", freq="D")
rows = []
for _, st in STATIONS.iterrows():
    # station-specific offsets (proximity to runoff inlets matters)
    chl_offset = {"MM01": 1.4, "MM02": 1.7, "MM03": 0.7,
                  "MM04": 0.5, "MM05": 1.1}[st.station_id]
    turb_offset = {"MM01": 1.5, "MM02": 1.8, "MM03": 0.8,
                   "MM04": 0.6, "MM05": 1.2}[st.station_id]
    for d in dates:
        amp = _crisis_amplitude(d)
        chla = _seasonal_chla(d) * chl_offset * amp + RNG.normal(0, 0.25)
        chla = max(chla, 0.05)
        turbidity = (0.8 * chl_offset * amp ** 0.8) * turb_offset \
                    + RNG.normal(0, 0.2)
        turbidity = max(turbidity, 0.1)
        sst = _seasonal_temp(d) + RNG.normal(0, 0.6)
        # Salinity drops sharply during DANA-type events
        salinity = 44.5 + RNG.normal(0, 0.6)
        if d >= pd.Timestamp("2019-09-10") and d <= pd.Timestamp("2019-10-20"):
            salinity -= 4.0 * np.exp(-((d - pd.Timestamp("2019-09-15")).days) ** 2 / 200)
        # Dissolved oxygen plunges in 2021 anoxia
        do = 7.5 + RNG.normal(0, 0.4) - (sst - 18) * 0.08
        if pd.Timestamp("2021-08-10") <= d <= pd.Timestamp("2021-09-05"):
            do -= 4.5 * np.exp(-((d - pd.Timestamp("2021-08-20")).days) ** 2 / 80)
        do = max(do, 0.1)
        # Nitrates: chronic background + DANA spikes
        nitrate = 0.8 + RNG.normal(0, 0.15)
        if pd.Timestamp("2019-09-10") <= d <= pd.Timestamp("2019-10-30"):
            nitrate += 12 * np.exp(-((d - pd.Timestamp("2019-09-18")).days) ** 2 / 100)

        rows.append({
            "date": d, "station_id": st.station_id,
            "sst_C": round(sst, 2),
            "salinity_psu": round(salinity, 2),
            "chla_mg_m3": round(chla, 3),
            "turbidity_FNU": round(turbidity, 3),
            "do_mg_L": round(do, 2),
            "nitrate_mg_L": round(nitrate, 3),
        })

insitu = pd.DataFrame(rows)
insitu.to_parquet(DATA_DIR / "insitu_buoys_2016_2025.parquet")
insitu.head(3).to_csv(DATA_DIR / "insitu_buoys_sample.csv", index=False)
print(f"[2/5] insitu_buoys_2016_2025.parquet  ({len(insitu):,} rows, "
      f"{insitu.station_id.nunique()} stations)")


# ---------------------------------------------------------------------------
# 3) Sentinel-2 derived water-quality time series (12 sampling points)
#    Simulates output of a C2RCC atmospheric correction + chl-a retrieval
# ---------------------------------------------------------------------------

SAMPLE_POINTS = []
for i in range(12):
    SAMPLE_POINTS.append({
        "point_id": f"S2_P{i+1:02d}",
        "lon": LON_MIN + (LON_MAX - LON_MIN) * RNG.uniform(0.1, 0.9),
        "lat": LAT_MIN + (LAT_MAX - LAT_MIN) * RNG.uniform(0.1, 0.9),
    })
sample_df = pd.DataFrame(SAMPLE_POINTS)
sample_df.to_csv(DATA_DIR / "s2_sampling_points.csv", index=False)

# Sentinel-2 overpass every 5 days, ~40% cloudy frames discarded
s2_dates = pd.date_range("2017-01-01", "2025-12-31", freq="5D")
s2_keep = RNG.random(len(s2_dates)) > 0.40
s2_dates = s2_dates[s2_keep]

s2_rows = []
for d in s2_dates:
    amp = _crisis_amplitude(d)
    for p in SAMPLE_POINTS:
        # Spatial gradient: north shore (MM01/02 area) more nutrient-loaded
        spatial_factor = 1.0 + 0.6 * (p["lat"] - LAT_MIN) / (LAT_MAX - LAT_MIN) \
                       + 0.4 * (LON_MAX - p["lon"]) / (LON_MAX - LON_MIN)
        chla = _seasonal_chla(d) * spatial_factor * amp + RNG.normal(0, 0.4)
        chla = max(chla, 0.1)
        turb = chla * 0.45 + RNG.normal(0, 0.3)
        turb = max(turb, 0.05)
        # Reflectance in three bands (Rrs values typical for Case-2 waters)
        b03 = 0.012 + 0.0008 * chla + RNG.normal(0, 0.0008)  # green
        b04 = 0.008 + 0.0004 * chla + RNG.normal(0, 0.0006)  # red
        b05 = 0.010 + 0.0009 * chla + RNG.normal(0, 0.0007)  # red-edge
        s2_rows.append({
            "date": d, "point_id": p["point_id"],
            "chla_mg_m3": round(chla, 3),
            "turbidity_FNU": round(turb, 3),
            "Rrs_B03": round(b03, 5),
            "Rrs_B04": round(b04, 5),
            "Rrs_B05": round(b05, 5),
        })
s2 = pd.DataFrame(s2_rows)
s2.to_parquet(DATA_DIR / "sentinel2_waterquality.parquet")
print(f"[3/5] sentinel2_waterquality.parquet  ({len(s2):,} rows)")


# ---------------------------------------------------------------------------
# 4) Sentinel-3 SLSTR-derived SST: gridded daily field over the lagoon
# ---------------------------------------------------------------------------

s3_dates = pd.date_range("2017-01-01", "2025-12-31", freq="D")
# Coarser grid mimicking SLSTR 1 km resampled to ~500 m
lon_grid = np.linspace(LON_MIN, LON_MAX, 30)
lat_grid = np.linspace(LAT_MIN, LAT_MAX, 40)

sst_cube = np.zeros((len(s3_dates), len(lat_grid), len(lon_grid)), dtype=np.float32)
# Land-sea mask: simple ellipse approximating lagoon shape (illustrative only)
lon2d, lat2d = np.meshgrid(lon_grid, lat_grid)
cx, cy = (LON_MIN + LON_MAX) / 2, (LAT_MIN + LAT_MAX) / 2
mask = ((lon2d - cx) / 0.08) ** 2 + ((lat2d - cy) / 0.10) ** 2 < 1.0

# Normalised spatial fields (0-1) used to give the heatwave real structure.
# The southern basin is shallower -> warms faster and amplifies heatwaves.
south_factor = 1.0 - (lat2d - LAT_MIN) / (LAT_MAX - LAT_MIN)   # 1 in south, 0 in north
west_factor  = 1.0 - (lon2d - LON_MIN) / (LON_MAX - LON_MIN)   # 1 in west,  0 in east


def _marine_heatwave(date):
    """Deterministic marine-heatwave anomaly (degC) from documented events.

    Each tuple is (peak_date, sigma_days, peak_magnitude). The August 2021
    event is the strongest -- it preceded the catastrophic fish-kill.
    """
    events = [
        ("2019-08-05", 22, 1.8),   # warm summer preceding the 2019 DANA
        ("2021-08-12", 32, 3.2),   # MARINE HEATWAVE before the Aug-2021 anoxia
        ("2022-07-18", 26, 2.0),   # 2022 summer
        ("2023-08-20", 28, 2.4),   # 2023 Mediterranean heatwave
        ("2024-08-05", 26, 2.1),   # 2024
    ]
    total = 0.0
    for peak_str, sigma, mag in events:
        dd = (date - pd.Timestamp(peak_str)).days
        total += mag * np.exp(-(dd ** 2) / (2.0 * sigma ** 2))
    return total


for i, d in enumerate(s3_dates):
    base = _seasonal_temp(d)
    # Shallow lagoons show strong horizontal SST gradients
    grad = 0.9 * (lat2d - LAT_MIN) / (LAT_MAX - LAT_MIN) \
         - 0.5 * (lon2d - LON_MIN) / (LON_MAX - LON_MIN)
    # Marine heatwave: amplified in the shallow south-western basin
    hw = _marine_heatwave(d)
    hw_field = hw * (0.6 + 0.5 * south_factor + 0.2 * west_factor)
    daily = base + grad + hw_field + RNG.normal(0, 0.4, lon2d.shape).astype(np.float32)
    daily[~mask] = np.nan
    sst_cube[i] = daily

# Mark roughly 30% of days as cloud-flagged (NaN over whole scene)
cloud_mask = RNG.random(len(s3_dates)) < 0.30
sst_cube[cloud_mask] = np.nan

ds = xr.Dataset(
    {
        "sst": (("time", "lat", "lon"), sst_cube,
                {"units": "degC",
                 "long_name": "Sea Surface Temperature",
                 "source": "Sentinel-3 SLSTR L2 (synthetic)"}),
    },
    coords={
        "time": s3_dates,
        "lat": ("lat", lat_grid, {"units": "degrees_north"}),
        "lon": ("lon", lon_grid, {"units": "degrees_east"}),
    },
    attrs={
        "title": "Mar Menor synthetic SST cube (Sentinel-3 SLSTR proxy)",
        "institution": "Workshop training data -- not for operational use",
        "reference": "Pedrera et al. 2024, doi:10.1016/j.ecoinf.2024.102545",
    },
)
ds.to_netcdf(DATA_DIR / "sentinel3_sst_cube.nc",
             encoding={"sst": {"zlib": True, "complevel": 4}})
print(f"[4/5] sentinel3_sst_cube.nc  ({ds.sst.nbytes / 1e6:.1f} MB on disk)")


# ---------------------------------------------------------------------------
# 5) Watershed forcing -- daily precipitation + nitrate runoff proxy
#    Mimics CHS-SAIH (Segura) + IMIDA agro-meteorological data
# ---------------------------------------------------------------------------

force_dates = pd.date_range("2016-01-01", "2025-12-31", freq="D")
precip = np.maximum(0, RNG.gamma(0.4, 4, len(force_dates)) - 1.0)
# Documented DANA events
event_days = ["2019-09-12", "2019-12-19", "2020-09-15",
              "2022-10-30", "2024-08-25"]
for ev in event_days:
    idx = (force_dates == pd.Timestamp(ev)).argmax()
    precip[idx:idx+3] += [90, 60, 25]

# Watershed nitrate flux proxy: 5-day lagged convolution of precip
kernel = np.array([0.1, 0.3, 0.35, 0.15, 0.10])
flux = np.convolve(precip, kernel, mode="same") * 1.2 + RNG.normal(0, 0.5, len(precip))
flux = np.maximum(flux, 0)

watershed = pd.DataFrame({
    "date": force_dates,
    "precip_mm": np.round(precip, 2),
    "nitrate_flux_kgN_day": np.round(flux * 50, 1),
})
watershed.to_csv(DATA_DIR / "watershed_forcing.csv", index=False)
print(f"[5/5] watershed_forcing.csv  ({len(watershed):,} rows)")

print("\nAll datasets written to:", DATA_DIR)
