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
    "Sneha Kiran Lakshmi Nikhil Priya Varun Sanjay Divya Harsh Isha "
    "Yash Riya Kunal Anushka Manav Ira Atharv Khushi Omisha Veer"
).split()
LAST_NAMES = (
    "Sharma Verma Iyer Nair Reddy Patel Singh Gupta Joshi Mehta "
    "Das Rao Kulkarni Chopra Malhotra Bose Menon Pillai Banerjee Kapoor "
    "Shah Desai Trivedi Pandey Chauhan"
).split()
DEPARTMENTS = ("Computer Science", "Information Technology", "Data Science")
SEMESTERS = tuple(f"Semester {n}" for n in range(1, 9))


def _names(count: int, rng: random.Random) -> list[str]:
    pairs = [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]
    if count > len(pairs):
        raise ValueError("Not enough fictional names for the requested row count.")
    chosen = pairs[:]
    rng.shuffle(chosen)
    return chosen[:count]


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _mark(skill: float, maximum: float, rng: random.Random, missing_probability: float) -> str:
    if rng.random() < missing_probability:
        return ""
    # Wider spread so grades from F through O appear naturally.
    center = maximum * (0.18 + 0.78 * skill)
    value = rng.gauss(center, maximum * 0.11)
    return f"{_clip(value, 0, maximum):.1f}"


def build_rows(count: int = 180, seed: int = 2026) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for index, name in enumerate(_names(count, rng), start=1):
        semester = rng.choice(SEMESTERS)
        semester_index = SEMESTERS.index(semester)
        # Later semesters lean slightly higher on average; still lots of noise.
        semester_boost = 0.015 * semester_index
        attendance = _clip(rng.gauss(76 + semester_boost * 40, 15), 40, 100)
        study_hours = _clip(0.4 + attendance / 32 + rng.gauss(0, 1.0), 0.5, 9.5)
        skill = _clip(
            0.05
            + semester_boost
            + 0.40 * (attendance / 100)
            + 0.20 * (study_hours / 9.5)
            + rng.gauss(0, 0.18),
            0.02,
            0.98,
        )
        rows.append(
            {
                "student_id": f"S{index:03d}",
                "student_name": name,
                "semester": semester,
                "department": rng.choice(DEPARTMENTS),
                "attendance_percentage": f"{attendance:.1f}",
                "study_hours": f"{study_hours:.1f}",
                "mathematics_marks": _mark(skill, 100, rng, 0.05),
                "programming_marks": _mark(skill, 100, rng, 0.05),
                "database_marks": _mark(skill, 100, rng, 0.05),
                "internal_marks": _mark(skill, 50, rng, 0.04),
                "final_marks": _mark(skill, 100, rng, 0.04),
            }
        )
    by_id = {row["student_id"]: row for row in rows}
    # Fixed demo edges across different semesters — still fictional.
    overrides = {
        "S001": {
            "semester": "Semester 7",
            "department": "Information Technology",
            "attendance_percentage": "96.0",
            "study_hours": "6.0",
            "mathematics_marks": "94.0",
            "programming_marks": "91.0",
            "database_marks": "93.0",
            "internal_marks": "46.0",
            "final_marks": "92.0",
        },
        "S040": {
            "semester": "Semester 3",
            "department": "Computer Science",
            "attendance_percentage": "58.0",
            "study_hours": "1.0",
            "mathematics_marks": "28.0",
            "programming_marks": "35.0",
            "database_marks": "31.0",
            "internal_marks": "12.0",
            "final_marks": "30.0",
        },
        "S097": {
            "semester": "Semester 2",
            "department": "Data Science",
            "attendance_percentage": "81.0",
            "study_hours": "3.0",
            "mathematics_marks": "",
            "programming_marks": "76.0",
            "database_marks": "74.0",
            "internal_marks": "34.0",
            "final_marks": "73.0",
        },
        "S098": {
            "semester": "Semester 1",
            "department": "Computer Science",
            "attendance_percentage": "88.0",
            "study_hours": "2.5",
            "mathematics_marks": "",
            "programming_marks": "",
            "database_marks": "",
            "internal_marks": "",
            "final_marks": "",
        },
        "S099": {
            "semester": "Semester 8",
            "department": "Information Technology",
            "attendance_percentage": "90.0",
            "study_hours": "4.0",
            "mathematics_marks": "0",
            "programming_marks": "72.0",
            "database_marks": "70.0",
            "internal_marks": "30.0",
            "final_marks": "68.0",
        },
        "S100": {
            "semester": "Semester 4",
            "department": "Data Science",
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


def write_sample(path: Path = SAMPLE_CSV_PATH, count: int = 180) -> Path:
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
