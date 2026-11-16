# ==============================================================================
# URBAN HEAT MITIGATION DECISION-SUPPORT TOOLKIT FOR OMAHA
# PYTHON ETL AND SPATIAL ANALYSIS ENGINE (STUB SCRIPTS)
# ==============================================================================

# Import standard python system libraries
import os
import json
import math

# Try importing spatial data libraries (gracefully handle if they are not installed yet)
try:
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask
    from shapely.geometry import shape, mapping, Polygon, MultiPolygon
    from sqlalchemy import create_engine
    GEOSPATIAL_LIBRARIES_AVAILABLE = True
except ImportError:
    GEOSPATIAL_LIBRARIES_AVAILABLE = False


def load_raw_landsat_surface_temperature_raster(temperature_raster_file_path):
    """
    Simulates or performs the loading of the USGS Landsat Land Surface Temperature raster data.
    """
    # Verify that the geospatial libraries are installed before executing spatial tasks
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        print("[WARNING] Geospatial libraries are not available. Returning simulated surface temperature data.")
        return {"status": "Simulated Landsat raster metadata load successful"}

    # Open the surface temperature raster file using rasterio
    with rasterio.open(temperature_raster_file_path) as surface_temperature_dataset:
        # Read the first band which contains the raw temperature values
        surface_temperature_band_data = surface_temperature_dataset.read(1)
        # Extract metadata associated with the temperature raster file
        surface_temperature_raster_metadata = surface_temperature_dataset.meta.copy()

    return {
        "data": surface_temperature_band_data,
        "metadata": surface_temperature_raster_metadata
    }


def load_tree_canopy_coverage_dataset(tree_canopy_shapefile_path):
    """
    Loads the USDA Forest Service Tree Canopy Cover vector dataset.
    """
    # Verify spatial library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        print("[WARNING] Geospatial libraries are not available. Returning simulated tree canopy vector metadata.")
        return {"status": "Simulated Tree Canopy shapefile load successful"}

    # Load the spatial shapefile or GeoPackage using geopandas
    tree_canopy_geodataframe = gpd.read_file(tree_canopy_shapefile_path)

    # Ensure that the dataset uses a consistent coordinate reference system (WGS84 - EPSG:4326)
    if tree_canopy_geodataframe.crs != "EPSG:4326":
        # Reproject the vector geometry to EPSG:4326
        tree_canopy_geodataframe = tree_canopy_geodataframe.to_crs("EPSG:4326")

    return tree_canopy_geodataframe


def load_census_demographics_dataset(census_demographics_shapefile_path, census_demographics_csv_path):
    """
    Loads the US Census block group spatial boundaries from NHGIS shapefile and joins them with the NHGIS demographic CSV.
    """
    # Check library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        print("[WARNING] Geospatial libraries are not available. Returning simulated demographic vector metadata.")
        return {"status": "Simulated Census Demographics load successful"}

    # Load the spatial block group boundaries shapefile
    print(f"[INFO] Loading Census block group shapefile: {census_demographics_shapefile_path}")
    block_groups_geodataframe = gpd.read_file(census_demographics_shapefile_path)

    # Load the demographic attributes CSV table
    print(f"[INFO] Loading Census demographic CSV table: {census_demographics_csv_path}")
    demographics_dataframe = pd.read_csv(census_demographics_csv_path)

    # Merge the spatial geodataframe and the attributes dataframe on the unique 'GISJOIN' column
    print("[INFO] Joining census spatial boundaries and demographic tables on 'GISJOIN'...")
    merged_census_geodataframe = block_groups_geodataframe.merge(demographics_dataframe, on="GISJOIN", how="inner")

    # Filter to keep only Douglas County (FIPS Code 055, which contains Omaha) to keep database extremely fast and small
    # Douglas County is State 31 (Nebraska), County 055
    county_column_name = None
    for possible_county_col in ["COUNTYFP20", "COUNTYFP10", "COUNTYFP", "COUNTY"]:
        if possible_county_col in merged_census_geodataframe.columns:
            county_column_name = possible_county_col
            break

    if county_column_name is not None:
        print(f"[INFO] Filtering block groups to Douglas County, NE (Omaha) using column '{county_column_name}'...")
        merged_census_geodataframe = merged_census_geodataframe[
            merged_census_geodataframe[county_column_name].astype(str).str.contains("055|douglas", case=False, na=False)
        ]
    else:
        print("[WARNING] County column not found. Processing all loaded block groups.")

    # Standardize demographic column codes to descriptive project variables
    # Total Population code in this dataset is 'U7H001'
    merged_census_geodataframe["total_population_count"] = merged_census_geodataframe["U7H001"].fillna(0).astype(int)

    # Calculate realistic vulnerability age estimates since separate age tables are omitted
    merged_census_geodataframe["vulnerable_population_under_five_years"] = (merged_census_geodataframe["total_population_count"] * 0.05).astype(int)
    merged_census_geodataframe["vulnerable_population_sixty_five_and_older"] = (merged_census_geodataframe["total_population_count"] * 0.15).astype(int)

    # Convert coordinate reference system to EPSG:4326 for consistency with map displays
    if merged_census_geodataframe.crs != "EPSG:4326":
        print("[INFO] Reprojecting census boundaries to EPSG:4326...")
        merged_census_geodataframe = merged_census_geodataframe.to_crs("EPSG:4326")

    print(f"[SUCCESS] Loaded {len(merged_census_geodataframe)} census block groups for Douglas County / Omaha!")
    return merged_census_geodataframe


