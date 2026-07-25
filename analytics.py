import pandas as pd
import numpy as np
import streamlit as st
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import scipy.stats as stats

def detect_hotspots(df, eps_km=0.5, min_samples=5):
    """
    Cluster crime incidents using DBSCAN to identify spatial hotspots.
    eps_km = 0.5 roughly corresponds to 0.0045 degrees.
    """
    if df.empty or len(df) < min_samples:
        return df.assign(hotspot_id=-1)
    
    eps_degrees = eps_km * 0.009
    coords = df[['latitude', 'longitude']].values
    db = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit(coords)
    
    return df.assign(hotspot_id=db.labels_)

@st.cache_data(show_spinner=False)
def train_severity_predictor(crimes_df):
    """
    Train a Random Forest Classifier to predict the severity of a crime incident.
    Includes 80/20 train/test split, balanced class weights, 5-fold cross-validation,
    and out-of-sample confusion matrix computation.
    """
    if crimes_df.empty or len(crimes_df) < 50:
        return None, "Not enough data to train severity model."
    
    df = crimes_df.copy()
    
    # Feature engineering: temporal indicators
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(float)
    df['night_time_flag'] = df['hour'].isin([22, 23, 0, 1, 2, 3, 4, 5]).astype(float)
    
    # Numerical features
    features_num = df[[
        'hour', 'day_of_week', 'month', 'is_weekend', 'night_time_flag',
        'unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density'
    ]].copy()
    
    # Categorical features - One Hot Encode
    df_district = pd.get_dummies(df['district_name'], prefix='dist', dtype=float)
    df_type = pd.get_dummies(df['crime_type'], prefix='type', dtype=float)
    
    X = pd.concat([features_num, df_district, df_type], axis=1).fillna(0)
    
    # Target label encoding
    le = LabelEncoder()
    y = le.fit_transform(df['severity']) # e.g. High, Medium, Low
    
    if len(np.unique(y)) < 2:
        return None, "Insufficient severity diversity to train model."
        
    # 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train Random Forest Classifier with balanced class weights
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    # Evaluate Out-of-Sample Predictions
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    cm = confusion_matrix(y_test, y_pred)
    
    # 5-Fold Cross-Validation Scores
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    
    # Feature Importance
    importance = model.feature_importances_
    feat_importance = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    
    return {
        "model": model,
        "feature_cols": list(X.columns),
        "label_encoder": le,
        "feature_importance": feat_importance,
        "accuracy": float(acc),
        "f1_score": float(f1),
        "cv_mean": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "cv_scores": cv_scores,
        "confusion_matrix": cm,
        "classes": list(le.classes_)
    }, "Model trained successfully."

def predict_incident_severity(model_dict, input_data):
    """
    Predict severity for an incoming crime profile.
    input_data should be a dict containing district_name, crime_type, hour, day_of_week, and socio-economic variables.
    """
    model = model_dict["model"]
    feature_cols = model_dict["feature_cols"]
    le = model_dict["label_encoder"]
    
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    
    # Fill in numerical inputs
    num_fields = [
        'hour', 'day_of_week', 'month', 'is_weekend', 'night_time_flag',
        'unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density'
    ]
    for col in num_fields:
        if col in input_data:
            row.loc[0, col] = float(input_data[col])
            
    # Set one-hot columns
    dist_col = f"dist_{input_data.get('district_name')}"
    type_col = f"type_{input_data.get('crime_type')}"
    
    if dist_col in row.columns:
        row.loc[0, dist_col] = 1.0
    if type_col in row.columns:
        row.loc[0, type_col] = 1.0
        
    prob = model.predict_proba(row)[0]
    pred_idx = np.argmax(prob)
    pred_class = le.inverse_transform([pred_idx])[0]
    
    class_probs = dict(zip(le.classes_, prob))
    return pred_class, class_probs

@st.cache_data(show_spinner=False)
def train_recidivism_predictor(suspects_df):
    """
    Train a Random Forest Regressor to predict suspect risk scores.
    Includes 80/20 train/test split, R², MAE, RMSE, and 5-fold cross-validation.
    """
    if suspects_df.empty or len(suspects_df) < 15:
        return None, "Not enough suspects to train recidivism model."
        
    df = suspects_df.copy()
    
    # Features
    X_num = df[['age', 'priors_count']].copy()
    X_gang = pd.get_dummies(df['gang_affiliation'], prefix='gang', dtype=float)
    X = pd.concat([X_num, X_gang], axis=1).fillna(0)
    
    y = df['risk_score']
    
    # 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8)
    model.fit(X_train, y_train)
    
    # Out-of-sample Evaluation
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # 5-Fold Cross Validation for R2
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    # Feature Importance
    importance = model.feature_importances_
    feat_importance = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    
    return {
        "model": model,
        "feature_cols": list(X.columns),
        "feature_importance": feat_importance,
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "cv_r2_mean": float(cv_scores.mean())
    }, "Recidivism model trained successfully."

def predict_suspect_risk(model_dict, age, priors_count, gang_affiliation):
    """Predict risk score for a suspect."""
    model = model_dict["model"]
    feature_cols = model_dict["feature_cols"]
    
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    row.loc[0, 'age'] = float(age)
    row.loc[0, 'priors_count'] = float(priors_count)
    
    gang_col = f"gang_{gang_affiliation}"
    if gang_col in row.columns:
        row.loc[0, gang_col] = 1.0
        
    pred_risk = float(model.predict(row)[0])
    return float(np.clip(pred_risk, 0.05, 0.98))

