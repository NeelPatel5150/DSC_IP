"""Glue between the database and the calculations used by every page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.analytics import build_summary, enrich
from modules.config import DATABASE_PATH, PASS_PERCENT, SAMPLE_CSV_PATH
from modules.data_loader import load_sample_dataframe
from modules.database import clear_students, fetch_wide, import_records, init_db, list_student_ids
from modules.risk import build_flag_table
from modules.validation import validate_dataframe


def ensure_database(db_path: Path | str = DATABASE_PATH) -> None:
    init_db(db_path)


def current_performance(
    pass_percent: float = PASS_PERCENT,
    db_path: Path | str = DATABASE_PATH,
) -> pd.DataFrame:
    """Read SQLite and add grades. An empty database returns an empty frame."""
    ensure_database(db_path)
    raw = fetch_wide(db_path)
    if raw.empty:
        return raw
    return enrich(raw, pass_percent=pass_percent)


def dashboard_summary(performance: pd.DataFrame, pass_percent: float, attendance_threshold: float, overall_threshold: float) -> dict:
    flags = build_flag_table(
        performance,
        pass_percent=pass_percent,
        attendance_threshold=attendance_threshold,
        overall_threshold=overall_threshold,
    )
    flagged = 0 if flags.empty else int(flags["student_id"].nunique())
    return build_summary(performance, flagged)


def load_sample_into_database(
    db_path: Path | str = DATABASE_PATH,
    sample_path: Path | str = SAMPLE_CSV_PATH,
    replace: bool = False,
) -> dict:
    """Import the fictional sample. ``replace`` deletes current rows first."""
    ensure_database(db_path)
    frame = load_sample_dataframe(sample_path)
    report = validate_dataframe(frame)
    if report.has_structural_error or report.invalid_count:
        messages = list(report.file_errors)
        messages.extend(
            f"Row {item['row_number']}: {'; '.join(item['messages'])}" for item in report.row_errors
        )
        raise ValueError("The sample dataset did not pass validation. " + " ".join(messages))
    if replace:
        clear_students(db_path)
    result = import_records(report.valid_frame, db_path=db_path, update_existing=replace)
    return {
        "inserted": result.inserted,
        "updated": result.updated,
        "skipped": result.skipped,
        "stored_ids": list_student_ids(db_path),
    }
