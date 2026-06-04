# -*- coding: utf-8 -*-
"""Curated, step-by-step slide content for the three modules.

Each entry is (builder_name, args_tuple). Consumed by build_slides_html.py.
Code snippets are trimmed to the essential lines; figures are the real outputs
extracted from the executed notebooks by extract_figures.py.
"""

# =========================================================================
# MODULE 1 — Satellite data extraction
# =========================================================================
F1 = ("module 1", "satellite data extraction")

MODULE1 = [
    ("cover", (
        "Module 01 · notebook 01_satellite_data_extraction",
        "Reading chlorophyll<br>and heat from orbit.",
        "Step by step: from raw Sentinel reflectance to the visible fingerprints "
        "of a dying lagoon — Sentinel-2 water colour and Sentinel-3 temperature.",
        [("10 m", "S2 resolution"), ("NDCI", "chlorophyll index"),
         ("+2 °C", "2021 heatwave"), ("18", "steps"),],
        ("module 1 / 00", "satellite data extraction · 75 min"))),

    # ---- Part 1: concepts ----
    ("divider", (
        "Part 1 — the concepts you need first",
        "Why this lagoon breaks<br>the textbook algorithms.",
        "Three ideas before any code: Case-2 optics, the red-edge index, and how "
        "the notebook is split into runnable sections.",
        F1)),

    ("concept", (
        "§ 1.1 — Case-2 waters",
        "Sediment, CDOM and macrophytes — not just phytoplankton.",
        "<p class='lede'>Open-ocean (Case-1) algorithms assume phytoplankton alone "
        "drives the colour. The Mar Menor is shallow and nutrient-loaded, so three "
        "things move the signal independently of chlorophyll.</p>"
        "<p>The fix: the <strong>C2RCC</strong> neural-network correction, then a "
        "locally-calibrated index.</p>",
        "<h3>The three confounders</h3><ul class='tight'>"
        "<li><strong>Suspended sediment</strong> raises blue/green → chl-a over-estimated</li>"
        "<li><strong>CDOM</strong> from runoff absorbs in the blue</li>"
        "<li><strong>Macrophytes</strong> on the bottom add a NIR signal</li></ul>"
        "<p style='margin-top:.8rem;color:#b8460c;'><em>L2A surface reflectance is a "
        "LAND correction — not, by itself, an aquatic C2RCC product.</em></p>",
        F1)),

    ("concept", (
        "§ 1.2 — The chlorophyll index",
        "The red-edge is the trick.",
        "<p class='lede'>Chlorophyll absorbs strongly in the red (B04, 665 nm) and "
        "reflects in the red-edge (B05, 705 nm). Any ratio of the two rises with "
        "concentration.</p>"
        "<div class='formula'>NDCI = (B05 − B04) / (B05 + B04)</div>"
        "<p>Robust to sediment, unlike a blue/green ratio.</p>",
        "<h3>Two forms we use</h3><ul class='tight'>"
        "<li><strong>B05/B04 ratio</strong> — the simple proxy (Section A)</li>"
        "<li><strong>NDCI</strong> — normalized, bounded, per-pixel (Section C)</li></ul>"
        "<p style='margin-top:.6rem;'>Real Mar Menor NDCI runs from <strong>−0.28</strong> "
        "(clear winter water) to <strong>−0.05</strong> (summer bloom).</p>",
        F1)),

    ("concept", (
        "§ 1.3 — How the notebook is built",
        "Three sections, three failure modes kept apart.",
        "<h3>A — Synthetic, offline</h3><p>Cached datasets in <code>data/</code>. "
        "Runs in class with no internet, no account.</p>"
        "<h3 style='margin-top:.7rem;'>B — Real workflow</h3><p>The CDSE / STAC "
        "download patterns. Shown, not run in class.</p>"
        "<h3 style='margin-top:.7rem;'>C — Real imagery</h3><p>Figures from real "
        "Sentinel-2 scenes. The lagoon outline is the actual satellite coastline.</p>",
        "<p class='lede'>The split means a student never gets stuck mid-lesson: "
        "“what runs anywhere” is cleanly separated from “what needs the cloud”.</p>"
        "<p style='margin-top:.8rem;'>Open the <strong>Table of contents</strong> "
        "(☰) in Colab to jump between them.</p>",
        F1)),

    # ---- Section A ----
    ("divider", (
        "Section A — synthetic, runs offline",
        "The long view of the crisis.",
        "Everything here runs from cached data calibrated against the published "
        "literature. The documented crises appear in the right months.",
        F1)),

    ("step", (
        "§ A — step 1 · load + resample",
        "Lagoon-wide weekly chlorophyll",
        "<p>Read the 12-point table, average to a lagoon-wide <strong>weekly mean</strong>, "
        "and smooth with a 4-week rolling window. The four crises light up.</p>",
        "s2 = pd.read_parquet(\n    DATA/'sentinel2_waterquality.parquet')\n\n"
        "weekly = (s2.set_index('date')['chla_mg_m3']\n"
        "            .resample('W').mean()\n"
        "            .rolling(4, min_periods=1).mean())",
        "mod1_01.png", F1)),

    ("step", (
        "§ A — step 2 · day-of-year climatology",
        "SST anomaly: signal vs the normal year",
        "<p>Build a <strong>day-of-year climatology</strong> (mean per day 1–365 "
        "across all years) and subtract it. What remains is the anomaly — red = "
        "warmer than usual.</p>",
        "clim = df.groupby('doy')['sst'].mean()\n"
        "df = df.join(clim, on='doy', rsuffix='_clim')\n"
        "df['anomaly'] = df['sst'] - df['mean']",
        "mod1_02.png", F1)),

    ("step", (
        "§ A — step 3 · heatwave → oxygen",
        "A +2 °C heatwave strangles the oxygen",
        "<p>August 2021 ran <strong>+1.9 °C</strong> above climatology. The "
        "Benson–Krause curve turns that into a <strong>−0.3 mg/L</strong> drop in "
        "oxygen capacity — the kill mechanism, quantified.</p>",
        "def o2_sat(T, S=37.0):\n"
        "    # Benson-Krause O2 solubility (mg/L)\n"
        "    ...\n"
        "drop = o2_sat(27.46) - o2_sat(30.50)\n"
        "# -> 0.31 mg/L lost from 2020 to 2021",
        "mod1_03.png", F1)),

    # ---- Section B ----
    ("divider", (
        "Section B — how to get the real data",
        "Discover &amp; download, the 2026 way.",
        "Reference patterns for your own project: the current CDSE STAC endpoint "
        "and the Cloud-Optimised-GeoTIFF window read.",
        F1)),

    ("concept", (
        "§ B — step 1 · STAC search",
        "Find scenes over the lagoon",
        "<p class='lede'>SciHub is retired. The current entry point is "
        "<strong>CDSE</strong>. Search the catalogue by area, dates and cloud cover.</p>"
        "<ul class='tight'><li>Endpoint: <code>stac.dataspace.copernicus.eu/v1</code></li>"
        "<li>Collection: lowercase <code>sentinel-2-l2a</code></li>"
        "<li>Use <strong>L2A</strong> (surface), not L1C</li></ul>",
        "<pre class='code'><span class='k'>from</span> pystac_client <span class='k'>import</span> Client\n"
        "cat = Client.open(\n  <span class='s'>\"https://stac.dataspace.\"</span>\n"
        "  <span class='s'>\"copernicus.eu/v1/\"</span>)\n"
        "search = cat.search(\n"
        "  collections=[<span class='s'>\"sentinel-2-l2a\"</span>],\n"
        "  datetime=<span class='s'>\"2021-08-01/2021-09-30\"</span>,\n"
        "  bbox=BBOX,\n"
        "  query={<span class='s'>\"eo:cloud_cover\"</span>:{<span class='s'>\"lt\"</span>:20}})</pre>",
        F1, ("edit", "REFERENCE"))),

    ("concept", (
        "§ B — step 2 · the COG trick",
        "Download only the AOI window",
        "<p class='lede'>A full scene is ~800 MB. A Cloud-Optimised GeoTIFF is "
        "internally tiled, so <code>rasterio</code> reads <strong>only the pixels "
        "over your bounding box</strong> — a few MB over HTTP.</p>"
        "<p>This single habit is what makes EO pipelines scale.</p>",
        "<pre class='code'><span class='k'>from</span> rasterio.windows <span class='k'>import</span> from_bounds\n"
        "<span class='k'>with</span> rasterio.open(tci_url) <span class='k'>as</span> src:\n"
        "    win = from_bounds(*bbox,\n"
        "        transform=src.transform)\n"
        "    rgb = src.read(window=win)\n"
        "<span class='c'># ~8 MB instead of ~240 MB</span></pre>",
        F1, ("edit", "REFERENCE"))),

    # ---- Section C ----
    ("divider", (
        "Section C — real Sentinel-2 imagery",
        "Pixel-perfect, from real scenes.",
        "Four cloud-free, full-coverage scenes spanning the 2021 crisis, chosen "
        "by measuring real coverage AND cloud over the lagoon itself.",
        F1)),

    ("step", (
        "§ C — step 1 · True-Colour composites",
        "What the satellite actually saw",
        "<p>Load each cached True-Colour GeoTIFF and draw the lagoon outline. The "
        "yellow line is extracted from the <strong>NIR band itself</strong> — 191 "
        "exact vertices, not a hand-drawn polygon.</p>",
        "def load_tci(path):\n"
        "    with rasterio.open(path) as src:\n"
        "        return np.moveaxis(src.read(),0,-1)\n\n"
        "for key in ['baseline','bloom','peak','recovery']:\n"
        "    ax.imshow(load_tci(f'../data/s2_{key}_TCI.tif'))",
        "mod1_04.png", F1)),

    ("step", (
        "§ C — step 2 · NDCI per pixel",
        "The chlorophyll index, 1.3 M pixels",
        "<p>Compute NDCI on every water pixel (clouds masked). Same colour scale "
        "across all four dates: <strong>summer 2021 stands out hard</strong> "
        "against the clear winter baseline.</p>",
        "b05 = load_band(f's2_{key}_B05.tif')\n"
        "b04 = load_band(f's2_{key}_B04.tif')\n"
        "valid = WATER_MASK & (b04>30) & (b04<800)\n"
        "ndci = (b05 - b04) / (b05 + b04)\n"
        "ndci = np.where(valid, ndci, np.nan)",
        "mod1_05.png", F1)),

    ("step", (
        "§ C — step 3 · zone analysis",
        "Where does the bloom hit hardest?",
        "<p>Split the lagoon into North / Centre / South and take the median NDCI "
        "per zone, per date. The <strong>north-west shore</strong> — fed by "
        "agricultural runoff — is consistently highest.</p>",
        "ZONES = {'north': LAT2D > 37.72,\n"
        "         'centre': (LAT2D<=37.72)&(LAT2D>37.66),\n"
        "         'south': LAT2D <= 37.66}\n"
        "for z, m in ZONES.items():\n"
        "    med = np.ma.median(ndci[m & ~ndci.mask])",
        "mod1_06.png", F1)),

    ("step", (
        "§ C — step 4 · points on the real image",
        "Synthetic points over real pixels",
        "<p>The 12 sampling points (Section A) drawn over the real crisis-peak "
        "scene. The coastline is the satellite's — context the synthetic data "
        "alone cannot give.</p>",
        "img = load_tci('../data/s2_peak_TCI.tif')\n"
        "ax.imshow(img, extent=ext, origin='upper')\n"
        "ax.scatter(pts.lon, pts.lat,\n"
        "           c=pts.chla_mg_m3, cmap=CMAP_CHLA)",
        "mod1_07.png", F1)),

    ("takeaways", (
        "§ — what to walk away with",
        "Module 1 in four lines.",
        [("CDSE, not SciHub.", "STAC at stac.dataspace.copernicus.eu/v1, collection sentinel-2-l2a."),
         ("Case-2 means be careful.", "Atmospheric-correct with C2RCC; never trust raw L2A as an aquatic product."),
         ("NDCI separates clear water from bloom", "and exposes the north–south nutrient gradient."),
         ("A +2 °C heatwave removes ~0.3 mg/L O₂", "— enough, with night-time respiration, to drive the 2021 anoxia.")],
        ("module 1 / fin", "satellite data extraction"))),
]


