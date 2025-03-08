# Canada Air Quality Dashboard - PM2.5 and O3 Levels vs Wildfire Seasons

Welcome to the **Canada Air Quality Dashboard**, a data visualization project focused on analyzing monthly PM2.5 and O₃ levels across Canadian cities, with a particular emphasis on wildfire seasons (May–September). This dashboard provides insights into pollutant trends and correlations across locations of various geographic categories, helping users understand air quality dynamics in wildfire-prone and urban areas.
This is an ongoing project, more analysis and data collecting to come!

## Live Deployment
You can interact with the dashboard here:  
👉 [Canada PM2.5 & O₃ Levels Dashboard](https://canada-pm25-o3-levels-fire-season.streamlit.app/)

## Project Overview

This project aggregates air quality data from various Canadian cities, focusing on two key pollutants: PM2.5 (particulate matter) and O₃ (ozone). I explored the data through:
- **Trend Analysis**: Visualizing monthly averages of PM2.5 and O₃, highlighting wildfire season impacts.
- **Geographic Heatmaps**: Mapping pollutant levels across Canada during wildfire seasons (May–September) from 2018 to 2024.
- **Correlation Insights**: Grouping cities based on PM2.5 and O₃ correlations, revealing synergy, alignment, divergence, and opposition patterns.

### Key Features
- **Interactive Filters**: Select pollutants (PM2.5, O₃) and location groups to analyze trends.
- **Broken Axis Visualization**: For groups with extreme PM2.5 values, I implemented a broken axis (e.g., 0–10 µg/m³ and 10–75 µg/m³ for Pollutant Synergy Zones) to focus on typical values while still showing outliers.
- **Wildfire Season Shading**: Highlighted May–September periods to emphasize wildfire impacts.
- **Correlation-Based Grouping**: Cities are grouped into four categories based on PM2.5 and O₃ correlations:
  - **Pollutant Synergy Zones** (e.g., Buffalo Narrows): High correlation, with wildfire-driven PM2.5 spikes (up to 120 µg/m³) and O₃ increases.
  - **Moderate Alignment Areas** (e.g., Beaverlodge, Toronto Downtown): Mild positive correlation, with PM2.5 peaks around 50 µg/m³.
  - **Mild Divergence Zones** (e.g., Courtenay Elementary): Slight negative correlation, with PM2.5 spikes (up to 60 µg/m³) but O₃ decreases.
  - **Pollutant Opposition Zones** (e.g., Bonner Lake, Ottawa Downtown): Strong negative correlation, with PM2.5 peaks (up to 40 µg/m³) and O₃ drops due to NOₓ titration.
- **Static Heatmaps**: Pre-generated maps showing PM2.5 and O₃ levels across Canada for each wildfire season.


## Discoveries
- **Wildfire Impact**: Cities in wildfire-prone areas (e.g., Buffalo Narrows, Fort Chipewyan) show significant PM2.5 spikes during May–September, often exceeding 50 µg/m³, with varying O₃ responses based on local conditions.
- **Urban vs. Rural Dynamics**: Urban areas like Toronto Downtown exhibit smaller PM2.5 increases (~20 µg/m³) but steady O₃ levels, influenced by traffic emissions.
- **Pollutant Relationships**:
  - Opposition Zones show PM2.5 spikes paired with O₃ drops, likely due to NOₓ titration from wildfire smoke or urban emissions.
- **Geographic Patterns**: Heatmaps reveal higher PM2.5 concentrations in inland wildfire-prone regions, with coastal areas often showing lower O₃ levels due to humidity.
