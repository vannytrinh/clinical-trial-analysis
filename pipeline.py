import sqlite3
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DB_FILE = "clinical_trial.db"

def run_pipeline():
    conn = sqlite3.connect(DB_FILE)

    populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    
    # PART 2: Relative Frequency Summary Table
    counts_df = pd.read_sql_query(
        "SELECT sample, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte FROM cell_counts;", 
        conn
    )

    # Calculate total number of cells 
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

    # PART 3: Responder Statistics

    # Extract relative cell frequencies for miraclib-treated melanoma PBMC samples, grouped by responder status
    query_melanoma_pbmc_response = """
    SELECT 
        f.population,
        f.percentage,
        LOWER(s.response) AS response
    FROM summary_frequencies f
    JOIN samples s ON f.sample = s.sample
    JOIN subjects sub ON s.subject = sub.subject
    WHERE LOWER(sub.condition) = 'melanoma'
      AND LOWER(s.treatment) = 'miraclib'
      AND UPPER(s.sample_type) = 'PBMC'
      AND LOWER(s.response) IN ('yes', 'no');
    """
    melanoma_response_df = pd.read_sql_query(query_melanoma_pbmc_response, conn)


    stat_results = []

    # Compare responders vs. non-responders for each cell population
    for pop in populations:
        subset = melanoma_response_df[melanoma_response_df["population"] == pop]

        resp = subset[subset["response"] == "yes"]["percentage"]
        non_resp = subset[subset["response"] == "no"]["percentage"]

        # Primary test: Non-parametric Mann-Whitney U
        mw_stat, mw_pval = stats.mannwhitneyu(resp, non_resp, alternative="two-sided")
        
        # Secondary sanity check: Parametric Welch's t-test
        welch_stat, welch_pval = stats.ttest_ind(resp, non_resp, equal_var=False)

        stat_results.append({
            "population": pop,
            "responder_median": float(resp.median()),
            "non_responder_median": float(non_resp.median()),
            "mw_stat": float(mw_stat),
            "mw_pval": float(mw_pval),
            "welch_stat": float(welch_stat),
            "welch_pval": float(welch_pval),
        })

    # Store statistical analysis for dashboard
    stat_df = pd.DataFrame(stat_results)
    stat_df.to_sql("statistical_results", conn, if_exists="replace", index=False)

    # PART 4: Baseline Subset Analysis

    cur = conn.cursor()

    # All baseline samples (t=0) for melanoma PBMC miraclib-treated subjects
    baseline_samples_df = pd.read_sql_query(
        """
        SELECT 
            s.sample,
            s.subject,
            s.project,
            COALESCE(s.response, 'Unknown') AS response,
            sub.sex,
            s.time_from_treatment_start
        FROM samples s
        JOIN subjects sub ON s.subject = sub.subject
        WHERE LOWER(sub.condition) = 'melanoma'
        AND LOWER(s.treatment) = 'miraclib'
        AND UPPER(s.sample_type) = 'PBMC'
        AND s.time_from_treatment_start = 0
        ORDER BY s.project, s.subject;
    """,
        conn,
    )

    # Store sample list for downstream queries and dashboard
    baseline_samples_df.to_sql(
        "baseline_samples", conn, if_exists="replace", index=False
    )

    # Extend query to calculate samples per project, per response, and per sex for baseline cohort
    project_counts = pd.read_sql_query(
        """
        SELECT project, COUNT(sample) AS sample_count
        FROM baseline_samples
        GROUP BY project
        ORDER BY sample_count DESC;
    """,
        conn,
    )

    responder_counts = pd.read_sql_query(
        """
        SELECT response, COUNT(DISTINCT subject) AS subject_count
        FROM baseline_samples
        GROUP BY response
        ORDER BY subject_count DESC;
    """,
        conn,
    )

    sex_counts = pd.read_sql_query(
        """
        SELECT sex, COUNT(DISTINCT subject) AS subject_count
        FROM baseline_samples
        GROUP BY sex
        ORDER BY subject_count DESC;
    """,
        conn,
    )

    # Store baseline cohort metrics for dashboard
    project_counts.to_sql(
        "baseline_project_counts", conn, if_exists="replace", index=False
    )
    responder_counts.to_sql(
        "baseline_responder_counts", conn, if_exists="replace", index=False
    )
    sex_counts.to_sql(
        "baseline_sex_counts", conn, if_exists="replace", index=False
    )    

    # Average B cells for Melanoma males, all sample/treatment types, responders, time=0
    q_avg_b = """
    SELECT COALESCE(ROUND(AVG(c.b_cell), 2), 0.0) AS avg_b_cells
    FROM cell_counts c
    JOIN samples s ON c.sample = s.sample
    JOIN subjects sub ON s.subject = sub.subject
    WHERE LOWER(TRIM(sub.condition)) = 'melanoma'
    AND LOWER(TRIM(sub.sex)) IN ('m', 'male')
    AND LOWER(TRIM(s.response)) IN ('yes', 'y')
    AND s.time_from_treatment_start = 0;
    """
    avg_b = cur.execute(q_avg_b).fetchone()[0]

    # Print: Average number of B cells for responders at time=0 for Melanoma males of all sample and treatment types
    print(f"Part 4 Average B Cells (Melanoma Male Responders t=0): {avg_b:.2f}")
    
    
    conn.close()

if __name__ == "__main__":
    run_pipeline()