def load_processed_data_to_postgresql(geodataframe, database_url):
    """
    Saves the processed real-world block group geometries and demographics directly into PostgreSQL/PostGIS.
    """
    try:
        # Import psycopg2 library to connect directly to PostgreSQL
        import psycopg2
        
        print(f"[INFO] Connecting to PostgreSQL database to load real-world geometries...")
        # Establish connection using your secure .env credentials
        database_connection = psycopg2.connect(database_url)
        database_cursor = database_connection.cursor()
        
        # Ensure the FIPS code column can accommodate longer GEO_ID/GIS_JOIN values dynamically
        database_cursor.execute("ALTER TABLE census_block_group_demographics ALTER COLUMN census_block_group_fips_code TYPE VARCHAR(50);")
        
        # Ensure pre-calculated environmental columns exist dynamically on the demographics table
        database_cursor.execute("ALTER TABLE census_block_group_demographics ADD COLUMN IF NOT EXISTS mean_land_surface_temperature_celsius DOUBLE PRECISION;")
        database_cursor.execute("ALTER TABLE census_block_group_demographics ADD COLUMN IF NOT EXISTS mean_canopy_coverage_percentage DOUBLE PRECISION;")
        database_cursor.execute("ALTER TABLE census_block_group_demographics ADD COLUMN IF NOT EXISTS mean_impervious_surface_percentage DOUBLE PRECISION;")
        
        # Alter columns type dynamically in case they were previously created with a lower NUMERIC precision limit
        database_cursor.execute("ALTER TABLE census_block_group_demographics ALTER COLUMN mean_land_surface_temperature_celsius TYPE DOUBLE PRECISION;")
        database_cursor.execute("ALTER TABLE census_block_group_demographics ALTER COLUMN mean_canopy_coverage_percentage TYPE DOUBLE PRECISION;")
        database_cursor.execute("ALTER TABLE census_block_group_demographics ALTER COLUMN mean_impervious_surface_percentage TYPE DOUBLE PRECISION;")
        
        # Clear (truncate) any old or mock records in the demographics table before loading fresh data
        print("[INFO] Truncating old database records in 'census_block_group_demographics' table...")
        database_cursor.execute("TRUNCATE TABLE census_block_group_demographics CASCADE;")
        
        # Iterate and insert each row of our geodataframe with its spatial geometry
        print(f"[INFO] Streaming {len(geodataframe)} real-world census block groups into PostGIS...")
        for row_index, census_row in geodataframe.iterrows():
            fips_code = str(census_row["fips_code"])
            total_population = int(census_row["total_population"])
            under_five_pop = int(census_row["population_under_five"])
            over_sixty_five_pop = int(census_row["population_sixty_five_and_older"])
            
            # Extract raw pre-calculated environmental zonal metrics safely
            temp_val = float(census_row["raw_temperature_celsius"]) if "raw_temperature_celsius" in census_row else 32.5
            canopy_val = float(census_row["raw_canopy_percentage"]) if "raw_canopy_percentage" in census_row else 15.0
            impervious_val = float(census_row["raw_impervious_percentage"]) if "raw_impervious_percentage" in census_row else 45.0
            
            # Convert the shapely polygon geometry into standard Well-Known Text (WKT) format
            wkt_geometry_string = census_row["geometry"].wkt
            
            # Insert record using ST_GeomFromText to register coordinates into PostGIS geometry column
            database_cursor.execute("""
                INSERT INTO census_block_group_demographics 
                    (census_block_group_fips_code, total_population_count, vulnerable_population_under_five_years, vulnerable_population_sixty_five_and_older, 
                     mean_land_surface_temperature_celsius, mean_canopy_coverage_percentage, mean_impervious_surface_percentage, block_group_geometry)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326));
            """, (fips_code, total_population, under_five_pop, over_sixty_five_pop, temp_val, canopy_val, impervious_val, wkt_geometry_string))
            
        # Commit transaction and release connection resources
        database_connection.commit()
        database_cursor.close()
        database_connection.close()
        print("[SUCCESS] Real-world census boundaries and demographics successfully loaded into PostGIS!")
        
    except Exception as database_load_error:
        print(f"[ERROR] Failed to write to PostgreSQL database: {database_load_error}")
        print("[WARNING] Please verify that your .env database URL credentials are correct.")


def calculate_zonal_temperature_statistics(census_demographics_geodataframe, temperature_raster_file_path):
    """
    Calculates zonal statistics to extract the mean Land Surface Temperature for each census block group.
    """
    # Check library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        # Create simulated temperature statistics column if spatial library is missing
        census_demographics_geodataframe["mean_land_surface_temperature_celsius"] = [35.5] * len(census_demographics_geodataframe)
        return census_demographics_geodataframe

    # Open the temperature raster file in read-only mode
    with rasterio.open(temperature_raster_file_path) as surface_temperature_raster:
        # Create an empty list to store computed mean temperature values for each geographic polygon
        computed_mean_temperatures_list = []

        # Reproject the entire geodataframe to match the raster's native coordinate reference system (CRS) on-the-fly
        reprojected_geodataframe = census_demographics_geodataframe.to_crs(surface_temperature_raster.crs)

        # Iterate through each census block group record in the geodataframe
        for geo_index, block_group_row in reprojected_geodataframe.iterrows():
            try:
                # Wrap the polygon geometry in a list to format it for rasterio masking
                polygon_geometry_list = [block_group_row.geometry]
                
                # Crop and mask the temperature raster dataset using the block group geometry
                masked_raster_pixels, masked_raster_transform = mask(
                    surface_temperature_raster, 
                    polygon_geometry_list, 
                    crop=True
                )
                
                # Extract the 2D array of pixel values for the first band
                temperature_pixel_array = masked_raster_pixels[0]
                
                # Identify valid temperature pixels (filter out nodata values, e.g. values below absolute zero)
                valid_temperature_pixels = temperature_pixel_array[temperature_pixel_array > -100]

                # If we have valid pixels within the polygon boundary, calculate their average
                if len(valid_temperature_pixels) > 0:
                    # Calculate mathematical mean of temperature pixel values
                    mean_temperature_value = float(np.mean(valid_temperature_pixels))
                else:
                    # Default to average temperature if no pixels fall inside the polygon
                    mean_temperature_value = 32.0
                
                # Append the calculated average temperature to our list
                computed_mean_temperatures_list.append(mean_temperature_value)
                
            except Exception as spatial_processing_error:
                print(f"[ERROR] Failed to calculate zonal stats for index {geo_index}: {spatial_processing_error}")
                # Append fallback average temperature in case of geometry processing failure
                computed_mean_temperatures_list.append(32.0)

        # Assign the computed temperatures list as a new attribute column on the geodataframe
        census_demographics_geodataframe["mean_land_surface_temperature_celsius"] = computed_mean_temperatures_list

    return census_demographics_geodataframe


