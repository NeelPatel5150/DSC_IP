"""Read CSV and Excel uploads, plus the bundled sample file."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.config import REQUIRED_COLUMNS, SAMPLE_CSV_PATH

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def read_dataframe(file_obj: object, filename: str) -> pd.DataFrame:
    """Read a CSV or xlsx file object. Lines that start with # are comments in CSV."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only .csv and .xlsx files are supported. Older .xls files are not.")
    if suffix == ".csv":
        return pd.read_csv(file_obj, comment="#")
    return pd.read_excel(file_obj, engine="openpyxl")


def load_sample_dataframe(path: Path | str = SAMPLE_CSV_PATH) -> pd.DataFrame:
    """Load the bundled fictional dataset."""
    return pd.read_csv(path, comment="#")


def sample_csv_bytes(path: Path | str = SAMPLE_CSV_PATH) -> bytes:
    return Path(path).read_bytes()


def template_csv_bytes() -> bytes:
    """Header row plus one obvious example. The example is fictional."""
    header = ",".join(REQUIRED_COLUMNS)
    note = (
        "# SYNTHETIC TEMPLATE — fictional example only. "
        "Delete the example row or replace it before a real demonstration import.\n"
    )
    example = "EXAMPLE,Example Student,Semester 5,Computer Science,80,2,70,70,70,30,70\n"
    return f"{note}{header}\n{example}".encode("utf-8")


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")
