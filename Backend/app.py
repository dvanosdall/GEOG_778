# ==============================================================================
# OMAHA URBAN HEAT DECISION-SUPPORT TOOLKIT - FASTAPI BACKEND API
# COMPLETE WEB SERVICE FOR POSTGRESQL/POSTGIS AND MCDA CALCULATIONS
# ==============================================================================

# Import standard python libraries
import os
import json
import math
from typing import List, Optional

# Import FastAPI and Pydantic libraries
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import SQLAlchemy database connection modules
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Text, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Define the database URL, defaulting to local PostgreSQL database "urbanheat"
# Uses environment variables if set, otherwise falls back to standard local credentials
POSTGRES_DATABASE_CONNECTION_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/urbanheat"
)

# Initialize the SQLAlchemy database engine
database_engine_connection = create_engine(POSTGRES_DATABASE_CONNECTION_URL)

# Setup a session maker factory to create database session connections
database_session_maker = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=database_engine_connection
)

# Declare a base class for SQLAlchemy ORM models
BaseDeclarativeModelClass = declarative_base()


# ==============================================================================
# SQLALCHEMY DATABASE ORM MODELS (MATCHING THE POSTGRES SCHEMA)
# ==============================================================================

class CensusBlockGroupDemographicsModel(BaseDeclarativeModelClass):
    """
    SQLAlchemy ORM model representing census tract block group demographic and environmental data.
    """
    __tablename__ = "census_block_group_demographics"

    # Primary key unique identifier
    block_group_id = Column(Integer, primary_key=True, index=True)
    # 12-character census FIPS code identifier
    census_block_group_fips_code = Column(String(12), unique=True, nullable=False, index=True)
    # Total count of population
    total_population_count = Column(Integer, nullable=False)
    # Population under five years old
    vulnerable_population_under_five_years = Column(Integer, nullable=False)
    # Population 65 years and older
    vulnerable_population_sixty_five_and_older = Column(Integer, nullable=False)
    # Median household income
    median_household_income_usd = Column(Numeric(12, 2), nullable=True)


class MultiCriteriaPlanningScenariosModel(BaseDeclarativeModelClass):
    """
    SQLAlchemy ORM model representing saved multi-criteria planning scenarios and their weights.
    """
    __tablename__ = "multi_criteria_planning_scenarios"

    # Primary key identifier for saved scenarios
    scenario_id = Column(Integer, primary_key=True, index=True)
    # Unique name of the planning scenario
    scenario_name = Column(String(255), unique=True, nullable=False)
    # Description of planning scenario intent
    scenario_description = Column(Text, nullable=True)
    # Normalized criteria weights (0.0 to 10.0)
    land_surface_temperature_criterion_weight = Column(Numeric(4, 2), nullable=False, default=1.0)
    tree_canopy_deficit_criterion_weight = Column(Numeric(4, 2), nullable=False, default=1.0)
    impervious_surface_criterion_weight = Column(Numeric(4, 2), nullable=False, default=1.0)
    population_density_criterion_weight = Column(Numeric(4, 2), nullable=False, default=1.0)
    demographic_vulnerability_criterion_weight = Column(Numeric(4, 2), nullable=False, default=1.0)


# ==============================================================================
# FASTAPI APPLICATION & CORS MIDDLEWARE INITIALIZATION
# ==============================================================================

fastapi_application_instance = FastAPI(
    title="Omaha Urban Heat Mitigation API",
    description="REST API to manage datasets, compute Multi-Criteria Decision Analysis, and fetch scenarios.",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing) middleware to allow web frontend files
# running locally (via double-click or local ports) to connect to the backend server
fastapi_application_instance.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# DATABASE SESSION DEPENDENCY INJECTION FUNCTION
# ==============================================================================

def get_database_session_connection():
    """
    Creates and manages a database session connection per HTTP request, closing it after completion.
    """
    active_database_session = database_session_maker()
    try:
        yield active_database_session
    finally:
        active_database_session.close()


