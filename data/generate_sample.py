"""Create the fictional sample CSV.

The people, marks, and attendance values are invented. They are not college
records. Run this file to regenerate ``data/sample_students.csv``.
It does not change the SQLite database.
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.config import REQUIRED_COLUMNS, SAMPLE_CSV_PATH

FIRST_NAMES = (
    "Aarav Vivaan Aditya Vihaan Arjun Sai Reyansh Krishna Ishaan Shaurya "
    "Meera Ananya Diya Aadhya Sara Anika Navya Pari Myra Kiara "
    "Kabir Rohan Neel Dev Ayaan Tara Nisha Rahul Pooja Amit "
    "Sneha Kiran Lakshmi Nikhil Priya Varun Sanjay Divya Harsh Isha"
).split()
LAST_NAMES = (
    "Sharma Verma Iyer Nair Reddy Patel Singh Gupta Joshi Mehta "
    "Das Rao Kulkarni Chopra Malhotra Bose Menon Pillai Banerjee Kapoor"
).split()
DEPARTMENTS = ("Computer Science", "Information Technology", "Data Science")
SEMESTERS = ("Semester 5", "Semester 6", "Semester 7")


def _names(count: int) -> list[str]:
    pairs = [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]
    if count > len(pairs):
        raise ValueError("Not enough fictional names for the requested row count.")
    return pairs[:count]


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _mark(skill: float, maximum: float, rng: random.Random, missing_probability: float) -> str:
    if rng.random() < missing_probability:
        return ""
    center = maximum * (0.20 + 0.72 * skill)
    value = rng.gauss(center, maximum * 0.09)
    return f"{_clip(value, 0, maximum):.1f}"


def build_rows(count: int = 100, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for index, name in enumerate(_names(count), start=1):
        attendance = _clip(rng.gauss(78, 14), 42, 100)
        study_hours = _clip(0.3 + attendance / 35 + rng.gauss(0, 0.8), 0.5, 8)
        skill = _clip(
            0.08
            + 0.42 * (attendance / 100)
            + 0.18 * (study_hours / 8)
            + rng.gauss(0, 0.16),
            0.02,
            0.98,
        )
        rows.append(
            {
                "student_id": f"S{index:03d}",
                "student_name": name,
                "semester": SEMESTERS[index % len(SEMESTERS)],
                "department": DEPARTMENTS[index % len(DEPARTMENTS)],
                "attendance_percentage": f"{attendance:.1f}",
                "study_hours": f"{study_hours:.1f}",
                "mathematics_marks": _mark(skill, 100, rng, 0.06),
                "programming_marks": _mark(skill, 100, rng, 0.06),
                "database_marks": _mark(skill, 100, rng, 0.06),
                "internal_marks": _mark(skill, 50, rng, 0.05),
                "final_marks": _mark(skill, 100, rng, 0.04),
            }
        )
    by_id = {row["student_id"]: row for row in rows}
    overrides = {
        "S001": {
            "attendance_percentage": "96.0",
            "study_hours": "6.0",
            "mathematics_marks": "94.0",
            "programming_marks": "91.0",
            "database_marks": "93.0",
            "internal_marks": "46.0",
            "final_marks": "92.0",
        },
        "S040": {
            "attendance_percentage": "58.0",
            "study_hours": "1.0",
            "mathematics_marks": "28.0",
            "programming_marks": "35.0",
            "database_marks": "31.0",
            "internal_marks": "12.0",
            "final_marks": "30.0",
        },
        "S097": {
            "attendance_percentage": "81.0",
            "study_hours": "3.0",
            "mathematics_marks": "",
            "programming_marks": "76.0",
            "database_marks": "74.0",
            "internal_marks": "34.0",
            "final_marks": "73.0",
        },
        "S098": {
            "attendance_percentage": "88.0",
            "study_hours": "2.5",
            "mathematics_marks": "",
            "programming_marks": "",
            "database_marks": "",
            "internal_marks": "",
            "final_marks": "",
        },
        "S099": {
            "attendance_percentage": "90.0",
            "study_hours": "4.0",
            "mathematics_marks": "0",
            "programming_marks": "72.0",
            "database_marks": "70.0",
            "internal_marks": "30.0",
            "final_marks": "68.0",
        },
        "S100": {
            "attendance_percentage": "74.0",
            "study_hours": "3.5",
            "mathematics_marks": "78.0",
            "programming_marks": "80.0",
            "database_marks": "77.0",
            "internal_marks": "36.0",
            "final_marks": "79.0",
        },
    }
    for student_id, changes in overrides.items():
        if student_id in by_id:
            by_id[student_id].update(changes)
    return [by_id[f"S{index:03d}"] for index in range(1, count + 1)]


def write_sample(path: Path = SAMPLE_CSV_PATH, count: int = 100) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        handle.write(
            "# SYNTHETIC DATA — fictional students for demonstration only. Not real college results.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(build_rows(count))
    return path


if __name__ == "__main__":
    destination = write_sample()
    print(f"Wrote {destination}")
