"""Averages, filters, correlations, and dashboard totals."""

import pandas as pd

from modules.analytics import (
    apply_filters,
    build_summary,
    describe_correlation,
    enrich,
    pearson,
    subject_summary,
)


def _students():
    return pd.DataFrame(
        [
            {
                "student_id": "S001",
                "student_name": "Aarav Sharma",
                "semester": "Semester 5",
                "department": "Computer Science",
                "attendance_percentage": 90,
                "study_hours": 4,
                "mathematics_marks": 80,
                "programming_marks": 90,
                "database_marks": 70,
                "internal_marks": 40,
                "final_marks": 85,
            },
            {
                "student_id": "S002",
                "student_name": "Meera Nair",
                "semester": "Semester 5",
                "department": "Computer Science",
                "attendance_percentage": 70,
                "study_hours": 1,
                "mathematics_marks": 30,
                "programming_marks": 35,
                "database_marks": 25,
                "internal_marks": 10,
                "final_marks": 28,
            },
            {
                "student_id": "S003",
                "student_name": "Rahul Das",
                "semester": "Semester 6",
                "department": "Data Science",
                "attendance_percentage": 88,
                "study_hours": 3,
                "mathematics_marks": None,
                "programming_marks": None,
                "database_marks": None,
                "internal_marks": None,
                "final_marks": None,
            },
        ]
    )


def test_summary_excludes_incomplete_from_pass_percentage():
    enriched = enrich(_students())
    summary = build_summary(enriched, flagged_students=1)
    assert summary["total_students"] == 3
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["incomplete"] == 1
    assert summary["pass_percentage"] == 50
    assert summary["overall_average"] == (80 + 30) / 2
    assert summary["highest"] == 80
    assert summary["flagged"] == 1
    assert round(summary["average_attendance"], 2) == round((90 + 70 + 88) / 3, 2)


def test_empty_summary_does_not_invent_rates():
    summary = build_summary(pd.DataFrame(), flagged_students=0)
    assert summary["has_data"] is False
    assert summary["total_students"] == 0
    assert summary["pass_percentage"] is None
    assert summary["overall_average"] is None


def test_rank_uses_only_comparable_students():
    enriched = enrich(_students())
    first = enriched.loc[enriched["student_id"] == "S001"].iloc[0]
    second = enriched.loc[enriched["student_id"] == "S002"].iloc[0]
    third = enriched.loc[enriched["student_id"] == "S003"].iloc[0]
    assert first["subject_percentage"] == 80
    assert second["subject_percentage"] == 30
    assert first["class_rank"] == 1
    assert second["class_rank"] == 2
    assert pd.isna(third["class_rank"])
    assert third["result_status"] == "Incomplete"


def test_subject_summary_ignores_blank_marks():
    summary = subject_summary(_students())
    mathematics = summary.loc[summary["subject"] == "Mathematics"].iloc[0]
    assert mathematics["students_recorded"] == 2
    assert mathematics["highest"] == 80
    assert mathematics["lowest"] == 30
    assert mathematics["average"] == 55


def test_filters_search_by_id_and_name():
    enriched = enrich(_students())
    by_name = apply_filters(enriched, search="meera")
    assert by_name["student_id"].tolist() == ["S002"]
    by_id = apply_filters(enriched, search="S00")
    assert set(by_id["student_id"]) == {"S001", "S002", "S003"}
    by_semester = apply_filters(enriched, semester="Semester 6", department="Data Science")
    assert by_semester["student_id"].tolist() == ["S003"]
    assert apply_filters(enriched, search="nobody").empty


def test_pearson_requires_enough_pairs_and_does_not_claim_cause():
    frame = pd.DataFrame({"attendance_percentage": [1, 2, 3, 4, 5], "subject_percentage": [2, 4, 6, 8, 10]})
    coefficient, count = pearson(frame, "attendance_percentage", "subject_percentage")
    assert count == 5
    assert round(coefficient, 5) == 1
    text = describe_correlation(coefficient, count, "attendance", "subject percentage")
    assert "does not show that one variable causes the other" in text
    small = pd.DataFrame({"attendance_percentage": [1, 2], "subject_percentage": [3, 4]})
    assert pearson(small, "attendance_percentage", "subject_percentage")[0] is None
