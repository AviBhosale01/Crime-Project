"""
Geospatial Intelligence View Module
"""
import streamlit as st
import pandas as pd
import analytics
import visualizations

def render_geospatial_view(df_crimes, df_districts):
    st.markdown("## Geospatial Analytics & Spatial Hotspot Detection")
    st.write("Leverage Density-Based Spatial Clustering (DBSCAN) to identify crime clusters and hotspots across districts.")
    
    map_type = st.radio("Select Analysis Layer", ["Incident Locations Scatter", "DBSCAN Cluster Hotspots", "Kernel Density Heatmap"], horizontal=True)
    
    if map_type == "DBSCAN Cluster Hotspots":
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            eps_slider = st.slider("DBSCAN Epsilon (roughly km range)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, help="Max distance between two crime points to be considered as same cluster.")
        with col_ctrl2:
            min_pts_slider = st.slider("Min Incidents to Define Hotspot", min_value=3, max_value=20, value=6, step=1, help="Minimum number of crimes in epsilon radius to create a cluster.")
            
        df_geo = analytics.detect_hotspots(df_crimes, eps_km=eps_slider, min_samples=min_pts_slider)
        active_ids = [hid for hid in df_geo['hotspot_id'].unique() if hid != -1]
        st.markdown(f"🤖 **Clustering Output**: Detected **{len(active_ids)}** active crime hotspot zones. Isolated incident points are marked as Noise.")
        
        hs_options = ["Show All Hotspots"] + [f"Hotspot Zone {hid}" for hid in sorted(active_ids)]
        sel_hs = st.selectbox("Isolate Specific Cluster Zone", hs_options)
        
        selected_id = None
        if sel_hs != "Show All Hotspots":
            selected_id = int(sel_hs.split()[-1])
            
        map_fig = visualizations.create_geospatial_map(df_geo, show_hotspots=True, selected_hotspot_id=selected_id)
        st.plotly_chart(map_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
        if len(active_ids) > 0:
            st.markdown("### Hotspot Breakdown")
            hs_details = []
            for hid in active_ids:
                sub_df = df_geo[df_geo['hotspot_id'] == hid]
                common_crime = sub_df['crime_type'].mode()[0] if not sub_df.empty else "N/A"
                common_district = sub_df['district_name'].mode()[0] if not sub_df.empty else "N/A"
                hs_details.append({
                    "Hotspot Zone": f"Zone {hid}",
                    "Incidents Count": len(sub_df),
                    "Dominant Crime": common_crime,
                    "Location / District": common_district,
                    "Avg Severity": "High" if (sub_df['severity'] == 'High').mean() > 0.4 else "Medium"
                })
            st.table(pd.DataFrame(hs_details))
            
    elif map_type == "Kernel Density Heatmap":
        density_fig = visualizations.create_density_map(df_crimes)
        st.plotly_chart(density_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
    else:
        scatter_fig = visualizations.create_geospatial_map(df_crimes, show_hotspots=False)
        st.plotly_chart(scatter_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
