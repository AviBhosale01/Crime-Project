import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

# Set default theme to dark
px.defaults.template = "plotly_dark"

def format_crime_hover_text(df, show_hotspots=False):
    """
    Generate rich, attractive HTML hover tooltips for map data points including:
    - Crime category & severity badge
    - District / location & exact lat/lon coordinates
    - Timestamp
    - Status
    - Linked Suspect Name (bold blue)
    - Gang Affiliation
    - ML Risk Score (color coded)
    - Hotspot cluster zone (if applicable)
    """
    hover_list = []
    
    for _, row in df.iterrows():
        # Suspect details
        sus_name = str(row['suspect_name']).strip() if pd.notnull(row.get('suspect_name')) and str(row['suspect_name']).strip() != '' and str(row['suspect_name']).lower() != 'none' and str(row['suspect_name']).lower() != 'nan' else None
        if sus_name:
            suspect_html = f"👤 <b>Linked Suspect:</b> <b style='color: #60A5FA; font-size: 1.05em;'>{sus_name}</b>"
        else:
            suspect_html = "👤 <b>Linked Suspect:</b> <span style='color: #9CA3AF;'>Unidentified / Unknown</span>"
            
        gang_name = str(row['gang_affiliation']).strip() if pd.notnull(row.get('gang_affiliation')) and str(row['gang_affiliation']).strip() != '' and str(row['gang_affiliation']).lower() != 'none' and str(row['gang_affiliation']).lower() != 'nan' else None
        if gang_name:
            gang_html = f"👥 <b>Gang:</b> <b>{gang_name}</b>"
        else:
            gang_html = "👥 <b>Gang:</b> <span style='color: #9CA3AF;'>Independent / None</span>"
            
        risk_score = row.get('suspect_risk_score')
        if pd.notnull(risk_score) and str(risk_score) != '':
            try:
                r_val = float(risk_score)
                r_color = "#EF4444" if r_val > 0.65 else ("#F59E0B" if r_val > 0.35 else "#10B981")
                risk_html = f"⚡ <b>ML Risk Score:</b> <b style='color: {r_color};'>{r_val:.2f}</b>"
            except Exception:
                risk_html = "⚡ <b>ML Risk Score:</b> <span style='color: #9CA3AF;'>N/A</span>"
        else:
            risk_html = "⚡ <b>ML Risk Score:</b> <span style='color: #9CA3AF;'>N/A</span>"
            
        # Timestamp
        ts = row.get('timestamp')
        if pd.notnull(ts):
            try:
                date_html = pd.to_datetime(ts).strftime('%d %b %Y, %I:%M %p')
            except Exception:
                date_html = str(ts)
        else:
            date_html = "N/A"
            
        # Severity
        sev = str(row.get('severity', 'Low'))
        if sev == "High":
            sev_badge = "<span style='background-color: rgba(239, 68, 68, 0.25); color: #EF4444; border: 1px solid #EF4444; padding: 2px 8px; border-radius: 12px; font-weight: bold;'>🔴 HIGH SEVERITY</span>"
        elif sev == "Medium":
            sev_badge = "<span style='background-color: rgba(245, 158, 11, 0.25); color: #F59E0B; border: 1px solid #F59E0B; padding: 2px 8px; border-radius: 12px; font-weight: bold;'>🟡 MEDIUM SEVERITY</span>"
        else:
            sev_badge = "<span style='background-color: rgba(16, 185, 129, 0.25); color: #10B981; border: 1px solid #10B981; padding: 2px 8px; border-radius: 12px; font-weight: bold;'>🟢 LOW SEVERITY</span>"
            
        # Status
        status = str(row.get('status', 'Open'))
        if status == "Closed":
            status_html = "<span style='color: #10B981; font-weight: 600;'>✅ Closed</span>"
        elif status == "In Investigation":
            status_html = "<span style='color: #F59E0B; font-weight: 600;'>🔍 In Investigation</span>"
        else:
            status_html = "<span style='color: #EF4444; font-weight: 600;'>⚠️ Open</span>"
            
        district = str(row.get('district_name', 'Pune Sector'))
        c_type = str(row.get('crime_type', 'Incident'))
        lat = float(row.get('latitude', 0.0))
        lon = float(row.get('longitude', 0.0))
        
        # Build Hover HTML string
        lines = [
            f"<b style='font-size: 1.15em; color: #FFFFFF;'>🚨 {c_type.upper()}</b> &nbsp;&nbsp; {sev_badge}",
            f"<span style='color: #4B5563;'>────────────────────────────────────────</span>",
            f"📍 <b>Location:</b> {district} &nbsp;({lat:.4f}° N, {lon:.4f}° E)",
            f"📅 <b>Timestamp:</b> {date_html}",
            f"📌 <b>Status:</b> {status_html}",
            f"<span style='color: #4B5563;'>────────────────────────────────────────</span>",
            f"{suspect_html}",
            f"{gang_html}",
            f"{risk_html}"
        ]
        
        if show_hotspots and 'Hotspot Type' in row:
            lines.append(f"🔥 <b>Cluster Zone:</b> <b style='color: #3B82F6;'>{row['Hotspot Type']}</b>")
            
        hover_list.append("<br>".join(lines))
        
    return hover_list