# ==============================================================================
# PYDANTIC VALIDATION SCHEMAS FOR API REQUESTS/RESPONSES
# ==============================================================================

class MCDAParametersSchema(BaseModel):
    """
    Pydantic schema to validate incoming weight parameters for real-time MCDA calculations.
    """
    temperature_weight: float = Field(default=7.0, ge=0.0, le=10.0, description="Weight for Land Surface Temperature (0 to 10)")
    canopy_deficit_weight: float = Field(default=6.0, ge=0.0, le=10.0, description="Weight for Tree Canopy deficit (0 to 10)")
    impervious_surface_weight: float = Field(default=3.0, ge=0.0, le=10.0, description="Weight for Impervious Surface density (0 to 10)")
    demographic_vulnerability_weight: float = Field(default=5.0, ge=0.0, le=10.0, description="Weight for Social Vulnerability index (0 to 10)")


class SaveScenarioRequestSchema(BaseModel):
    """
    Pydantic schema to validate request bodies for saving planning scenarios.
    """
    scenario_name: str = Field(..., description="Unique name of the planning scenario")
    scenario_description: Optional[str] = Field(None, description="Optional text description")
    temperature_weight: float = Field(..., ge=0.0, le=10.0)
    canopy_deficit_weight: float = Field(..., ge=0.0, le=10.0)
    impervious_surface_weight: float = Field(..., ge=0.0, le=10.0)
    demographic_vulnerability_weight: float = Field(..., ge=0.0, le=10.0)


# ==============================================================================
# BACKUP SIMULATED DATA GENERATOR (WHEN POSTGRES IS EMPTY OR NOT INSTALLED)
# ==============================================================================

def generate_simulated_omaha_geojson_features():
    """
    Generates a set of simulated Omaha block groups to return if PostgreSQL lacks data during testing.
    """
    # Centers around Omaha, Nebraska
    omahaLatitudeCenter = 41.2586
    omahaLongitudeCenter = -96.0102
    gridRowsCount = 6
    gridColumnsCount = 7
    gridSpacingDegrees = 0.015

    assembled_geojson_features = []

    for rowIndex in range(gridRowsCount):
        for colIndex in range(gridColumnsCount):
            numericalId = (rowIndex * gridColumnsCount) + colIndex + 1
            # Generate a valid 12-digit Census block group GEOID: State (31), County (055), Tract (9800xx), Block Group (1)
            fipsCodeString = f"310559800{numericalId:02d}1"
            
            # Boundary coordinates
            minLong = omahaLongitudeCenter + (colIndex - (gridColumnsCount / 2.0)) * gridSpacingDegrees
            maxLong = minLong + gridSpacingDegrees
            minLat = omahaLatitudeCenter + (rowIndex - (gridRowsCount / 2.0)) * gridSpacingDegrees
            maxLat = minLat + gridSpacingDegrees

            # Spatial gradients for realistic variations
            eastWestGradient = colIndex / gridColumnsCount
            northSouthGradient = rowIndex / gridRowsCount

            # Eastern Omaha is hotter and denser
            tempCelsius = 28.5 + (12.0 * eastWestGradient) + (3.0 * math.sin(northSouthGradient * math.pi))
            canopyPercentage = max(2.0, min(85.0, 75.0 - (70.0 * eastWestGradient) + (10.0 * math.cos(northSouthGradient * math.pi))))
            imperviousPercentage = max(10.0, min(95.0, 15.0 + (75.0 * eastWestGradient) - (15.0 * math.sin(northSouthGradient * math.pi))))
            
            totalPopulation = int(1200 + (2500 * (1.0 - eastWestGradient)) + (800 * math.cos(rowIndex)))
            popUnderFive = int(totalPopulation * (0.04 + (0.05 * eastWestGradient)))
            popSixtyFive = int(totalPopulation * (0.08 + (0.12 * (1.0 - eastWestGradient))))
            vulnerabilityIndex = (eastWestGradient * 80.0) + (northSouthGradient * 20.0)

            polygonCoordinates = [
                [minLong, minLat],
                [maxLong, minLat],
                [maxLong, maxLat],
                [minLong, maxLat],
                [minLong, minLat]
            ]

            featureRecord = {
                "type": "Feature",
                "id": numericalId,
                "properties": {
                    "id": numericalId,
                    "fips_code": fipsCodeString,
                    "total_population": totalPopulation,
                    "population_under_five": popUnderFive,
                    "population_sixty_five_and_older": popSixtyFive,
                    "raw_temperature_celsius": round(tempCelsius, 2),
                    "raw_canopy_percentage": round(canopyPercentage, 2),
                    "raw_impervious_percentage": round(imperviousPercentage, 2),
                    "raw_vulnerability_index": round(vulnerabilityIndex, 2)
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygonCoordinates]
                }
            }
            assembled_geojson_features.append(featureRecord)

    return assembled_geojson_features


