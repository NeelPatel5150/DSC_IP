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
    attendance_bands_chart,
    attendance_scatter,
    correlation_heatmap,
    study_hours_scatter,
    subject_percentage_by_attendance_band_chart,
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
    left, right = st.columns(2)
    with left:
        show_chart(
            attendance_scatter(view),
            "Attendance and subject percentage need at least two complete pairs.",
        )
    with right:
        show_chart(
            attendance_bands_chart(view, threshold=settings["attendance_threshold"]),
            "No attendance values to group into bands.",
        )
        st.caption(
            f"Bands use the sidebar review threshold ({settings['attendance_threshold']:.0f}%) "
            "and a high band from 85% upward."
        )

if "study_hours" not in view.columns:
    st.warning("Study hours are not in this dataset, so that chart is unavailable.")
else:
    study_r, study_n = pearson(view, "study_hours", "subject_percentage")
    st.write(describe_correlation(study_r, study_n, "study hours", "subject percentage"))
    show_chart(study_hours_scatter(view), "Study hours and subject percentage need at least two complete pairs.")

st.subheader("Attendance bands and subject percentage")
st.caption(
    "Average subject percentage inside each attendance band. "
    "This describes the filtered records only. It does not prove that attendance causes marks."
)
show_chart(
    subject_percentage_by_attendance_band_chart(
        view,
        threshold=settings["attendance_threshold"],
    ),
    "Need attendance and subject percentage values to draw this bar chart.",
)

st.subheader("Correlation heatmap")
show_chart(
    correlation_heatmap(view),
    "A heatmap needs at least two numeric columns with five or more varying values.",
)
st.caption(
    "Pearson r is near 1 for a strong positive association, near -1 for a strong negative association, "
    "and near 0 when the linear association is weak. Observational student records cannot prove a cause."
)