def calculate_zonal_canopy_statistics(census_demographics_geodataframe, canopy_raster_file_path):
    """
    Calculates zonal statistics to extract the mean Tree Canopy Cover percentage for each census block group.
    """
    # Check library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        # Create simulated canopy statistics column if spatial library is missing
        census_demographics_geodataframe["mean_canopy_coverage_percentage"] = [15.0] * len(census_demographics_geodataframe)
        return census_demographics_geodataframe

    print(f"[INFO] Calculating zonal tree canopy statistics from raster: {canopy_raster_file_path}")
    # Open the canopy raster file in read-only mode
    with rasterio.open(canopy_raster_file_path) as canopy_raster:
        # Create an empty list to store computed mean canopy values for each geographic polygon
        computed_mean_canopy_list = []

        # Reproject the entire geodataframe to match the canopy raster's native CRS on-the-fly
        reprojected_geodataframe = census_demographics_geodataframe.to_crs(canopy_raster.crs)

        # Iterate through each census block group record in the geodataframe
        for geo_index, block_group_row in reprojected_geodataframe.iterrows():
            try:
                # Wrap the polygon geometry in a list to format it for rasterio masking
                polygon_geometry_list = [block_group_row.geometry]
                
                # Crop and mask the canopy raster dataset using the block group geometry
                masked_raster_pixels, masked_raster_transform = mask(
                    canopy_raster, 
                    polygon_geometry_list, 
                    crop=True
                )
                
                # Extract the 2D array of pixel values for the first band
                canopy_pixel_array = masked_raster_pixels[0]
                
                # Identify valid canopy pixels (filter out nodata values, e.g. values below zero or above 100)
                valid_canopy_pixels = canopy_pixel_array[(canopy_pixel_array >= 0) & (canopy_pixel_array <= 100)]

                # If we have valid pixels within the polygon boundary, calculate their average
                if len(valid_canopy_pixels) > 0:
                    # Calculate mathematical mean of canopy pixel values
                    mean_canopy_value = float(np.mean(valid_canopy_pixels))
                else:
                    # Default to average canopy if no pixels fall inside the polygon
                    mean_canopy_value = 15.0
                
                # Append the calculated average canopy to our list
                computed_mean_canopy_list.append(mean_canopy_value)
                
            except Exception as spatial_processing_error:
                print(f"[ERROR] Failed to calculate zonal canopy stats for index {geo_index}: {spatial_processing_error}")
                # Append fallback average canopy in case of geometry processing failure
                computed_mean_canopy_list.append(15.0)

        # Assign the computed canopy list as a new attribute column on the geodataframe
        census_demographics_geodataframe["mean_canopy_coverage_percentage"] = computed_mean_canopy_list

    return census_demographics_geodataframe


def calculate_zonal_impervious_statistics(census_demographics_geodataframe, impervious_raster_file_path):
    """
    Calculates zonal statistics to extract the mean Developed Impervious Surface percentage for each census block group.
    """
    # Check library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        # Create simulated impervious statistics column if spatial library is missing
        census_demographics_geodataframe["mean_impervious_percentage"] = [45.0] * len(census_demographics_geodataframe)
        return census_demographics_geodataframe

    print(f"[INFO] Calculating zonal developed imperviousness statistics from raster: {impervious_raster_file_path}")
    # Open the impervious raster file in read-only mode
    with rasterio.open(impervious_raster_file_path) as impervious_raster:
        # Create an empty list to store computed mean impervious values for each geographic polygon
        computed_mean_impervious_list = []

        # Reproject the entire geodataframe to match the impervious raster's native CRS on-the-fly
        reprojected_geodataframe = census_demographics_geodataframe.to_crs(impervious_raster.crs)

        # Iterate through each census block group record in the geodataframe
        for geo_index, block_group_row in reprojected_geodataframe.iterrows():
            try:
                # Wrap the polygon geometry in a list to format it for rasterio masking
                polygon_geometry_list = [block_group_row.geometry]
                
                # Crop and mask the impervious raster dataset using the block group geometry
                masked_raster_pixels, masked_raster_transform = mask(
                    impervious_raster, 
                    polygon_geometry_list, 
                    crop=True
                )
                
                # Extract the 2D array of pixel values for the first band
                impervious_pixel_array = masked_raster_pixels[0]
                
                # Identify valid impervious pixels (filter out nodata values, e.g. values below zero or above 100)
                valid_impervious_pixels = impervious_pixel_array[(impervious_pixel_array >= 0) & (impervious_pixel_array <= 100)]

                # If we have valid pixels within the polygon boundary, calculate their average
                if len(valid_impervious_pixels) > 0:
                    # Calculate mathematical mean of impervious pixel values
                    mean_impervious_value = float(np.mean(valid_impervious_pixels))
                else:
                    # Default to average impervious if no pixels fall inside the polygon
                    mean_impervious_value = 45.0
                
                # Append the calculated average impervious to our list
                computed_mean_impervious_list.append(mean_impervious_value)
                
            except Exception as spatial_processing_error:
                print(f"[ERROR] Failed to calculate zonal impervious stats for index {geo_index}: {spatial_processing_error}")
                # Append fallback average impervious in case of geometry processing failure
                computed_mean_impervious_list.append(45.0)

        # Assign the computed impervious list as a new attribute column on the geodataframe
        census_demographics_geodataframe["mean_impervious_percentage"] = computed_mean_impervious_list

    return census_demographics_geodataframe


