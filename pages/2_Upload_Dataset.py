"""Upload a CSV or Excel file, check it, and then import the valid rows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from modules.analytics import find_existing_ids
from modules.config import MAX_UPLOAD_BYTES
from modules.data_loader import read_dataframe, sample_csv_bytes, template_csv_bytes
from modules.database import clear_students, import_records, list_student_ids
from modules.service import load_sample_into_database
from modules.ui import banner, flash, loading, prepare_page
from modules.validation import validate_dataframe

prepare_page()
banner(
    "Upload Dataset",
    "Preview the file, correct rows in the table, and import only after the checks are clear.",
)

sample_col, template_col = st.columns(2)
with sample_col:
    st.download_button(
        "Download fictional sample CSV",
        data=sample_csv_bytes(),
        file_name="sample_students.csv",
        mime="text/csv",
    )
with template_col:
    st.download_button(
        "Download empty template",
        data=template_csv_bytes(),
        file_name="student_template.csv",
        mime="text/csv",
    )
st.caption(
    "CSV and Excel (.xlsx) files up to 5 MB are accepted. "
    "A blank mark stays missing. It is not stored as zero. "
    "Lines in a CSV that start with # are treated as comments."
)

uploaded = st.file_uploader("Student file", type=["csv", "xlsx"])
if uploaded is not None:
    if uploaded.size > MAX_UPLOAD_BYTES:
        st.error("This file is larger than 5 MB. Split it or remove extra columns and try again.")
        st.stop()
    try:
        raw = read_dataframe(uploaded, uploaded.name)
    except Exception as exc:
        st.error(
            "Could not read this file. Use a CSV or Excel workbook (.xlsx) with a header row."
        )
        st.caption(str(exc)[:300])
        st.stop()

    file_key = f"{uploaded.name}:{uploaded.size}"
    st.subheader("Preview of the uploaded file")
    st.dataframe(raw.head(15), width="stretch", hide_index=True)
    st.caption(
        f"{len(raw)} data rows and {len(raw.columns)} columns were read. "
        "Edit the working table below before importing. Deleting a row here removes it from the import."
    )

    edited = st.data_editor(
        raw,
        num_rows="dynamic",
        width="stretch",
        key=f"upload_editor_{file_key}",
    )
    report = validate_dataframe(edited)

    valid_col, invalid_col = st.columns(2)
    valid_col.metric("Valid rows", report.valid_count)
    invalid_col.metric("Invalid rows", report.invalid_count)

    if report.file_errors:
        for message in report.file_errors:
            st.error(message)
    if report.missing_columns:
        st.error("Missing required columns: " + ", ".join(report.missing_columns) + ".")
    if report.ignored_columns:
        st.info("These columns will be ignored: " + ", ".join(report.ignored_columns) + ".")
    if report.row_errors:
        st.subheader("Rows that need a correction")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Row": item["row_number"],
                        "Student ID": item["student_id"],
                        "Issues": "; ".join(item["messages"]),
                    }
                    for item in report.row_errors
                ]
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption("Row numbers start at 1 in the working table. Edit a cell, or delete the row, and the check runs again.")
    elif not report.has_structural_error:
        st.success("Every row in the working table passed the checks.")

    if report.missing_mark_notes and not report.has_structural_error:
        with st.expander("Blank marks that will stay missing"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Row": item["row_number"],
                            "Student ID": item["student_id"],
                            "Not recorded": "; ".join(item["messages"]),
                        }
                        for item in report.missing_mark_notes
                    ]
                ),
                width="stretch",
                hide_index=True,
            )

    existing = []
    if not report.valid_frame.empty:
        existing = find_existing_ids(report.valid_frame["student_id"].tolist(), list_student_ids())
    if existing:
        st.warning(
            f"{len(existing)} student IDs are already stored: {', '.join(existing[:12])}"
            + ("..." if len(existing) > 12 else "")
            + ". They are skipped unless you choose to update them."
        )
    update_existing = st.checkbox("Update students that already exist", value=False)
    skip_invalid = st.checkbox(
        "Skip invalid rows and import the valid rows",
        value=False,
        disabled=report.invalid_count == 0,
    )

    if st.button("Import into database", type="primary"):
        if report.has_structural_error:
            st.error("Fix the column headers before importing. Nothing was saved.")
        elif report.invalid_count and not skip_invalid:
            st.error("Correct or remove the invalid rows, or choose to skip them. Nothing was saved.")
        elif report.valid_frame.empty:
            st.warning("There are no valid rows to import.")
        else:
            with loading("Importing valid rows…"):
                result = import_records(report.valid_frame, update_existing=update_existing)
            st.success(
                f"Inserted {len(result.inserted)}, updated {len(result.updated)}, "
                f"and skipped {len(result.skipped)} existing IDs."
            )
            if result.skipped:
                st.caption("Skipped IDs were left unchanged: " + ", ".join(result.skipped[:20]))

st.divider()
st.subheader("Reset the demonstration data")
st.caption("This deletes every student in the local database. It does not affect the CSV file on disk.")
confirm_reset = st.checkbox("I understand this deletes the stored students")
if st.button("Replace stored data with the fictional sample", disabled=not confirm_reset):
    with loading("Replacing stored records…"):
        clear_students()
        result = load_sample_into_database(replace=False)
    flash(f"The database now holds {len(result['inserted'])} fictional students.")
    st.rerun()
