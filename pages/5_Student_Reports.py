"""One student at a time. Class averages are included. Other students' marks are not."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.reporting import build_student_report, report_to_csv_bytes, report_to_pdf_bytes, subject_table
from modules.ui import banner, empty_state, filter_performance, loading, open_records, prepare_page

settings = prepare_page()
banner(
    "Individual Report",
    "The report uses one stored student. Subject averages come from that student's semester and department.",
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No records yet", "Load or add student records before opening a report.")
    st.stop()

view = filter_performance(performance)
if view.empty:
    empty_state("No matches", "No students match these filters.")
    st.stop()

selected = st.selectbox(
    "Student",
    view["student_id"].tolist(),
    format_func=lambda value: (
        f"{value} — {view.loc[view['student_id'] == value, 'student_name'].iloc[0]}"
    ),
)
with loading("Building the report…"):
    report = build_student_report(
        selected,
        performance,
        pass_percent=settings["pass_percent"],
        attendance_threshold=settings["attendance_threshold"],
        overall_threshold=settings["overall_threshold"],
    )
if report is None:
    st.warning("That student is no longer available.")
    st.stop()

st.caption(report["rules_note"])
for label, value in report["fields"]:
    st.write(f"**{label}:** {value}")

st.subheader("Subject marks")
st.dataframe(subject_table(report), width="stretch", hide_index=True)
st.caption(
    "The class average includes this student and the other stored students in the same semester and department. "
    "Students without a mark for a component are left out of that component's average."
)

left, right = st.columns(2)
with left:
    st.markdown("**Strengths**")
    if report["strengths"]:
        for item in report["strengths"]:
            st.write(f"- {item}")
    else:
        st.write("None identified by the current rules.")
with right:
    st.markdown("**Areas that may need support**")
    if report["improvements"]:
        for item in report["improvements"]:
            st.write(f"- {item}")
    else:
        st.write("None identified by the current rules.")

st.subheader("Suggestions")
for text in report["suggestions"]:
    st.write(f"- {text}")

csv_col, pdf_col = st.columns(2)
with csv_col:
    st.download_button(
        "Download CSV report",
        data=report_to_csv_bytes(report),
        file_name=f"{report['student_id']}_report.csv",
        mime="text/csv",
    )
with pdf_col:
    try:
        with loading("Preparing the PDF…"):
            pdf_bytes = report_to_pdf_bytes(report)
    except Exception as exc:
        st.caption(f"PDF export is unavailable: {exc}")
    else:
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name=f"{report['student_id']}_report.pdf",
            mime="application/pdf",
        )
