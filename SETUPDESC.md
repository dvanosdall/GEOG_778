# Omaha Urban Heat Mitigation Decision-Support Toolkit

This repository contains a GIS-based decision-support toolkit for urban heat mitigation planning in Omaha, Nebraska. It integrates environmental, demographic, land cover, and local geographic information to identify areas where specific heat mitigation strategies are most appropriate.

---

## Project Directory Structure

```text
C:\Work\UrbanHeat\
├── AGENTS.md                   # This file, documenting project architecture and workflow
├── Database/
│   └── schema.sql              # SQL script defining PostgreSQL/PostGIS schemas, tables, and spatial indexes
├── Docs/
│   ├── Vanosdall-MockupUserTesting.pdf
│   ├── Vanosdall-Omaha_Urban_Heat_Project_Plan.pdf
│   └── project-proposal.md     # Primary project requirements and proposal specifications
├── Frontend/
│   └── index.html              # Standalone, interactive Kepler.gl + React dashboard with live scoring
├── Backend/
│   └── app.py                  # FastAPI REST web service connecting PostgreSQL/PostGIS and computing MCDA
└── Scripts/
    └── urban_heat_etl_analysis.py # Python ETL and Multi-Criteria Decision Analysis (MCDA) pipeline
```

---

## Technical Components

### 1. Spatial Database Setup (`Database/schema.sql`)
The PostgreSQL/PostGIS database schema includes:
* **PostGIS Extensions**: Enables spatial geometry and raster analysis.
* **Tables & Spatial Indexes**:
  * `omaha_study_area_boundary`: Study area boundary (EPSG:4326).
  * `land_surface_temperature_rasters`: Satellite LST raster data.
  * `tree_canopy_cover_grid_cells`: Vector polygon grid with canopy coverage percentages.
  * `impervious_surface_grid_cells`: NLCD developed impervious surface density grid.
  * `census_block_group_demographics`: Census Tract population metrics (including vulnerable age counts).
  * `multi_criteria_planning_scenarios`: Stored weight configurations.
  * `urban_heat_mitigation_priority_results`: Calculated priority ratings and mitigation recommendations per scenario and zone.

### 2. FastAPI Web Service Backend (`Backend/app.py`)
Provides a Python-based REST API to serve spatial data and manage calculations:
* **CORS Enabled**: Configured to accept cross-origin requests, allowing local HTML files to connect securely.
* **MCDA Endpoint**: Computes real-time Multi-Criteria Decision Analysis dynamically.
* **Scenario Management**: Enables saving and retrieving planning weight combinations.
* **Robust Fallbacks**: Automatically generates simulated Omaha spatial geometries if PostgreSQL connection is absent.

### 3. Python Spatial ETL & MCDA Analysis (`Scripts/urban_heat_etl_analysis.py`)
Provides the core data preparation and analytical modeling functions:
* **Data Ingestion**: Stubs for loading raster files (`rasterio`) and vector shapes (`geopandas`).
* **Zonal Statistics**: Extracts average surface temperatures across census boundaries.
* **Normalization**: Linear mapping of raw attributes to a standardized 0.0 to 100.0 priority index.
* **MCDA Scoring**: Integrates normalized scores weighted according to planning assumptions.
* **Heuristics Recommendations**: Suggests targeted mitigation strategies based on spatial data conditions.

### 4. Interactive Web Dashboard (`Frontend/index.html`)
A standalone React and Redux client implementing Kepler.gl maps via CDN:
* **Dual Operation Modes**:
  * **Offline Mockup Mode**: Runs instantly in any browser when opened locally (no database required).
  * **Connected API Mode**: Automatically detects a running local FastAPI server, flashing green as "Database Connected", and queries PostgreSQL/PostGIS.
* **Interactive Controls**: Side sliders adjust criteria weights. Clicking "Apply weights" recalculates priorities dynamically and recolors the map choropleth.
* **Focus Area Inspector**: Click on any map polygon zone to inspect its raw values and recommended interventions.
* **Scenario Exports**: Download computed results immediately as a GeoJSON file.

