import sqlite3
import pandas as pd

DB_FILE = "clinical_trial.db"
CSV_FILE = "cell-count.csv"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Subjects table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        subject TEXT PRIMARY KEY,
        age INTEGER,
        sex TEXT,
        condition TEXT
    );
    """)

    # Samples table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS samples (
        sample TEXT PRIMARY KEY,
        subject TEXT,
        project TEXT,
        treatment TEXT,
        response TEXT,
        sample_type TEXT,
        time_from_treatment_start INTEGER,
        FOREIGN KEY (subject) REFERENCES subjects (subject)
    );
    """)

    # Cell Counts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cell_counts (
        sample TEXT PRIMARY KEY,
        b_cell REAL,
        cd8_t_cell REAL,
        cd4_t_cell REAL,
        nk_cell REAL,
        monocyte REAL,
        FOREIGN KEY (sample) REFERENCES samples (sample)
    );
    """)
    conn.commit()
    return conn

def load_data():
    df = pd.read_csv(CSV_FILE)

    # Clean duplicate sample rows 
    df = df.drop_duplicates(subset=["sample"])

    conn = init_db()

    # Insert unique subjects 
    subjects_df = df[["subject", "age", "sex", "condition"]].drop_duplicates(subset=["subject"])
    subjects_df.to_sql("subjects", conn, if_exists="append", index=False)

    # Insert samples
    samples_df = df[[
        "sample", "subject", "project", "treatment", 
        "response", "sample_type", "time_from_treatment_start"
    ]]
    samples_df.to_sql("samples", conn, if_exists="append", index=False)

    # Insert counts
    counts_df = df[["sample", "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]]
    counts_df.to_sql("cell_counts", conn, if_exists="append", index=False)

    conn.close()


if __name__ == "__main__":
    load_data()