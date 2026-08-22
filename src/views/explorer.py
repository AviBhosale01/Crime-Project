"""
Search & Explorer View Module
"""
import streamlit as st
import pandas as pd
import visualizations

def render_explorer_view(df_crimes, df_suspects, severity_list):
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