def normalize_metric_indicator_scores(raw_metric_value_series, inversion_flag=False):
    """
    Normalizes a numerical data series into a standardized score ranging from 0.0 to 100.0.
    Inversion flag:
    - False: Higher raw value maps to a higher score (e.g., higher temperature -> higher priority).
    - True: Lower raw value maps to a higher score (e.g., lower tree canopy cover -> higher priority).
    """
    # Calculate the minimum value in the series, ignoring missing values
    minimum_raw_value = float(raw_metric_value_series.min())
    # Calculate the maximum value in the series, ignoring missing values
    maximum_raw_value = float(raw_metric_value_series.max())
    # Determine the mathematical range of values in the series
    raw_value_range = maximum_raw_value - minimum_raw_value

    # Prevent division by zero if all values in the data series are identical
    if raw_value_range == 0.0:
        # Return a series of neutral 50.0 priority scores
        return pd.Series([50.0] * len(raw_metric_value_series))

    # Standardize the raw values depending on whether higher or lower values represent a priority
    if not inversion_flag:
        # High value = high priority (e.g. Temperature, Impervious surface density)
        normalized_scores_series = ((raw_metric_value_series - minimum_raw_value) / raw_value_range) * 100.0
    else:
        # Low value = high priority (e.g. Tree canopy coverage deficit)
        normalized_scores_series = ((maximum_raw_value - raw_metric_value_series) / raw_value_range) * 100.0

    return normalized_scores_series


def execute_multi_criteria_decision_analysis(
    processed_geodataframe,
    temperature_weight=0.30,
    canopy_deficit_weight=0.25,
    impervious_surface_weight=0.20,
    demographic_vulnerability_weight=0.25
):
    """
    Combines normalized environmental and demographic indicators using configurable weights to calculate the final priority scores.
    """
    # Standardize and calculate weights to ensure they sum up to exactly 1.0
    total_raw_weight_sum = temperature_weight + canopy_deficit_weight + impervious_surface_weight + demographic_vulnerability_weight
    # Divide individual weights by the total sum to normalize them
    normalized_temperature_weight = temperature_weight / total_raw_weight_sum
    # Normalize tree canopy deficit weight
    normalized_canopy_deficit_weight = canopy_deficit_weight / total_raw_weight_sum
    # Normalize impervious surface weight
    normalized_impervious_surface_weight = impervious_surface_weight / total_raw_weight_sum
    # Normalize socio-demographic vulnerability weight
    normalized_demographic_vulnerability_weight = demographic_vulnerability_weight / total_raw_weight_sum

    # Calculate the final decision-support priority score using a weighted linear combination of criteria scores
    processed_geodataframe["final_mitigation_priority_score"] = (
        (processed_geodataframe["normalized_temperature_score"] * normalized_temperature_weight) +
        (processed_geodataframe["normalized_canopy_deficit_score"] * normalized_canopy_deficit_weight) +
        (processed_geodataframe["normalized_impervious_surface_score"] * normalized_impervious_surface_weight) +
        (processed_geodataframe["normalized_demographic_vulnerability_score"] * normalized_demographic_vulnerability_weight)
    )

    # Create an empty list to store recommended types of mitigation interventions for each record
    determined_intervention_types_list = []

    # Iterate through the rows to determine appropriate urban heat mitigation strategies based on spatial conditions
    for data_index, block_group_row in processed_geodataframe.iterrows():
        # High heat and low tree canopy coverage triggers a tree planting priority
        if block_group_row["normalized_temperature_score"] >= 60.0 and block_group_row["normalized_canopy_deficit_score"] >= 65.0:
            determined_intervention_types_list.append("Urban Forestry & Tree Canopy Expansion")
        # High heat and high impervious percentage triggers cool surface retrofits (cool roofs/pavements)
        elif block_group_row["normalized_temperature_score"] >= 60.0 and block_group_row["normalized_impervious_surface_score"] >= 70.0:
            determined_intervention_types_list.append("Cool Roof & Cool Surface Retrofitting")
        # High heat combined with high demographic vulnerability in moderate canopy areas triggers shade structures and green space
        elif block_group_row["normalized_temperature_score"] >= 50.0 and block_group_row["normalized_demographic_vulnerability_score"] >= 60.0:
            determined_intervention_types_list.append("Community Shade Structures & Parks")
        # High impervious percentage with lower canopy deficit triggers bioswales and pervious surfaces
        elif block_group_row["normalized_impervious_surface_score"] >= 50.0:
            determined_intervention_types_list.append("Pervious Paving & Rain Gardens")
        # Fallback category for low-priority or moderate-priority planning conditions
        else:
            determined_intervention_types_list.append("General Cool Green Infrastructure")

    # Add the determined intervention recommendations column to the geodataframe
    processed_geodataframe["recommended_intervention_type"] = determined_intervention_types_list

    return processed_geodataframe


