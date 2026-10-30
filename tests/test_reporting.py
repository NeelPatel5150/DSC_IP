"""Individual reports stay limited to the selected student."""

import pandas as pd

from modules.analytics import enrich
from modules.reporting import build_student_report, report_to_csv_bytes, report_to_pdf_bytes


def _performance():
    frame = pd.DataFrame(
        [
            {
                "student_id": "S001",
                "student_name": "Aarav Sharma",
                "semester": "Semester 5",
                "department": "Computer Science",
                "attendance_percentage": 96,
                "study_hours": 5,
                "mathematics_marks": 90,
                "programming_marks": 92,
                "database_marks": 88,
                "internal_marks": 45,
                "final_marks": 91,
            },
            {
                "student_id": "S002",
                "student_name": "Meera Nair",
                "semester": "Semester 5",
                "department": "Computer Science",
                "attendance_percentage": 60,
                "study_hours": 1,
                "mathematics_marks": 42,
                "programming_marks": 45,
                "database_marks": 40,
                "internal_marks": 20,
                "final_marks": 41,
            },
        ]
    )
    return enrich(frame)


def test_report_uses_only_the_selected_student():
    performance = _performance()
    report = build_student_report("S002", performance)
    assert report is not None
    text = report_to_csv_bytes(report).decode("utf-8")
    assert "S002" in text
    assert "Meera Nair" in text
    assert "S001" not in text
    assert "Aarav Sharma" not in text
    assert "Below the class average" in text
    assert report["rules_note"]
    pdf = report_to_pdf_bytes(report)
    assert pdf.startswith(b"%PDF")
    assert b"Aarav" not in pdf


def test_missing_student_returns_none():
    assert build_student_report("S999", _performance()) is None