def create_geospatial_map(crimes_df, show_hotspots=False, selected_hotspot_id=None):
    """
    Generate an interactive Mapbox map of crimes with rich suspect hover popups.
    If show_hotspots=True, color-code nodes by DBSCAN cluster IDs.
    """
    if crimes_df.empty:
        fig = px.scatter_mapbox(lat=[18.5204], lon=[73.8567], zoom=11.5)
        fig.update_layout(mapbox_style="carto-darkmatter")
        return fig
        
    df = crimes_df.copy()
    
    centroid_lats = []
    centroid_lons = []
    centroid_texts = []
    
    if show_hotspots and 'hotspot_id' in df.columns:
        df['Hotspot Type'] = df['hotspot_id'].apply(lambda x: "Noise / Isolated" if x == -1 else f"Hotspot Zone {x}")
        
        if selected_hotspot_id is not None:
            df = df[df['hotspot_id'] == selected_hotspot_id]
            
        color_col = 'Hotspot Type'
        unique_hotspots = sorted(df['hotspot_id'].unique())
        color_discrete_map = {"Noise / Isolated": "#6b7280"}
        colors = px.colors.qualitative.Bold
        color_idx = 0
        for hid in unique_hotspots:
            if hid != -1:
                color_discrete_map[f"Hotspot Zone {hid}"] = colors[color_idx % len(colors)]
                color_idx += 1
                
        active_hids = [hid for hid in df['hotspot_id'].unique() if hid != -1]
        hotspot_names = {
            0: "Kothrud Central Zone",
            1: "Hinjawadi IT Corridor",
            2: "Koregaon Park Nightlife Hub"
        }
        for hid in active_hids:
            sub = df[df['hotspot_id'] == hid]
            if not sub.empty:
                c_lat = sub['latitude'].mean()
                c_lon = sub['longitude'].mean()
                c_count = len(sub)
                c_name = hotspot_names.get(hid, f"Hotspot Zone {hid}")
                centroid_lats.append(c_lat)
                centroid_lons.append(c_lon)
                centroid_texts.append(f"🔴 <b>{c_name}</b> ({c_count} cases)")
                
        df['hover_info'] = format_crime_hover_text(df, show_hotspots=True)
        
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            color=color_col,
            color_discrete_map=color_discrete_map,
            size=df['severity'].map({'Low': 8, 'Medium': 12, 'High': 18}),
            custom_data=['hover_info'],
            zoom=11.5,
            title="Geospatial Intelligence Map - DBSCAN Hotspots"
        )
    else:
        df['hover_info'] = format_crime_hover_text(df, show_hotspots=False)
        
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            color='crime_type',
            size=df['severity'].map({'Low': 8, 'Medium': 12, 'High': 18}),
            custom_data=['hover_info'],
            zoom=11.5,
            title="Geospatial Intelligence Map - Incident Distribution"
        )
        
    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>"
    )
        
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=11.5,
        mapbox_center={"lat": 18.5204, "lon": 73.8567},
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",
        hovermode="closest",
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(17, 24, 39, 0.85)",
            bordercolor="rgba(75, 85, 99, 0.4)",
            borderwidth=1,
            font=dict(color="#E5E7EB", size=12)
        )
    )
    
    # Overlay active hotspot centroids with text labels directly on map
    if show_hotspots and centroid_lats:
        fig.add_trace(go.Scattermapbox(
            lat=centroid_lats,
            lon=centroid_lons,
            mode='markers+text',
            marker=dict(size=14, color='#EF4444', opacity=0.95),
            text=centroid_texts,
            textposition='top right',
            textfont=dict(size=12, color='#FFFFFF', family='Outfit, Inter, sans-serif'),
            hoverinfo='text',
            name='Active Hotspots Centroids'
        ))
        
    return fig

