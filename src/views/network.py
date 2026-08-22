"""
Criminal Network Analysis View Module
"""
import streamlit as st
import pandas as pd
import database
import visualizations

def render_network_view(df_suspects, df_connections, df_crimes):
    st.markdown("## 🕸️ Criminal Social Network & Associate Linkage")
    st.write("Perform criminal network link analysis across gangs, accomplices, and co-arrestees. Utilize graph centrality algorithms to identify syndicate leaders and cross-group bridge figures.")
    
    col_f1, col_f2 = st.columns([1.5, 2])
    with col_f1:
        gang_options = ["All Gangs"] + sorted([g for g in df_suspects['gang_affiliation'].unique() if g != "None"])
        sel_gang_net = st.selectbox("Filter Network by Syndicate / Gang", gang_options, key="sel_gang_network")
    with col_f2:
        st.markdown("<div style='padding-top: 25px; color: #9CA3AF; font-size: 0.85rem;'>💡 <b>Tip</b>: Use mouse scroll to zoom in/out of the network graph. Drag nodes or background to pan. Click on legend items to toggle specific link types (Gang Member, Accomplice, Co-arrestee, Relative).</div>", unsafe_allow_html=True)
        
    fig_network, centrality_metrics = visualizations.create_network_graph(df_suspects, df_connections, selected_gang=sel_gang_net)
    
    if centrality_metrics:
        cent_df = pd.DataFrame.from_dict(centrality_metrics, orient='index')
        top_hub_name = cent_df.sort_values(by='degree_centrality', ascending=False).iloc[0]['name'] if not cent_df.empty else "N/A"
        top_bridge_name = cent_df.sort_values(by='betweenness_centrality', ascending=False).iloc[0]['name'] if not cent_df.empty else "N/A"
        
        kpi_n1, kpi_n2, kpi_n3, kpi_n4 = st.columns(4)
        with kpi_n1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Network Suspects</div><div class="kpi-value">{len(cent_df)}</div></div>""", unsafe_allow_html=True)
        with kpi_n2:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Links</div><div class="kpi-value">{cent_df['degree'].sum() // 2}</div></div>""", unsafe_allow_html=True)
        with kpi_n3:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Primary Gang Hub</div><div class="kpi-value" style="font-size: 1.1rem; color: #60A5FA;">{top_hub_name}</div></div>""", unsafe_allow_html=True)
        with kpi_n4:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Top Bridge Figure</div><div class="kpi-value" style="font-size: 1.1rem; color: #F59E0B;">{top_bridge_name}</div></div>""", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

    col_net1, col_net2 = st.columns([2.2, 1])
    with col_net1:
        st.plotly_chart(fig_network, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        
    with col_net2:
        st.markdown("### 🕸️ Key Network Influencers")
        st.write("Calculated via Degree Centrality (Gang Hubs) and Betweenness Centrality (Bridge Connectors).")
        
        if centrality_metrics:
            cent_sorted = cent_df.sort_values(by='degree_centrality', ascending=False).head(5)
            st.write("**Top Associate Hubs (Gang Leaders)**")
            st.dataframe(
                cent_sorted[['name', 'degree', 'degree_centrality']].rename(
                    columns={'name': 'Suspect Name', 'degree': 'Links', 'degree_centrality': 'Degree Centrality'}
                ).assign(**{'Degree Centrality': lambda x: x['Degree Centrality'].map('{:.3f}'.format)}),
                use_container_width=True,
                hide_index=True
            )
            
            bridge_sorted = cent_df.sort_values(by='betweenness_centrality', ascending=False).head(5)
            st.write("**Top Bridge Figures (Cross-Group Connectors)**")
            st.dataframe(
                bridge_sorted[['name', 'betweenness_centrality']].rename(
                    columns={'name': 'Suspect Name', 'betweenness_centrality': 'Bridge Score'}
                ).assign(**{'Bridge Score': lambda x: x['Bridge Score'].map('{:.3f}'.format)}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No central metrics calculated.")
            
    st.markdown("<hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)
    st.markdown("### 📅 Suspect Crime History Timelines")
    st.write("Select a suspect from the database to build a complete chronological profile of their crimes.")
    
    conn = database.get_connection()
    c_cursor = conn.cursor()
    c_cursor.execute("SELECT DISTINCT suspect_id FROM crimes WHERE suspect_id IS NOT NULL")
    suspect_ids_with_crimes = [row[0] for row in c_cursor.fetchall()]
    conn.close()
    
    if suspect_ids_with_crimes:
        suspects_with_crimes_df = df_suspects[df_suspects['id'].isin(suspect_ids_with_crimes)].sort_values(by='name')
        sus_options = {row['id']: f"{row['name']} (Priors: {row['priors_count']})" for _, row in suspects_with_crimes_df.iterrows()}
        selected_sus_id = st.selectbox("Select Suspect to Track", list(sus_options.keys()), format_func=lambda x: sus_options[x])
        
        if selected_sus_id:
            s_name = df_suspects[df_suspects['id'] == selected_sus_id]['name'].iloc[0]
            st.markdown(f"Highlighting **{s_name}** in the social network...")
            fig_net_highlight, _ = visualizations.create_network_graph(df_suspects, df_connections, highlight_suspect_id=selected_sus_id)
            
            col_track1, col_track2 = st.columns([1, 1])
            with col_track1:
                st.plotly_chart(fig_net_highlight, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            with col_track2:
                fig_timeline = visualizations.create_offender_timeline(selected_sus_id, df_crimes, s_name)
                st.plotly_chart(fig_timeline, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
                s_row = df_suspects[df_suspects['id'] == selected_sus_id].iloc[0]
                if st.button(f"🤖 Generate AI Officer Briefing for {s_name}", key=f"btn_ai_brief_{selected_sus_id}"):
                    sus_crimes = df_crimes[df_crimes['suspect_id'] == selected_sus_id]
                    crime_summary = ", ".join(sus_crimes['crime_type'].unique()) if not sus_crimes.empty else "No logged crime categories"
                    briefing_text = (
                        f"**CONFIDENTIAL POLICE BRIEFING — SUBJECT RECORD #{selected_sus_id}**\n\n"
                        f"• **Subject Profile**: {s_row['name']} (Age {s_row['age']}), Gang Affiliation: **{s_row['gang_affiliation']}**.\n"
                        f"• **Risk Classification**: Recidivism Risk Index of **{s_row['risk_score']:.2f}** with **{s_row['priors_count']} prior arrests**.\n"
                        f"• **Operational History**: Linked to {len(sus_crimes)} incident reports ({crime_summary}) across Pune sectors.\n"
                        f"• **Tactical Directive**: Maintain active history-sheeter surveillance, track station roll-call attendance, and monitor known gang associate links."
                    )
                    st.info(briefing_text)
    else:
        st.info("No crimes are currently linked to suspects. Go to 'Intel Entry' to link suspects to crime reports.")
