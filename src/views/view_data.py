"""
View Data & Inline Database Editor View Module
"""
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import database
from src.utils.exporters import export_excel, export_pdf, export_image

def render_view_data_view(VIEW_DATA_KEY):
    st.markdown("## 📂 Database Records Viewer & Editor")
    st.write("Explore, search, edit, delete, and download raw tables from the Pune Crime Intelligence database.")
    
    if "view_data_success_msg" in st.session_state and st.session_state["view_data_success_msg"]:
        st.success(st.session_state.pop("view_data_success_msg"))
    
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
    
    # Load fresh datasets to display
    conn = database.get_connection()
    df_sus = pd.read_sql_query("SELECT * FROM suspects ORDER BY id DESC", conn)
    df_cri = pd.read_sql_query("""
        SELECT c.id, c.timestamp, d.name as area_name, c.crime_type, c.severity, c.latitude, c.longitude, c.status, c.suspect_id
        FROM crimes c
        LEFT JOIN districts d ON c.district_id = d.id
        ORDER BY c.id DESC
    """, conn)
    df_con = pd.read_sql_query("SELECT suspect_a, suspect_b, relation_type, strength FROM suspect_connections", conn)
    df_dist_choices = pd.read_sql_query("SELECT id, name FROM districts", conn)
    conn.close()

    tab_sus, tab_cri, tab_con = st.tabs([
        "👤 Suspects Database",
        "⚠️ Incident Log",
        "🔗 Association Network"
    ])
    
    # Tab 1: Suspects
    with tab_sus:
        st.markdown("### Suspect Registry")
        st.write("Use the table below to view, search, edit, or delete suspects. Click **Save Suspect Changes** to persist your updates to SQLite.")
        
        search_sus = st.text_input("🔍 Search Suspects by Name, Gang, or ID", "", key="search_suspects")
        filtered_sus = df_sus.copy()
        if search_sus:
            filtered_sus = filtered_sus[
                filtered_sus['name'].str.contains(search_sus, case=False, na=False) |
                filtered_sus['gang_affiliation'].str.contains(search_sus, case=False, na=False) |
                filtered_sus['id'].astype(str).str.contains(search_sus, case=False, na=False)
            ]
            
        st.info("💡 **Tip**: Double-click any cell to edit. Select a row and press **Delete** or **Backspace** to delete. Scroll to the bottom to add a new row.")
        
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
        
        c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 5])
        with c_btn1:
            if st.button("Reset / Undo All Edits", key="reset_suspects"):
                st.rerun()
        with c_btn2:
            if st.button("Save Suspect Changes", key="save_suspects"):
                editor_state = st.session_state.get("suspects_editor", {})
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        sus_id = int(filtered_sus.iloc[row_idx]["id"])
                        name = changes.get("name", filtered_sus.iloc[row_idx]["name"])
                        age = int(changes.get("age", filtered_sus.iloc[row_idx]["age"]))
                        gang = changes.get("gang_affiliation", filtered_sus.iloc[row_idx]["gang_affiliation"])
                        priors = int(changes.get("priors_count", filtered_sus.iloc[row_idx]["priors_count"]))
                        risk = float(changes.get("risk_score", filtered_sus.iloc[row_idx]["risk_score"]))
                        database.update_suspect_details(sus_id, name, age, gang, priors, risk)
                        
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        name = row.get("name", "New Suspect")
                        age = int(row.get("age", 25))
                        gang = row.get("gang_affiliation", "None")
                        priors = int(row.get("priors_count", 0))
                        risk = float(np.clip((priors * 0.15) + (0.2 if gang != "None" else 0) + 0.1, 0.1, 0.95))
                        risk = float(row.get("risk_score", risk))
                        database.add_suspect(name, age, gang, priors, risk)
                        
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        sus_id = int(filtered_sus.iloc[row_idx]["id"])
                        database.delete_suspect(sus_id)
                        
                st.session_state["view_data_success_msg"] = "✅ Suspect changes saved successfully to database!"
                st.cache_data.clear()
                st.rerun()
                
        st.markdown("#### 📥 Export Suspect Data")
        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
        with exp_col1:
            st.download_button("CSV Export", filtered_sus.to_csv(index=False).encode('utf-8'), "pune_suspects.csv", "text/csv", key="dl_sus_csv")
        with exp_col2:
            st.download_button("Excel Export", export_excel(filtered_sus, "pune_suspects.xlsx"), "pune_suspects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_sus_excel")
        with exp_col3:
            st.download_button("PDF Export", export_pdf(filtered_sus, "Pune Suspects Database"), "pune_suspects.pdf", "application/pdf", key="dl_sus_pdf")
        with exp_col4:
            st.download_button("Table Image (PNG)", export_image(filtered_sus, "Pune Suspects Database"), "pune_suspects.png", "image/png", key="dl_sus_png")

    # Tab 2: Incident Log
    with tab_cri:
        st.markdown("### Crime Incident Logs")
        st.write("Use the table below to view, search, edit, or delete crime incidents.")
        
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
        
        cc_btn1, cc_btn2, _ = st.columns([1.5, 1.5, 5])
        with cc_btn1:
            if st.button("Reset / Undo All Edits", key="reset_crimes"):
                st.rerun()
        with cc_btn2:
            if st.button("Save Crime Changes", key="save_crimes"):
                editor_state = st.session_state.get("crimes_editor", {})
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        crime_id = int(filtered_cri.iloc[row_idx]["id"])
                        timestamp = changes.get("timestamp", filtered_cri.iloc[row_idx]["timestamp"])
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
                        
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        timestamp = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        area_name = row.get("area_name", "Shivajinagar")
                        matched_dist = df_dist_choices[df_dist_choices['name'] == area_name]
                        district_id = int(matched_dist.iloc[0]['id']) if not matched_dist.empty else 1
                        crime_type = row.get("crime_type", "Theft")
                        severity = row.get("severity", "Low")
                        latitude = float(row.get("latitude", 18.5204))
                        longitude = float(row.get("longitude", 73.8567))
                        status = row.get("status", "Open")
                        suspect_id_val = row.get("suspect_id")
                        suspect_id = None if pd.isna(suspect_id_val) or suspect_id_val == "" or suspect_id_val is None else int(suspect_id_val)
                        database.add_crime(timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
                        
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        crime_id = int(filtered_cri.iloc[row_idx]["id"])
                        database.delete_crime(crime_id)
                        
                st.session_state["view_data_success_msg"] = "✅ Crime incident changes saved successfully to database!"
                st.cache_data.clear()
                st.rerun()
                
        st.markdown("#### 📥 Export Incident Data")
        exp_cri_col1, exp_cri_col2, exp_cri_col3, exp_cri_col4 = st.columns(4)
        with exp_cri_col1:
            st.download_button("CSV Export", filtered_cri.to_csv(index=False).encode('utf-8'), "pune_crimes.csv", "text/csv", key="dl_cri_csv")
        with exp_cri_col2:
            st.download_button("Excel Export", export_excel(filtered_cri, "pune_crimes.xlsx"), "pune_crimes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_cri_excel")
        with exp_cri_col3:
            st.download_button("PDF Export", export_pdf(filtered_cri, "Pune Crime Incident Logs"), "pune_crimes.pdf", "application/pdf", key="dl_cri_pdf")
        with exp_cri_col4:
            st.download_button("Table Image (PNG)", export_image(filtered_cri, "Pune Crime Incident Logs"), "pune_crimes.png", "image/png", key="dl_cri_png")

    # Tab 3: Connections
    with tab_con:
        st.markdown("### Criminal Associate Network Connections")
        st.write("View and modify modeled relationship edges between suspects in the intelligence graph.")
        
        search_con = st.text_input("🔍 Filter by Suspect ID or Relation Type", "", key="search_con")
        filtered_con = df_con.copy()
        if search_con:
            filtered_con = filtered_con[
                filtered_con['suspect_a'].astype(str).str.contains(search_con, case=False, na=False) |
                filtered_con['suspect_b'].astype(str).str.contains(search_con, case=False, na=False) |
                filtered_con['relation_type'].str.contains(search_con, case=False, na=False)
            ]
            
        edited_con_df = st.data_editor(
            filtered_con,
            num_rows="dynamic",
            use_container_width=True,
            key="con_editor",
            column_config={
                "suspect_a": st.column_config.NumberColumn("Suspect A (ID)"),
                "suspect_b": st.column_config.NumberColumn("Suspect B (ID)"),
                "relation_type": st.column_config.SelectboxColumn("Relation Type", options=["Accomplice", "Co-arrestee", "Gang Member", "Relative"]),
                "strength": st.column_config.NumberColumn("Strength (1-5)", min_value=1, max_value=5)
            }
        )
        
        con_btn1, con_btn2, _ = st.columns([1.5, 1.5, 5])
        with con_btn1:
            if st.button("Reset / Undo Edits", key="reset_con"):
                st.rerun()
        with con_btn2:
            if st.button("Save Connections", key="save_connections"):
                editor_state = st.session_state.get("con_editor", {})
                if "edited_rows" in editor_state:
                    for row_idx_str, changes in editor_state["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        s_a = int(filtered_con.iloc[row_idx]["suspect_a"])
                        s_b = int(filtered_con.iloc[row_idx]["suspect_b"])
                        rel = changes.get("relation_type", filtered_con.iloc[row_idx]["relation_type"])
                        strength = int(changes.get("strength", filtered_con.iloc[row_idx]["strength"]))
                        database.update_connection_details(s_a, s_b, rel, strength)
                        
                if "added_rows" in editor_state:
                    for row in editor_state["added_rows"]:
                        s_a = int(row.get("suspect_a", 1))
                        s_b = int(row.get("suspect_b", 2))
                        rel = row.get("relation_type", "Accomplice")
                        strength = int(row.get("strength", 3))
                        database.add_connection(s_a, s_b, rel, strength)
                        
                if "deleted_rows" in editor_state:
                    for row_idx in editor_state["deleted_rows"]:
                        s_a = int(filtered_con.iloc[row_idx]["suspect_a"])
                        s_b = int(filtered_con.iloc[row_idx]["suspect_b"])
                        database.delete_connection(s_a, s_b)
                        
                st.session_state["view_data_success_msg"] = "✅ Criminal associate connection changes saved successfully!"
                st.cache_data.clear()
                st.rerun()
