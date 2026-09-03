import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Secure Path Resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ingestion.loader import AWSDataLoader
from src.ingestion.generator import generate_synthetic_aws_data
from src.fusion import FusionEngine
from src.explain import ExplanationGenerator

# Static File Constants
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "synthetic_aws_telemetry.csv")
REAL_CLEANED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "mpi_jena_cleaned.csv")
REAL_RAW_DATA_PATH = os.path.join(BASE_DIR, "max_planck_weather_ts.csv")

st.set_page_config(
    page_title="SkyGuard AI - Intelligent AWS Anomaly Detection",
    page_icon="🛰️",
    layout="wide"
)

# Header & Subheader
st.title("🛰️ SkyGuard AI: Intelligent Real-Time Anomaly Detection System for AWS")
st.markdown("##### Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD) — SIH PS 26073")

# Highlights Banner: Core Design Principles
st.info("""
🎯 **CORE DESIGN HIGHLIGHTS (IMD Hackathon Architecture)**:
1. **Decoupled Signal Layers**: Strict isolation between **Physics**, **Temporal**, and **Spatial** layers (lat/lon strictly restricted to geographic neighbor lookup — zero feature leakage).
2. **Weather vs. Sensor Fault Disambiguation**: $(\\text{Temporal Deviation} \\uparrow \\text{ AND Spatial Disagreement} \\downarrow) \\rightarrow \\mathbf{\\text{Real Severe Weather Event}}$ (eliminates false alarms during genuine extreme weather).
3. **IMD Self-Healing Network**: Automated real-time spatial IDW telemetry imputation for self-correcting weather station operations.
""")