def create_density_map(crimes_df):
    """Density Heatmap of crimes with interactive scatter overlay for dot-level hover details."""
    if crimes_df.empty:
        fig = px.scatter_mapbox(lat=[18.5204], lon=[73.8567], zoom=11.5)
        fig.update_layout(mapbox_style="carto-darkmatter")
        return fig
        
    df = crimes_df.copy()
    df['hover_info'] = format_crime_hover_text(df, show_hotspots=False)
    
    # Base density map
    fig = px.density_mapbox(
        df, 
        lat='latitude', 
        lon='longitude', 
        radius=18,
        zoom=11.5,
        mapbox_style="carto-darkmatter",
        title="Crime Density Heatmap & Incident Overlay",
        color_continuous_scale="Viridis"
    )
    
    # Interactive scatter overlay trace for individual point hover popups
    scatter_trace = go.Scattermapbox(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=dict(
            size=df['severity'].map({'Low': 8, 'Medium': 12, 'High': 16}),
            color=df['severity'].map({'Low': '#10B981', 'Medium': '#F59E0B', 'High': '#EF4444'}),
            opacity=0.75
        ),
        text=df['hover_info'],
        hovertemplate="%{text}<extra></extra>",
        name="Incident Details Overlay"
    )
    fig.add_trace(scatter_trace)
    
    fig.update_layout(
        mapbox_center={"lat": 18.5204, "lon": 73.8567},
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",
        hovermode="closest",
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(17, 24, 39, 0.85)",
            bordercolor="rgba(75, 85, 99, 0.4)",
            borderwidth=1,
            font=dict(color="#E5E7EB", size=12)
        )
    )
    return fig

