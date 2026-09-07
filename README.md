# GEOG_778

Repo for my GEOG_778 project

David Vanosdall / Fall 2026 / Geography 778

## Table of Contents

- [Urban Heat Mitigation Decision-Support Toolkit for Omaha](#urban-heat-mitigation-decision-support-toolkit-for-omaha)
  - [Project Overview](#project-overview)
  - [Decision-Support Approach](#decision-support-approach)
  - [Intended Users](#intended-users)
  - [Data Sources](#data-sources)
  - [System Architecture](#system-architecture)
  - [Technology Stack](#technology-stack)
  - [Planned Functionality](#planned-functionality)
  - [GIS&T Knowledge Areas](#gist-knowledge-areas)
  - [Project Goals](#project-goals)
  - [Project Status](#project-status)
  - [Future Development](#future-development)
  - [Disclaimer](#disclaimer)

## Urban Heat Mitigation Decision-Support Toolkit for Omaha

A configurable geospatial decision-support system for evaluating urban heat-mitigation opportunities in Omaha, Nebraska.

[Back to Table of Contents](#table-of-contents)

## Project Overview

Urban heat is an important place based problem in Omaha.  Factors associated with urban heat exposure, including land surface temperature, tree canopy, impervious surfaces, land cover, and population distribution, vary considerably across the city.

Omaha has also identified climate resilience, greenspace, and tree canopy as important areas for planning and investment.  However, translating these broad planning goals into geographically specific priorities requires integrating multiple types of spatial information.

This project will develop a **GIS based urban heat mitigation decision-support toolkit** that identifies areas of Omaha where different heat-mitigation strategies may provide the greatest potential benefit.

The project is intended to move beyond simply identifying where urban heat exists.  The system will help answer:

- **Why is an area a priority?**
- **What type of intervention may be appropriate?**
- **How do priorities change when different planning criteria are emphasized?**

[Back to Table of Contents](#table-of-contents)

## Decision-Support Approach

The system will combine multiple spatial criteria to evaluate potential heat-mitigation opportunities.

A conceptual scoring workflow is:

> **Heat intensity + canopy deficit + imperviousness + population exposure + site/intervention constraints → normalized criteria → configurable weighting → intervention priority**

For example:

- High surface temperature + low tree canopy + high population exposure + sufficient planting space → **tree-canopy priority**
- High surface temperature + high imperviousness + limited planting opportunities → **cool-surface priority**
- High heat exposure + sensitive population or facility + limited shade → **shade intervention priority**

The system will support configurable criteria and weighting so that different planning scenarios can be evaluated and compared.

[Back to Table of Contents](#table-of-contents)

## Intended Users

The primary intended users are:

- Municipal planners
- Urban forestry staff
- Sustainability and climate-resilience personnel
- Organizations involved in heat-mitigation planning and investment

The toolkit may also provide value to other GIS professionals or researchers interested in evaluating urban heat-mitigation strategies.

[Back to Table of Contents](#table-of-contents)

## Data Sources

The initial analysis will use established public geospatial datasets.

| Dataset | Purpose |
|---|---|
| **USGS Landsat-derived Land Surface Temperature** | Measure urban heat intensity |
| **USDA Forest Service Tree Canopy Cover** | Measure existing tree canopy and canopy deficits |
| **MRLC Annual NLCD** | Land cover and impervious-surface characteristics |
| **U.S. Census ACS** | Population and demographic exposure |
| **Omaha / Local GIS Data** | Roads, schools, parks, public facilities, and other local context |

A recent data year will be used for the primary analysis.  Historical datasets may be incorporated later as an optional capability for comparison or validation.

[Back to Table of Contents](#table-of-contents)

## System Architecture

The system is designed as a modular geospatial workflow:

[![Urban Heat Mitigation Toolkit Architecture](docs/architecture.png)](docs/architecture.png)

The architecture separates the analytical engine from the visualization layer.  This allows the analysis to be rerun with updated datasets or different criteria without requiring the visualization component to be rebuilt.

The detailed architecture diagram is maintained separately in the project documentation.

[Back to Table of Contents](#table-of-contents)

## Technology Stack

The technology stack is currently envisioned as:

### Data Processing & Analysis

- **Python**
- Raster and vector geospatial processing
- Spatial statistics and analysis
- Multi-criteria decision analysis
- Automated data processing

### Spatial Database

- **PostgreSQL**
- **PostGIS**

PostGIS will provide the spatial database environment for storing source data, derived analytical layers, criteria, and intervention-priority results.

### Visualization & Application

- **JavaScript**
- **HTML / CSS**
- **Kepler.gl or similar geospatial visualization library**
- Web-based interactive mapping
- API/application layer

The exact application framework will be determined during implementation.

### Development

- Git
- GitHub
- Visual Studio Code
- Python virtual environment / dependency management

[Back to Table of Contents](#table-of-contents)

## Planned Functionality

The completed toolkit is expected to support functionality such as:

- Interactive exploration of urban heat conditions
- Display of analytical criteria
- Spatial querying
- Inspection of contributing criteria
- Configurable criteria weights
- Multiple planning scenarios
- Comparison of scenario results
- Identification of potential intervention types
- Summary statistics and charts
- Export of analytical results for use in other GIS software

[Back to Table of Contents](#table-of-contents)

## GIS&T Knowledge Areas

The project applies concepts and technical skills from several areas of the GIS&T Body of Knowledge, including:

- Spatial analysis
- Raster analysis
- Geospatial data management
- Spatial databases
- Geovisualization
- Interactive mapping
- Geospatial application development
- Geographic information communication

The project combines these areas into a single reproducible geospatial workflow rather than applying a single GIS technique.

[Back to Table of Contents](#table-of-contents)

## Project Goals

The primary goal is to create a **reproducible and configurable geospatial decision-support system for evaluating urban heat-mitigation opportunities in Omaha**.

The system should allow users to move from:

> **"Where is urban heat a problem?"**

toward:

> **"Why is this area a priority?"**

> **"What type of intervention may be appropriate here?"**

> **"How do those priorities change when planning criteria change?"**

[Back to Table of Contents](#table-of-contents)

## Project Status

**Current phase:** Project planning and architecture

### Completed

- [x] Project concept established
- [x] Omaha identified as study area
- [x] Initial data-source investigation
- [x] Preliminary system architecture
- [x] Git repository established
- [x] Architecture diagram created

### In Progress

- [ ] Finalize data inventory
- [ ] Establish project data schema
- [ ] Design PostgreSQL/PostGIS database
- [ ] Develop Python ETL workflow
- [ ] Develop analytical criteria
- [ ] Implement multi-criteria scoring
- [ ] Develop interactive visualization
- [ ] Implement scenario comparison
- [ ] Test and validate results

[Back to Table of Contents](#table-of-contents)

## Future Development

Potential future capabilities include:

- Reproducible application installation and deployment
- Additional intervention types
- Additional local planning constraints
- Expanded scenario and sensitivity analysis

[Back to Table of Contents](#table-of-contents)

## Disclaimer

This project is an academic GIS development project.  Intervention priorities produced by the toolkit represent analytical results based on the selected datasets, criteria, and weighting assumptions.  They should be treated as decision-support information rather than definitive recommendations or engineering designs.

[Back to Table of Contents](#table-of-contents)