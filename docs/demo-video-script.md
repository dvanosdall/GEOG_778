# Final Demonstration Video Script & Recording Guide

**Target Duration:** 5:30 – 6:30 (strictly within the **5–7 minute** specification)  
**Format:** Screen recording via **Zoom** (MP4 upload or YouTube unlisted/public URL)  
**Project:** Omaha Urban Heat Mitigation Decision-Support Toolkit (`GEOG 778, Fall 2026`)

---

## Pre-Recording Checklist (What to Have Open Before You Hit Record)

1. **Close clutter**: Turn off desktop notifications; close unrelated browser tabs and DevTools (`F12`).
2. **Verify your backend & database are running** (so the header badge shows green **"Database Connected"**):
   * PostgreSQL/PostGIS running with `GEOG_778` populated.
   * FastAPI running (`uvicorn Backend.app:fastapi_application_instance --reload --port 8000`).
3. **Open 3 clean tabs/windows ready to switch between**:
   * **Tab 1 (Primary):** `Frontend/index.html` loaded in your browser (with the **Kepler.gl Legend** icon on the top-left of the map expanded so the Light-to-Dark Purple legend is visible!).
   * **Tab 2:** `docs/architecture.png` (or `docs/executive-summary.md` showing the architecture diagram).
   * **Tab 3:** VS Code / editor showing `Database/schema.sql`, `Scripts/urban_heat_etl_analysis.py`, or `Backend/app.py` (for the quick 45-second technical/GIS&T BoK walkthrough).
4. **Zoom Recording Setup**:
   * Start a new Zoom meeting with just yourself → **Share Screen** (select your primary monitor or browser window) → **Record on this Computer** (saves an `.mp4` locally).
   * Do a 10-second mic check first to confirm audio is clear.

---

## Timed Script & On-Screen Actions (Target: ~6 Minutes)

### [0:00 – 0:50] 1. Introduction, Problem & Intended Audience (~50 sec)
* **[SCREEN]**: Start on **Tab 1** (`Frontend/index.html` dashboard showing Omaha / Douglas County shaded in the Light-to-Dark Purple gradient). Point your cursor to the title, the green **"Database Connected"** badge, and pan slightly over Omaha.
* **[SAY]**:
  > "Hi everyone, I'm David Vanosdall, and this is my GEOG 778 capstone project: the **Omaha Urban Heat Mitigation Decision-Support Toolkit**.
  >
  > Extreme urban heat is a major public health and infrastructure challenge across Omaha and Douglas County. While cities have access to satellite heat data, tree canopy data, and census demographics, a standalone heat map doesn't tell planners *why* a neighborhood is a priority, *what* physical intervention fits best, or *how* priorities shift under different policy goals.
  >
  > I built this toolkit for **municipal planners, urban foresters, sustainability coordinators, and GIS professionals** so they can move beyond static maps and interactively explore those trade-offs."

---

### [0:50 – 1:50] 2. Architecture, Data & GIS&T Body of Knowledge (~60 sec)
* **[SCREEN]**: Switch to **Tab 2** (`docs/architecture.png` diagram) for ~25 seconds, then briefly show **Tab 3** (`Database/schema.sql` and `Backend/app.py`) for ~35 seconds.
* **[SAY]**:
  > "From a technical standpoint, this project integrates all five core Knowledge Areas of the **GIS&T Body of Knowledge**:
  > * **Data Management (DM)** and **Domain Applications (DA)**: Using a Python ETL pipeline with GeoPandas, Rasterio, and Shapely, I standardized five public datasets to WGS 84—USGS Landsat 9 Land Surface Temperature, USDA Forest Service Tree Canopy Cover, MRLC NLCD Imperviousness, IPUMS NHGIS Census ACS demographics, and local DOGIS context—and stored them in **PostgreSQL with PostGIS** using GIST spatial indexes.
  > * **Programming and Development (PD)**: A **FastAPI** Python backend queries PostGIS and serves real-time Multi-Criteria Decision Analysis calculations to a **React, Redux, and Kepler.gl** web frontend—with an automatic offline browser fallback if the API is ever unreachable.
  > * **Cartography and Visualization (CV)**: Notice on the map that I used a **Light-to-Dark Purple sequential palette** instead of a traditional red-yellow-green ramp. This ensures the choropleth is **colorblind-safe** and maintains crisp contrast against the dark basemap."

---

### [1:50 – 3:15] 3. Live Feature Walkthrough: Inspection & Transparency (~85 sec)
* **[SCREEN]**: Switch back to **Tab 1** (`Frontend/index.html`).
  * Hover slowly over 2–3 different block groups so the **yellow border highlight** appears and **Section 3: Focus Area Inspection** updates live.
  * Click one high-priority (dark purple) block group to lock it. Point to each row in Section 3, especially **`Vulnerable (<5 / 65+)`** and the green **`Recommended Interventions`** box.
  * Click **`About Toolkit`** at the top-left, scroll down to **`Methodology & Calculations`**, pause 3 seconds, and click **Close**.
