"""
🛡️ Crime Intelligence Command Center
Main Application Entry Point (Modular Architecture)
"""
import streamlit as st
import database
from src.core.config import (
    PAGE_TITLE, PAGE_ICON, INTEL_ENTRY_KEY, VIEW_DATA_KEY, NEWS_API_KEY,
    CRIME_TYPES, SEVERITY_LEVELS, PUNE_DISTRICTS
)
from src.core.data_loader import load_base_data
from src.utils.styles import apply_custom_styles
from src.components.header import render_header
from src.components.sidebar import render_sidebar
from src.components.floating_assistant import render_floating_assistant

# Page Views
from src.views.dashboard import render_dashboard_view
from src.views.geospatial import render_geospatial_view
from src.views.explorer import render_explorer_view
from src.views.predictions import render_predictions_view
from src.views.network import render_network_view
from src.views.intel_entry import render_intel_entry_view
from src.views.view_data import render_view_data_view
from src.views.chatbot import render_chatbot_view
from src.views.news import render_news_view

# 1. Set Streamlit Page Configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Theme Styles & CSS
apply_custom_styles()

# 3. Initialize SQLite Database Engine
database.init_db()

# 4. Load Raw District Records for Sidebar Filters
_, _, districts_raw, _ = load_base_data()

# 5. Render Sidebar Navigation & Collect Filters
selected_page, filter_dict, selected_districts = render_sidebar(districts_raw)

# 6. Load Filtered Datasets for Current View
df_crimes, df_suspects, df_districts, df_connections = load_base_data(filter_dict)

# 7. Render Main Branding Header
render_header()

# 8. Route to Active Page View
district_names = sorted(districts_raw['name'].tolist()) if not districts_raw.empty else PUNE_DISTRICTS

if selected_page == "📊 Command Dashboard":
    render_dashboard_view(df_crimes, df_suspects, df_districts)

elif selected_page == "🗺️ Geospatial Intelligence":
    render_geospatial_view(df_crimes, df_districts)

elif selected_page == "🔍 Search & Explorer":
    render_explorer_view(df_crimes, df_suspects, SEVERITY_LEVELS)

elif selected_page == "🧠 AI Predictive Models":
    render_predictions_view(df_crimes, df_suspects, df_districts, district_names, CRIME_TYPES)

elif selected_page == "🕸️ Criminal Network Analysis":
    render_network_view(df_suspects, df_connections, df_crimes)

elif selected_page == "📝 Intel Entry (CRUD)":
    render_intel_entry_view(df_suspects, df_districts, CRIME_TYPES, SEVERITY_LEVELS, INTEL_ENTRY_KEY)

elif selected_page == "📂 View Data":
    render_view_data_view(VIEW_DATA_KEY)

elif selected_page == "💬 AI Intel Chatbot":
    render_chatbot_view()

elif selected_page == "📰 Crime News":
    render_news_view(NEWS_API_KEY)

# 9. Global Page End Footer
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

# 10. Render Floating 3D Police Assistant Widget
render_floating_assistant(selected_page)
