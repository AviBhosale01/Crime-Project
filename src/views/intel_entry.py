"""
Intelligence Records Entry (CRUD) View Module
"""
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import database

def render_intel_entry_view(df_suspects, df_districts, crime_types_list, severity_list, INTEL_ENTRY_KEY):
    st.markdown("## Intelligence Records Entry & Management")
    st.write("Directly interface with the SQLite databases to log crime records, register suspects, and model relationships.")
    
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
    
    if "crud_success_msg" in st.session_state and st.session_state["crud_success_msg"]:
        st.success(st.session_state.pop("crud_success_msg"))
    
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
                dist_choices = {row['id']: row['name'] for _, row in df_districts.iterrows()}
                c_district_id = st.selectbox("Incident Area / Location", list(dist_choices.keys()), format_func=lambda x: dist_choices[x])
                c_type = st.selectbox("Crime Category", crime_types_list)
                c_severity = st.selectbox("Severity Classification", severity_list)
                
            with col_c2:
                dist_row = df_districts[df_districts['id'] == c_district_id].iloc[0]
                c_lat = st.number_input("Latitude Coordinate", value=float(dist_row['center_lat']), format="%.6f")
                c_lon = st.number_input("Longitude Coordinate", value=float(dist_row['center_lon']), format="%.6f")
                c_status = st.selectbox("Investigation Status", ["Open", "In Investigation", "Closed"])
                
                suspect_choices = {0: "None (Unidentified)"}
                for _, row in df_suspects.sort_values(by='name').iterrows():
                    suspect_choices[row['id']] = f"{row['name']} (ID: {row['id']})"
                c_suspect_id = st.selectbox("Primary Linked Suspect", list(suspect_choices.keys()), format_func=lambda x: suspect_choices[x])
                
            submit_crime = st.form_submit_button("Log Incident")
            
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
                st.cache_data.clear()
                st.session_state["crud_success_msg"] = f"🚨 Incident reported successfully! Registered Crime ID: **{new_id}** ({c_type} in {dist_choices.get(c_district_id, 'Area')})"
                st.rerun()
                
    # 2. Register Suspect
    with tab_add_suspect:
        st.markdown("### Register New Suspect Profile")
        with st.form("add_suspect_form", clear_on_submit=True):
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                s_name = st.text_input("Full Name", placeholder="e.g. Rahul Shinde")
                s_age = st.number_input("Age", min_value=12, max_value=100, value=25)
                
            with col_s2:
                available_gangs = ["None"] + sorted([g for g in df_suspects['gang_affiliation'].unique() if g and g != "None"])
                s_gang = st.selectbox("Gang Affiliation", available_gangs)
                s_priors = st.number_input("Prior Arrests Count", min_value=0, max_value=100, value=0)
                
            submit_suspect = st.form_submit_button("Register Suspect")
            
            if submit_suspect:
                if s_name.strip() == "":
                    st.error("Name field cannot be left blank.")
                else:
                    base_risk = float(np.clip((s_priors * 0.15) + (0.2 if s_gang != "None" else 0) + 0.1, 0.1, 0.95))
                    new_id = database.add_suspect(
                        name=s_name.strip(),
                        age=int(s_age),
                        gang=s_gang,
                        priors=int(s_priors),
                        risk_score=base_risk
                    )
                    st.cache_data.clear()
                    st.session_state["crud_success_msg"] = f"👤 Suspect profile registered successfully! Assigned Suspect ID: **{new_id}** (Name: **{s_name.strip()}**, Syndicate: **{s_gang}**, Risk: **{base_risk:.2f}**)"
                    st.rerun()
                    
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
                    st.cache_data.clear()
                    st.session_state["crud_success_msg"] = f"🔗 Criminal link modeled successfully between Suspect ID **{s_a}** and Suspect ID **{s_b}** ({rel_type})!"
                    st.rerun()
