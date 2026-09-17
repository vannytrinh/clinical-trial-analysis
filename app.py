import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Increase element render limit for displaying data in dashboard 
pd.set_option("styler.render.max_elements", 262500)

st.set_page_config(page_title="Loblaw Bio Dashboard", layout="wide")

@st.cache_resource
def get_connection():
    return sqlite3.connect("clinical_trial.db", check_same_thread=False)

conn = get_connection()

st.title("Loblaw Bio: Miraclib Clinical Trial Analysis")

tab1, tab2, tab3 = st.tabs([
    "Part 2: Cell Frequencies", 
    "Part 3: Responder Statistics", 
    "Part 4: Baseline Cohorts"
])

# PART 2: Relative Frequency Summary Table
with tab1:
    st.header("Relative Cell Population Frequencies")

    # Allow user to filter by sample ID or All 
    sample_list = pd.read_sql("SELECT DISTINCT sample FROM summary_frequencies;", conn)["sample"].tolist()
    selected_sample = st.selectbox("Filter by Sample ID (or view all)", ["All"] + sample_list)
    
    if selected_sample == "All":
        freq_df = pd.read_sql("SELECT * FROM summary_frequencies;", conn)
    else:
        freq_df = pd.read_sql("SELECT * FROM summary_frequencies WHERE sample = ?;", conn, params=(selected_sample,))

    # Display frequency table
    st.dataframe(freq_df.style.format({"percentage": "{:.2f}%", "count": "{:.0f}", "total_count": "{:.0f}"}), use_container_width=True)

