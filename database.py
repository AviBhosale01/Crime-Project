import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

DB_PATH = "/tmp/crime_analytics.db" if (os.path.exists("/mount/src") or os.environ.get("STREAMLIT_SERVER_PORT")) else "crime_analytics.db"

def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_readonly_connection():
    """Return a strict read-only connection to the SQLite database enforcing mode=ro at the database engine level."""
    abs_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def get_dynamic_severity(crime_type, hour, poverty_index=0.15):
    """
    Generate realistic severity levels with spatio-temporal and socio-economic variance.
    Eliminates deterministic data leakage so Random Forest models learn real probabilistic signals.
    """
    base_map = {
        "Theft": {"Low": 0.70, "Medium": 0.25, "High": 0.05},
        "Burglary": {"Low": 0.15, "Medium": 0.70, "High": 0.15},
        "Assault": {"Low": 0.10, "Medium": 0.40, "High": 0.50},
        "Narcotics": {"Low": 0.20, "Medium": 0.50, "High": 0.30},
        "Fraud": {"Low": 0.60, "Medium": 0.30, "High": 0.10},
        "Cybercrime": {"Low": 0.30, "Medium": 0.50, "High": 0.20},
        "Homicide": {"Low": 0.02, "Medium": 0.18, "High": 0.80}
    }
    
    probs = base_map.get(crime_type, {"Low": 0.33, "Medium": 0.33, "High": 0.34}).copy()
    
    if hour >= 22 or hour <= 4:
        probs["High"] += 0.15
        probs["Low"] = max(0.01, probs["Low"] - 0.15)
        
    if poverty_index > 0.20:
        probs["High"] += 0.10
        probs["Medium"] = max(0.01, probs["Medium"] - 0.10)
        
    total = sum(probs.values())
    p_values = [probs["Low"] / total, probs["Medium"] / total, probs["High"] / total]
    
    return np.random.choice(["Low", "Medium", "High"], p=p_values)

