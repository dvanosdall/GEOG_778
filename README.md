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
1. Open your PostgreSQL command-line tool (`psql`) or graphical client (**pgAdmin**).
2. Connect as a database superuser (`postgres`) and create the main target database:
   ```sql
   -- Create database instance
   CREATE DATABASE urbanheat;
   ```
3. Connect to the newly created `urbanheat` database.
4. Execute the SQL schema script provided in this repository to create tables, keys, and spatial indexes:
   * Using command-line psql:
     ```bash
     # Run schema sql to initialize PostGIS tables and indexes
     psql -U postgres -d urbanheat -f Database/schema.sql
     ```
   * Or open `Database/schema.sql` in pgAdmin's Query Tool, select the entire text, and click **Execute**.

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
     ```powershell
     # Activate environment inside PowerShell
     venv\Scripts\Activate.ps1
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
With the virtual environment active, run `pip` to install all GIS, database, and REST API backend dependencies:
```bash
# Install core web service, database driver, ORM, and spatial geometry math dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary geopandas rasterio shapely pandas numpy
```

### Step 5: Start the FastAPI Backend REST Server
1. Activate your virtual environment (if not already done).
2. Launch the backend API using uvicorn:
   ```bash
   # Run the server with hot-reloads enabled on local port 8000
   uvicorn Backend.app:fastapi_application_instance --reload --port 8000
   ```
3. Verify that the server is active by visiting `http://127.0.0.1:8000/` in your browser. You should receive a welcoming JSON message.
4. You can explore and test the interactive OpenAPI documentation panel at: `http://127.0.0.1:8000/docs`

### Step 6: Launch and Explore the Frontend Web Dashboard
1. Open your File Explorer and navigate to: `C:\Work\UrbanHeat\Frontend\`
2. Double-click the **`index.html`** file. It will automatically load in your default browser.
3. **Dynamic Connectivity Auto-Detection**:
   * If your local FastAPI server is running, the dashboard header banner will automatically display a green **"Database Connected"** status badge. Any weight adjustments and calculations will be offloaded to your local FastAPI backend!
   * If the local server is offline, the dashboard header will display a gray **"Offline Mockup Mode"** status badge. It will smoothly fall back to our high-speed in-browser MCDA calculation engine and simulated Omaha coordinate grid, letting you run and test the full visual experience without any setup!
4. Move the weight sliders, click the green **"Apply weights & Recalculate"** button, hover over grid tiles to inspect variables, and click **"Export Scenario GeoJSON"** to download your custom planning results!

### Step 7: Load Real-World Geospatial Datasets
Once you download your USGS Landsat surface temperatures, USDA canopy covers, NLCD land covers, and U.S. Census block group shapefiles:
1. Place raw files into your workspace directory (e.g. under a `Data` folder).
2. Open `Scripts/urban_heat_etl_analysis.py` in your code editor.
3. Edit the raw file path variables to point to your local downloaded files.
4. Execute the ETL script with your active virtual environment:
   ```bash
   # Run the spatial data pipeline to load processed variables into PostgreSQL
   python Scripts/urban_heat_etl_analysis.py
   ```
5. The Python ETL pipeline will write processed data rows directly to your local `urbanheat` PostGIS database. The FastAPI backend will immediately read these real-world values on the next page refresh!

---

## Coding Standards Applied

* **Verbose and Clear Variables**: Names throughout Python, JavaScript, CSS, and SQL (e.g., `calculated_final_mitigation_priority_score`) are explicitly defined for clarity.
* **Block Comments Placement**: All inline documentation is written directly **above** the line or block of code it describes.
* **Highly Modular Structure**: Decoupled styles, dynamic generator logic, math computations, and React rendering engines for clean maintainability.
* **Zero Software Installations**: Designed to run immediately with native tools and CDN assets.
