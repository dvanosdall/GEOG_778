/* ==============================================================================
   URBAN HEAT MITIGATION DECISION-SUPPORT DASHBOARD - REACT INTERFACE ENGINE
   Coordinates Redux, renders panel sliders, queries FastAPI, and manages maps
   ============================================================================== */

// Set up raw GeoJSON dataset using our global window generator
const rawOmahaGeoJsonDataset = window.generateOmahaStudyAreaGeometries();

// Setup Kepler.gl's native Redux reducer
const keplerGlReducerInstance = KeplerGl.keplerGlReducer;

// Combine into root reducer
const rootReducerInstance = Redux.combineReducers({
    keplerGl: keplerGlReducerInstance
});

// Create central Redux store injecting middleware tasks
const storeInstance = Redux.createStore(
    rootReducerInstance,
    {},
    Redux.applyMiddleware(KeplerGl.taskMiddleware)
);

// Declare the dashboard component using hooks
const DecisionSupportDashboardApplication = () => {
    // Sliders state (ranges from 0 to 10)
    const [temperatureWeightParam, setTemperatureWeightParam] = React.useState(7);
    const [canopyDeficitWeightParam, setCanopyDeficitWeightParam] = React.useState(6);
    const [imperviousWeightParam, setImperviousWeightParam] = React.useState(3);
    const [vulnerabilityWeightParam, setVulnerabilityWeightParam] = React.useState(5);

    // API connectivity states
    const [useBackendAPI, setUseBackendAPI] = React.useState(false);

    // Selected features state
    const [inspectedBlockGroupRecord, setInspectedBlockGroupRecord] = React.useState(null);

    // Processing status state
    const [isWorkflowProcessing, setIsWorkflowProcessing] = React.useState(false);

    // Redux store dispatch trigger
    const dispatch = ReactRedux.useDispatch();

    // Check if local FastAPI API is online during initial page load
    React.useEffect(() => {
        fetch("http://127.0.0.1:8000/")
            .then(response => response.json())
            .then(data => {
                if (data && data.service_name) {
                    console.log("[INFO] Detected local FastAPI service online! Enabling Backend API Mode.");
                    setUseBackendAPI(true);
                }
            })
            .catch(error => {
                console.log("[INFO] Local FastAPI service offline. Defaulting to standalone browser mockup mode.");
                setUseBackendAPI(false);
            });
    }, []);

    // Recalculate and update the Kepler map layer as soon as API mode state changes or settles
    React.useEffect(() => {
        triggerMCDARecalculationAndRefresh();
    }, [useBackendAPI]);

    // Inspect Kepler's internal UI state changes
    const keplerStateInstance = ReactRedux.useSelector(state => state.keplerGl.omaha_toolkit_map);

    // Sync the custom sidebar inspector automatically whenever a user hovers over or clicks a polygon
    React.useEffect(() => {
        if (keplerStateInstance && keplerStateInstance.visState) {
            const hoveredObjectRecord = keplerStateInstance.visState.hoverInfo;
            const clickedObjectRecord = keplerStateInstance.visState.clicked;

            // Prioritize displaying clicked feature, fall back to hovered feature
            const activeInspectSource = clickedObjectRecord || hoveredObjectRecord;

            if (activeInspectSource && activeInspectSource.object) {
                const propertiesExtract = activeInspectSource.object.properties;
                setInspectedBlockGroupRecord(propertiesExtract);
            } else if (!inspectedBlockGroupRecord && rawOmahaGeoJsonDataset.features.length > 0) {
                // Initialize with first grid cell
                setInspectedBlockGroupRecord(rawOmahaGeoJsonDataset.features[0].properties);
            }
        }
    }, [keplerStateInstance]);

    // Formats any prioritized GeoJSON feature collection and pushes it into the Kepler instance
    const renderDatasetIntoKeplerMap = (calculatedGeoJsonData) => {
        const totalFeatures = calculatedGeoJsonData.features;
        
        // Refresh sidebar inspector to show fresh MCDA scores for the currently selected cell
        if (inspectedBlockGroupRecord) {
            const matchingFreshRecord = totalFeatures.find(feat => feat.properties.id === inspectedBlockGroupRecord.id);
            if (matchingFreshRecord) {
                setInspectedBlockGroupRecord(matchingFreshRecord.properties);
            }
        } else {
            setInspectedBlockGroupRecord(totalFeatures[0].properties);
        }

        // Map calculated columns into Kepler's schema
        const keplerDatasetStructure = {
            info: {
                id: 'omaha_block_groups_dataset',
                label: 'Omaha Mitigation Priorities'
            },
            data: {
                fields: [
                    { name: 'id', type: 'integer' },
                    { name: 'fips_code', type: 'string' },
                    { name: 'total_population', type: 'integer' },
                    { name: 'population_under_five', type: 'integer' },
                    { name: 'population_sixty_five_and_older', type: 'integer' },
                    { name: 'raw_temperature_celsius', type: 'real' },
                    { name: 'raw_canopy_percentage', type: 'real' },
                    { name: 'raw_impervious_percentage', type: 'real' },
                    { name: 'raw_vulnerability_index', type: 'real' },
                    { name: 'normalized_temp_score', type: 'real' },
                    { name: 'normalized_canopy_deficit_score', type: 'real' },
                    { name: 'normalized_impervious_score', type: 'real' },
                    { name: 'normalized_demographic_score', type: 'real' },
                    { name: 'final_mitigation_priority_score', type: 'real' },
                    { name: 'recommended_intervention_type', type: 'string' },
                    { name: 'geometry', type: 'geojson' }
                ],
                rows: totalFeatures.map(feat => [
                    feat.properties.id,
                    feat.properties.fips_code,
                    feat.properties.total_population,
                    feat.properties.population_under_five,
                    feat.properties.population_sixty_five_and_older,
                    feat.properties.raw_temperature_celsius,
                    feat.properties.raw_canopy_percentage,
                    feat.properties.raw_impervious_percentage,
                    feat.properties.raw_vulnerability_index,
                    feat.properties.normalized_temp_score,
                    feat.properties.normalized_canopy_deficit_score,
                    feat.properties.normalized_impervious_score,
                    feat.properties.normalized_demographic_score,
                    feat.properties.final_mitigation_priority_score,
                    feat.properties.recommended_intervention_type,
                    feat.geometry
                ])
            }
        };

        // Layout styles and mapping styles for choropleth layers
        const keplerConfigStructure = {
            version: 'v1',
            config: {
                visState: {
                    layers: [
                        {
                            id: 'omaha_priority_choropleth_layer',
                            type: 'geojson',
                            config: {
                                dataId: 'omaha_block_groups_dataset',
                                label: 'Omaha Priority Level',
                                color: [255, 153, 0],
                                columns: { geojson: 'geometry' },
                                isVisible: true,
                                visConfig: {
                                    opacity: 0.75,
                                    strokeColor: [255, 255, 255],
                                    strokeOpacity: 0.3,
                                    thickness: 0.8,
                                    colorRange: {
                                        name: 'Global Warm',
                                        type: 'sequential',
                                        colors: ['#fef0d9', '#fdd49e', '#fdbb84', '#fc8d59', '#ef6548', '#d7301f', '#990000']
                                    },
                                    colorField: {
                                        name: 'final_mitigation_priority_score',
                                        type: 'real'
                                    }
                                }
                            }
                        }
                    ],
                    interactionConfig: {
                        tooltip: {
                            fieldsToShow: [
                                { name: 'fips_code', format: null },
                                { name: 'final_mitigation_priority_score', format: null },
                                { name: 'raw_temperature_celsius', format: null },
                                { name: 'raw_canopy_percentage', format: null },
                                { name: 'recommended_intervention_type', format: null }
                            ],
                            enabled: true
                        },
                        brush: { enabled: false }
                    }
                },
                mapState: {
                    bearing: 0,
                    dragRotate: false,
                    latitude: 41.2586,
                    longitude: -96.0102,
                    pitch: 0,
                    zoom: 11,
                    isSplit: false
                },
                mapStyle: {
                    styleType: 'dark',
                    topLayerGroups: {},
                    visibleLayerGroups: {
                        label: true,
                        road: true,
                        border: true,
                        building: true,
                        water: true,
                        land: true
                    }
                }
            }
        };

        // Dispatch dataset and styling to the Kepler map instance
        dispatch(KeplerGl.addDataToMap({
            datasets: [keplerDatasetStructure],
            options: { keepExistingConfig: false },
            config: keplerConfigStructure
        }));

        setIsWorkflowProcessing(false);
    };

    // Orchestrates the calculation request, choosing between backend API or standalone browser engine
    const triggerMCDARecalculationAndRefresh = () => {
        setIsWorkflowProcessing(true);

        if (useBackendAPI) {
            // Fetch calculations from local FastAPI server
            fetch("http://127.0.0.1:8000/api/scenarios/calculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    temperature_weight: Number(temperatureWeightParam),
                    canopy_deficit_weight: Number(canopyDeficitWeightParam),
                    impervious_surface_weight: Number(imperviousWeightParam),
                    demographic_vulnerability_weight: Number(vulnerabilityWeightParam)
                })
            })
            .then(response => {
                if (!response.ok) throw new Error("FastAPI calculations query failed.");
                return response.json();
            })
            .then(calculatedGeoJsonData => {
                console.log("[INFO] Recalculation fetched from FastAPI Backend API successfully.");
                renderDatasetIntoKeplerMap(calculatedGeoJsonData);
            })
            .catch(error => {
                console.warn("[WARNING] Backend API calculation failed. Falling back to local browser engine:", error);
                executeInBrowserLocalRecalculation();
            });
        } else {
            executeInBrowserLocalRecalculation();
        }
    };

    // Runs browser calculations locally inside browser memory
    const executeInBrowserLocalRecalculation = () => {
        setTimeout(() => {
            const calculatedGeoJsonData = window.recalculatePrioritizedScenarioResults(
                rawOmahaGeoJsonDataset,
                Number(temperatureWeightParam),
                Number(canopyDeficitWeightParam),
                Number(imperviousWeightParam),
                Number(vulnerabilityWeightParam)
            );
            renderDatasetIntoKeplerMap(calculatedGeoJsonData);
        }, 300);
    };

    // Package calculated metrics as GeoJSON and download locally
    const exportComputedGeoJsonFile = () => {
        const outputCalculatedCollection = window.recalculatePrioritizedScenarioResults(
            rawOmahaGeoJsonDataset,
            Number(temperatureWeightParam),
            Number(canopyDeficitWeightParam),
            Number(imperviousWeightParam),
            Number(vulnerabilityWeightParam)
        );

        const geoJsonStringData = JSON.stringify(outputCalculatedCollection, null, 2);
        const fileBlobAttachment = new Blob([geoJsonStringData], { type: 'application/json' });
        const blobAttachmentUrl = URL.createObjectURL(fileBlobAttachment);

        const downloadAnchorElement = document.createElement('a');
        downloadAnchorElement.href = blobAttachmentUrl;
        downloadAnchorElement.download = `omaha_mitigation_priorities_temp${temperatureWeightParam}_canopy${canopyDeficitWeightParam}.geojson`;
        document.body.appendChild(downloadAnchorElement);
        downloadAnchorElement.click();
        document.body.removeChild(downloadAnchorElement);
        URL.revokeObjectURL(blobAttachmentUrl);
    };

    // Recalculate local variables to display real-time dashboard card stats
    const currentScenarioCalculatedGeojson = window.recalculatePrioritizedScenarioResults(
        rawOmahaGeoJsonDataset,
        Number(temperatureWeightParam),
        Number(canopyDeficitWeightParam),
        Number(imperviousWeightParam),
        Number(vulnerabilityWeightParam)
    );

    // Sum vulnerable residents in block groups with priority score >= 60.0
    const totalProtectedVulnerablePopulation = currentScenarioCalculatedGeojson.features
        .filter(feat => feat.properties.final_mitigation_priority_score >= 60.0)
        .reduce((accum, feat) => accum + feat.properties.total_population, 0);

    // Compute average prioritization score across the full spatial mesh
    const summedPriorityScores = currentScenarioCalculatedGeojson.features
        .reduce((accum, feat) => accum + feat.properties.final_mitigation_priority_score, 0);
    const averagePriorityScoreValue = (summedPriorityScores / currentScenarioCalculatedGeojson.features.length).toFixed(1);

    return React.createElement(
        'div',
        { id: 'dashboard-application-container' },
        
        // Sidebar control panel
        React.createElement(
            'div',
            { id: 'control-and-inspection-panel' },
            
            // Drawer Header Node
            React.createElement(
                'div',
                { className: 'panel-header-container' },
                React.createElement('h1', { className: 'panel-header-title' }, 'Urban Heat Toolkit'),
                React.createElement('p', { className: 'panel-header-subtitle' }, 'Multi-Criteria Decision-Support Decision Engine for Omaha, NE'),
                
                // Connection Mode indicator Banner
                useBackendAPI ? 
                    React.createElement('span', { className: 'connection-mode-banner connection-mode-online' }, 'Database Connected') :
                    React.createElement('span', { className: 'connection-mode-banner connection-mode-offline' }, 'Offline Mockup Mode')
            ),

            // Section 1: Parameter Weight Sliders
            React.createElement(
                'div',
                { className: 'panel-section-container' },
                React.createElement('h2', { className: 'section-title-label' }, '1. Planning Criteria Weights'),
                
                // Temperature Weight slider
                React.createElement(
                    'div',
                    { className: 'criteria-weight-slider-group' },
                    React.createElement('div', { className: 'slider-label-row' },
                        React.createElement('span', { className: 'slider-name-label' }, 'Land Surface Temperature (LST)'),
                        React.createElement('span', { className: 'slider-value-display' }, temperatureWeightParam)
                    ),
                    React.createElement('input', {
                        type: 'range', min: 0, max: 10,
                        value: temperatureWeightParam,
                        className: 'custom-range-slider-input',
                        onChange: (evt) => setTemperatureWeightParam(Number(evt.target.value))
                    })
                ),

                // Canopy Deficit weight slider
                React.createElement(
                    'div',
                    { className: 'criteria-weight-slider-group' },
                    React.createElement('div', { className: 'slider-label-row' },
                        React.createElement('span', { className: 'slider-name-label' }, 'Tree Canopy Deficit'),
                        React.createElement('span', { className: 'slider-value-display' }, canopyDeficitWeightParam)
                    ),
                    React.createElement('input', {
                        type: 'range', min: 0, max: 10,
                        value: canopyDeficitWeightParam,
                        className: 'custom-range-slider-input',
                        onChange: (evt) => setCanopyDeficitWeightParam(Number(evt.target.value))
                    })
                ),

                // Impervious surface weight slider
                React.createElement(
                    'div',
                    { className: 'criteria-weight-slider-group' },
                    React.createElement('div', { className: 'slider-label-row' },
                        React.createElement('span', { className: 'slider-name-label' }, 'Impervious Surfaces'),
                        React.createElement('span', { className: 'slider-value-display' }, imperviousWeightParam)
                    ),
                    React.createElement('input', {
                        type: 'range', min: 0, max: 10,
                        value: imperviousWeightParam,
                        className: 'custom-range-slider-input',
                        onChange: (evt) => setImperviousWeightParam(Number(evt.target.value))
                    })
                ),

                // Socioeconomic vulnerability weight slider
                React.createElement(
                    'div',
                    { className: 'criteria-weight-slider-group' },
                    React.createElement('div', { className: 'slider-label-row' },
                        React.createElement('span', { className: 'slider-name-label' }, 'Social Vulnerability'),
                        React.createElement('span', { className: 'slider-value-display' }, vulnerabilityWeightParam)
                    ),
                    React.createElement('input', {
                        type: 'range', min: 0, max: 10,
                        value: vulnerabilityWeightParam,
                        className: 'custom-range-slider-input',
                        onChange: (evt) => setVulnerabilityWeightParam(Number(evt.target.value))
                    })
                ),

                // Recalculate dispatch button
                React.createElement('button', {
                    className: 'action-button-element',
                    style: { marginTop: '16px', backgroundColor: '#10b981' },
                    onClick: triggerMCDARecalculationAndRefresh
                }, 'Apply weights & Recalculate')
            ),

            // Section 2: Summary Stats cards
            React.createElement(
                'div',
                { className: 'panel-section-container' },
                React.createElement('h2', { className: 'section-title-label' }, '2. Scenario Statistics'),
                React.createElement(
                    'div',
                    { className: 'summary-statistics-cards-grid' },
                    
                    React.createElement('div', { className: 'metric-card-element' },
                        React.createElement('span', { className: 'metric-card-label' }, 'Avg Priority Score'),
                        React.createElement('span', { className: 'metric-card-value-text' }, `${averagePriorityScoreValue}/100`),
                        React.createElement('span', { className: 'metric-card-sub-text' }, 'Across Study Area')
                    ),

                    React.createElement('div', { className: 'metric-card-element' },
                        React.createElement('span', { className: 'metric-card-label' }, 'High Priority Pop'),
                        React.createElement('span', { className: 'metric-card-value-text' }, totalProtectedVulnerablePopulation.toLocaleString()),
                        React.createElement('span', { className: 'metric-card-sub-text', style: { color: '#fb923c' } }, 'Residents in focus zones')
                    )
                )
            ),

            // Section 3: Geographic focus area metrics Inspector
            React.createElement(
                'div',
                { className: 'panel-section-container', style: { flexGrow: 1, borderBottom: 'none' } },
                React.createElement('h2', { className: 'section-title-label' }, '3. Focus Area Inspection'),
                
                inspectedBlockGroupRecord ? React.createElement(
                    'div',
                    { className: 'feature-inspector-container' },
                    React.createElement('div', { className: 'inspector-row-item' },
                        React.createElement('span', { className: 'inspector-row-label-text' }, 'Block Group FIPS'),
                        React.createElement('span', { className: 'inspector-row-value-text', style: { color: '#38bdf8' } }, inspectedBlockGroupRecord.fips_code)
                    ),
                    React.createElement('div', { className: 'inspector-row-item' },
                        React.createElement('span', { className: 'inspector-row-label-text' }, 'LST Temperature'),
                        React.createElement('span', { className: 'inspector-row-value-text' }, `${inspectedBlockGroupRecord.raw_temperature_celsius}°C`)
                    ),
                    React.createElement('div', { className: 'inspector-row-item' },
                        React.createElement('span', { className: 'inspector-row-label-text' }, 'Tree Canopy Cover'),
                        React.createElement('span', { className: 'inspector-row-value-text' }, `${inspectedBlockGroupRecord.raw_canopy_percentage}%`)
                    ),
                    React.createElement('div', { className: 'inspector-row-item' },
                        React.createElement('span', { className: 'inspector-row-label-text' }, 'Impervious Surfaces'),
                        React.createElement('span', { className: 'inspector-row-value-text' }, `${inspectedBlockGroupRecord.raw_impervious_percentage}%`)
                    ),
                    React.createElement('div', { className: 'inspector-row-item' },
                        React.createElement('span', { className: 'inspector-row-label-text' }, 'Demographics Count'),
                        React.createElement('span', { className: 'inspector-row-value-text' }, inspectedBlockGroupRecord.total_population ? inspectedBlockGroupRecord.total_population.toLocaleString() : 'N/A')
                    ),
                    React.createElement('div', { className: 'inspector-row-item', style: { fontWeight: '700', borderBottom: 'none' } },
                        React.createElement('span', { className: 'inspector-row-label-text', style: { color: '#f1f5f9' } }, 'Final Priority Score'),
                        React.createElement('span', { className: 'inspector-row-value-text', style: { color: '#fb923c', fontSize: '14px' } }, `${inspectedBlockGroupRecord.final_mitigation_priority_score}/100`)
                    ),

                    // Heuristics mitigation Strategy banner
                    React.createElement(
                        'div',
                        { className: 'intervention-recommendation-callout-box' },
                        React.createElement('div', { className: 'intervention-callout-header' }, 'Recommended Interventions'),
                        React.createElement('div', { className: 'intervention-callout-value-text' }, inspectedBlockGroupRecord.recommended_intervention_type || 'General Cool Infrastructure')
                    )
                ) : React.createElement('p', { style: { fontSize: '12px', color: '#64748b', margin: 0 } }, 'Hover over or click on any map polygon zone to inspect metrics.'),

                // Download GeoJSON button
                React.createElement('button', {
                    className: 'action-button-element',
                    style: { marginTop: '24px' },
                    onClick: exportComputedGeoJsonFile
                }, 'Export Scenario GeoJSON')
            )
        ),

        // Mapping viewport wrapper
        React.createElement(
            'div',
            { id: 'map-visualization-viewport' },
            
            // Kepler component
            React.createElement(KeplerGl.KeplerGl, {
                id: 'omaha_toolkit_map',
                width: window.innerWidth - 420,
                height: window.innerHeight,
                mapboxApiAccessToken: 'pk.eyJ1IjoibW9ja2VkdG9rZW4iLCJhIjoiY2p4NDV2cmx3MDB6ZDN6bzh2b3QycTJkayJ9.mockedtoken_notneeded'
            }),

            // Loading screen overlay during MCDA processing runs
            isWorkflowProcessing ? React.createElement(
                'div',
                { className: 'global-loading-screen-overlay' },
                React.createElement('div', { className: 'loading-spinner-element' }),
                React.createElement('p', { className: 'loading-status-text' }, 'Recalculating spatial planning indicators...')
            ) : null
        )
    );
};

// Render layout mounted into Redux Provider tags
ReactDOM.render(
    React.createElement(
        ReactRedux.Provider,
        { store: storeInstance },
        React.createElement(DecisionSupportDashboardApplication)
    ),
    document.getElementById('dashboard-application-container')
);
