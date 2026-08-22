"""
Sidebar Navigation & Filter Controls Component
"""
import streamlit as st
import random
from datetime import datetime, timedelta

def render_sidebar(districts_raw):
    """
    Render the sidebar navigation, dataset filters, PCR patrol feed simulator, and author footer.
    """
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 15px 0;">
        <h3 style="margin: 0; color: #60a5fa;">INTELLIGENCE SUITE</h3>
        <hr style="border-top: 1px solid #1f2937; margin: 10px 0;">
    </div>
    """, unsafe_allow_html=True)

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

    # Programmatic query param navigation
    if hasattr(st, "query_params") and "page" in st.query_params:
        qp = str(st.query_params.get("page", "")).lower()
        if qp in ["chatbot", "ai_chatbot", "ai_intel_chatbot"]:
            st.session_state["nav_radio"] = "💬 AI Intel Chatbot"
            try:
                st.query_params.clear()
            except Exception:
                pass

    if "requested_page" in st.session_state and st.session_state["requested_page"]:
        req_p = st.session_state.pop("requested_page")
        if req_p in nav_options:
            st.session_state["nav_radio"] = req_p

    if "nav_radio" not in st.session_state:
        st.session_state["nav_radio"] = "📊 Command Dashboard"

    selected_page = st.sidebar.radio("Navigation", nav_options, key="nav_radio")

    st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 15px 0;'>", unsafe_allow_html=True)
    st.sidebar.subheader("Filter Workspace")

    # District Filter
    district_names = sorted(districts_raw['name'].tolist())
    selected_districts = st.sidebar.multiselect("Areas / Locations", district_names, default=[])

    # Crime Type Filter
    crime_types_list = ["Theft", "Burglary", "Assault", "Narcotics", "Fraud", "Cybercrime", "Homicide"]
    selected_crime_types = st.sidebar.multiselect("Crime Types", crime_types_list, default=[])

    # Severity Filter
    severity_list = ["Low", "Medium", "High"]
    selected_severities = st.sidebar.multiselect("Severities", severity_list, default=[])

    # Date Range Filter
    start_date_input = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date_input = st.sidebar.date_input("End Date", datetime.now())

    # Build filter dictionary
    filter_dict = {}
    if selected_districts:
        d_ids = districts_raw[districts_raw['name'].isin(selected_districts)]['id'].tolist()
        filter_dict["district_ids"] = d_ids
    if selected_crime_types:
        filter_dict["crime_types"] = selected_crime_types
    if selected_severities:
        filter_dict["severities"] = selected_severities

    filter_dict["start_date"] = start_date_input.strftime("%Y-%m-%d 00:00:00")
    filter_dict["end_date"] = end_date_input.strftime("%Y-%m-%d 23:59:59")

    # Live Patrol Feed Simulator
    st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 25px 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown("### 📡 Live Dispatch Feed")
    live_feed_active = st.sidebar.toggle("🔴 Simulate PCR Patrol Feed", value=False)
    if live_feed_active:
        sectors = ["Hinjawadi", "Kothrud", "Koregaon Park", "Shivajinagar", "Viman Nagar", "Hadapsar"]
        c_types = ["Theft", "Cybercrime", "Burglary", "Narcotics", "Assault"]
        sec = random.choice(sectors)
        ctype = random.choice(c_types)
        pcr_id = random.randint(1, 15)
        t_str = datetime.now().strftime("%I:%M:%S %p")
        st.sidebar.error(f"🚨 **[{t_str}] Dispatch Alert**: PCR-{pcr_id} routed to **{sec}** ({ctype}).")

    st.sidebar.markdown("<hr style='border-top: 1px solid #1f2937; margin: 15px 0;'>", unsafe_allow_html=True)
    st.sidebar.caption("🤖 **AI Platform Core Status**")
    st.sidebar.caption("🟢 Database: SQLite v3")
    st.sidebar.caption("🟢 Hotspot Model: DBSCAN Active")
    st.sidebar.caption("🟢 Anomaly Threshold: 2.0 Z-score")
    st.sidebar.caption("🟢 Recidivism Predictor: RF Regressor")

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

    return selected_page, filter_dict, selected_districts
