import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

# --- Layout ---
st.set_page_config(layout="wide", page_title="Climate-Tech Centrality Explorer")
st.title("🌎 U.S. County Climate-Tech Dashboard")

# --- View mode ---
view_mode = st.sidebar.radio("Choose View:", ["📈 Scatterplot", "🗺️ Choropleth Map"])

@st.cache_data
def load_data():
    df = pd.read_csv("county_climate_summary.csv")
    gdf = gpd.read_file("cb_2022_us_county_5m.shp")
    gdf["GEOID"] = gdf["STATEFP"] + gdf["COUNTYFP"]
    df["GEOID"] = df["GEOID"].astype(str).str.zfill(5)

    # Convert FIPS to state names
    state_fips_to_name = {
        "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas", "06": "California",
        "08": "Colorado", "09": "Connecticut", "10": "Delaware", "11": "District of Columbia",
        "12": "Florida", "13": "Georgia", "15": "Hawaii", "16": "Idaho", "17": "Illinois",
        "18": "Indiana", "19": "Iowa", "20": "Kansas", "21": "Kentucky", "22": "Louisiana",
        "23": "Maine", "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
        "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
        "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
        "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
        "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina",
        "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah", "50": "Vermont",
        "51": "Virginia", "53": "Washington", "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming"
    }
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    df["state_name"] = df["state_fips"].map(state_fips_to_name)
    df["county_state"] = df["county_name"] + ", " + df["state_name"]

    return df, gdf

df, gdf = load_data()

# --- Metric selection ---
numeric_cols = [col for col in df.columns if col.endswith("_degree_centrality")] + ["gdp_2023"]
selected_col = st.sidebar.selectbox("Select metric to visualize:", numeric_cols)

# --- Scatterplot View ---
if view_mode == "📈 Scatterplot":
    log_x = st.sidebar.checkbox("Log scale for X-axis")
    log_y = st.sidebar.checkbox("Log scale for Y-axis")
    plot_df = df[[selected_col, "gdp_2023", "county_state"]].dropna()

    fig = px.scatter(
        plot_df,
        x=selected_col,
        y="gdp_2023",
        hover_name="county_state",
        trendline="ols",
        labels={
            selected_col: selected_col.replace("_degree_centrality", "") + " Centrality",
            "gdp_2023": "GDP (USD)"
        },
        title=f"{selected_col.replace('_degree_centrality', '')} Centrality vs. GDP"
    )

    fig.update_traces(marker=dict(size=7, opacity=0.7, color="teal"))
    fig.update_xaxes(type="log" if log_x else "linear")
    fig.update_yaxes(type="log" if log_y else "linear")

    for trace in fig.data:
        if trace.mode == "lines":
            trace.line.color = "gray"
            trace.line.dash = "dash"
            trace.name = "OLS Trendline"

    st.plotly_chart(fig, use_container_width=True)

# --- Choropleth View ---
else:
    log_color = st.sidebar.checkbox("Log scale for choropleth color")
    merged = gdf.merge(df[["GEOID", selected_col, "county_state"]], on="GEOID", how="left").dropna(subset=[selected_col])

    fig = px.choropleth_mapbox(
        merged,
        geojson=json.loads(merged.to_json()),
        locations=merged.index,
        color=selected_col,
        hover_name="county_state",
        hover_data={"GEOID": True, selected_col: True},
        mapbox_style="carto-positron",
        zoom=3,
        center={"lat": 37.8, "lon": -96},
        opacity=0.85,
        color_continuous_scale="Viridis",
        labels={selected_col: selected_col.replace("_degree_centrality", "")},
        height=700
    )

    if log_color:
        fig.update_coloraxes(colorbar_tickformat="~.2e", colorscale="Viridis")

    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        title=f"Choropleth Map: {selected_col.replace('_degree_centrality', '')}"
    )
    st.plotly_chart(fig, use_container_width=True)
