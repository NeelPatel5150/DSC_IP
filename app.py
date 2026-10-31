"""Application entry point. Page scripts live in ``pages``."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.ui import inject_css

st.set_page_config(
    page_title="Student Academic Performance",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

navigation = st.navigation(
    [
        st.Page("pages/0_Dashboard.py", title="Dashboard", default=True),
        st.Page("pages/1_Student_Management.py", title="Student Management"),
        st.Page("pages/2_Upload_Dataset.py", title="Upload Dataset"),
        st.Page("pages/3_Academic_Analysis.py", title="Academic Analysis"),
        st.Page("pages/4_Attendance_Analysis.py", title="Attendance Analysis"),
        st.Page("pages/5_Student_Reports.py", title="Individual Reports"),
        st.Page("pages/6_Risk_Identification.py", title="Risk Identification"),
        st.Page("pages/7_Prediction.py", title="Prediction"),
    ]
)
navigation.run()
