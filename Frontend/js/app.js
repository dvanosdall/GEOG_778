/* ==============================================================================
   URBAN HEAT MITIGATION DECISION-SUPPORT DASHBOARD - REACT INTERFACE ENGINE
   Coordinates Redux, renders panel sliders, queries FastAPI, and manages maps
   ============================================================================== */

// Check if the required CDN libraries loaded successfully, otherwise display a helpful network error on screen
if (!window.React || !window.ReactDOM || !window.Redux || !window.KeplerGl) {
    document.addEventListener("DOMContentLoaded", () => {
        const errorContainer = document.getElementById("dashboard-application-container");
        if (errorContainer) {
            errorContainer.style.padding = "40px";
            errorContainer.style.display = "flex";
            errorContainer.style.flexDirection = "column";
            errorContainer.style.alignItems = "center";
            errorContainer.style.justifyContent = "center";
            errorContainer.style.height = "100vh";
            errorContainer.style.backgroundColor = "#0f172a";
            errorContainer.style.color = "#f8fafc";
            errorContainer.style.textAlign = "center";
            errorContainer.style.fontFamily = "'Inter', sans-serif";

            errorContainer.innerHTML = `
                <div style="max-width: 600px; background-color: #1e293b; border: 1px solid #e11d48; border-radius: 8px; padding: 32px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                    <h1 style="color: #f43f5e; font-size: 24px; margin-bottom: 16px; font-weight: 700;">Network Connection Blocked</h1>
                    <p style="font-size: 14px; line-height: 1.6; color: #94a3b8; margin-bottom: 20px;">
                        It looks like your local computer's corporate firewall or security proxy is blocking access to our mapping CDNs (specifically <strong>unpkg.com</strong>).
                    </p>
                    <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin-bottom: 20px; font-weight: 500;">
                        This is completely expected on secured corporate networks!
                    </p>
                    <p style="font-size: 13px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px;">
                        To run and test this toolkit successfully, you can:
                    </p>
                    <div style="text-align: left; margin: 0 auto; max-width: 480px; font-size: 13px; color: #cbd5e1; line-height: 1.8; background-color: #0f172a; padding: 20px; border-radius: 6px; border: 1px solid #334155;">
                        1. <strong>Run on another PC</strong>: Transfer this project folder to a personal or standard network with full internet access.<br>
                        2. <strong>Work offline</strong>: Since we created a full set of stubs, you can continue to edit Python and PostgreSQL schemas locally.
                    </div>
                </div>
            `;
        }
    });
    // Stop executing the rest of the script to avoid syntax and undefined errors
    throw new Error("Missing CDN dependencies due to network proxy blocks.");
}

// Set the global Mapbox GL access token directly to ensure standard Mapbox layers authenticate successfully
console.log("[INFO] Checking Globals:", window.mapboxgl, window.urbanHeatApplicationConfig);
if (window.mapboxgl && window.urbanHeatApplicationConfig) {
    const resolvedToken = (window.urbanHeatApplicationConfig.mapboxPublicAccessToken && window.urbanHeatApplicationConfig.mapboxPublicAccessToken.startsWith('pk.')) ?
        window.urbanHeatApplicationConfig.mapboxPublicAccessToken :
        (localStorage.getItem('mapbox_token') || 'pk.placeholder');
    window.mapboxgl.accessToken = resolvedToken;
    console.log("[INFO] Global Mapbox Token Set:", window.mapboxgl.accessToken);
}

// Set up raw GeoJSON dataset using our global window generator
const rawOmahaGeoJsonDataset = window.generateOmahaStudyAreaGeometries();

// Setup Kepler.gl's native Redux reducer
const keplerGlReducerInstance = KeplerGl.keplerGlReducer;

// Combine into root reducer
const rootReducerInstance = Redux.combineReducers({
    keplerGl: keplerGlReducerInstance
});

// Create central Redux store injecting middleware tasks
var keplerMiddlewares;
if (window.KeplerGl && typeof window.KeplerGl.enhanceReduxMiddleware === "function") {
    keplerMiddlewares = window.KeplerGl.enhanceReduxMiddleware([]);
} else {
    keplerMiddlewares = [];
}

const storeInstance = Redux.createStore(
    rootReducerInstance,
    {},
    Redux.applyMiddleware.apply(null, keplerMiddlewares)
);

