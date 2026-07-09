# 🛡️ Pune Crime Intelligence Command Center (PCICC)

An advanced, premium-tier AI-powered Geospatial Analytics, Suspect Risk Profiling, and Criminal Social Network Linkage platform built specifically for **Pune, Maharashtra, India**. 

Equipped with a **Universal Text-to-SQL AI Chatbot**, the platform allows investigators to ask natural language questions, automatically queries the SQLite database, and presents smart analytics using models from Gemini, OpenAI, OpenRouter, Groq, and NVIDIA NIM.

---

## 🌟 Key Features

*   **📊 Command Dashboard**: Real-time KPI indicators showcasing active crime metrics, DBSCAN-generated hotspots, high-risk recidivists, and daily anomaly spikes (Z-score analysis).
*   **🗺️ Geospatial Intelligence Map**: Plotly Mapbox maps centered on Pune showing crime distribution. Includes DBSCAN clustering layers and centroid markers displaying hotspot names and crime counts.
*   **🔍 Intelligence Explorer & Search**: Search directory supporting text-filtering over **2,050 suspects** and **3,000+ crime logs**. Features a detailed **Suspect Dossier Inspector** linking biographical indicators and incident timelines.
*   **🧠 AI Predictive Models**:
    *   *Incident Severity Predictor*: Random Forest Classifier predicting Low/Medium/High incident severity based on socio-economic and temporal factors.
    *   *Recidivism Risk Forecaster*: Random Forest Regressor predicting a repeat offender's risk index.
    *   *Socio-Economic Correlation*: Interactive Pearson correlation metrics tracking crime density vs. local poverty and unemployment.
*   **🕸️ Criminal Network Analysis**: Interactive social link analysis of cliques and associates. Employs NetworkX centrality scores to identify associate hubs (degree centrality) and bridge figures (betweenness centrality).
*   **📝 CRUD Intel Entry (Passkey Locked)**: Clean form validation interfaces to log crime incidents, register new suspects, and model criminal connections. Access is restricted using a secure password validation gate.
*   **📂 View Data Explorer & Editor (Passkey Locked)**:
    *   *Direct Database Management*: A full-featured editor page to view, search, add, edit, and delete suspects, crime logs, and associations.
    *   *SQLite Synchronization*: Persist inline edits directly to SQLite. Cascading deletions automatically unlink suspect IDs from crimes and clear network connections.
    *   *Built-in Undo/Redo & Reset*: Reset edits easily or use standard `Ctrl+Z` / `Ctrl+Y` shortcuts to revert table edits.
*   **💬 AI Intelligence Chatbot**: A secure conversational interface supporting **Gemini, OpenAI, OpenRouter, Groq, and NVIDIA NIM**. Auto-translates English questions into SQLite code, queries the database, and summarizes results contextually.

---

## 🔒 Security & Access Control

Access to data entry and raw database tables is restricted using secure password gates. These keys are defined in the external file `config_keys.py`:

| Page / Action | Environment Key | Default Passkey |
| :--- | :--- | :--- |
| **📝 Intel Entry (CRUD)** | `INTEL_ENTRY_KEY` | `crime_pune_entry_2026` |
| **📂 View Data (Explorer)** | `VIEW_DATA_KEY` | `crime_pune_view_2026` |

*To change passkeys for deployment, simply edit the string constants inside `config_keys.py`.*

---

## 🛠️ Technology Stack

*   **Frontend UI & Dashboard**: Streamlit (Premium Custom Dark Matter styling)
*   **Data Wrangling**: Pandas, NumPy
*   **Visualizations & Maps**: Plotly Express/GO, Folium, Mapbox, Matplotlib
*   **Machine Learning**: Scikit-Learn (Random Forests, Isolation Forest, DBSCAN)
*   **Network Graphs**: NetworkX
*   **Database Management**: SQLite3
*   **Exports**: `openpyxl` (Excel), `reportlab` (PDF)
*   **AI Chatbot Engine**: Gemini, OpenAI, OpenRouter, Groq, NVIDIA NIM (NVIDIA NeMo Cloud)

