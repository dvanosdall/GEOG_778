/* ==============================================================================
   URBAN HEAT MITIGATION DECISION-SUPPORT DASHBOARD - ANALYTICAL MATH ENGINE
   Calculates MCDA scores and custom-rule intervention strategies dynamically
   ============================================================================== */

// Computes 0-100 normalizations, merges variables with weights, and recommends strategies
window.recalculatePrioritizedScenarioResults = (
    rawGeoJsonDataset,
    temperatureWeightParam,
    canopyDeficitWeightParam,
    imperviousWeightParam,
    vulnerabilityWeightParam
) => {
    // Extract raw metrics arrays from GeoJSON features to identify exact bounding limits
    const rawTemperatureValuesList = rawGeoJsonDataset.features.map(feat => feat.properties.raw_temperature_celsius);
    const rawCanopyValuesList = rawGeoJsonDataset.features.map(feat => feat.properties.raw_canopy_percentage);
    const rawImperviousValuesList = rawGeoJsonDataset.features.map(feat => feat.properties.raw_impervious_percentage);
    const rawVulnerabilityValuesList = rawGeoJsonDataset.features.map(feat => feat.properties.raw_vulnerability_index);

    // Identify minimums, maximums, and ranges for linear normalizations (ignoring empty features)
    const minTemperature = Math.min(...rawTemperatureValuesList);
    const maxTemperature = Math.max(...rawTemperatureValuesList);
    const rangeTemperature = maxTemperature - minTemperature || 1.0;

    const minCanopy = Math.min(...rawCanopyValuesList);
    const maxCanopy = Math.max(...rawCanopyValuesList);
    const rangeCanopy = maxCanopy - minCanopy || 1.0;

    const minImpervious = Math.min(...rawImperviousValuesList);
    const maxImpervious = Math.max(...rawImperviousValuesList);
    const rangeImpervious = maxImpervious - minImpervious || 1.0;

    const minVulnerability = Math.min(...rawVulnerabilityValuesList);
    const maxVulnerability = Math.max(...rawVulnerabilityValuesList);
    const rangeVulnerability = maxVulnerability - minVulnerability || 1.0;

    // Sum all raw weights to scale them proportionally to 100% (avoiding scaling distortion)
    const totalWeightParameterSum = temperatureWeightParam + canopyDeficitWeightParam + imperviousWeightParam + vulnerabilityWeightParam;
    const reScaledTempWeight = totalWeightParameterSum > 0 ? (temperatureWeightParam / totalWeightParameterSum) : 0.25;
    const reScaledCanopyWeight = totalWeightParameterSum > 0 ? (canopyDeficitWeightParam / totalWeightParameterSum) : 0.25;
    const reScaledImperviousWeight = totalWeightParameterSum > 0 ? (imperviousWeightParam / totalWeightParameterSum) : 0.25;
    const reScaledVulnerabilityWeight = totalWeightParameterSum > 0 ? (vulnerabilityWeightParam / totalWeightParameterSum) : 0.25;

    // Deep copy and maps attributes to new prioritized variables
    const recalculatedFeaturesList = rawGeoJsonDataset.features.map(originalFeature => {
        const props = originalFeature.properties;

        // Perform linear standardizations: 100 represents max mitigation priority, 0 represents lowest priority
        
        // High surface temperature represents high heat stress priority
        const normalizedTemperatureScore = ((props.raw_temperature_celsius - minTemperature) / rangeTemperature) * 100.0;
        
        // Low tree canopy represents high deficit priority (Inverted normalization)
        const normalizedCanopyDeficitScore = ((maxCanopy - props.raw_canopy_percentage) / rangeCanopy) * 100.0;
        
        // High impervious surfaces represent high storm and thermal stress priority
        const normalizedImperviousScore = ((props.raw_impervious_percentage - minImpervious) / rangeImpervious) * 100.0;
        
        // High demographics vulnerability represents high exposure priority
        const normalizedDemographicScore = ((props.raw_vulnerability_index - minVulnerability) / rangeVulnerability) * 100.0;

        // Compute final Multi-Criteria linear priority score using rescaled weights
        const computedFinalPriorityScore = (
            (normalizedTemperatureScore * reScaledTempWeight) +
            (normalizedCanopyDeficitScore * reScaledCanopyWeight) +
            (normalizedImperviousScore * reScaledImperviousWeight) +
            (normalizedDemographicScore * reScaledVulnerabilityWeight)
        );

        // Classify localized cells to suggest custom physical interventions
        let recommendedInterventionString = "General Cool Infrastructure";
        if (normalizedTemperatureScore >= 60.0 && normalizedCanopyDeficitScore >= 65.0) {
            recommendedInterventionString = "Urban Forestry & Tree Canopy Expansion";
        } else if (normalizedTemperatureScore >= 60.0 && normalizedImperviousScore >= 70.0) {
            recommendedInterventionString = "Cool Roof & Cool Surface Retrofitting";
        } else if (normalizedTemperatureScore >= 50.0 && normalizedDemographicScore >= 60.0) {
            recommendedInterventionString = "Community Shade Structures & Parks";
        } else if (normalizedImperviousScore >= 50.0) {
            recommendedInterventionString = "Pervious Paving & Rain Gardens";
        }

        // Return updated GeoJSON Feature properties node
        return {
            ...originalFeature,
            properties: {
                ...props,
                normalized_temp_score: Number(normalizedTemperatureScore.toFixed(1)),
                normalized_canopy_deficit_score: Number(normalizedCanopyDeficitScore.toFixed(1)),
                normalized_impervious_score: Number(normalizedImperviousScore.toFixed(1)),
                normalized_demographic_score: Number(normalizedDemographicScore.toFixed(1)),
                final_mitigation_priority_score: Number(computedFinalPriorityScore.toFixed(1)),
                recommended_intervention_type: recommendedInterventionString
            }
        };
    });

    return {
        "type": "FeatureCollection",
        "features": recalculatedFeaturesList
    };
};
