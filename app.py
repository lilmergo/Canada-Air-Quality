import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime
import numpy as np
import io
import os
import colorsys  # For HSL color manipulation

# Set page config to a slightly narrower custom width
st.set_page_config(layout="wide", page_title="Canada Air Quality Dashboard", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1100px;  /* Slightly narrower than default 'wide' */
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load the monthly aggregate data
df = pd.read_csv("air_quality_monthly_data.csv")

# Ensure 'Month Start (UTC)' is in datetime format and normalize to the first of the month
df['Month Start (UTC)'] = pd.to_datetime(df['Month Start (UTC)']).dt.normalize()

# Pre-generate maps for each season
@st.cache_data
def pregenerate_maps():
    unique_years = sorted(df['Month Start (UTC)'].dt.year.unique())
    wildfire_seasons = [f"{year} (May-Sep)" for year in unique_years if year >= 2018 and year <= 2024]  # Exclude 2025
    preloaded_maps = {}

    for season in wildfire_seasons:
        year = int(season.split(" ")[0])
        season_df = df[
            (df['Month Start (UTC)'].dt.year == year) &
            (df['Month Start (UTC)'].dt.month.isin([5, 6, 7, 8, 9]))
        ].copy()

        # Prepare data for the heatmap
        heatmap_data = season_df.groupby(['Latitude', 'Longitude', 'Sensor Parameter'])['Monthly Average'].mean().reset_index()

        # Create the map using matplotlib and cartopy
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        # Set the extent to focus on Canada (zoomed in)
        ax.set_extent([-165, -52, 40, 83], crs=ccrs.PlateCarree())  # Adjusted for zoom

        # Add geographic features
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.LAKES, facecolor='lightblue', edgecolor='black')
        ax.add_feature(cfeature.STATES, linestyle='--')

        # Define colors and markers for each pollutant
        pollutant_styles = {
            "pm2.5": {"color": "red", "marker": "o", "label": "PM2.5"},
            "o₃": {"color": "purple", "marker": "o", "label": "O₃"}
        }

        # Plot each pollutant's data
        handles = []
        labels = []
        for pollutant in target_pollutants:
            pollutant_data = heatmap_data[heatmap_data['Sensor Parameter'] == pollutant]
            if not pollutant_data.empty:
                # Normalize Monthly Average for sizing
                sizes = pollutant_data['Monthly Average'] / pollutant_data['Monthly Average'].max() * 500
                scatter = ax.scatter(
                    pollutant_data['Longitude'], pollutant_data['Latitude'],
                    s=sizes,
                    c=pollutant_styles[pollutant]["color"],
                    marker=pollutant_styles[pollutant]["marker"],
                    alpha=0.6,
                    transform=ccrs.PlateCarree()
                )
                # Create a handle with a fixed size for the legend
                handle = plt.scatter([], [], s=100, c=pollutant_styles[pollutant]["color"],
                                     marker=pollutant_styles[pollutant]["marker"],
                                     label=pollutant_styles[pollutant]["label"])
                handles.append(handle)
                labels.append(pollutant_styles[pollutant]["label"])

        # Add custom legend with fixed-size markers
        ax.legend(handles=handles, labels=labels, title="Pollutants")
        ax.set_title(f"Air Quality in Canada - {season}", pad=20)
        plt.tight_layout()

        # Save the figure to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        preloaded_maps[season] = buf

        # Close the figure to free memory
        plt.close(fig)

    return preloaded_maps

# Pre-generate maps at startup
target_pollutants = ["pm2.5", "o₃"]
preloaded_maps = pregenerate_maps()

# Streamlit UI
st.title("Canada Air Quality Dashboard - Monthly Aggregates (Wildfire Focus)")

# Trend Graph Section
st.header("Monthly Trend Analysis")

# Row 1: Two columns for filters
col1, col2 = st.columns(2)
with col1:
    # Pollutant filter
    display_pollutants = {"pm2.5": "PM2.5", "o₃": "O₃"}
    selected_pollutants_api = st.multiselect("Select Pollutants", target_pollutants, default=["pm2.5", "o₃"])
    selected_pollutants_display = [display_pollutants[p] for p in selected_pollutants_api]