// Declare the dashboard component using hooks
const DecisionSupportDashboardApplication = () => {
    // Sliders state (ranges from 0 to 10)
    const [temperatureWeightParam, setTemperatureWeightParam] = React.useState(7);
    const [canopyDeficitWeightParam, setCanopyDeficitWeightParam] = React.useState(6);
    const [imperviousWeightParam, setImperviousWeightParam] = React.useState(3);
    const [vulnerabilityWeightParam, setVulnerabilityWeightParam] = React.useState(5);

    // API connectivity states (initially null to prevent clashing datasets during startup checks)
    const [useBackendAPI, setUseBackendAPI] = React.useState(null);

    // Selected features state
    const [inspectedBlockGroupRecord, setInspectedBlockGroupRecord] = React.useState(null);

    // Processing status state
    const [isWorkflowProcessing, setIsWorkflowProcessing] = React.useState(false);

    // About Dialog status state
    const [isAboutModalOpen, setIsAboutModalOpen] = React.useState(false);

    // State for Mapbox Token input field
    const [mapboxTokenInput, setMapboxTokenInput] = React.useState(localStorage.getItem('mapbox_token') || '');

    // Function to save the token to browser local storage and reload the page
    const handleSaveMapboxToken = () => {
        if (mapboxTokenInput.trim().startsWith('pk.')) {
            localStorage.setItem('mapbox_token', mapboxTokenInput.trim());
            alert("Mapbox token saved successfully! Reloading map...");
            window.location.reload();
        } else if (mapboxTokenInput.trim() === '') {
            localStorage.removeItem('mapbox_token');
            alert("Mapbox token removed. Reloading map...");
            window.location.reload();
        } else {
            alert("Invalid token format! Mapbox public tokens must start with 'pk.'.");
        }
    };

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
        if (useBackendAPI !== null) {
            triggerMCDARecalculationAndRefresh();
        }
    }, [useBackendAPI]);

    // Inspect Kepler's internal UI state changes
    const keplerStateInstance = ReactRedux.useSelector(state => state.keplerGl.map);

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
            }
        }
    }, [keplerStateInstance]);

    // Formats any prioritized GeoJSON feature collection and pushes it into the Kepler instance
    const renderDatasetIntoKeplerMap = (calculatedGeoJsonData) => {
        const totalFeatures = calculatedGeoJsonData.features;

        // Refresh sidebar inspector to show fresh MCDA scores for the currently selected cell
        if (inspectedBlockGroupRecord) {
            const matchingFreshRecord = totalFeatures.find(feat => feat.properties.id === inspectedBlockGroupRecord.id);
            setInspectedBlockGroupRecord(matchingFreshRecord ? matchingFreshRecord.properties : totalFeatures[0].properties);
        } else if (totalFeatures.length > 0) {
            setInspectedBlockGroupRecord(totalFeatures[0].properties);
        }

        const scores = calculatedGeoJsonData.features.map(feat => feat.properties.final_mitigation_priority_score);
        console.log("[INFO] Calculated priority score list:", scores);

        // Parse the calculated GeoJSON dataset using Kepler's native GeoJSON processor
        const processedKeplerData = KeplerGl.processGeojson ?
            KeplerGl.processGeojson(calculatedGeoJsonData) :
            KeplerGl.processors.processGeojson(calculatedGeoJsonData);

        console.log("[INFO] Processed Kepler Data:", processedKeplerData);
        console.log("[INFO] Processed fields names:", processedKeplerData.fields.map(f => f.name));

        const detectedFieldObj = processedKeplerData.fields.find(field => field.name === 'final_mitigation_priority_score');
        const priorityScoreFieldType = detectedFieldObj ? detectedFieldObj.type : 'real';
        console.log("[INFO] Dynamic field type of final_mitigation_priority_score:", priorityScoreFieldType);

        // Dynamically generated IDs to bypass Kepler.gl state reconciliation/race condition conflicts
        const uniqueDatasetId = `omaha_block_groups_dataset_${Date.now()}`;
        const uniqueLayerId = `omaha_priority_layer_${Date.now()}`;

        // Format dataset structure for Kepler.gl ingestion
        const keplerDatasetStructure = {
            info: {
                id: uniqueDatasetId,
                label: 'Omaha Mitigation Priorities'
            },
            data: processedKeplerData
        };

        // Layout styles and mapping styles for choropleth layers
        const keplerConfigStructure = {
            version: 'v1',
            config: {
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
                    styleType: 'dark'
                },
                visState: {
                    layers: [
                        {
                            id: uniqueLayerId,
                            type: 'geojson',
                            config: {
                                dataId: uniqueDatasetId,
                                label: 'Omaha Mitigation Priorities',
                                color: [18, 147, 154],
                                columns: {
                                    geojson: 'geojson'
                                },
                                isVisible: true,
                                visConfig: {
                                    opacity: 0.8,
                                    strokeOpacity: 0.8,
                                    thickness: 0.5,
                                    strokeColor: [255, 255, 255],
                                    colorRange: {
                                        name: 'Colorblind-Safe Purple Palette',
                                        type: 'sequential',
                                        category: 'Custom',
                                        colors: ["#f3e8ff", "#d8b4fe", "#c084fc", "#9333ea", "#6b21a8", "#4c1d95"]
                                    },
                                    filled: true,
                                    stroked: true
                                }
                            }
                        }
                    ]
                }
            }
        };

        // Register the Mapbox Access Token directly inside Kepler's Redux state style reducer
        const activeMapboxToken = (window.urbanHeatApplicationConfig && window.urbanHeatApplicationConfig.mapboxPublicAccessToken) ?
            window.urbanHeatApplicationConfig.mapboxPublicAccessToken :
            'pk.placeholder';
        dispatch(KeplerGl.wrapTo('map', KeplerGl.inputMapStyle({ mapboxApiAccessToken: activeMapboxToken })));

        // Phase 1: Ingest dataset with full keplerConfigStructure + autoCreateLayers fallback
        dispatch(KeplerGl.wrapTo('map', KeplerGl.addDataToMap({
            datasets: [keplerDatasetStructure],
            options: {
                keepExistingConfig: false,
                autoCreateLayers: true
            },
            config: keplerConfigStructure
        })));

        // Phase 2 (150ms delay): Configure the auto-created layer's label, palette, and colorField
        setTimeout(() => {
            const getLatestLayer = () => storeInstance.getState().keplerGl.map.visState.layers[0];
            const datasets = storeInstance.getState().keplerGl.map.visState.datasets;
            const targetLayer = getLatestLayer();

            if (targetLayer && datasets[uniqueDatasetId]) {
                const targetField = datasets[uniqueDatasetId].fields.find(
                    f => f.name === 'final_mitigation_priority_score'
                );

                if (KeplerGl.layerVisConfigChange) {
                    dispatch(KeplerGl.wrapTo('map', KeplerGl.layerVisConfigChange(
                        getLatestLayer(),
                        {
                            opacity: 0.8,
                            strokeColor: [255, 255, 255],
                            colorRange: {
                                name: 'Colorblind-Safe Purple Palette',
                                type: 'sequential',
                                category: 'Custom',
                                colors: ["#f3e8ff", "#d8b4fe", "#c084fc", "#9333ea", "#6b21a8", "#4c1d95"]
                            }
                        }
                    )));
                }

                if (targetField && KeplerGl.layerVisualChannelConfigChange) {
                    dispatch(KeplerGl.wrapTo('map', KeplerGl.layerVisualChannelConfigChange(
                        getLatestLayer(),
                        { colorField: targetField, colorScale: 'quantile' },
                        'color'
                    )));
                }
            }
            setIsWorkflowProcessing(false);
        }, 150);
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
                    React.createElement('span', { className: 'connection-mode-banner connection-mode-offline' }, 'Offline Mockup Mode'),

                React.createElement('br'),

                // Trigger button for the About Modal dialog
                React.createElement('button', {
                    className: 'about-toolkit-trigger-button',
                    onClick: () => setIsAboutModalOpen(true)
                }, 'About Toolkit')
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
                id: 'map',
                width: window.innerWidth - 420,
                height: window.innerHeight,
                getState: state => state.keplerGl,
                mapboxApiAccessToken: (window.urbanHeatApplicationConfig && window.urbanHeatApplicationConfig.mapboxPublicAccessToken && window.urbanHeatApplicationConfig.mapboxPublicAccessToken.startsWith('pk.')) ?
                    window.urbanHeatApplicationConfig.mapboxPublicAccessToken :
                    (localStorage.getItem('mapbox_token') || 'pk.placeholder')
            }),

            // Loading screen overlay during MCDA processing runs
            isWorkflowProcessing ? React.createElement(
                'div',
                { className: 'global-loading-screen-overlay' },
                React.createElement('div', { className: 'loading-spinner-element' }),
                React.createElement('p', { className: 'loading-status-text' }, 'Recalculating spatial planning indicators...')
            ) : null
        ),

        // About Toolkit Modal Backdrop Overlay (renders only when active)
        isAboutModalOpen ? React.createElement(
            'div',
            { className: 'about-modal-overlay-backdrop', onClick: () => setIsAboutModalOpen(false) },

            // Modal Card Container
            React.createElement(
                'div',
                { className: 'about-modal-card-box', onClick: (evt) => evt.stopPropagation() },

                // Modal Header block
                React.createElement(
                    'div',
                    { className: 'about-modal-header' },
                    React.createElement('h2', { className: 'about-modal-header-title' }, 'About the Toolkit'),
                    React.createElement('button', {
                        className: 'about-modal-close-icon-button',
                        onClick: () => setIsAboutModalOpen(false)
                    }, '✕')
                ),

                // Modal Body Scrollable area
                React.createElement(
                    'div',
                    { className: 'about-modal-body-scrollable' },

                    React.createElement('h3', null, 'Overview & Purpose'),
                    React.createElement('p', null, 'This decision-support toolkit integrates physical environmental metrics, land cover databases, and demographic census data into a Multi-Criteria Decision Analysis (MCDA) framework. It is designed to identify priority areas and target interventions (urban forestry, cool pavements, shade structures) to mitigate urban heat stress across Omaha, Nebraska.'),

                    React.createElement('h3', null, 'User Guide: How to Interact with the Map'),
                    React.createElement('p', null, '1. Map Navigation: Left-click and drag to pan across Omaha. Scroll your mouse wheel up/down to zoom in or out. Right-click and drag up/down to tilt the map into a 3D viewpoint.'),
                    React.createElement('p', null, '2. Hover to Quick Inspect: Move your cursor over any neighborhood polygon. A floating tooltip will instantly display its FIPS code, average summer temperature, tree canopy, and custom strategy.'),
                    React.createElement('p', null, '3. Click to Lock & Inspect: Left-click on any neighborhood polygon. This "locks" that specific neighborhood into the right-hand panel (Section 3: Focus Area Inspection) in the sidebar, displaying its detailed census and environmental metrics.'),
                    React.createElement('p', null, '4. Custom Physical Recommendations: At the very bottom of Section 3, a highlighted callout box displays a specific physical cooling intervention (such as Forestry Expansion, Cool Roofs, or Rain Gardens) customized precisely matching that neighborhood\'s local data.'),

                    React.createElement('h3', null, 'Understanding the Weight Sliders'),
                    React.createElement('p', null, 'Adjusting the weights (Section 1) simulates different planning priorities. Dragging a slider high forces the system to emphasize that specific criteria (e.g. prioritizing tree deficits or vulnerable age groups). Clicking "Apply weights & Recalculate" automatically computes the live priorities and updates the map\'s heatmap dynamically!'),

                    React.createElement('h3', null, 'Primary Spatial Data Sources'),
                    React.createElement(
                        'ul',
                        { className: 'about-modal-list-item-grid' },
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'USGS Landsat Land Surface Temperature'),
                            React.createElement('a', { className: 'about-modal-item-link-anchor', href: 'https://www.usgs.gov/landsat-missions/landsat-surface-temperature', target: '_blank' }, 'Visit Website')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'USDA Forest Service Tree Canopy Cover'),
                            React.createElement('a', { className: 'about-modal-item-link-anchor', href: 'https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/', target: '_blank' }, 'Visit Website')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'NLCD developed imperviousness'),
                            React.createElement('a', { className: 'about-modal-item-link-anchor', href: 'https://www.mrlc.gov/data', target: '_blank' }, 'Visit Website')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'U.S. Census Bureau ACS demographics'),
                            React.createElement('a', { className: 'about-modal-item-link-anchor', href: 'https://www.census.gov/programs-surveys/acs/about.html', target: '_blank' }, 'Visit Website')
                        )
                    ),

                    React.createElement('h3', null, 'Core System Libraries'),
                    React.createElement(
                        'ul',
                        { className: 'about-modal-list-item-grid' },
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'Geospatial mapping engine'),
                            React.createElement('span', null, 'Kepler.gl & Mapbox GL')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'State architecture management'),
                            React.createElement('span', null, 'React & Redux')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'Backend REST web service'),
                            React.createElement('span', null, 'FastAPI (Python)')
                        ),
                        React.createElement('li', null,
                            React.createElement('span', { className: 'about-modal-item-label' }, 'Database relational storage'),
                            React.createElement('span', null, 'PostgreSQL & PostGIS')
                        )
                    ),

                    React.createElement('h3', null, 'Project Information & Co-Authors'),
                    React.createElement('p', null, 'Created as an academic spatial analytics product under GEOG 778, Fall 2026, by David Vanosdall.'),
                    React.createElement('p', null, 'Scripting, code formatting, and spatial database configuration assisted by GitHub Copilot and conversational AI developer agents.')
                ),

                // Modal Footer
                React.createElement(
                    'div',
                    { className: 'about-modal-footer' },
                    React.createElement('button', {
                        className: 'action-button-element',
                        style: { width: 'auto', padding: '8px 24px' },
                        onClick: () => setIsAboutModalOpen(false)
                    }, 'Close')
                )
            )
        ) : null
    );
};

// Render layout mounted into Redux Provider tags
ReactDOM.render(
    React.createElement(
        ReactRedux.Provider,
        { store: storeInstance },
        React.createElement(DecisionSupportDashboardApplication)
    ),
    document.getElementById('root')
);
