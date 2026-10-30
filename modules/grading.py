"""Grade, percentage, and pass/fail rules.

Demonstration rules, used because no official college regulation is bundled
with this project:

- Subject percentage uses Mathematics, Programming, and Database only.
  Each of those papers is out of 100. The percentage is the sum of the
  recorded papers divided by 100 times how many of them are recorded.
- A blank paper is skipped. It is not scored as zero, so students who sat
  different papers are not forced onto the same total.
- Internal assessment is out of 50. It counts toward pass/fail and toward
  review flags. It is not folded into the subject percentage.
- Final marks are stored for reporting and for the optional prediction.
  They do not change the pass/fail status.
- Letter grades use a fixed scale starting at 90, 80, 70, 60, 50, and 40.
- Pass/fail uses the configured pass percentage (40 by default). A student
  passes when every recorded subject and the internal mark, if recorded,
  reach that percentage of the component maximum. No recorded subject or
  internal mark means Incomplete, which is neither Pass nor Fail.
"""

from __future__ import annotations

import math

import pandas as pd

from modules.config import GRADE_MINIMUMS, MARK_SCHEMES, PASS_PERCENT
from modules.data_cleaning import is_blank


def grade_from_percentage(percentage: float | None) -> str | None:
    """Return the demonstration letter grade, or None when no percentage exists."""
    if percentage is None or (isinstance(percentage, float) and math.isnan(percentage)):
        return None
    try:
        if pd.isna(percentage):
            return None
    except TypeError:
        pass
    value = float(percentage)
    for minimum, grade in GRADE_MINIMUMS:
        if value >= minimum:
            return grade
    return "F"


def pass_threshold(maximum: float, pass_percent: float = PASS_PERCENT) -> float:
    """Minimum marks that count as a pass for one component."""
    return float(maximum) * float(pass_percent) / 100.0


def component_outcomes(record: dict, pass_percent: float = PASS_PERCENT) -> list[dict]:
    """Describe every mark component as missing, pass, or fail."""
    outcomes = []
    for scheme in MARK_SCHEMES:
        raw_value = record.get(scheme["column"])
        maximum = float(scheme["maximum"])
        if is_blank(raw_value):
            state = "missing"
            marks = None
        else:
            marks = float(raw_value)
            state = "pass" if marks >= pass_threshold(maximum, pass_percent) else "fail"
        outcomes.append(
            {
                "column": scheme["column"],
                "name": scheme["subject_name"],
                "maximum": maximum,
                "examination_type": scheme["examination_type"],
                "counts_for_percentage": scheme["counts_for_percentage"],
                "counts_for_pass": scheme["counts_for_pass"],
                "marks": marks,
                "state": state,
            }
        )
    return outcomes


def subject_metrics(outcomes: list[dict]) -> dict:
    """Average and percentage across the recorded percentage subjects only."""
    recorded = [
        item["marks"]
        for item in outcomes
        if item["counts_for_percentage"] and item["marks"] is not None
    ]
    names = [
        item["name"]
        for item in outcomes
        if item["counts_for_percentage"] and item["marks"] is not None
    ]
    attempted = len(recorded)
    if attempted == 0:
        return {
            "subjects_attempted": 0,
            "subject_total": None,
            "subject_maximum": None,
            "subject_percentage": None,
            "overall_average": None,
            "subjects_recorded": "",
        }
    total = float(sum(recorded))
    maximum = 100.0 * attempted
    percentage = total / maximum * 100.0
    return {
        "subjects_attempted": attempted,
        "subject_total": total,
        "subject_maximum": maximum,
        "subject_percentage": percentage,
        "overall_average": total / attempted,
        "subjects_recorded": ", ".join(names),
    }


def result_status(outcomes: list[dict]) -> str:
    """Pass, Fail, or Incomplete from subject and internal components."""
    recorded = [item for item in outcomes if item["counts_for_pass"] and item["state"] != "missing"]
    if not recorded:
        return "Incomplete"
    if any(item["state"] == "fail" for item in recorded):
        return "Fail"
    return "Pass"


def summarize_student(record: dict, pass_percent: float = PASS_PERCENT) -> dict:
    """Combine percentage, grade, and pass/fail for one student dictionary."""
    outcomes = component_outcomes(record, pass_percent=pass_percent)
    metrics = subject_metrics(outcomes)
    metrics["grade"] = grade_from_percentage(metrics["subject_percentage"])
    metrics["result_status"] = result_status(outcomes)
    metrics["outcomes"] = outcomes
    return metrics
