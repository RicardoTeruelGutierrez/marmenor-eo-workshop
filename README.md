# Mar Menor — Earth Observation Workshop

**Audience:** PhD students, NYU
**Duration:** 2.5–3 h core + ~1.5 h advanced (Module 3)
**Language:** English
**Format:** Hands-on Jupyter notebooks with pre-cached datasets

---

## 1. What this workshop teaches

A practitioner-level introduction to extracting and analyzing Earth observation data over the **Mar Menor coastal lagoon** (Murcia, Spain), combining:

- ESA Copernicus **Sentinel-2** (chlorophyll-a, turbidity in Case-2 waters)
- ESA Copernicus **Sentinel-3 SLSTR** (sea surface temperature)
- **In-situ data** from the regional monitoring networks (CARM/IMIDA buoys, CHS-SAIH watershed)
- Time-series methods + **machine learning** for retrieval and anomaly detection
- **Building your own database from scratch** — discover, download, clean, store and analyse, so students can start their own monitoring projects (Module 3)

The Mar Menor is used as a canonical case study because it offers a long, well-documented series of eutrophication crises (2016, 2019 DANA, 2021 fish-kill, 2025 surge) and is one of the most-studied coastal lagoons in Europe.

## 2. Suggested schedule

| Time | Module | Format |
|------|--------|--------|
| 00:00–00:20 | Context lecture (`slides/intro.html`) | Slides |
| 00:20–01:35 | **Module 1** — Satellite data extraction (Sentinel-2 + Sentinel-3) | Notebook 01 |
| 01:35–01:50 | Break | — |
| 01:50–03:00 | **Module 2** — In-situ integration, time series, ML / anomalies | Notebook 02 |
| *+90 min* | **Module 3** — From zero to pro: build your own EO database | Notebook 03 |

**Module 3** is the "do it yourself for your own project" capstone: the full
pipeline from on-demand download to a queryable **SQLite + Parquet** database and
a reproducible pollution study. Run it as an extended third session, a hands-on
lab, or a take-home project — it is self-contained and runs offline from the
cached data.

If you have 3 h, extend the exercises in Module 1 §2.9 and Module 2 §4.2. If you have only 2 h, skip Module 1 §B (the CDSE/OData/STAC workflow) and Module 2 §3.2 (the spatial GroupKFold).

## 3. Prerequisites

Students should be comfortable with:

- Python data stack: `numpy`, `pandas`, `xarray`, `matplotlib`
- Basic geospatial concepts: WGS84, raster vs. vector, NetCDF
- Elementary supervised learning (regression, cross-validation)

No prior remote-sensing experience is assumed; we introduce reflectance, atmospheric correction and Case-2 waters in Module 1.

## 4. Environment setup

All dependencies are pinned in **`requirements.txt`**:

```bash
# Recommended: a fresh conda env
conda create -n marmenor python=3.11 -y
conda activate marmenor

pip install -r requirements.txt
```

Both notebooks begin with a dependency check that fails early with a clear
message if anything is missing, and a data sanity check that lists exactly which
files are absent. Verify the core stack manually with:

```bash
python -c "import numpy, pandas, pyarrow, xarray, sklearn, rasterio; print('OK')"
```

> **Note on `pyarrow`.** Both modules read `.parquet` datasets, so `pyarrow`
> (or `fastparquet`) is **required**, not optional.

## 5. Data inventory (`data/`)

The `data/` folder holds **two kinds** of files (see also the A/B/C notebook
structure in §1):

### 5.1 Synthetic datasets — for Sections A/B (offline, reproducible)

| File | Size | Content |
|------|------|---------|
| `stations.csv` | <1 KB | Five in-situ buoy stations (id, lat, lon, depth) |
| `insitu_buoys_2016_2025.parquet` | 249 KB | Daily T, S, chl-a, turbidity, DO, nitrate per station (18,265 rows) |
| `insitu_buoys_sample.csv` | <1 KB | First 3 rows for quick preview |
| `sentinel2_waterquality.parquet` | 75 KB | Bi-weekly Sentinel-2 derived chl-a + turbidity + 3 reflectance bands at 12 sampling points (4,860 rows) |
| `s2_sampling_points.csv` | <1 KB | Coordinates of the 12 sampling points |
| `sentinel3_sst_cube.nc` | 6.6 MB | Daily SLSTR SST on a 40×30 grid, 2017–2025, with **realistic marine-heatwave anomalies** injected for 2019/2021/2023/2024 (NetCDF, CF-compliant) |
| `watershed_forcing.csv` | 73 KB | Daily precipitation + nitrate flux proxy, 2016–2025 |