with col2:
    # Define correlation-based location groups with insights and correlations
    location_groups = {
        "Pollutant Synergy Zones": {
            "cities": ["Buffalo Narrows", "Winnipeg_Ellens"],
            "insight": (
                "Pollutant Synergy Zones: Inland areas where wildfires or urban emissions boost both pollutants. "
                "During wildfire seasons (May-Sep, yellow boxes), Buffalo Narrows shows sharp PM2.5 spikes, peaking at ~120 µg/m³ in July 2017, "
                "while O₃ also rises, reaching ~0.035 ppm, reflecting synergy from photochemical reactions with wildfire VOCs. "
                "Winnipeg_Ellens exhibits smaller PM2.5 peaks (~20 µg/m³ in July 2021) but steady O₃ increases (up to 0.03 ppm), likely due to urban emissions enhancing O₃ formation."
            ),
            "correlations": {"Buffalo Narrows": 0.393, "Winnipeg_Ellens": 0.457},
            "characteristics": {"Buffalo Narrows": "Wildfire-prone, inland", "Winnipeg_Ellens": "Urban, inland"}
        },
        "Moderate Alignment Areas": {
            "cities": [
                "Beaverlodge", "Brandon", "CHARLOTTETOWN", "Calgary Central2", "Edmonton Central Eas",
                "FORT ST JOHN LEARNIN", "Fort Chipewyan", "Kingston", "Mont-Saint-Michel", "PRINCE ALBERT",
                "Radisson", "Regina", "Rouyn-Noranda - Parc", "Saskatoon", "Sudbury", "Toronto Downtown"
            ],
            "insight": (
                "Moderate Alignment Areas: Mix of urban and wildfire-prone inland areas with a mild positive link. "
                "In wildfire seasons (yellow boxes), Beaverlodge and Fort Chipewyan show PM2.5 peaks (~50 µg/m³ in July 2021), with O₃ slightly rising (up to 0.03 ppm), "
                "indicating some synergy from wildfire smoke. Urban areas like Toronto Downtown maintain steady O₃ (~0.02 ppm) but see smaller PM2.5 increases (~20 µg/m³ in June 2023), "
                "suggesting traffic emissions contribute to both pollutants but with less wildfire impact."
            ),
            "correlations": {
                "Beaverlodge": 0.166, "Brandon": 0.263, "CHARLOTTETOWN": 0.026, "Calgary Central2": 0.202,
                "Edmonton Central Eas": 0.226, "FORT ST JOHN LEARNIN": 0.183, "Fort Chipewyan": 0.060,
                "Kingston": 0.101, "Mont-Saint-Michel": 0.073, "PRINCE ALBERT": 0.195, "Radisson": 0.258,
                "Regina": 0.169, "Rouyn-Noranda - Parc": 0.161, "Saskatoon": 0.105, "Sudbury": 0.158,
                "Toronto Downtown": 0.191
            },
            "characteristics": {
                "Beaverlodge": "Wildfire-prone, inland", "Brandon": "Urban, inland", "CHARLOTTETOWN": "Coastal, urban",
                "Calgary Central2": "Urban, inland", "Edmonton Central Eas": "Urban, inland", "FORT ST JOHN LEARNIN": "Wildfire-prone, inland",
                "Fort Chipewyan": "Wildfire-prone, inland", "Kingston": "Urban, inland", "Mont-Saint-Michel": "Rural, inland",
                "PRINCE ALBERT": "Urban, inland", "Radisson": "Wildfire-prone, inland", "Regina": "Urban, inland",
                "Rouyn-Noranda - Parc": "Urban, inland", "Saskatoon": "Urban, inland", "Sudbury": "Urban, inland",
                "Toronto Downtown": "Major urban, inland"
            }
        },
        "Mild Divergence Zones": {
            "cities": [
                "Auclair", "Courtenay Elementary", "FIREHALL-LABRADORCIT", "Notre-Dame-du-Rosair",
                "PRG Plaza 400", "Smithers Muheim Memo", "Whitehorse NAPS"
            ],
            "insight": (
                "Mild Divergence Zones: Coastal and northern areas with slight pollutant divergence. "
                "During wildfire seasons (yellow boxes), Courtenay Elementary sees PM2.5 spikes (~60 µg/m³ in July 2021), but O₃ drops to ~0.02 ppm, "
                "likely due to coastal humidity reducing photochemical O₃ formation. Smithers Muheim Memo shows similar trends, with PM2.5 peaking at ~50 µg/m³ in August 2018, "
                "while O₃ remains low (~0.015 ppm), possibly from temperature inversions."
            ),
            "correlations": {
                "Auclair": -0.269, "Courtenay Elementary": -0.275, "FIREHALL-LABRADORCIT": -0.114,
                "Notre-Dame-du-Rosair": -0.282, "PRG Plaza 400": -0.159, "Smithers Muheim Memo": -0.150,
                "Whitehorse NAPS": -0.136
            },
            "characteristics": {
                "Auclair": "Rural, inland", "Courtenay Elementary": "Coastal, urban", "FIREHALL-LABRADORCIT": "Coastal, urban",
                "Notre-Dame-du-Rosair": "Coastal, rural", "PRG Plaza 400": "Urban, inland", "Smithers Muheim Memo": "Rural, inland",
                "Whitehorse NAPS": "Urban, inland"
            }
        },
        "Pollutant Opposition Zones": {
            "cities": [
                "BATHURST", "Bonner Lake", "Dorset", "Flin Flon", "North Bay", "Ottawa Downtown",
                "Parry Sound", "Quesnel Johnston Ave", "SYDNEY", "Sault Ste Marie", "Thunder Bay"
            ],
            "insight": (
                "Pollutant Opposition Zones: Northern and urban areas with strong negative correlation. "
                "In wildfire seasons (yellow boxes), Bonner Lake and Sault Ste Marie exhibit massive PM2.5 spikes (up to 40 µg/m³ in July 2021), "
                "while O₃ plummets to ~0.005 ppm, likely due to NOₓ titration from wildfire smoke. Ottawa Downtown shows smaller PM2.5 peaks (~20 µg/m³ in June 2023) "
                "but a sharp O₃ drop to ~0.01 ppm, reflecting urban NOₓ emissions further suppressing O₃."
            ),
            "correlations": {
                "BATHURST": -0.420, "Bonner Lake": -1.0, "Dorset": -0.362, "Flin Flon": -0.375,
                "North Bay": -0.482, "Ottawa Downtown": -0.448, "Parry Sound": -0.352,
                "Quesnel Johnston Ave": -0.436, "SYDNEY": -0.540, "Sault Ste Marie": -0.849,
                "Thunder Bay": -0.598
            },
            "characteristics": {
                "BATHURST": "Coastal, urban", "Bonner Lake": "Wildfire-prone, inland", "Dorset": "Rural, inland",
                "Flin Flon": "Urban, inland", "North Bay": "Urban, inland", "Ottawa Downtown": "Major urban, inland",
                "Parry Sound": "Rural, inland", "Quesnel Johnston Ave": "Rural, inland", "SYDNEY": "Coastal, urban",
                "Sault Ste Marie": "Urban, inland", "Thunder Bay": "Urban, inland"
            }
        }
    }

    # Group filter (single selection)
    all_groups = list(location_groups.keys())
    selected_group = st.selectbox("Select a Location Group", all_groups, index=all_groups.index("Pollutant Opposition Zones"))