* **[SAY]**:
  > "Let's look at how the dashboard works. On the right is the interactive Kepler.gl map with our labeled purple legend. As I hover over different Census Block Groups in Douglas County, the border highlights in yellow and **Section 3: Focus Area Inspection** updates live.
  >
  > Clicking a neighborhood locks it in. Here we can see *why* this area scored high: its FIPS code, Landsat surface temperature in Celsius, tree canopy percentage, impervious surface percentage, total population, and the **`Vulnerable (<5 / 65+)`** breakdown—which combines children under 5 and seniors 65 and older as a percentage of total population.
  >
  > At the bottom, a rule-based heuristic translates those normalized scores into a tailored strategy—such as **Urban Forestry**, **Cool Roof Retrofitting**, **Community Shade Structures & Parks**, or **Pervious Paving**.
  >
  > To keep the math transparent for planners, clicking **About Toolkit** opens the built-in **Methodology & Calculations** guide, documenting the 0-to-100 linear normalization, inverted canopy deficit, Weighted Linear Combination formula, and exact intervention thresholds."

---

### [3:15 – 5:10] 4. Live Scenario Analysis (MCDA Use Cases) (~115 sec)
* **[SCREEN]**: Stay on **Tab 1**. Point to **Section 2: Scenario Statistics** (`Avg Priority Score` and `High Priority Pop`), noting the current numbers before changing sliders.
  * **Scenario A**: Slide **Land Surface Temperature** to `10`, **Impervious Surfaces** to `8`, **Tree Canopy Deficit** to `1`, **Social Vulnerability** to `1`. Click **`Apply weights & Recalculate`**. Wait for the map and cards to update.
  * **Scenario B**: Slide **Tree Canopy Deficit** to `10`, and set the other three sliders to `1`. Click **`Apply weights & Recalculate`**. Hover/click a newly darkened purple zone and point out the intervention callout.
  * **Scenario C**: Slide **Social Vulnerability** to `10`, and set the other three sliders to `1`. Click **`Apply weights & Recalculate`**. Point directly at **`High Priority Pop`** increasing!
  * Click **`Export Scenario GeoJSON`** briefly to show the download works.
* **[SAY]**:
  > "This brings us to **Analytics and Modeling (AM)**—live **Multi-Criteria Decision Analysis** scenario testing. Right now, **Section 2: Scenario Statistics** shows our study-area **Avg Priority Score** and **High Priority Pop**, which counts the exact number of residents living in focus zones scoring 60 or higher.
  >
  > Let's test three real-world planning scenarios:
  > * **First, 'Extreme Urban Heat Islands First'**: I'll set Temperature to 10 and Impervious Surfaces to 8, keeping the others at 1, and click **Apply weights & Recalculate**. Notice how the deep purple hotspots concentrate in Omaha's dense commercial and industrial corridors where asphalt traps heat, recommending **Cool Roofs** and **Pervious Paving**.
  > * **Second, 'Urban Forestry & Green Equity'**: I'll set Tree Canopy Deficit to 10 and the others to 1, then recalculate. Now the priority map shifts to neighborhoods lacking shade, guiding arborists toward **Urban Forestry & Tree Canopy Expansion**.
  > * **Third, 'Socio-Environmental Vulnerability'**: I'll set Social Vulnerability to 10 and the others to 1, and recalculate. Watch **High Priority Pop** jump—proving how emphasizing vulnerable age cohorts targets denser residential neighborhoods and surfaces **Community Shade Structures & Parks** where residents need cooling most.
  >
  > Finally, planners can click **Export Scenario GeoJSON** at any time to download the active weighted results for further work in QGIS or ArcGIS Pro."

---

### [5:10 – 6:00] 5. Conclusion, Limitations & Future Work (~50 sec)
* **[SCREEN]**: Stay on **Tab 1** (or switch briefly back to **Tab 2** `architecture.png` for a clean closing visual).
* **[SAY]**:
  > "To wrap up, this toolkit demonstrates a full-stack geospatial workflow from raw satellite and census data in PostGIS to an accessible, interactive decision-support web app.
  >
  > Key limitations include the Modifiable Areal Unit Problem from aggregating 30-meter rasters to block groups, reliance on a single peak-summer Landsat snapshot, and the lack of parcel-level planting or utility constraints. In the future, I'd like to add side-by-side scenario comparison, parcel-level right-of-way screening, and nighttime air-temperature data.
  >
  > Thank you for watching, and I welcome any questions or feedback."

---

## Post-Recording Submission Checklist
* Check video length: verify the `.mp4` is between **5:00 and 7:00** minutes.
* Scrub through the video to confirm audio is clear, text on screen is readable, and no sensitive passwords/tokens are visible.
* Upload the `.mp4` directly to Canvas **or** upload to YouTube (Unlisted or Public) and submit the URL.