---

## Step-by-Step Installation and Setup Guide
Follow these steps to deploy, run, and test the complete stack on a system with full internet and local software access.

### Step 1: Install System Prerequisites
Download and install the following software for your platform (Windows/macOS/Linux):
1. **PostgreSQL Database Server** (version 13 or newer recommended): [PostgreSQL Downloads](https://www.postgresql.org/download/)
2. **PostGIS Extension Bundle**:
   * On Windows: Open the "Application Stack Builder" utility packaged with your PostgreSQL installation, navigate to "Spatial Extensions", and select **PostGIS**.
   * On macOS: Use Postgres.app or Homebrew (`brew install postgis`).
3. **Python** (version 3.9 or newer recommended): [Python Downloads](https://www.python.org/downloads/)

### Step 2: Set Up the PostgreSQL/PostGIS Database
1. Connect to your PostgreSQL database server (typically **`localhost`** on your own computer) using command-line `psql` or pgAdmin.
2. Run the following command to create a new database named `GEOG_778` (or `urbanheat`, depending on your preference):
   ```sql
   -- Create the main database instance
   CREATE DATABASE GEOG_778;
   ```
3. Connect to your new database.
4. Execute the SQL schema creation script provided in this toolkit to create all tables, keys, and spatial indexes:
   * Using command-line psql:
     ```bash
     # Execute schema file on your database server (replace user, host, database as needed)
     psql -U postgres -h localhost -d GEOG_778 -f Database/schema.sql
     ```
   * Or simply open `Database/schema.sql` in pgAdmin's Query Tool, connect to your local server, select all code, and click **Execute**.

### Step 3: Set Up the Python Virtual Environment
1. Open a terminal or PowerShell console and navigate to the project directory:
   ```bash
   # Navigate to root directory
   cd C:\Work\UrbanHeat
   ```
2. Create a clean virtual environment:
   ```bash
   # Create environment
   python -m venv venv
   ```
3. Activate the virtual environment:
   * On Windows (PowerShell):
     If Windows blocks the script execution, run the bypass command first:
     ```powershell
     # Bypasses execution policy restrictions for the current PowerShell terminal session
     Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

     # Activate the virtual environment
     .\venv\Scripts\Activate.ps1
     ```
   * On Windows (Command Prompt):
     ```cmd
     :: Activate cmd
     venv\Scripts\activate.bat
     ```
   * On macOS/Linux:
     ```bash
     # Activate Unix shell
     source venv/bin/activate
     ```

### Step 4: Install Python Dependencies
With your virtual environment activated, install all required GIS, database, and backend libraries using the provided `requirements.txt` file:
```powershell
# Install all required Python packages
pip install -r requirements.txt
```

### Step 5: Start the FastAPI Backend Server
1. Activate your virtual environment (if not already done).
2. Configure your database connection string to point to your database server (typically `localhost`). Set the `DATABASE_URL` environment variable before running the server:
   * On Windows (PowerShell):
     ```powershell
     # Set the database URL environment variable (replace user, password, database, port as needed)
     $env:DATABASE_URL="postgresql://postgres:admin@localhost:5432/GEOG_778"
     ```
   * On Windows (Command Prompt):
     ```cmd
     :: Set the database URL environment variable
     set DATABASE_URL=postgresql://postgres:admin@localhost:5432/GEOG_778
     ```
   * On macOS/Linux:
     ```bash
     # Set the database URL environment variable
     export DATABASE_URL="postgresql://postgres:admin@localhost:5432/GEOG_778"
     ```
3. Start the FastAPI development web service on port 8000 using one of these options:
   * **Option A: Standard Command (If Activated)**
     * On Windows (PowerShell):
       ```powershell
       # Start the server with hot-reload enabled
       uvicorn Backend.app:fastapi_application_instance --reload --port 8000
       ```
     * On Windows (Command Prompt) / macOS / Linux:
       ```bash
       # Start the server
       uvicorn Backend.app:fastapi_application_instance --reload --port 8000
       ```
   * **Option B: Direct Python Execution (Bypasses uvicorn command path issues)**
     * On Windows (PowerShell):
       ```powershell
       # Run uvicorn as a module using the virtual environment's python executable
       .\venv\Scripts\python.exe -m uvicorn Backend.app:fastapi_application_instance --reload --port 8000
       ```
     * On Windows (Command Prompt):
       ```cmd
       :: Run uvicorn directly
       venv\Scripts\python.exe -m uvicorn Backend.app:fastapi_application_instance --reload --port 8000
       ```
4. Open your browser and navigate to: `http://127.0.0.1:8000/`
   * You should see a JSON welcome response indicating that the backend service is online.
   * You can explore the interactive API Documentation panel at: `http://127.0.0.1:8000/docs`

### Step 6: Launch and Test the Frontend Dashboard
1. Go to your file browser and locate the file: `Frontend/index.html`
2. Double-click to open it in your web browser.
3. The dashboard will automatically detect that your FastAPI backend is running locally.
4. Notice the header banner transitions to a green **"Database Connected"** badge.
5. Move the weight sliders and click **"Apply weights & Recalculate"**. The frontend will now call your FastAPI REST endpoint, which Queries PostGIS and runs calculations on the Python backend!

### Step 7: Load Real-World Geospatial Datasets into PostGIS

Once you download your Landsat surface temperatures, USDA canopy, and Census block shapefiles, follow these steps to process and load them into your PostGIS database:

#### **Option A: High-Performance PostGIS CLI Loaders (Recommended for Rasters)**
PostGIS comes with a built-in command-line tool named **`raster2pgsql`** which is by far the fastest way to load your Landsat LST `.TIF` rasters into PostgreSQL:

1. Place your unzipped Landsat Surface Temperature GeoTIFF (e.g. `LC09_L2SP_028031_20260717_20260718_02_T1_ST_B10.TIF`) inside the **`C:\Work\UrbanHeat\Data\`** folder.
2. Open your terminal and run this pipe command (replace `-h localhost` and `-U postgres` with your actual database host and username):
   ```powershell
   # Convert the summer Landsat temperature GeoTIFF into tiled 256x256 SQL blocks and pipe directly into PostGIS
   raster2pgsql -I -C -M -s 4326 -t 256x256 Data\LC09_L2SP_028031_20260717_20260718_02_T1_ST_B10.TIF public.land_surface_temperature_rasters | psql -h localhost -U postgres -d GEOG_778
   ```

#### **Option B: Python Ingestion Pipeline Script (For Vector Shapefiles)**
For vector datasets (such as Census block group shapefiles and USDA canopy cover polygons), use our unified Python ETL pipeline script:

1. **Census Demographics**: Download TIGER/Line census block group boundary shapefiles joined with ACS population tables (total population, under 5, over 65) via [NHGIS IPUMS](https://www.nhgis.org/). Unzip the files into **`C:\Work\UrbanHeat\Data\`**.
2. **USDA Tree Canopy Cover**: Download the Tree Canopy Cover (TCC) shapefile or raster via the [USDA Forest Service Raster Gateway](https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/). Place the unzipped files into **`C:\Work\UrbanHeat\Data\`**.
3. Open **`Scripts/urban_heat_etl_analysis.py`** in your code editor.
4. Update the path variables in the main block to point directly to your raw downloaded files (e.g. `C:/Work/UrbanHeat/Data/omaha_census_block_groups.shp`).
5. Execute the ETL script within your active virtual environment:
   ```powershell
   # Run the spatial data pipeline to process, reproject, and load your vector layers into PostgreSQL
   python Scripts/urban_heat_etl_analysis.py
   ```

The script will automatically reproject your layers to standard WGS 84 (`EPSG:4326`), calculate spatial metrics, and write them directly into your PostGIS database tables, making them queryable by the FastAPI Backend!

---

## Data Sources & Academic Citations

To maintain academic integrity and standard research attribution guidelines, please use the following official citations when publishing research, reports, or materials derived from this decision-support toolkit:

### 1. Demographic & Boundary Data (IPUMS NHGIS)
For all census geography boundaries (TIGER/Line block groups) and demographic attributes accessed via NHGIS, cite as:

* **Full Academic Citation**:
  > Jonathan Schroeder, David Van Riper, Steven Manson, Grace Cooper, Zachary Krause, Tracy Kugler, Tsu Zhu, and Steven Ruggles. IPUMS National Historical Geographic Information System: Version 21.0 [dataset]. Minneapolis, MN: IPUMS. 2026. http://doi.org/10.18128/D050.V21.0
* **Shorter/Media Citation** (Policy briefs, press, or online resources):
  > IPUMS NHGIS, University of Minnesota, www.nhgis.org

### 2. Land Surface Temperature (USGS Landsat)
For satellite-derived thermal indicators accessed via USGS (specifically the peak-summer Landsat 9 scene `LC09_L2SP_028031_20260717_20260718_02_T1` acquired on July 17, 2026):
* **Academic Citation**:
  > U.S. Geological Survey (USGS). Landsat Collection 2 Level-2 Surface Temperature Product (Science Product) [dataset]. Sioux Falls, SD: USGS Earth Resources Observation and Science (EROS) Center. 2026. https://www.usgs.gov/landsat-missions/landsat-surface-temperature

### 3. Tree Canopy Coverage (USDA Forest Service)
For existing tree canopy metrics:
* **Academic Citation**:
  > USDA Forest Service. Tree Canopy Cover (TCC) [dataset]. Salt Lake City, UT: USDA Forest Service Geospatial Technology and Application Center (GTAC). 2021. https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/

### 4. Developed Imperviousness Density (MRLC NLCD)
For land cover characteristics and developed density variables:
* **Academic Citation**:
  > Multi-Resolution Land Characteristics (MRLC) Consortium. National Land Cover Database (NLCD) [dataset]. Sioux Falls, SD: U.S. Geological Survey. 2021. https://www.mrlc.gov/data

### 5. Local Geographic Context Data (DOGIS)
For local municipal reference layers (streets, municipal boundaries, schools, parks, and landmarks):
* **Academic Citation**:
  > Douglas Omaha Geographic Information Systems (DOGIS). City of Omaha and Douglas County Spatial Data Warehouse [dataset]. Omaha, NE: City of Omaha Planning Department and Douglas County GIS Department. 2026. https://data.dogis.org/

---

## Coding Standards Applied

* **Verbose and Clear Variables**: Names throughout Python, JavaScript, and SQL (e.g., `calculated_final_mitigation_priority_score`) are explicitly defined for clarity.
* **Block Comments Placement**: All inline documentation is written directly **above** the line or block of code it describes.
* **Zero Software Installations**: Designed to run immediately with native tools and CDN assets.

---

## Decision-Support MCDA Weighting & User Interaction Guide

This guide explains how the Multi-Criteria Decision Analysis (MCDA) weighting engine calculates priorities and how you can interact with the toolkit to explore planning scenarios.

### 1. How the MCDA Weighting Engine Works

The toolkit evaluates **four spatial planning criteria** to identify which neighborhoods are in the most urgent need of heat-mitigation interventions:

1. **Land Surface Temperature (LST) [0 - 10]**: Extracted from Landsat 9 thermal infrared band 10. Higher temperatures represent higher priority.
2. **Tree Canopy Deficit [0 - 10]**: Extracted from the USDA Forest Service canopy database. Lower existing canopy coverage (higher deficit) represents higher priority.
3. **Impervious Surfaces [0 - 10]**: Extracted from the NLCD developed land cover database. Higher concrete, roof, and asphalt density represents higher priority.
4. **Social Vulnerability [0 - 10]**: Calculated from the Census ACS demographics. Higher counts of heat-vulnerable age groups (children under 5 and seniors over 65) represent higher priority.

#### The Weighting Mathematics:
When you adjust the sliders on the left, you are assigning raw importance weights to each of the four criteria. The system calculates the final priority score using a **Weighted Linear Combination (WLC)**:

$$\text{Priority Score} = (T_{norm} \times W_{temp}) + (C_{norm} \times W_{canopy}) + (I_{norm} \times W_{imperv}) + (V_{norm} \times W_{vulner})$$

* All raw criteria values are first normalized to a standardized **0.0 to 100.0 scale** ($T_{norm}$, $C_{norm}$, etc.) so they can be mathematically compared.
* The raw slider weights are automatically rescaled to **proportionally sum to exactly 1.0 (100%)** ($W_{temp}$, etc.). This ensures that regardless of what raw numbers you slide, the final score will always fit perfectly on a clean **0.0 to 100.0 scale**.

---

### 2. Planning Scenarios & What to Expect When Sliding

By adjusting the sliders, you are simulating different policy directives:

* **Scenario A: "Extreme Urban Heat Islands First" (Focus on LST & Concrete)**
  * *Slider Settings*: Slide **Temperature** to 10, **Impervious Surfaces** to 8, others to 1.
  * *Expectation*: The map will turn deep red in the heavily developed urban core, industrial corridors, and commercial downtown areas of Omaha where asphalt and steel trap thermal heat.
* **Scenario B: "Urban Forestry & Green Equity" (Focus on Canopy Deficit)**
  * *Slider Settings*: Slide **Tree Canopy Deficit** to 10, others to 1.
  * *Expectation*: Highlights neighborhoods lacking natural shade. This guides urban foresters exactly where to plant new trees to maximize canopy cooling.
* **Scenario C: "Socio-Environmental Vulnerability" (Focus on Demographics)**
  * *Slider Settings*: Slide **Social Vulnerability** to 10, others to 1.
  * *Expectation*: Prioritizes neighborhoods with dense populations of young children and elderly residents, ensuring municipal cooling centers and shade structures protect the most vulnerable people first.

---

### 3. Understanding the Dashboard Card Metrics

The **Section 2: Scenario Statistics** cards provide high-level citywide summaries under your active scenario:

1. **Avg Priority Score (e.g. 54.2 / 100)**:
   * Represents the mathematical average of the priority scores across all 489 block groups in Omaha. 
   * Useful for comparing scenarios: a higher average indicates a scenario with more widespread critical needs, whereas a lower average indicates a more balanced citywide spread.
2. **High Priority Pop (e.g. 84,350 Residents)**:
   * Counts the **total number of residents** living in focus areas that have scored **60.0 or higher** under your current weights.
   * *Strategic Use*: Helps planners quantify the human impact! For example, shifting a slider from Scenario A to Scenario C might increase the "High Priority Pop" from 40k to 90k, proving that Scenario C successfully targets denser, more populated neighborhoods.

---

### 4. Interactive User Help File: How to Use the Map

#### **A. Navigation Controls**
* **Pan (Move around)**: Left-click and drag anywhere on the map.
* **Zoom In / Out**: Use your mouse scroll-wheel, or click the `+` and `-` buttons in the top right corner of the map canvas.
* **Rotate / Tilt**: Right-click and drag up/down to tilt the map into 3D space, or left/right to rotate the compass.

#### **B. Layer & Legend Controls (Left-Hand Panel)**
* Click the small arrow button **`>`** in the top left corner of the map to expand the **Kepler.gl Control Panel**.
* Click the **Layers icon** (the stacked layers page) to see your layers list.
* Click the small **Legend icon** (the list lines) to expand a floating legend showing you exactly what the Yellow-Red colors represent on the map scale.

#### **C. Inspecting Neighborhoods**
* **Hover**: Move your mouse over any neighborhood polygon. A floating tooltip will display its FIPS code, average temperature, canopy cover, and recommended intervention.
* **Click to Inspect**: Left-click on any polygon. This "locks" the neighborhood into **Section 3: Focus Area Inspection** in the right-hand sidebar.
* **Mitigation Recommendation**: Look at the highlighted dark-green callout box in Section 3. It will recommend a specific, targeted physical strategy (such as **`Urban Forestry`**, **`Cool Roof Retrofits`**, or **`Pervious Paving`**) customized precisely for that neighborhood's environmental and social conditions!
