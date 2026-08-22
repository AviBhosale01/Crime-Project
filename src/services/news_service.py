"""
Live OSINT Crime News Service Module (NewsAPI Integration)
"""
import streamlit as st
import requests
import urllib.parse
from datetime import datetime

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_news_data(query_str: str, api_key_str: str):
    """
    Fetch real-time crime news articles from NewsAPI with 5-minute intelligent caching.
    """
    if not api_key_str:
        return [], "NewsAPI Key is missing. Please provide a valid API Key."
        
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
