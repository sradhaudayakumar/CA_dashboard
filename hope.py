import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import io
from plotly.io import to_image
import base64

# --- Setup
st.set_page_config(page_title="California Wildfires Dashboard", layout="wide", page_icon="🔥")
st.title("🔥 California Wildfires Dashboard")

# --- Upload or Select Dataset
st.sidebar.header("📁 Upload or Select Dataset")
uploaded_file = st.sidebar.file_uploader("Upload your GeoJSON file", type=["geojson"], key="uploader_main")
year_option = st.sidebar.radio("Select Dataset Year", ["2016", "2017", "2018", "2019", "2020", "Cumulative"])

# --- Load & Prepare Data
def load_and_prepare(path, year):
    try:
        gdf = gpd.read_file(path)
        gdf = gdf.to_crs(epsg=3310)
        gdf["area_ha"] = gdf.geometry.area / 10000
        gdf = gdf.to_crs(epsg=4326)
        if "year" not in gdf.columns and year != "Cumulative":
            gdf["year"] = year
        if "year" in gdf.columns:
            gdf["year"] = pd.to_numeric(gdf["year"], errors="coerce").astype("Int64")
        gdf = gdf[gdf.geometry.is_valid]
        return gdf
    except Exception as e:
        st.error(f"❌ Error loading {year} data: {e}")
        return gpd.GeoDataFrame()

# --- Load Data Based on Input
if uploaded_file:
    try:
        gdf = gpd.read_file(uploaded_file)
        gdf = gdf.to_crs(epsg=3310)
        gdf["area_ha"] = gdf.geometry.area / 10000
        gdf = gdf.to_crs(epsg=4326)
        gdf["year"] = "Uploaded"
        gdf = gdf[gdf.geometry.is_valid]
        st.success("✅ Uploaded file loaded successfully.")
    except Exception as e:
        st.error(f"❌ Failed to load uploaded file: {e}")
        gdf = gpd.GeoDataFrame()
else:
    path = f"C:/Users/udaya/OneDrive/Documents/burned_{year_option.lower()}_vector.geojson" if year_option != "Cumulative" else "C:/Users/udaya/OneDrive/Documents/burned_cumulative_vector.geojson"
    gdf = load_and_prepare(path, year_option)

if gdf.empty:
    st.warning("⚠️ No wildfire data loaded.")
    st.stop()

# --- Wildfire and SDG Intro Text
st.markdown("""
<div style='font-size: 18px; line-height: 1.6;'>
<h3>📍 Why California?</h3>
For this project, we selected California due to its geographical location, high wildfire incidence, and climate vulnerability. The state consistently experiences some of the most frequent and intense wildfires in the United States. To support this investigation, we compared the frequency of wildfire outbreaks over a span of four years. Using MODIS satellite data accessed through Google Earth Engine, we compiled near real-time burned area data for the years 2016 to 2020. This dataset was then overlaid in QGIS, contextualized against population distribution and spatial patterns across the broader United States.
<br><br>
<h3>🔥 Understanding California Wildfires (2016–2020)</h3>
The major causes of wildfires for the period 2016–2020 include negligent human activity (poor campfire management, debris burning, inadequate use of power tools), vegetation stress from droughts, climate-induced high winds, lightning storms, and inadequate forest management.

These factors can be summarized as:
<ul>
<li>🔥 Hotter and drier summers increasing the amount of burnable fuel</li>
<li>⚡ Encroaching electricity infrastructure faults</li>
<li>🌆 Increased urbanization into previously forested areas</li>
<li>🚒 A legacy of inadequate fire suppression activities</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='font-size: 18px; line-height: 1.6;'>
<h3>🌍 Wildfire Monitoring and the Sustainable Development Goals (SDGs)</h3>
Wildfire monitoring impacts multiple Sustainable Development Goals (SDGs), particularly those related to the environment, climate, health, and livelihoods.<br><br>
<b>The key SDGs affected include:</b>
</div>
""", unsafe_allow_html=True)

