"""
Data Loading and Caching Module
"""
import streamlit as st
import pandas as pd
import database

@st.cache_data(ttl=60)
def load_base_data(filter_dict=None):
    """
    Load core datasets with 60-second caching for high performance.
    """
    df_crimes = database.get_crimes_df(filter_dict)
    df_suspects = database.get_suspects_df()
    df_districts = database.get_districts_df()
    df_connections = database.get_connections_df()
    return df_crimes, df_suspects, df_districts, df_connections

def get_fresh_data():
    """
    Load completely uncached, fresh datasets directly from SQLite.
    """
    conn = database.get_connection()
    df_sus = pd.read_sql_query("SELECT * FROM suspects ORDER BY id DESC", conn)
    df_cri = pd.read_sql_query("""
        SELECT c.id, c.timestamp, d.name as area_name, c.crime_type, c.severity, c.latitude, c.longitude, c.status, c.suspect_id
        FROM crimes c
        LEFT JOIN districts d ON c.district_id = d.id
        ORDER BY c.id DESC
    """, conn)
    df_con = pd.read_sql_query("SELECT suspect_a, suspect_b, relation_type, strength FROM suspect_connections", conn)
    df_dist = pd.read_sql_query("SELECT id, name FROM districts", conn)
    conn.close()
    return df_cri, df_sus, df_dist, df_con
