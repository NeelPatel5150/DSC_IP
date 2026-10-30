"""One-student report built only from that student's row and group averages.

Class averages do not include other students' names or individual marks.
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from modules.config import (
    ATTENDANCE_REVIEW_PERCENT,
    MARK_SCHEMES,
    OVERALL_REVIEW_PERCENT,
    PASS_PERCENT,
)
from modules.data_cleaning import is_blank
from modules.grading import pass_threshold
from modules.risk import review_reasons


def _peer_average(peers: pd.DataFrame, column: str) -> float | None:
    if peers is None or peers.empty or column not in peers.columns:
        return None
    series = pd.to_numeric(peers[column], errors="coerce").dropna()
    if series.empty:
        return None
    return float(series.mean())


def _compare(marks: float | None, average: float | None) -> str:
    if marks is None:
        return "Not recorded"
    if average is None:
        return "No class average available"
    if abs(marks - average) < 0.05:
        return "Matches the class average"
    if marks > average:
        return "Above the class average"
    return "Below the class average"


def build_student_report(
    student_id: str,
    performance: pd.DataFrame,
    pass_percent: float = PASS_PERCENT,
    attendance_threshold: float = ATTENDANCE_REVIEW_PERCENT,
    overall_threshold: float = OVERALL_REVIEW_PERCENT,
) -> dict | None:
    """Build a report for one ID. Returns None when the student is not in the frame."""
    if performance is None or performance.empty:
        return None
    matches = performance[
        performance["student_id"].astype(str).str.upper() == str(student_id).strip().upper()
    ]
    if matches.empty:
        return None
    student = matches.iloc[0].to_dict()
    peers = performance[
        (performance["semester"] == student["semester"])
        & (performance["department"] == student["department"])
    ]

    subjects = []
    strengths = []
    improvements = []
    for scheme in MARK_SCHEMES:
        marks = None if is_blank(student.get(scheme["column"])) else float(student[scheme["column"]])
        average = _peer_average(peers, scheme["column"])
        comparison = _compare(marks, average)
        subjects.append(
            {
                "subject": scheme["subject_name"],
                "marks": marks,
                "maximum": float(scheme["maximum"]),
                "class_average": average,
                "comparison": comparison,
            }
        )
        if marks is None or not scheme["counts_for_percentage"]:
            continue
        threshold = pass_threshold(scheme["maximum"], pass_percent)
        if comparison == "Above the class average" and marks >= threshold:
            strengths.append(scheme["subject_name"])
        if comparison == "Below the class average" or marks < threshold:
            improvements.append(scheme["subject_name"])

    reasons = review_reasons(
        student,
        pass_percent=pass_percent,
        attendance_threshold=attendance_threshold,
        overall_threshold=overall_threshold,
    )
    suggestions = [item["message"] for item in reasons]
    if improvements:
        suggestions.append(
            "These subjects are below the class average or the pass mark: "
            + ", ".join(improvements)
            + ". Additional practice in those subjects may help."
        )
    if not suggestions:
        suggestions.append(
            "No review rule fired for the current thresholds. Continue regular academic monitoring."
        )

    percentage = student.get("subject_percentage")
    fields = [
        ("Student ID", student.get("student_id")),
        ("Student name", student.get("student_name")),
        ("Semester", student.get("semester")),
        ("Department", student.get("department")),
        ("Attendance %", _format_number(student.get("attendance_percentage"))),
        ("Study hours per day", _format_number(student.get("study_hours"))),
        ("Subjects recorded", student.get("subjects_recorded") or "None"),
        ("Subject total", _format_number(student.get("subject_total"))),
        ("Subject maximum", _format_number(student.get("subject_maximum"))),
        ("Subject percentage", _format_number(percentage)),
        ("Grade", student.get("grade") or "Not available"),
        ("Result", student.get("result_status") or "Not available"),
        ("Rank in comparison group", _format_rank(student.get("class_rank"), student.get("rank_group_size"))),
        ("Pass mark used", f"{float(pass_percent):.0f}% of each component maximum"),
        (
            "Comparison group",
            f"All stored students in {student.get('semester')}, {student.get('department')}.",
        ),
    ]
    return {
        "student_id": student.get("student_id"),
        "student_name": student.get("student_name"),
        "fields": fields,
        "subjects": subjects,
        "strengths": strengths,
        "improvements": improvements,
        "suggestions": suggestions,
        "rules_note": (
            "Suggestions follow the published demonstration rules. "
            "They are decision-support notes, not a judgment of the student's ability. "
            "Letter grades use the fixed demonstration scale. "
            "Pass or fail also checks recorded subject marks and the internal mark."
        ),
    }


def subject_table(report: dict) -> pd.DataFrame:
    """Subject rows for the on-screen table, rounded for display."""
    frame = pd.DataFrame(report["subjects"])
    for column in ("marks", "class_average"):
        frame[column] = frame[column].map(lambda value: None if is_blank(value) else round(float(value), 1))
    frame["maximum"] = frame["maximum"].map(lambda value: round(float(value), 1))
    return frame


def _format_number(value: object) -> str:
    if is_blank(value):
        return "Not recorded"
    return f"{float(value):.1f}"


def _format_rank(rank: object, group_size: object) -> str:
    if is_blank(rank):
        return "Not ranked. A rank is shown only when at least two students share the same recorded subjects."
    size = int(group_size) if not is_blank(group_size) else 0
    return f"{int(rank)} of {size}"


def report_to_csv_bytes(report: dict) -> bytes:
    """Two-column field/value file, including subject rows. No other student's marks."""
    rows = [{"section": "profile", "field": label, "value": value} for label, value in report["fields"]]
    for subject in report["subjects"]:
        rows.append(
            {
                "section": "subject",
                "field": subject["subject"],
                "value": (
                    f"marks={_format_number(subject['marks'])}; "
                    f"maximum={subject['maximum']:g}; "
                    f"class_average={_format_number(subject['class_average'])}; "
                    f"comparison={subject['comparison']}"
                ),
            }
        )
    for index, text in enumerate(report["suggestions"], start=1):
        rows.append({"section": "suggestion", "field": f"suggestion_{index}", "value": text})
    rows.append({"section": "note", "field": "rules", "value": report["rules_note"]})
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def report_to_pdf_bytes(report: dict) -> bytes:
    """Simple text PDF. Characters outside Latin-1 are replaced so the file still builds."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    _write(pdf, "Student academic performance report", height=9, style="B", size=16)
    _write(
        pdf,
        "Synthetic demonstration report. It contains one student and class averages only.",
        height=6,
        size=11,
    )
    for label, value in report["fields"]:
        _write(pdf, f"{label}: {value}")
    _write(pdf, "Subject marks", height=8, style="B", size=13)
    for subject in report["subjects"]:
        line = (
            f"{subject['subject']}: {_format_number(subject['marks'])} / {subject['maximum']:g}. "
            f"Class average {_format_number(subject['class_average'])}. {subject['comparison']}."
        )
        _write(pdf, line)
    _write(pdf, "Strengths", height=8, style="B", size=13)
    strength_text = ", ".join(report["strengths"]) if report["strengths"] else "None identified by the current rules."
    _write(pdf, strength_text)
    _write(pdf, "Areas that may need support", height=8, style="B", size=13)
    improvement_text = (
        ", ".join(report["improvements"]) if report["improvements"] else "None identified by the current rules."
    )
    _write(pdf, improvement_text)
    _write(pdf, "Suggestions", height=8, style="B", size=13)
    for text in report["suggestions"]:
        _write(pdf, f"- {text}")
    _write(pdf, report["rules_note"])
    output = pdf.output()
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    buffer = BytesIO()
    buffer.write(output)
    return buffer.getvalue()


def _pdf_safe(text: object) -> str:
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def _write(pdf, text: object, height: float = 6, style: str = "", size: int = 11) -> None:
    """Write one wrapped block and return to the left margin for the next block."""
    pdf.set_font("Helvetica", style, size)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, height, _pdf_safe(text))
    pdf.ln(1)
