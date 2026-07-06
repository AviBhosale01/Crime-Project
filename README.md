# 🛡️ Pune Crime Intelligence Command Center (PCICC)

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Streamlit App](https://img.shields.io/badge/Streamlit-v1.30+-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Database](https://img.shields.io/badge/SQLite-3-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![AI/ML](https://img.shields.io/badge/Scikit--Learn-Latest-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![LLM Support](https://img.shields.io/badge/Gemini%20%2F%20OpenAI-Integrated-8E44AD.svg?style=for-the-badge&logo=google-gemini&logoColor=white)](#)

An advanced, premium-tier AI-powered Geospatial Analytics, Suspect Risk Profiling, and Criminal Social Network Linkage platform built specifically for **Pune, Maharashtra, India**. 

Equipped with a **Text-to-SQL AI Chatbot**, the platform allows investigators to ask natural language questions, automatically queries the SQLite database, and presents smart analytics.

---

## 🌟 Key Features

*   **📊 Command Dashboard**: Real-time KPI indicators showcasing active crime metrics, DBSCAN-generated hotspots, high-risk recidivists, and daily anomaly spikes (Z-score analysis).
*   **🗺️ Geospatial Intelligence Map**: Plotly Mapbox maps centered on Pune showing crime distribution. Includes DBSCAN clustering layers and Kernel Density Heatmaps to isolate active crime zones.
*   **🔍 Intelligence Explorer & Search**: Search directory supporting text-filtering over **2,050 suspects** and **3,000+ crime logs**. Features a detailed **Suspect Dossier Inspector** linking biographical indicators and incident timelines.
*   **🧠 AI Predictive Models**:
    *   *Incident Severity Predictor*: Random Forest Classifier predicting Low/Medium/High incident severity based on socio-economic and temporal factors.
    *   *Recidivism Risk Forecaster*: Random Forest Regressor predicting a repeat offender's risk index.
    *   *Socio-Economic Correlation*: Interactive Pearson correlation metrics tracking crime density vs. local poverty and unemployment.
*   **🕸️ Criminal Network Analysis**: Interactive social link analysis of cliques and associates. Employs NetworkX centrality scores to identify associate hubs (degree centrality) and bridge figures (betweenness centrality).
*   **📝 CRUD Intel Entry**: Clean form validation interfaces to log crime incidents, register new suspects, and model criminal connections. Saving new data automatically clears cache for instant search indexing.
*   **💬 AI Intelligence Chatbot**: A secure conversational interface supporting Gemini & OpenAI API keys. Auto-translates English questions into SQLite code, queries the database, and summarizes results contextually.

---

## 🛠️ Technology Stack

*   **Frontend UI & Dashboard**: Streamlit (Premium Custom Dark Matter styling)
*   **Data Wrangling**: Pandas, NumPy
*   **Visualizations & Maps**: Plotly Express/GO, Folium, Mapbox
*   **Machine Learning**: Scikit-Learn (Random Forests, Isolation Forest, DBSCAN)
*   **Network Graphs**: NetworkX
*   **Database Management**: SQLite3
*   **AI Chatbot Engine**: Google Generative AI (`gemini-1.5-flash`), OpenAI API (`gpt-3.5-turbo`)

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
├── 📄 database.py         # SQLite connection & database seeding
├── 📄 analytics.py        # ML predictors & anomaly detection
├── 📄 visualizations.py   # Plotly charts, Mapbox maps, & NetworkX
├── 📄 requirements.txt    # Library dependencies
└── 📄 README.md           # Documentation
```

### Step 2: Install Dependencies
Open your terminal inside the project directory and run:
```bash
pip install -r requirements.txt
```
*Note: This installs essential packages including `streamlit`, `scikit-learn`, `networkx`, `plotly`, `google-generativeai`, and `openai`.*

### Step 3: Run the Application
Start the Streamlit development server:
```bash
streamlit run app.py
```
The server will boot up and print local URLs. The application will open automatically in your browser at `http://localhost:8501`.

---

## 💬 Using the AI Chatbot

1.  Navigate to the **💬 AI Intel Chatbot** page in the left sidebar.
2.  Choose your provider (**Gemini** or **OpenAI**).
3.  Enter your API Key in the secure password input field and click **Save API Credentials**.
4.  Type a question about Pune crime analytics in the chat box. E.g.:
    *   *"How many crimes occurred in Hinjawadi in total?"*
    *   *"Who are the top 5 highest risk suspects in the Koregaon Park Cartel?"*
    *   *"List all incidents with High severity in Kothrud."*
5.  The chatbot will translate your question into a SQLite query, execute it, display the query logs (collapsible expander), and explain the response.

---

## 🛡️ License

This project is developed for Datathon analytics and law enforcement modeling purposes. All generated suspect records are synthetic and randomized for demonstration.