sdg_boxes = [
    ("SDG 13: Climate Action 🌡️", 
     "Wildfires contribute significantly to greenhouse gas emissions. Monitoring wildfire activity helps mitigate climate change by enabling early response and the development of long-term fire management strategies.",
     "warning"),

    ("SDG 15: Life on Land 🐾🌳", 
     "Wildfires destroy forests, wildlife habitats, and biodiversity. Monitoring high-risk fire-prone areas supports conservation efforts and helps restore ecosystems.",
     "success"),

    ("SDG 3: Good Health and Well-being 🏥😷", 
     "Smoke and air pollution from wildfires cause respiratory illnesses and other health problems. Early detection and resolution action helps minimise human exposure and health risks.",
     "info"),

    ("SDG 11: Sustainable Cities and Communities 🏟️🔥", 
     "Wildfires threaten urban–rural interfaces and infrastructure. Monitoring enhances disaster preparedness and resilient city planning.",
     "danger"),

    ("SDG 12: Responsible Consumption and Production ♻️👨‍💼", 
     "Monitoring can inform sustainable land and resource management, helping to prevent human-induced fires due to land clearing or industrial activities.",
     "secondary")
]

for title, desc, box_type in sdg_boxes:
    color_map = {
        "info": "rgba(23, 162, 184, 0.2)",
        "success": "rgba(40, 167, 69, 0.2)",
        "warning": "rgba(255, 193, 7, 0.2)",
        "danger": "rgba(220, 53, 69, 0.2)",
        "secondary": "rgba(108, 117, 125, 0.2)"
    }
    box_color = color_map.get(box_type, "rgba(108, 117, 125, 0.2)")

    st.markdown(f"""
    <div style="border-left: 6px solid {box_color}; background-color: {box_color}; padding: 1rem; margin-bottom: 1rem; border-radius: 10px; font-size: 16px;">
    <strong>{title}</strong><br>{desc}
    </div>
    """, unsafe_allow_html=True)

# --- Filters
st.write("✅ Data loaded successfully.")
st.sidebar.header("🔧 Filters")

if year_option != "Cumulative" and "year" in gdf.columns:
    gdf["year"] = pd.to_numeric(gdf["year"], errors="coerce").astype("Int64")
    gdf_filtered_year = gdf[gdf["year"] == int(year_option)].copy()
else:
    gdf_filtered_year = gdf.copy()

area_bins = {
    "All": (0, float("inf")),
    "< 100 ha": (0, 100),
    "100 - 500 ha": (100, 500),
    "500 - 1000 ha": (500, 1000),
    "1000 - 5000 ha": (1000, 5000),
    "5000 - 10000 ha": (5000, 10000),
    "> 10000 ha": (10000, float("inf"))
}
area_category = st.sidebar.selectbox("Burned Area Category", list(area_bins.keys()))
area_range = area_bins[area_category]

name_filter = st.sidebar.text_input("Search Fire Name")
cause_column = next((col for col in gdf.columns if "cause" in col.lower()), None)
selected_causes = st.sidebar.multiselect("Filter by Cause", gdf_filtered_year[cause_column].dropna().unique()) if cause_column else []

filtered = gdf_filtered_year.copy()
if "area_ha" in filtered.columns:
    filtered = filtered[(filtered["area_ha"] >= area_range[0]) & (filtered["area_ha"] <= area_range[1])]
if name_filter and "fire_name" in filtered.columns:
    filtered = filtered[filtered["fire_name"].str.contains(name_filter, case=False, na=False)]
if selected_causes and cause_column:
    filtered = filtered[filtered[cause_column].isin(selected_causes)]

# --- Summary Stats
st.subheader("📊 Summary Statistics")
if "year" in gdf.columns:
    summary = gdf.groupby("year")["area_ha"].agg(["count", "mean", "max"]).rename(columns={"count": "Total Fires", "mean": "Avg Area (ha)", "max": "Max Area (ha)"})
    st.write("**Full Dataset Summary by Year:**")
    st.dataframe(summary)

col1, col2, col3 = st.columns(3)
col1.metric("🧯 Total Fires (Filtered)", len(filtered))
col2.metric("📏 Avg Area (ha)", round(filtered["area_ha"].mean(), 2) if not filtered.empty else 0)
col3.metric("🚨 Max Area (ha)", round(filtered["area_ha"].max(), 2) if not filtered.empty else 0)