def init_db(force_recreate=False):
    """Initialize the database and populate it with realistic seed data if empty or forced."""
    db_exists = os.path.exists(DB_PATH)
    needs_seed = False
    
    if db_exists and not force_recreate:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Check if all required tables exist
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('districts', 'suspects', 'crimes', 'suspect_connections')")
            table_count = cursor.fetchone()[0]
            if table_count < 4:
                needs_seed = True
            else:
                cursor.execute("SELECT COUNT(*) FROM suspects")
                suspect_count = cursor.fetchone()[0]
                if suspect_count == 0:
                    needs_seed = True
            conn.close()
        except Exception:
            needs_seed = True
    else:
        needs_seed = True
        
    if force_recreate and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
            
    conn = get_connection()
    cursor = conn.cursor()
    
    if not needs_seed and not force_recreate:
        conn.close()
        return
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        unemployment_rate REAL,
        poverty_index REAL,
        median_income REAL,
        education_index REAL,
        population_density REAL,
        center_lat REAL,
        center_lon REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suspects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gang_affiliation TEXT,
        priors_count INTEGER,
        risk_score REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crimes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        district_id INTEGER,
        crime_type TEXT,
        severity TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT,
        suspect_id INTEGER,
        FOREIGN KEY(district_id) REFERENCES districts(id),
        FOREIGN KEY(suspect_id) REFERENCES suspects(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suspect_connections (
        suspect_a INTEGER,
        suspect_b INTEGER,
        relation_type TEXT,
        strength INTEGER,
        PRIMARY KEY(suspect_a, suspect_b),
        FOREIGN KEY(suspect_a) REFERENCES suspects(id),
        FOREIGN KEY(suspect_b) REFERENCES suspects(id)
    )
    """)
    
    conn.commit()
    
    # Check if we need to seed data
    cursor.execute("SELECT COUNT(*) FROM districts")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
        
    conn.close()

def seed_data(conn):
    """Seed the database with realistic Pune-based crime intelligence data."""
    cursor = conn.cursor()
    
    # 1. Seed Districts (Pune, Maharashtra)
    districts = [
        # name, unemployment_rate, poverty_index, median_income, education_index, population_density, center_lat, center_lon
        ("Shivajinagar", 5.2, 0.12, 65000, 0.85, 9500, 18.5308, 73.8475),
        ("Kothrud", 3.8, 0.08, 85000, 0.90, 8000, 18.5074, 73.8077),
        ("Viman Nagar", 4.5, 0.10, 95000, 0.88, 7000, 18.5679, 73.9143),
        ("Hinjawadi", 6.2, 0.15, 105000, 0.82, 4500, 18.5913, 73.7389),
        ("Koregaon Park", 3.1, 0.05, 150000, 0.92, 5000, 18.5362, 73.8930),
        ("Hadapsar", 8.5, 0.22, 55000, 0.72, 8500, 18.5089, 73.9260),
        ("Katraj", 9.1, 0.25, 48000, 0.68, 9000, 18.4575, 73.8677),
        ("Swargate", 7.8, 0.18, 52000, 0.75, 11000, 18.5018, 73.8636)
    ]
    
    cursor.executemany("""
    INSERT INTO districts (name, unemployment_rate, poverty_index, median_income, education_index, population_density, center_lat, center_lon)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, districts)
    conn.commit()
    
    # Get district IDs mapped to names and poverty indices
    cursor.execute("SELECT id, name, center_lat, center_lon, poverty_index FROM districts")
    district_map = {row['name']: (row['id'], row['center_lat'], row['center_lon'], row['poverty_index']) for row in cursor.fetchall()}
    
    # 2. Seed 2,050 Suspects (Maharashtrian / Indian Names)
    first_names = [
        "Rahul", "Amit", "Sachin", "Sunil", "Rohit", "Amol", "Sandeep", "Nilesh", "Sanjay", "Manoj",
        "Swapnil", "Rohan", "Atul", "Anand", "Vivek", "Vijay", "Ajit", "Nitin", "Sameer", "Ajay",
        "Mahesh", "Deepak", "Chetan", "Kedar", "Vishal", "Sagar", "Akshay", "Pratik", "Abhishek", "Harshal",
        "Rajesh", "Dinesh", "Prakash", "Suresh", "Ramesh", "Kiran", "Ashok", "Kishor", "Vinod", "Pramod",
        "Priya", "Vaishali", "Snehal", "Deepali", "Shubhangi", "Gauri", "Tanvi", "Swati", "Anjali", "Meenal"
    ]
    last_names = [
        "Deshmukh", "Patil", "Kulkarni", "Shinde", "Pawar", "Joshi", "Chavan", "Jadhav", "More", "Gaikwad",
        "Phadke", "Kamble", "Sawant", "Kadam", "Tambe", "Sathe", "Gokhale", "Bhonsle", "Apte", "Raje",
        "Desai", "Bhat", "Mane", "Salunkhe", "Mohite", "Thorat", "Bhosale", "Jagtap", "Nalawade", "Pisal",
        "Karande", "Kate", "Dhumal", "Nikam", "Wadekar", "Rane", "Ghadge", "Shelar", "Kokane", "Bandal",
        "Jedhe", "Kank", "Shirke", "Kudale", "Wagh", "Mulay", "Karkhanis", "Kale", "Ghatge", "Suryavanshi"
    ]
    
    gangs = [
        "None", "Pune Local Syndicate", "Shivaji Nagar Cartel", "Koregaon Park Network",
        "Hinjawadi Tech Syndicate", "Deccan Metro Syndicate", "Swargate Crime Ring", "None", "None"
    ]
    
    np.random.seed(42)
    suspect_names = set()
    while len(suspect_names) < 2050:
        name = f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
        suspect_names.add(name)
    suspect_names = list(suspect_names)
    
    suspects_list = []
    for i in range(2050):
        name = suspect_names[i]
        age = int(np.random.randint(18, 65))
        gang = np.random.choice(gangs)
        priors = int(np.random.negative_binomial(2, 0.4)) # right-skewed priors count
        # Base risk calculation
        risk = float(np.clip((priors * 0.12) + (0.2 if gang != "None" else 0) + (np.random.uniform(0.05, 0.25)), 0.1, 0.95))
        suspects_list.append((name, age, gang, priors, risk))
        
    cursor.executemany("""
    INSERT INTO suspects (name, age, gang_affiliation, priors_count, risk_score)
    VALUES (?, ?, ?, ?, ?)
    """, suspects_list)
    conn.commit()
    
    # Get all suspect IDs
    cursor.execute("SELECT id FROM suspects")
    suspect_ids = [row['id'] for row in cursor.fetchall()]
    
    # 3. Seed Crimes (Historical for past 540 days)
    crime_types = {
        "Theft": {"weight": 0.28},
        "Burglary": {"weight": 0.18},
        "Assault": {"weight": 0.22},
        "Narcotics": {"weight": 0.15},
        "Fraud": {"weight": 0.10},
        "Cybercrime": {"weight": 0.05},
        "Homicide": {"weight": 0.02}
    }
    
    # Different Pune districts have different crime profiles
    district_crime_profiles = {
        "Shivajinagar": ["Theft", "Assault", "Burglary", "Fraud"],
        "Kothrud": ["Theft", "Burglary", "Fraud", "Assault"],
        "Viman Nagar": ["Theft", "Narcotics", "Fraud", "Cybercrime"],
        "Hinjawadi": ["Cybercrime", "Theft", "Fraud", "Burglary"],
        "Koregaon Park": ["Narcotics", "Theft", "Assault", "Homicide"],
        "Hadapsar": ["Burglary", "Assault", "Theft", "Narcotics"],
        "Katraj": ["Theft", "Assault", "Burglary", "Narcotics"],
        "Swargate": ["Assault", "Theft", "Burglary", "Homicide"]
    }
    
    crimes_list = []
    start_date = datetime.now() - timedelta(days=540)
    statuses = ["Closed", "Closed", "In Investigation", "Open"]
    
    # We generate exactly 3,095 crimes total distributed according to Pune illustrative weights:
    district_targets = {
        "Shivajinagar": 495,
        "Kothrud": 433,
        "Viman Nagar": 371,
        "Hinjawadi": 464,
        "Koregaon Park": 310,
        "Hadapsar": 402,
        "Katraj": 310,
        "Swargate": 310
    }
    
    # Hotspot allocations (these counts are part of the target district count)
    hotspot_specs = {
        "Hinjawadi": {"count": 120, "std": 0.0015, "type": "Cybercrime"},
        "Kothrud": {"count": 100, "std": 0.0018, "type": "Theft"},
        "Koregaon Park": {"count": 110, "std": 0.0015, "type": "Narcotics"}
    }
    
    # Anomaly allocations (these counts are part of the target district count and are placed in the last 30-45 days)
    anomaly_specs = {
        "Hinjawadi": {"count": 50, "std": 0.002, "type": "Cybercrime", "days": 30, "hours": [9, 10, 11, 12, 13, 14, 15, 16, 17]},
        "Koregaon Park": {"count": 45, "std": 0.002, "type": "Narcotics", "days": 45, "hours": [21, 22, 23, 0, 1, 2]}
    }
    
    for dname, target_count in district_targets.items():
        did, center_lat, center_lon, d_poverty = district_map[dname]
        
        # Determine allocations
        h_spec = hotspot_specs.get(dname)
        a_spec = anomaly_specs.get(dname)
        
        h_count = h_spec["count"] if h_spec else 0
        a_count = a_spec["count"] if a_spec else 0
        normal_count = target_count - h_count - a_count
        
        # 1. Seeding Hotspot Crimes
        if h_spec:
            for _ in range(h_count):
                days_offset = np.random.randint(0, 540)
                hour = np.random.randint(0, 24)
                crime_time = start_date + timedelta(days=days_offset, hours=hour, minutes=np.random.randint(0, 60))
                
                # Tightly clustered coordinates
                lat = center_lat + np.random.normal(0, h_spec["std"])
                lon = center_lon + np.random.normal(0, h_spec["std"])
                
                crime_type = h_spec["type"]
                severity = get_dynamic_severity(crime_type, hour, d_poverty)
                status = np.random.choice(statuses, p=[0.45, 0.35, 0.15, 0.05])
                
                sus_id = None
                if np.random.rand() < 0.45:
                    sus_id = int(np.random.choice(suspect_ids))
                    
                crimes_list.append((
                    crime_time.strftime("%Y-%m-%d %H:%M:%S"),
                    did,
                    crime_type,
                    severity,
                    lat,
                    lon,
                    status,
                    sus_id
                ))
                
        # 2. Seeding Anomaly Crimes (Recent Spike)
        if a_spec:
            anomaly_start = datetime.now() - timedelta(days=a_spec["days"])
            for _ in range(a_count):
                days_offset = np.random.randint(0, a_spec["days"])
                hour = int(np.random.choice(a_spec["hours"]))
                crime_time = anomaly_start + timedelta(days=days_offset, hours=hour, minutes=np.random.randint(0, 60))
                
                lat = center_lat + np.random.normal(0, a_spec["std"])
                lon = center_lon + np.random.normal(0, a_spec["std"])
                
                crime_type = a_spec["type"]
                severity = get_dynamic_severity(crime_type, hour, d_poverty)
                status = np.random.choice(["Open", "In Investigation", "Closed"], p=[0.2, 0.4, 0.4])
                
                sus_id = None
                if np.random.rand() < 0.45:
                    sus_id = int(np.random.choice(suspect_ids))
                    
                crimes_list.append((
                    crime_time.strftime("%Y-%m-%d %H:%M:%S"),
                    did,
                    crime_type,
                    severity,
                    lat,
                    lon,
                    status,
                    sus_id
                ))
                
        # 3. Seeding Normal Crimes
        for _ in range(normal_count):
            days_offset = np.random.randint(0, 540)
            hour = np.random.randint(0, 24)
            crime_time = start_date + timedelta(days=days_offset, hours=hour, minutes=np.random.randint(0, 60))
            
            lat = center_lat + np.random.normal(0, 0.005)
            lon = center_lon + np.random.normal(0, 0.005)
            
            allowed_types = district_crime_profiles[dname]
            type_weights = [crime_types[t]["weight"] for t in allowed_types]
            type_weights = np.array(type_weights) / sum(type_weights)
            crime_type = np.random.choice(allowed_types, p=type_weights)
            
            severity = get_dynamic_severity(crime_type, hour, d_poverty)
            status = np.random.choice(statuses, p=[0.5, 0.3, 0.15, 0.05])
            
            sus_id = None
            if np.random.rand() < 0.45:
                sus_id = int(np.random.choice(suspect_ids))
                
            crimes_list.append((
                crime_time.strftime("%Y-%m-%d %H:%M:%S"),
                did,
                crime_type,
                severity,
                lat,
                lon,
                status,
                sus_id
            ))
        
    cursor.executemany("""
    INSERT INTO crimes (timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, crimes_list)
    conn.commit()
    
    # 4. Seed Authentic Criminal Network Connections (~50-65 high-value realistic links)
    connections = set()
    
    # Query suspects grouped by gang syndicate directly from the seeded suspects database table
    cursor.execute("SELECT id, name, gang_affiliation, risk_score FROM suspects WHERE gang_affiliation != 'None'")
    gang_rows = cursor.fetchall()
    
    gang_groups = {}
    for r in gang_rows:
        g_name = r['gang_affiliation']
        if g_name not in gang_groups:
            gang_groups[g_name] = []
        gang_groups[g_name].append(dict(r))
        
    gang_leaders = {}
    # For each syndicate, select the top-risk suspect as the Gang Leader / Hub
    for g_name, s_list in gang_groups.items():
        if len(s_list) >= 4:
            sorted_s = sorted(s_list, key=lambda x: x['risk_score'], reverse=True)
            leader = sorted_s[0]
            gang_leaders[g_name] = leader['id']
            
            # Connect leader to top lieutenants/associates (star topology)
            lieutenants = sorted_s[1:6]
            for lt in lieutenants:
                pair = (min(leader['id'], lt['id']), max(leader['id'], lt['id']))
                connections.add((pair[0], pair[1], "Gang Member", int(np.random.randint(4, 6))))
                
            # Interconnect a few lieutenants (inner clique links)
            for i in range(len(lieutenants)):
                for j in range(i + 1, min(i + 3, len(lieutenants))):
                    if np.random.rand() < 0.4:
                        pair = (min(lieutenants[i]['id'], lieutenants[j]['id']), max(lieutenants[i]['id'], lieutenants[j]['id']))
                        connections.add((pair[0], pair[1], "Gang Member", int(np.random.randint(3, 5))))

    # Co-Arrestee & Accomplice links: Connect suspects co-occurring in the same crime incident records
    cursor.execute("""
        SELECT suspect_id, district_id, crime_type 
        FROM crimes 
        WHERE suspect_id IS NOT NULL 
        LIMIT 250
    """)
    crime_rows = cursor.fetchall()
    
    co_occurrences = {}
    for r in crime_rows:
        key = (r['district_id'], r['crime_type'])
        if key not in co_occurrences:
            co_occurrences[key] = []
        co_occurrences[key].append(r['suspect_id'])
        
    for key, s_list in co_occurrences.items():
        unique_s = list(set(s_list))
        if len(unique_s) >= 2:
            for i in range(min(2, len(unique_s) - 1)):
                s_a, s_b = unique_s[i], unique_s[i + 1]
                if s_a != s_b:
                    pair = (min(s_a, s_b), max(s_a, s_b))
                    if not any(c[0] == pair[0] and c[1] == pair[1] for c in connections):
                        rel = np.random.choice(["Accomplice", "Co-arrestee"], p=[0.6, 0.4])
                        connections.add((pair[0], pair[1], rel, int(np.random.randint(2, 5))))

    # Inter-Gang Bridge Connectors (3-4 bridge links between syndicate leaders/lieutenants)
    leader_ids = list(gang_leaders.values())
    if len(leader_ids) >= 2:
        for i in range(len(leader_ids) - 1):
            s_a, s_b = leader_ids[i], leader_ids[i + 1]
            pair = (min(s_a, s_b), max(s_a, s_b))
            if not any(c[0] == pair[0] and c[1] == pair[1] for c in connections):
                rel = np.random.choice(["Accomplice", "Co-arrestee", "Relative"], p=[0.4, 0.4, 0.2])
                connections.add((pair[0], pair[1], rel, int(np.random.randint(3, 5))))

    cursor.executemany("""
    INSERT INTO suspect_connections (suspect_a, suspect_b, relation_type, strength)
    VALUES (?, ?, ?, ?)
    """, list(connections))
    conn.commit()


# --- Database Query Helpers ---

def get_crimes_df(filter_dict=None):
    """Retrieve crimes, joined with district and suspect info, as a pandas DataFrame."""
    conn = get_connection()
    query = """
    SELECT 
        c.id as crime_id,
        c.timestamp,
        c.crime_type,
        c.severity,
        c.latitude,
        c.longitude,
        c.status,
        d.id as district_id,
        d.name as district_name,
        d.unemployment_rate,
        d.poverty_index,
        d.median_income,
        d.education_index,
        d.population_density,
        s.id as suspect_id,
        s.name as suspect_name,
        s.age as suspect_age,
        s.gang_affiliation,
        s.priors_count as suspect_priors,
        s.risk_score as suspect_risk_score
    FROM crimes c
    JOIN districts d ON c.district_id = d.id
    LEFT JOIN suspects s ON c.suspect_id = s.id
    WHERE 1=1
    """
    params = []
    
    if filter_dict:
        if "district_ids" in filter_dict and filter_dict["district_ids"]:
            placeholders = ",".join("?" for _ in filter_dict["district_ids"])
            query += f" AND d.id IN ({placeholders})"
            params.extend(filter_dict["district_ids"])
            
        if "crime_types" in filter_dict and filter_dict["crime_types"]:
            placeholders = ",".join("?" for _ in filter_dict["crime_types"])
            query += f" AND c.crime_type IN ({placeholders})"
            params.extend(filter_dict["crime_types"])
            
        if "severities" in filter_dict and filter_dict["severities"]:
            placeholders = ",".join("?" for _ in filter_dict["severities"])
            query += f" AND c.severity IN ({placeholders})"
            params.extend(filter_dict["severities"])
            
        if "start_date" in filter_dict and filter_dict["start_date"]:
            query += " AND c.timestamp >= ?"
            params.append(filter_dict["start_date"])
            
        if "end_date" in filter_dict and filter_dict["end_date"]:
            query += " AND c.timestamp <= ?"
            params.append(filter_dict["end_date"])
            
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_suspects_df():
    """Retrieve all suspect records as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM suspects", conn)
    conn.close()
    return df

def get_districts_df():
    """Retrieve all district records as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM districts", conn)
    conn.close()
    return df

def get_connections_df():
    """Retrieve all suspect associate connections."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM suspect_connections", conn)
    conn.close()
    return df

