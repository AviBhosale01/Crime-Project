"""
UI Styles & Custom CSS Module
"""
import streamlit as st

def apply_custom_styles():
    """
    Inject modern cyberpunk dark theme CSS, fonts, and responsive container styles.
    """
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
