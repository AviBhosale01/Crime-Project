import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import base64

import database
import analytics
import visualizations

# Load security passkeys securely (from config_keys.py or Streamlit Secrets)
INTEL_ENTRY_KEY = None
VIEW_DATA_KEY = None

try:
    import config_keys
    INTEL_ENTRY_KEY = getattr(config_keys, "INTEL_ENTRY_KEY", None)
    VIEW_DATA_KEY = getattr(config_keys, "VIEW_DATA_KEY", None)
except ImportError:
    pass

if not INTEL_ENTRY_KEY:
    try:
        INTEL_ENTRY_KEY = st.secrets.get("INTEL_ENTRY_KEY", None)
    except Exception:
        INTEL_ENTRY_KEY = None

if not VIEW_DATA_KEY:
    try:
        VIEW_DATA_KEY = st.secrets.get("VIEW_DATA_KEY", None)
    except Exception:
        VIEW_DATA_KEY = None

# Set Streamlit Page Config
st.set_page_config(
    page_title="AI-Driven Crime Analytics Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Dark Theme & Glassmorphic Dashboard
# SEO & HTML Accessibility Meta Tags
st.markdown("""
<head>
    <meta name="description" content="AI-Driven Crime Intelligence Command Center: Real-time geospatial crime analytics, risk scoring, 30-day time-series forecasting, and criminal social network linkage platform.">
    <meta name="keywords" content="Crime Analytics, AI Crime Prediction, Police Intelligence, Recidivism Risk, DBSCAN Hotspots, Time-Series Forecasting">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "GovernmentService",
      "name": "Crime Intelligence Command Center",
      "provider": {
        "@type": "GovernmentOrganization",
        "name": "Pune Police Department"
      },
      "description": "Real-time AI-Powered Geospatial Crime Analytics, Risk Scoring & Criminal Network Linkage Platform"
    }
    </script>
</head>
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Main titles and headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
    }
    
    /* Muted text high-contrast override for accessibility (WCAG AA/AAA) */
    p, span, label, caption, .stCaption {
        color: #cbd5e1 !important;
    }
    
    /* Glowing card indicators */
    .kpi-card {
        background: rgba(17, 24, 39, 0.85);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.25);
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.6);
    }
    .kpi-title {
        font-size: 0.875rem;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    .kpi-trend {
        font-size: 0.775rem;
        margin-top: 4px;
        font-weight: 500;
    }
    .trend-up {
        color: #f87171 !important;
    }
    .trend-down {
        color: #34d399 !important;
    }
    
    /* Custom badge/alert styling */
    .anomaly-alert {
        padding: 12px;
        background-color: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    
    /* Button custom styles */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white !important;
        border: none;
        padding: 8px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: opacity 0.2s;
    }
    div.stButton > button:hover {
        opacity: 0.9;
        border: none;
    }
    
    /* Adjust map & chart containers to prevent layout shifts (CLS fix) */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(75, 85, 99, 0.2);
        min-height: 380px;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
database.init_db()

# --- Load Datasets ---
# Cached for performance, but with manual refresh capability
@st.cache_data(ttl=60)
def load_base_data(filter_dict=None):
    df_crimes = database.get_crimes_df(filter_dict)
    df_suspects = database.get_suspects_df()
    df_districts = database.get_districts_df()
    df_connections = database.get_connections_df()
    return df_crimes, df_suspects, df_districts, df_connections

# App Header
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; border-bottom: 1px solid rgba(75, 85, 99, 0.2); padding-bottom: 15px;">
    <div>
        <h1 style="margin: 0; font-size: 2.2rem; background: linear-gradient(to right, #ffffff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🛡️ Crime Intelligence Command Center</h1>
        <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;">Real-time AI-Powered Geospatial Crime Analytics, Risk Scoring & Criminal Network Linkage Platform</p>
    </div>
    <div style="text-align: right;">
        <span style="background-color: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #93c5fd; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">System Online</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.markdown("""
<div style="text-align: center; padding: 15px 0;">
    <h3 style="margin: 0; color: #60a5fa;">INTELLIGENCE SUITE</h3>
    <hr style="border-top: 1px solid #1f2937; margin: 10px 0;">
</div>
""", unsafe_allow_html=True)

# Navigation
nav_options = [
    "📊 Command Dashboard",
    "🗺️ Geospatial Intelligence",
    "🔍 Search & Explorer",
    "🧠 AI Predictive Models",
    "🕸️ Criminal Network Analysis",
    "📝 Intel Entry (CRUD)",
    "📂 View Data",
    "💬 AI Intel Chatbot",
    "📰 Crime News"
]

# Handle programmatic page redirection (e.g. from floating assistant widget)
if "requested_page" in st.session_state and st.session_state["requested_page"]:
    req_p = st.session_state.pop("requested_page")
    if req_p in nav_options:
        st.session_state["nav_radio"] = req_p

if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = "📊 Command Dashboard"

selected_page = st.sidebar.radio("Navigation", nav_options, key="nav_radio")

st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 15px 0;'>", unsafe_allow_html=True)
st.sidebar.subheader("Filter Workspace")

# Pull initial unique fields for filter dropdowns
_, suspects_raw, districts_raw, _ = load_base_data()

# District Filter
district_names = sorted(districts_raw['name'].tolist())
selected_districts = st.sidebar.multiselect("Areas / Locations", district_names, default=[])

# Crime Type Filter
crime_types_list = ["Theft", "Burglary", "Assault", "Narcotics", "Fraud", "Cybercrime", "Homicide"]
selected_crime_types = st.sidebar.multiselect("Crime Types", crime_types_list, default=[])

# Severity Filter
severity_list = ["Low", "Medium", "High"]
selected_severities = st.sidebar.multiselect("Severities", severity_list, default=[])

# Time Range Filter
start_date_input = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
end_date_input = st.sidebar.date_input("End Date", datetime.now())

# Compile filter dictionary
filter_dict = {}
if selected_districts:
    # Map district names to database IDs
    d_ids = districts_raw[districts_raw['name'].isin(selected_districts)]['id'].tolist()
    filter_dict["district_ids"] = d_ids
if selected_crime_types:
    filter_dict["crime_types"] = selected_crime_types
if selected_severities:
    filter_dict["severities"] = selected_severities

# Format dates to string for query filter
filter_dict["start_date"] = start_date_input.strftime("%Y-%m-%d 00:00:00")
filter_dict["end_date"] = end_date_input.strftime("%Y-%m-%d 23:59:59")

# Fetch filtered datasets
df_crimes, df_suspects, df_districts, df_connections = load_base_data(filter_dict)

# Sidebar Live Dispatch Feed Simulator
st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 25px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("### 📡 Live Dispatch Feed")
live_feed_active = st.sidebar.toggle("🔴 Simulate PCR Patrol Feed", value=False)
if live_feed_active:
    import random
    sectors = ["Hinjawadi", "Kothrud", "Koregaon Park", "Shivajinagar", "Viman Nagar", "Hadapsar"]
    c_types = ["Theft", "Cybercrime", "Burglary", "Narcotics", "Assault"]
    sec = random.choice(sectors)
    ctype = random.choice(c_types)
    pcr_id = random.randint(1, 15)
    t_str = datetime.now().strftime("%I:%M:%S %p")
    st.sidebar.error(f"🚨 **[{t_str}] Dispatch Alert**: PCR-{pcr_id} routed to **{sec}** ({ctype}).")

st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 15px 0;'>", unsafe_allow_html=True)
st.sidebar.caption("🤖 **AI Platform Core Status**")
st.sidebar.caption("• Database: SQLite v3")
st.sidebar.caption("• Hotspot Model: DBSCAN Active")
st.sidebar.caption("• Anomaly Threshold: 2.0 Z-score")
st.sidebar.caption("• Recidivism Predictor: RF Regressor")

# Sidebar Author Badge
st.sidebar.markdown("""
<div style="text-align: center; margin-top: 20px; padding: 12px 0; border-top: 1px solid rgba(75, 85, 99, 0.4);">
    <span style="color: #9ca3af; font-size: 0.85rem;">Made by </span>
    <a href="https://github.com/AviBhosale01" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 700; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 4px;">
        Avii
        <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: middle; fill: #60a5fa;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
    </a>
</div>
""", unsafe_allow_html=True)

# --- Page 1: Command Dashboard ---
if selected_page == "📊 Command Dashboard":
    dash_tab_live, dash_tab_ncrb = st.tabs(["📈 Live Operations (DB)", "🏛️ Pune Police Statistics (NCRB)"])
    
    with dash_tab_live:
        st.caption("ℹ️ **Operational Simulation Database**: The live metrics below are dynamically populated demo records for Pune crime pattern testing. For official historical figures, switch to the **Pune Police Statistics (NCRB)** tab.")
        
        # 1. KPI Cards Row
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        # Calculate stats
        total_crimes = len(df_crimes)
        
        # Active hotspots (using DBSCAN clustering)
        df_clustered = analytics.detect_hotspots(df_crimes, eps_km=0.5, min_samples=6)
        active_hotspots = max(0, df_clustered['hotspot_id'].nunique() - (1 if -1 in df_clustered['hotspot_id'].values else 0))
        
        # High-risk suspects (ML risk score > 0.6)
        high_risk_suspects = len(df_suspects[df_suspects['risk_score'] > 0.65])
        
        # Run anomaly detection to count total z-score anomalies in selection range
        daily_stats, _ = analytics.detect_anomalies_rolling(df_crimes)
        total_anomalies = len(daily_stats[daily_stats['is_anomaly'] == True]) if not daily_stats.empty else 0
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Crime Records</div>
                <div class="kpi-value">{total_crimes:,}</div>
                <div class="kpi-trend trend-up">⚠️ In selection filters</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Hotspot Zones</div>
                <div class="kpi-value">{active_hotspots}</div>
                <div class="kpi-trend trend-down">💡 DBSCAN Clusters</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">High-Risk Suspects</div>
                <div class="kpi-value">{high_risk_suspects}</div>
                <div class="kpi-trend trend-up">🔴 Score &gt; 0.65</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Trend Alerts (Anomalies)</div>
                <div class="kpi-value">{total_anomalies}</div>
                <div class="kpi-trend trend-up">📈 Z-Score Spikes</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Main Visualization Row
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("### Crime Distribution by Category")
            if not df_crimes.empty:
                type_counts = df_crimes['crime_type'].value_counts().reset_index()
                type_counts.columns = ['Crime Type', 'Count']
                fig_pie = px.pie(
                    type_counts, 
                    values='Count', 
                    names='Crime Type', 
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(
                    margin=dict(t=30, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            else:
                st.info("No crime data fits the selected filters.")
                
        with col_chart2:
            st.markdown("### Incident Frequencies by District")
            if not df_crimes.empty:
                district_counts = df_crimes['district_name'].value_counts().reset_index()
                district_counts.columns = ['District', 'Incidents']
                fig_bar = px.bar(
                    district_counts,
                    x='Incidents',
                    y='District',
                    orientation='h',
                    color='Incidents',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(
                    margin=dict(t=30, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            else:
                st.info("No crime data fits the selected filters.")
                
        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        
        # 2.5 Patrol Resource Optimization (Decision-Support System)
        st.markdown("### 🚓 Tactical Patrol Unit (PCR) Allocation Optimizer")
        st.write("Proportional risk-weighted decision-support system: optimizes $N$ active patrol vans across Pune police sectors to maximize spatial coverage and minimize emergency response latency.")
        
        col_opt_ctrl, col_opt_kpi = st.columns([1, 1.5])
        with col_opt_ctrl:
            num_vans = st.slider("Available Police Control Room (PCR) Vans", 5, 30, 14, key="slider_num_vans")
            patrol_df = analytics.optimize_patrol_allocations(df_crimes, df_districts, num_patrol_units=num_vans)
            
            if not patrol_df.empty:
                avg_response = patrol_df['expected_response_min'].mean()
                avg_coverage = patrol_df['coverage_pct'].mean()
                
                pk1, pk2 = st.columns(2)
                with pk1:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Est. Response Latency</div><div class="kpi-value" style="color: #10B981;">{avg_response:.1f} mins</div></div>""", unsafe_allow_html=True)
                with pk2:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Spatial Coverage</div><div class="kpi-value" style="color: #60A5FA;">{avg_coverage:.1f}%</div></div>""", unsafe_allow_html=True)
                    
        with col_opt_kpi:
            if not patrol_df.empty:
                fig_patrol = visualizations.create_patrol_optimization_chart(patrol_df)
                st.plotly_chart(fig_patrol, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        
        # 3. Anomaly Alerts & Details Row
        col_anomaly, col_priors = st.columns([3, 2])
        
        with col_anomaly:
            st.markdown("### 🚨 Crime Trend Anomaly Alerts")
            if not daily_stats.empty:
                active_alerts = daily_stats[daily_stats['is_anomaly'] == True].sort_values(by='date', ascending=False)
                if not active_alerts.empty:
                    st.markdown(f"Detected **{len(active_alerts)}** statistical crime spikes in history range:")
                    for _, alert in active_alerts.head(5).iterrows():
                        dt_str = alert['date'].strftime('%Y-%m-%d')
                        st.markdown(
                            f"""<div class="anomaly-alert">
                                <strong>{dt_str}</strong> - Spiked to <strong>{alert['crime_count']}</strong> crimes! 
                                (Expected 14-day rolling average: <em>{alert['rolling_mean']:.1f}</em>, Z-score: <em>{alert['z_score']:.2f}</em>)
                            </div>""", unsafe_allow_html=True
                        )
                else:
                    st.success("No active frequency anomalies detected in this range.")
            else:
                st.info("No historical daily aggregation available.")
                
        with col_priors:
            st.markdown("### 👤 High-Risk Recidivists (Repeat Offenders)")
            if not df_suspects.empty:
                repeat_offenders = df_suspects.sort_values(by='priors_count', ascending=False).head(5)
                # Display as custom markdown list
                for _, r in repeat_offenders.iterrows():
                    badge_color = "#ef4444" if r['risk_score'] > 0.75 else ("#f59e0b" if r['risk_score'] > 0.45 else "#10b981")
                    st.markdown(
                        f"""<div style="background-color: #1f2937; padding: 12px; border-radius: 8px; border: 1px solid rgba(75,85,99,0.3); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #ffffff;">{r['name']}</strong> (Age: {r['age']})<br>
                                <span style="color: #9ca3af; font-size: 0.85rem;">Gang: {r['gang_affiliation']}</span>
                            </div>
                            <div style="text-align: right;">
                                <span style="background-color: {badge_color}; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 700;">Risk: {r['risk_score']:.2f}</span><br>
                                <span style="color: #9ca3af; font-size: 0.8rem; font-weight: 600;">{r['priors_count']} Priors</span>
                            </div>
                        </div>""", unsafe_allow_html=True
                    )
            else:
                st.info("No suspect intelligence records available.")

    with dash_tab_ncrb:
        st.success("🏛️ **Official NCRB Benchmark Data**: The statistics below are compiled from official National Crime Records Bureau (NCRB) publications and Pune Police annual crime reports.")
        st.markdown("### 🏛️ Pune City Police — Official Historical Crime Statistics (NCRB)")
        st.write("Browse official data compiled from National Crime Records Bureau (NCRB) publications and Pune Police reviews showing yearly trends and solvability analytics.")

        # Tab metrics / summary
        ncrb_col1, ncrb_col2, ncrb_col3 = st.columns(3)
        with ncrb_col1:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Total Cognizable Volume (2023)</div>
                <div class="kpi-value">17,022</div>
                <div class="kpi-trend trend-up">🔺 +20.1% YoY</div>
            </div>
            """, unsafe_allow_html=True)
        with ncrb_col2:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Homicides (2025)</div>
                <div class="kpi-value">79</div>
                <div class="kpi-trend trend-down">🟢 -21.7% vs 2023</div>
            </div>
            """, unsafe_allow_html=True)
        with ncrb_col3:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Pune Safety Index</div>
                <div class="kpi-value">Top 2</div>
                <div class="kpi-trend trend-down">💡 Safest Metro in India (NCRB 2022)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 1: Cognizable cases & Violent Crimes
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.markdown("#### Annual Cognizable Cases (IPC + SLL)")
            df_cog = pd.DataFrame({
                "Year": ["2021", "2022", "2023"],
                "IPC Cases": [9511, 11074, 12542],
                "SLL Cases": [3458, 3099, 4480],
                "Total Cases": [12969, 14173, 17022]
            })
            
            fig_cog = go.Figure()
            fig_cog.add_trace(go.Bar(x=df_cog["Year"], y=df_cog["IPC Cases"], name="IPC Cases", marker_color="#393E46"))
            fig_cog.add_trace(go.Bar(x=df_cog["Year"], y=df_cog["SLL Cases"], name="SLL Cases", marker_color="#00ADB5"))
            fig_cog.add_trace(go.Scatter(x=df_cog["Year"], y=df_cog["Total Cases"], name="Total Crime Volume", line=dict(color="#EEEEEE", width=2.5)))
            
            fig_cog.update_layout(
                barmode='stack',
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_cog, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with row1_col2:
            st.markdown("#### Violent Crime Category Trends (2021–2025)")
            df_violent = pd.DataFrame({
                "Year": ["2021", "2022", "2023", "2024", "2025"],
                "Murder": [100, 104, 101, 93, 79],
                "Attempt to Murder": [296, 280, 240, 240, 179],
                "Assault (Hurt)": [938, 1060, 1362, 1515, 1453]
            })
            
            fig_violent = go.Figure()
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Murder"], name="Murders", line=dict(color="#00ADB5", width=2)))
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Attempt to Murder"], name="Attempt to Murder", line=dict(color="#EEEEEE", width=2, dash="dash")))
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Assault (Hurt)"], name="Non-fatal Assaults", line=dict(color="#393E46", width=2)))
            
            fig_violent.update_layout(
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_violent, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        # Row 2: Cybercrime & Social Crimes
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            st.markdown("#### Cybercrime Offenses (Rising Trends)")
            df_cyber = pd.DataFrame({
                "Year": ["2021", "2022", "2023"],
                "Cases": [225, 357, 487]
            })
            fig_cyber = px.bar(df_cyber, x="Year", y="Cases", text="Cases", color_discrete_sequence=["#00ADB5"])
            fig_cyber.update_layout(
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            fig_cyber.update_traces(textposition='outside')
            st.plotly_chart(fig_cyber, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            
        with row2_col2:
            st.markdown("#### Vulnerable Demographics Trends")
            df_vuln = pd.DataFrame({
                "Year": ["2021", "2022", "2023"],
                "Crimes Against Women": [1616, 2074, 2550],
                "Crimes Against Children": [835, 732, 1234]
            })
            fig_vuln = go.Figure()
            fig_vuln.add_trace(go.Bar(x=df_vuln["Year"], y=df_vuln["Crimes Against Women"], name="Against Women", marker_color="#393E46"))
            fig_vuln.add_trace(go.Bar(x=df_vuln["Year"], y=df_vuln["Crimes Against Children"], name="Against Children", marker_color="#00ADB5"))
            fig_vuln.update_layout(
                barmode='group',
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_vuln, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        
        # Row 3: Pimpri-Chinchwad Police (PCPC) & Preventive Actions
        st.markdown("### Pimpri-Chinchwad Police Commissionerate (PCPC) — 2025 Annual Crime Report")
        
        pc_col1, pc_col2 = st.columns(2)
        with pc_col1:
            st.markdown("#### PCPC Crime Solver Rates (2025)")
            df_pcpc = pd.DataFrame({
                "Category": ["Dacoity", "Robbery", "Chain Snatching", "Burglary", "Vehicle Theft", "Overall Property", "Murder", "Cybercrime"],
                "Cases": [20, 182, 75, 285, 960, 2129, 63, 269],
                "Solved %": [100.0, 87.0, 83.0, 51.0, 39.0, 47.0, 95.0, 35.0]
            })
            
            fig_pcpc = px.bar(
                df_pcpc, 
                x="Solved %", 
                y="Category", 
                orientation="h", 
                color="Cases",
                color_continuous_scale="Blues",
                labels={"Category": "Crime Type", "Solved %": "Detection Rate (%)", "Cases": "Cases Registered"},
                title="PCPC Case Solved / Detection Rates"
            )
            fig_pcpc.update_layout(
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_pcpc, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            
        with pc_col2:
            st.markdown("#### Preventive & Legal Actions (PCPC 2025)")
            df_prev = pd.DataFrame({
                "Action Type": ["MPDA Act", "MCOCA Act", "Externment Actions", "BNS 126 (Wrongful Restraint)", "BNS 129 (Criminal Force)", "Total Actions"],
                "Cases Count": [35, 213, 368, 5474, 3243, 12295]
            })
            
            st.dataframe(
                df_prev.rename(columns={"Action Type": "Action / Statute Type", "Cases Count": "Total Preventative Actions Logged"}),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("""
            > **MCOCA (Maharashtra Control of Organised Crime Act)** is actively invoked to curb syndicate activity, showing 213 actions in 2025. 
            > **Externment** orders were executed on 368 repeat offenders, expelling them from city limits to maintain law and order.
            """)

# --- Page 2: Geospatial Intelligence ---
elif selected_page == "🗺️ Geospatial Intelligence":
    st.markdown("## Geospatial Analytics & Spatial Hotspot Detection")
    st.write("Leverage Density-Based Spatial Clustering (DBSCAN) to identify crime clusters and hotspots across districts.")
    
    # Mapping Controls
    map_type = st.radio("Select Analysis Layer", ["Incident Locations Scatter", "DBSCAN Cluster Hotspots", "Kernel Density Heatmap"], horizontal=True)
    
    if map_type == "DBSCAN Cluster Hotspots":
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            eps_slider = st.slider("DBSCAN Epsilon (roughly km range)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, help="Max distance between two crime points to be considered as same cluster.")
        with col_ctrl2:
            min_pts_slider = st.slider("Min Incidents to Define Hotspot", min_value=3, max_value=20, value=6, step=1, help="Minimum number of crimes in epsilon radius to create a cluster.")
            
        # Detect hotspots
        df_geo = analytics.detect_hotspots(df_crimes, eps_km=eps_slider, min_samples=min_pts_slider)
        
        # Display hotspot statistics
        active_ids = [hid for hid in df_geo['hotspot_id'].unique() if hid != -1]
        
        st.markdown(f"🤖 **Clustering Output**: Detected **{len(active_ids)}** active crime hotspot zones. Isolated incident points are marked as Noise.")
        
        # Dropdown to isolate specific hotspot
        hs_options = ["Show All Hotspots"] + [f"Hotspot Zone {hid}" for hid in sorted(active_ids)]
        sel_hs = st.selectbox("Isolate Specific Cluster Zone", hs_options)
        
        selected_id = None
        if sel_hs != "Show All Hotspots":
            selected_id = int(sel_hs.split()[-1])
            
        map_fig = visualizations.create_geospatial_map(df_geo, show_hotspots=True, selected_hotspot_id=selected_id)
        st.plotly_chart(map_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
        # Hotspot Details Table
        if len(active_ids) > 0:
            st.markdown("### Hotspot Breakdown")
            hs_details = []
            for hid in active_ids:
                sub_df = df_geo[df_geo['hotspot_id'] == hid]
                common_crime = sub_df['crime_type'].mode()[0] if not sub_df.empty else "N/A"
                common_district = sub_df['district_name'].mode()[0] if not sub_df.empty else "N/A"
                hs_details.append({
                    "Hotspot Zone": f"Zone {hid}",
                    "Incidents Count": len(sub_df),
                    "Dominant Crime": common_crime,
                    "Location / District": common_district,
                    "Avg Severity": "High" if (sub_df['severity'] == 'High').mean() > 0.4 else "Medium"
                })
            st.table(pd.DataFrame(hs_details))
            
    elif map_type == "Kernel Density Heatmap":
        density_fig = visualizations.create_density_map(df_crimes)
        st.plotly_chart(density_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
    else: # Standard scatter map
        scatter_fig = visualizations.create_geospatial_map(df_crimes, show_hotspots=False)
        st.plotly_chart(scatter_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

# --- Page 2.5: Search & Explorer ---
elif selected_page == "🔍 Search & Explorer":
    st.markdown("## 🔍 Intelligence Search & Exploration")
    st.write("Perform search queries and apply filters across the entire database of 2,000+ Maharashtrian suspects and 3,000+ Pune crime reports.")

    tab_suspect_search, tab_crime_search = st.tabs([
        "👤 Suspect Directory Search",
        "⚠️ Crime Registry Search"
    ])

    with tab_suspect_search:
        st.markdown("### Search Suspect Profiles")
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1:
            s_query = st.text_input("Search Suspect Name", placeholder="e.g. Patil, Rahul, Deshmukh...", key="sus_name_search")
        with col_s2:
            gang_list = ["All"] + sorted(list(df_suspects['gang_affiliation'].unique()))
            selected_gang_filter = st.selectbox("Filter by Gang Affiliation", gang_list)
        with col_s3:
            risk_filter = st.slider("Min Risk Score", 0.0, 1.0, 0.0, 0.05)

        # Apply filtering logic
        filtered_sus = df_suspects.copy()
        if s_query:
            filtered_sus = filtered_sus[filtered_sus['name'].str.contains(s_query, case=False, na=False)]
        if selected_gang_filter != "All":
            filtered_sus = filtered_sus[filtered_sus['gang_affiliation'] == selected_gang_filter]
        if risk_filter > 0.0:
            filtered_sus = filtered_sus[filtered_sus['risk_score'] >= risk_filter]

        st.markdown(f"Found **{len(filtered_sus)}** matching suspects.")

        if not filtered_sus.empty:
            display_df = filtered_sus.head(50).copy()
            st.dataframe(
                display_df[['id', 'name', 'age', 'gang_affiliation', 'priors_count', 'risk_score']].rename(
                    columns={
                        'id': 'ID', 'name': 'Full Name', 'age': 'Age',
                        'gang_affiliation': 'Gang Affiliation', 'priors_count': 'Prior Arrests',
                        'risk_score': 'ML Risk Index'
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
            if len(filtered_sus) > 50:
                st.caption("⚠️ Showing the first 50 matches. Refine your search query to narrow down results.")

            # Suspect Profiler Inspector
            st.markdown("---")
            st.markdown("### 🔍 Suspect Dossier Inspector")
            st.write("Select a suspect from the matches to pull their full intelligence profile and crime timeline:")
            suspect_names_map = {row['id']: f"{row['name']} (ID: {row['id']})" for _, row in display_df.iterrows()}
            selected_inspect_id = st.selectbox("Inspect Suspect Dossier", list(suspect_names_map.keys()), format_func=lambda x: suspect_names_map[x])

            if selected_inspect_id:
                s_data = df_suspects[df_suspects['id'] == selected_inspect_id].iloc[0]
                
                det_col1, det_col2 = st.columns([1, 2])
                with det_col1:
                    risk_val = s_data['risk_score']
                    color = "#ef4444" if risk_val > 0.65 else ("#f59e0b" if risk_val > 0.35 else "#10b981")
                    st.markdown(f"""
                    <div style="background-color: #111827; padding: 20px; border-radius: 12px; border: 1px solid rgba(75,85,99,0.3); text-align: center;">
                        <h4 style="margin: 0; color: #9ca3af;">{s_data['name']}</h4>
                        <div style="font-size: 2.5rem; font-weight: 800; color: {color}; margin: 10px 0;">{risk_val:.2f}</div>
                        <span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">ML Risk Index</span>
                        <hr style="border-top: 1px solid #1f2937; margin: 15px 0;">
                        <div style="text-align: left; font-size: 0.9rem; line-height: 1.6;">
                            <b>Database ID:</b> {s_data['id']}<br>
                            <b>Age:</b> {s_data['age']}<br>
                            <b>Gang Affiliation:</b> {s_data['gang_affiliation']}<br>
                            <b>Priors:</b> {s_data['priors_count']} arrests
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with det_col2:
                    timeline_fig = visualizations.create_offender_timeline(selected_inspect_id, df_crimes, s_data['name'])
                    st.plotly_chart(timeline_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        else:
            st.info("No suspects match your search query and filters.")

    with tab_crime_search:
        st.markdown("### Search Crime Registry")
        col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
        with col_c1:
            c_query = st.text_input("Search Crime Type or Status", placeholder="e.g. Theft, Open, In Investigation...", key="crime_search_query")
        with col_c2:
            c_dist_list = ["All"] + sorted(list(df_crimes['district_name'].unique()))
            selected_c_dist = st.selectbox("Filter by Area / Location", c_dist_list, key="crime_dist_filter")
        with col_c3:
            c_severity_filter = st.selectbox("Filter by Severity", ["All"] + severity_list)

        filtered_crimes = df_crimes.copy()
        if c_query:
            filtered_crimes = filtered_crimes[
                filtered_crimes['crime_type'].str.contains(c_query, case=False, na=False) |
                filtered_crimes['status'].str.contains(c_query, case=False, na=False)
            ]
        if selected_c_dist != "All":
            filtered_crimes = filtered_crimes[filtered_crimes['district_name'] == selected_c_dist]
        if c_severity_filter != "All":
            filtered_crimes = filtered_crimes[filtered_crimes['severity'] == c_severity_filter]

        st.markdown(f"Found **{len(filtered_crimes)}** matching crimes.")

        if not filtered_crimes.empty:
            display_crimes = filtered_crimes.head(100).copy()
            display_crimes['timestamp_str'] = display_crimes['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(
                display_crimes[['crime_id', 'timestamp_str', 'district_name', 'crime_type', 'severity', 'status', 'suspect_name']].rename(
                    columns={
                        'crime_id': 'Crime ID', 'timestamp_str': 'Timestamp', 'district_name': 'District',
                        'crime_type': 'Crime Category', 'severity': 'Severity', 'status': 'Status',
                        'suspect_name': 'Linked Suspect'
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
            if len(filtered_crimes) > 100:
                st.caption("⚠️ Showing the first 100 crime logs. Refine your search filters to narrow down results.")
        else:
            st.info("No crime incidents match your search criteria.")

# --- Page 3: AI Predictive Models ---
elif selected_page == "🧠 AI Predictive Models":
    st.markdown("## 🧠 AI/ML Forecasting & Scientific Predictive Intelligence")
    st.write("Production-grade machine learning predictive suite for police commanders: evaluate incident severity, forecast suspect recidivism risk, generate 30-day forward time-series crime projections, analyze socio-economic correlations, and detect rolling anomaly spikes.")
    
    tab_predict, tab_suspect, tab_forecast, tab_socio, tab_anomaly = st.tabs([
        "🔮 Incident Severity Classifier",
        "👤 Recidivism Risk (Suspects)",
        "📈 30-Day Forward Forecasting",
        "📊 Socio-Economic Correlations",
        "🚨 Rolling Anomaly Detection"
    ])
    
    # Tab 1: Incident Severity Classification
    with tab_predict:
        st.markdown("### Predict Potential Crime Severity")
        st.write("Random Forest Classifier trained on historical crime logs using spatio-temporal features, district socio-economics, and category indicators with 80/20 train/test evaluation and 5-fold cross-validation.")
        
        # Train model
        model_dict, train_msg = analytics.train_severity_predictor(df_crimes)
        
        if model_dict:
            # Model Validation Performance Metrics Banner
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Out-of-Sample Accuracy</div><div class="kpi-value" style="color: #34d399;">{model_dict['accuracy']*100:.1f}%</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Weighted F1-Score</div><div class="kpi-value" style="color: #60a5fa;">{model_dict['f1_score']:.3f}</div></div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">5-Fold CV Accuracy</div><div class="kpi-value" style="color: #fbbf24;">{model_dict['cv_mean']*100:.1f}% ± {model_dict['cv_std']*100:.1f}%</div></div>""", unsafe_allow_html=True)
            with m4:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Dataset Size</div><div class="kpi-value" style="font-size: 1.1rem; color: #a855f7;">{len(df_crimes):,} Incident Logs</div></div>""", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_in1, col_in2 = st.columns(2)
            
            with col_in1:
                st.markdown("#### Input Incident Conditions")
                in_district = st.selectbox("Incident Area / Location", district_names, key="pred_district_sel")
                in_type = st.selectbox("Crime Category", crime_types_list, key="pred_type_sel")
                in_hour = st.slider("Hour of Day (24h Clock)", 0, 23, 12, key="pred_hour_slider")
                in_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="pred_day_sel")
                
                day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                day_idx = day_map[in_day]
                
                dist_row = df_districts[df_districts['name'] == in_district].iloc[0]
                
                predict_btn = st.button("Calculate Severity Risk", key="btn_calc_severity")
                
            with col_in2:
                st.markdown("#### Prediction Output & Tactical Advisory")
                if predict_btn:
                    input_data = {
                        "district_name": in_district,
                        "crime_type": in_type,
                        "hour": in_hour,
                        "day_of_week": day_idx,
                        "month": datetime.now().month,
                        "is_weekend": 1.0 if day_idx >= 5 else 0.0,
                        "unemployment_rate": dist_row['unemployment_rate'],
                        "poverty_index": dist_row['poverty_index'],
                        "median_income": dist_row['median_income'],
                        "education_index": dist_row['education_index'],
                        "population_density": dist_row['population_density']
                    }
                    
                    pred_class, class_probs = analytics.predict_incident_severity(model_dict, input_data)
                    
                    color_map = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"}
                    bg_color = color_map[pred_class]
                    
                    st.markdown(
                        f"""<div style="background-color: {bg_color}; color: white; padding: 18px; border-radius: 10px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                            <div style="font-size: 0.85rem; text-transform: uppercase; font-weight: 600; opacity: 0.9;">Predicted Severity Classification</div>
                            <h3 style="margin: 5px 0 0 0; text-transform: uppercase; font-size: 1.8rem; font-weight: 800;">{pred_class} SEVERITY</h3>
                        </div>""", unsafe_allow_html=True
                    )
                    
                    st.write("**Model Confidence Breakdown:**")
                    for cls, prob in class_probs.items():
                        st.progress(float(prob), text=f"{cls} Severity Probability: {prob*100:.1f}%")
                        
                    st.markdown("---")
                    st.markdown("##### 🛡️ Tactical Police Advisory")
                    if pred_class == "High":
                        st.error("🚨 **HIGH SEVERITY DIRECTIVE**: Dispatch Mobile Patrol (PCR) Van immediately. Alert Station House Officer (SHO) and Divisional ACP. Monitor local CCTV feeds in real time.")
                    elif pred_class == "Medium":
                        st.warning("🟡 **MEDIUM SEVERITY DIRECTIVE**: Increase beat constable patrolling in the sector. Schedule random vehicle nakabandi checks during specified hour range.")
                    else:
                        st.success("🟢 **ROUTINE DIRECTIVE**: Log incident entry and assign standard beat constable coverage.")
                        
            st.markdown("<br><hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)
            
            col_diag1, col_diag2 = st.columns([1.2, 1])
            with col_diag1:
                st.markdown("#### Random Forest Feature Importance Analysis")
                st.write("Top spatio-temporal and socio-economic variables influencing severity prediction:")
                
                feat_imp = model_dict['feature_importance'].head(8).reset_index()
                feat_imp.columns = ['Feature', 'Importance']
                feat_imp['Feature'] = feat_imp['Feature'].str.replace('dist_', 'District: ').str.replace('type_', 'Type: ').str.replace('_', ' ').str.title()
                
                fig_imp = px.bar(feat_imp, x='Importance', y='Feature', orientation='h', color='Importance', color_continuous_scale='Purples')
                fig_imp.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                fig_imp.update_yaxes(categoryorder="total ascending")
                st.plotly_chart(fig_imp, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                
            with col_diag2:
                st.markdown("#### Model Confusion Matrix Diagnostics")
                st.write("Validation test set predictions vs ground-truth crime severity:")
                fig_cm = visualizations.create_confusion_matrix_chart(model_dict['confusion_matrix'], model_dict['classes'])
                st.plotly_chart(fig_cm, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            
        else:
            st.warning(train_msg)
            
    # Tab 2: Suspect Recidivism Prediction
    with tab_suspect:
        st.markdown("### Suspect Recidivism Risk Forecaster")
        st.write("Random Forest Regressor evaluating suspect demographic & arrest history to compute a **Recidivism Risk Index**.")
        
        sus_model_dict, sus_msg = analytics.train_recidivism_predictor(df_suspects)
        
        if sus_model_dict:
            # Model Metrics Banner
            sm1, sm2, sm3, sm4 = st.columns(4)
            with sm1:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Model R² Score</div><div class="kpi-value" style="color: #34d399;">{sus_model_dict['r2']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm2:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Mean Absolute Error (MAE)</div><div class="kpi-value" style="color: #60a5fa;">{sus_model_dict['mae']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm3:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">RMSE Metric</div><div class="kpi-value" style="color: #fbbf24;">{sus_model_dict['rmse']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm4:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">5-Fold CV R² Mean</div><div class="kpi-value" style="color: #a855f7;">{sus_model_dict['cv_r2_mean']:.3f}</div></div>""", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_sus1, col_sus2 = st.columns([1, 1.2])
            with col_sus1:
                st.markdown("#### Input Suspect Profile")
                s_age = st.slider("Suspect Age", 18, 90, 30, key="sus_age_slider")
                s_priors = st.number_input("Prior Offenses (Arrests)", min_value=0, max_value=50, value=2, key="sus_priors_input")
                s_gang = st.selectbox("Gang Affiliation Status", ["None", "Pune Local Boys", "Shivaji Nagar Syndicate", "Koregaon Park Cartel", "Hinjawadi Hackers", "D-Company Gang", "Chhota Rajan Gang"], key="sus_gang_sel")
                
                calc_sus = st.button("Evaluate Recidivism Risk Index", key="btn_eval_recidivism")
                
            with col_sus2:
                st.markdown("#### Evaluated Risk Gauge & Police Directive")
                if calc_sus:
                    pred_risk = analytics.predict_suspect_risk(sus_model_dict, s_age, s_priors, s_gang)
                    
                    fig_gauge = visualizations.create_recidivism_gauge_chart(pred_risk)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                    
                    higher_count = len(df_suspects[df_suspects['risk_score'] > pred_risk])
                    total_sus = len(df_suspects)
                    pct = (higher_count / total_sus) * 100.0
                    st.caption(f"📊 **Database Percentile**: This profile risks higher than **{100.0 - pct:.1f}%** of suspects in the Pune Crime Registry.")
                    
                    st.markdown("##### 👮 Police Actionable Directive")
                    if pred_risk > 0.65:
                        st.error("🚨 **CRITICAL SURVEILLANCE DIRECTIVE**: High Recidivist Risk Index (> 0.65). List under History-Sheeter Register, initiate electronic & physical surveillance, and evaluate CrPC Sec 110 preventive action.")
                    elif pred_risk > 0.35:
                        st.warning("🟡 **ELEVATED MONITORING DIRECTIVE**: Moderate Recidivist Risk Index (0.35 - 0.65). Require bi-weekly Police Station Attendance roll-call and verify local employment.")
                    else:
                        st.success("🟢 **ROUTINE RECORD DIRECTIVE**: Low Recidivist Risk Index (< 0.35). Maintain standard station records; no active surveillance required.")
        else:
            st.warning(sus_msg)
            
    # Tab 3: 30-Day Forward Crime Forecasting
    with tab_forecast:
        st.markdown("### 📈 30-Day Time-Series Crime Forecasting")
        st.write("Predict future daily crime incident volumes across Pune using lag-based regression time-series forecasting with **95% Confidence Intervals**.")
        
        hist_df, forecast_df = analytics.forecast_future_crimes(df_crimes, days_to_forecast=30)
        
        if not forecast_df.empty:
            fig_fc = visualizations.create_forecast_chart(hist_df, forecast_df)
            st.plotly_chart(fig_fc, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            
            st.markdown("#### 📅 30-Day Projected Incident Surge Register")
            st.dataframe(
                forecast_df[['date', 'predicted_count', 'lower_ci', 'upper_ci']].rename(
                    columns={
                        'date': 'Forecast Date',
                        'predicted_count': 'Projected Daily Crimes',
                        'lower_ci': 'Lower 95% Bound',
                        'upper_ci': 'Upper 95% Bound'
                    }
                ).assign(
                    **{
                        'Forecast Date': lambda x: pd.to_datetime(x['Forecast Date']).dt.strftime('%Y-%m-%d'),
                        'Projected Daily Crimes': lambda x: x['Projected Daily Crimes'].map('{:.1f}'.format),
                        'Lower 95% Bound': lambda x: x['Lower 95% Bound'].map('{:.1f}'.format),
                        'Upper 95% Bound': lambda x: x['Upper 95% Bound'].map('{:.1f}'.format)
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Insufficient historical crime log timeline to generate 30-day forecast.")
            
    # Tab 3: Socio-Economic Correlations
    with tab_socio:
        st.markdown("### Socio-Economic Correlation Matrix")
        st.write("Examine statistical correlations between a district's socio-economic profiles (unemployment, poverty, income, education, density) and the total occurrences of crimes.")
        
        st.markdown("""
        > 💡 **Police Intelligence Briefing**: Socio-economic indicators provide empirical data for beat allocation. Areas with high poverty or unemployment indices show elevated property crime frequencies, supporting targeted community policing interventions.
        """)
        
        corr_df = analytics.calculate_socioeconomic_correlations(df_crimes, df_districts)
        
        if not corr_df.empty:
            col_sc1, col_sc2 = st.columns([1, 1])
            with col_sc1:
                fig_heatmap = visualizations.create_correlation_heatmap(corr_df)
                st.plotly_chart(fig_heatmap, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            with col_sc2:
                feat_opt = corr_df['feature'].tolist()
                feat_labels = {f: f.replace('_', ' ').title() for f in feat_opt}
                sel_feat = st.selectbox("Select Variable for Trendline Regression", feat_opt, format_func=lambda x: feat_labels[x], key="sel_corr_feat")
                
                fig_scatter = visualizations.create_correlation_scatter(df_crimes, df_districts, sel_feat)
                st.plotly_chart(fig_scatter, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
            # Table of exact statistical coefficients
            st.markdown("#### 📐 Statistical Correlation Coefficients (Pearson r & Spearman ρ)")
            display_corr = corr_df.copy()
            if 'feature' in display_corr.columns:
                display_corr['feature'] = display_corr['feature'].astype(str).str.replace('_', ' ').str.title()
            if 'pearson_r' in display_corr.columns:
                display_corr['pearson_r'] = display_corr['pearson_r'].map('{:+.3f}'.format)
            if 'p_value' in display_corr.columns:
                display_corr['p_value'] = display_corr['p_value'].map('{:.4f}'.format)
            if 'spearman_rho' in display_corr.columns:
                display_corr['spearman_rho'] = display_corr['spearman_rho'].map('{:+.3f}'.format)
            if 'spearman_p' in display_corr.columns:
                display_corr['spearman_p'] = display_corr['spearman_p'].map('{:.4f}'.format)

            display_corr = display_corr.rename(columns={
                'feature': 'Socio-Economic Feature',
                'pearson_r': 'Pearson Correlation (r)',
                'p_value': 'Pearson p-value',
                'spearman_rho': 'Spearman Rank (ρ)',
                'spearman_p': 'Spearman p-value'
            })
            st.dataframe(display_corr, use_container_width=True, hide_index=True)
        else:
            st.info("No correlation data available.")
            
    # Tab 4: Rolling Anomaly Detection
    with tab_anomaly:
        st.markdown("### Historical Timeline & Dual Anomaly Detection")
        st.write("Combines 14-day rolling statistical Z-score thresholding with multidimensional **Isolation Forest ML** anomaly detection on daily crime logs.")
        
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            sel_window = st.slider("Rolling Baseline Window (Days)", 7, 30, 14, key="slider_anomaly_window")
        with col_an2:
            sel_z_thresh = st.slider("Z-Score Anomaly Threshold (σ)", 1.5, 3.0, 2.0, step=0.1, key="slider_z_thresh")
            
        daily_stats, df_pivot = analytics.detect_anomalies_rolling(df_crimes, window_days=sel_window, threshold_z=sel_z_thresh)
        
        if not daily_stats.empty:
            fig_anomaly = visualizations.create_anomaly_chart(daily_stats)
            st.plotly_chart(fig_anomaly, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            
            anomalies_only = daily_stats[daily_stats['is_anomaly'] == True].sort_values(by='date', ascending=False)
            if not anomalies_only.empty:
                st.markdown("#### 🚨 Historical Crime Anomaly Surge Register")
                st.dataframe(
                    anomalies_only[['date', 'crime_count', 'rolling_mean', 'z_score', 'iso_anomaly']].rename(
                        columns={
                            'date': 'Anomaly Date',
                            'crime_count': 'Actual Incident Count',
                            'rolling_mean': f'Expected {sel_window}-Day Baseline',
                            'z_score': 'Statistical Z-Score (σ)',
                            'iso_anomaly': 'Isolation Forest ML Outlier'
                        }
                    ).assign(
                        **{
                            'Anomaly Date': lambda x: pd.to_datetime(x['Anomaly Date']).dt.strftime('%Y-%m-%d'),
                            'Statistical Z-Score (σ)': lambda x: x['Statistical Z-Score (σ)'].map('{:+.2f} σ'.format),
                            'Isolation Forest ML Outlier': lambda x: x['Isolation Forest ML Outlier'].map(lambda v: '🚨 Confirmed Outlier' if v else '⚪ Baseline')
                        }
                    ),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No historical trends to show.")

# --- Page 4: Criminal Network Analysis ---
elif selected_page == "🕸️ Criminal Network Analysis":
    st.markdown("## 🕸️ Criminal Social Network & Associate Linkage")
    st.write("Perform criminal network link analysis across gangs, accomplices, and co-arrestees. Utilize graph centrality algorithms to identify syndicate leaders and cross-group bridge figures.")
    
    # Gang Filter & Controls Header
    col_f1, col_f2 = st.columns([1.5, 2])
    with col_f1:
        gang_options = ["All Gangs"] + sorted([g for g in df_suspects['gang_affiliation'].unique() if g != "None"])
        sel_gang_net = st.selectbox("Filter Network by Syndicate / Gang", gang_options, key="sel_gang_network")
    with col_f2:
        st.markdown("<div style='padding-top: 25px; color: #9CA3AF; font-size: 0.85rem;'>💡 <b>Tip</b>: Use mouse scroll to zoom in/out of the network graph. Drag nodes or background to pan. Click on legend items to toggle specific link types (Gang Member, Accomplice, Co-arrestee, Relative).</div>", unsafe_allow_html=True)
        
    # Render Network Graph
    fig_network, centrality_metrics = visualizations.create_network_graph(df_suspects, df_connections, selected_gang=sel_gang_net)
    
    # KPI Row
    if centrality_metrics:
        cent_df = pd.DataFrame.from_dict(centrality_metrics, orient='index')
        top_hub_name = cent_df.sort_values(by='degree_centrality', ascending=False).iloc[0]['name'] if not cent_df.empty else "N/A"
        top_bridge_name = cent_df.sort_values(by='betweenness_centrality', ascending=False).iloc[0]['name'] if not cent_df.empty else "N/A"
        
        kpi_n1, kpi_n2, kpi_n3, kpi_n4 = st.columns(4)
        with kpi_n1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Network Suspects</div><div class="kpi-value">{len(cent_df)}</div></div>""", unsafe_allow_html=True)
        with kpi_n2:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Links</div><div class="kpi-value">{cent_df['degree'].sum() // 2}</div></div>""", unsafe_allow_html=True)
        with kpi_n3:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Primary Gang Hub</div><div class="kpi-value" style="font-size: 1.1rem; color: #60A5FA;">{top_hub_name}</div></div>""", unsafe_allow_html=True)
        with kpi_n4:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Top Bridge Figure</div><div class="kpi-value" style="font-size: 1.1rem; color: #F59E0B;">{top_bridge_name}</div></div>""", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

    col_net1, col_net2 = st.columns([2.2, 1])
    
    with col_net1:
        st.plotly_chart(fig_network, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
    with col_net2:
        st.markdown("### 🕸️ Key Network Influencers")
        st.write("Calculated via Degree Centrality (Gang Hubs) and Betweenness Centrality (Bridge Connectors).")
        
        if centrality_metrics:
            cent_sorted = cent_df.sort_values(by='degree_centrality', ascending=False).head(5)
            st.write("**Top Associate Hubs (Gang Leaders)**")
            st.dataframe(
                cent_sorted[['name', 'degree', 'degree_centrality']].rename(
                    columns={'name': 'Suspect Name', 'degree': 'Links', 'degree_centrality': 'Degree Centrality'}
                ).assign(**{'Degree Centrality': lambda x: x['Degree Centrality'].map('{:.3f}'.format)}),
                use_container_width=True,
                hide_index=True
            )
            
            bridge_sorted = cent_df.sort_values(by='betweenness_centrality', ascending=False).head(5)
            st.write("**Top Bridge Figures (Cross-Group Connectors)**")
            st.dataframe(
                bridge_sorted[['name', 'betweenness_centrality']].rename(
                    columns={'name': 'Suspect Name', 'betweenness_centrality': 'Bridge Score'}
                ).assign(**{'Bridge Score': lambda x: x['Bridge Score'].map('{:.3f}'.format)}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No central metrics calculated.")
            
    st.markdown("<hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)
    
    # Timelines Section
    st.markdown("### 📅 Suspect Crime History Timelines")
    st.write("Select a suspect from the database to build a complete chronological profile of their crimes.")
    
    # Filter suspects that actually have crimes associated with them in database
    conn = database.get_connection()
    c_cursor = conn.cursor()
    c_cursor.execute("SELECT DISTINCT suspect_id FROM crimes WHERE suspect_id IS NOT NULL")
    suspect_ids_with_crimes = [row[0] for row in c_cursor.fetchall()]
    conn.close()
    
    if suspect_ids_with_crimes:
        suspects_with_crimes_df = df_suspects[df_suspects['id'].isin(suspect_ids_with_crimes)].sort_values(by='name')
        
        sus_options = {row['id']: f"{row['name']} (Priors: {row['priors_count']})" for _, row in suspects_with_crimes_df.iterrows()}
        selected_sus_id = st.selectbox("Select Suspect to Track", list(sus_options.keys()), format_func=lambda x: sus_options[x])
        
        if selected_sus_id:
            s_name = df_suspects[df_suspects['id'] == selected_sus_id]['name'].iloc[0]
            
            # Create a network sub-graph view highlight
            st.markdown(f"Highlighting **{s_name}** in the social network...")
            fig_net_highlight, _ = visualizations.create_network_graph(df_suspects, df_connections, highlight_suspect_id=selected_sus_id)
            
            col_track1, col_track2 = st.columns([1, 1])
            with col_track1:
                st.plotly_chart(fig_net_highlight, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            with col_track2:
                fig_timeline = visualizations.create_offender_timeline(selected_sus_id, df_crimes, s_name)
                st.plotly_chart(fig_timeline, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
                # AI Case Narrative Briefing Generator
                s_row = df_suspects[df_suspects['id'] == selected_sus_id].iloc[0]
                if st.button(f"🤖 Generate AI Officer Briefing for {s_name}", key=f"btn_ai_brief_{selected_sus_id}"):
                    sus_crimes = df_crimes[df_crimes['suspect_id'] == selected_sus_id]
                    crime_summary = ", ".join(sus_crimes['crime_type'].unique()) if not sus_crimes.empty else "No logged crime categories"
                    
                    briefing_text = (
                        f"**CONFIDENTIAL POLICE BRIEFING — SUBJECT RECORD #{selected_sus_id}**\n\n"
                        f"• **Subject Profile**: {s_row['name']} (Age {s_row['age']}), Gang Affiliation: **{s_row['gang_affiliation']}**.\n"
                        f"• **Risk Classification**: Recidivism Risk Index of **{s_row['risk_score']:.2f}** with **{s_row['priors_count']} prior arrests**.\n"
                        f"• **Operational History**: Linked to {len(sus_crimes)} incident reports ({crime_summary}) across Pune sectors.\n"
                        f"• **Tactical Directive**: Maintain active history-sheeter surveillance, track station roll-call attendance, and monitor known gang associate links."
                    )
                    st.info(briefing_text)
    else:
        st.info("No crimes are currently linked to suspects. Go to 'Intel Entry' to link suspects to crime reports.")

# --- Page 5: Intel Entry (CRUD) ---
elif selected_page == "📝 Intel Entry (CRUD)":
    st.markdown("## Intelligence Records Entry & Management")
    st.write("Directly interface with the SQLite databases to log crime records, register suspects, and model relationships.")
    
    # Passkey protection
    if not INTEL_ENTRY_KEY:
        st.warning("⚠️ Security Policy Warning: Passkey configuration required. Please configure INTEL_ENTRY_KEY in Streamlit Secrets or config_keys.py to unlock access.")
        st.stop()
        
    entered_key = st.text_input("Enter Passkey to Access Intel Entry Forms", type="password", key="intel_entry_passkey")
    if entered_key != INTEL_ENTRY_KEY:
        if entered_key:
            st.error("Incorrect Passkey. Access Denied.")
        else:
            st.warning("Please enter the correct passkey to unlock the forms.")
        st.stop()
    
    tab_add_crime, tab_add_suspect, tab_add_rel = st.tabs([
        "⚠️ Report Crime Incident",
        "👤 Register New Suspect",
        "🔗 Model Criminal Associations"
    ])
    
    # 1. Report Crime
    with tab_add_crime:
        st.markdown("### Log a New Crime Incident")
        with st.form("add_crime_form", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                c_timestamp = st.text_input("Incident Timestamp (YYYY-MM-DD HH:MM:SS)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # Fetch districts dynamically for selectbox
                dist_choices = {row['id']: row['name'] for _, row in df_districts.iterrows()}
                c_district_id = st.selectbox("Incident Area / Location", list(dist_choices.keys()), format_func=lambda x: dist_choices[x])
                
                c_type = st.selectbox("Crime Category", crime_types_list)
                c_severity = st.selectbox("Severity Classification", severity_list)
                
            with col_c2:
                # Autofill district center coordinates with minor offset
                dist_row = df_districts[df_districts['id'] == c_district_id].iloc[0]
                c_lat = st.number_input("Latitude Coordinate", value=float(dist_row['center_lat']), format="%.6f")
                c_lon = st.number_input("Longitude Coordinate", value=float(dist_row['center_lon']), format="%.6f")
                c_status = st.selectbox("Investigation Status", ["Open", "In Investigation", "Closed"])
                
                # Suspect list dropdown
                suspect_choices = {0: "None (Unidentified)"}
                for _, row in df_suspects.sort_values(by='name').iterrows():
                    suspect_choices[row['id']] = f"{row['name']} (ID: {row['id']})"
                c_suspect_id = st.selectbox("Primary Linked Suspect", list(suspect_choices.keys()), format_func=lambda x: suspect_choices[x])
                
            submit_crime = st.form_submit_value = st.form_submit_button("Log Incident")
            
            if submit_crime:
                actual_suspect = None if c_suspect_id == 0 else int(c_suspect_id)
                new_id = database.add_crime(
                    timestamp=c_timestamp,
                    district_id=int(c_district_id),
                    crime_type=c_type,
                    severity=c_severity,
                    latitude=c_lat,
                    longitude=c_lon,
                    status=c_status,
                    suspect_id=actual_suspect
                )
                st.success(f"Incident reported successfully! Registered ID: {new_id}")
                st.cache_data.clear() # Clear streamlit cache to reload new data
                
    # 2. Register Suspect
    with tab_add_suspect:
        st.markdown("### Register New Suspect Profile")
        with st.form("add_suspect_form", clear_on_submit=True):
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                s_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                s_age = st.number_input("Age", min_value=12, max_value=100, value=25)
                
            with col_s2:
                s_gang = st.selectbox("Gang Affiliation", ["None", "Pune Local Boys", "Shivaji Nagar Syndicate", "Koregaon Park Cartel", "Hinjawadi Hackers", "D-Company Gang", "Chhota Rajan Gang"])
                s_priors = st.number_input("Prior Arrests Count", min_value=0, max_value=100, value=0)
                
            submit_suspect = st.form_submit_button("Register Suspect")
            
            if submit_suspect:
                if s_name.strip() == "":
                    st.error("Name field cannot be left blank.")
                else:
                    # Calculate baseline risk score dynamically using ML or formula
                    base_risk = float(np.clip((s_priors * 0.15) + (0.2 if s_gang != "None" else 0) + 0.1, 0.1, 0.95))
                    new_id = database.add_suspect(
                        name=s_name,
                        age=int(s_age),
                        gang=s_gang,
                        priors=int(s_priors),
                        risk_score=base_risk
                    )
                    st.success(f"Suspect profile registered! Database ID: {new_id}")
                    st.cache_data.clear() # Clear streamlit cache
                    
    # 3. Model Criminal Associations
    with tab_add_rel:
        st.markdown("### Establish Criminal Associates Connection")
        st.write("Log connections between suspects to update the global network link analysis graph in real time.")
        
        with st.form("add_connection_form", clear_on_submit=True):
            col_r1, col_r2 = st.columns(2)
            
            suspect_choices = {row['id']: f"{row['name']} (ID: {row['id']})" for _, row in df_suspects.sort_values(by='name').iterrows()}
            
            with col_r1:
                s_a = st.selectbox("Suspect Alpha", list(suspect_choices.keys()), format_func=lambda x: suspect_choices[x])
                rel_type = st.selectbox("Relation Type", ["Accomplice", "Co-arrestee", "Gang Member", "Relative"])
                
            with col_r2:
                s_b = st.selectbox("Suspect Beta", list(suspect_choices.keys()), format_func=lambda x: suspect_choices[x])
                strength = st.slider("Association Strength", min_value=1, max_value=5, value=3, help="1 is weak, 5 is extremely strong (e.g. gang leader/accomplice in major crimes).")
                
            submit_connection = st.form_submit_button("Model Association")
            
            if submit_connection:
                if s_a == s_b:
                    st.error("Cannot create association connection to self.")
                else:
                    database.add_connection(s_a=int(s_a), s_b=int(s_b), rel_type=rel_type, strength=int(strength))
                    st.success(f"Criminal link modeled successfully between Suspect {s_a} and Suspect {s_b}!")
                    st.cache_data.clear() # Clear streamlit cache

# --- Page: View Data ---
elif selected_page == "📂 View Data":
    st.markdown("## 📂 Database Records Viewer & Editor")
    st.write("Explore, search, edit, delete, and download raw tables from the Pune Crime Intelligence database.")
    
    # Passkey protection
    if not VIEW_DATA_KEY:
        st.warning("⚠️ Security Policy Warning: Passkey configuration required. Please configure VIEW_DATA_KEY in Streamlit Secrets or config_keys.py to unlock access.")
        st.stop()
        
    entered_key = st.text_input("Enter Passkey to Access View Data", type="password", key="view_data_passkey")
    if entered_key != VIEW_DATA_KEY:
        if entered_key:
            st.error("Incorrect Passkey. Access Denied.")
        else:
            st.warning("Please enter the correct passkey to unlock the database viewer.")
        st.stop()
        
    st.success("Access Granted! Showing database tables.")
    
    # Helper exports functions
    def export_excel(df, filename):
        import io
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        return towrite.getvalue()
        
    def export_pdf(df, title):
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.HexColor("#3B82F6")
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 10))
        
        # Limit to 500 rows to avoid massive page size
        preview_df = df.head(500)
        data = [list(preview_df.columns)]
        for _, row in preview_df.iterrows():
            data.append([str(val) for val in row.values])
            
        col_width = (792 - 40) / len(preview_df.columns)
        t = Table(data, colWidths=[col_width]*len(preview_df.columns))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#111827")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 7),
        ]))
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def export_image(df, title):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        # Render top 50 rows in image for readability
        preview_df = df.head(50)
        fig, ax = plt.subplots(figsize=(14, len(preview_df) * 0.3 + 1.5))
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(
            cellText=preview_df.values,
            colLabels=preview_df.columns,
            loc='center',
            cellLoc='left'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.3)
        
        for (row_idx, col_idx), cell in table.get_celld().items():
            if row_idx == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#111827')
            else:
                cell.set_facecolor('#f8fafc' if row_idx % 2 == 0 else '#ffffff')
                
        plt.title(f"{title} (Showing top {len(preview_df)} records)", fontsize=14, color='#111827', weight='bold', pad=20)
        
        import io
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # Load fresh datasets to display
    conn = database.get_connection()
    df_sus = pd.read_sql_query("SELECT * FROM suspects ORDER BY id DESC", conn)
    # Get crimes with district names
    df_cri = pd.read_sql_query("""
        SELECT c.id, c.timestamp, d.name as area_name, c.crime_type, c.severity, c.latitude, c.longitude, c.status, c.suspect_id
        FROM crimes c
        LEFT JOIN districts d ON c.district_id = d.id
        ORDER BY c.id DESC
    """, conn)
    df_con = pd.read_sql_query("SELECT suspect_a, suspect_b, relation_type, strength FROM suspect_connections", conn)
    
    # Map district IDs for dropdown edits
    df_dist_choices = pd.read_sql_query("SELECT id, name FROM districts", conn)
    conn.close()

    tab_sus, tab_cri, tab_con = st.tabs([
        "👤 Suspects Database",
        "⚠️ Incident Log",
        "🔗 Association Network"
    ])
    
    # ------------------ Tab 1: Suspects ------------------
    with tab_sus:
        st.markdown("### Suspect Registry")
        st.write("Use the table below to view, search, edit, or delete suspects. Click **Save Changes** at the bottom of the section to persist your updates to the database.")
        
        # Search Bar
        search_sus = st.text_input("🔍 Search Suspects by Name, Gang, or ID", "", key="search_suspects")
        filtered_sus = df_sus.copy()
        if search_sus:
            filtered_sus = filtered_sus[
                filtered_sus['name'].str.contains(search_sus, case=False, na=False) |
                filtered_sus['gang_affiliation'].str.contains(search_sus, case=False, na=False) |
                filtered_sus['id'].astype(str).str.contains(search_sus, case=False, na=False)
            ]
            
        # Inline editor instructions
        st.info("💡 **Tip**: Use double-click to edit any cell. Select a row and press **Delete** or **Backspace** on your keyboard to delete it. To add a new suspect, scroll to the bottom of the table and fill in the empty row. You can use standard keyboard shortcuts like **Ctrl+Z** to undo edits before saving.")
        
        # Render data editor
        edited_sus_df = st.data_editor(
            filtered_sus,
            num_rows="dynamic",
            use_container_width=True,
            key="suspects_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "risk_score": st.column_config.NumberColumn("Risk Score (0.0 - 1.0)", min_value=0.0, max_value=1.0, step=0.01),
                "age": st.column_config.NumberColumn("Age", min_value=12, max_value=100),
                "priors_count": st.column_config.NumberColumn("Priors Count", min_value=0, max_value=100)
            }
        )
        
        # Undo/Redo & Save Buttons row
        c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 5])
        with c_btn1:
            if st.button("Reset / Undo All Edits", key="reset_suspects"):
                st.rerun()
        with c_btn2:
            if st.button("Save Suspect Changes", key="save_suspects"):
                # Handle changes
                editor_state = st.session_state.get("suspects_editor", {})
                
                # Check for edits
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        # Get ID of the record in filtered dataframe
                        sus_id = int(filtered_sus.iloc[row_idx]["id"])
                        name = changes.get("name", filtered_sus.iloc[row_idx]["name"])
                        age = int(changes.get("age", filtered_sus.iloc[row_idx]["age"]))
                        gang = changes.get("gang_affiliation", filtered_sus.iloc[row_idx]["gang_affiliation"])
                        priors = int(changes.get("priors_count", filtered_sus.iloc[row_idx]["priors_count"]))
                        risk = float(changes.get("risk_score", filtered_sus.iloc[row_idx]["risk_score"]))
                        
                        database.update_suspect_details(sus_id, name, age, gang, priors, risk)
                        
                # Check for additions
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        name = row.get("name", "New Suspect")
                        age = int(row.get("age", 25))
                        gang = row.get("gang_affiliation", "None")
                        priors = int(row.get("priors_count", 0))
                        # calculate risk default
                        risk = float(np.clip((priors * 0.15) + (0.2 if gang != "None" else 0) + 0.1, 0.1, 0.95))
                        risk = float(row.get("risk_score", risk))
                        
                        database.add_suspect(name, age, gang, priors, risk)
                        
                # Check for deletions
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        sus_id = int(filtered_sus.iloc[row_idx]["id"])
                        database.delete_suspect(sus_id)
                        
                st.success("Suspect changes saved successfully!")
                st.cache_data.clear()
                st.rerun()
                
        # Download panel
        st.markdown("#### 📥 Export Suspect Data")
        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
        with exp_col1:
            st.download_button(
                "CSV Export",
                filtered_sus.to_csv(index=False).encode('utf-8'),
                "pune_suspects.csv",
                "text/csv",
                key="dl_sus_csv"
            )
        with exp_col2:
            st.download_button(
                "Excel Export",
                export_excel(filtered_sus, "pune_suspects.xlsx"),
                "pune_suspects.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_sus_excel"
            )
        with exp_col3:
            st.download_button(
                "PDF Export",
                export_pdf(filtered_sus, "Pune Suspects Database"),
                "pune_suspects.pdf",
                "application/pdf",
                key="dl_sus_pdf"
            )
        with exp_col4:
            st.download_button(
                "Table Image (PNG)",
                export_image(filtered_sus, "Pune Suspects Database"),
                "pune_suspects.png",
                "image/png",
                key="dl_sus_png"
            )

    # ------------------ Tab 2: Incident Log ------------------
    with tab_cri:
        st.markdown("### Crime Incident Logs")
        st.write("Use the table below to view, search, edit, or delete crime incidents.")
        
        # Search Bar
        search_cri = st.text_input("🔍 Search Incident Log by Category, Status, Area, or ID", "", key="search_crimes")
        filtered_cri = df_cri.copy()
        if search_cri:
            filtered_cri = filtered_cri[
                filtered_cri['crime_type'].str.contains(search_cri, case=False, na=False) |
                filtered_cri['status'].str.contains(search_cri, case=False, na=False) |
                filtered_cri['area_name'].str.contains(search_cri, case=False, na=False) |
                filtered_cri['id'].astype(str).str.contains(search_cri, case=False, na=False)
            ]
            
        st.info("💡 **Tip**: Area Name column is for viewing. When adding/modifying crimes, type the district ID matching Pune districts: 1 (Shivajinagar), 2 (Kothrud), 3 (Viman Nagar), 4 (Hinjawadi), 5 (Koregaon Park), 6 (Hadapsar), 7 (Katraj), 8 (Swargate).")
        
        # Render data editor
        edited_cri_df = st.data_editor(
            filtered_cri,
            num_rows="dynamic",
            use_container_width=True,
            key="crimes_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "latitude": st.column_config.NumberColumn("Latitude", format="%.6f"),
                "longitude": st.column_config.NumberColumn("Longitude", format="%.6f"),
                "suspect_id": st.column_config.NumberColumn("Linked Suspect ID")
            }
        )
        
        # Undo/Redo & Save Buttons row
        cc_btn1, cc_btn2, cc_btn3 = st.columns([1.5, 1.5, 5])
        with cc_btn1:
            if st.button("Reset / Undo All Edits", key="reset_crimes"):
                st.rerun()
        with cc_btn2:
            if st.button("Save Crime Changes", key="save_crimes"):
                editor_state = st.session_state.get("crimes_editor", {})
                
                # Check for edits
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        crime_id = int(filtered_cri.iloc[row_idx]["id"])
                        timestamp = changes.get("timestamp", filtered_cri.iloc[row_idx]["timestamp"])
                        
                        # Handle area renaming to district_id
                        area_name = changes.get("area_name", filtered_cri.iloc[row_idx]["area_name"])
                        matched_dist = df_dist_choices[df_dist_choices['name'] == area_name]
                        if not matched_dist.empty:
                            district_id = int(matched_dist.iloc[0]['id'])
                        else:
                            try:
                                district_id = int(area_name)
                            except ValueError:
                                district_id = 1
                                
                        crime_type = changes.get("crime_type", filtered_cri.iloc[row_idx]["crime_type"])
                        severity = changes.get("severity", filtered_cri.iloc[row_idx]["severity"])
                        latitude = float(changes.get("latitude", filtered_cri.iloc[row_idx]["latitude"]))
                        longitude = float(changes.get("longitude", filtered_cri.iloc[row_idx]["longitude"]))
                        status = changes.get("status", filtered_cri.iloc[row_idx]["status"])
                        
                        suspect_id_val = changes.get("suspect_id", filtered_cri.iloc[row_idx]["suspect_id"])
                        suspect_id = None if pd.isna(suspect_id_val) or suspect_id_val == "" or suspect_id_val is None else int(suspect_id_val)
                        
                        database.update_crime_details(crime_id, timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
                        
                # Check for additions
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        timestamp = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
                        area_name = row.get("area_name", "Shivajinagar")
                        matched_dist = df_dist_choices[df_dist_choices['name'] == area_name]
                        if not matched_dist.empty:
                            district_id = int(matched_dist.iloc[0]['id'])
                        else:
                            try:
                                district_id = int(area_name)
                            except ValueError:
                                district_id = 1
                                
                        crime_type = row.get("crime_type", "Theft")
                        severity = row.get("severity", "Low")
                        latitude = float(row.get("latitude", 18.5204))
                        longitude = float(row.get("longitude", 73.8567))
                        status = row.get("status", "Open")
                        
                        suspect_id_val = row.get("suspect_id")
                        suspect_id = None if pd.isna(suspect_id_val) or suspect_id_val == "" or suspect_id_val is None else int(suspect_id_val)
                        
                        database.add_crime(timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
                        
                # Check for deletions
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        crime_id = int(filtered_cri.iloc[row_idx]["id"])
                        database.delete_crime(crime_id)
                        
                st.success("Crime incident changes saved successfully!")
                st.cache_data.clear()
                st.rerun()
                
        # Download panel
        st.markdown("#### 📥 Export Incident Data")
        exp_cri_col1, exp_cri_col2, exp_cri_col3, exp_cri_col4 = st.columns(4)
        with exp_cri_col1:
            st.download_button(
                "CSV Export",
                filtered_cri.to_csv(index=False).encode('utf-8'),
                "pune_crimes.csv",
                "text/csv",
                key="dl_cri_csv"
            )
        with exp_cri_col2:
            st.download_button(
                "Excel Export",
                export_excel(filtered_cri, "pune_crimes.xlsx"),
                "pune_crimes.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_cri_excel"
            )
        with exp_cri_col3:
            st.download_button(
                "PDF Export",
                export_pdf(filtered_cri, "Pune Crime Incident Logs"),
                "pune_crimes.pdf",
                "application/pdf",
                key="dl_cri_pdf"
            )
        with exp_cri_col4:
            st.download_button(
                "Table Image (PNG)",
                export_image(filtered_cri, "Pune Crime Incident Logs"),
                "pune_crimes.png",
                "image/png",
                key="dl_cri_png"
            )

    # ------------------ Tab 3: Association Network ------------------
    with tab_con:
        st.markdown("### Suspect Connections Network")
        st.write("Use the table below to view, search, edit, or delete criminal associations.")
        
        # Search Bar
        search_con = st.text_input("🔍 Search Connections by Suspect ID or Relation Type", "", key="search_connections")
        filtered_con = df_con.copy()
        if search_con:
            filtered_con = filtered_con[
                filtered_con['relation_type'].str.contains(search_con, case=False, na=False) |
                filtered_con['suspect_a'].astype(str).str.contains(search_con, case=False, na=False) |
                filtered_con['suspect_b'].astype(str).str.contains(search_con, case=False, na=False)
            ]
            
        st.info("💡 **Tip**: Relationship Strength ranges from 1 (weak) to 5 (extremely strong).")
        
        # Render data editor
        edited_con_df = st.data_editor(
            filtered_con,
            num_rows="dynamic",
            use_container_width=True,
            key="connections_editor",
            column_config={
                "suspect_a": st.column_config.NumberColumn("Suspect Alpha ID"),
                "suspect_b": st.column_config.NumberColumn("Suspect Beta ID"),
                "strength": st.column_config.NumberColumn("Strength (1 - 5)", min_value=1, max_value=5)
            }
        )
        
        # Undo/Redo & Save Buttons row
        con_btn1, con_btn2, con_btn3 = st.columns([1.5, 1.5, 5])
        with con_btn1:
            if st.button("Reset / Undo All Edits", key="reset_connections"):
                st.rerun()
        with con_btn2:
            if st.button("Save Connection Changes", key="save_connections"):
                editor_state = st.session_state.get("connections_editor", {})
                
                # Check for edits
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        s_a = int(filtered_con.iloc[row_idx]["suspect_a"])
                        s_b = int(filtered_con.iloc[row_idx]["suspect_b"])
                        rel_type = changes.get("relation_type", filtered_con.iloc[row_idx]["relation_type"])
                        strength = int(changes.get("strength", filtered_con.iloc[row_idx]["strength"]))
                        
                        database.update_connection_details(s_a, s_b, rel_type, strength)
                        
                # Check for additions
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        s_a_val = row.get("suspect_a")
                        s_b_val = row.get("suspect_b")
                        if s_a_val is not None and s_b_val is not None:
                            s_a = int(s_a_val)
                            s_b = int(s_b_val)
                            rel_type = row.get("relation_type", "Accomplice")
                            strength = int(row.get("strength", 3))
                            
                            database.add_connection(s_a, s_b, rel_type, strength)
                            
                # Check for deletions
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        s_a = int(filtered_con.iloc[row_idx]["suspect_a"])
                        s_b = int(filtered_con.iloc[row_idx]["suspect_b"])
                        database.delete_connection(s_a, s_b)
                        
                st.success("Criminal network connection changes saved successfully!")
                st.cache_data.clear()
                st.rerun()
                
        # Download panel
        st.markdown("#### 📥 Export Connection Data")
        exp_con_col1, exp_con_col2, exp_con_col3, exp_con_col4 = st.columns(4)
        with exp_con_col1:
            st.download_button(
                "CSV Export",
                filtered_con.to_csv(index=False).encode('utf-8'),
                "pune_connections.csv",
                "text/csv",
                key="dl_con_csv"
            )
        with exp_con_col2:
            st.download_button(
                "Excel Export",
                export_excel(filtered_con, "pune_connections.xlsx"),
                "pune_connections.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_con_excel"
            )
        with exp_con_col3:
            st.download_button(
                "PDF Export",
                export_pdf(filtered_con, "Suspect Associates Network"),
                "pune_connections.pdf",
                "application/pdf",
                key="dl_con_pdf"
            )
        with exp_con_col4:
            st.download_button(
                "Table Image (PNG)",
                export_image(filtered_con, "Suspect Associates Network"),
                "pune_connections.png",
                "image/png",
                key="dl_con_png"
            )

# --- Page 6: AI Intel Chatbot ---
elif selected_page == "💬 AI Intel Chatbot":
    st.markdown("## 💬 AI Intelligence Chatbot & Natural Language SQL Assistant")
    st.write("Ask natural language queries about Pune crime records, suspect registries, gang networks, and district socio-economics. The AI assistant generates verified read-only SQL queries and presents structured intelligence briefings.")

    api_key = st.session_state.get("llm_api_key", "")
    provider = st.session_state.get("llm_provider", "Gemini")
    model_name = st.session_state.get("llm_model", "gemini-1.5-flash")
    
    # Status bar header
    col_st1, col_st2 = st.columns([3, 1])
    with col_st1:
        if api_key:
            st.markdown(f"**Connection Status**: 🟢 <span style='color: #10B981; font-weight: 700;'>Online</span> &nbsp;|&nbsp; **Provider**: `{provider}` &nbsp;|&nbsp; **Model**: `{model_name}`", unsafe_allow_html=True)
        else:
            st.markdown("**Connection Status**: 🔴 <span style='color: #EF4444; font-weight: 700;'>API Key Required</span>", unsafe_allow_html=True)
    with col_st2:
        if st.button("🗑️ Clear Chat History", key="btn_clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Collapsible API Settings Expander
    with st.expander("⚙️ API Provider & Key Configuration", expanded=not bool(api_key)):
        config_col1, config_col2, config_col3 = st.columns([1, 1.2, 1.2])
        with config_col1:
            provider_list = ["Gemini", "OpenAI", "OpenRouter", "Groq", "NVIDIA NIM"]
            provider_idx = provider_list.index(provider) if provider in provider_list else 0
            new_provider = st.selectbox("API Provider", provider_list, index=provider_idx, key="cb_provider_sel")
        with config_col2:
            presets = {
                "Gemini": ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "Custom Model"],
                "OpenAI": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "Custom Model"],
                "OpenRouter": ["meta-llama/llama-3-8b-instruct:free", "google/gemma-2-9b-it:free", "mistralai/mistral-7b-instruct:free", "openrouter/auto", "Custom Model"],
                "Groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "Custom Model"],
                "NVIDIA NIM": ["meta/llama3-70b-instruct", "nvidia/nemotron-4-340b-instruct", "nvidia/llama-3.1-nemotron-70b-instruct", "Custom Model"]
            }
            options = presets.get(new_provider, ["Custom Model"])
            default_idx = options.index(model_name) if model_name in options else (len(options) - 1 if "Custom Model" in options else 0)
            selected_model_option = st.selectbox("Model Version", options, index=default_idx, key="cb_model_option")
            model_name_input = st.text_input("Custom Model Name/ID", value=model_name if model_name not in options else "", key="cb_custom_model_txt") if selected_model_option == "Custom Model" else selected_model_option
                
        with config_col3:
            api_key_input = st.text_input("API Key", type="password", value=api_key, placeholder="Paste your API Key here", key="cb_api_key_input")
            
        btn_c1, btn_c2, _ = st.columns([1, 1, 3])
        with btn_c1:
            if st.button("Save Credentials", key="btn_save_creds"):
                st.session_state["llm_api_key"] = api_key_input
                st.session_state["llm_provider"] = new_provider
                st.session_state["llm_model"] = model_name_input
                st.success("API credentials saved!")
                st.rerun()
        with btn_c2:
            if st.button("Clear Credentials", key="btn_clear_creds"):
                st.session_state["llm_api_key"] = ""
                st.session_state["llm_provider"] = "Gemini"
                st.session_state["llm_model"] = "gemini-1.5-flash"
                st.success("Credentials cleared!")
                st.rerun()

    st.markdown("<hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)

    if not api_key:
        st.info("💡 **API Key Required**: Please expand the settings above and save your Gemini or OpenAI API Key to start chatting with the intelligence database.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Quick Prompt Chips
        st.markdown("##### 💡 Suggested Intelligence Queries:")
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        clicked_prompt = None
        with chip_col1:
            if st.button("🔍 Top 5 High-Risk Suspects", key="chip_top_suspects"):
                clicked_prompt = "List top 5 highest risk repeat suspects in Pune with their gang affiliation."
        with chip_col2:
            if st.button("📍 Crimes in Kothrud", key="chip_kothrud_crimes"):
                clicked_prompt = "How many crimes were logged in Kothrud district and what are their severity levels?"
        with chip_col3:
            if st.button("🚨 Open High Severity Cases", key="chip_open_cases"):
                clicked_prompt = "List all open crimes with High severity level across Pune."
        with chip_col4:
            if st.button("👥 Pune Local Boys Gang", key="chip_gang_members"):
                clicked_prompt = "Who are all the suspects affiliated with Pune Local Boys gang?"

        st.markdown("<br>", unsafe_allow_html=True)

        # Display Chat History
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sql_query" in message and message["sql_query"]:
                    with st.expander("🔍 Executed SQL Query"):
                        st.code(message["sql_query"], language="sql")
                if "query_df_json" in message and message["query_df_json"]:
                    with st.expander("📊 Queried Database Records"):
                        try:
                            df_rec = pd.read_json(message["query_df_json"])
                            st.dataframe(df_rec, use_container_width=True, hide_index=True)
                        except Exception:
                            pass
                if "sql_error" in message and message["sql_error"]:
                    st.error(f"SQL Error: {message['sql_error']}")

        # Input logic
        chat_user_input = st.chat_input("Ask a question about Pune crime database...")
        prompt_to_process = clicked_prompt if clicked_prompt else chat_user_input

        if prompt_to_process:
            with st.chat_message("user"):
                st.markdown(prompt_to_process)
            
            st.session_state.messages.append({"role": "user", "content": prompt_to_process})
            
            with st.chat_message("assistant"):
                status_placeholder = st.status("🤖 Analyzing question & writing SQL query...", expanded=True)
                
                # Fetch live real-time system clock
                now_dt = datetime.now()
                live_datetime_str = now_dt.strftime("%A, %d %B %Y, %I:%M:%S %p IST")
                live_date_iso = now_dt.strftime("%Y-%m-%d")
                
                sql_system = f"""You are an expert SQL assistant for a Crime Analytics platform in Pune, Maharashtra.
CURRENT REAL-TIME SYSTEM DATE: {live_date_iso} ({live_datetime_str}).
The database is SQLite. The schema has 4 tables:
1. districts (id, name, unemployment_rate, poverty_index, median_income, education_index, population_density, center_lat, center_lon)
2. suspects (id, name, age, gang_affiliation, priors_count, risk_score)
3. crimes (id, timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
4. suspect_connections (suspect_a, suspect_b, relation_type, strength)

Your task is to translate the user's natural language question into a single valid SQLite SELECT query.
Return ONLY the SQL query inside a markdown code block starting with ```sql and ending with ```.
Do not write any explanation or intro/outro. Only SELECT queries are permitted.

Examples:
Question: "How many crimes are there in Kothrud?"
Response:
```sql
SELECT COUNT(*) as total_crimes FROM crimes c JOIN districts d ON c.district_id = d.id WHERE d.name = 'Kothrud';
```

Question: "Who are the top 5 highest risk suspects?"
Response:
```sql
SELECT name, gang_affiliation, risk_score, priors_count FROM suspects ORDER BY risk_score DESC LIMIT 5;
```

Question: "List all crimes committed by Rahul Pawar."
Response:
```sql
SELECT c.crime_type, c.severity, c.timestamp, d.name as district, c.status FROM crimes c JOIN suspects s ON c.suspect_id = s.id JOIN districts d ON c.district_id = d.id WHERE s.name = 'Rahul Pawar';
```

If the question is a greeting, time/date query, general conversational message, or cannot be answered by querying the database, respond with exactly:
NO_SQL
"""
                try:
                    response_text = ""
                    extra_headers = {}
                    if provider == "OpenRouter":
                        extra_headers = {
                            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                            "X-Title": "Antigravity Crime Command Center"
                        }
                        
                    if provider == "Gemini":
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(model_name, system_instruction=sql_system)
                        response_text = model.generate_content(prompt_to_process).text
                    else:
                        from openai import OpenAI
                        base_urls = {
                            "OpenAI": None,
                            "OpenRouter": "https://openrouter.ai/api/v1",
                            "Groq": "https://api.groq.com/openai/v1",
                            "NVIDIA NIM": "https://integrate.api.nvidia.com/v1"
                        }
                        client = OpenAI(api_key=api_key, base_url=base_urls.get(provider))
                        resp = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": sql_system},
                                {"role": "user", "content": prompt_to_process}
                            ],
                            temperature=0.0,
                            extra_headers=extra_headers
                        )
                        response_text = resp.choices[0].message.content

                    response_text = response_text.strip()
                    sql_query = None
                    
                    if "NO_SQL" not in response_text and "```sql" in response_text:
                        start = response_text.find("```sql") + 6
                        end = response_text.find("```", start)
                        sql_query = response_text[start:end].strip()
                    elif "NO_SQL" not in response_text and "SELECT" in response_text.upper():
                        sql_query = response_text

                    sql_error = None
                    query_df_json = None
                    df_result = None
                    
                    # Read-only enforcement check
                    if sql_query:
                        cleaned_sql = sql_query.upper().strip()
                        forbidden_words = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "REPLACE"]
                        if any(w in cleaned_sql for w in forbidden_words) or not (cleaned_sql.startswith("SELECT") or cleaned_sql.startswith("WITH")):
                            sql_error = "Security Policy Error: Non-read-only query blocked."
                            sql_query = None
                            status_placeholder.update(label="❌ Security Policy Error: Non-read-only query blocked.", state="error")
                        else:
                            status_placeholder.update(label="🔍 Executing read-only query on SQLite...", state="running")
                            try:
                                conn = database.get_connection()
                                df_result = pd.read_sql_query(sql_query, conn)
                                conn.close()
                                query_df_json = df_result.to_json(orient="records")
                                status_placeholder.update(label=f"✅ Query complete. Found {len(df_result)} records.", state="complete")
                            except Exception as e:
                                sql_error = str(e)
                                status_placeholder.update(label="❌ SQLite Execution Failed.", state="error")
                    else:
                        status_placeholder.update(label="🤖 Answer generated directly.", state="complete")

                    # Formulate final response
                    status_placeholder2 = st.empty()
                    status_placeholder2.info("📝 Formulating response briefing...")
                    
                    explain_system = f"""You are the AI Intelligence Briefing Officer for Pune Police Command Center.
CURRENT REAL-TIME SYSTEM CLOCK: {live_datetime_str} (Date: {live_date_iso}).
IMPORTANT INSTRUCTION ON TIME/DATE: You HAVE direct access to the live system clock ({live_datetime_str}). If the user asks for today's date, current time, or live system status, state the exact date and time immediately and accurately. NEVER say "I do not have access to real-time system clocks".

Interpret database results clearly and professionally for police commanders.
Keep responses concise, factual, and formatted with clean Markdown bullet points. Refer to Pune, Maharashtra context.
"""
                    prompt = f"User Question: {prompt_to_process}\n\n"
                    if sql_query:
                        prompt += f"Executed SQL Query:\n{sql_query}\n\n"
                        if sql_error:
                            prompt += f"SQL Error:\n{sql_error}\n\n"
                        else:
                            prompt += f"Raw DB Results:\n{query_df_json}\n\n"
                    else:
                        prompt += "(No SQL query was run for this request.)\n\n"
                    
                    final_answer = ""
                    if provider == "Gemini":
                        model2 = genai.GenerativeModel(model_name, system_instruction=explain_system)
                        final_answer = model2.generate_content(prompt).text
                    else:
                        resp = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": explain_system},
                                {"role": "user", "content": prompt}
                            ],
                            extra_headers=extra_headers
                        )
                        final_answer = resp.choices[0].message.content
                    
                    status_placeholder2.empty()
                    st.markdown(final_answer)
                    
                    if sql_query:
                        with st.expander("🔍 Executed SQL Query"):
                            st.code(sql_query, language="sql")
                    if df_result is not None and not df_result.empty:
                        with st.expander("📊 Queried Database Records"):
                            st.dataframe(df_result, use_container_width=True, hide_index=True)
                    if sql_error:
                        st.error(f"SQL Error: {sql_error}")
                        
                    msg_obj = {"role": "assistant", "content": final_answer}
                    if sql_query:
                        msg_obj["sql_query"] = sql_query
                    if query_df_json:
                        msg_obj["query_df_json"] = query_df_json
                    if sql_error:
                        msg_obj["sql_error"] = sql_error
                        
                    st.session_state.messages.append(msg_obj)
                    st.rerun()
                    
                except Exception as ex:
                    status_placeholder.update(label="❌ Failed to connect to API or parse response.", state="error")
                    st.error(f"Error: {ex}")
                    st.info("Please make sure your API key is valid and you have an active internet connection.")

# --- Page: Live Crime News & OSINT Feed ---
elif selected_page == "📰 Crime News":
    st.markdown("## 📰 Live OSINT Crime News & Intelligence Feed")
    st.write("Real-time Open-Source Intelligence (OSINT) crime news feed powered by **NewsAPI**. Search live crime headlines, monitor breaking operational developments, and chat with AI to summarize news reports.")
    
    DEFAULT_NEWS_API_KEY = "a2a5fc4ec79447288f2589520a64c8e5"
    
    # Expander for NewsAPI Credentials
    with st.expander("⚙️ NewsAPI Key & Feed Settings", expanded=False):
        user_news_key = st.text_input("NewsAPI Key", value=st.session_state.get("news_api_key", DEFAULT_NEWS_API_KEY), type="password", key="txt_news_api_key_input")
        if st.button("Save NewsAPI Key", key="btn_save_news_key"):
            st.session_state["news_api_key"] = user_news_key
            st.success("NewsAPI Key updated successfully!")
            st.rerun()
            
    active_news_key = st.session_state.get("news_api_key", DEFAULT_NEWS_API_KEY)
    
    # Quick Search Chips
    st.markdown("##### 🔍 Quick News Search Filters:")
    n_col1, n_col2, n_col3, n_col4, n_col5 = st.columns(5)
    
    selected_query = None
    with n_col1:
        if st.button("📍 Pune Crime News", key="chip_news_pune"):
            selected_query = "Pune crime"
    with n_col2:
        if st.button("🚨 Maharashtra Police", key="chip_news_mh"):
            selected_query = "Maharashtra police crime"
    with n_col3:
        if st.button("💻 India Cybercrime", key="chip_news_cyber"):
            selected_query = "India cybercrime fraud"
    with n_col4:
        if st.button("💊 Narcotics Seizures", key="chip_news_narcotics"):
            selected_query = "Pune narcotics drugs arrest"
    with n_col5:
        if st.button("⚖️ Court & Legal News", key="chip_news_legal"):
            selected_query = "Pune police court arrest"

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Search Query Input
    search_input = st.text_input("Enter News Search Topic or Location", value="Pune crime", placeholder="e.g. Pune crime, Hinjawadi fraud, Maharashtra police...", key="txt_news_search_query")
    query_to_run = selected_query if selected_query else search_input
    
    # NewsAPI Fetcher Function
    @st.cache_data(ttl=300, show_spinner=False)
    def fetch_live_news_data(query_str, api_key_str):
        import requests
        import urllib.parse
        encoded_q = urllib.parse.quote(query_str)
        url = f"https://newsapi.org/v2/everything?q={encoded_q}&sortBy=publishedAt&language=en&pageSize=20&apiKey={api_key_str}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    return data.get("articles", []), None
                else:
                    return [], data.get("message", "NewsAPI request failed.")
            else:
                return [], f"HTTP Error {resp.status_code}: Unable to reach NewsAPI."
        except Exception as ex:
            return [], str(ex)

    with st.spinner(f"📡 Fetching live crime news for '{query_to_run}' via NewsAPI..."):
        articles, news_err = fetch_live_news_data(query_to_run, active_news_key)
        
    tab_news_feed, tab_news_chat = st.tabs([
        f"📰 Live News Feed ({len(articles)} Articles)",
        "🤖 Ask AI News Analyst"
    ])
    
    # Tab 1: Live News Feed
    with tab_news_feed:
        if news_err:
            st.error(f"⚠️ NewsAPI Fetch Error: {news_err}")
            st.info("Please make sure your NewsAPI key is valid and active.")
        elif not articles:
            st.warning(f"No news articles found for query: '{query_to_run}'. Try adjusting your search term.")
        else:
            st.caption(f"Showing **{len(articles)}** real-time news articles sorted by latest publication timestamp.")
            
            # Display Articles in 2-Column Grid
            for i in range(0, len(articles), 2):
                col_art1, col_art2 = st.columns(2)
                
                # Column 1 Article
                with col_art1:
                    art = articles[i]
                    source_name = art.get("source", {}).get("name", "News Source")
                    pub_time = art.get("publishedAt", "")[:10]
                    title = art.get("title", "No Title")
                    desc = art.get("description") or art.get("content") or "No description summary available."
                    url = art.get("url", "#")
                    img_url = art.get("urlToImage")
                    
                    st.markdown(f"""
                    <div style="background-color: rgba(17, 24, 39, 0.7); border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 12px; padding: 18px; margin-bottom: 20px; height: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); padding: 3px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">{source_name}</span>
                            <span style="color: #9ca3af; font-size: 0.8rem;">📅 {pub_time}</span>
                        </div>
                        <h4 style="margin: 8px 0; font-size: 1.05rem; line-height: 1.3;"><a href="{url}" target="_blank" style="color: #60a5fa; text-decoration: none;">{title}</a></h4>
                        <p style="color: #d1d5db; font-size: 0.85rem; line-height: 1.4; margin-bottom: 12px;">{desc[:220]}...</p>
                        <a href="{url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600;">🔗 Read Full Article</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Column 2 Article (if exists)
                if i + 1 < len(articles):
                    with col_art2:
                        art = articles[i + 1]
                        source_name = art.get("source", {}).get("name", "News Source")
                        pub_time = art.get("publishedAt", "")[:10]
                        title = art.get("title", "No Title")
                        desc = art.get("description") or art.get("content") or "No description summary available."
                        url = art.get("url", "#")
                        
                        st.markdown(f"""
                        <div style="background-color: rgba(17, 24, 39, 0.7); border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 12px; padding: 18px; margin-bottom: 20px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); padding: 3px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">{source_name}</span>
                                <span style="color: #9ca3af; font-size: 0.8rem;">📅 {pub_time}</span>
                            </div>
                            <h4 style="margin: 8px 0; font-size: 1.05rem; line-height: 1.3;"><a href="{url}" target="_blank" style="color: #60a5fa; text-decoration: none;">{title}</a></h4>
                            <p style="color: #d1d5db; font-size: 0.85rem; line-height: 1.4; margin-bottom: 12px;">{desc[:220]}...</p>
                            <a href="{url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600;">🔗 Read Full Article</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
    # Tab 2: Ask AI News Analyst
    with tab_news_chat:
        st.markdown("### 🤖 Live AI Crime News Intelligence Analyst")
        st.write("Ask any question about today's crime headlines or real-time news reports. The AI cross-references the live fetched NewsAPI articles and provides an executive intelligence briefing.")
        
        api_key = st.session_state.get("llm_api_key", "")
        provider = st.session_state.get("llm_provider", "Gemini")
        model_name = st.session_state.get("llm_model", "gemini-1.5-flash")
        
        if not api_key:
            st.info("💡 **LLM API Key Required**: Please configure and save your API Key in the **💬 AI Intel Chatbot** tab above to interact with the AI News Analyst.")
            
        if "news_messages" not in st.session_state:
            st.session_state.news_messages = []
            
        # Suggested Question Chips
        st.markdown("##### 💡 Suggested News Queries:")
        nq_col1, nq_col2, nq_col3 = st.columns(3)
        clicked_news_q = None
        with nq_col1:
            if st.button("📰 What are today's top crime news in Pune?", key="chip_nq_top_pune"):
                clicked_news_q = "What are today's top crime headlines and news reports in Pune?"
        with nq_col2:
            if st.button("💻 Summarize latest cybercrime & fraud news", key="chip_nq_cyber"):
                clicked_news_q = "Summarize the latest cybercrime and financial fraud reports from the news."
        with nq_col3:
            if st.button("🚨 List recent police arrests & seizures", key="chip_nq_arrests"):
                clicked_news_q = "List key recent police arrests, narcotics seizures, and major investigations from the news feed."
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display News Chat History
        for nmsg in st.session_state.news_messages:
            with st.chat_message(nmsg["role"]):
                st.markdown(nmsg["content"])
                
        news_user_input = st.chat_input("Ask a question about the live crime news feed...")
        news_prompt = clicked_news_q if clicked_news_q else news_user_input
        
        if news_prompt:
            if not api_key:
                st.warning("Please save your API Key in the '💬 AI Intel Chatbot' tab first.")
            else:
                with st.chat_message("user"):
                    st.markdown(news_prompt)
                st.session_state.news_messages.append({"role": "user", "content": news_prompt})
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Analyzing real-time NewsAPI articles and writing OSINT briefing..."):
                        # Construct article context
                        art_snippets = []
                        for idx, a in enumerate(articles[:12]):
                            art_snippets.append(f"[{idx+1}] Source: {a.get('source',{}).get('name')}\nTitle: {a.get('title')}\nDate: {a.get('publishedAt', '')[:10]}\nSnippet: {a.get('description')}\nURL: {a.get('url')}")
                        context_str = "\n\n".join(art_snippets) if art_snippets else "No live articles currently fetched."
                        
                        now_dt = datetime.now()
                        live_dt_str = now_dt.strftime("%A, %d %B %Y, %I:%M:%S %p IST")
                        
                        news_system_prompt = f"""You are the OSINT Crime News Intelligence Analyst for Pune Police Command Center.
CURRENT REAL-TIME SYSTEM DATETIME: {live_dt_str}.

You have access to real-time live news articles fetched via NewsAPI for query '{query_to_run}'.

LIVE FETCHED ARTICLES CONTEXT:
{context_str}

INSTRUCTIONS:
1. Answer the user's question accurately using the live news articles provided above.
2. If articles contain information relevant to the question, synthesize them into a clear, professional police briefing with bullet points and cite the news source.
3. If the user asks for "today's crime" or "latest news", summarize the top articles from the context above. State clearly that this information is live open-source news (OSINT).
4. Maintain an authoritative, factual police intelligence briefing tone.
"""
                        ai_answer = ""
                        try:
                            if provider == "Gemini":
                                import google.generativeai as genai
                                genai.configure(api_key=api_key)
                                m_news = genai.GenerativeModel(model_name, system_instruction=news_system_prompt)
                                ai_answer = m_news.generate_content(news_prompt).text
                            else:
                                from openai import OpenAI
                                base_urls = {
                                    "OpenAI": None,
                                    "OpenRouter": "https://openrouter.ai/api/v1",
                                    "Groq": "https://api.groq.com/openai/v1",
                                    "NVIDIA NIM": "https://integrate.api.nvidia.com/v1"
                                }
                                client = OpenAI(api_key=api_key, base_url=base_urls.get(provider))
                                extra_headers = {}
                                if provider == "OpenRouter":
                                    extra_headers = {
                                        "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                                        "X-Title": "Antigravity Crime Command Center"
                                    }
                                resp = client.chat.completions.create(
                                    model=model_name,
                                    messages=[
                                        {"role": "system", "content": news_system_prompt},
                                        {"role": "user", "content": news_prompt}
                                    ],
                                    extra_headers=extra_headers
                                )
                                ai_answer = resp.choices[0].message.content
                        except Exception as ex_news:
                            ai_answer = f"⚠️ Could not generate AI News Briefing: {ex_news}\n\nPlease verify your LLM API Key settings in the AI Intel Chatbot configuration panel."
                            
                        st.markdown(ai_answer)
                        st.session_state.news_messages.append({"role": "assistant", "content": ai_answer})
                        st.rerun()
                    st.rerun()

# --- Global Page End Footer ---
st.markdown("<br><hr style='border-top: 1px solid rgba(75, 85, 99, 0.3); margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 15px 0 10px 0; color: #9ca3af; font-size: 0.9rem;">
    <span>Made by </span>
    <a href="https://github.com/AviBhosale01" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 700; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 5px;">
        Avii
        <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: middle; fill: #60a5fa;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
    </a>
</div>
""", unsafe_allow_html=True)

# --- Floating 3D Police Assistant Widget (Bottom-Right Corner) ---
police_icon_path = os.path.join(os.path.dirname(__file__), "assets", "police-3d-icon.png")
police_icon_b64 = ""
if os.path.exists(police_icon_path):
    with open(police_icon_path, "rb") as img_f:
        police_icon_b64 = base64.b64encode(img_f.read()).decode("utf-8")

if police_icon_b64 and selected_page != "💬 AI Intel Chatbot":
    st.markdown(f"""
    <style>
    div[data-testid="stButton"]:has(button[key="btn_floating_ai_assistant"]),
    div:has(> button[key="btn_floating_ai_assistant"]),
    div[data-testid="stButton"]:has(button[aria-label="Open AI Intel Assistant Chatbot"]) {{
        position: fixed !important;
        bottom: 28px !important;
        right: 28px !important;
        z-index: 9999999 !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 68px !important;
        height: 68px !important;
    }}
    button[aria-label="Open AI Intel Assistant Chatbot"],
    button[key="btn_floating_ai_assistant"] {{
        position: fixed !important;
        bottom: 28px !important;
        right: 28px !important;
        z-index: 9999999 !important;
        width: 68px !important;
        height: 68px !important;
        min-width: 68px !important;
        min-height: 68px !important;
        border-radius: 50% !important;
        border: 2.5px solid rgba(96, 165, 250, 0.9) !important;
        background: radial-gradient(circle at 35% 35%, #1e40af, #0f172a) !important;
        background-image: url('data:image/png;base64,{police_icon_b64}') !important;
        background-size: 48px 48px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        box-shadow: 0 8px 30px rgba(37, 99, 235, 0.6), 0 0 20px rgba(59, 130, 246, 0.5) !important;
        cursor: pointer !important;
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease, border-color 0.25s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
    }}
    button[aria-label="Open AI Intel Assistant Chatbot"]:hover,
    button[key="btn_floating_ai_assistant"]:hover {{
        transform: scale(1.14) translateY(-4px) !important;
        border-color: #93c5fd !important;
        box-shadow: 0 14px 40px rgba(37, 99, 235, 0.9), 0 0 30px rgba(96, 165, 250, 0.8) !important;
    }}
    button[aria-label="Open AI Intel Assistant Chatbot"] p,
    button[key="btn_floating_ai_assistant"] p {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    if st.button(" ", key="btn_floating_ai_assistant", help="Open AI Intel Assistant Chatbot"):
        st.session_state["requested_page"] = "💬 AI Intel Chatbot"
        st.rerun()