# ==============================================================================
# API ENDPOINT ROUTING DEFINITIONS
# ==============================================================================

@fastapi_application_instance.get("/")
def get_root_welcome_status():
    """
    Root status page displaying service information.
    """
    return {
        "status": "Online",
        "service_name": "Omaha Urban Heat Mitigation Decision Support Service",
        "interactive_api_docs_url": "/docs"
    }


@fastapi_application_instance.get("/api/block-groups")
def get_all_block_groups_data(db_session: Session = Depends(get_database_session_connection)):
    """
    Retrieves the raw block group spatial attributes from PostgreSQL, falling back to simulated data if empty.
    """
    try:
        # Check database connectivity and fetch rows if the table exists
        query_result_rows = db_session.query(CensusBlockGroupDemographicsModel).all()
        
        # If the query returns no records, use simulated Omaha data
        if len(query_result_rows) == 0:
            print("[INFO] Database empty. Serving simulated Omaha block group data.")
            simulated_features_collection = generate_simulated_omaha_geojson_features()
            return {
                "type": "FeatureCollection",
                "source": "simulated",
                "features": simulated_features_collection
            }
        
        # Assemble SQL query to extract geometries as GeoJSON string format directly from PostGIS,
        # performing spatial intersections to average canopy and impervious grids, and computing demographic vulnerability.
        raw_spatial_query = text("""
            SELECT bg.block_group_id, bg.census_block_group_fips_code, bg.total_population_count, 
                   bg.vulnerable_population_under_five_years, bg.vulnerable_population_sixty_five_and_older, 
                   COALESCE((SELECT AVG(tc.canopy_coverage_percentage) FROM tree_canopy_cover_grid_cells tc WHERE ST_Intersects(bg.block_group_geometry, tc.grid_cell_geometry)), 15.0) as avg_canopy,
                   COALESCE((SELECT AVG(imp.impervious_surface_percentage) FROM impervious_surface_grid_cells imp WHERE ST_Intersects(bg.block_group_geometry, imp.grid_cell_geometry)), 45.0) as avg_impervious,
                   COALESCE((bg.vulnerable_population_under_five_years + bg.vulnerable_population_sixty_five_and_older)::float / NULLIF(bg.total_population_count, 0) * 100.0, 50.0) as vulnerability_index,
                   ST_AsGeoJSON(bg.block_group_geometry) as geojson_geom 
            FROM census_block_group_demographics bg;
        """)
        
        spatial_query_results = db_session.execute(raw_spatial_query)
        compiled_database_features = []

        # Parse SQL rows and compile standard GeoJSON structures
        for spatial_row in spatial_query_results:
            geometry_dictionary = json.loads(spatial_row.geojson_geom)
            
            # Map database columns to standard properties keys matching frontend requirements
            compiled_feature = {
                "type": "Feature",
                "id": spatial_row.block_group_id,
                "properties": {
                    "id": spatial_row.block_group_id,
                    "fips_code": spatial_row.census_block_group_fips_code,
                    "total_population": spatial_row.total_population_count,
                    "population_under_five": spatial_row.vulnerable_population_under_five_years,
                    "population_sixty_five_and_older": spatial_row.vulnerable_population_sixty_five_and_older,
                    # Retrieve environmental indicators from our spatial subqueries, defaulting temperature realistically
                    "raw_temperature_celsius": 32.5,
                    "raw_canopy_percentage": round(float(spatial_row.avg_canopy), 2),
                    "raw_impervious_percentage": round(float(spatial_row.avg_impervious), 2),
                    "raw_vulnerability_index": round(float(spatial_row.vulnerability_index), 2)
                },
                "geometry": geometry_dictionary
            }
            compiled_database_features.append(compiled_feature)

        return {
            "type": "FeatureCollection",
            "source": "postgresql_postgis",
            "features": compiled_database_features
        }

    except Exception as database_query_error:
        print(f"[WARNING] SQL Query failed: {database_query_error}. Serving simulated Omaha block group data.")
        # Fallback to simulated data if PostgreSQL or PostGIS extensions are missing
        simulated_features_collection = generate_simulated_omaha_geojson_features()
        return {
            "type": "FeatureCollection",
            "source": "simulated_fallback",
            "features": simulated_features_collection
        }


