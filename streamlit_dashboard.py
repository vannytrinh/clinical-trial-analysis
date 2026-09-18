import os
import subprocess
import sys
import runpy
import streamlit as st

# Tell Streamlit this is an active app
st.set_page_config(page_title="Clinical Trial Analysis", layout="wide")

DB_FILE = "clinical_trial.db"

if not os.path.exists(DB_FILE):
    with st.spinner("Building clinical trial database..."):
        # Use sys.executable to ensure the correct virtualenv python is used
        subprocess.run([sys.executable, "load_data.py"], check=True)
        subprocess.run([sys.executable, "pipeline.py"], check=True)

# Run app.py cleanly in its own execution context
runpy.run_path("app.py", run_name="__main__")