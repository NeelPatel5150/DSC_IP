"""Home dashboard. Every card is calculated from the current database view."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.service import dashboard_summary, load_sample_into_database
from modules.ui import (
    banner,
    empty_state,
    filter_performance,
    flash,
    format_number,
    loading,
    open_records,
    prepare_page,
    show_chart,
    show_summary,
)
from modules.visualization import grade_donut, pass_fail_chart, subject_average_chart
from modules.analytics import subject_summary

settings = prepare_page()
banner(
    "Student Academic Performance Analysis",
    "Figures on this page are calculated from the students stored in the local database.",
)

performance = open_records(settings["pass_percent"])

if performance.empty:
    empty_state(
        "No records yet",
        "Load the fictional sample to explore the dashboard, or add students from Student Management or Upload Dataset.",
    )
    st.caption("The sample is synthetic. It is not a set of real college results.")
    if st.button("Load sample dataset", type="primary"):
        with loading("Saving the sample records…"):
            result = load_sample_into_database(replace=False)
        flash(f"Loaded {len(result['inserted'])} fictional students.")
        st.rerun()
    st.stop()

view = filter_performance(performance)

if view.empty:
    empty_state("No matches", "No students match these filters. Clear the search or choose All.")
    st.stop()

with loading("Calculating summary and charts…"):
    summary = dashboard_summary(
        view,
        pass_percent=settings["pass_percent"],
        attendance_threshold=settings["attendance_threshold"],
        overall_threshold=settings["overall_threshold"],
    )
    subject_rows = subject_summary(view)
    result_chart = pass_fail_chart(view)
    grade_chart = grade_donut(view)
    average_chart = subject_average_chart(subject_rows)

show_summary(summary)
left, right = st.columns(2)
with left:
    show_chart(result_chart, "There is no pass, fail, or incomplete data to chart.")
with right:
    show_chart(grade_chart, "No letter grades yet, because no subject marks are recorded in this view.")
show_chart(average_chart, "No component averages to chart.")
st.caption(
    "Internal assessment is out of 50 and the other components are out of 100. "
    "The bar chart uses a percentage of each maximum so the components can be compared. "
    f"The highest subject percentage in this view is {format_number(summary['highest'])}."
)
st.caption(
    "Letter grades use the fixed demonstration scale. The sidebar pass mark changes who is counted as Pass or Fail. "
    "More charts are on Academic Analysis and Attendance Analysis."
)