# Flatten selected group into a list of cities and validate sample size
selected_cities = []
excluded_cities = []
for city in location_groups[selected_group]["cities"]:
    city_data = df[df['City'] == city]
    if len(city_data['Month Start (UTC)'].unique()) >= 10:  # Minimum 10 months
        selected_cities.append(city)
    else:
        excluded_cities.append(city)
selected_cities = sorted(list(set(selected_cities)))  # Remove duplicates and sort

# Row 2: Plot and Insights side-by-side
col_plot, col_insight = st.columns([4, 1])
with col_plot:
    if selected_cities:
        trend_data = df[df['Sensor Parameter'].isin(selected_pollutants_api) & df['City'].isin(selected_cities)].copy()
    else:
        trend_data = df[df['Sensor Parameter'].isin(selected_pollutants_api)].copy()

    if not trend_data.empty:
        wildfire_season_months = [5, 6, 7, 8, 9]
        trend_data['Is Wildfire Season'] = trend_data['Month Start (UTC)'].dt.month.isin(wildfire_season_months)

        # Create the figure with subplots based on the selected group
        if selected_group == "Pollutant Opposition Zones":
            # Single subplot for this group
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 6))
            ax2_twin = ax2.twinx()
            ax1 = None  # No upper subplot
        else:
            # Two subplots for broken axis
            fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={'height_ratios': [1, 4], 'hspace': 0.05})
            ax2_twin = ax2.twinx()

        # Group-based color shades with lightness variation
        group_color_shades = {
            "Pollutant Synergy Zones": {"pm2.5": "#FF4500", "o₃": "#8A2BE2"},
            "Moderate Alignment Areas": {"pm2.5": "#FF6347", "o₃": "#9932CC"},
            "Mild Divergence Zones": {"pm2.5": "#FA8072", "o₃": "#BA55D3"},
            "Pollutant Opposition Zones": {"pm2.5": "#F08080", "o₃": "#C71585"}
        }

        # Function to adjust lightness of a hex color
        def adjust_lightness(hex_color, factor):
            rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(*rgb)
            new_l = min(max(l * factor, 0.2), 0.9)  # Limit lightness between 0.2 and 0.9
            r, g, b = colorsys.hls_to_rgb(h, new_l, s)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        # Group data by pollutant and city for plotting
        grouped = trend_data.groupby(['Sensor Parameter', 'City'])

        # Plot individual location lines with adjusted transparency
        for idx, ((pollutant, city), group) in enumerate(grouped):
            city_group = selected_group
            base_color = group_color_shades.get(city_group, {"pm2.5": "red", "o₃": "purple"})[pollutant]
            lightness_factor = 0.8 + (idx % 5) * 0.1
            color = adjust_lightness(base_color, lightness_factor)

            if pollutant == "pm2.5":
                if selected_group != "Pollutant Opposition Zones":
                    # Plot on both subplots for PM2.5 (broken axis groups)
                    ax1.plot(group['Month Start (UTC)'], group['Monthly Average'], label=f"{city} (PM2.5)", color=color, alpha=0.3, linewidth=1.5)
                    ax2.plot(group['Month Start (UTC)'], group['Monthly Average'], label=f"{city} (PM2.5)", color=color, alpha=0.3, linewidth=1.5)
                else:
                    # Plot on single subplot for Pollutant Opposition Zones
                    ax2.plot(group['Month Start (UTC)'], group['Monthly Average'], label=f"{city} (PM2.5)", color=color, alpha=0.3, linewidth=1.5)
            else:
                # Plot O₃ only on the lower subplot's secondary y-axis
                ax2_twin.plot(group['Month Start (UTC)'], group['Monthly Average'], label=f"{city} (O₃)", color=color, alpha=0.3, linewidth=1.5)

        # Calculate and plot overall average lines with adjusted thickness
        for pollutant in selected_pollutants_api:
            pollutant_data = trend_data[trend_data['Sensor Parameter'] == pollutant]
            if not pollutant_data.empty:
                avg_data = pollutant_data.groupby('Month Start (UTC)')['Monthly Average'].mean().reset_index()
                if pollutant == "pm2.5":
                    if selected_group != "Pollutant Opposition Zones":
                        # Plot average on both subplots
                        ax1.plot(avg_data['Month Start (UTC)'], avg_data['Monthly Average'], label="Average PM2.5",
                                 color=group_color_shades[selected_group]["pm2.5"], alpha=1.0, linewidth=2)
                        ax2.plot(avg_data['Month Start (UTC)'], avg_data['Monthly Average'], label="Average PM2.5",
                                 color=group_color_shades[selected_group]["pm2.5"], alpha=1.0, linewidth=2)
                    else:
                        # Plot average on single subplot
                        ax2.plot(avg_data['Month Start (UTC)'], avg_data['Monthly Average'], label="Average PM2.5",
                                 color=group_color_shades[selected_group]["pm2.5"], alpha=1.0, linewidth=2)
                else:
                    # Plot O₃ average on the lower subplot's secondary y-axis
                    ax2_twin.plot(avg_data['Month Start (UTC)'], avg_data['Monthly Average'], label="Average O₃",
                                  color=group_color_shades[selected_group]["o₃"], alpha=1.0, linewidth=2)

        # Add wildfire season shading
        years = trend_data['Month Start (UTC)'].dt.year.unique()
        for year in years:
            if year != 2025:
                start_date = pd.Timestamp(year=year, month=5, day=1)
                end_date = pd.Timestamp(year=year, month=9, day=30)
                if selected_group != "Pollutant Opposition Zones":
                    ax1.axvspan(start_date, end_date, facecolor='orange', alpha=0.2)
                    ax2.axvspan(start_date, end_date, facecolor='orange', alpha=0.2)
                else:
                    ax2.axvspan(start_date, end_date, facecolor='orange', alpha=0.2)

        # Set y-axis limits based on the selected group
        if selected_group == "Pollutant Synergy Zones":
            ax1.set_ylim(10, 75)
            ax2.set_ylim(0, 10)
        elif selected_group == "Moderate Alignment Areas":
            ax1.set_ylim(10, 55)
            ax2.set_ylim(0, 10)
        elif selected_group == "Mild Divergence Zones":
            ax1.set_ylim(10, 50)
            ax2.set_ylim(0, 10)
        elif selected_group == "Pollutant Opposition Zones":
            ax2.set_ylim(0, 20)  # Single axis for this group

        # Configure broken axis for groups with two subplots
        if selected_group != "Pollutant Opposition Zones":
            # Hide the spines between the subplots to create the broken axis effect
            ax1.spines['bottom'].set_visible(False)
            ax2.spines['top'].set_visible(False)

            # Adjust ticks
            ax1.xaxis.tick_top()
            ax1.tick_params(labeltop=False)
            ax2.xaxis.tick_bottom()

            # Add diagonal lines to indicate the break
            d = 0.015  # Size of the diagonal lines
            kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
            ax1.plot((-d, +d), (-d, +d), **kwargs)  # Top-left diagonal
            ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # Top-right diagonal
            kwargs.update(transform=ax2.transAxes)
            ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # Bottom-left diagonal
            ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # Bottom-right diagonal

        # Set labels and titles
        if selected_group != "Pollutant Opposition Zones":
            ax1.set_ylabel("PM2.5 (µg/m³)")
            ax2.set_ylabel("PM2.5 (µg/m³)")
        else:
            ax2.set_ylabel("PM2.5 (µg/m³)")
        ax2_twin.set_ylabel("O₃ (ppm)")
        ax2.set_xlabel("Year")
        fig.suptitle(f"Monthly {', '.join(selected_pollutants_display)} Averages", fontsize=16)

        # Adjust x-axis ticks to show years
        years = trend_data['Month Start (UTC)'].dt.year.unique()
        ax2.set_xticks([pd.Timestamp(year=year, month=1, day=1) for year in years])
        ax2.set_xticklabels([str(year) for year in years])

        # Display the plot in Streamlit
        st.pyplot(fig)