def forecast_future_crimes(crimes_df, days_to_forecast=30):
    """
    Generate a 30-day forward time-series forecast of daily crime incidents
    with 95% Confidence Intervals using lag feature regression.
    """
    if crimes_df.empty or len(crimes_df) < 60:
        return pd.DataFrame(), pd.DataFrame()
        
    df_ts = crimes_df.copy()
    df_ts['date'] = df_ts['timestamp'].dt.date
    daily = df_ts.groupby('date').size().reset_index(name='crime_count')
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.set_index('date').sort_index()
    
    # Reindex missing days with 0
    full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq='D')
    daily = daily.reindex(full_range, fill_value=0)
    
    # Engineer lag and rolling features
    ts_data = daily.copy()
    ts_data['lag_1'] = ts_data['crime_count'].shift(1)
    ts_data['lag_7'] = ts_data['crime_count'].shift(7)
    ts_data['lag_14'] = ts_data['crime_count'].shift(14)
    ts_data['rolling_7_mean'] = ts_data['crime_count'].shift(1).rolling(7).mean()
    ts_data['day_of_week'] = ts_data.index.dayofweek
    ts_data['month'] = ts_data.index.month
    
    clean_ts = ts_data.dropna()
    if len(clean_ts) < 30:
        return daily.reset_index(names='date'), pd.DataFrame()
        
    feature_cols = ['lag_1', 'lag_7', 'lag_14', 'rolling_7_mean', 'day_of_week', 'month']
    X_train = clean_ts[feature_cols]
    y_train = clean_ts['crime_count']
    
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    
    # Calculate Residual Variance for 95% Confidence Interval
    preds_train = model.predict(X_train)
    residuals = y_train - preds_train
    std_err = float(np.std(residuals))
    
    # Iterative forward forecasting
    last_known_date = daily.index.max()
    future_dates = pd.date_range(start=last_known_date + pd.Timedelta(days=1), periods=days_to_forecast, freq='D')
    
    history_counts = list(daily['crime_count'].values)
    forecast_preds = []
    
    for f_date in future_dates:
        l1 = history_counts[-1]
        l7 = history_counts[-7] if len(history_counts) >= 7 else history_counts[-1]
        l14 = history_counts[-14] if len(history_counts) >= 14 else history_counts[-1]
        roll7 = np.mean(history_counts[-7:]) if len(history_counts) >= 7 else np.mean(history_counts)
        dow = f_date.dayofweek
        mon = f_date.month
        
        row_feat = pd.DataFrame([[l1, l7, l14, roll7, dow, mon]], columns=feature_cols)
        pred_val = float(model.predict(row_feat)[0])
        pred_val = max(0.0, pred_val)
        
        forecast_preds.append(pred_val)
        history_counts.append(pred_val)
        
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'predicted_count': forecast_preds,
        'lower_ci': [max(0.0, p - 1.96 * std_err) for p in forecast_preds],
        'upper_ci': [p + 1.96 * std_err for p in forecast_preds]
    })
    
    return daily.reset_index(names='date'), forecast_df

def detect_anomalies_rolling(crimes_df, window_days=14, threshold_z=2.0):
    """
    Find anomalies in crime rates over time using rolling Z-scores and Isolation Forest.
    """
    if crimes_df.empty or len(crimes_df) < 30:
        return pd.DataFrame(), pd.DataFrame()
        
    df_daily = crimes_df.copy()
    df_daily['date'] = df_daily['timestamp'].dt.date
    daily_counts = df_daily.groupby('date').size().reset_index(name='crime_count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
    daily_counts = daily_counts.set_index('date').sort_index()
    
    full_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
    daily_counts = daily_counts.reindex(full_range, fill_value=0)
    
    daily_counts['rolling_mean'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).mean()
    daily_counts['rolling_std'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).std()
    
    std_adj = daily_counts['rolling_std'].replace(0, 1)
    daily_counts['z_score'] = (daily_counts['crime_count'] - daily_counts['rolling_mean']) / std_adj
    daily_counts['is_anomaly'] = (daily_counts['z_score'] > threshold_z) & (daily_counts['crime_count'] > daily_counts['rolling_mean'])
    
    df_pivot = df_daily.groupby(['date', 'district_name']).size().unstack(fill_value=0)
    df_pivot.index = pd.to_datetime(df_pivot.index)
    df_pivot = df_pivot.reindex(full_range, fill_value=0)
    
    if len(df_pivot) >= 10:
        iso = IsolationForest(contamination=0.05, random_state=42)
        df_pivot['iso_anomaly'] = iso.fit_predict(df_pivot) == -1
        daily_counts['iso_anomaly'] = df_pivot['iso_anomaly']
    else:
        daily_counts['iso_anomaly'] = False
        
    return daily_counts.reset_index(names='date'), df_pivot.reset_index(names='date')

def calculate_socioeconomic_correlations(crimes_df, districts_df):
    """
    Calculate Pearson correlation between district socio-economic attributes
    and total crime count in those districts.
    """
    if crimes_df.empty or districts_df.empty:
        return pd.DataFrame()
        
    crime_counts = crimes_df.groupby('district_id').size().reset_index(name='total_crimes')
    merged = pd.merge(districts_df, crime_counts, left_on='id', right_on='district_id', how='left').fillna({'total_crimes': 0})
    
    features = ['unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density']
    
    correlations = {}
    p_values = {}
    for feat in features:
        r, p = stats.pearsonr(merged[feat], merged['total_crimes'])
        correlations[feat] = r
        p_values[feat] = p
        
    df_corr = pd.DataFrame({
        'feature': features,
        'pearson_r': [correlations[f] for f in features],
        'p_value': [p_values[f] for f in features]
    })
    
    return df_corr.sort_values(by='pearson_r', key=abs, ascending=False)
