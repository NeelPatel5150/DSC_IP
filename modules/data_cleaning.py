"""Column cleanup for uploaded student tables.

Assumptions, also stated in the README:

- Column headers are matched after trimming, lowercasing, and turning
  underscores into spaces. ``Student ID`` and ``student_id`` are the same.
- Semester and department labels are stored in title case so
  ``computer science`` and ``Computer Science`` land in one category.
- A blank mark stays missing. It is never replaced with zero.
- A numeric zero is kept, because a student can genuinely score zero.
- Extra columns are ignored and reported. They are not stored.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import pandas as pd

from modules.config import COLUMN_ALIASES, REQUIRED_COLUMNS

_DUPLICATE_SUFFIX = re.compile(r"\.\d+$")


@dataclass
class PreparedTable:
    """A renamed table plus file-level problems found before row checks."""

    frame: pd.DataFrame
    ignored_columns: list[str]
    missing_columns: list[str]
    file_errors: list[str]


def canonicalize_column(name: object) -> str:
    """Map one header to the project's column name, or a normalized leftover."""
    text = _DUPLICATE_SUFFIX.sub("", str(name))
    key = " ".join(text.strip().lower().replace("_", " ").split())
    if key in COLUMN_ALIASES:
        return COLUMN_ALIASES[key]
    return key.replace(" ", "_")


def is_blank(value: object) -> bool:
    """True when a cell should be treated as 'not recorded'."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        try:
            return bool(math.isnan(float(value)))
        except (TypeError, ValueError):
            return False
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def parse_number(value: object) -> tuple[float | None, str]:
    """Parse a cell.

    Returns ``(number, "ok")``, ``(None, "blank")``, or ``(None, "bad")``.
    A trailing percent sign is allowed so ``85%`` can be read as 85.
    """
    if is_blank(value):
        return None, "blank"
    if isinstance(value, bool):
        return None, "bad"
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None, "bad"
        return number, "ok"
    text = str(value).strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        number = float(text)
    except ValueError:
        return None, "bad"
    if math.isnan(number) or math.isinf(number):
        return None, "bad"
    return number, "ok"


def normalize_label(value: object) -> str:
    """Collapse spacing and use title case for semester and department."""
    return " ".join(str(value).split()).title()


def normalize_person_name(value: object) -> str:
    """Collapse spacing. Names are not title-cased, so initials stay as typed."""
    return " ".join(str(value).split())


def prepare_columns(df: pd.DataFrame) -> PreparedTable:
    """Rename headers and report missing, extra, or colliding columns."""
    if df is None or not isinstance(df, pd.DataFrame):
        return PreparedTable(
            pd.DataFrame(),
            [],
            list(REQUIRED_COLUMNS),
            ["The uploaded data is not a table."],
        )

    file_errors: list[str] = []
    if len(df.columns) == 0:
        file_errors.append("The file has no column headers.")
        return PreparedTable(pd.DataFrame(), [], list(REQUIRED_COLUMNS), file_errors)

    canonical_names: list[str] = []
    seen: dict[str, str] = {}
    for original in df.columns:
        canonical = canonicalize_column(original)
        if canonical in seen:
            file_errors.append(
                f"The columns '{seen[canonical]}' and '{original}' both map to '{canonical}'."
            )
        else:
            seen[canonical] = str(original)
        canonical_names.append(canonical)

    working = df.copy()
    working.columns = canonical_names

    ignored = [name for name in canonical_names if name not in REQUIRED_COLUMNS]
    missing = [name for name in REQUIRED_COLUMNS if name not in seen]

    if file_errors:
        return PreparedTable(pd.DataFrame(), ignored, missing, file_errors)

    if missing:
        return PreparedTable(pd.DataFrame(), ignored, missing, [])

    # Keep one copy of each required column in a stable order.
    frame = working.loc[:, list(REQUIRED_COLUMNS)].copy()
    return PreparedTable(frame, ignored, [], [])
