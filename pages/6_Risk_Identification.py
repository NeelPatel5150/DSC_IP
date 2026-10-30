"""Students who match a published review rule, with the reason written out."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.data_loader import dataframe_to_csv_bytes
from modules.risk import build_flag_table, reason_counts
from modules.ui import banner, display_table, empty_state, filter_performance, loading, open_records, prepare_page, show_chart
from modules.visualization import reason_chart

settings = prepare_page()
banner(
    "Academic Risk Identification",
    "Needs academic review means a rule matched. It does not decide the student's ability.",
)

st.info(
    "These flags are decision-support indicators. A teacher can use them to decide who may benefit "
    "from additional support. They are not a final result and they are not a label of weak ability."
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No records yet", "Load or add student records before running the review rules.")
    st.stop()

view = filter_performance(performance)
if view.empty:
    empty_state("No matches", "No students match these filters.")
    st.stop()

with loading("Checking review rules…"):
    flags = build_flag_table(
        view,
        pass_percent=settings["pass_percent"],
        attendance_threshold=settings["attendance_threshold"],
        overall_threshold=settings["overall_threshold"],
    )
    counts = reason_counts(flags)

left, right = st.columns(2)
left.metric("Students in this view", len(view))
right.metric("May benefit from additional support", 0 if flags.empty else int(flags["student_id"].nunique()))
st.caption(
    f"Current rules: attendance below {settings['attendance_threshold']:.0f}%, "
    f"any recorded pass component below {settings['pass_percent']:.0f}% of its maximum, "
    f"subject percentage below {settings['overall_threshold']:.0f}%, "
    "or a missing examination result. Change the thresholds from the sidebar."
)

show_chart(reason_chart(counts), "No review rules matched the students in this filter.")

if flags.empty:
    st.success("No student in this filter currently matches a review rule.")
else:
    display_table(
        flags,
        columns=(
            "student_id",
            "student_name",
            "semester",
            "department",
            "attendance_percentage",
            "subject_percentage",
            "result_status",
            "reasons",
        ),
    )
    download = flags.drop(columns=["reason_codes"])
    st.download_button(
        "Download review list",
        data=dataframe_to_csv_bytes(download),
        file_name="academic_review.csv",
        mime="text/csv",
    )
