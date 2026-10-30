"""Academic review reasons."""

import pandas as pd

from modules.analytics import enrich
from modules.risk import build_flag_table, review_reasons


def _record(**overrides):
    base = {
        "student_id": "S010",
        "student_name": "Ananya Iyer",
        "semester": "Semester 7",
        "department": "Data Science",
        "attendance_percentage": 90,
        "study_hours": 3,
        "mathematics_marks": 80,
        "programming_marks": 82,
        "database_marks": 78,
        "internal_marks": 40,
        "final_marks": 81,
    }
    base.update(overrides)
    return enrich(pd.DataFrame([base])).iloc[0].to_dict()


def _codes(record, **settings):
    return {item["code"] for item in review_reasons(record, **settings)}


def test_clean_record_has_no_flags():
    assert review_reasons(_record()) == []


def test_attendance_threshold_is_exclusive_at_the_boundary():
    assert "low_attendance" in _codes(_record(attendance_percentage=74.9))
    assert "low_attendance" not in _codes(_record(attendance_percentage=75))
    low = review_reasons(_record(attendance_percentage=74.9))
    assert any("below the review threshold" in item["message"] for item in low)


def test_below_pass_missing_mark_and_low_overall_are_separate_reasons():
    record = _record(
        mathematics_marks=30,
        programming_marks=None,
        database_marks=40,
        internal_marks=40,
    )
    codes = _codes(record)
    assert "below_pass" in codes
    assert "missing_result" in codes
    assert "low_overall" in codes
    messages = " ".join(item["message"] for item in review_reasons(record))
    assert "Mathematics" in messages
    assert "Programming result is not recorded." in messages


def test_final_mark_can_raise_a_review_without_changing_pass_status():
    record = _record(final_marks=20)
    assert record["result_status"] == "Pass"
    messages = [item["message"] for item in review_reasons(record)]
    assert any("Final marks" in message for message in messages)


def test_flag_table_lists_only_matched_students():
    records = pd.DataFrame(
        [
            _record(),
            _record(student_id="S011", student_name="Dev Menon", attendance_percentage=50),
        ]
    )
    # _record() already returns an enriched dict, so build the table from those rows directly.
    table = build_flag_table(records)
    assert table["student_id"].tolist() == ["S011"]
    assert "Attendance" in table.iloc[0]["reasons"]
