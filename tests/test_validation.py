"""Validation and cleaning checks."""

import pandas as pd

from modules.data_loader import read_dataframe, template_csv_bytes
from modules.validation import validate_dataframe


def _row(**overrides):
    base = {
        "student_id": "S001",
        "student_name": "Aarav Sharma",
        "semester": "Semester 5",
        "department": "Computer Science",
        "attendance_percentage": 80,
        "study_hours": 2,
        "mathematics_marks": 70,
        "programming_marks": 75,
        "database_marks": 72,
        "internal_marks": 30,
        "final_marks": 74,
    }
    base.update(overrides)
    return base


def test_valid_row_is_accepted_and_blank_mark_stays_missing():
    report = validate_dataframe(pd.DataFrame([_row(mathematics_marks="")]))
    assert report.valid_count == 1
    assert report.invalid_count == 0
    assert pd.isna(report.valid_frame.loc[0, "mathematics_marks"])
    assert report.missing_mark_notes[0]["messages"] == ["Mathematics is not recorded."]


def test_aliases_and_title_case_labels():
    frame = pd.DataFrame(
        [
            {
                "Student ID": "s010",
                "Name": "Meera Nair",
                "Class": "semester 6",
                "Dept": "computer science",
                "Attendance %": "91%",
                "Study Hours": 3,
                "Maths": 80,
                "Programming": 81,
                "DB": 82,
                "Internal": 40,
                "Final": 83,
                "Hobby": "chess",
            }
        ]
    )
    report = validate_dataframe(frame)
    assert report.valid_count == 1
    assert report.ignored_columns == ["hobby"]
    row = report.valid_frame.iloc[0]
    assert row["student_id"] == "S010"
    assert row["semester"] == "Semester 6"
    assert row["department"] == "Computer Science"
    assert row["attendance_percentage"] == 91


def test_missing_column_is_reported():
    frame = pd.DataFrame([_row()]).drop(columns=["department"])
    report = validate_dataframe(frame)
    assert "department" in report.missing_columns
    assert report.valid_count == 0


def test_duplicate_headers_are_rejected():
    frame = pd.DataFrame([["S001", "S002"]], columns=["Student ID", "student_id"])
    report = validate_dataframe(frame)
    assert report.file_errors
    assert report.valid_count == 0


def test_duplicate_student_ids_are_rejected():
    frame = pd.DataFrame([_row(student_id="S001"), _row(student_id="s001", student_name="Ananya Iyer")])
    report = validate_dataframe(frame)
    assert report.valid_count == 0
    assert report.invalid_count == 2
    assert all(
        "Student ID appears more than once in this file." in item["messages"] for item in report.row_errors
    )


def test_marks_outside_range_are_rejected_and_zero_is_kept():
    high = validate_dataframe(pd.DataFrame([_row(programming_marks=101)]))
    assert high.invalid_count == 1
    assert any("cannot be above 100" in message for item in high.row_errors for message in item["messages"])

    low = validate_dataframe(pd.DataFrame([_row(database_marks=-1)]))
    assert low.invalid_count == 1

    internal = validate_dataframe(pd.DataFrame([_row(internal_marks=51)]))
    assert internal.invalid_count == 1

    zero = validate_dataframe(pd.DataFrame([_row(mathematics_marks=0)]))
    assert zero.valid_count == 1
    assert zero.valid_frame.loc[0, "mathematics_marks"] == 0


def test_attendance_and_study_hours_bounds():
    assert validate_dataframe(pd.DataFrame([_row(attendance_percentage=0, study_hours=16)])).valid_count == 1
    assert validate_dataframe(pd.DataFrame([_row(attendance_percentage=101)])).invalid_count == 1
    assert validate_dataframe(pd.DataFrame([_row(study_hours=-0.1)])).invalid_count == 1
    assert validate_dataframe(pd.DataFrame([_row(attendance_percentage="")])).invalid_count == 1
    bad_text = validate_dataframe(pd.DataFrame([_row(mathematics_marks="absent")]))
    assert bad_text.invalid_count == 1
    assert any("must be a number" in message for item in bad_text.row_errors for message in item["messages"])


def test_template_and_excel_round_trip(tmp_path):
    template = tmp_path / "template.csv"
    template.write_bytes(template_csv_bytes())
    loaded = read_dataframe(template.open("rb"), template.name)
    report = validate_dataframe(loaded)
    assert report.valid_count == 1
    assert report.valid_frame.loc[0, "student_id"] == "EXAMPLE"

    workbook = tmp_path / "students.xlsx"
    pd.DataFrame([_row()]).to_excel(workbook, index=False)
    excel_frame = read_dataframe(workbook.open("rb"), workbook.name)
    assert validate_dataframe(excel_frame).valid_count == 1


def test_non_numeric_attendance_is_not_silently_dropped():
    report = validate_dataframe(pd.DataFrame([_row(attendance_percentage="good")]))
    assert report.valid_count == 0
    assert any("Attendance percentage" in message for item in report.row_errors for message in item["messages"])