# --- Insert Graph Image (After Summary Stats)
st.subheader("📸 Wildfire Trend Overview")
st.image("C:/Users/udaya/OneDrive/Documents/graph.jpg", caption="Trend of Wildfires Over the Years", use_container_width=False, width=2000)


# --- Map
st.subheader("🗺️ Wildfire Map")
if not filtered.empty and "geometry" in filtered.columns:
    map_style = st.sidebar.selectbox("Map Style", ["carto-positron", "open-street-map", "stamen-terrain"])
    color_col = "year" if year_option == "Cumulative" and "year" in filtered.columns else "area_ha"
    fig_map = px.choropleth_mapbox(
        filtered,
        geojson=filtered.__geo_interface__,
        locations=filtered.index,
        color=color_col,
        color_continuous_scale="YlOrRd",
        mapbox_style=map_style,
        zoom=5,
        center={"lat": 37.5, "lon": -119},
        opacity=0.6
    )
    fig_map.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, template="plotly_dark")
    st.plotly_chart(fig_map, use_container_width=True, key="main_map")

# --- Map Comparison
st.subheader("🧭 Wildfire Map Comparison")

col1, col2 = st.columns(2)
with col1:
    comp_year_1 = st.selectbox("Left Map: Select Year", ["2016", "2017", "2018", "2019", "2020", "Cumulative"], key="comp1")
with col2:
    comp_year_2 = st.selectbox("Right Map: Select Year", ["2016", "2017", "2018", "2019", "2020", "Cumulative"], key="comp2")

def get_filtered_gdf(year_label):
    if uploaded_file and year_label == "Uploaded":
        return gdf.copy()
    file_path = f"C:/Users/udaya/OneDrive/Documents/burned_{year_label.lower()}_vector.geojson" if year_label != "Cumulative" else "C:/Users/udaya/OneDrive/Documents/burned_cumulative_vector.geojson"
    return load_and_prepare(file_path, year_label)

gdf_left = get_filtered_gdf(comp_year_1)
gdf_right = get_filtered_gdf(comp_year_2)

map_style = st.sidebar.selectbox("Comparison Map Style", ["carto-positron", "open-street-map", "stamen-terrain"], key="comp_style")

if not gdf_left.empty and not gdf_right.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🗺️ {comp_year_1} Wildfires")
        fig_left = px.choropleth_mapbox(
            gdf_left,
            geojson=gdf_left.__geo_interface__,
            locations=gdf_left.index,
            color="area_ha",
            color_continuous_scale="YlOrRd",
            mapbox_style=map_style,
            zoom=5,
            center={"lat": 37.5, "lon": -119},
            opacity=0.6,
            template="plotly_dark"
        )
        fig_left.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig_left, use_container_width=True, key=f"map_left_{comp_year_1}")

    with col2:
        st.markdown(f"### 🗺️ {comp_year_2} Wildfires")
        fig_right = px.choropleth_mapbox(
            gdf_right,
            geojson=gdf_right.__geo_interface__,
            locations=gdf_right.index,
            color="area_ha",
            color_continuous_scale="YlOrRd",
            mapbox_style=map_style,
            zoom=5,
            center={"lat": 37.5, "lon": -119},
            opacity=0.6,
            template="plotly_dark"
        )
        fig_right.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig_right, use_container_width=True, key=f"map_right_{comp_year_2}")
else:
    st.warning("One or both datasets could not be loaded for comparison.")
# --- Related SDG Resources
st.sidebar.markdown("### 🌍 Related SDG Resources")
st.sidebar.markdown("""
- [UN SDG Tracker](https://sdgs.un.org/goals)
- [California Climate Dashboard](https://cal-adapt.org/)
- [NASA EarthData Fire and Climate](https://earthdata.nasa.gov/learn/toolkits/wildfires)
- [OECD SDG Indicators](https://www.oecd.org/sdgs/)
- [Global Forest Watch Fires](https://fires.globalforestwatch.org/)
""")