def create_network_graph(suspects_df, connections_df, highlight_suspect_id=None, selected_gang=None):
    """
    Build and render criminal network graph using NetworkX and Plotly.
    Node size reflects Degree Centrality.
    Node color reflects ML Suspect Risk Score.
    Edge colors reflect Relationship Type (Gang Member, Accomplice, Co-arrestee, Relative).
    Edge thickness reflects Link Strength (1-5).
    """
    if suspects_df.empty or connections_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Network Data Available", showarrow=False, font=dict(size=18, color="#9CA3AF"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig, {}
        
    df_sus = suspects_df.copy()
    df_con = connections_df.copy()
    
    # Optional Gang Filter
    if selected_gang and selected_gang != "All Gangs":
        df_sus = df_sus[df_sus['gang_affiliation'] == selected_gang]
        valid_ids = set(df_sus['id'].tolist())
        df_con = df_con[df_con['suspect_a'].isin(valid_ids) & df_con['suspect_b'].isin(valid_ids)]
        
    if highlight_suspect_id is not None:
        neighbors = {int(highlight_suspect_id)}
        for _, row in df_con.iterrows():
            sa, sb = int(row['suspect_a']), int(row['suspect_b'])
            if sa == highlight_suspect_id:
                neighbors.add(sb)
            elif sb == highlight_suspect_id:
                neighbors.add(sa)
                
        filtered_suspects = df_sus[df_sus['id'].isin(neighbors)]
        filtered_connections = df_con[
            df_con['suspect_a'].isin(neighbors) & 
            df_con['suspect_b'].isin(neighbors)
        ]
    else:
        # Show top 90 most connected suspects
        degrees = {}
        for _, row in df_con.iterrows():
            sa, sb = int(row['suspect_a']), int(row['suspect_b'])
            degrees[sa] = degrees.get(sa, 0) + 1
            degrees[sb] = degrees.get(sb, 0) + 1
            
        top_connected = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:90]
        top_connected_set = set(top_connected)
        
        filtered_suspects = df_sus[df_sus['id'].isin(top_connected_set)]
        filtered_connections = df_con[
            df_con['suspect_a'].isin(top_connected_set) & 
            df_con['suspect_b'].isin(top_connected_set)
        ]

    if filtered_suspects.empty:
        fig = go.Figure()
        fig.add_annotation(text="No matching suspect network links.", showarrow=False, font=dict(size=16, color="#9CA3AF"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig, {}

    G = nx.Graph()
    
    for _, row in filtered_suspects.iterrows():
        G.add_node(
            int(row['id']),
            name=row['name'],
            age=int(row['age']),
            gang=row['gang_affiliation'],
            risk=float(row['risk_score']),
            priors=int(row['priors_count'])
        )
        
    for _, row in filtered_connections.iterrows():
        G.add_edge(
            int(row['suspect_a']),
            int(row['suspect_b']),
            relation=row['relation_type'],
            weight=int(row['strength'])
        )
        
    deg_centrality = nx.degree_centrality(G)
    bet_centrality = nx.betweenness_centrality(G)
    
    pos = nx.spring_layout(G, k=0.55, iterations=60, seed=42)
    
    # ---------------- Edge Traces by Relation Type ----------------
    relation_colors = {
        "Gang Member": "#EF4444",   # Crimson Red
        "Accomplice": "#F59E0B",    # Amber Yellow
        "Co-arrestee": "#3B82F6",   # Electric Blue
        "Relative": "#10B981"       # Emerald Green
    }
    
    edge_traces = []
    
    # Group edges by relation_type
    for rel_type, color in relation_colors.items():
        rel_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get('relation') == rel_type]
        if not rel_edges:
            continue
            
        edge_x = []
        edge_y = []
        mid_x = []
        mid_y = []
        mid_texts = []
        
        for u, v, d in rel_edges:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            # Midpoint for hover tooltip
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            mid_x.append(mx)
            mid_y.append(my)
            
            u_name = G.nodes[u]['name']
            v_name = G.nodes[v]['name']
            str_val = d.get('weight', 1)
            mid_texts.append(
                f"🔗 <b>Relation: {rel_type}</b><br>"
                f"👥 <b>Connected:</b> {u_name} ↔ {v_name}<br>"
                f"💪 <b>Link Strength:</b> {str_val}/5"
            )
            
        # Line trace
        edge_line_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.8, color=color),
            hoverinfo='none',
            mode='lines',
            name=f"Link: {rel_type}",
            showlegend=True
        )
        
        # Midpoint hover trace
        edge_mid_trace = go.Scatter(
            x=mid_x, y=mid_y,
            mode='markers',
            marker=dict(size=6, color=color, opacity=0.8),
            text=mid_texts,
            hovertemplate="%{text}<extra></extra>",
            name=f"Link Info ({rel_type})",
            showlegend=False
        )
        
        edge_traces.extend([edge_line_trace, edge_mid_trace])
        
    # ---------------- Node Trace ----------------
    node_x = []
    node_y = []
    node_color = []
    node_size = []
    node_text = []
    node_labels = []
    node_border_width = []
    node_border_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        attrs = G.nodes[node]
        node_color.append(attrs['risk'])
        
        # Size based on degree centrality (16 to 48)
        size = 16 + deg_centrality[node] * 75
        node_size.append(size)
        
        # Suspect Name label next to node for top connected gang hubs
        if deg_centrality[node] > 0.08 or (highlight_suspect_id is not None and node == highlight_suspect_id):
            node_labels.append(f"<b>{attrs['name']}</b>")
        else:
            node_labels.append("")
            
        # Rich Hover Card
        r_val = attrs['risk']
        r_color = "#EF4444" if r_val > 0.65 else ("#F59E0B" if r_val > 0.35 else "#10B981")
        
        hover_txt = (
            f"<b style='font-size: 1.15em; color: #FFFFFF;'>👤 {attrs['name']}</b><br>"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
            f"👥 <b>Gang:</b> <b>{attrs['gang']}</b><br>"
            f"🎂 <b>Age:</b> {attrs['age']} &nbsp;|&nbsp; 🔒 <b>Arrests (Priors):</b> {attrs['priors']}<br>"
            f"⚡ <b>ML Risk Score:</b> <b style='color: {r_color};'>{r_val:.2f}</b><br>"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
            f"🌐 <b>Network Degree (Links):</b> {G.degree(node)}<br>"
            f"📊 <b>Degree Centrality:</b> {deg_centrality[node]:.3f}<br>"
            f"🌉 <b>Bridge Centrality (Betweenness):</b> {bet_centrality[node]:.3f}"
        )
        node_text.append(hover_txt)
        
        if highlight_suspect_id is not None and node == highlight_suspect_id:
            node_border_width.append(3.5)
            node_border_color.append("#10B981") # Bright Emerald
        elif attrs['risk'] > 0.65:
            node_border_width.append(2)
            node_border_color.append("#EF4444") # Red border for high risk
        else:
            node_border_width.append(1)
            node_border_color.append("#4B5563")
            
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_labels,
        textposition='top center',
        textfont=dict(size=11, color='#F3F4F6', family='Outfit, sans-serif'),
        hoverinfo='text',
        hovertext=node_text,
        hovertemplate="%{hovertext}<extra></extra>",
        name="Suspect Profiles",
        marker=dict(
            showscale=True,
            colorscale='Plasma',
            reversescale=False,
            color=node_color,
            size=node_size,
            colorbar=dict(
                title='ML Risk Score',
                thickness=16,
                x=1.02,
                len=0.75,
                ypad=0,
                tickfont=dict(color="#E5E7EB")
            ),
            line=dict(color=node_border_color, width=node_border_width)
        )
    )
    
    fig = go.Figure(
        data=[*edge_traces, node_trace],
        layout=go.Layout(
            title=dict(text='<b>Criminal Associates & Gang Link Analysis Graph</b>', font=dict(size=17, color="#FFFFFF")),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=10, l=10, r=10, t=45),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode='pan',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.05,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(17, 24, 39, 0.85)",
                bordercolor="rgba(75, 85, 99, 0.4)",
                borderwidth=1,
                font=dict(color="#E5E7EB", size=11)
            )
        )
    )
    
    metrics = {
        node: {
            "name": G.nodes[node]["name"],
            "degree": G.degree(node),
            "degree_centrality": deg_centrality[node],
            "betweenness_centrality": bet_centrality[node]
        }
        for node in G.nodes()
    }
    
    return fig, metrics