@fastapi_application_instance.post("/api/scenarios/calculate")
def post_recalculate_mitigation_priority_scenario(
    request_weights_params: MCDAParametersSchema,
    db_session: Session = Depends(get_database_session_connection)
):
    """
    Executes the Multi-Criteria Decision Analysis linear combination in the backend.
    """
    # Fetch base block groups
    base_geofeatures_response = get_all_block_groups_data(db_session)
    features_list = base_geofeatures_response["features"]

    # Extract raw data to calculate normalization bounds dynamically
    raw_temperature_values = [feat["properties"]["raw_temperature_celsius"] for feat in features_list]
    raw_canopy_values = [feat["properties"]["raw_canopy_percentage"] for feat in features_list]
    raw_impervious_values = [feat["properties"]["raw_impervious_percentage"] for feat in features_list]
    raw_vulnerability_values = [feat["properties"]["raw_vulnerability_index"] for feat in features_list]

    # Boundaries
    min_temp, max_temp = min(raw_temperature_values), max(raw_temperature_values)
    range_temp = max_temp - min_temp or 1.0

    min_canopy, max_canopy = min(raw_canopy_values), max(raw_canopy_values)
    range_canopy = max_canopy - min_canopy or 1.0

    min_imp, max_imp = min(raw_impervious_values), max(raw_impervious_values)
    range_imp = max_imp - min_imp or 1.0

    min_vuln, max_vuln = min(raw_vulnerability_values), max(raw_vulnerability_values)
    range_vuln = max_vuln - min_vuln or 1.0

    # Rescale weights proportionally to sum up to 1.0
    total_raw_weights_sum = (
        request_weights_params.temperature_weight +
        request_weights_params.canopy_deficit_weight +
        request_weights_params.impervious_surface_weight +
        request_weights_params.demographic_vulnerability_weight
    )

    rescaled_temp_weight = request_weights_params.temperature_weight / total_raw_weights_sum if total_raw_weights_sum > 0 else 0.25
    rescaled_canopy_weight = request_weights_params.canopy_deficit_weight / total_raw_weights_sum if total_raw_weights_sum > 0 else 0.25
    rescaled_imp_weight = request_weights_params.impervious_surface_weight / total_raw_weights_sum if total_raw_weights_sum > 0 else 0.25
    rescaled_vuln_weight = request_weights_params.demographic_vulnerability_weight / total_raw_weights_sum if total_raw_weights_sum > 0 else 0.25

    recalculated_features = []

    # Iterate features to calculate scores
    for feat in features_list:
        props = feat["properties"]

        # Linear standardizations to scale metrics from 0.0 to 100.0
        norm_temp = ((props["raw_temperature_celsius"] - min_temp) / range_temp) * 100.0
        norm_canopy_deficit = ((max_canopy - props["raw_canopy_percentage"]) / range_canopy) * 100.0
        norm_imp = ((props["raw_impervious_percentage"] - min_imp) / range_imp) * 100.0
        norm_vuln = ((props["raw_vulnerability_index"] - min_vuln) / range_vuln) * 100.0

        # Calculate MCDA weighted linear sum
        final_priority_score = (
            (norm_temp * rescaled_temp_weight) +
            (norm_canopy_deficit * rescaled_canopy_weight) +
            (norm_imp * rescaled_imp_weight) +
            (norm_vuln * rescaled_vuln_weight)
        )

        # Apply mitigation recommendations rule engines
        intervention_recommendation = "General Cool Infrastructure"
        if norm_temp >= 60.0 and norm_canopy_deficit >= 65.0:
            intervention_recommendation = "Urban Forestry & Tree Canopy Expansion"
        elif norm_temp >= 60.0 and norm_imp >= 70.0:
            intervention_recommendation = "Cool Roof & Cool Surface Retrofitting"
        elif norm_temp >= 50.0 and norm_vuln >= 60.0:
            intervention_recommendation = "Community Shade Structures & Parks"
        elif norm_imp >= 50.0:
            intervention_recommendation = "Pervious Paving & Rain Gardens"

        # Construct prioritized feature
        prioritized_feature = {
            "type": "Feature",
            "id": feat["id"],
            "properties": {
                **props,
                "normalized_temp_score": round(norm_temp, 1),
                "normalized_canopy_deficit_score": round(norm_canopy_deficit, 1),
                "normalized_impervious_score": round(norm_imp, 1),
                "normalized_demographic_score": round(norm_vuln, 1),
                "final_mitigation_priority_score": round(final_priority_score, 1),
                "recommended_intervention_type": intervention_recommendation
            },
            "geometry": feat["geometry"]
        }
        recalculated_features.append(prioritized_feature)

    return {
        "type": "FeatureCollection",
        "source": base_geofeatures_response["source"],
        "features": recalculated_features
    }