Regenerate (no network needed):

```bash
python scripts/generate_datasets.py
```

> **Authenticity.** These are **synthetic**, calibrated against peer-reviewed
> literature (Soriano-Gonzalez et al. 2022; Sola et al. 2023; Pedrera et al.
> 2024; arXiv:2510.09736) so the documented crises (2016, 2019, 2021, 2025)
> appear in the right months with realistic magnitudes. **Teaching only.**

### 5.2 Real Sentinel-2 imagery — for Section C (one-off download)

These are **real** satellite pixels, downloaded from the public AWS Open-Data COG
mirror (no credentials). They are **not** produced by `generate_datasets.py`; run
the downloader once:

```bash
python scripts/download_sentinel2.py        # needs internet, 25 files, ~140 MB
```

| File pattern | Content |
|--------------|---------|
| `s2_{baseline,bloom,peak,recovery}_TCI.tif` | Real True-Colour composites (10 Feb 2020, 18 Aug 2021, 12 Sep 2021, 01 Mar 2022) on a common WGS84 grid |
| `s2_{scene}_{B02,B03,B04,B05,B08}.tif` | Individual bands for NDCI / false-colour |
| `lagoon_contour_wgs84.npy` | Lagoon outline (191 vertices) extracted from the real NIR band |

If these are absent, **Section C prints a notice and skips** — Sections A and B
still run, and the notebook falls back to a hand-digitised lagoon outline.

### 5.3 The database (`database/`) — built by Module 3

Module 3 (`03_build_database.ipynb`) *creates* this folder; you do not ship it.
Running the notebook produces:

| Path | Content |
|------|---------|
| `database/marmenor.db` | SQLite database: `scenes` (image catalogue + QA), `observations` (tidy long-format NDCI/chl-a by date/zone/source), `stations` (in-situ metadata) |
| `database/rasters/ndci_YYYY-MM-DD.parquet` | Per-pixel NDCI fields as columnar Parquet (bulk arrays kept out of the DB) |

Inspect it from any shell:

```bash
sqlite3 database/marmenor.db
sqlite> .tables
sqlite> SELECT variable, COUNT(*) FROM observations GROUP BY variable;
```

## 6. How to access the *real* data

The notebooks include the exact code patterns to use against the live services. The two practical entry points are:

### 6.1 Copernicus Data Space Ecosystem (CDSE)

Replaces the old Open Access Hub since November 2023.

- Portal: <https://dataspace.copernicus.eu>
- Documentation: <https://documentation.dataspace.copernicus.eu/>
- APIs: OData (REST), STAC, Sentinel Hub Process/Statistical/Catalog, openEO

Free account; no credit card. Quota: 30,000 processing units / month per user (more than enough for a PhD project at this scale).

> **Current STAC endpoint (Nov 2025).** The old `catalogue.dataspace.copernicus.eu/stac`
> was deprecated on 17 Nov 2025. Use **`https://stac.dataspace.copernicus.eu/v1/`**
> with lowercase collection IDs such as **`sentinel-2-l2a`** (not `SENTINEL-2`).
> Module 1 §B.3 shows the current pattern.

> **No-credentials shortcut.** Sentinel-2 L2A is also mirrored as Cloud-Optimised
> GeoTIFFs on AWS Open Data, searchable anonymously via Earth Search STAC. That is
> what `scripts/download_sentinel2.py` uses, so the workshop needs no CDSE login.

### 6.2 Copernicus Marine Service

- Portal: <https://marine.copernicus.eu>
- CLI: `pip install copernicus-marine` then `copernicus-marine subset ...`
- Most useful products for the Mar Menor:
  - `MEDSEA_MULTIYEAR_PHY_006_004` — Mediterranean physics reanalysis
  - `MEDSEA_ANALYSISFORECAST_BGC_006_014` — biogeochemistry forecast
  - `INSITU_MED_PHYBGCWAV_DISCRETE_MYNRT_013_035` — in-situ TAC

