-- Enable the PostGIS extension to support spatial data types and operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable the PostGIS raster extension to support raster-based environmental datasets (like Landsat)
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Create table to store the geographic boundary of the Omaha study area
CREATE TABLE IF NOT EXISTS omaha_study_area_boundary (
    -- Unique identifier for each boundary polygon
    study_area_id SERIAL PRIMARY KEY,
    -- Name of the study area, e.g., "Omaha Metro Area"
    study_area_name VARCHAR(255) NOT NULL,
    -- Spatial geometry column representing the boundary in coordinate system EPSG:4326 (WGS 84)
    boundary_geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    -- Timestamp indicating when this boundary record was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a spatial index on the study area boundary geometry to optimize spatial queries
CREATE INDEX IF NOT EXISTS idx_omaha_study_area_boundary_geom 
ON omaha_study_area_boundary USING GIST (boundary_geometry);


-- Create table to store the processed Landsat land surface temperature (LST) raster data
CREATE TABLE IF NOT EXISTS land_surface_temperature_rasters (
    -- Unique identifier for each raster tile or dataset
    raster_id SERIAL PRIMARY KEY,
    -- Name of the raster file or source identifier
    raster_source_file_name VARCHAR(512) NOT NULL,
    -- The date and time when the satellite image was captured
    satellite_acquisition_date DATE NOT NULL,
    -- The actual raster data containing temperature values in degrees Celsius, using EPSG:4326
    temperature_raster_data RASTER NOT NULL,
    -- Timestamp indicating when this raster record was imported into the database
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Create table to store tree canopy cover percentage data, represented as vector polygons or grid cells
CREATE TABLE IF NOT EXISTS tree_canopy_cover_grid_cells (
    -- Unique identifier for each grid cell or canopy polygon
    grid_cell_id SERIAL PRIMARY KEY,
    -- The percentage of tree canopy coverage within this specific cell (ranging from 0.0 to 100.0)
    canopy_coverage_percentage NUMERIC(5, 2) NOT NULL CHECK (canopy_coverage_percentage >= 0.0 AND canopy_coverage_percentage <= 100.0),
    -- The square footage or acreage of tree canopy within this cell
    canopy_area_square_meters NUMERIC(12, 2) NOT NULL CHECK (canopy_area_square_meters >= 0.0),
    -- Spatial polygon representing the boundary of this grid cell in EPSG:4326
    grid_cell_geometry GEOMETRY(Polygon, 4326) NOT NULL,
    -- Timestamp indicating when this canopy cell record was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a spatial index on the tree canopy grid cell geometry for fast spatial overlay analysis
CREATE INDEX IF NOT EXISTS idx_tree_canopy_cover_grid_cells_geom 
ON tree_canopy_cover_grid_cells USING GIST (grid_cell_geometry);


-- Create table to store the National Land Cover Database (NLCD) impervious surface characteristics
CREATE TABLE IF NOT EXISTS impervious_surface_grid_cells (
    -- Unique identifier for each land cover grid cell
    grid_cell_id SERIAL PRIMARY KEY,
    -- The percentage of impervious surface area within this cell (ranging from 0.0 to 100.0)
    impervious_surface_percentage NUMERIC(5, 2) NOT NULL CHECK (impervious_surface_percentage >= 0.0 AND impervious_surface_percentage <= 100.0),
    -- The dominant land cover class code as defined by NLCD standards (e.g., 21 for developed, open space)
    national_land_cover_class_code INTEGER NOT NULL,
    -- Spatial polygon representing the boundary of this grid cell in EPSG:4326
    grid_cell_geometry GEOMETRY(Polygon, 4326) NOT NULL,
    -- Timestamp indicating when this impervious surface cell record was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a spatial index on the impervious surface grid geometry for optimization
CREATE INDEX IF NOT EXISTS idx_impervious_surface_grid_cells_geom 
ON impervious_surface_grid_cells USING GIST (grid_cell_geometry);


-- Create table to store demographic and socioeconomic indicators from the U.S. Census American Community Survey (ACS) at the block group level
CREATE TABLE IF NOT EXISTS census_block_group_demographics (
    -- Unique identifier for each census block group
    block_group_id SERIAL PRIMARY KEY,
    -- The standard 12-character Federal Information Processing Series (FIPS) identifier for the block group
    census_block_group_fips_code VARCHAR(12) UNIQUE NOT NULL,
    -- Total population count living in the block group
    total_population_count INTEGER NOT NULL CHECK (total_population_count >= 0),
    -- Number of individuals under 5 years old (vulnerable to extreme heat)
    vulnerable_population_under_five_years INTEGER NOT NULL CHECK (vulnerable_population_under_five_years >= 0),
    -- Number of individuals 65 years and older (vulnerable to extreme heat)
    vulnerable_population_sixty_five_and_older INTEGER NOT NULL CHECK (vulnerable_population_sixty_five_and_older >= 0),
    -- Median household income of the block group in USD
    median_household_income_usd NUMERIC(12, 2) CHECK (median_household_income_usd >= 0.0),
    -- Spatial multi-polygon representing the boundary of the census block group in EPSG:4326
    block_group_geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    -- Timestamp indicating when this demographic record was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a spatial index on the census block group geometry to support spatial joins with heat/canopy rasters
CREATE INDEX IF NOT EXISTS idx_census_block_group_demographics_geom 
ON census_block_group_demographics USING GIST (block_group_geometry);


-- Create table to store user-defined multi-criteria planning scenarios and their associated weights
CREATE TABLE IF NOT EXISTS multi_criteria_planning_scenarios (
    -- Unique identifier for each saved planning scenario
    scenario_id SERIAL PRIMARY KEY,
    -- Name given to the scenario, e.g., "Vulnerable Communities First"
    scenario_name VARCHAR(255) UNIQUE NOT NULL,
    -- Detailed description of the scenario and its planning objectives
    scenario_description TEXT,
    -- The numerical weight assigned to the land surface temperature criterion (ranging from 0.0 to 10.0)
    land_surface_temperature_criterion_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0 CHECK (land_surface_temperature_criterion_weight >= 0.0 AND land_surface_temperature_criterion_weight <= 10.0),
    -- The numerical weight assigned to the tree canopy coverage deficit criterion (ranging from 0.0 to 10.0)
    tree_canopy_deficit_criterion_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0 CHECK (tree_canopy_deficit_criterion_weight >= 0.0 AND tree_canopy_deficit_criterion_weight <= 10.0),
    -- The numerical weight assigned to the impervious surface coverage criterion (ranging from 0.0 to 10.0)
    impervious_surface_criterion_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0 CHECK (impervious_surface_criterion_weight >= 0.0 AND impervious_surface_criterion_weight <= 10.0),
    -- The numerical weight assigned to the population density criterion (ranging from 0.0 to 10.0)
    population_density_criterion_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0 CHECK (population_density_criterion_weight >= 0.0 AND population_density_criterion_weight <= 10.0),
    -- The numerical weight assigned to the socio-demographic vulnerability criterion (ranging from 0.0 to 10.0)
    demographic_vulnerability_criterion_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0 CHECK (demographic_vulnerability_criterion_weight >= 0.0 AND demographic_vulnerability_criterion_weight <= 10.0),
    -- Timestamp indicating when this scenario configuration was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Timestamp indicating when this scenario was last updated
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Create table to store the computed decision support priority results for specific geographic areas
CREATE TABLE IF NOT EXISTS urban_heat_mitigation_priority_results (
    -- Unique identifier for each calculated priority result
    priority_result_id SERIAL PRIMARY KEY,
    -- Reference to the scenario used to calculate this priority
    associated_scenario_id INTEGER REFERENCES multi_criteria_planning_scenarios(scenario_id) ON DELETE CASCADE,
    -- Reference to the corresponding census block group
    associated_block_group_id INTEGER REFERENCES census_block_group_demographics(block_group_id) ON DELETE CASCADE,
    -- Normalized index score for land surface temperature (0.0 to 100.0)
    normalized_temperature_indicator_score NUMERIC(5, 2) NOT NULL CHECK (normalized_temperature_indicator_score >= 0.0 AND normalized_temperature_indicator_score <= 100.0),
    -- Normalized index score for tree canopy deficit (0.0 to 100.0)
    normalized_canopy_deficit_indicator_score NUMERIC(5, 2) NOT NULL CHECK (normalized_canopy_deficit_indicator_score >= 0.0 AND normalized_canopy_deficit_indicator_score <= 100.0),
    -- Normalized index score for impervious surface density (0.0 to 100.0)
    normalized_impervious_surface_indicator_score NUMERIC(5, 2) NOT NULL CHECK (normalized_impervious_surface_indicator_score >= 0.0 AND normalized_impervious_surface_indicator_score <= 100.0),
    -- Normalized index score for demographic vulnerability (0.0 to 100.0)
    normalized_demographic_vulnerability_indicator_score NUMERIC(5, 2) NOT NULL CHECK (normalized_demographic_vulnerability_indicator_score >= 0.0 AND normalized_demographic_vulnerability_indicator_score <= 100.0),
    -- The final calculated multi-criteria decision priority score (0.0 to 100.0)
    calculated_final_mitigation_priority_score NUMERIC(5, 2) NOT NULL CHECK (calculated_final_mitigation_priority_score >= 0.0 AND calculated_final_mitigation_priority_score <= 100.0),
    -- Recommended intervention category (e.g., "Tree Planting", "Cool Roof Retrofit", "Shade Structure", "Green Space Expansion")
    recommended_mitigation_intervention_type VARCHAR(100) NOT NULL,
    -- Timestamp indicating when this priority result was calculated
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Unique constraint to prevent duplicate calculation records for the same block group and scenario
    CONSTRAINT unique_priority_result_per_scenario_and_block_group UNIQUE (associated_scenario_id, associated_block_group_id)
);

-- Create index to optimize priority lookups by scenario
CREATE INDEX IF NOT EXISTS idx_priority_results_scenario 
ON urban_heat_mitigation_priority_results (associated_scenario_id);

-- Create index to optimize priority lookups by block group
CREATE INDEX IF NOT EXISTS idx_priority_results_block_group 
ON urban_heat_mitigation_priority_results (associated_block_group_id);