# Sidebar Data & Mode Selection
st.sidebar.header("⚙️ Data Source & Parameters")
data_option = st.sidebar.selectbox(
    "Select Dataset",
    ["Simulated Multi-Station Network (India)", "Max Planck Institute Real Weather Dataset (Unlabelled)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Layer Weight Tuning")
p_weight = st.sidebar.slider("Physics Weight", 0.1, 0.6, 0.40, 0.05)
s_weight = st.sidebar.slider("Spatial Weight", 0.1, 0.6, 0.35, 0.05)
t_weight = st.sidebar.slider("Temporal Weight", 0.1, 0.6, 0.25, 0.05)

@st.cache_data(ttl=3600, show_spinner=False)
def get_pipeline_results(dataset_choice: str, pw: float, sw: float, tw: float):
    loader = AWSDataLoader()
    engine = FusionEngine(physics_wt=pw, spatial_wt=sw, temporal_wt=tw)
    explainer = ExplanationGenerator()

    if dataset_choice == "Simulated Multi-Station Network (India)":
        if os.path.exists(SYNTHETIC_DATA_PATH):
            df = loader.load_data(SYNTHETIC_DATA_PATH)
        else:
            df = generate_synthetic_aws_data(num_days=3)
    else:
        if not os.path.exists(REAL_CLEANED_DATA_PATH):
            df = loader.clean_max_planck_dataset(REAL_RAW_DATA_PATH, REAL_CLEANED_DATA_PATH)
        else:
            df = loader.load_data(REAL_CLEANED_DATA_PATH)
        # Subsample for fast UI responsiveness
        df = df.iloc[:1500].copy()

    processed_df = engine.process_pipeline(df, train_baseline=True)
    final_df = explainer.add_explanations_to_dataframe(processed_df)
    return final_df

df_results = get_pipeline_results(data_option, p_weight, s_weight, t_weight)

# Top Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)
total_obs = len(df_results)
anom_count = df_results['is_anomaly_pred'].sum()
weather_events = (df_results['root_cause'] == 'real_weather_event').sum()
anom_rate = (anom_count / total_obs) * 100.0 if total_obs > 0 else 0.0
avg_health = df_results['station_health_pct'].mean()

col1.metric("Total Telemetry Rows", f"{total_obs:,}")
col2.metric("Sensor Fault Anomalies", f"{anom_count:,}", f"{anom_rate:.1f}% rate", delta_color="inverse")
col3.metric("Real Weather Events Saved", f"{weather_events:,}", "Disambiguated", delta_color="normal")
col4.metric("Network Health Index", f"{avg_health:.1f}%")
col5.metric("Active Stations", f"{df_results['station_id'].nunique()}")

st.markdown("---")

# Navigation Tabs
tab_overview, tab_station, tab_alerts, tab_explain = st.tabs([
    "🗺️ Network Health & Disambiguation",
    "🩹 Self-Healing Telemetry Imputation",
    "🚨 Live Alert Feed & Root Causes",
    "🔬 3-Layer Decoupled Signal Evidence"
])

# TAB 1: Network Map & Summary
with tab_overview:
    st.subheader("Geographic Network Health Index Map")
    meta_df = df_results[['station_id', 'region', 'lat', 'lon', 'station_health_pct']].drop_duplicates('station_id')

    fig_map = px.scatter_geo(
        meta_df,
        lat='lat',
        lon='lon',
        color='station_health_pct',
        color_continuous_scale='RdYlGn',
        range_color=[50, 100],
        hover_name='station_id',
        hover_data=['region', 'station_health_pct'],
        size=np.full(len(meta_df), 16),
        title="AWS Network Station Health Index (%)",
        scope='asia' if data_option.startswith("Simulated") else 'world'
    )
    fig_map.update_geos(fitbounds="locations" if data_option.startswith("Simulated") else None)
    fig_map.update_layout(height=450, margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

    col_cause, col_health = st.columns(2)
    with col_cause:
        st.subheader("Classification & Disambiguation Breakdown")
        cause_df = df_results['root_cause'].value_counts().reset_index()
        cause_df.columns = ['Category', 'Count']
        fig_pie = px.pie(
            cause_df, names='Category', values='Count', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Sensor Faults vs Genuine Severe Weather Events"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_health:
        st.subheader("Station Health Index Rankings")
        st.dataframe(
            meta_df[['station_id', 'region', 'station_health_pct']].sort_values('station_health_pct'),
            use_container_width=True
        )

# TAB 2: Station Deep-Dive & Self-Healing Imputation
with tab_station:
    st.subheader("Self-Healing Telemetry Auto-Correction")
    st.markdown("""
    When a sensor fault is confirmed (e.g. $55^\\circ\\text{C}$ spike or frozen reading), the **Spatial IDW Interpolation Layer**
    calculates the expected true reading from surrounding healthy stations and **imputes the corrected telemetry**.
    """)

    st_list = df_results['station_id'].unique()
    selected_st = st.selectbox("Select AWS Station ID", st_list)

    st_df = df_results[df_results['station_id'] == selected_st].sort_values('timestamp')

    fig_ts = go.Figure()
    # Raw Temperature
    fig_ts.add_trace(go.Scatter(
        x=st_df['timestamp'], y=st_df['temperature_C'],
        mode='lines', name='Raw Sensor Telemetry (°C)', line=dict(color='lightgray', width=1.5)
    ))
    # Corrected / Imputed Temperature
    fig_ts.add_trace(go.Scatter(
        x=st_df['timestamp'], y=st_df['corrected_temp_C'],
        mode='lines', name='Self-Healing Imputed Telemetry (°C)', line=dict(color='green', width=2.0)
    ))
    # Anomaly Markers
    anom_rows = st_df[st_df['is_anomaly_pred']]
    if not anom_rows.empty:
        fig_ts.add_trace(go.Scatter(
            x=anom_rows['timestamp'], y=anom_rows['temperature_C'],
            mode='markers', name='Flagged Sensor Anomaly',
            marker=dict(color='red', size=9, symbol='x')
        ))

    fig_ts.update_layout(
        title=f"Telemetry & Self-Healing Auto-Correction Overlay for {selected_st}",
        xaxis_title="Timestamp", yaxis_title="Temperature (°C)",
        height=450, hovermode="x unified"
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("Raw vs Self-Healing Imputed Table (Anomalies Only)")
    anom_table = st_df[st_df['is_anomaly_pred']][
        ['timestamp', 'temperature_C', 'spatial_expected_temp', 'corrected_temp_C', 'root_cause', 'confidence_score']
    ]
    st.dataframe(anom_table, use_container_width=True)

# TAB 3: Alert Feed
with tab_alerts:
    st.subheader("Real-Time Anomaly Alert Log")
    anom_feed = df_results[df_results['is_anomaly_pred']].sort_values('timestamp', ascending=False)

    cause_filter = st.multiselect(
        "Filter by Root Cause",
        options=df_results['root_cause'].unique(),
        default=df_results['root_cause'].unique()
    )
    filtered_feed = anom_feed[anom_feed['root_cause'].isin(cause_filter)]

    st.write(f"Showing {len(filtered_feed)} anomaly alerts:")
    for _, row in filtered_feed.head(25).iterrows():
        st.error(f"⚠️ **{row['timestamp']}** | Station: `{row['station_id']}` | Cause: `{row['root_cause'].upper()}`\n\n{row['explanation']}")

# TAB 4: Explainability & Physics Rules
with tab_explain:
    st.subheader("3-Layer Decoupled Signal Evidence Matrix")
    st.markdown("""
    - **Physics Layer ($S_{\\text{physics}}$)**: Zero-false-positive deterministic checks (Dew Point $T_{dew} \\le T_{air}$, rate-of-change limits, range bounds).
    - **Temporal Layer ($S_{\\text{temporal}}$)**: Per-station Isolation Forest baseline model learning historical diurnal rhythm.
    - **Spatial Layer ($S_{\\text{spatial}}$)**: IDW distance comparison against geographic neighbors (location used **only** for distance computation).
    """)

    st.dataframe(
        df_results[
            ['timestamp', 'station_id', 'temperature_C', 'corrected_temp_C',
             'physics_score', 'temporal_score', 'spatial_score', 'root_cause', 'explanation']
        ].head(50),
        use_container_width=True
    )
