import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

# Set default theme to dark
px.defaults.template = "plotly_dark"

def create_geospatial_map(crimes_df, show_hotspots=False, selected_hotspot_id=None):
    """
    Generate an interactive Mapbox map of crimes.
    If show_hotspots=True, color-code nodes by DBSCAN cluster IDs.
    """
    if crimes_df.empty:
        # Return empty map centered on Pune
        fig = px.scatter_mapbox(lat=[18.5204], lon=[73.8567], zoom=11.5)
        fig.update_layout(mapbox_style="carto-darkmatter")
        return fig
        
    df = crimes_df.copy()
    
    # Pre-format dates for hover
    df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    
    centroid_lats = []
    centroid_lons = []
    centroid_texts = []
    
    if show_hotspots and 'hotspot_id' in df.columns:
        # Separate noise (-1) from hotspots
        # Convert hotspot_id to categorical string for discrete colors
        df['Hotspot Type'] = df['hotspot_id'].apply(lambda x: "Noise / Isolated" if x == -1 else f"Hotspot Zone {x}")
        
        # Filter if a specific hotspot is selected
        if selected_hotspot_id is not None:
            df = df[df['hotspot_id'] == selected_hotspot_id]
            
        color_col = 'Hotspot Type'
        # Generate color map
        unique_hotspots = sorted(df['hotspot_id'].unique())
        color_discrete_map = {"Noise / Isolated": "#6b7280"} # Gray for noise
        colors = px.colors.qualitative.Safe
        color_idx = 0
        for hid in unique_hotspots:
            if hid != -1:
                color_discrete_map[f"Hotspot Zone {hid}"] = colors[color_idx % len(colors)]
                color_idx += 1
                
        # Calculate centroids of hotspots for overlays
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
                centroid_texts.append(f"🔴 {c_name} ({c_count} cases)")
                
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            color=color_col,
            color_discrete_map=color_discrete_map,
            size=df['severity'].map({'Low': 6, 'Medium': 10, 'High': 15}),
            hover_name='crime_type',
            hover_data={
                'date_str': True,
                'severity': True,
                'district_name': True,
                'status': True,
                'latitude': False,
                'longitude': False,
                'Hotspot Type': True
            },
            zoom=12,
            title="Geospatial Intelligence Map - DBSCAN Hotspots"
        )
    else:
        # Standard crime map colored by Crime Type or Severity
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            color='crime_type',
            size=df['severity'].map({'Low': 6, 'Medium': 10, 'High': 15}),
            hover_name='crime_type',
            hover_data={
                'date_str': True,
                'severity': True,
                'district_name': True,
                'status': True,
                'latitude': False,
                'longitude': False
            },
            zoom=12,
            title="Geospatial Intelligence Map - Incident Distribution"
        )
        
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=11.5,
        mapbox_center={"lat": 18.5204, "lon": 73.8567},
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(75, 85, 99, 0.4)",
            borderwidth=1
        )
    )
    
    # Overlay active hotspot centroids with text labels directly on map
    if show_hotspots and centroid_lats:
        fig.add_trace(go.Scattermapbox(
            lat=centroid_lats,
            lon=centroid_lons,
            mode='markers+text',
            marker=dict(size=14, color='#3B82F6', opacity=0.95),
            text=centroid_texts,
            textposition='top right',
            textfont=dict(size=11, color='#EEEEEE', family='Outfit, Inter, sans-serif'),
            hoverinfo='text',
            name='Active Hotspots Info'
        ))
        
    return fig

