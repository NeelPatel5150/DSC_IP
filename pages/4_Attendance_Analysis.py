"""Attendance, study hours, and how they move with marks in this dataset."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.analytics import describe_correlation, pearson
from modules.ui import banner, empty_state, filter_performance, open_records, prepare_page, show_chart
from modules.visualization import (
    attendance_scatter,
    correlation_heatmap,
    internal_final_scatter,
    study_hours_scatter,
)

settings = prepare_page()
banner(
    "Attendance and Study Habits",
    "These charts describe the filtered records. A correlation is not evidence that one habit causes higher marks.",
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No records yet", "Load or add student records before looking at attendance and study habits.")
    st.stop()

view = filter_performance(performance)
if view.empty:
    empty_state("No matches", "No students match these filters.")
    st.stop()

if "attendance_percentage" not in view.columns:
    st.warning("Attendance is not in this dataset, so the attendance chart is unavailable.")
else:
    attendance_r, attendance_n = pearson(view, "attendance_percentage", "subject_percentage")
    st.write(describe_correlation(attendance_r, attendance_n, "attendance", "subject percentage"))
    show_chart(attendance_scatter(view), "Attendance and subject percentage need at least two complete pairs.")

if "study_hours" not in view.columns:
    st.warning("Study hours are not in this dataset, so that chart is unavailable.")
else:
    study_r, study_n = pearson(view, "study_hours", "subject_percentage")
    st.write(describe_correlation(study_r, study_n, "study hours", "subject percentage"))
    show_chart(study_hours_scatter(view), "Study hours and subject percentage need at least two complete pairs.")

internal_available = view["internal_marks"].notna().any() if "internal_marks" in view.columns else False
final_available = view["final_marks"].notna().any() if "final_marks" in view.columns else False
if not internal_available or not final_available:
    missing = []
    if not internal_available:
        missing.append("internal marks")
    if not final_available:
        missing.append("final marks")
    st.info("The internal-versus-final chart is hidden because this view has no " + " or ".join(missing) + ".")
else:
    internal_r, internal_n = pearson(view, "internal_marks", "final_marks")
    st.write(describe_correlation(internal_r, internal_n, "internal marks", "final marks"))
    show_chart(internal_final_scatter(view), "Not enough paired internal and final marks to draw the chart.")

st.subheader("Correlation heatmap")
show_chart(
    correlation_heatmap(view),
    "A heatmap needs at least two numeric columns with five or more varying values.",
)
st.caption(
    "Pearson r is near 1 for a strong positive association, near -1 for a strong negative association, "
    "and near 0 when the linear association is weak. Observational student records cannot prove a cause."
)