def create_offender_timeline(suspect_id, crimes_df, suspect_name):
    """Generate crime timeline for a specific suspect."""
    suspect_crimes = crimes_df[crimes_df['suspect_id'] == suspect_id].copy()
    
    if suspect_crimes.empty:
        fig = go.Figure()
        fig.add_annotation(text="No crime record history linked to this suspect ID.", showarrow=False, font=dict(size=14))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    suspect_crimes = suspect_crimes.sort_values(by='timestamp')
    suspect_crimes['date_str'] = suspect_crimes['timestamp'].dt.strftime('%Y-%m-%d')
    
    fig = px.scatter(
        suspect_crimes,
        x='timestamp',
        y='crime_type',
        color='severity',
        color_discrete_map={'Low': '#10B981', 'Medium': '#F59E0B', 'High': '#EF4444'},
        size=suspect_crimes['severity'].map({'Low': 12, 'Medium': 18, 'High': 24}),
        hover_name='crime_type',
        hover_data={
            'date_str': True,
            'district_name': True,
            'status': True,
            'severity': True,
            'timestamp': False
        },
        title=f"Offense Timeline: {suspect_name}"
    )
    
    fig.update_layout(
        xaxis_title="Date of Offense",
        yaxis_title="Crime Category",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320
    )
    fig.update_yaxes(categoryorder="category ascending")
    return fig