def create_density_map(crimes_df):
    """Density Heatmap of crimes."""
    if crimes_df.empty:
        fig = px.scatter_mapbox(lat=[18.5204], lon=[73.8567], zoom=11.5)
        fig.update_layout(mapbox_style="carto-darkmatter")
        return fig
        
    fig = px.density_mapbox(
        crimes_df, 
        lat='latitude', 
        lon='longitude', 
        radius=12,
        zoom=11.5,
        mapbox_style="carto-darkmatter",
        title="Crime Density Heatmap"
    )
    fig.update_layout(
        mapbox_center={"lat": 18.5204, "lon": 73.8567},
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_network_graph(suspects_df, connections_df, highlight_suspect_id=None):
    """
    Build and render criminal network graph using NetworkX and Plotly.
    Node size reflects Degree Centrality (connections count).
    Node color reflects ML Suspect Risk Score.
    """
    if suspects_df.empty or connections_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Network Data Available", showarrow=False, font=dict(size=18))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig, {}
        
    # --- Performance Optimization ---
    # With 2000+ suspects, rendering all in browser freezes it. We filter to connected suspects.
    if highlight_suspect_id is not None:
        # Highlight: Show target suspect + neighbors
        neighbors = {int(highlight_suspect_id)}
        for _, row in connections_df.iterrows():
            sa, sb = int(row['suspect_a']), int(row['suspect_b'])
            if sa == highlight_suspect_id:
                neighbors.add(sb)
            elif sb == highlight_suspect_id:
                neighbors.add(sa)
        
        filtered_suspects = suspects_df[suspects_df['id'].isin(neighbors)]
        filtered_connections = connections_df[
            connections_df['suspect_a'].isin(neighbors) & 
            connections_df['suspect_b'].isin(neighbors)
        ]
    else:
        # No Highlight: Show top 80 most connected suspects to keep network readable & responsive
        degrees = {}
        for _, row in connections_df.iterrows():
            sa, sb = int(row['suspect_a']), int(row['suspect_b'])
            degrees[sa] = degrees.get(sa, 0) + 1
            degrees[sb] = degrees.get(sb, 0) + 1
            
        top_connected = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:80]
        top_connected_set = set(top_connected)
        
        filtered_suspects = suspects_df[suspects_df['id'].isin(top_connected_set)]
        filtered_connections = connections_df[
            connections_df['suspect_a'].isin(top_connected_set) & 
            connections_df['suspect_b'].isin(top_connected_set)
        ]

    # Build NetworkX graph
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in filtered_suspects.iterrows():
        G.add_node(
            int(row['id']),
            name=row['name'],
            age=int(row['age']),
            gang=row['gang_affiliation'],
            risk=float(row['risk_score']),
            priors=int(row['priors_count'])
        )
        
    # Add edges
    for _, row in filtered_connections.iterrows():
        G.add_edge(
            int(row['suspect_a']),
            int(row['suspect_b']),
            relation=row['relation_type'],
            weight=int(row['strength'])
        )

        
    # Compute Centrality Metrics
    deg_centrality = nx.degree_centrality(G)
    bet_centrality = nx.betweenness_centrality(G)
    
    # Save metrics back to node attributes
    for node in G.nodes():
        G.nodes[node]['deg_cent'] = deg_centrality[node]
        G.nodes[node]['bet_cent'] = bet_centrality[node]
        
    # Generate node positions using spring layout
    pos = nx.spring_layout(G, k=0.45, seed=42)
    
    # Extract Edge Lines
    edge_x = []
    edge_y = []
    edge_text = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.2, color='rgba(156, 163, 175, 0.45)'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Extract Nodes
    node_x = []
    node_y = []
    node_color = []
    node_size = []
    node_text = []
    node_border_width = []
    node_border_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        attrs = G.nodes[node]
        node_color.append(attrs['risk'])
        
        # Size based on degree centrality (scaled for visual size 12 to 38)
        size = 12 + deg_centrality[node] * 70
        node_size.append(size)
        
        # Hover info
        hover_txt = (
            f"<b>Name:</b> {attrs['name']}<br>"
            f"<b>Gang:</b> {attrs['gang']}<br>"
            f"<b>Age:</b> {attrs['age']}<br>"
            f"<b>Priors:</b> {attrs['priors']}<br>"
            f"<b>Risk Score:</b> {attrs['risk']:.2f}<br>"
            f"<b>Connections Count:</b> {G.degree(node)}<br>"
            f"<b>Degree Centrality:</b> {deg_centrality[node]:.3f}<br>"
            f"<b>Bridge Centrality (Betweenness):</b> {bet_centrality[node]:.3f}"
        )
        node_text.append(hover_txt)
        
        # Highlight selected suspect
        if highlight_suspect_id is not None and node == highlight_suspect_id:
            node_border_width.append(3)
            node_border_color.append("#10B981") # Bright Emerald green
        else:
            node_border_width.append(1)
            node_border_color.append("#4B5563") # Gray
            
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='Viridis', # Indigo-Yellow representing low to high risk
            reversescale=False,
            color=node_color,
            size=node_size,
            colorbar=dict(
                title='ML Risk Score',
                thickness=15,
                x=1.02,
                len=0.7,
                ypad=0
            ),
            line=dict(color=node_border_color, width=node_border_width)
        )
    )
    
    # Create network figure
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title=dict(text='<b>Criminal Network & Associates Link Analysis</b>', font=dict(size=16)),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                 )
    )
    
    # Store metrics to return
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

