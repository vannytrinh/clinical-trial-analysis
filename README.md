# Clinical Trial Analysis 

A data pipeline and Streamlit dashboard for processing, analyzing, and visualizing clinical trial cell count and cohort data using SQLite.

---

## Live Dashboard

- **Dashboard URL**: [https://clinical-trial-analysis-hvqvbhhk9rjzgv72zk2vos.streamlit.app/](https://clinical-trial-analysis-hvqvbhhk9rjzgv72zk2vos.streamlit.app/)

---

## How to Run

### Using Make 

```bash
# 1. Install dependencies
make setup

# 2. Ingest data and run analysis pipeline
make pipeline

# 3. Launch dashboard
make dashboard
```

---

### Manual Execution Steps

```bash
# 1. Environment Setup
pip install --upgrade pip
pip install -r requirements.txt

# 2. Data Ingestion & Pipeline
python load_data.py
python pipeline.py

# 3. Launch Dashboard
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

---

## Project Structure

```text
clinical-trial-analysis/
├── app.py                 # Streamlit presentation dashboard
├── pipeline.py            # Transformation pipeline and precomputed cohort tables
├── load_data.py           # Raw data ingestion into SQLite
├── clinical_trial.db      # SQLite relational database (created by pipeline)
├── cell-count.csv         # Raw clinical cell count assay dataset
├── Makefile               # Automated build, test, and run directives
├── requirements.txt       # Python package dependencies
├── .gitignore             # Git ignore patterns (.venv, *.db, caches)
└── README.md              # Project documentation and run instructions
```
---

## Database Schema

The pipeline normalizes raw data into an embedded SQLite database (`clinical_trial.db`) across the following core tables:

* **`subjects`**: `subject` (PK), `condition`, `sex`, `age`
* **`samples`**: `sample` (PK), `subject` (FK), `sample_type`, `treatment`, `response`, `time_from_treatment_start`, `project`
* **`cell_counts`**: `sample` (FK), cell population frequencies (`b_cell`, `cd4_t_cell`, `cd8_t_cell`, `nk_cell`, `monocyte`)