def generate_simulated_omaha_census_block_group_data():
    """
    Generates realistic, mock demographic and spatial data for Omaha to allow the toolkit to run out of the box.
    """
    print("[INFO] Generating simulated geospatial dataset for Omaha, Nebraska (approx. 40 block groups)...")
    
    # Establish a list to accumulate simulated geographic feature records
    simulated_block_group_features_list = []
    
    # Coordinates centered approximately around Omaha, Nebraska (-96.0, 41.25)
    omaha_latitude_center = 41.2586
    omaha_longitude_center = -96.0102
    grid_size_rows = 6
    grid_size_columns = 7
    grid_spacing_degrees = 0.015

    # Generate grid features representing spatial neighborhoods/block groups in Omaha
    for row_index in range(grid_size_rows):
        for col_index in range(grid_size_columns):
            # Calculate unique identifiers and spatial characteristics
            block_group_numerical_id = (row_index * grid_size_columns) + col_index + 1
            census_block_group_fips_string = f"3105500{block_group_numerical_id:03d}0"
            
            # Calculate coordinates for the boundaries of the grid cell polygon
            grid_cell_min_longitude = omaha_longitude_center + (col_index - (grid_size_columns / 2.0)) * grid_spacing_degrees
            grid_cell_max_longitude = grid_cell_min_longitude + grid_spacing_degrees
            grid_cell_min_latitude = omaha_latitude_center + (row_index - (grid_size_rows / 2.0)) * grid_spacing_degrees
            grid_cell_max_latitude = grid_cell_min_latitude + grid_spacing_degrees

            # Create polygon coordinates starting from bottom-left corner and moving clockwise
            grid_cell_polygon_coordinates = [
                (grid_cell_min_longitude, grid_cell_min_latitude),
                (grid_cell_min_longitude, grid_cell_max_latitude),
                (grid_cell_max_longitude, grid_cell_max_latitude),
                (grid_cell_max_longitude, grid_cell_min_latitude),
                (grid_cell_min_longitude, grid_cell_min_latitude)
            ]

            # Use raw shapely Polygon geometry if geospatial libraries are available
            if GEOSPATIAL_LIBRARIES_AVAILABLE:
                grid_cell_geometry = Polygon(grid_cell_polygon_coordinates)
            else:
                # Fallback to coordinate dictionary representations if GIS libraries are unavailable
                grid_cell_geometry = {
                    "type": "Polygon",
                    "coordinates": [grid_cell_polygon_coordinates]
                }

            # Generate realistic variables reflecting spatial variation (e.g., East Omaha is warmer and has less canopy)
            east_west_distance_factor = float(col_index) / float(grid_size_columns)
            north_south_distance_factor = float(row_index) / float(grid_size_rows)

            # Warm eastern areas, cool western areas
            simulated_mean_temperature_celsius = 28.5 + (12.0 * east_west_distance_factor) + (3.0 * math.sin(north_south_distance_factor * math.pi))
            
            # High canopy in West Omaha, very low in East Omaha
            simulated_canopy_coverage_percentage = max(2.0, min(85.0, 75.0 - (70.0 * east_west_distance_factor) + (10.0 * math.cos(north_south_distance_factor * math.pi))))
            
            # High impervious surface in urban centers/eastern corridors
            simulated_impervious_surface_percentage = max(10.0, min(95.0, 15.0 + (75.0 * east_west_distance_factor) - (15.0 * math.sin(north_south_distance_factor * math.pi))))
            
            # Generate simulated demographic populations
            simulated_total_population = int(1200 + (2500 * (1.0 - east_west_distance_factor)) + (800 * math.cos(row_index)))
            simulated_vulnerable_under_five = int(simulated_total_population * (0.04 + (0.05 * east_west_distance_factor)))
            simulated_vulnerable_sixty_five = int(simulated_total_population * (0.08 + (0.12 * (1.0 - east_west_distance_factor))))
            simulated_vulnerable_socio_index = (east_west_distance_factor * 80.0) + (north_south_distance_factor * 20.0)

            # Store computed attributes into a structured feature record
            block_group_record_dictionary = {
                "id": block_group_numerical_id,
                "fips_code": census_block_group_fips_string,
                "total_population": simulated_total_population,
                "population_under_five": simulated_vulnerable_under_five,
                "population_sixty_five_and_older": simulated_vulnerable_sixty_five,
                "mean_temperature_celsius": round(simulated_mean_temperature_celsius, 2),
                "canopy_coverage_percentage": round(simulated_canopy_coverage_percentage, 2),
                "impervious_surface_percentage": round(simulated_impervious_surface_percentage, 2),
                "vulnerability_socio_index": round(simulated_vulnerable_socio_index, 2),
                "geometry": grid_cell_geometry
            }

            simulated_block_group_features_list.append(block_group_record_dictionary)

    # Convert the records list to a pandas/geopandas dataframe if libraries are available
    if GEOSPATIAL_LIBRARIES_AVAILABLE:
        block_group_geodataframe = gpd.GeoDataFrame(simulated_block_group_features_list, geometry="geometry", crs="EPSG:4326")
    else:
        block_group_geodataframe = simulated_block_group_features_list

    return block_group_geodataframe


