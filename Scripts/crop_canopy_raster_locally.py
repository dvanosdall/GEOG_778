# ==============================================================================
# OMAHA URBAN HEAT TOOLKIT - RASTER CROPPING AND SPACE-SAVING UTILITY
# CROPS THE GIANT 5.5GB CONUS RASTER DOWN TO OMAHA AND SAVES AS A 5MB TIF
# ==============================================================================

# Import standard python libraries
import os
import numpy as np

# Try importing spatial libraries
try:
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask
    GEOSPATIAL_LIBRARIES_AVAILABLE = True
except ImportError:
    GEOSPATIAL_LIBRARIES_AVAILABLE = False


def crop_massive_conus_canopy_raster_to_omaha_boundary():
    """
    Crops the giant 5.5GB CONUS tree canopy cover raster down to Douglas County (Omaha) and saves it as a 5MB local file.
    """
    if not GEOSPATIAL_LIBRARIES_AVAILABLE:
        print("[ERROR] Geospatial libraries (geopandas, rasterio) are not installed in your active environment!")
        return

    # Define raw file paths
    raw_census_shapefile_path = "C:/Work/UrbanHeat/Data/nhgis0001_shape/nhgis0001_shapefile_tl2020_310_blck_grp_2020/NE_blck_grp_2020.shp"
    raw_canopy_conus_raster_path = "C:/Work/UrbanHeat/Data/science_tcc_conus_2025_v2025-6_wgs84/science_tcc_conus_wgs84_v2025-6_20250101_20251231.tif"
    output_cropped_canopy_raster_path = "C:/Work/UrbanHeat/Data/omaha_tree_canopy_cover.tif"

    # Verify that both the shapefile and raster exist on disk
    if not os.path.exists(raw_census_shapefile_path):
        print(f"[ERROR] Census shapefile not found at: {raw_census_shapefile_path}")
        return
    if not os.path.exists(raw_canopy_conus_raster_path):
        print(f"[ERROR] Giant 5.5GB CONUS Tree Canopy raster not found at: {raw_canopy_conus_raster_path}")
        return

    print("\n" + "="*80)
    print("[INFO] INITIATING LOCAL SPACE-SAVING RASTER CROPPING PROCESS...")
    print("="*80 + "\n")

    try:
        # Load census block group boundaries shapefile
        print("[1/3] Loading Nebraska Census Block Group boundaries...")
        census_boundaries_dataframe = gpd.read_file(raw_census_shapefile_path)

        # Filter block groups to keep only Douglas County (FIPS 055) which contains Omaha
        print("[INFO] Filtering boundaries specifically to Douglas County, NE (Omaha)...")
        douglas_county_boundaries = census_boundaries_dataframe[census_boundaries_dataframe["COUNTYFP"] == "055"]

        # Open the giant CONUS Tree Canopy raster
        print("[2/3] Opening the giant 5.5GB CONUS Tree Canopy raster file (please wait)...")
        with rasterio.open(raw_canopy_conus_raster_path) as raw_conus_raster_dataset:
            # Ensure the Douglas County geometries are in the exact same projection as the raster
            if douglas_county_boundaries.crs != raw_conus_raster_dataset.crs:
                print(f"[INFO] Reprojecting boundaries from {douglas_county_boundaries.crs} to match raster projection: {raw_conus_raster_dataset.crs}...")
                douglas_county_boundaries = douglas_county_boundaries.to_crs(raw_conus_raster_dataset.crs)

            # Package the polygon geometries as a single multi-polygon list for rasterio masking
            boundary_polygons_geometry_list = list(douglas_county_boundaries.geometry)

            # Crop (cookie-cutter) the giant raster using the Douglas County polygon boundaries
            print("[INFO] Executing spatial crop (clipping the 5.5GB raster down to Douglas County)...")
            cropped_raster_pixels, cropped_raster_transform = mask(
                raw_conus_raster_dataset,
                boundary_polygons_geometry_list,
                crop=True
            )

            # Extract metadata from raw raster to configure output format correctly
            output_raster_metadata = raw_conus_raster_dataset.meta.copy()
            
            # Update metadata dimensions and affine transform coordinates for the newly cropped raster
            output_raster_metadata.update({
                "height": cropped_raster_pixels.shape[1],
                "width": cropped_raster_pixels.shape[2],
                "transform": cropped_raster_transform
            })

            # Save only the newly cropped 5MB local Omaha raster file on disk
            print(f"[3/3] Saving the tiny cropped Omaha canopy raster to: {output_cropped_canopy_raster_path}")
            with rasterio.open(output_cropped_canopy_raster_path, "w", **output_raster_metadata) as output_cropped_file:
                output_cropped_file.write(cropped_raster_pixels)

        print("\n" + "="*80)
        print("[SUCCESS] CROPPING PROCESS COMPLETE!")
        print(f"[SUCCESS] Saved 5MB Omaha Tree Canopy Raster to: {output_cropped_canopy_raster_path}")
        print("[SUCCESS] You can now safely delete the entire 5.5GB CONUS folder:")
        print("          'Data/science_tcc_conus_2025_v2025-6_wgs84/'")
        print("          This will shrink your folder size from 5.8 GB to just 130 MB!")
        print("="*80 + "\n")

    except Exception as cropping_error:
        print(f"[ERROR] Failed to crop raster: {cropping_error}")


# Execute utility function on start
if __name__ == "__main__":
    crop_massive_conus_canopy_raster_to_omaha_boundary()
