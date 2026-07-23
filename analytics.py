import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, r2_score, mean_absolute_error, mean_squared_error
)
import scipy.stats as stats

def detect_hotspots(df, eps_km=0.5, min_samples=5):
    """
    Cluster crime incidents using DBSCAN to identify geospatial hotspots.
    eps_km = 0.5 roughly corresponds to 0.0045 degrees lat/lon in Pune.
    """
    if df.empty or len(df) < min_samples:
        return df.assign(hotspot_id=-1)
    
    eps_degrees = eps_km * 0.009
    coords = df[['latitude', 'longitude']].values
    db = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit(coords)
    
    return df.assign(hotspot_id=db.labels_)

def train_severity_predictor(crimes_df):
    """
    Train a Random Forest Classifier to predict crime incident severity (Low, Medium, High).
    Uses 80/20 train-test split, balanced class weights, and evaluates real validation metrics:
    Accuracy, F1 Macro, Precision, Recall, Confusion Matrix, and 5-Fold Cross-Validation.
    """
    if crimes_df.empty or len(crimes_df) < 50:
        return None, "Insufficient data to train severity model (minimum 50 incident logs required)."
    
    df = crimes_df.copy()
    
    # Extract spatio-temporal features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(float)
    
    # Numerical socio-economic & spatio-temporal features
    features_num = df[[
        'hour', 'day_of_week', 'month', 'is_weekend',
        'unemployment_rate', 'poverty_index', 'median_income',
        'education_index', 'population_density'
    ]].copy()
    
    # One-Hot Encode Categoricals (District Location and Crime Category)
    df_district = pd.get_dummies(df['district_name'], prefix='dist', dtype=float)
    df_type = pd.get_dummies(df['crime_type'], prefix='type', dtype=float)
    
    X = pd.concat([features_num, df_district, df_type], axis=1).fillna(0)
    
    # Target encoding
    le = LabelEncoder()
    y = le.fit_transform(df['severity']) # Classes e.g., ['High', 'Low', 'Medium']
    
    # Train / Test Split (80% Train, 20% Validation Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # Fit Random Forest Classifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    
    # Model Validation Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1_mac = f1_score(y_test, y_pred, average='macro', zero_division=0)
    prec_mac = precision_score(y_test, y_pred, average='macro', zero_division=0)
    rec_mac = recall_score(y_test, y_pred, average='macro', zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    # 5-Fold Cross Validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    cv_acc_mean = cv_scores.mean()
    cv_acc_std = cv_scores.std()
    
    # Feature Importance
    importance = model.feature_importances_
    feat_importance = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    
    model_dict = {
        "model": model,
        "feature_cols": list(X.columns),
        "label_encoder": le,
        "feature_importance": feat_importance,
        "accuracy": acc,
        "f1_score": f1_mac,
        "precision": prec_mac,
        "recall": rec_mac,
        "cv_accuracy_mean": cv_acc_mean,
        "cv_accuracy_std": cv_acc_std,
        "confusion_matrix": cm,
        "classes": list(le.classes_),
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    return model_dict, f"Severity prediction model successfully trained on {len(df)} historical crime logs."

def predict_incident_severity(model_dict, input_data):
    """
    Predict severity class and probability distribution for incoming crime incident conditions.
    """
    model = model_dict["model"]
    feature_cols = model_dict["feature_cols"]
    le = model_dict["label_encoder"]
    
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    
    # Populate numerical features
    num_fields = [
        'hour', 'day_of_week', 'month', 'is_weekend',
        'unemployment_rate', 'poverty_index', 'median_income',
        'education_index', 'population_density'
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

def train_recidivism_predictor(suspects_df):
    """
    Train a Random Forest Regressor to forecast offender Recidivism Risk Index (0.0 to 1.0)
    using suspect demographics, prior criminal history, and syndicate/gang affiliation.
    Evaluates R^2, Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and 5-fold CV.
    """
    if suspects_df.empty or len(suspects_df) < 20:
        return None, "Insufficient suspect records to train recidivism regression model."
        
    df = suspects_df.copy()
    
    X_num = df[['age', 'priors_count']].copy()
    # Feature engineering: prior intensity ratio
    X_num['priors_per_year_age'] = df['priors_count'] / (df['age'] - 16).clip(lower=1)
    
    X_gang = pd.get_dummies(df['gang_affiliation'], prefix='gang', dtype=float)
    X = pd.concat([X_num, X_gang], axis=1).fillna(0)
    
    y = df['risk_score'].astype(float)
    
    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Test set evaluation
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # 5-Fold Cross Validation
    cv_r2_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    importance = model.feature_importances_
    feat_importance = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    
    model_dict = {
        "model": model,
        "feature_cols": list(X.columns),
        "feature_importance": feat_importance,
        "r2_score": r2,
        "mae": mae,
        "rmse": rmse,
        "cv_r2_mean": cv_r2_scores.mean(),
        "total_suspects": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    return model_dict, f"Recidivism forecaster successfully trained on {len(df)} suspect profiles."

def predict_suspect_risk(model_dict, age, priors_count, gang_affiliation):
    """Predict Recidivism Risk Index for a suspect profile."""
    model = model_dict["model"]
    feature_cols = model_dict["feature_cols"]
    
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    row.loc[0, 'age'] = float(age)
    row.loc[0, 'priors_count'] = float(priors_count)
    row.loc[0, 'priors_per_year_age'] = float(priors_count) / max(float(age) - 16.0, 1.0)
    
    gang_col = f"gang_{gang_affiliation}"
    if gang_col in row.columns:
        row.loc[0, gang_col] = 1.0
        
    pred_risk = float(model.predict(row)[0])
    return float(np.clip(pred_risk, 0.0, 1.0))

def detect_anomalies_rolling(crimes_df, window_days=14, threshold_z=2.0):
    """
    Dual statistical and machine learning anomaly detection on daily crime frequencies.
    1. Rolling Z-Score temporal surge detection (Threshold Z > 2.0).
    2. Multidimensional Isolation Forest for district-wide spatio-temporal crime anomalies.
    """
    if crimes_df.empty or len(crimes_df) < 30:
        return pd.DataFrame(), pd.DataFrame()
        
    df_daily = crimes_df.copy()
    df_daily['date'] = df_daily['timestamp'].dt.date
    daily_counts = df_daily.groupby('date').size().reset_index(name='crime_count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
    daily_counts = daily_counts.set_index('date').sort_index()
    
    # Reindex to ensure continuous calendar daily sequence
    full_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
    daily_counts = daily_counts.reindex(full_range, fill_value=0)
    
    # Rolling Statistics
    daily_counts['rolling_mean'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).mean()
    daily_counts['rolling_std'] = daily_counts['crime_count'].rolling(window=window_days, min_periods=3).std()
    
    std_adj = daily_counts['rolling_std'].replace(0, 1.0)
    daily_counts['z_score'] = (daily_counts['crime_count'] - daily_counts['rolling_mean']) / std_adj
    daily_counts['is_anomaly'] = (daily_counts['z_score'] > threshold_z) & (daily_counts['crime_count'] > daily_counts['rolling_mean'])
    
    # Isolation Forest Multidimensional Anomaly Detection per district
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
    Calculate Pearson (r) and Spearman (rho) rank correlations between district socio-economic variables
    and district crime frequencies / crime rates per 1,000 population density.
    """
    if crimes_df.empty or districts_df.empty:
        return pd.DataFrame()
        
    crime_counts = crimes_df.groupby('district_id').size().reset_index(name='total_crimes')
    merged = pd.merge(districts_df, crime_counts, left_on='id', right_on='district_id', how='left').fillna({'total_crimes': 0})
    
    # Normalize crime rate per 1,000 population density
    merged['crime_rate_per_1k_density'] = (merged['total_crimes'] / merged['population_density']) * 1000.0
    
    features = ['unemployment_rate', 'poverty_index', 'median_income', 'education_index', 'population_density']
    
    rows = []
    for feat in features:
        r_val, r_p = stats.pearsonr(merged[feat], merged['total_crimes'])
        rho_val, rho_p = stats.spearmanr(merged[feat], merged['total_crimes'])
        
        rows.append({
            'feature': feat,
            'pearson_r': r_val,
            'p_value': r_p,
            'spearman_rho': rho_val,
            'spearman_p': rho_p
        })
        
    df_corr = pd.DataFrame(rows)
    return df_corr.sort_values(by='pearson_r', key=abs, ascending=False)