def create_recidivism_gauge_chart(risk_score):
    """
    Generate a Plotly radial gauge dial chart for offender recidivism risk index (0.0 to 1.0).
    Color coded: Emerald Green (Low) -> Amber (Elevated) -> Crimson (Critical).
    """
    val = float(np.clip(risk_score, 0.0, 1.0)) * 100.0
    
    if val > 65:
        bar_color = "#EF4444"
        risk_label = "CRITICAL / HIGH RISK"
    elif val > 35:
        bar_color = "#F59E0B"
        risk_label = "ELEVATED RISK"
    else:
        bar_color = "#10B981"
        risk_label = "LOW RISK"
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=val,
        number={'suffix': "%", 'font': {'size': 38, 'color': bar_color, 'family': 'Outfit, sans-serif'}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>{risk_label}</b>", 'font': {'size': 14, 'color': bar_color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#4B5563", 'dtick': 20},
            'bar': {'color': bar_color, 'thickness': 0.3},
            'bgcolor': "rgba(17, 24, 39, 0.6)",
            'borderwidth': 1,
            'bordercolor': "rgba(75, 85, 99, 0.3)",
            'steps': [
                {'range': [0, 35], 'color': 'rgba(16, 185, 129, 0.15)'},
                {'range': [35, 65], 'color': 'rgba(245, 158, 11, 0.15)'},
                {'range': [65, 100], 'color': 'rgba(239, 68, 68, 0.15)'}
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 3},
                'thickness': 0.75,
                'value': 65
            }
        }
    ))
    
    fig.update_layout(
        height=240,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_anomaly_chart(daily_counts):
    """
    Chart crime timeline with 14-day rolling stats, upper 2-sigma confidence band, and Z-score anomalies.
    """
    if daily_counts.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for anomalies.", showarrow=False)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    df = daily_counts.copy()
    # Calculate upper confidence bound (rolling mean + 2 * rolling std)
    df['upper_bound'] = df['rolling_mean'] + (2.0 * df['rolling_std'].fillna(0))
    
    fig = go.Figure()
    
    # 1. Shaded confidence band (Upper threshold limit)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['upper_bound'],
        mode='lines',
        name='2-Sigma Anomaly Limit',
        line=dict(color='rgba(239, 68, 68, 0.4)', width=1, dash='dot'),
        fill=None
    ))
    
    # 2. Plot daily crime count line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['crime_count'],
        mode='lines',
        name='Daily Crime Frequency',
        line=dict(color='#3B82F6', width=2)
    ))
    
    # 3. Plot 14-day rolling average
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rolling_mean'],
        mode='lines',
        name='14-Day Rolling Baseline',
        line=dict(color='#10B981', width=1.8, dash='dash')
    ))
    
    # 4. Highlight Z-Score anomalies (rolling threshold exceeded)
    anomalies = df[df['is_anomaly'] == True].copy()
    if not anomalies.empty:
        anomalies['hover_txt'] = anomalies.apply(
            lambda r: f"🚨 <b>Crime Spike Detected</b><br>📅 Date: {r['date'].strftime('%Y-%m-%d')}<br>📊 Crimes: <b>{r['crime_count']}</b> (Expected: {r['rolling_mean']:.1f})<br>⚡ Z-Score: <b>+{r['z_score']:.2f} σ</b>",
            axis=1
        )
        fig.add_trace(go.Scatter(
            x=anomalies['date'],
            y=anomalies['crime_count'],
            mode='markers',
            name='Statistical Anomaly Alert (Z > 2.0)',
            marker=dict(color='#EF4444', size=11, symbol='diamond', line=dict(color='#FFFFFF', width=1.5)),
            text=anomalies['hover_txt'],
            hovertemplate="%{text}<extra></extra>"
        ))
        
    fig.update_layout(
        title="<b>Daily Crime Frequency & Statistical Anomaly Spikes (Z-Score > 2.0)</b>",
        xaxis_title="Timeline Date",
        yaxis_title="Daily Crime Incidents Count",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(17, 24, 39, 0.8)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_correlation_heatmap(corr_df):
    """Correlation Bar/Heatmap with exact Pearson coefficients and p-values."""
    if corr_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Correlation Data", showarrow=False)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    df = corr_df.copy()
    df['Feature Name'] = df['feature'].str.replace('_', ' ').str.title()
    df['text_label'] = df.apply(lambda r: f"r = {r['pearson_r']:+.2f} (p={r['p_value']:.3f})", axis=1)
    
    fig = px.bar(
        df,
        x='pearson_r',
        y='Feature Name',
        orientation='h',
        color='pearson_r',
        color_continuous_scale='Purples',
        text='text_label',
        range_color=[-1, 1],
        labels={'pearson_r': 'Pearson Correlation (r)', 'Feature Name': 'Socio-economic Factor'},
        title="<b>Socio-Economic Factors Correlation to Local Crime Density</b>"
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320
    )
    fig.update_yaxes(categoryorder="total ascending")
    return fig

def create_correlation_scatter(crimes_df, districts_df, feature):
    """Scatter plot with OLS trendline regression between a district socio-economic feature and crime frequency."""
    if crimes_df.empty or districts_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Data Available", showarrow=False)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    crime_counts = crimes_df.groupby('district_id').size().reset_index(name='total_crimes')
    merged = pd.merge(districts_df, crime_counts, left_on='id', right_on='district_id', how='left').fillna({'total_crimes': 0})
    
    feat_title = feature.replace('_', ' ').title()
    
    fig = px.scatter(
        merged,
        x=feature,
        y='total_crimes',
        text='name',
        trendline='ols',
        hover_data={'name': True, feature: ':.2f', 'total_crimes': True, 'population_density': True},
        labels={feature: feat_title, 'total_crimes': 'Total Crime Incidents Logged'},
        title=f"<b>OLS Trendline: {feat_title} vs. Crime Frequency</b>"
    )
    
    fig.update_traces(textposition='top center', marker=dict(size=14, color='#10B981', line=dict(width=1.5, color='#FFFFFF')))
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320
    )
    return fig