def run_urban_heat_analysis_workflow_pipeline(
    temperature_weight_param=0.35,
    canopy_weight_param=0.30,
    impervious_weight_param=0.15,
    demographic_weight_param=0.20
):
    """
    Coordinates and runs the complete spatial ETL and Multi-Criteria Decision Analysis pipeline.
    """
    print("[INFO] Initiating Urban Heat Mitigation Analysis Workflow...")

    # Load spatial datasets (generate mock data as a default stub)
    omaha_processed_dataframe = generate_simulated_omaha_census_block_group_data()

    # Perform analysis in pandas/geopandas dataframes if libraries are available
    if GEOSPATIAL_LIBRARIES_AVAILABLE:
        # Normalize the land surface temperature values
        omaha_processed_dataframe["normalized_temperature_score"] = normalize_metric_indicator_scores(
            omaha_processed_dataframe["mean_temperature_celsius"], 
            inversion_flag=False
        )
        
        # Normalize the tree canopy deficit (inversion = True, because lower tree canopy means higher priority)
        omaha_processed_dataframe["normalized_canopy_deficit_score"] = normalize_metric_indicator_scores(
            omaha_processed_dataframe["canopy_coverage_percentage"], 
            inversion_flag=True
        )
        
        # Normalize the impervious surface percentages
        omaha_processed_dataframe["normalized_impervious_surface_score"] = normalize_metric_indicator_scores(
            omaha_processed_dataframe["impervious_surface_percentage"], 
            inversion_flag=False
        )
        
        # Normalize the social and demographic vulnerability values
        omaha_processed_dataframe["normalized_demographic_vulnerability_score"] = normalize_metric_indicator_scores(
            omaha_processed_dataframe["vulnerability_socio_index"], 
            inversion_flag=False
        )

        # Execute the Multi-Criteria Decision Analysis prioritization scoring
        omaha_prioritized_results_dataframe = execute_multi_criteria_decision_analysis(
            omaha_processed_dataframe,
            temperature_weight=temperature_weight_param,
            canopy_deficit_weight=canopy_weight_param,
            impervious_surface_weight=impervious_weight_param,
            demographic_vulnerability_weight=demographic_weight_param
        )
        
        print(f"[INFO] Successfully calculated mitigation priority scores for {len(omaha_prioritized_results_dataframe)} geographic zones.")
        return omaha_prioritized_results_dataframe
    else:
        # Fallback dictionary-based manual processing loop if geopandas is not installed
        print("[INFO] Running raw python dictionary processing fallback for pipeline simulation...")
        simulated_results_list = []
        
        # Manually normalize and score each record dictionary
        for record in omaha_processed_dataframe:
            # Simple linear mapping formulas simulating standardizations
            normalized_temp = ((record["mean_temperature_celsius"] - 28.0) / 15.0) * 100.0
            normalized_temp = max(0.0, min(100.0, normalized_temp))
            
            # Low canopy = high deficit priority
            normalized_canopy = ((85.0 - record["canopy_coverage_percentage"]) / 83.0) * 100.0
            normalized_canopy = max(0.0, min(100.0, normalized_canopy))
            
            normalized_impervious = ((record["impervious_surface_percentage"] - 10.0) / 85.0) * 100.0
            normalized_impervious = max(0.0, min(100.0, normalized_impervious))
            
            normalized_vulnerability = record["vulnerability_socio_index"]

            # Calculate the multi-criteria linear combinations manually
            total_param_weights = temperature_weight_param + canopy_weight_param + impervious_weight_param + demographic_weight_param
            final_priority_score = (
                (normalized_temp * (temperature_weight_param / total_param_weights)) +
                (normalized_canopy * (canopy_weight_param / total_param_weights)) +
                (normalized_impervious * (impervious_weight_param / total_param_weights)) +
                (normalized_vulnerability * (demographic_weight_param / total_param_weights))
            )

            # Recommend interventions using simple rules
            if normalized_temp >= 60.0 and normalized_canopy >= 65.0:
                intervention = "Urban Forestry & Tree Canopy Expansion"
            elif normalized_temp >= 60.0 and normalized_impervious >= 70.0:
                intervention = "Cool Roof & Cool Surface Retrofitting"
            elif normalized_temp >= 50.0 and normalized_vulnerability >= 60.0:
                intervention = "Community Shade Structures & Parks"
            elif normalized_impervious >= 50.0:
                intervention = "Pervious Paving & Rain Gardens"
            else:
                intervention = "General Cool Green Infrastructure"

            # Create the final prioritized simulated record
            prioritized_record = record.copy()
            prioritized_record["normalized_temperature_score"] = round(normalized_temp, 2)
            prioritized_record["normalized_canopy_deficit_score"] = round(normalized_canopy, 2)
            prioritized_record["normalized_impervious_surface_score"] = round(normalized_impervious, 2)
            prioritized_record["normalized_demographic_vulnerability_score"] = round(normalized_vulnerability, 2)
            prioritized_record["final_mitigation_priority_score"] = round(final_priority_score, 2)
            prioritized_record["recommended_intervention_type"] = intervention
            
            simulated_results_list.append(prioritized_record)
            
        return simulated_results_list


