"""
Command Dashboard View Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import analytics
import visualizations

def render_dashboard_view(df_crimes, df_suspects, df_districts):
    dash_tab_live, dash_tab_ncrb = st.tabs(["📈 Live Operations (DB)", "🏛️ Pune Police Statistics (NCRB)"])
    
    with dash_tab_live:
        st.caption("ℹ️ **Operational Simulation Database**: The live metrics below are dynamically populated demo records for Pune crime pattern testing. For official historical figures, switch to the **Pune Police Statistics (NCRB)** tab.")
        
        # 1. KPI Cards Row
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        total_crimes = len(df_crimes)
        df_clustered = analytics.detect_hotspots(df_crimes, eps_km=0.5, min_samples=6)
        active_hotspots = max(0, df_clustered['hotspot_id'].nunique() - (1 if -1 in df_clustered['hotspot_id'].values else 0))
        high_risk_suspects = len(df_suspects[df_suspects['risk_score'] > 0.65])
        
        daily_stats, _ = analytics.detect_anomalies_rolling(df_crimes)
        total_anomalies = len(daily_stats[daily_stats['is_anomaly'] == True]) if not daily_stats.empty else 0
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Crime Records</div>
                <div class="kpi-value">{total_crimes:,}</div>
                <div class="kpi-trend trend-up">⚠️ In selection filters</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Hotspot Zones</div>
                <div class="kpi-value">{active_hotspots}</div>
                <div class="kpi-trend trend-down">💡 DBSCAN Clusters</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">High-Risk Suspects</div>
                <div class="kpi-value">{high_risk_suspects}</div>
                <div class="kpi-trend trend-up">🔴 Score &gt; 0.65</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Trend Alerts (Anomalies)</div>
                <div class="kpi-value">{total_anomalies}</div>
                <div class="kpi-trend trend-up">📈 Z-Score Spikes</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Main Visualization Row
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("### Crime Distribution by Category")
            if not df_crimes.empty:
                type_counts = df_crimes['crime_type'].value_counts().reset_index()
                type_counts.columns = ['Crime Type', 'Count']
                fig_pie = px.pie(
                    type_counts, 
                    values='Count', 
                    names='Crime Type', 
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(
                    margin=dict(t=30, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            else:
                st.info("No crime data fits the selected filters.")
                
        with col_chart2:
            st.markdown("### Incident Frequencies by District")
            if not df_crimes.empty:
                district_counts = df_crimes['district_name'].value_counts().reset_index()
                district_counts.columns = ['District', 'Incidents']
                fig_bar = px.bar(
                    district_counts,
                    x='Incidents',
                    y='District',
                    orientation='h',
                    color='Incidents',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(
                    margin=dict(t=30, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            else:
                st.info("No crime data fits the selected filters.")
                
        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        
        # 2.5 Patrol Resource Optimization
        st.markdown("### 🚓 Tactical Patrol Unit (PCR) Allocation Optimizer")
        st.write("Proportional risk-weighted decision-support system: optimizes $N$ active patrol vans across Pune police sectors to maximize spatial coverage and minimize emergency response latency.")
        
        col_opt_ctrl, col_opt_kpi = st.columns([1, 1.5])
        with col_opt_ctrl:
            num_vans = st.slider("Available Police Control Room (PCR) Vans", 5, 30, 14, key="slider_num_vans")
            patrol_df = analytics.optimize_patrol_allocations(df_crimes, df_districts, num_patrol_units=num_vans)
            
            if not patrol_df.empty:
                avg_response = patrol_df['expected_response_min'].mean()
                avg_coverage = patrol_df['coverage_pct'].mean()
                
                pk1, pk2 = st.columns(2)
                with pk1:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Est. Response Latency</div><div class="kpi-value" style="color: #10B981;">{avg_response:.1f} mins</div></div>""", unsafe_allow_html=True)
                with pk2:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Spatial Coverage</div><div class="kpi-value" style="color: #60A5FA;">{avg_coverage:.1f}%</div></div>""", unsafe_allow_html=True)
                    
        with col_opt_kpi:
            if not patrol_df.empty:
                fig_patrol = visualizations.create_patrol_optimization_chart(patrol_df)
                st.plotly_chart(fig_patrol, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        
        # 3. Anomaly Alerts & Details Row
        col_anomaly, col_priors = st.columns([3, 2])
        
        with col_anomaly:
            st.markdown("### 🚨 Crime Trend Anomaly Alerts")
            if not daily_stats.empty:
                active_alerts = daily_stats[daily_stats['is_anomaly'] == True].sort_values(by='date', ascending=False)
                if not active_alerts.empty:
                    st.markdown(f"Detected **{len(active_alerts)}** statistical crime spikes in history range:")
                    for _, alert in active_alerts.head(5).iterrows():
                        dt_str = alert['date'].strftime('%Y-%m-%d')
                        st.markdown(
                            f"""<div class="anomaly-alert">
                                <strong>{dt_str}</strong> - Spiked to <strong>{alert['crime_count']}</strong> crimes! 
                                (Expected 14-day rolling average: <em>{alert['rolling_mean']:.1f}</em>, Z-score: <em>{alert['z_score']:.2f}</em>)
                            </div>""", unsafe_allow_html=True
                        )
                else:
                    st.success("No active frequency anomalies detected in this range.")
            else:
                st.info("No historical daily aggregation available.")
                
        with col_priors:
            st.markdown("### 👤 High-Risk Recidivists (Repeat Offenders)")
            if not df_suspects.empty:
                repeat_offenders = df_suspects.sort_values(by='priors_count', ascending=False).head(5)
                for _, r in repeat_offenders.iterrows():
                    badge_color = "#ef4444" if r['risk_score'] > 0.75 else ("#f59e0b" if r['risk_score'] > 0.45 else "#10b981")
                    st.markdown(
                        f"""<div style="background-color: #1f2937; padding: 12px; border-radius: 8px; border: 1px solid rgba(75,85,99,0.3); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #ffffff;">{r['name']}</strong> (Age: {r['age']})<br>
                                <span style="color: #9ca3af; font-size: 0.85rem;">Gang: {r['gang_affiliation']}</span>
                            </div>
                            <div style="text-align: right;">
                                <span style="background-color: {badge_color}; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 700;">Risk: {r['risk_score']:.2f}</span><br>
                                <span style="color: #9ca3af; font-size: 0.8rem; font-weight: 600;">{r['priors_count']} Priors</span>
                            </div>
                        </div>""", unsafe_allow_html=True
                    )
            else:
                st.info("No suspect intelligence records available.")

    with dash_tab_ncrb:
        st.success("🏛️ **Official NCRB Benchmark Data**: The statistics below are compiled from official National Crime Records Bureau (NCRB) publications and Pune Police annual crime reports.")
        st.markdown("### 🏛️ Pune City Police — Official Historical Crime Statistics (NCRB)")
        st.write("Browse official data compiled from National Crime Records Bureau (NCRB) publications and Pune Police reviews showing yearly trends and solvability analytics.")

        ncrb_col1, ncrb_col2, ncrb_col3 = st.columns(3)
        with ncrb_col1:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Total Cognizable Volume (2023)</div>
                <div class="kpi-value">17,022</div>
                <div class="kpi-trend trend-up">🔺 +20.1% YoY</div>
            </div>
            """, unsafe_allow_html=True)
        with ncrb_col2:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Homicides (2025)</div>
                <div class="kpi-value">79</div>
                <div class="kpi-trend trend-down">🟢 -21.7% vs 2023</div>
            </div>
            """, unsafe_allow_html=True)
        with ncrb_col3:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-title">Pune Safety Index</div>
                <div class="kpi-value">Top 2</div>
                <div class="kpi-trend trend-down">💡 Safest Metro in India (NCRB 2022)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("#### Annual Cognizable Cases (IPC + SLL)")
            df_cog = pd.DataFrame({
                "Year": ["2021", "2022", "2023"],
                "IPC Cases": [9511, 11074, 12542],
                "SLL Cases": [3458, 3099, 4480],
                "Total Cases": [12969, 14173, 17022]
            })
            fig_cog = go.Figure()
            fig_cog.add_trace(go.Bar(x=df_cog["Year"], y=df_cog["IPC Cases"], name="IPC Cases", marker_color="#393E46"))
            fig_cog.add_trace(go.Bar(x=df_cog["Year"], y=df_cog["SLL Cases"], name="SLL Cases", marker_color="#00ADB5"))
            fig_cog.add_trace(go.Scatter(x=df_cog["Year"], y=df_cog["Total Cases"], name="Total Crime Volume", line=dict(color="#EEEEEE", width=2.5)))
            fig_cog.update_layout(
                barmode='stack',
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_cog, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with row1_col2:
            st.markdown("#### Violent Crime Category Trends (2021–2025)")
            df_violent = pd.DataFrame({
                "Year": ["2021", "2022", "2023", "2024", "2025"],
                "Murder": [100, 104, 101, 93, 79],
                "Attempt to Murder": [296, 280, 240, 240, 179],
                "Assault (Hurt)": [938, 1060, 1362, 1515, 1453]
            })
            fig_violent = go.Figure()
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Murder"], name="Murders", line=dict(color="#00ADB5", width=2)))
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Attempt to Murder"], name="Attempt to Murder", line=dict(color="#EEEEEE", width=2, dash="dash")))
            fig_violent.add_trace(go.Scatter(x=df_violent["Year"], y=df_violent["Assault (Hurt)"], name="Non-fatal Assaults", line=dict(color="#393E46", width=2)))
            fig_violent.update_layout(
                margin=dict(t=30, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_violent, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("#### Cybercrime Offenses (Rising Trends)")
            df_cyber = pd.DataFrame({"Year": ["2021", "2022", "2023"], "Cases": [225, 357, 487]})
            fig_cyber = px.bar(df_cyber, x="Year", y="Cases", text="Cases", color_discrete_sequence=["#00ADB5"])
            fig_cyber.update_layout(margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig_cyber.update_traces(textposition='outside')
            st.plotly_chart(fig_cyber, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with row2_col2:
            st.markdown("#### Vulnerable Demographics Trends")
            df_vuln = pd.DataFrame({"Year": ["2021", "2022", "2023"], "Crimes Against Women": [1616, 2074, 2550], "Crimes Against Children": [835, 732, 1234]})
            fig_vuln = go.Figure()
            fig_vuln.add_trace(go.Bar(x=df_vuln["Year"], y=df_vuln["Crimes Against Women"], name="Against Women", marker_color="#393E46"))
            fig_vuln.add_trace(go.Bar(x=df_vuln["Year"], y=df_vuln["Crimes Against Children"], name="Against Children", marker_color="#00ADB5"))
            fig_vuln.update_layout(barmode='group', margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_vuln, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        st.markdown("<hr style='border-top: 1px solid rgba(0, 173, 181, 0.2);'>", unsafe_allow_html=True)
        st.markdown("### Pimpri-Chinchwad Police Commissionerate (PCPC) — 2025 Annual Crime Report")
        pc_col1, pc_col2 = st.columns(2)
        with pc_col1:
            st.markdown("#### PCPC Crime Solver Rates (2025)")
            df_pcpc = pd.DataFrame({
                "Category": ["Dacoity", "Robbery", "Chain Snatching", "Burglary", "Vehicle Theft", "Overall Property", "Murder", "Cybercrime"],
                "Cases": [20, 182, 75, 285, 960, 2129, 63, 269],
                "Solved %": [100.0, 87.0, 83.0, 51.0, 39.0, 47.0, 95.0, 35.0]
            })
            fig_pcpc = px.bar(df_pcpc, x="Solved %", y="Category", orientation="h", color="Cases", color_continuous_scale="Blues", labels={"Category": "Crime Type", "Solved %": "Detection Rate (%)", "Cases": "Cases Registered"}, title="PCPC Case Solved / Detection Rates")
            fig_pcpc.update_layout(margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
            st.plotly_chart(fig_pcpc, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with pc_col2:
            st.markdown("#### Preventive & Legal Actions (PCPC 2025)")
            df_prev = pd.DataFrame({
                "Action Type": ["MPDA Act", "MCOCA Act", "Externment Actions", "BNS 126 (Wrongful Restraint)", "BNS 129 (Criminal Force)", "Total Actions"],
                "Cases Count": [35, 213, 368, 5474, 3243, 12295]
            })
            st.dataframe(df_prev.rename(columns={"Action Type": "Action / Statute Type", "Cases Count": "Total Preventative Actions Logged"}), use_container_width=True, hide_index=True)
            st.markdown("""
            > **MCOCA (Maharashtra Control of Organised Crime Act)** is actively invoked to curb syndicate activity, showing 213 actions in 2025. 
            > **Externment** orders were executed on 368 repeat offenders, expelling them from city limits to maintain law and order.
            """)
