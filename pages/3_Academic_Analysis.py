"""Subject averages, grades, and rankings for the filtered students."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.analytics import subject_summary
from modules.ui import banner, display_table, empty_state, filter_performance, loading, open_records, prepare_page, show_chart
from modules.visualization import (
    grade_donut,
    pass_fail_chart,
    percentage_histogram,
    student_comparison_chart,
    subject_average_chart,
)

settings = prepare_page()
banner(
    "Academic Analysis",
    "Averages, grades, and the pass rate below are calculated from the filtered students.",
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No records yet", "Load or add student records before running the academic analysis.")
    st.stop()

view = filter_performance(performance)
if view.empty:
    empty_state("No matches", "No students match these filters.")
    st.stop()

with loading("Preparing the academic summary…"):
    summary = subject_summary(view)
st.subheader("Component summary")
st.caption(
    "Highest and lowest use recorded marks only. A blank result is not treated as zero, "
    "so it does not become the lowest mark."
)
display_table(
    summary,
    columns=("subject", "students_recorded", "average", "highest", "lowest", "maximum_marks", "average_percent"),
)

left, right = st.columns(2)
with left:
    show_chart(subject_average_chart(summary), "No recorded marks to average.")
with right:
    show_chart(grade_donut(view), "No letter grades in this filter.")

left, right = st.columns(2)
with left:
    show_chart(percentage_histogram(view), "No subject percentages to plot.")
with right:
    show_chart(pass_fail_chart(view), "No results to plot.")

st.subheader("Ranking")
st.caption(
    "Rank 1 is the highest subject percentage. Students are ranked only with peers who share the same "
    "semester, department, and set of recorded subjects. The rank comes from the full database. "
    "This filter chooses who is listed, and it does not renumber the ranks."
)
ranking = view.dropna(subset=["subject_percentage"]).sort_values(
    ["semester", "department", "class_rank"], ascending=[True, True, True]
)
display_table(
    ranking,
    columns=(
        "class_rank",
        "student_id",
        "student_name",
        "semester",
        "department",
        "subjects_recorded",
        "subject_percentage",
        "grade",
        "result_status",
    ),
)

st.subheader("Compare selected students")
options = view["student_id"].tolist()
selected = st.multiselect(
    "Students",
    options,
    default=options[:5],
    max_selections=8,
    format_func=lambda value: f"{value} — {view.loc[view['student_id'] == value, 'student_name'].iloc[0]}",
)
st.caption("Missing subject marks are left blank on the chart. They are not drawn as zero.")
show_chart(
    student_comparison_chart(view, selected),
    "Select at least one student to compare subject marks.",
)
