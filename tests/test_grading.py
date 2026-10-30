"""Grade boundaries and pass/fail rules."""

from modules.grading import grade_from_percentage, result_status, subject_metrics, summarize_student
from modules.grading import component_outcomes


def _outcomes(pass_percent=40, **marks):
    record = {
        "mathematics_marks": marks.get("math"),
        "programming_marks": marks.get("programming"),
        "database_marks": marks.get("database"),
        "internal_marks": marks.get("internal"),
        "final_marks": marks.get("final"),
    }
    return component_outcomes(record, pass_percent=pass_percent)


def test_grade_boundaries():
    assert grade_from_percentage(100) == "O"
    assert grade_from_percentage(90) == "O"
    assert grade_from_percentage(89.99) == "A+"
    assert grade_from_percentage(80) == "A+"
    assert grade_from_percentage(79.99) == "A"
    assert grade_from_percentage(70) == "A"
    assert grade_from_percentage(60) == "B+"
    assert grade_from_percentage(50) == "B"
    assert grade_from_percentage(40) == "C"
    assert grade_from_percentage(39.99) == "F"
    assert grade_from_percentage(0) == "F"
    assert grade_from_percentage(None) is None
    assert grade_from_percentage(float("nan")) is None


def test_missing_marks_are_not_scored_as_zero():
    metrics = subject_metrics(_outcomes(math=80, programming=None, database=60))
    assert metrics["subjects_attempted"] == 2
    assert metrics["subject_total"] == 140
    assert metrics["subject_maximum"] == 200
    assert metrics["subject_percentage"] == 70
    assert metrics["overall_average"] == 70


def test_no_subject_marks_have_no_percentage():
    metrics = subject_metrics(_outcomes())
    assert metrics["subject_percentage"] is None
    assert metrics["subject_total"] is None


def test_pass_fail_and_incomplete():
    assert result_status(_outcomes(math=40, programming=40, database=40, internal=20)) == "Pass"
    assert result_status(_outcomes(math=39.99, programming=90, database=90, internal=40)) == "Fail"
    assert result_status(_outcomes(math=80, programming=80, database=80, internal=19.99)) == "Fail"
    assert result_status(_outcomes(final=10)) == "Incomplete"
    assert result_status(_outcomes(math=80, programming=None, database=None, internal=None)) == "Pass"


def test_custom_pass_percent_changes_status_not_grade_scale():
    summary = summarize_student(
        {
            "mathematics_marks": 45,
            "programming_marks": 45,
            "database_marks": 45,
            "internal_marks": 25,
            "final_marks": 10,
        },
        pass_percent=50,
    )
    assert summary["grade"] == "C"
    assert summary["result_status"] == "Fail"
    assert summary["subject_percentage"] == 45
