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


def load_census_demographics_dataset(census_demographics_file_path):
    """
    Loads the US Census American Community Survey (ACS) block group demographic boundaries and attributes.
    """
    # Check library availability
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        print("[WARNING] Geospatial libraries are not available. Returning simulated demographic vector metadata.")
        return {"status": "Simulated Census Demographics load successful"}

    # Load census block group shapefile containing population and socioeconomic attributes
    census_demographics_geodataframe = gpd.read_file(census_demographics_file_path)

    # Convert coordinate reference system to EPSG:4326 for consistency with map displays
    if census_demographics_geodataframe.crs != "EPSG:4326":
        # Transform the vector coordinates
        census_demographics_geodataframe = census_demographics_geodataframe.to_crs("EPSG:4326")

    return census_demographics_geodataframe


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

        # Iterate through each census block group record in the geodataframe
        for geo_index, block_group_row in census_demographics_geodataframe.iterrows():
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
    # Execute the analysis using standard weights
    analysis_results_dataset = run_urban_heat_analysis_workflow_pipeline(
        temperature_weight_param=0.35,
        canopy_weight_param=0.30,
        impervious_weight_param=0.15,
        demographic_weight_param=0.20
    )

    # Save the processed mockup results to a JSON file so the frontend application can load it
    output_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Frontend", "data")
    
    # Create the output data folder if it does not exist
    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path)

    output_file_path = os.path.join(output_directory_path, "omaha_urban_heat_priority_data.json")

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
                "properties": {
                    "id": item["id"],
                    "fips_code": item["fips_code"],
                    "total_population": item["total_population"],
                    "population_under_five": item["population_under_five"],
                    "population_sixty_five_and_older": item["population_sixty_five_and_older"],
                    "mean_temperature_celsius": item["mean_temperature_celsius"],
                    "canopy_coverage_percentage": item["canopy_coverage_percentage"],
                    "impervious_surface_percentage": item["impervious_surface_percentage"],
                    "vulnerability_socio_index": item["vulnerability_socio_index"],
                    "normalized_temperature_score": item["normalized_temperature_score"],
                    "normalized_canopy_deficit_score": item["normalized_canopy_deficit_score"],
                    "normalized_impervious_surface_score": item["normalized_impervious_surface_score"],
                    "normalized_demographic_vulnerability_score": item["normalized_demographic_vulnerability_score"],
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
