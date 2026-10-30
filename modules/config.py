"""Shared constants for the student performance project.

Grade bands, pass rules, and column names live here so the pages, tests,
and database inserts cannot drift apart.
"""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "app.db"
SAMPLE_CSV_PATH = DATA_DIR / "sample_students.csv"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000

PASS_PERCENT = 40.0
ATTENDANCE_REVIEW_PERCENT = 75.0
OVERALL_REVIEW_PERCENT = 50.0
STUDY_HOURS_MAX = 16.0
MIN_PREDICTION_ROWS = 40

# Letter grades use this fixed demonstration scale.
# The sidebar pass mark changes pass/fail only. It does not move these bands.
GRADE_MINIMUMS = (
    (90.0, "O"),
    (80.0, "A+"),
    (70.0, "A"),
    (60.0, "B+"),
    (50.0, "B"),
    (40.0, "C"),
    (0.0, "F"),
)

MARK_SCHEMES = (
    {
        "column": "mathematics_marks",
        "subject_name": "Mathematics",
        "maximum": 100.0,
        "examination_type": "subject",
        "counts_for_percentage": True,
        "counts_for_pass": True,
    },
    {
        "column": "programming_marks",
        "subject_name": "Programming",
        "maximum": 100.0,
        "examination_type": "subject",
        "counts_for_percentage": True,
        "counts_for_pass": True,
    },
    {
        "column": "database_marks",
        "subject_name": "Database",
        "maximum": 100.0,
        "examination_type": "subject",
        "counts_for_percentage": True,
        "counts_for_pass": True,
    },
    {
        "column": "internal_marks",
        "subject_name": "Internal",
        "maximum": 50.0,
        "examination_type": "internal",
        "counts_for_percentage": False,
        "counts_for_pass": True,
    },
    {
        "column": "final_marks",
        "subject_name": "Final",
        "maximum": 100.0,
        "examination_type": "final",
        "counts_for_percentage": False,
        "counts_for_pass": False,
    },
)

IDENTITY_COLUMNS = ("student_id", "student_name", "semester", "department")
HABIT_COLUMNS = ("attendance_percentage", "study_hours")
MARK_COLUMNS = tuple(item["column"] for item in MARK_SCHEMES)
REQUIRED_COLUMNS = IDENTITY_COLUMNS + HABIT_COLUMNS + MARK_COLUMNS

PREDICTION_FEATURES = (
    "attendance_percentage",
    "study_hours",
    "internal_marks",
    "mathematics_marks",
    "programming_marks",
    "database_marks",
)
PREDICTION_TARGET = "final_marks"

COLUMN_ALIASES = {
    "student id": "student_id",
    "studentid": "student_id",
    "id": "student_id",
    "student name": "student_name",
    "name": "student_name",
    "class": "semester",
    "sem": "semester",
    "semester": "semester",
    "department": "department",
    "dept": "department",
    "attendance": "attendance_percentage",
    "attendance percentage": "attendance_percentage",
    "attendance %": "attendance_percentage",
    "study hours": "study_hours",
    "study hours per day": "study_hours",
    "math": "mathematics_marks",
    "maths": "mathematics_marks",
    "mathematics": "mathematics_marks",
    "mathematics marks": "mathematics_marks",
    "programming": "programming_marks",
    "programming marks": "programming_marks",
    "database": "database_marks",
    "database marks": "database_marks",
    "db": "database_marks",
    "internal": "internal_marks",
    "internal marks": "internal_marks",
    "internal assessment": "internal_marks",
    "final": "final_marks",
    "final marks": "final_marks",
    "final examination": "final_marks",
}

DISPLAY_NAMES = {
    "student_id": "Student ID",
    "student_name": "Student name",
    "semester": "Semester",
    "department": "Department",
    "attendance_percentage": "Attendance %",
    "study_hours": "Study hours / day",
    "mathematics_marks": "Mathematics",
    "programming_marks": "Programming",
    "database_marks": "Database",
    "internal_marks": "Internal",
    "final_marks": "Final",
    "subject_percentage": "Subject %",
    "grade": "Grade",
    "result_status": "Result",
    "class_rank": "Rank",
    "subjects_recorded": "Subjects recorded",
    "created_at": "Created at",
    "subject": "Component",
    "students_recorded": "Students recorded",
    "average": "Average marks",
    "highest": "Highest",
    "lowest": "Lowest",
    "maximum_marks": "Maximum",
    "average_percent": "Average % of maximum",
    "reasons": "Reasons",
}

RESULT_COLORS = {
    "Pass": "#1E8449",
    "Fail": "#C0392B",
    "Incomplete": "#B9770E",
}

GRADE_COLORS = {
    "O": "#1A5276",
    "A+": "#1F618D",
    "A": "#148F77",
    "B+": "#117A65",
    "B": "#B7950B",
    "C": "#CA6F1E",
    "F": "#922B21",
}
