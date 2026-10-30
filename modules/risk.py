"""Rule-based academic review flags.

A flag means a published rule matched the stored record. The wording is
"Needs academic review" because the rule is a decision-support indicator,
not a judgment of the student's ability.
"""

from __future__ import annotations

import pandas as pd

from modules.config import (
    ATTENDANCE_REVIEW_PERCENT,
    OVERALL_REVIEW_PERCENT,
    PASS_PERCENT,
)
from modules.data_cleaning import is_blank
from modules.grading import component_outcomes


def review_reasons(
    record: dict,
    pass_percent: float = PASS_PERCENT,
    attendance_threshold: float = ATTENDANCE_REVIEW_PERCENT,
    overall_threshold: float = OVERALL_REVIEW_PERCENT,
) -> list[dict]:
    """Return reason codes and sentences for one enriched student row."""
    reasons: list[dict] = []
    attendance = record.get("attendance_percentage")
    if is_blank(attendance):
        reasons.append(
            {
                "code": "low_attendance",
                "message": "Attendance is not recorded.",
            }
        )
    elif float(attendance) < float(attendance_threshold):
        reasons.append(
            {
                "code": "low_attendance",
                "message": (
                    f"Attendance is {float(attendance):.1f}%, below the review threshold "
                    f"of {float(attendance_threshold):.0f}%."
                ),
            }
        )

    for item in component_outcomes(record, pass_percent=pass_percent):
        if item["state"] == "missing":
            reasons.append(
                {
                    "code": "missing_result",
                    "message": f"{item['name']} result is not recorded.",
                }
            )
        elif item["state"] == "fail" and item["counts_for_pass"]:
            reasons.append(
                {
                    "code": "below_pass",
                    "message": (
                        f"{item['name']} is below the pass mark "
                        f"({float(pass_percent):.0f}% of {item['maximum']:g})."
                    ),
                }
            )
        elif item["state"] == "fail" and item["examination_type"] == "final":
            reasons.append(
                {
                    "code": "below_pass",
                    "message": (
                        f"Final marks are below the pass mark of {float(pass_percent):.0f} "
                        f"out of {item['maximum']:g}. Final marks do not change the pass/fail "
                        "status, but they can still be reviewed."
                    ),
                }
            )

    percentage = record.get("subject_percentage")
    if not is_blank(percentage) and float(percentage) < float(overall_threshold):
        reasons.append(
            {
                "code": "low_overall",
                "message": (
                    f"Subject percentage is {float(percentage):.1f}%, below the review "
                    f"threshold of {float(overall_threshold):.0f}%."
                ),
            }
        )
    return reasons


def build_flag_table(
    df: pd.DataFrame,
    pass_percent: float = PASS_PERCENT,
    attendance_threshold: float = ATTENDANCE_REVIEW_PERCENT,
    overall_threshold: float = OVERALL_REVIEW_PERCENT,
) -> pd.DataFrame:
    """One row per student who has at least one review reason."""
    columns = [
        "student_id",
        "student_name",
        "semester",
        "department",
        "attendance_percentage",
        "subject_percentage",
        "result_status",
        "reasons",
        "reason_codes",
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for record in df.to_dict(orient="records"):
        reasons = review_reasons(
            record,
            pass_percent=pass_percent,
            attendance_threshold=attendance_threshold,
            overall_threshold=overall_threshold,
        )
        if not reasons:
            continue
        rows.append(
            {
                "student_id": record.get("student_id"),
                "student_name": record.get("student_name"),
                "semester": record.get("semester"),
                "department": record.get("department"),
                "attendance_percentage": record.get("attendance_percentage"),
                "subject_percentage": record.get("subject_percentage"),
                "result_status": record.get("result_status"),
                "reasons": " | ".join(item["message"] for item in reasons),
                "reason_codes": sorted({item["code"] for item in reasons}),
            }
        )
    if not rows:
        return pd.DataFrame(columns=columns)
    table = pd.DataFrame(rows)
    return table.sort_values(["student_id"]).reset_index(drop=True)


REASON_LABELS = {
    "low_attendance": "Attendance below threshold",
    "below_pass": "A recorded mark is below the pass mark",
    "low_overall": "Subject percentage below threshold",
    "missing_result": "An examination result is missing",
}


def reason_counts(flag_table: pd.DataFrame) -> pd.DataFrame:
    """Count students once for each reason code they carry."""
    labels = []
    if flag_table is None or flag_table.empty:
        return pd.DataFrame(columns=["code", "reason", "students"])
    for code, label in REASON_LABELS.items():
        count = int(flag_table["reason_codes"].map(lambda codes, needle=code: needle in codes).sum())
        if count:
            labels.append({"code": code, "reason": label, "students": count})
    if not labels:
        return pd.DataFrame(columns=["code", "reason", "students"])
    return pd.DataFrame(labels)