---

## 📋 Database Schema

The SQLite database (`crime_analytics.db`) is structured as follows:

```
 districts ──────────┐
 (Socio-economics)   │ (1-to-many)
                     ▼
                  crimes ◄────────── suspects
                 (Incidents)        (2,000+ Profiles)
                                           │ (many-to-many via self-join)
                                           ▼
                                   suspect_connections
                                   (Clique link maps)
```

*   **`districts`**: Uniquely models Pune regions (Shivajinagar, Kothrud, Hinjawadi, Koregaon Park, Hadapsar, Katraj, Swargate, Viman Nagar) with local coordinates, unemployment rates, poverty index, median incomes, and population density.
*   **`suspects`**: Tracks 2,050 unique Maharashtrian suspect profiles with gang affiliations, priors, and calculated risk index.
*   **`crimes`**: Contains historical logs of 3,095 incidents including timestamps, severity classifications, and coordinates.
*   **`suspect_connections`**: Defines relationship links (Accomplice, Co-arrestee, Gang Member, Relative) and link strengths.

---

## 🚀 Installation & Setup Guide

Get the Pune Crime Intelligence Command Center running on your local machine in three simple steps:

### Step 1: Clone or Copy the Repository
Make sure all project files are placed in your working directory:
```bash
📂 project-directory/
├── 📄 app.py              # Streamlit dashboard layout & pages
├── 📄 database.py         # SQLite connection, seeding, & CRUD functions
├── 📄 config_keys.py      # App security passkey configurations
├── 📄 analytics.py        # ML predictors & anomaly detection
├── 📄 visualizations.py   # Plotly charts, Mapbox maps, & NetworkX
├── 📄 requirements.txt    # Library dependencies
└── 📄 README.md           # Documentation
```

### Step 2: Install Dependencies
Open your terminal inside the project directory and run:
```bash
pip install -r requirements.txt openpyxl reportlab
```
*Note: This installs essential packages including `streamlit`, `scikit-learn`, `networkx`, `plotly`, `google-generativeai`, `openai`, `openpyxl`, and `reportlab`.*

### Step 3: Run the Application
Start the Streamlit development server:
```bash
streamlit run app.py
```
The server will boot up and print local URLs. The application will open automatically in your browser at `http://localhost:8501`.

---

## 📥 Exporting & Downloading Data

Under the **📂 View Data** tab, investigators can search for any record and export tables using the following buttons:
1.  **CSV Export**: Native comma-separated values download.
2.  **Excel Export**: Fully formatted `.xlsx` workbook sheet.
3.  **PDF Export**: A clean, landscape-oriented document report compiled using `reportlab`.
4.  **Table Image (PNG)**: Renders a high-resolution alternating-row preview table image using `matplotlib`.

---

## 💬 Using the AI Chatbot

1.  Navigate to the **💬 AI Intel Chatbot** page in the left sidebar.
2.  Choose your API provider (**Gemini, OpenAI, OpenRouter, Groq, or NVIDIA NIM**).
3.  Select a preset version or select **Custom Model** to type any specific model ID.
4.  Enter your API Key in the secure password input field and click **Save API Credentials**.
5.  Type a question about Pune crime analytics in the chat box. E.g.:
    *   *"How many crimes occurred in Hinjawadi in total?"*
    *   *"Who are the top 5 highest risk suspects in the Koregaon Park Cartel?"*
    *   *"List all incidents with High severity in Kothrud."*
6.  The chatbot will translate your question into a SQLite query, execute it, display the query logs (collapsible expander), and explain the response.

---

## 🛡️ License & Credit

This project is developed for Datathon analytics and law enforcement modeling purposes. All generated suspect records are synthetic and randomized for demonstration.

**Made by Shreya**