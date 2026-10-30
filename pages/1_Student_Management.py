"""Add, edit, search, and delete student records."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.config import MARK_SCHEMES
from modules.data_cleaning import is_blank
from modules.database import delete_student, import_records, list_student_ids
from modules.reporting import build_student_report, subject_table
from modules.ui import banner, display_table, empty_state, filter_performance, flash, loading, open_records, prepare_page
from modules.validation import validate_student_dict


def _label(frame, student_id: str) -> str:
    name = frame.loc[frame["student_id"] == student_id, "student_name"].iloc[0]
    return f"{student_id} — {name}"


settings = prepare_page()
banner(
    "Student Management",
    "Search the stored records, then add, edit, or delete one student. Deletes ask for confirmation.",
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No students stored", "Add one below, or load the sample from the Dashboard.")
else:
    view = filter_performance(performance)
    st.caption(
        "Rank is calculated on the full database, inside the same semester, department, and recorded-subject group. "
        "Filters only change which rows are shown."
    )
    display_table(view)

st.divider()
add_tab, edit_tab, profile_tab, delete_tab = st.tabs(["Add", "Edit", "Profile", "Delete"])


def _remember(key: str, default):
    """Set a widget's first value before the widget is created."""
    if key not in st.session_state:
        st.session_state[key] = default


def _mark_inputs(prefix: str, defaults: dict | None = None) -> dict:
    values = {}
    defaults = defaults or {}
    for scheme in MARK_SCHEMES:
        column = scheme["column"]
        current = defaults.get(column)
        missing = is_blank(current)
        number_key = f"{prefix}_{column}"
        blank_key = f"{prefix}_{column}_blank"
        _remember(number_key, 0.0 if missing else float(current))
        _remember(blank_key, missing)
        left, right = st.columns([3, 1])
        with left:
            number = st.number_input(
                f"{scheme['subject_name']} (out of {scheme['maximum']:g})",
                min_value=0.0,
                max_value=float(scheme["maximum"]),
                step=0.5,
                key=number_key,
            )
        with right:
            not_recorded = st.checkbox("Not recorded", key=blank_key)
        values[column] = None if not_recorded else float(number)
    return values


with add_tab:
    st.caption("A mark of 0 is a genuine zero. Choose Not recorded when that exam has no result.")
    with st.form("add_student"):
        student_id = st.text_input("Student ID")
        student_name = st.text_input("Student name")
        semester = st.text_input("Semester", value="Semester 7")
        department = st.text_input("Department", value="Computer Science")
        attendance = st.number_input("Attendance %", min_value=0.0, max_value=100.0, value=75.0, step=0.5)
        study_hours = st.number_input(
            "Study hours per day", min_value=0.0, max_value=16.0, value=2.0, step=0.5
        )
        marks = _mark_inputs("add")
        submitted = st.form_submit_button("Save student", type="primary")
    if submitted:
        record = {
            "student_id": student_id,
            "student_name": student_name,
            "semester": semester,
            "department": department,
            "attendance_percentage": attendance,
            "study_hours": study_hours,
            **marks,
        }
        report = validate_student_dict(record)
        if report.has_structural_error or report.row_errors:
            messages = list(report.file_errors)
            messages.extend(message for item in report.row_errors for message in item["messages"])
            st.error(" ".join(messages))
        elif record["student_id"].strip().upper() in set(list_student_ids()):
            st.error("This student ID is already stored. Use the Edit tab to change it.")
        else:
            with loading("Saving the student…"):
                result = import_records(report.valid_frame, update_existing=False)
            if result.inserted:
                flash(f"Saved {result.inserted[0]}.")
                st.rerun()
            st.warning("The student was not saved.")

with edit_tab:
    if performance.empty:
        empty_state("Nothing to edit", "Add a student before editing.")
    else:
        selected = st.selectbox(
            "Student to edit",
            performance["student_id"].tolist(),
            format_func=lambda value: _label(performance, value),
        )
        current = performance[performance["student_id"] == selected].iloc[0].to_dict()
        st.caption("Student ID stays the same. Delete the row and add a new one if the ID itself is wrong.")
        with st.form(f"edit_{selected}"):
            student_name = st.text_input("Student name", value=str(current["student_name"]))
            semester = st.text_input("Semester", value=str(current["semester"]))
            department = st.text_input("Department", value=str(current["department"]))
            attendance = st.number_input(
                "Attendance %",
                min_value=0.0,
                max_value=100.0,
                value=float(current["attendance_percentage"]),
                step=0.5,
            )
            study_hours = st.number_input(
                "Study hours per day",
                min_value=0.0,
                max_value=16.0,
                value=float(current["study_hours"]),
                step=0.5,
            )
            marks = _mark_inputs(f"edit_{selected}", current)
            submitted = st.form_submit_button("Update student", type="primary")
        if submitted:
            record = {
                "student_id": selected,
                "student_name": student_name,
                "semester": semester,
                "department": department,
                "attendance_percentage": attendance,
                "study_hours": study_hours,
                **marks,
            }
            report = validate_student_dict(record)
            if report.row_errors or report.has_structural_error:
                messages = [message for item in report.row_errors for message in item["messages"]]
                st.error(" ".join(messages) or "The student could not be updated.")
            else:
                with loading("Updating the student…"):
                    result = import_records(report.valid_frame, update_existing=True)
                if result.updated or result.inserted:
                    flash(f"Updated {selected}.")
                    st.rerun()
                st.warning("The student was not updated.")

with profile_tab:
    if performance.empty:
        empty_state("No profile yet", "Add a student before opening a profile.")
    else:
        selected = st.selectbox(
            "Student profile",
            performance["student_id"].tolist(),
            format_func=lambda value: _label(performance, value),
            key="profile_student",
        )
        report = build_student_report(
            selected,
            performance,
            pass_percent=settings["pass_percent"],
            attendance_threshold=settings["attendance_threshold"],
            overall_threshold=settings["overall_threshold"],
        )
        if report is None:
            st.warning("That student is no longer in the database.")
        else:
            for label, value in report["fields"]:
                st.write(f"**{label}:** {value}")
            st.dataframe(subject_table(report), width="stretch", hide_index=True)

with delete_tab:
    if performance.empty:
        empty_state("Nothing to delete", "There are no stored students.")
    else:
        selected = st.selectbox(
            "Student to delete",
            performance["student_id"].tolist(),
            format_func=lambda value: _label(performance, value),
            key="delete_student",
        )
        st.warning(f"This permanently deletes {selected} and every mark stored for that ID.")
        confirm = st.checkbox(f"I confirm deletion of {selected}")
        if st.button("Delete student", disabled=not confirm):
            with loading("Deleting the student…"):
                removed = delete_student(selected)
            if removed:
                flash(f"Deleted {selected}.")
                st.rerun()
            st.error("That student was not found.")
