import streamlit as st
import os

# Security passkeys configuration
INTEL_ENTRY_KEY = None
VIEW_DATA_KEY = None
NEWS_API_KEY = 'a2a5fc4ec79447288f2589520a64c8e5'

try:
    import config_keys
    INTEL_ENTRY_KEY = getattr(config_keys, 'INTEL_ENTRY_KEY', None)
    VIEW_DATA_KEY = getattr(config_keys, 'VIEW_DATA_KEY', None)
    if hasattr(config_keys, 'NEWS_API_KEY') and config_keys.NEWS_API_KEY:
        NEWS_API_KEY = config_keys.NEWS_API_KEY
except ImportError:
    pass

if not INTEL_ENTRY_KEY:
    try:
        INTEL_ENTRY_KEY = st.secrets.get('INTEL_ENTRY_KEY', None)
    except Exception:
        INTEL_ENTRY_KEY = None

if not VIEW_DATA_KEY:
    try:
        VIEW_DATA_KEY = st.secrets.get('VIEW_DATA_KEY', None)
    except Exception:
        VIEW_DATA_KEY = None

try:
    secret_news_key = st.secrets.get('NEWS_API_KEY', None)
    if secret_news_key:
        NEWS_API_KEY = secret_news_key
except Exception:
    pass

# Application Constants
PAGE_TITLE = 'AI-Driven Crime Analytics Platform'
PAGE_ICON = '🛡️'

CRIME_TYPES = [
    'Theft', 'Assault', 'Burglary', 'Robbery', 'Narcotics', 
    'Fraud', 'Homicide', 'Vandalism', 'Extortion', 'Cybercrime'
]

SEVERITY_LEVELS = ['Low', 'Medium', 'High']
INVESTIGATION_STATUSES = ['Open', 'In Investigation', 'Closed']
RELATION_TYPES = ['Accomplice', 'Co-arrestee', 'Gang Member', 'Relative']

PUNE_DISTRICTS = [
    'Shivajinagar', 'Kothrud', 'Viman Nagar', 'Hinjawadi',
    'Koregaon Park', 'Hadapsar', 'Katraj', 'Swargate'
]

KNOWN_GANG_SYNDICATES = [
    'None', 'Pune Local Boys', 'Shivaji Nagar Syndicate',
    'Koregaon Park Cartel', 'Hinjawadi Hackers', 'D-Company Gang', 'Chhota Rajan Gang'
]

# Theme Colors & UI Palette
THEME = {
    'bg_primary': '#0b0f19',
    'bg_card': 'rgba(17, 24, 39, 0.85)',
    'border_glow': 'rgba(59, 130, 246, 0.3)',
    'accent_blue': '#3b82f6',
    'accent_cyan': '#06b6d4',
    'danger_red': '#ef4444',
    'warning_amber': '#f59e0b',
    'success_emerald': '#10b981',
    'text_primary': '#ffffff',
    'text_muted': '#cbd5e1'
}
