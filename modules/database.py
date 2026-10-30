"""SQLite storage for students, attendance, and subject marks.

The database file is created on first use at ``database/app.db``.
Delete that file and restart the app to reset local data during development.
Every query uses ``?`` placeholders.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from modules.config import DATABASE_PATH, MARK_SCHEMES, REQUIRED_COLUMNS
from modules.data_cleaning import is_blank

_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    student_name TEXT NOT NULL,
    semester TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS academic_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL UNIQUE,
    attendance_percentage REAL NOT NULL CHECK (
        attendance_percentage >= 0 AND attendance_percentage <= 100
    ),
    study_hours REAL NOT NULL CHECK (study_hours >= 0 AND study_hours <= 16),
    academic_term TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subject_marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    marks_obtained REAL CHECK (
        marks_obtained IS NULL
        OR (marks_obtained >= 0 AND marks_obtained <= maximum_marks)
    ),
    maximum_marks REAL NOT NULL,
    examination_type TEXT NOT NULL CHECK (
        examination_type IN ('subject', 'internal', 'final')
    ),
    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
    UNIQUE (student_id, subject_name, examination_type)
);
"""


@dataclass
class ImportResult:
    inserted: list[str]
    updated: list[str]
    skipped: list[str]


def connect(db_path: Path | str = DATABASE_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | str = DATABASE_PATH) -> None:
    """Create tables when they do not already exist."""
    with connect(db_path) as connection:
        connection.executescript(_SCHEMA)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _optional_float(value: object) -> float | None:
    if is_blank(value):
        return None
    return float(value)


def list_student_ids(db_path: Path | str = DATABASE_PATH) -> list[str]:
    init_db(db_path)
    with connect(db_path) as connection:
        rows = connection.execute("SELECT student_id FROM students ORDER BY student_id").fetchall()
    return [row["student_id"] for row in rows]


def _write_student(connection: sqlite3.Connection, record: dict, now: str) -> str:
    """Insert or update one student. Returns ``inserted`` or ``updated``."""
    student_id = str(record["student_id"]).strip().upper()
    existing = connection.execute(
        "SELECT created_at FROM students WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    action = "updated" if existing else "inserted"
    created_at = existing["created_at"] if existing else now
    connection.execute(
        """
        INSERT INTO students (student_id, student_name, semester, department, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            student_name = excluded.student_name,
            semester = excluded.semester,
            department = excluded.department
        """,
        (
            student_id,
            str(record["student_name"]),
            str(record["semester"]),
            str(record["department"]),
            created_at,
        ),
    )
    connection.execute(
        """
        INSERT INTO academic_records (
            student_id, attendance_percentage, study_hours, academic_term
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            attendance_percentage = excluded.attendance_percentage,
            study_hours = excluded.study_hours,
            academic_term = excluded.academic_term
        """,
        (
            student_id,
            float(record["attendance_percentage"]),
            float(record["study_hours"]),
            str(record["semester"]),
        ),
    )
    for scheme in MARK_SCHEMES:
        connection.execute(
            """
            INSERT INTO subject_marks (
                student_id, subject_name, marks_obtained, maximum_marks, examination_type
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id, subject_name, examination_type) DO UPDATE SET
                marks_obtained = excluded.marks_obtained,
                maximum_marks = excluded.maximum_marks
            """,
            (
                student_id,
                scheme["subject_name"],
                _optional_float(record.get(scheme["column"])),
                float(scheme["maximum"]),
                scheme["examination_type"],
            ),
        )
    return action


def import_records(
    frame: pd.DataFrame,
    db_path: Path | str = DATABASE_PATH,
    update_existing: bool = False,
) -> ImportResult:
    """Store valid rows. Existing IDs are skipped unless an update is requested."""
    init_db(db_path)
    inserted: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    if frame is None or frame.empty:
        return ImportResult(inserted, updated, skipped)

    now = _utc_now()
    with connect(db_path) as connection:
        existing_ids = {
            row["student_id"]
            for row in connection.execute("SELECT student_id FROM students").fetchall()
        }
        for record in frame.to_dict(orient="records"):
            student_id = str(record["student_id"]).strip().upper()
            record["student_id"] = student_id
            if student_id in existing_ids and not update_existing:
                skipped.append(student_id)
                continue
            action = _write_student(connection, record, now)
            existing_ids.add(student_id)
            if action == "inserted":
                inserted.append(student_id)
            else:
                updated.append(student_id)
    return ImportResult(inserted, updated, skipped)


def delete_student(student_id: str, db_path: Path | str = DATABASE_PATH) -> bool:
    """Delete one student. Marks and the academic row are removed by the foreign key."""
    init_db(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM students WHERE student_id = ?",
            (str(student_id).strip().upper(),),
        )
        return cursor.rowcount > 0


def clear_students(db_path: Path | str = DATABASE_PATH) -> int:
    """Delete every student. Used only after an explicit confirmation."""
    init_db(db_path)
    with connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
        connection.execute("DELETE FROM students")
    return int(count)


def _marks_by_student(marks: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    lookup = {scheme["subject_name"]: scheme["column"] for scheme in MARK_SCHEMES}
    grouped: dict[str, dict[str, float | None]] = {}
    if marks is None or marks.empty:
        return grouped
    for row in marks.to_dict(orient="records"):
        column = lookup.get(row["subject_name"])
        if column is None:
            continue
        student = grouped.setdefault(str(row["student_id"]), {})
        value = row["marks_obtained"]
        student[column] = None if is_blank(value) else float(value)
    return grouped


def fetch_wide(db_path: Path | str = DATABASE_PATH) -> pd.DataFrame:
    """Return one row per student, with a column for each mark component."""
    init_db(db_path)
    with connect(db_path) as connection:
        students = pd.read_sql_query(
            """
            SELECT student_id, student_name, semester, department, created_at
            FROM students
            ORDER BY student_id
            """,
            connection,
        )
        records = pd.read_sql_query(
            """
            SELECT student_id, attendance_percentage, study_hours, academic_term
            FROM academic_records
            """,
            connection,
        )
        marks = pd.read_sql_query(
            """
            SELECT student_id, subject_name, marks_obtained, maximum_marks, examination_type
            FROM subject_marks
            """,
            connection,
        )

    columns = ["created_at", *REQUIRED_COLUMNS]
    if students.empty:
        return pd.DataFrame(columns=columns)

    merged = students.merge(records, on="student_id", how="left")
    mark_lookup = _marks_by_student(marks)
    rows = []
    for record in merged.to_dict(orient="records"):
        student_marks = mark_lookup.get(str(record["student_id"]), {})
        row = {
            "student_id": record["student_id"],
            "student_name": record["student_name"],
            "semester": record["semester"],
            "department": record["department"],
            "attendance_percentage": record.get("attendance_percentage"),
            "study_hours": record.get("study_hours"),
            "created_at": record.get("created_at"),
        }
        for scheme in MARK_SCHEMES:
            row[scheme["column"]] = student_marks.get(scheme["column"])
        rows.append(row)
    frame = pd.DataFrame(rows)
    return frame.loc[:, ["created_at", *REQUIRED_COLUMNS]]