# =========================================================================
# MODULE 2 — In-situ integration & ML
# =========================================================================
F2 = ("module 2", "in-situ + machine learning")

MODULE2 = [
    ("cover", (
        "Module 02 · notebook 02_insitu_timeseries_ml",
        "From buoys to<br>early warning.",
        "Step by step: validate the satellite against the buoy network, then learn "
        "to predict and flag the lagoon's crises — with honest statistics.",
        [("5", "buoy stations"), ("18k", "daily records"),
         ("2", "honest CV schemes"), ("42 d", "best lead time")],
        ("module 2 / 00", "in-situ + machine learning · 70 min"))),

    ("divider", (
        "Part 1 — the ground truth",
        "What the agency saw in real time.",
        "Daily buoy data (CARM/IMIDA) and watershed hydrology (CHS-SAIH) — the "
        "truth the satellite must agree with.",
        F2)),

    ("concept", (
        "§ 1 — the in-situ networks",
        "Where the data lives",
        "<table class='mini'><tr><th>Source</th><th>What</th></tr>"
        "<tr><td><strong>CARM Mar Menor</strong></td><td>T, S, chl-a, DO, turbidity sondes</td></tr>"
        "<tr><td><strong>IMIDA / SIAM</strong></td><td>agro-meteorology, nitrate proxies</td></tr>"
        "<tr><td><strong>CHS-SAIH</strong></td><td>watershed rain &amp; runoff</td></tr>"
        "<tr><td><strong>CMEMS INS-TAC</strong></td><td>aggregated Med in-situ obs</td></tr></table>",
        "<p class='lede'>Our cached file mimics CARM exports: five stations, daily, "
        "2016–2025, six variables.</p>"
        "<p style='margin-top:.6rem;'>The upstream agricultural data is what "
        "ultimately drives the lagoon — keep that causal chain in view.</p>",
        F2)),

    ("step", (
        "§ 1 — step 1 · the 2021 hypoxia",
        "Dissolved oxygen crashes below 2 mg/L",
        "<p>Plot DO at the worst stations against the <strong>2 mg/L hypoxia "
        "line</strong>, SST overlaid. This is the chart behind the fish-kill "
        "headlines.</p>",
        "focus = insitu.query(\n"
        "  \"station_id in ['MM01','MM02','MM05'] and \"\n"
        "  \"'2021-07-01' <= date <= '2021-10-15'\")\n"
        "ax.axhline(2.0, color='red', ls=':')  # hypoxia",
        "mod2_01.png", F2)),

    ("step", (
        "§ 1 — step 2 · the 2019 DANA",
        "Rain → nitrate → salinity, a cascade",
        "<p>A cut-off cold drop dumped 300+ mm in 48 h. The buoys show salinity "
        "dropping ~4 PSU as nitrate spikes ten-fold — the watershed plume entering "
        "the lagoon.</p>",
        "dana = insitu.query(\"'2019-08-15'<=date<='2019-11-30'\")\n"
        "ws   = pd.read_csv(DATA/'watershed_forcing.csv')\n"
        "# precip (top) | nitrate (mid) | salinity (bottom)",
        "mod2_02.png", F2)),

    ("divider", (
        "Part 2 — validation",
        "Does the satellite agree with the water?",
        "Co-locate each satellite point with its nearest buoy and score the "
        "retrieval the way an ocean-colour paper would.",
        F2)),

    ("step", (
        "§ 2 — match-ups",
        "Satellite vs in-situ chlorophyll",
        "<p>Pair each S2 point with its nearest buoy (within 4 km, same day). "
        "Report R², RMSE and RMSLE (log form — chl-a is log-normal), and always "
        "draw the <strong>1:1 line</strong>.</p>",
        "m = matchup.dropna()\n"
        "rmse  = mean_squared_error(x, y) ** 0.5\n"
        "rmsle = mean_squared_error(\n"
        "    np.log1p(x), np.log1p(y)) ** 0.5\n"
        "r2    = r2_score(x, y)",
        "mod2_03.png", F2)),

    ("divider", (
        "Part 3 — machine learning, honestly",
        "Two cross-validations, two questions.",
        "A gradient-boosting regressor predicts chl-a from reflectances — but how "
        "we validate it decides whether the result is trustworthy.",
        F2)),

    ("concept", (
        "§ 3 — honest cross-validation",
        "Time CV looks easy; space CV is the truth",
        "<table class='mini'><tr><th>Scheme</th><th>Question</th><th>R²</th></tr>"
        "<tr><td>TimeSeriesSplit</td><td>predict future dates?</td><td>high</td></tr>"
        "<tr><td>GroupKFold by station</td><td>predict an unseen station?</td><td>≈ 0.17</td></tr></table>"
        "<p style='margin-top:.7rem;'>The gap is the lesson.</p>",
        "<p class='lede'>A model can look great in time yet be weak in space. "
        "When you talk about deploying somewhere new, <strong>report the "
        "unseen-station number</strong>, not the easy one.</p>",
        F2)),

    ("step", (
        "§ 3 — feature importance",
        "What the model leans on",
        "<p>Refit on all data and inspect the gradient-boosting importances. "
        "Red-edge bands and the band ratios dominate — the physics and the model "
        "agree.</p>",
        "model = GradientBoostingRegressor(\n"
        "    n_estimators=600, max_depth=4,\n"
        "    learning_rate=0.05)\n"
        "model.fit(X, y)\n"
        "imp = pd.Series(model.feature_importances_, FEATS)",
        "mod2_04.png", F2)),

    ("divider", (
        "Part 4 — anomaly detection",
        "An early warning that never peeks.",
        "Multivariate anomalies across six variables — trained only on the quiet "
        "years, judged out-of-sample.",
        F2)),

    ("step", (
        "§ 4 — Isolation Forest",
        "Trained on quiet years, applied forward",
        "<p>Fit on the calm <strong>2017–2018</strong> baseline only, then apply "
        "to 2019+. Every later flag is genuinely out-of-sample — otherwise the "
        "detector just learns the crises as normal.</p>",
        "train = sm.query(\"date < '2019-01-01'\")\n"
        "iso = IsolationForest(n_estimators=300,\n"
        "    contamination=0.03).fit(train[FEATURES])\n"
        "sm['anomaly'] = iso.predict(sm[FEATURES])",
        "mod2_05.png", F2)),

    ("concept", (
        "§ 4 — lead time vs detection delay",
        "Two opposite outcomes, never merged",
        "<table class='mini'><tr><th>Crisis</th><th>First flag</th><th>Outcome</th></tr>"
        "<tr><td>2019 DANA</td><td>−42 days</td><td>early warning</td></tr>"
        "<tr><td>2021 anoxia</td><td>+2 days</td><td>late (a miss)</td></tr>"
        "<tr><td>2025 bloom</td><td>+1 day</td><td>late (a miss)</td></tr></table>",
        "<p class='lede'>A flag <strong>before</strong> the start is lead time — a "
        "win. A flag <strong>after</strong> is detection delay — a miss. Lumping "
        "them together is how monitoring papers oversell themselves.</p>",
        F2)),

    ("takeaways", (
        "§ — what to walk away with",
        "Module 2 in four lines.",
        [("Validate before you model.", "Match-ups with R²/RMSE/bias and a 1:1 line."),
         ("Time CV ≠ space CV.", "Report the unseen-station score, not just the easy one."),
         ("Early warning trains on quiet years", "and must be judged out-of-sample."),
         ("Lead time and detection delay are opposites.", "Only a flag before onset is a real warning.")],
        ("module 2 / fin", "in-situ + machine learning"))),
]


