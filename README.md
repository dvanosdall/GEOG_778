# Omaha Urban Heat Mitigation Decision-Support Toolkit

Welcome to the **Omaha Urban Heat Mitigation Decision-Support Toolkit**! This project is an interactive geospatial decision-support application built to help municipal planners, urban foresters, and climate resilience coordinators identify spatial priority zones for urban heat mitigation in Omaha, Nebraska.

The system evaluates multiple environmental and demographic criteria, letting users configure planning scenario weights to see how identified priorities and target interventions change in real-time.

---

## Project Directory Structure

```text
C:\Work\UrbanHeat/
├── README.md                   # This file, with master setup and execution instructions
├── AGENTS.md                   # Agent system specifications and architecture review
├── Database/
│   └── schema.sql              # SQL script defining PostgreSQL/PostGIS schemas and indexes
├── Docs/
│   ├── Vanosdall-MockupUserTesting.pdf
│   ├── Vanosdall-Omaha_Urban_Heat_Project_Plan.pdf
│   └── project-proposal.md     # Primary project requirements and guidelines
├── Backend/
│   └── app.py                  # FastAPI REST API database manager and MCDA calculation service
├── Scripts/
│   └── urban_heat_etl_analysis.py # Python ETL and spatial data processing pipeline
└── Frontend/
    ├── index.html              # Clean, modular index file launching the web dashboard
    ├── css/
    │   ├── variables.css       # Stylesheet defining theme variables and colors
    │   ├── layout.css          # Stylesheet defining structural flexbox layout rules
    │   └── components.css      # Stylesheet defining widgets, sliders, cards, and scrollbars
    └── js/
        ├── data_generator.js   # Script generating dynamic simulated spatial grid features
        ├── mcda_engine.js      # Math engine computing linear MCDA and recommendation rules
        └── app.js              # React engine mounting Kepler.gl and handling REST fetch connections
```

---

## Technical Architecture & Stack

1. **Frontend Presentation**: HTML5, Modular CSS3, and JavaScript compiled with:
   * **React** (v16.14.0) & **Redux** (v4.1.2) for declarative state management.
   * **Kepler.gl** (v2.5.5) & **Mapbox GL** (v1.13.2) loaded via CDN for high-performance canvas mapping.
2. **Backend API**: **FastAPI** (Python >= 3.9) providing REST endpoints for database queries and real-time MCDA calculations.
3. **Database Layer**: **PostgreSQL** with **PostGIS** spatial extensions.
4. **ETL Pipeline**: Python scripts leveraging **GeoPandas**, **Rasterio**, **SQLAlchemy**, and **Shapely** to ingest, reproject, and aggregate raw rasters and shapefiles.

---

## Step-by-Step Setup and Execution Guide

Follow these sequential steps to set up, deploy, and run the complete codebase on a system with full software access.

### Step 1: Install System Requirements
Install the following core packages on your host machine:
1. **PostgreSQL Server** (version 13 or newer): [Download Installer](https://www.postgresql.org/download/)
2. **PostGIS Extension Bundle**:
   * On Windows: Open the "Application Stack Builder" utility packaged with your PostgreSQL installer. Expand "Spatial Extensions" and check **PostGIS**.
   * On macOS: Use Postgres.app or Homebrew (`brew install postgis`).
3. **Python** (version 3.9 or newer): [Download Installer](https://www.python.org/downloads/)

### Step 2: Initialize the PostgreSQL/PostGIS Database
1. Connect to your PostgreSQL database server (typically **`localhost`** on your own computer) using command-line `psql` or pgAdmin.
2. Run the following command to create a new database named `GEOG_778` (or `urbanheat`, depending on your preference):
   ```sql
   -- Create the main database instance
   CREATE DATABASE GEOG_778;
   ```
3. Connect to your new database.
4. Execute the SQL schema script provided in this repository to create all tables, keys, and spatial indexes:
   * Using command-line psql:
     ```bash
     # Execute schema file on your database server (replace user, host, database as needed)
     psql -U postgres -h localhost -d GEOG_778 -f Database/schema.sql
     ```
   * Or simply open `Database/schema.sql` in pgAdmin's Query Tool, connect to your local server, select all code, and click **Execute**.

### Step 3: Create and Activate Python Virtual Environment
1. Open a terminal or PowerShell console and navigate to the project directory:
   ```bash
   # Navigate to the workspace root directory
   cd C:\Work\UrbanHeat
   ```
2. Generate a isolated Python virtual environment:
   ```bash
   # Create a virtual environment folder named 'venv'
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
     :: Activate environment inside Cmd
     venv\Scripts\activate.bat
     ```
   * On macOS/Linux:
     ```bash
     # Activate environment inside Bash/Zsh
     source venv/bin/activate
     ```

### Step 4: Install Python Packages
With the virtual environment active, run `pip` to install all GIS, database, and REST API backend dependencies using the provided `requirements.txt` file:
```powershell
# Install all required Python packages
pip install -r requirements.txt
```

### Step 5: Start the FastAPI Backend REST Server
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
4. Verify that the server is active by visiting `http://127.0.0.1:8000/` in your browser. You should receive a welcoming JSON message.
5. You can explore and test the interactive OpenAPI documentation panel at: `http://127.0.0.1:8000/docs`

### Step 6: Launch and Explore the Frontend Web Dashboard
1. Open your File Explorer and navigate to: `C:\Work\UrbanHeat\Frontend\`
2. Double-click the **`index.html`** file. It will automatically load in your default browser.
3. **Dynamic Connectivity Auto-Detection**:
   * If your local FastAPI server is running, the dashboard header banner will automatically display a green **"Database Connected"** status badge. Any weight adjustments and calculations will be offloaded to your local FastAPI backend!
   * If the local server is offline, the dashboard header will display a gray **"Offline Mockup Mode"** status badge. It will smoothly fall back to our high-speed in-browser MCDA calculation engine and simulated Omaha coordinate grid, letting you run and test the full visual experience without any setup!
4. Move the weight sliders, click the green **"Apply weights & Recalculate"** button, hover over grid tiles to inspect variables, and click **"Export Scenario GeoJSON"** to download your custom planning results!

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

* **Verbose and Clear Variables**: Names throughout Python, JavaScript, CSS, and SQL (e.g., `calculated_final_mitigation_priority_score`) are explicitly defined for clarity.
* **Block Comments Placement**: All inline documentation is written directly **above** the line or block of code it describes.
* **Highly Modular Structure**: Decoupled styles, dynamic generator logic, math computations, and React rendering engines for clean maintainability.
* **Zero Software Installations**: Designed to run immediately with native tools and CDN assets.
