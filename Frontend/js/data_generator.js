/* ==============================================================================
   URBAN HEAT MITIGATION DECISION-SUPPORT DASHBOARD - DATA GENERATOR MODULE
   Generates a simulated spatial grid representing Omaha census block groups
   ============================================================================== */

// Generate realistic Omaha grid coordinates and census metrics dynamically in the browser
// to avoid local file CORS fetch blocks when opened without an API server
window.generateOmahaStudyAreaGeometries = () => {
    // Center point coordinates for Omaha, Nebraska
    const omahaLatitudeCenterPoint = 41.2586;
    const omahaLongitudeCenterPoint = -96.0102;
    
    // Grid spatial resolution parameters
    const rowCountGrid = 6;
    const columnCountGrid = 7;
    const spacingDegreesGrid = 0.015;

    // List to collect all generated spatial features
    const assembledGeoJsonFeaturesList = [];

    // Iterate across rows and columns to generate a spatial tile coordinate mesh
    for (let rowIndex = 0; rowIndex < rowCountGrid; rowIndex++) {
        for (let colIndex = 0; colIndex < columnCountGrid; colIndex++) {
            // Calculate sequential identifier values and mock FIPS numbers
            const uniqueNumericalId = (rowIndex * columnCountGrid) + colIndex + 1;
            const fipsCodeString = `3105500${String(uniqueNumericalId).padStart(3, '0')}0`;

            // Calculate exact bounding coordinates for the specific grid box
            const minLongitudeValue = omahaLongitudeCenterPoint + (colIndex - (columnCountGrid / 2.0)) * spacingDegreesGrid;
            const maxLongitudeValue = minLongitudeValue + spacingDegreesGrid;
            const minLatitudeValue = omahaLatitudeCenterPoint + (rowIndex - (rowCountGrid / 2.0)) * spacingDegreesGrid;
            const maxLatitudeValue = minLatitudeValue + spacingDegreesGrid;

            // Compute distance factors representing spatial gradients (e.g. East Omaha vs West Omaha)
            const eastWestDistanceGradient = colIndex / columnCountGrid;
            const northSouthDistanceGradient = rowIndex / rowCountGrid;

            // Temperature gradient: Hot eastern urban core, cooler western green zones
            const averageSurfaceTemperatureCelsius = 28.5 + (12.0 * eastWestDistanceGradient) + (3.0 * Math.sin(northSouthDistanceGradient * Math.PI));

            // Canopy gradient: Very sparse canopy in the east, rich lush forests in the west
            const baseCanopyPercentage = Math.max(2.0, Math.min(85.0, 75.0 - (70.0 * eastWestDistanceGradient) + (10.0 * Math.cos(northSouthDistanceGradient * Math.PI))));

            // Impervious gradient: Densely built industrial/commercial zones in the east/center
            const baseImperviousPercentage = Math.max(10.0, Math.min(95.0, 15.0 + (75.0 * eastWestDistanceGradient) - (15.0 * Math.sin(northSouthDistanceGradient * Math.PI))));

            // Demographic counts: Higher density housing clusters
            const calculatedTotalPopulation = Math.floor(1200 + (2500 * (1.0 - eastWestDistanceGradient)) + (800 * Math.cos(rowIndex)));
            const populationUnderFive = Math.floor(calculatedTotalPopulation * (0.04 + (0.05 * eastWestDistanceGradient)));
            const populationSixtyFiveAndOlder = Math.floor(calculatedTotalPopulation * (0.08 + (0.12 * (1.0 - eastWestDistanceGradient))));

            // Socioeconomic vulnerability gradient (higher score represents more vulnerable populations)
            const calculatedSocioeconomicVulnerabilityIndex = (eastWestDistanceGradient * 80.0) + (northSouthDistanceGradient * 20.0);

            // Assemble coordinates list defining standard polygon outer boundary ring (counter-clockwise)
            const polygonOuterBoundaryCoordinates = [
                [minLongitudeValue, minLatitudeValue],
                [maxLongitudeValue, minLatitudeValue],
                [maxLongitudeValue, maxLatitudeValue],
                [minLongitudeValue, maxLatitudeValue],
                [minLongitudeValue, minLatitudeValue]
            ];

            // Package attributes and coordinates into a standard GeoJSON Feature node
            const geoJsonFeatureItem = {
                "type": "Feature",
                "id": uniqueNumericalId,
                "properties": {
                    "id": uniqueNumericalId,
                    "fips_code": fipsCodeString,
                    "total_population": calculatedTotalPopulation,
                    "population_under_five": populationUnderFive,
                    "population_sixty_five_and_older": populationSixtyFiveAndOlder,
                    "raw_temperature_celsius": Number(averageSurfaceTemperatureCelsius.toFixed(2)),
                    "raw_canopy_percentage": Number(baseCanopyPercentage.toFixed(2)),
                    "raw_impervious_percentage": Number(baseImperviousPercentage.toFixed(2)),
                    "raw_vulnerability_index": Number(calculatedSocioeconomicVulnerabilityIndex.toFixed(2))
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygonOuterBoundaryCoordinates]
                }
            };

            assembledGeoJsonFeaturesList.push(geoJsonFeatureItem);
        }
    }

    return {
        "type": "FeatureCollection",
        "features": assembledGeoJsonFeaturesList
    };
};
