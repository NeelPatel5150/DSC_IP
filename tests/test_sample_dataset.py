"""The bundled fictional dataset is large enough and passes the same checks as an upload."""

from data.generate_sample import build_rows
from modules.config import SAMPLE_CSV_PATH
from modules.data_loader import load_sample_dataframe
from modules.validation import validate_dataframe


def test_checked_in_sample_is_labeled_and_valid():
    text = SAMPLE_CSV_PATH.read_text(encoding="utf-8")
    assert text.startswith("# SYNTHETIC DATA")
    assert "Not real college results" in text
    frame = load_sample_dataframe()
    report = validate_dataframe(frame)
    assert report.file_errors == []
    assert report.missing_columns == []
    assert report.invalid_count == 0
    assert report.valid_count >= 80
    assert report.valid_frame["student_id"].is_unique


def test_sample_contains_the_demonstration_edges():
    rows = {row["student_id"]: row for row in build_rows(100)}
    assert rows["S001"]["mathematics_marks"] == "94.0"
    assert rows["S040"]["mathematics_marks"] == "28.0"
    assert rows["S097"]["mathematics_marks"] == ""
    assert rows["S098"]["programming_marks"] == ""
    assert rows["S098"]["internal_marks"] == ""
    assert rows["S099"]["mathematics_marks"] == "0"
    assert float(rows["S100"]["attendance_percentage"]) < 75
