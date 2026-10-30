"""Checks for uploaded rows and student forms.

A row is rejected when an ID, name, attendance value, study-hours value,
or mark is malformed or out of range. A blank subject mark is allowed and
is reported separately. It is not turned into zero and it does not, by
itself, reject the row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from modules.config import (
    HABIT_COLUMNS,
    MARK_SCHEMES,
    MAX_ROWS,
    REQUIRED_COLUMNS,
    STUDY_HOURS_MAX,
)
from modules.data_cleaning import (
    is_blank,
    normalize_label,
    normalize_person_name,
    parse_number,
    prepare_columns,
)

_STUDENT_ID = re.compile(r"^[A-Z0-9_-]{2,20}$")
_PERSON_NAME = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,79}$")


@dataclass
class ValidationReport:
    """Everything the upload page needs to explain a file."""

    valid_frame: pd.DataFrame
    invalid_frame: pd.DataFrame
    row_errors: list[dict] = field(default_factory=list)
    missing_mark_notes: list[dict] = field(default_factory=list)
    ignored_columns: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    file_errors: list[str] = field(default_factory=list)

    @property
    def has_structural_error(self) -> bool:
        return bool(self.file_errors or self.missing_columns)

    @property
    def valid_count(self) -> int:
        return 0 if self.has_structural_error else int(len(self.valid_frame))

    @property
    def invalid_count(self) -> int:
        return 0 if self.has_structural_error else int(len(self.invalid_frame))


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(REQUIRED_COLUMNS))


def _check_identity(raw: dict) -> tuple[dict, list[str]]:
    messages: list[str] = []
    cleaned: dict = {}

    student_id = "" if is_blank(raw.get("student_id")) else str(raw.get("student_id")).strip().upper()
    if not student_id:
        messages.append("Student ID is required.")
    elif not _STUDENT_ID.fullmatch(student_id):
        messages.append(
            "Student ID must be 2 to 20 characters and use only letters, numbers, '_' or '-'."
        )
    cleaned["student_id"] = student_id

    name = "" if is_blank(raw.get("student_name")) else normalize_person_name(raw.get("student_name"))
    if not name:
        messages.append("Student name is required.")
    elif not _PERSON_NAME.fullmatch(name):
        messages.append(
            "Student name must be 2 to 80 characters and use letters, spaces, apostrophes, periods, or hyphens."
        )
    cleaned["student_name"] = name

    for column, label in (("semester", "Semester"), ("department", "Department")):
        if is_blank(raw.get(column)):
            messages.append(f"{label} is required.")
            cleaned[column] = ""
            continue
        label_value = normalize_label(raw.get(column))
        if not 2 <= len(label_value) <= 40 or any(char in label_value for char in "<>"):
            messages.append(f"{label} must be 2 to 40 characters.")
            cleaned[column] = label_value
        else:
            cleaned[column] = label_value
    return cleaned, messages


def _check_habits(raw: dict) -> tuple[dict, list[str]]:
    messages: list[str] = []
    cleaned: dict = {}
    rules = {
        "attendance_percentage": ("Attendance percentage", 0.0, 100.0),
        "study_hours": ("Study hours", 0.0, STUDY_HOURS_MAX),
    }
    for column in HABIT_COLUMNS:
        label, low, high = rules[column]
        number, status = parse_number(raw.get(column))
        if status == "blank":
            messages.append(f"{label} is required.")
            cleaned[column] = None
        elif status == "bad":
            messages.append(f"{label} must be a number from {low:g} to {high:g}.")
            cleaned[column] = None
        elif number is None or number < low or number > high:
            messages.append(f"{label} must be from {low:g} to {high:g}.")
            cleaned[column] = number
        else:
            cleaned[column] = float(number)
    return cleaned, messages


def _check_marks(raw: dict) -> tuple[dict, list[str], list[str]]:
    messages: list[str] = []
    notes: list[str] = []
    cleaned: dict = {}
    for scheme in MARK_SCHEMES:
        column = scheme["column"]
        label = scheme["subject_name"]
        maximum = float(scheme["maximum"])
        number, status = parse_number(raw.get(column))
        if status == "blank":
            cleaned[column] = None
            notes.append(f"{label} is not recorded.")
        elif status == "bad":
            cleaned[column] = None
            messages.append(f"{label} marks must be a number from 0 to {maximum:g}, or left blank.")
        elif number is None or number < 0:
            cleaned[column] = number
            messages.append(f"{label} marks cannot be below 0.")
        elif number > maximum:
            cleaned[column] = number
            messages.append(f"{label} marks cannot be above {maximum:g}.")
        else:
            cleaned[column] = float(number)
    return cleaned, messages, notes


def validate_dataframe(df: pd.DataFrame) -> ValidationReport:
    """Validate a whole uploaded table. The caller's dataframe is not modified."""
    prepared = prepare_columns(df)
    if prepared.file_errors or prepared.missing_columns:
        return ValidationReport(
            valid_frame=_empty_frame(),
            invalid_frame=_empty_frame(),
            ignored_columns=prepared.ignored_columns,
            missing_columns=prepared.missing_columns,
            file_errors=list(prepared.file_errors),
        )

    if len(prepared.frame) > MAX_ROWS:
        return ValidationReport(
            valid_frame=_empty_frame(),
            invalid_frame=_empty_frame(),
            ignored_columns=prepared.ignored_columns,
            file_errors=[f"This demonstration accepts up to {MAX_ROWS} data rows."],
        )

    if prepared.frame.empty:
        return ValidationReport(
            valid_frame=_empty_frame(),
            invalid_frame=_empty_frame(),
            ignored_columns=prepared.ignored_columns,
            file_errors=["The file has column headers but no data rows."],
        )

    cleaned_rows: list[dict] = []
    row_errors: list[dict] = []
    missing_notes: list[dict] = []
    id_rows: dict[str, list[int]] = {}

    for position, raw in enumerate(prepared.frame.to_dict(orient="records"), start=1):
        identity, identity_messages = _check_identity(raw)
        habits, habit_messages = _check_habits(raw)
        marks, mark_messages, notes = _check_marks(raw)
        record = {**identity, **habits, **marks}
        record["_row_number"] = position
        cleaned_rows.append(record)
        messages = identity_messages + habit_messages + mark_messages
        student_id = identity["student_id"]
        if student_id:
            id_rows.setdefault(student_id, []).append(position)
        if messages:
            row_errors.append(
                {"row_number": position, "student_id": student_id, "messages": messages}
            )
        if notes:
            missing_notes.append(
                {"row_number": position, "student_id": student_id, "messages": notes}
            )

    duplicate_rows: set[int] = set()
    for student_id, positions in id_rows.items():
        if len(positions) > 1:
            duplicate_rows.update(positions)
            for position in positions:
                row_errors.append(
                    {
                        "row_number": position,
                        "student_id": student_id,
                        "messages": ["Student ID appears more than once in this file."],
                    }
                )

    # Merge messages for the same row into one display line.
    merged: dict[int, dict] = {}
    for item in row_errors:
        bucket = merged.setdefault(
            item["row_number"],
            {"row_number": item["row_number"], "student_id": item["student_id"], "messages": []},
        )
        for message in item["messages"]:
            if message not in bucket["messages"]:
                bucket["messages"].append(message)
    row_errors = [merged[key] for key in sorted(merged)]
    bad_rows = set(merged) | duplicate_rows

    valid_records = []
    invalid_records = []
    for record in cleaned_rows:
        public = {column: record[column] for column in REQUIRED_COLUMNS}
        if record["_row_number"] in bad_rows:
            invalid_records.append(public)
        else:
            valid_records.append(public)

    valid_frame = pd.DataFrame(valid_records, columns=list(REQUIRED_COLUMNS))
    invalid_frame = pd.DataFrame(invalid_records, columns=list(REQUIRED_COLUMNS))
    return ValidationReport(
        valid_frame=valid_frame,
        invalid_frame=invalid_frame,
        row_errors=row_errors,
        missing_mark_notes=missing_notes,
        ignored_columns=prepared.ignored_columns,
    )


def validate_student_dict(record: dict) -> ValidationReport:
    """Validate one student typed into a form."""
    return validate_dataframe(pd.DataFrame([record]))
