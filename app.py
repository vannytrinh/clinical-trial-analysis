import streamlit as st
import sqlite3
import pandas as pd

# Increase element render limit for displaying data in dashboard 
pd.set_option("styler.render.max_elements", 262500)

st.set_page_config(page_title="Loblaw Bio Dashboard")

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
        freq_df = pd.read_sql("SELECT * FROM summary_frequencies LIMIT 500;", conn)
    else:
        freq_df = pd.read_sql("SELECT * FROM summary_frequencies WHERE sample = ?;", conn, params=(selected_sample,))

    # Display frequency table
    st.dataframe(freq_df.style.format({"percentage": "{:.2f}%", "count": "{:.0f}", "total_count": "{:.0f}"}), use_container_width=True)