def create_anomaly_chart(daily_counts):
    """
    Chart crime timeline with rolling stats and anomalies highlighted.
    """
    if daily_counts.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for anomalies.", showarrow=False)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    fig = go.Figure()
    
    # 1. Plot crime count line
    fig.add_trace(go.Scatter(
        x=daily_counts['date'],
        y=daily_counts['crime_count'],
        mode='lines',
        name='Daily Crimes',
        line=dict(color='#3B82F6', width=1.5)
    ))
    
    # 2. Plot rolling mean
    fig.add_trace(go.Scatter(
        x=daily_counts['date'],
        y=daily_counts['rolling_mean'],
        mode='lines',
        name='14-Day Rolling Avg',
        line=dict(color='#10B981', width=1.2, dash='dash')
    ))
    
    # 3. Highlight Z-Score anomalies (rolling threshold exceeded)
    anomalies = daily_counts[daily_counts['is_anomaly'] == True]
    fig.add_trace(go.Scatter(
        x=anomalies['date'],
        y=anomalies['crime_count'],
        mode='markers',
        name='Trend Alerts (Anomaly)',
        marker=dict(color='#EF4444', size=8, symbol='circle')
    ))
    
    fig.update_layout(
        title="<b>Crime Frequency Trend & Anomaly Alerts (z-score > 2.0)</b>",
        xaxis_title="Date",
        yaxis_title="Daily Crime Count",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_correlation_heatmap(corr_df):
    """Heatmap showing socio-economic correlation coefficients."""
    if corr_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Correlation Data", showarrow=False)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    # Standardize names for display
    corr_df = corr_df.copy()
    corr_df['Feature Name'] = corr_df['feature'].str.replace('_', ' ').str.title()
    
    fig = px.bar(
        corr_df,
        x='pearson_r',
        y='Feature Name',
        orientation='h',
        color='pearson_r',
        color_continuous_scale='RdBu',
        range_color=[-1, 1],
        labels={'pearson_r': 'Pearson Correlation (r)', 'Feature Name': 'Socio-economic Indicator'},
        title="Socio-economic Correlation to Total Crimes"
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300
    )
    fig.update_yaxes(categoryorder="total ascending")
    return fig

def create_correlation_scatter(crimes_df, districts_df, feature):
    """Scatter plot showing crimes vs a specific feature across districts with a trendline."""
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
        labels={feature: feat_title, 'total_crimes': 'Total Crime Count'},
        title=f"Correlation: {feat_title} vs. Crime Frequency"
    )
    
    fig.update_traces(textposition='top center', marker=dict(size=12, color='#10B981'))
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320
    )
    return fig