### 6.3 Regional in-situ portals

- **CARM (Murcia regional government):** <https://canalmarmenor.carm.es/datos-en-tiempo-real/> — Mar Menor real-time monitoring dashboard. Exports as CSV.
- **CHS-SAIH (Segura watershed hydrology):** <https://www.chsegura.es/en/cuenca/redes-de-control/saih/>
- **IMIDA agro-meteorological network:** <http://siam.imida.es/>

## 7. Folder layout

```
marmenor_workshop/
├── README.md                     ← this file
├── requirements.txt              ← pinned dependencies (pip install -r)
├── data/                         ← datasets (synthetic §5.1 + downloaded §5.2)
├── database/                     ← built by Module 3 (marmenor.db + rasters/*.parquet)
├── notebooks/
│   ├── 01_satellite_data_extraction.ipynb   (Sections A/B/C, English)
│   ├── 02_insitu_timeseries_ml.ipynb        (English)
│   └── 03_build_database.ipynb              (0-to-pro DB pipeline, English)
├── slides/
│   └── intro.html                ← context lecture (open in a browser)
├── requirements.txt
└── scripts/
    ├── generate_datasets.py      ← builds the SYNTHETIC data/ files (§5.1, offline)
    ├── download_sentinel2.py     ← downloads the REAL Sentinel-2 GeoTIFFs (§5.2)
    ├── nb_builder.py             ← internal helper (creates output dir on save)
    ├── build_nb1.py              ← rebuilds notebook 1 from source
    ├── build_nb2.py              ← rebuilds notebook 2 from source
    └── build_nb3.py              ← rebuilds notebook 3 from source
```

> **Module 1 is organised in three sections** (see the notebook header):
> **A** — synthetic cached data (offline, reproducible in class);
> **B** — optional real-data workflow via CDSE / STAC;
> **C** — instructor figures from the downloaded real Sentinel-2 GeoTIFFs.
> Both modules are in **English**, with an ES→EN glossary of local terms in
> Module 1.

## 8. References

Key papers explicitly referenced in the notebooks:

1. Brockmann, C. et al. (2016). *Evolution of the C2RCC neural network for Sentinel-2 and -3 for the retrieval of ocean colour products in normal and extreme optically complex waters*. ESA SP-740.
2. Soriano-González, J. et al. (2022). *Use of Sentinel-2 and Landsat-8 satellites for water quality monitoring: an early warning tool in the Mar Menor coastal lagoon*. Remote Sensing 14, 2744.
3. Sola, F. et al. (2023). *Machine learning for detection of macroalgal blooms in the Mar Menor coastal lagoon using Sentinel-2*. Remote Sensing 15, 1208.
4. Pedrera, A. et al. (2024). *Assessment of oceanographic services for the monitoring of highly anthropised coastal lagoons*. Ecological Informatics.
5. Skarmeta, A. F. et al. (2025). *Chlorophyll-a mapping and prediction in the Mar Menor lagoon using C2RCC-processed Sentinel-2 imagery*. arXiv:2510.09736.

## 9. Instructor checklist

Before the workshop:

- [ ] `pip install -r requirements.txt` in a fresh env, then run the dependency-check cell at the top of each notebook.
- [ ] Confirm `python scripts/generate_datasets.py` runs in under a minute (Sections A/B).
- [ ] Run `python scripts/download_sentinel2.py` once on a machine with internet to populate the real-imagery files for **Section C** (otherwise Section C self-skips).
- [ ] Pre-execute both notebooks once so the cached outputs render even without re-running.
- [ ] Have one student create a free CDSE account live so the others see the Section B flow.

During:

- Module 1 §1 (auth, OData) is the slowest part for newcomers — budget 25 min.
- Module 1 §2.3 is the visual hook (the crisis chart) — pause for discussion.
- Module 2 §4 is the analytical climax — leave 15 min for it.

After:

- The take-home assignment (notebook 2, §5) is genuinely interesting work, suitable as a starter for an end-of-semester project or a paper-club extension.

---

*Workshop materials prepared with Claude. Synthetic datasets are calibrated against published literature but are not real measurements.*