def add_crime(timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id=None):
    """Insert a new crime record into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO crimes (timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_crime(crime_id, status, suspect_id=None):
    """Update status or suspect of an existing crime."""
    conn = get_connection()
    cursor = conn.cursor()
    if suspect_id:
        cursor.execute("UPDATE crimes SET status = ?, suspect_id = ? WHERE id = ?", (status, suspect_id, crime_id))
    else:
        cursor.execute("UPDATE crimes SET status = ? WHERE id = ?", (status, crime_id))
    conn.commit()
    conn.close()

def add_suspect(name, age, gang, priors, risk_score):
    """Insert a new suspect into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO suspects (name, age, gang_affiliation, priors_count, risk_score)
    VALUES (?, ?, ?, ?, ?)
    """, (name, age, gang, priors, risk_score))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def add_connection(s_a, s_b, rel_type, strength):
    """Insert a connection between two suspects (order sorted to prevent duplicates)."""
    conn = get_connection()
    cursor = conn.cursor()
    first, second = min(s_a, s_b), max(s_a, s_b)
    cursor.execute("""
    INSERT OR REPLACE INTO suspect_connections (suspect_a, suspect_b, relation_type, strength)
    VALUES (?, ?, ?, ?)
    """, (first, second, rel_type, strength))
    conn.commit()
def update_suspect_details(suspect_id, name, age, gang_affiliation, priors_count, risk_score):
    """Update details of an existing suspect."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE suspects
    SET name = ?, age = ?, gang_affiliation = ?, priors_count = ?, risk_score = ?
    WHERE id = ?
    """, (name, age, gang_affiliation, priors_count, risk_score, suspect_id))
    conn.commit()
    conn.close()

def update_crime_details(crime_id, timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id=None):
    """Update details of an existing crime."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE crimes
    SET timestamp = ?, district_id = ?, crime_type = ?, severity = ?, latitude = ?, longitude = ?, status = ?, suspect_id = ?
    WHERE id = ?
    """, (timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id, crime_id))
    conn.commit()
    conn.close()

def update_connection_details(suspect_a, suspect_b, relation_type, strength):
    """Update details of an existing connection."""
    conn = get_connection()
    cursor = conn.cursor()
    first, second = min(suspect_a, suspect_b), max(suspect_a, suspect_b)
    cursor.execute("""
    UPDATE suspect_connections
    SET relation_type = ?, strength = ?
    WHERE suspect_a = ? AND suspect_b = ?
    """, (relation_type, strength, first, second))
    conn.commit()
    conn.close()

def delete_suspect(suspect_id):
    """Delete a suspect and clean up associated foreign key records."""
    conn = get_connection()
    cursor = conn.cursor()
    # Unlink from crimes
    cursor.execute("UPDATE crimes SET suspect_id = NULL WHERE suspect_id = ?", (suspect_id,))
    # Delete suspect connections
    cursor.execute("DELETE FROM suspect_connections WHERE suspect_a = ? OR suspect_b = ?", (suspect_id, suspect_id))
    # Delete the suspect profile
    cursor.execute("DELETE FROM suspects WHERE id = ?", (suspect_id,))
    conn.commit()
    conn.close()

def delete_crime(crime_id):
    """Delete a crime incident."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM crimes WHERE id = ?", (crime_id,))
    conn.commit()
    conn.close()

def delete_connection(s_a, s_b):
    """Delete a relationship connection between suspects."""
    conn = get_connection()
    cursor = conn.cursor()
    first, second = min(s_a, s_b), max(s_a, s_b)
    cursor.execute("DELETE FROM suspect_connections WHERE suspect_a = ? AND suspect_b = ?", (first, second))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db(force_recreate=True)
    conn = get_connection()
    s_count = conn.execute("SELECT COUNT(*) FROM suspects").fetchone()[0]
    c_count = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
    conn.close()
    print("Database Initialized!")
    print(f"Suspects Count: {s_count}")
    print(f"Crimes Count: {c_count}")
