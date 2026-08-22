"""
Application Header Component
"""
import streamlit as st

def render_header():
    """
    Render the top dashboard banner with Pune Police intelligence branding and live status pill.
    """
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
