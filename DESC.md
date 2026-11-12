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
1. Open your PostgreSQL command-line utility (`psql`) or a graphical GUI like **pgAdmin**.
2. Run the following command to create a new database named `urbanheat`:
   ```sql
   -- Create the main database instance
   CREATE DATABASE urbanheat;
   ```
3. Connect to your new `urbanheat` database.
4. Execute the SQL schema creation script provided in this toolkit:
   * Using command-line psql:
     ```bash
     # Execute schema file on the database
     psql -U postgres -d urbanheat -f Database/schema.sql
     ```
   * Or simply open `Database/schema.sql` in pgAdmin's Query Tool, select all code, and click **Execute**.

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
     ```powershell
     # Activate powershell
     venv\Scripts\Activate.ps1
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
With your virtual environment activated, install all required GIS, database, and backend libraries:
```bash
# Install core web service, ORM, database adapters, and GIS math dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary geopandas rasterio shapely pandas numpy
```

### Step 5: Start the FastAPI Backend Server
1. Activate your virtual environment (if not already done).
2. Start the FastAPI development web service on port 8000:
   ```bash
   # Run the server using uvicorn with hot-reload enabled
   uvicorn Backend.app:fastapi_application_instance --reload --port 8000
   ```
3. Open your browser and navigate to: `http://127.0.0.1:8000/`
   * You should see a JSON welcome response indicating that the backend service is online.
   * You can explore the interactive API Documentation panel at: `http://127.0.0.1:8000/docs`

### Step 6: Launch and Test the Frontend Dashboard
1. Go to your file browser and locate the file: `Frontend/index.html`
2. Double-click to open it in your web browser.
3. The dashboard will automatically detect that your FastAPI backend is running locally.
4. Notice the header banner transitions to a green **"Database Connected"** badge.
5. Move the weight sliders and click **"Apply weights & Recalculate"**. The frontend will now call your FastAPI REST endpoint, which Queries PostGIS and runs calculations on the Python backend!

### Step 7: Run the Spatial ETL Data Loader (When Datasets are Ready)
Once you download your USGS surface temperatures, USDA canopy, and Census block shapefiles:
1. Open `Scripts/urban_heat_etl_analysis.py` in an editor.
2. Edit the raw file paths to point to your local downloaded files.
3. Run the ETL process script:
   ```bash
   # Execute the ETL loading script to write raw layers into PostgreSQL
   python Scripts/urban_heat_etl_analysis.py
   ```
4. The script will write processed values directly into your PostGIS database tables, making them immediately queryable by the FastAPI Backend!

---

## Coding Standards Applied

* **Verbose and Clear Variables**: Names throughout Python, JavaScript, and SQL (e.g., `calculated_final_mitigation_priority_score`) are explicitly defined for clarity.
* **Block Comments Placement**: All inline documentation is written directly **above** the line or block of code it describes.
* **Zero Software Installations**: Designed to run immediately with native tools and CDN assets.