# =========================================================================
# MODULE 3 — Build your own database
# =========================================================================
F3 = ("module 3", "from zero to pro")

MODULE3 = [
    ("cover", (
        "Module 03 · notebook 03_build_database",
        "Build your own<br>data pipeline.",
        "Step by step and live: discover, download, clean, store in SQLite + "
        "Parquet, and turn it into a pollution study — for any coast.",
        [("8", "free sources"), ("3 %", "of a scene pulled"),
         ("SQL", "+ Parquet store"), ("21", "steps")],
        ("module 3 / 00", "from zero to pro · 90 min"))),

    ("divider", (
        "The whole pipeline",
        "Six steps, like a kitchen.",
        "Grocery run → wash → chop → fridge → cook → run the restaurant. Every "
        "section of the notebook maps to one step.",
        F3)),

    ("concept", (
        "§ 0 — the data landscape",
        "Know the archive, know the login",
        "<table class='mini'><tr><th>Source</th><th>Login?</th></tr>"
        "<tr><td>NASA GIBS (true-colour)</td><td>none</td></tr>"
        "<tr><td>Earth Search → AWS COG</td><td>none</td></tr>"
        "<tr><td>Open-Meteo Air-Quality</td><td>none</td></tr>"
        "<tr><td>Open-Meteo Marine</td><td>none</td></tr>"
        "<tr><td>Copernicus CDSE / SH</td><td>free acct</td></tr></table>",
        "<p class='lede'>Prototype today with the four no-login sources; graduate "
        "to a free Copernicus account when you need server-side processing or the "
        "full archive.</p>"
        "<p style='margin-top:.6rem;'>The pattern never changes: "
        "<strong>discover → request a subset → get an array/table</strong>.</p>",
        F3)),

    # ---- Part 1: live downloads ----
    ("divider", (
        "Part 1 — discover &amp; download, live",
        "Watch real data arrive.",
        "Four downloads you run in the room, no credentials. Each degrades "
        "gracefully if you're offline.",
        F3)),

    ("step", (
        "§ 1.1 — NASA GIBS",
        "A satellite snapshot for any date",
        "<p>One URL → a true-colour PNG of the lagoon, any day since 2000. This is "
        "how you <strong>browse</strong> for cloud-free dates before a heavy "
        "download.</p>",
        "url = ('https://gibs.earthdata.nasa.gov/wms/'\n"
        "  ...'&LAYERS=MODIS_Terra_...TrueColor'\n"
        "  f'&TIME={DATE}')\n"
        "img = mpimg.imread(BytesIO(requests.get(url)...))",
        "mod3_01.png", F3)),

    ("step", (
        "§ 1.2 — Sentinel-2 COG window",
        "10 m bands, only the AOI",
        "<p>Search the public STAC, open the COG header <strong>without "
        "downloading</strong>, then read only the AOI window — ~8 MB, 3 % of the "
        "scene.</p>",
        "with rasterio.open(b04_href) as src:\n"
        "    win = from_bounds(*aoi_utm,\n"
        "        transform=src.transform)\n"
        "    red = src.read(1, window=win)\n"
        "# ~8 MB instead of ~240 MB",
        "mod3_02.png", F3)),

    ("step", (
        "§ 1.3 — Open-Meteo Air-Quality",
        "Pollution data for the lagoon",
        "<p>A keyless API returns hourly <strong>PM2.5, PM10, ozone</strong> for "
        "any coordinate. Direct pollution context — one GET, one DataFrame.</p>",
        "url = ('https://air-quality-api.open-meteo.com'\n"
        "  f'/v1/air-quality?latitude={lat}&longitude={lon}'\n"
        "  '&hourly=pm10,pm2_5,ozone&past_days=7')\n"
        "aq = pd.DataFrame(requests.get(url).json()['hourly'])",
        "mod3_03.png", F3)),

    ("step", (
        "§ 1.4 — Open-Meteo Marine",
        "Live sea-surface temperature",
        "<p>Same pattern, a different endpoint: hourly SST for any point — a free "
        "complement to the Sentinel-3 cube of Module 1.</p>",
        "url = ('https://marine-api.open-meteo.com/v1/'\n"
        "  f'marine?latitude={lat}&longitude={lon}'\n"
        "  '&hourly=sea_surface_temperature&past_days=10')\n"
        "sst = pd.DataFrame(requests.get(url).json()['hourly'])",
        "mod3_04.png", F3)),

    # ---- Copernicus account ----
    ("divider", (
        "Part 1.5 — your free Copernicus account",
        "Unlock server-side processing.",
        "Register in class, paste your API key, and the server computes products "
        "for you — no raw-band downloads.",
        F3)),

    ("concept", (
        "§ 1.5 — register &amp; authenticate",
        "Three minutes, then paste your key",
        "<h3>① Register</h3><p><code>dataspace.copernicus.eu</code> → Register → "
        "confirm email. Free, ~30k units/month.</p>"
        "<h3 style='margin-top:.5rem;'>② OAuth client</h3><p>Sentinel Hub dashboard "
        "→ User settings → OAuth clients → Create. Copy the ID + secret.</p>"
        "<h3 style='margin-top:.5rem;'>③ Paste &amp; run</h3><p>The cell prompts you; "
        "the secret box is hidden.</p>",
        "<pre class='code'><span class='c'># run -&gt; paste when prompted</span>\n"
        "CID  = input(<span class='s'>\"Client ID: \"</span>)\n"
        "CSEC = getpass.getpass(<span class='s'>\"Secret: \"</span>)\n\n"
        "TOKEN = cdse_token(CID, CSEC)\n"
        "<span class='c'># every CDSE cell now runs live</span></pre>",
        F3, ("edit", "EDIT — paste your key"))),

    ("step", (
        "§ 1.5 — Process API",
        "On-demand NDCI map, any date",
        "<p>Send a tiny <strong>evalscript</strong> (what each pixel should be) "
        "plus a date; CDSE runs it server-side and returns a ready NDCI array. No "
        "band downloads.</p>",
        "EVALSCRIPT = '''//VERSION=3\n"
        "function evaluatePixel(s){\n"
        "  return [(s.B05-s.B04)/(s.B05+s.B04)];}'''\n"
        "tif = process_ndci(TOKEN, BBOX, '2021-09-12')",
        "mod3_05.png", F3)),

    ("step", (
        "§ 1.5 — image + raw bands",
        "True-colour AND the numbers",
        "<p>The same API returns a real <strong>true-colour image</strong> and the "
        "<strong>raw per-band reflectance</strong> — read the chlorophyll "
        "signature straight off the spectrum.</p>",
        "# B02..B08 as FLOAT32, plus dataMask\n"
        "with rasterio.open(BytesIO(tif)) as src:\n"
        "    a = src.read()          # (6, H, W)\n"
        "mean_reflectance = a[:5][:, mask].mean(1)",
        "mod3_06.png", F3)),

    ("step", (
        "§ 1.5 — Statistical API",
        "A whole time series, zero images",
        "<p>The real game-changer: one request returns mean NDCI <strong>every 10 "
        "days</strong> over the AOI — downloading no imagery at all. This is how "
        "you run a monitoring dashboard cheaply.</p>",
        "js = stats_ndci(TOKEN, BBOX,\n"
        "    '2021-06-01', '2021-10-31', interval='P10D')\n"
        "ts = pd.DataFrame(parse(js))  # 15 dates, 0 downloads",
        "mod3_08.png", F3)),

    # ---- Parts 2-4: build the DB ----
    ("divider", (
        "Parts 2–4 — clean, extract, store",
        "Turn pixels into a database.",
        "Mask the bad pixels, reshape to tidy rows, and load them into SQLite — "
        "typed, indexed and idempotent.",
        F3)),

    ("concept", (
        "§ 2–3 — clean &amp; extract",
        "Only trustworthy pixels, tidy shape",
        "<p class='lede'>Raw pixels aren't observations. Keep only lagoon water, "
        "drop clouds, then reshape to long format: one row per "
        "(date, variable, zone, value).</p>",
        "<pre class='code'>valid = WATER_MASK & (b04&gt;30) & (b04&lt;800)\n"
        "ndci  = (b05-b04)/(b05+b04)\n\n"
        "rows.append({<span class='s'>'date'</span>:date,\n"
        "  <span class='s'>'variable'</span>:<span class='s'>'ndci'</span>, <span class='s'>'zone'</span>:zone,\n"
        "  <span class='s'>'value'</span>:np.ma.median(ndci[sel])})</pre>",
        F3, ("run", "RUN"))),

    ("concept", (
        "§ 4 — the schema",
        "SQLite for queries, Parquet for bulk",
        "<p class='lede'>The <code>UNIQUE</code> constraint + <code>INSERT OR "
        "REPLACE</code> make every re-run <strong>idempotent</strong> — no "
        "duplicates, safe to schedule.</p>"
        "<p>Millions of per-pixel values go to Parquet, referenced from the DB.</p>",
        "<pre class='code'><span class='k'>CREATE TABLE</span> observations(\n"
        "  obs_id   INTEGER PRIMARY KEY,\n"
        "  date     TEXT, source TEXT,\n"
        "  variable TEXT, zone   TEXT,\n"
        "  value    REAL,\n"
        "  UNIQUE(date,source,variable,zone));</pre>",
        F3, ("run", "RUN"))),

    # ---- Part 5: analyse ----
    ("divider", (
        "Part 5 — the pollution study",
        "Answers, straight from SQL.",
        "With everything in the database, monitoring questions become one query "
        "each.",
        F3)),

    ("step", (
        "§ 5 — trend &amp; exceedance",
        "The study, generated from the DB",
        "<p>Monthly-mean chl-a, a robust <strong>Theil-Sen trend</strong>, and the "
        "share of 'poor status' days per year. The exceedance counts spike in "
        "exactly 2019 and 2021.</p>",
        "monthly = pd.read_sql('''\n"
        "  SELECT substr(date,1,7) AS month,\n"
        "         AVG(value) AS chla\n"
        "  FROM observations WHERE variable='chla_mg_m3'\n"
        "  GROUP BY month''', con)",
        "mod3_09.png", F3)),

    ("step", (
        "§ 5 — the satellite ↔ in-situ join",
        "One query across two sources",
        "<p>Load the in-situ series into a table and <strong>JOIN</strong> it to "
        "the satellite series by month — the match-up of a validation paper, in "
        "SQL. r = 0.99.</p>",
        "compare = pd.read_sql('''\n"
        "  SELECT m.month, m.chla_satellite, i.chla_mg_m3\n"
        "  FROM (...) m\n"
        "  JOIN insitu_monthly i ON m.month = i.month''', con)",
        "mod3_10.png", F3)),

    ("takeaways", (
        "§ — what to walk away with",
        "Module 3 in four lines.",
        [("Discover → subset → array/table", "is the same pattern for every source."),
         ("Move as few pixels as possible.", "COG windows + the server-side Statistical API."),
         ("Clean before you store; store tidy.", "Idempotent SQLite + Parquet scales to a scheduled job."),
         ("The SQL transfers", "to PostGIS / DuckDB. Swap the AOI and the database builds itself.")],
        ("module 3 / fin", "from zero to pro"))),
]