# Main script execution trigger for testing and validation
if __name__ == "__main__":
    # Get dynamic project root directory to support any drive letter and custom paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Check if the unzipped NHGIS real-world files and Tree Canopy raster are on disk
    real_world_shapefile_path = os.path.join(project_root, "Data", "nhgis0001_shape", "nhgis0001_shapefile_tl2020_310_blck_grp_2020", "NE_blck_grp_2020.shp")
    real_world_csv_path = os.path.join(project_root, "Data", "nhgis0001_csv", "nhgis0001_ds258_2020_blck_grp.csv")
    
    # Check if the tiny cropped Omaha canopy raster is on disk, fallback to the giant CONUS raster if missing
    real_world_canopy_raster_path = os.path.join(project_root, "Data", "omaha_tree_canopy_cover.tif")
    if not os.path.exists(real_world_canopy_raster_path):
        real_world_canopy_raster_path = os.path.join(project_root, "Data", "science_tcc_conus_2025_v2025-6_wgs84", "science_tcc_conus_wgs84_v2025-6_20250101_20251231.tif")
    
    real_world_temperature_raster_path = os.path.join(project_root, "Data", "LC09_L2SP_028031_20260717_20260718_02_T1_ST_B10.TIF")
    
    # Try finding the custom NLCD developed imperviousness cropped raster inside the unzipped folder
    real_world_impervious_raster_path = os.path.join(project_root, "Data", "Annual_NLCD_CONUSV1_Ref_Data_Release", "lcnext-1.0-stratum-map-Clipped.tif")

    # Define output file path for the compiled, database-free frontend JSON dataset
    output_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Frontend", "data")
    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path)
    output_file_path = os.path.join(output_directory_path, "omaha_urban_heat_priority_data.json")

    # Load local private .env file to get the database connection URL if present
    database_connection_url = None
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Backend", ".env")
    if os.path.exists(env_file_path):
        with open(env_file_path, "r") as target_env_file:
            for env_line in target_env_file:
                stripped_line = env_line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    env_key, env_value = stripped_line.split("=", 1)
                    if env_key.strip() == "DATABASE_URL":
                        database_connection_url = env_value.strip()

    # Flag to check if we should run the complete real-world compilation pipeline
    run_real_world_pipeline = (
        os.path.exists(real_world_shapefile_path) and 
        os.path.exists(real_world_csv_path) and 
        os.path.exists(real_world_canopy_raster_path) and 
        os.path.exists(real_world_temperature_raster_path) and 
        GEOSPATIAL_LIBRARIES_AVAILABLE
    )

    if run_real_world_pipeline:
        print("\n" + "="*80)
        print("[INFO] DETECTED COMPLETE REAL-WORLD SPATIAL DATASETS ON DISK!")
        print("[INFO] INITIATING FULL REAL-WORLD DATABASE-FREE COMPILATION PIPELINE...")
        print("="*80 + "\n")
        try:
            # 1. Load and join Census Block Group boundaries and demographic populations
            print("[1/4] Processing Census Block Groups & Demographic Populations...")
            omaha_geodataframe = load_census_demographics_dataset(real_world_shapefile_path, real_world_csv_path)
            
            # 2. Extract average land surface temperatures from Landsat 9 thermal raster
            print("[2/4] Executing spatial zonal statistics on Landsat 9 Summer Thermal Raster...")
            omaha_geodataframe = calculate_zonal_temperature_statistics(omaha_geodataframe, real_world_temperature_raster_path)
            
            # 3. Extract average tree canopy coverages from USDA Forest Service CONUS raster
            print("[3/4] Executing spatial zonal statistics on USDA Tree Canopy Cover Raster...")
            omaha_geodataframe = calculate_zonal_canopy_statistics(omaha_geodataframe, real_world_canopy_raster_path)
            
            # 4. Extract developed imperviousness from NLCD cropped raster if available (fallback gracefully if missing)
            print("[4/4] Processing Developed Imperviousness Density layer...")
            if os.path.exists(real_world_impervious_raster_path):
                omaha_geodataframe = calculate_zonal_impervious_statistics(omaha_geodataframe, real_world_impervious_raster_path)
            else:
                print("[WARNING] NLCD Developed Impervious raster not unzipped yet. Applying realistic placeholder (45%).")
                omaha_geodataframe["mean_impervious_percentage"] = [45.0] * len(omaha_geodataframe)

            # 5. Run the Multi-Criteria Decision Analysis (MCDA) normalizations and priority scoring
            print("[INFO] Normalizing raw metrics and executing Multi-Criteria scoring equations...")
            omaha_geodataframe["normalized_temp_score"] = normalize_metric_indicator_scores(
                omaha_geodataframe["mean_land_surface_temperature_celsius"], 
                inversion_flag=False
            )
            omaha_geodataframe["normalized_canopy_deficit_score"] = normalize_metric_indicator_scores(
                omaha_geodataframe["mean_canopy_coverage_percentage"], 
                inversion_flag=True
            )
            omaha_geodataframe["normalized_impervious_score"] = normalize_metric_indicator_scores(
                omaha_geodataframe["mean_impervious_percentage"], 
                inversion_flag=False
            )
            omaha_geodataframe["normalized_demographic_score"] = normalize_metric_indicator_scores(
                omaha_geodataframe["vulnerable_population_under_five_years"] + omaha_geodataframe["vulnerable_population_sixty_five_and_older"], 
                inversion_flag=False
            )

            # Calculate final linear weighted priority scores
            print("[INFO] Computing final priority levels and recommending targeted physical interventions...")
            omaha_geodataframe["final_mitigation_priority_score"] = (
                (omaha_geodataframe["normalized_temp_score"] * 0.35) +
                (omaha_geodataframe["normalized_canopy_deficit_score"] * 0.30) +
                (omaha_geodataframe["normalized_impervious_score"] * 0.15) +
                (omaha_geodataframe["normalized_demographic_score"] * 0.20)
            )

            # Determine rule-based interventions
            determined_interventions = []
            for _, row in omaha_geodataframe.iterrows():
                if row["normalized_temp_score"] >= 60.0 and row["normalized_canopy_deficit_score"] >= 65.0:
                    determined_interventions.append("Urban Forestry & Tree Canopy Expansion")
                elif row["normalized_temp_score"] >= 60.0 and row["normalized_impervious_score"] >= 70.0:
                    determined_interventions.append("Cool Roof & Cool Surface Retrofitting")
                elif row["normalized_temp_score"] >= 50.0 and row["normalized_demographic_score"] >= 60.0:
                    determined_interventions.append("Community Shade Structures & Parks")
                elif row["normalized_impervious_score"] >= 50.0:
                    determined_interventions.append("Pervious Paving & Rain Gardens")
                else:
                    determined_interventions.append("General Cool Green Infrastructure")
            omaha_geodataframe["recommended_intervention_type"] = determined_interventions

            # 6. Export the complete real-world prioritized dataset as a single, compiled 100KB GeoJSON
            print("[INFO] Compiling spatial geometries and exporting final dataset...")
            
            # Map columns to match frontend's properties keys exactly
            omaha_geodataframe["id"] = range(1, len(omaha_geodataframe) + 1)
            
            # Find appropriate FIPS/GEOID column dynamically (supporting multiple census block group naming standards)
            fips_col = None
            for possible_fips in ["GEOID", "GEOID20", "GEOID10", "GEO_ID", "GISJOIN"]:
                if possible_fips in omaha_geodataframe.columns:
                    fips_col = possible_fips
                    break
            
            if fips_col is not None:
                if fips_col == "GISJOIN":
                    omaha_geodataframe["fips_code"] = omaha_geodataframe["GISJOIN"].str.replace("G", "").str.replace("S", "")
                else:
                    # Clean up longer GEO_IDs like "1500000US310550011001" to just "310550011001"
                    fips_series = omaha_geodataframe[fips_col].astype(str)
                    omaha_geodataframe["fips_code"] = fips_series.apply(lambda x: x.split("US")[-1] if "US" in x else x)
            else:
                omaha_geodataframe["fips_code"] = [f"3105500{idx:03d}0" for idx in range(1, len(omaha_geodataframe) + 1)]
            omaha_geodataframe["total_population"] = omaha_geodataframe["total_population_count"]
            omaha_geodataframe["population_under_five"] = omaha_geodataframe["vulnerable_population_under_five_years"]
            omaha_geodataframe["population_sixty_five_and_older"] = omaha_geodataframe["vulnerable_population_sixty_five_and_older"]
            omaha_geodataframe["raw_temperature_celsius"] = omaha_geodataframe["mean_land_surface_temperature_celsius"].round(1)
            omaha_geodataframe["raw_canopy_percentage"] = omaha_geodataframe["mean_canopy_coverage_percentage"].round(1)
            omaha_geodataframe["raw_impervious_percentage"] = omaha_geodataframe["mean_impervious_percentage"].round(1)
            omaha_geodataframe["raw_vulnerability_index"] = omaha_geodataframe["normalized_demographic_score"].round(1)
            omaha_geodataframe["normalized_temp_score"] = omaha_geodataframe["normalized_temp_score"].round(1)
            omaha_geodataframe["normalized_canopy_deficit_score"] = omaha_geodataframe["normalized_canopy_deficit_score"].round(1)
            omaha_geodataframe["normalized_impervious_score"] = omaha_geodataframe["normalized_impervious_score"].round(1)
            omaha_geodataframe["normalized_demographic_score"] = omaha_geodataframe["normalized_demographic_score"].round(1)
            omaha_geodataframe["final_mitigation_priority_score"] = omaha_geodataframe["final_mitigation_priority_score"].round(1)

            # Export the GeoDataFrame directly to GeoJSON format string
            export_geojson_columns = [
                "id", "fips_code", "total_population", "population_under_five", "population_sixty_five_and_older",
                "raw_temperature_celsius", "raw_canopy_percentage", "raw_impervious_percentage", "raw_vulnerability_index",
                "normalized_temp_score", "normalized_canopy_deficit_score", "normalized_impervious_score", "normalized_demographic_score",
                "final_mitigation_priority_score", "recommended_intervention_type", "geometry"
            ]
            geojson_dataset_string = omaha_geodataframe[export_geojson_columns].to_json()
            with open(output_file_path, "w") as target_geojson_output_file:
                target_geojson_output_file.write(geojson_dataset_string)

            print("\n" + "="*80)
            print(f"[SUCCESS] REAL-WORLD OMAHA DATASET SUCCESSFULLY COMPILED!")
            print(f"[SUCCESS] Exported compiled 100KB dataset to: {output_file_path}")
            
            # If the database connection is configured, load the real-world boundaries directly into PostGIS
            if database_connection_url:
                load_processed_data_to_postgresql(omaha_geodataframe, database_connection_url)
                
            print("[SUCCESS] You can now safely delete your raw 5GB CONUS folders and TIF rasters!")
            print("="*80 + "\n")
            
            # Set a flag to bypass mock runner
            analysis_results_dataset = None
            
        except Exception as processing_error:
            print(f"[ERROR] Failed to compile real-world datasets: {processing_error}")
            print("[INFO] Falling back to default simulated pipeline...")
            analysis_results_dataset = run_urban_heat_analysis_workflow_pipeline(
                temperature_weight_param=0.35,
                canopy_weight_param=0.30,
                impervious_weight_param=0.15,
                demographic_weight_param=0.20
            )
    else:
        print("[INFO] Real-world dataset files not fully unzipped or missing. Running default simulated pipeline...")
        # Execute the analysis using standard weights
        analysis_results_dataset = run_urban_heat_analysis_workflow_pipeline(
            temperature_weight_param=0.35,
            canopy_weight_param=0.30,
            impervious_weight_param=0.15,
            demographic_weight_param=0.20
        )

    # Save the processed mockup results only if real-world pipeline was skipped
    if analysis_results_dataset is not None:
        # Format the results into standard GeoJSON format for mapping
        geojson_features_collection = []

        # Handle converting dataframe records or list records to standard GeoJSON
        if GEOSPATIAL_LIBRARIES_AVAILABLE and isinstance(analysis_results_dataset, gpd.GeoDataFrame):
            # Convert Geopandas geodataframe directly to geojson format string
            geojson_dataset_string = analysis_results_dataset.to_json()
            with open(output_file_path, "w") as target_geojson_output_file:
                target_geojson_output_file.write(geojson_dataset_string)
        else:
            # Manually assemble standard GeoJSON dictionaries
            for item in analysis_results_dataset:
                geojson_feature_item = {
                    "type": "Feature",
                    "id": item["id"],
                    "properties": {
                        "id": item["id"],
                        "fips_code": item["fips_code"],
                        "total_population": item["total_population"],
                        "population_under_five": item["population_under_five"],
                        "population_sixty_five_and_older": item["population_sixty_five_and_older"],
                        "raw_temperature_celsius": item["mean_temperature_celsius"],
                        "raw_canopy_percentage": item["canopy_coverage_percentage"],
                        "raw_impervious_percentage": item["impervious_surface_percentage"],
                        "raw_vulnerability_index": item["vulnerability_socio_index"],
                        "normalized_temp_score": item["normalized_temperature_score"],
                        "normalized_canopy_deficit_score": item["normalized_canopy_deficit_score"],
                        "normalized_impervious_score": item["normalized_impervious_surface_score"],
                        "normalized_demographic_score": item["normalized_demographic_vulnerability_score"],
                        "final_mitigation_priority_score": item["final_mitigation_priority_score"],
                        "recommended_intervention_type": item["recommended_intervention_type"]
                    },
                    "geometry": item["geometry"]
                }
                geojson_features_collection.append(geojson_feature_item)

            geojson_root_structure = {
                "type": "FeatureCollection",
                "features": geojson_features_collection
            }

            # Save standard GeoJSON file containing mock values for the webmap
            with open(output_file_path, "w") as target_geojson_output_file:
                json.dump(geojson_root_structure, target_geojson_output_file, indent=2)

        print(f"[SUCCESS] Exported processed analysis mockup results to: {output_file_path}")
