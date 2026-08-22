"""
AI Predictive Models View Module
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import analytics
import visualizations

def render_predictions_view(df_crimes, df_suspects, df_districts, district_names, crime_types_list):
    st.markdown("## 🧠 AI/ML Forecasting & Scientific Predictive Intelligence")
    st.write("Production-grade machine learning predictive suite for police commanders: evaluate incident severity, forecast suspect recidivism risk, generate 30-day forward time-series crime projections, analyze socio-economic correlations, and detect rolling anomaly spikes.")
    
    tab_predict, tab_suspect, tab_forecast, tab_socio, tab_anomaly = st.tabs([
        "🔮 Incident Severity Classifier",
        "👤 Recidivism Risk (Suspects)",
        "📈 30-Day Forward Forecasting",
        "📊 Socio-Economic Correlations",
        "🚨 Rolling Anomaly Detection"
    ])
    
    with tab_predict:
        st.markdown("### Predict Potential Crime Severity")
        st.write("Random Forest Classifier trained on historical crime logs using spatio-temporal features, district socio-economics, and category indicators with 80/20 train/test evaluation and 5-fold cross-validation.")
        
        model_dict, train_msg = analytics.train_severity_predictor(df_crimes)
        
        if model_dict:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Out-of-Sample Accuracy</div><div class="kpi-value" style="color: #34d399;">{model_dict['accuracy']*100:.1f}%</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Weighted F1-Score</div><div class="kpi-value" style="color: #60a5fa;">{model_dict['f1_score']:.3f}</div></div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">5-Fold CV Accuracy</div><div class="kpi-value" style="color: #fbbf24;">{model_dict['cv_mean']*100:.1f}% ± {model_dict['cv_std']*100:.1f}%</div></div>""", unsafe_allow_html=True)
            with m4:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Dataset Size</div><div class="kpi-value" style="font-size: 1.1rem; color: #a855f7;">{len(df_crimes):,} Incident Logs</div></div>""", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                st.markdown("#### Input Incident Conditions")
                in_district = st.selectbox("Incident Area / Location", district_names, key="pred_district_sel")
                in_type = st.selectbox("Crime Category", crime_types_list, key="pred_type_sel")
                in_hour = st.slider("Hour of Day (24h Clock)", 0, 23, 12, key="pred_hour_slider")
                in_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="pred_day_sel")
                
                day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                day_idx = day_map[in_day]
                dist_row = df_districts[df_districts['name'] == in_district].iloc[0]
                predict_btn = st.button("Calculate Severity Risk", key="btn_calc_severity")
                
            with col_in2:
                st.markdown("#### Prediction Output & Tactical Advisory")
                if predict_btn:
                    input_data = {
                        "district_name": in_district,
                        "crime_type": in_type,
                        "hour": in_hour,
                        "day_of_week": day_idx,
                        "month": datetime.now().month,
                        "is_weekend": 1.0 if day_idx >= 5 else 0.0,
                        "unemployment_rate": dist_row['unemployment_rate'],
                        "poverty_index": dist_row['poverty_index'],
                        "median_income": dist_row['median_income'],
                        "education_index": dist_row['education_index'],
                        "population_density": dist_row['population_density']
                    }
                    
                    pred_class, class_probs = analytics.predict_incident_severity(model_dict, input_data)
                    color_map = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"}
                    bg_color = color_map[pred_class]
                    
                    st.markdown(
                        f"""<div style="background-color: {bg_color}; color: white; padding: 18px; border-radius: 10px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                            <div style="font-size: 0.85rem; text-transform: uppercase; font-weight: 600; opacity: 0.9;">Predicted Severity Classification</div>
                            <h3 style="margin: 5px 0 0 0; text-transform: uppercase; font-size: 1.8rem; font-weight: 800;">{pred_class} SEVERITY</h3>
                        </div>""", unsafe_allow_html=True
                    )
                    
                    st.write("**Model Confidence Breakdown:**")
                    for cls, prob in class_probs.items():
                        st.progress(float(prob), text=f"{cls} Severity Probability: {prob*100:.1f}%")
                        
                    st.markdown("---")
                    st.markdown("##### 🛡️ Tactical Police Advisory")
                    if pred_class == "High":
                        st.error("🚨 **HIGH SEVERITY DIRECTIVE**: Dispatch Mobile Patrol (PCR) Van immediately. Alert Station House Officer (SHO) and Divisional ACP. Monitor local CCTV feeds in real time.")
                    elif pred_class == "Medium":
                        st.warning("🟡 **MEDIUM SEVERITY DIRECTIVE**: Increase beat constable patrolling in the sector. Schedule random vehicle nakabandi checks during specified hour range.")
                    else:
                        st.success("🟢 **ROUTINE DIRECTIVE**: Log incident entry and assign standard beat constable coverage.")
                        
            st.markdown("<br><hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)
            col_diag1, col_diag2 = st.columns([1.2, 1])
            with col_diag1:
                st.markdown("#### Random Forest Feature Importance Analysis")
                feat_imp = model_dict['feature_importance'].head(8).reset_index()
                feat_imp.columns = ['Feature', 'Importance']
                feat_imp['Feature'] = feat_imp['Feature'].str.replace('dist_', 'District: ').str.replace('type_', 'Type: ').str.replace('_', ' ').str.title()
                fig_imp = px.bar(feat_imp, x='Importance', y='Feature', orientation='h', color='Importance', color_continuous_scale='Purples')
                fig_imp.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                fig_imp.update_yaxes(categoryorder="total ascending")
                st.plotly_chart(fig_imp, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                
            with col_diag2:
                st.markdown("#### Model Confusion Matrix Diagnostics")
                fig_cm = visualizations.create_confusion_matrix_chart(model_dict['confusion_matrix'], model_dict['classes'])
                st.plotly_chart(fig_cm, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
        else:
            st.warning(train_msg)
            
    with tab_suspect:
        st.markdown("### Suspect Recidivism Risk Forecaster")
        st.write("Random Forest Regressor evaluating suspect demographic & arrest history to compute a **Recidivism Risk Index**.")
        
        sus_model_dict, sus_msg = analytics.train_recidivism_predictor(df_suspects)
        if sus_model_dict:
            sm1, sm2, sm3, sm4 = st.columns(4)
            with sm1:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Model R² Score</div><div class="kpi-value" style="color: #34d399;">{sus_model_dict['r2']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm2:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Mean Absolute Error (MAE)</div><div class="kpi-value" style="color: #60a5fa;">{sus_model_dict['mae']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm3:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">RMSE Metric</div><div class="kpi-value" style="color: #fbbf24;">{sus_model_dict['rmse']:.3f}</div></div>""", unsafe_allow_html=True)
            with sm4:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">5-Fold CV R² Mean</div><div class="kpi-value" style="color: #a855f7;">{sus_model_dict['cv_r2_mean']:.3f}</div></div>""", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            col_sus1, col_sus2 = st.columns([1, 1.2])
            with col_sus1:
                st.markdown("#### Input Suspect Profile")
                s_age = st.slider("Suspect Age", 18, 90, 30, key="sus_age_slider")
                s_priors = st.number_input("Prior Offenses (Arrests)", min_value=0, max_value=50, value=2, key="sus_priors_input")
                s_gang = st.selectbox("Gang Affiliation Status", ["None", "Pune Local Boys", "Shivaji Nagar Syndicate", "Koregaon Park Cartel", "Hinjawadi Hackers", "D-Company Gang", "Chhota Rajan Gang"], key="sus_gang_sel")
                calc_sus = st.button("Evaluate Recidivism Risk Index", key="btn_eval_recidivism")
                
            with col_sus2:
                st.markdown("#### Evaluated Risk Gauge & Police Directive")
                if calc_sus:
                    pred_risk = analytics.predict_suspect_risk(sus_model_dict, s_age, s_priors, s_gang)
                    fig_gauge = visualizations.create_recidivism_gauge_chart(pred_risk)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                    higher_count = len(df_suspects[df_suspects['risk_score'] > pred_risk])
                    total_sus = len(df_suspects)
                    pct = (higher_count / total_sus) * 100.0
                    st.caption(f"📊 **Database Percentile**: This profile risks higher than **{100.0 - pct:.1f}%** of suspects in the Pune Crime Registry.")
                    
                    st.markdown("##### 👮 Police Actionable Directive")
                    if pred_risk > 0.65:
                        st.error("🚨 **CRITICAL SURVEILLANCE DIRECTIVE**: High Recidivist Risk Index (> 0.65). List under History-Sheeter Register, initiate electronic & physical surveillance, and evaluate CrPC Sec 110 preventive action.")
                    elif pred_risk > 0.35:
                        st.warning("🟡 **ELEVATED MONITORING DIRECTIVE**: Moderate Recidivist Risk Index (0.35 - 0.65). Require bi-weekly Police Station Attendance roll-call and verify local employment.")
                    else:
                        st.success("🟢 **ROUTINE RECORD DIRECTIVE**: Low Recidivist Risk Index (< 0.35). Maintain standard station records; no active surveillance required.")
        else:
            st.warning(sus_msg)
            
    with tab_forecast:
        st.markdown("### 📈 30-Day Time-Series Crime Forecasting")
        st.write("Predict future daily crime incident volumes across Pune using lag-based regression time-series forecasting with **95% Confidence Intervals**.")
        hist_df, forecast_df = analytics.forecast_future_crimes(df_crimes, days_to_forecast=30)
        if not forecast_df.empty:
            fig_fc = visualizations.create_forecast_chart(hist_df, forecast_df)
            st.plotly_chart(fig_fc, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            st.markdown("#### 📅 30-Day Projected Incident Surge Register")
            st.dataframe(
                forecast_df[['date', 'predicted_count', 'lower_ci', 'upper_ci']].rename(
                    columns={'date': 'Forecast Date', 'predicted_count': 'Projected Daily Crimes', 'lower_ci': 'Lower 95% Bound', 'upper_ci': 'Upper 95% Bound'}
                ).assign(
                    **{
                        'Forecast Date': lambda x: pd.to_datetime(x['Forecast Date']).dt.strftime('%Y-%m-%d'),
                        'Projected Daily Crimes': lambda x: x['Projected Daily Crimes'].map('{:.1f}'.format),
                        'Lower 95% Bound': lambda x: x['Lower 95% Bound'].map('{:.1f}'.format),
                        'Upper 95% Bound': lambda x: x['Upper 95% Bound'].map('{:.1f}'.format)
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Insufficient historical crime log timeline to generate 30-day forecast.")
            
    with tab_socio:
        st.markdown("### Socio-Economic Correlation Matrix")
        st.write("Examine statistical correlations between a district's socio-economic profiles (unemployment, poverty, income, education, density) and the total occurrences of crimes.")
        corr_df = analytics.calculate_socioeconomic_correlations(df_crimes, df_districts)
        if not corr_df.empty:
            col_sc1, col_sc2 = st.columns([1, 1])
            with col_sc1:
                fig_heatmap = visualizations.create_correlation_heatmap(corr_df)
                st.plotly_chart(fig_heatmap, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            with col_sc2:
                feat_opt = corr_df['feature'].tolist()
                feat_labels = {f: f.replace('_', ' ').title() for f in feat_opt}
                sel_feat = st.selectbox("Select Variable for Trendline Regression", feat_opt, format_func=lambda x: feat_labels[x], key="sel_corr_feat")
                fig_scatter = visualizations.create_correlation_scatter(df_crimes, df_districts, sel_feat)
                st.plotly_chart(fig_scatter, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                
            st.markdown("#### 📐 Statistical Correlation Coefficients (Pearson r & Spearman ρ)")
            display_corr = corr_df.copy()
            if 'feature' in display_corr.columns:
                display_corr['feature'] = display_corr['feature'].astype(str).str.replace('_', ' ').str.title()
            if 'pearson_r' in display_corr.columns:
                display_corr['pearson_r'] = display_corr['pearson_r'].map('{:+.3f}'.format)
            if 'p_value' in display_corr.columns:
                display_corr['p_value'] = display_corr['p_value'].map('{:.4f}'.format)
            if 'spearman_rho' in display_corr.columns:
                display_corr['spearman_rho'] = display_corr['spearman_rho'].map('{:+.3f}'.format)
            if 'spearman_p' in display_corr.columns:
                display_corr['spearman_p'] = display_corr['spearman_p'].map('{:.4f}'.format)

            display_corr = display_corr.rename(columns={
                'feature': 'Socio-Economic Feature',
                'pearson_r': 'Pearson Correlation (r)',
                'p_value': 'Pearson p-value',
                'spearman_rho': 'Spearman Rank (ρ)',
                'spearman_p': 'Spearman p-value'
            })
            st.dataframe(display_corr, use_container_width=True, hide_index=True)
        else:
            st.info("No correlation data available.")
            
    with tab_anomaly:
        st.markdown("### Historical Timeline & Dual Anomaly Detection")
        st.write("Combines 14-day rolling statistical Z-score thresholding with multidimensional **Isolation Forest ML** anomaly detection on daily crime logs.")
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            sel_window = st.slider("Rolling Baseline Window (Days)", 7, 30, 14, key="slider_anomaly_window")
        with col_an2:
            sel_z_thresh = st.slider("Z-Score Anomaly Threshold (σ)", 1.5, 3.0, 2.0, step=0.1, key="slider_z_thresh")
            
        daily_stats, df_pivot = analytics.detect_anomalies_rolling(df_crimes, window_days=sel_window, threshold_z=sel_z_thresh)
        if not daily_stats.empty:
            fig_anomaly = visualizations.create_anomaly_chart(daily_stats)
            st.plotly_chart(fig_anomaly, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            anomalies_only = daily_stats[daily_stats['is_anomaly'] == True].sort_values(by='date', ascending=False)
            if not anomalies_only.empty:
                st.markdown("#### 🚨 Historical Crime Anomaly Surge Register")
                st.dataframe(
                    anomalies_only[['date', 'crime_count', 'rolling_mean', 'z_score', 'iso_anomaly']].rename(
                        columns={
                            'date': 'Anomaly Date',
                            'crime_count': 'Actual Incident Count',
                            'rolling_mean': f'Expected {sel_window}-Day Baseline',
                            'z_score': 'Statistical Z-Score (σ)',
                            'iso_anomaly': 'Isolation Forest ML Outlier'
                        }
                    ).assign(
                        **{
                            'Anomaly Date': lambda x: pd.to_datetime(x['Anomaly Date']).dt.strftime('%Y-%m-%d'),
                            'Statistical Z-Score (σ)': lambda x: x['Statistical Z-Score (σ)'].map('{:+.2f} σ'.format),
                            'Isolation Forest ML Outlier': lambda x: x['Isolation Forest ML Outlier'].map(lambda v: '🚨 Confirmed Outlier' if v else '⚪ Baseline')
                        }
                    ),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No historical trends to show.")