with col_insight:
    st.subheader("Insights")
    st.write(f"**{selected_group}**: {location_groups[selected_group]['insight']}")

# Row 3: Insights table
st.subheader("Detailed Insights")
table_data = {
    "City": [city for city in location_groups[selected_group]["cities"] if city in selected_cities],
    "Correlation": [location_groups[selected_group]["correlations"][city] for city in location_groups[selected_group]["cities"] if city in selected_cities],
    "Characteristics": [location_groups[selected_group]["characteristics"][city] for city in location_groups[selected_group]["cities"] if city in selected_cities]
}
st.table(pd.DataFrame(table_data))

# Sample size validation note
if excluded_cities:
    st.warning(f"Excluded cities with <10 months of data: {', '.join(excluded_cities)}")
else:
    st.info("All selected cities have sufficient data (>=10 months).")

# Heatmap Section
st.header("Wildfire Season Heatmap (May-Sep)")

# Row 1: Filter and Map
col1, col2 = st.columns([1.5, 3.5])
with col1:
    st.subheader("Select Wildfire Season")
    unique_years = sorted(df['Month Start (UTC)'].dt.year.unique())
    wildfire_seasons = [f"{year} (May-Sep)" for year in unique_years if year >= 2018 and year <= 2024]
    selected_season = st.radio("Choose Season", wildfire_seasons, index=len(wildfire_seasons)-1)

with col2:
    if selected_season:
        st.subheader(f"Static Geographic Heatmap for PM2.5 and O₃ - {selected_season}")
        st.image(preloaded_maps[selected_season], use_container_width=True)

# Row 2: Aggregate Table
if selected_season:
    year = int(selected_season.split(" ")[0])
    season_df = df[
        (df['Month Start (UTC)'].dt.year == year) &
        (df['Month Start (UTC)'].dt.month.isin([5, 6, 7, 8, 9]))
    ].copy()
    st.subheader("Aggregated Air Quality Data for Selected Wildfire Season")
    agg_data = season_df.groupby(['City', 'Sensor Parameter', 'Unit'])[['Monthly Average']].mean().reset_index()
    agg_data['Season'] = selected_season
    st.write(agg_data[['City', 'Sensor Parameter', 'Unit', 'Monthly Average', 'Season']], use_container_width=True)