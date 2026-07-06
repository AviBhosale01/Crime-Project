import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.preprocessing import LabelEncoder
import scipy.stats as stats

def detect_hotspots(df, eps_km=0.5, min_samples=5):
    """
    Cluster crime incidents using DBSCAN to identify hotspots.
    eps_km = 0.5 roughly corresponds to 0.0045 degrees.
    """
    if df.empty or len(df) < min_samples:
        return df.assign(hotspot_id=-1)
    
    # 1 degree lat is approx 111 km. 1 degree lon is approx 111 * cos(lat) km.
    # We use a simple approximation: 0.1 km ~ 0.0009 degrees
    eps_degrees = eps_km * 0.009
    
    coords = df[['latitude', 'longitude']].values
    db = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit(coords)
    
    return df.assign(hotspot_id=db.labels_)

def train_severity_predictor(crimes_df):
    """
    Train a Random Forest Classifier to predict the severity of a crime incident
    based on District, Time of Day, Day of Week, and Crime Type.
    """
    if crimes_df.empty or len(crimes_df) < 50:
        return None, "Not enough data to train severity model."
    
    df = crimes_df.copy()
    
    # Extract temporal features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Prepare features
    # Numerical features
    features_num = df[['hour', 'day_of_week', 'unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density']].copy()
    
    # Categorical features - One Hot Encode
    df_district = pd.get_dummies(df['district_name'], prefix='dist', dtype=float)
    df_type = pd.get_dummies(df['crime_type'], prefix='type', dtype=float)
    
    X = pd.concat([features_num, df_district, df_type], axis=1)
    
    # Label encode target
    le = LabelEncoder()
    y = le.fit_transform(df['severity']) # e.g. High=0, Low=1, Medium=2 (alphabetical usually)
    
    # Fill any NaNs
    X = X.fillna(0)
    
    # Train model
    model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=8)
    model.fit(X, y)
    
    # Get feature importance
    importance = model.feature_importances_
    feat_importance = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    
    return {
        "model": model,
        "feature_cols": list(X.columns),
        "label_encoder": le,
        "feature_importance": feat_importance
    }, "Model trained successfully."

def predict_incident_severity(model_dict, input_data):
    """
    Predict severity for an incoming crime profile.
    input_data should be a dict with:
      - district_name, crime_type, hour, day_of_week, and district socio-economics
    """
    model = model_dict["model"]
    feature_cols = model_dict["feature_cols"]
    le = model_dict["label_encoder"]
    
    # Create empty row with all columns set to 0
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    
    # Fill in numerical inputs
    for col in ['hour', 'day_of_week', 'unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density']:
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
    
    # Zip classes and probabilities
    class_probs = dict(zip(le.classes_, prob))
    return pred_class, class_probs

def train_recidivism_predictor(suspects_df):
    """
    Train a Random Forest Regressor to predict the risk score of a suspect
    based on age, gang affiliation, and prior convictions.
    """
    if suspects_df.empty or len(suspects_df) < 10:
        return None, "Not enough suspects to train recidivism model."
        
    df = suspects_df.copy()
    
    # Features
    X_num = df[['age', 'priors_count']].copy()
    X_gang = pd.get_dummies(df['gang_affiliation'], prefix='gang', dtype=float)
    X = pd.concat([X_num, X_gang], axis=1)
    
    y = df['risk_score']
    
    X = X.fillna(0)
    
    model = RandomForestRegressor(n_estimators=30, random_state=42, max_depth=6)
    model.fit(X, y)
    
    return {
        "model": model,
        "feature_cols": list(X.columns)
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
    return min(max(pred_risk, 0.0), 1.0)

def detect_anomalies_rolling(crimes_df, window_days=14, threshold_z=2.0):
    """
    Find anomalies in crime rates over time.
    Resamples crime counts by day and checks for z-scores higher than threshold.
    """
    if crimes_df.empty or len(crimes_df) < 30:
        return pd.DataFrame(), pd.DataFrame()
        
    # Group by day and count crimes
    df_daily = crimes_df.copy()
    df_daily['date'] = df_daily['timestamp'].dt.date
    daily_counts = df_daily.groupby('date').size().reset_index(name='crime_count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
    daily_counts = daily_counts.set_index('date').sort_index()
    
    # Reindex to fill missing days with 0
    full_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
    daily_counts = daily_counts.reindex(full_range, fill_value=0)
    
    # Calculate rolling statistics
    daily_counts['rolling_mean'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).mean()
    daily_counts['rolling_std'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).std()
    
    # Z-score
    # Avoid division by zero
    std_adj = daily_counts['rolling_std'].replace(0, 1)
    daily_counts['z_score'] = (daily_counts['crime_count'] - daily_counts['rolling_mean']) / std_adj
    
    # Label anomalies
    daily_counts['is_anomaly'] = (daily_counts['z_score'] > threshold_z) & (daily_counts['crime_count'] > daily_counts['rolling_mean'])
    
    # Multidimensional isolation forest anomaly detection (incorporates district crime counts)
    # We pivot to get daily counts per district
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
        
    # Count crimes by district
    crime_counts = crimes_df.groupby('district_id').size().reset_index(name='total_crimes')
    
    # Join with district stats
    merged = pd.merge(districts_df, crime_counts, left_on='id', right_on='district_id', how='left').fillna({'total_crimes': 0})
    
    # Calculate rate per 1000 population density (or raw crimes vs index)
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