@fastapi_application_instance.post("/api/scenarios")
def post_save_planning_scenario(
    request_body: SaveScenarioRequestSchema,
    db_session: Session = Depends(get_database_session_connection)
):
    """
    Saves a custom planning scenario configuration in the PostgreSQL database.
    """
    try:
        # Create a new scenario database record model
        new_scenario_record = MultiCriteriaPlanningScenariosModel(
            scenario_name=request_body.scenario_name,
            scenario_description=request_body.scenario_description,
            land_surface_temperature_criterion_weight=request_body.temperature_weight,
            tree_canopy_deficit_criterion_weight=request_body.canopy_deficit_weight,
            impervious_surface_criterion_weight=request_body.impervious_surface_weight,
            demographic_vulnerability_criterion_weight=request_body.demographic_vulnerability_weight
        )
        
        # Add to the session transactions list
        db_session.add(new_scenario_record)
        # Save change transactions permanently in PostgreSQL
        db_session.commit()
        # Refresh to populate database-generated fields (like primary keys)
        db_session.refresh(new_scenario_record)

        return {
            "success": True,
            "message": f"Successfully saved scenario '{request_body.scenario_name}' in the database.",
            "scenario_id": new_scenario_record.scenario_id
        }
    except Exception as database_insert_error:
        db_session.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save scenario configuration: {str(database_insert_error)}"
        )


@fastapi_application_instance.get("/api/scenarios")
def get_all_saved_planning_scenarios(db_session: Session = Depends(get_database_session_connection)):
    """
    Queries and returns a list of all saved planning scenarios from the database.
    """
    try:
        query_scenarios_results = db_session.query(MultiCriteriaPlanningScenariosModel).all()
        return query_scenarios_results
    except Exception as database_query_error:
        print(f"[WARNING] SQL scenarios fetch failed: {database_query_error}. Returning empty fallback list.")
        return []


# Run instructions for starting local execution of this REST service
# (Can be triggered via: uvicorn Backend.app:fastapi_application_instance --reload --port 8000)
if __name__ == "__main__":
    import uvicorn
    # Start the server on local host interface port 8000
    uvicorn.run("app:fastapi_application_instance", host="127.0.0.1", port=8000, reload=True)