# PART 3: Responder Visualization and Statistics
with tab2:
    st.header("Melanoma PBMC Response Comparison (Miraclib)")

    # Plot boxplot comparing responders vs. non-responders for each cell population 
    st.subheader("Visual Comparison")

    query_melanoma_pbmc_response = """
    SELECT f.population, f.percentage, s.response
    FROM summary_frequencies f
    JOIN samples s ON f.sample = s.sample
    JOIN subjects sub ON s.subject = sub.subject
    WHERE LOWER(sub.condition) = 'melanoma'
      AND LOWER(s.treatment) = 'miraclib'
      AND UPPER(s.sample_type) = 'PBMC'
      AND LOWER(s.response) IN ('yes', 'no');
    """
    melanoma_response_df = pd.read_sql(query_melanoma_pbmc_response, conn)

    # Allow user to filter populations
    available_populations = sorted(melanoma_response_df["population"].unique())
    selected_populations = st.multiselect(
        "Select Cell Populations to Display:",
        options=available_populations,
        default=available_populations
    )

    plot_df = melanoma_response_df[melanoma_response_df["population"].isin(selected_populations)]

    if not plot_df.empty:
        fig = px.box(
            plot_df,
            x="population",
            y="percentage",
            color="response",
            category_orders={"response": ["no", "yes"]},
            color_discrete_map={"no": "#7f7f7f", "yes": "#1f77b4"},
            labels={
                "percentage": "Relative Frequency (%)",
                "population": "Cell Population",
                "response": "Response",
            },
            title="Cell Population Relative Frequencies: Responders vs. Non-Responders",
            height=600,
        )
        fig.update_layout(boxmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one cell population to display.")  

    # Show statistical results for Mann-Whitney U test and Welch's t-test
    stat_df = pd.read_sql("SELECT * FROM statistical_results;", conn)

    # Split statistical results into primary and secondary views
    # And evaluate significance based on p-value < 0.05
    mw_df = stat_df[[
        "population", "responder_median", "non_responder_median", 
        "mw_stat", "mw_pval"
    ]].rename(columns={
        "population": "Cell Population",
        "responder_median": "Responder Median (%)",
        "non_responder_median": "Non-Responder Median (%)",
        "mw_stat": "U Statistic",
        "mw_pval": "p-value",
    })
    mw_df["Significant (p < 0.05)"] = mw_df["p-value"] < 0.05


    welch_df = stat_df[[
        "population", "welch_stat", "welch_pval"
    ]].rename(columns={
        "population": "Cell Population",
        "welch_stat": "Welch's t-test Statistic",
        "welch_pval": "Welch's t-test p-value"
    })
    welch_df["Significant (p < 0.05)"] = welch_df["Welch's t-test p-value"] < 0.05

    # Display tables for Mann-Whitney U test and Welch's t-test results 
    st.subheader("Statistical Analysis (Mann-Whitney U Test)")

    st.success("""
    **Key Finding: CD4+ T Cells Differentiate Responders from Non-Responders**

    * **Significant Biomarker Signal:** Among all five evaluated immune cell lineages, only **CD4+ T cells** exhibit a statistically significant difference in relative frequency between responders and non-responders ($p = 0.0133$, Mann-Whitney U test).
    * **Direction of Effect:** Responders demonstrate an elevated median CD4+ T cell frequency (**30.22%**) relative to non-responders (**29.66%**).
    * **Cross-Validation:** This finding is reinforced by an auxiliary Welch's t-test ($t = 2.8094, p = 0.0050$), confirming the distribution shift across both non-parametric and parametric models.
    * **Other Lineages:** No significant frequency differences were observed for B cells, CD8+ T cells, NK cells, or monocytes ($p > 0.05$).
    """)

    st.dataframe(
        mw_df.style.format({
            "Responder Median (%)": "{:.2f}%",
            "Non-Responder Median (%)": "{:.2f}%",
            "U Statistic": "{:.1f}",
            "p-value": "{:.4f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("View Auxiliary Parametric Test Results (Welch's t-Test)"):
        st.dataframe(
            welch_df.style.format({
                "Welch's t-test p-value": "{:.4f}"
            }),
            use_container_width=True,
            hide_index=True
        )

# PART 4: Baseline Cohort Exploration
with tab3:
    st.subheader("Baseline Cohort Exploration (t = 0)")
    st.markdown(
        """
        Exploratory subset analysis for **Melanoma PBMC** samples collected at 
        baseline (`time_from_treatment_start = 0`) from subjects treated with **miraclib**.
        """
    )

    # Read precomputed DataFrames
    baseline_samples_df = pd.read_sql_query("SELECT * FROM baseline_samples;", conn)
    project_counts = pd.read_sql_query("SELECT * FROM baseline_project_counts;", conn)
    responder_counts = pd.read_sql_query("SELECT * FROM baseline_responder_counts;", conn)
    sex_counts = pd.read_sql_query("SELECT * FROM baseline_sex_counts;", conn)


# 1. Collapsible Baseline Samples Table
    with st.expander(
        f"View Baseline Sample Records (N = {len(baseline_samples_df)})",
        expanded=False,
    ):
        st.dataframe(
            baseline_samples_df.rename(
                columns={
                    "subject": "Subject ID",
                    "sample": "Sample ID",
                    "project": "Project",
                    "response": "Response",
                    "sex": "Sex",
                    "time_from_treatment_start": "Time (t)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # 2. Breakdown Visualizations (Consistent Horizontal Bar Charts)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Samples per Project**")
        fig_proj = px.bar(
            project_counts,
            x="sample_count",
            y="project",
            orientation="h",
            text="sample_count",
            color_discrete_sequence=["#109618"],  # Clinical Green
            height=320,
        )
        fig_proj.update_traces(textposition="outside")
        fig_proj.update_layout(
            xaxis_title="Samples",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=25, t=10, b=10),
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    with col2:
        st.markdown("**Subjects by Response**")
        fig_resp = px.bar(
            responder_counts,
            x="subject_count",
            y="response",
            orientation="h",
            text="subject_count",
            color="response",
            color_discrete_map={"no": "#7f7f7f", "yes": "#1f77b4"},
            height=320,
        )
        fig_resp.update_traces(textposition="outside")
        fig_resp.update_layout(
            showlegend=False,
            xaxis_title="Subjects",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=25, t=10, b=10),
        )
        st.plotly_chart(fig_resp, use_container_width=True)

    with col3:
        st.markdown("**Subjects by Sex**")
        fig_sex = px.bar(
            sex_counts,
            x="subject_count",
            y="sex",
            orientation="h",
            text="subject_count",
            color_discrete_sequence=["#990099"],  # Plum / Violet
            height=320,
        )
        fig_sex.update_traces(textposition="outside")
        fig_sex.update_layout(
            xaxis_title="Subjects",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=25, t=10, b=10),
        )
        st.plotly_chart(fig_sex, use_container_width=True)