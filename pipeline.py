import sqlite3
import pandas as pd

DB_FILE = "clinical_trial.db"

def run_pipeline():
    conn = sqlite3.connect(DB_FILE)
    
    # PART 2: Relative Frequency Summary Table
    counts_df = pd.read_sql_query(
        "SELECT sample, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte FROM cell_counts;", 
        conn
    )

    # Calculate total number of cells 
    populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    counts_df["total_count"] = counts_df[populations].sum(axis=1)

    # Compute relative frequencies (percentage) 
    summary_df = counts_df.melt(
        id_vars=["sample", "total_count"],
        value_vars=populations,
        var_name="population",
        value_name="count"
    )
    summary_df["percentage"] = (summary_df["count"] / summary_df["total_count"]) * 100.0

    # Store summary for downstream analysis and dashboard
    summary_df[["sample", "total_count", "population", "count", "percentage"]].to_sql(
        "summary_frequencies", conn, if_exists="replace", index=False
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_summary_sample ON summary_frequencies(sample, population);")
    
    conn.close()

if __name__ == "__main__":
    run_pipeline()