"""SQLite create, update, reload, and delete."""

import sqlite3

import pandas as pd

from modules.database import (
    clear_students,
    delete_student,
    fetch_wide,
    import_records,
    init_db,
    list_student_ids,
)
from modules.service import load_sample_into_database
from data.generate_sample import write_sample


def _frame():
    return pd.DataFrame(
        [
            {
                "student_id": "s020",
                "student_name": "Tara Kapoor",
                "semester": "Semester 5",
                "department": "Computer Science",
                "attendance_percentage": 86,
                "study_hours": 2.5,
                "mathematics_marks": 77,
                "programming_marks": None,
                "database_marks": 69,
                "internal_marks": 31,
                "final_marks": 73,
            }
        ]
    )


def test_insert_survives_a_new_connection_and_keeps_blank_marks(tmp_path):
    db_path = tmp_path / "students.db"
    init_db(db_path)
    result = import_records(_frame(), db_path=db_path, update_existing=False)
    assert result.inserted == ["S020"]

    again = import_records(_frame(), db_path=db_path, update_existing=False)
    assert again.skipped == ["S020"]
    assert again.inserted == []

    loaded = fetch_wide(db_path)
    assert loaded.loc[0, "student_id"] == "S020"
    assert loaded.loc[0, "mathematics_marks"] == 77
    assert pd.isna(loaded.loc[0, "programming_marks"])
    assert list_student_ids(db_path) == ["S020"]


def test_update_and_delete_cascade(tmp_path):
    db_path = tmp_path / "students.db"
    import_records(_frame(), db_path=db_path)
    changed = _frame()
    changed.loc[0, "student_name"] = "Tara Bose"
    changed.loc[0, "programming_marks"] = 88
    updated = import_records(changed, db_path=db_path, update_existing=True)
    assert updated.updated == ["S020"]
    loaded = fetch_wide(db_path)
    assert loaded.loc[0, "student_name"] == "Tara Bose"
    assert loaded.loc[0, "programming_marks"] == 88

    assert delete_student("S020", db_path=db_path) is True
    assert fetch_wide(db_path).empty
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    marks = connection.execute("SELECT COUNT(*) FROM subject_marks").fetchone()[0]
    records = connection.execute("SELECT COUNT(*) FROM academic_records").fetchone()[0]
    connection.close()
    assert marks == 0
    assert records == 0


def test_database_rejects_an_attendance_value_validation_would_block(tmp_path):
    db_path = tmp_path / "students.db"
    bad = _frame()
    bad.loc[0, "attendance_percentage"] = 150
    try:
        import_records(bad, db_path=db_path)
    except sqlite3.IntegrityError:
        return
    raise AssertionError("The database accepted attendance above 100.")


def test_clear_and_sample_reload(tmp_path):
    db_path = tmp_path / "students.db"
    sample_path = write_sample(tmp_path / "sample_students.csv", count=80)
    first = load_sample_into_database(db_path=db_path, sample_path=sample_path, replace=False)
    assert len(first["inserted"]) == 80
    assert clear_students(db_path) == 80
    assert fetch_wide(db_path).empty
    second = load_sample_into_database(db_path=db_path, sample_path=sample_path, replace=False)
    assert len(second["inserted"]) == 80
