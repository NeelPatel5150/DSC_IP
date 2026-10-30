"""Table-level academic calculations.

These functions do not read the database and do not draw charts. Pages pass
in a dataframe and display whatever comes back.
"""

from __future__ import annotations

import pandas as pd

from modules.config import MARK_SCHEMES, PASS_PERCENT
from modules.grading import summarize_student

SUMMARY_COLUMNS = (
    "subjects_attempted",
    "subject_total",
    "subject_maximum",
    "subject_percentage",
    "overall_average",
    "subjects_recorded",
    "grade",
    "result_status",
    "subjects_key",
    "class_rank",
    "rank_group_size",
)


def enrich(df: pd.DataFrame, pass_percent: float = PASS_PERCENT) -> pd.DataFrame:
    """Add percentage, grade, pass/fail, and full-group rank columns."""
    if df is None or df.empty:
        columns = list(df.columns) if isinstance(df, pd.DataFrame) else []
        return pd.DataFrame(columns=columns + list(SUMMARY_COLUMNS))

    summaries = []
    for record in df.to_dict(orient="records"):
        summary = summarize_student(record, pass_percent=pass_percent)
        summary.pop("outcomes", None)
        summary["subjects_key"] = summary["subjects_recorded"] or "No subjects recorded"
        summaries.append(summary)

    extra = pd.DataFrame(summaries)
    combined = pd.concat([df.reset_index(drop=True), extra], axis=1)
    return _add_ranks(combined)


def _add_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Rank students who share semester, department, and recorded subjects.

    A group of one is not ranked. Students with no subject percentage are
    not ranked. Rank 1 is the highest subject percentage. Ties share the
    minimum rank.
    """
    out = df.copy()
    out["class_rank"] = pd.NA
    out["rank_group_size"] = 0
    group_columns = ["semester", "department", "subjects_key"]
    for _, index in out.groupby(group_columns, dropna=False).groups.items():
        members = out.loc[list(index)]
        ranked = members.dropna(subset=["subject_percentage"])
        out.loc[members.index, "rank_group_size"] = int(len(ranked))
        if len(ranked) < 2:
            continue
        ranks = ranked["subject_percentage"].rank(ascending=False, method="min")
        out.loc[ranks.index, "class_rank"] = ranks.astype("int64")
    return out


def apply_filters(
    df: pd.DataFrame,
    search: str = "",
    semester: str = "All",
    department: str = "All",
) -> pd.DataFrame:
    """Filter by semester, department, and a case-insensitive ID or name search."""
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    view = df
    if semester and semester != "All":
        view = view[view["semester"] == semester]
    if department and department != "All":
        view = view[view["department"] == department]
    query = (search or "").strip().lower()
    if query:
        id_match = view["student_id"].astype(str).str.lower().str.contains(query, regex=False)
        name_match = view["student_name"].astype(str).str.lower().str.contains(query, regex=False)
        view = view[id_match | name_match]
    return view.reset_index(drop=True)


def subject_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Average, highest, and lowest for each component, skipping blank marks."""
    rows = []
    for scheme in MARK_SCHEMES:
        if df is None or df.empty or scheme["column"] not in df.columns:
            series = pd.Series(dtype="float64")
        else:
            series = pd.to_numeric(df[scheme["column"]], errors="coerce").dropna()
        recorded = int(series.shape[0])
        average = float(series.mean()) if recorded else None
        maximum = float(scheme["maximum"])
        rows.append(
            {
                "subject": scheme["subject_name"],
                "column": scheme["column"],
                "students_recorded": recorded,
                "average": average,
                "highest": float(series.max()) if recorded else None,
                "lowest": float(series.min()) if recorded else None,
                "maximum_marks": maximum,
                "average_percent": None if average is None else average / maximum * 100.0,
            }
        )
    return pd.DataFrame(rows)


def build_summary(df: pd.DataFrame, flagged_students: int) -> dict:
    """Dashboard card values. Empty input does not invent zeroes for rates."""
    if df is None or df.empty:
        return {
            "total_students": 0,
            "overall_average": None,
            "average_attendance": None,
            "pass_percentage": None,
            "passed": 0,
            "failed": 0,
            "incomplete": 0,
            "highest": None,
            "flagged": 0,
            "has_data": False,
        }

    with_percentage = df.dropna(subset=["subject_percentage"])
    evaluated = df[df["result_status"].isin(["Pass", "Fail"])]
    passed = int((df["result_status"] == "Pass").sum())
    failed = int((df["result_status"] == "Fail").sum())
    incomplete = int((df["result_status"] == "Incomplete").sum())
    attendance = pd.to_numeric(df["attendance_percentage"], errors="coerce").dropna()
    return {
        "total_students": int(len(df)),
        "overall_average": float(with_percentage["subject_percentage"].mean())
        if not with_percentage.empty
        else None,
        "average_attendance": float(attendance.mean()) if not attendance.empty else None,
        "pass_percentage": (passed / len(evaluated) * 100.0) if len(evaluated) else None,
        "passed": passed,
        "failed": failed,
        "incomplete": incomplete,
        "highest": float(with_percentage["subject_percentage"].max())
        if not with_percentage.empty
        else None,
        "flagged": int(flagged_students),
        "has_data": True,
    }


def pearson(df: pd.DataFrame, x_column: str, y_column: str, min_pairs: int = 5) -> tuple[float | None, int]:
    """Pearson correlation and the number of complete pairs.

    Fewer than ``min_pairs`` complete rows returns ``(None, count)`` so the
    page can say the sample is too small instead of quoting a noisy value.
    """
    if df is None or df.empty or x_column not in df.columns or y_column not in df.columns:
        return None, 0
    pairs = df[[x_column, y_column]].apply(pd.to_numeric, errors="coerce").dropna()
    count = int(len(pairs))
    if count < min_pairs:
        return None, count
    if pairs[x_column].nunique() < 2 or pairs[y_column].nunique() < 2:
        return None, count
    return float(pairs[x_column].corr(pairs[y_column])), count


def correlation_matrix(df: pd.DataFrame, columns: list[str], min_pairs: int = 5) -> pd.DataFrame:
    """Correlation matrix using only columns that have enough numbers."""
    usable = []
    for column in columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.nunique() >= 2 and len(series) >= min_pairs:
            usable.append(column)
    if len(usable) < 2:
        return pd.DataFrame()
    return df[usable].apply(pd.to_numeric, errors="coerce").corr()


def describe_correlation(coefficient: float | None, pair_count: int, x_name: str, y_name: str) -> str:
    """Plain-language description that does not claim a cause."""
    if coefficient is None:
        return (
            f"Not enough paired values to describe a correlation between {x_name} and {y_name} "
            f"({pair_count} complete pairs). At least 5 pairs with variation are required."
        )
    magnitude = abs(coefficient)
    if magnitude < 0.3:
        strength = "weak"
    elif magnitude < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    direction = "positive" if coefficient > 0 else "negative"
    return (
        f"In this filtered dataset, {x_name} and {y_name} show a {strength} {direction} "
        f"Pearson correlation (r = {coefficient:.2f}, n = {pair_count}). "
        "This describes the selected records only. It does not show that one variable causes the other."
    )


def find_existing_ids(candidate_ids: list[str], stored_ids: list[str]) -> list[str]:
    """IDs that are both in the upload and already in the database."""
    stored = {str(value).strip().upper() for value in stored_ids}
    seen = []
    for value in candidate_ids:
        student_id = str(value).strip().upper()
        if student_id in stored and student_id not in seen:
            seen.append(student_id)
    return seen
