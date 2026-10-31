"""Prediction metrics and the guard against a tiny or leaky model."""

import numpy as np
import pandas as pd

from modules.config import MIN_PREDICTION_ROWS, PREDICTION_FEATURES, PREDICTION_TARGET
from modules.prediction import estimate_final_marks, regression_scores, train_final_mark_model


def test_regression_scores_match_a_hand_calculation():
    scores = regression_scores([0, 0, 3], [0, 0, 0])
    assert scores["mae"] == 1
    assert scores["rmse"] == np.sqrt(3)
    assert scores["r2"] == -0.5
    flat = regression_scores([5, 5, 5], [5, 5, 5])
    assert flat["mae"] == 0
    assert flat["r2"] is None


def test_target_is_not_a_feature_and_small_samples_are_refused():
    assert PREDICTION_TARGET not in PREDICTION_FEATURES
    small = _modeling_frame(10)
    outcome = train_final_mark_model(small)
    assert outcome.status == "too_small"
    assert outcome.linear_mae is None
    assert outcome.comparison is None


def test_model_metrics_are_finite_and_missing_targets_are_excluded():
    frame = _modeling_frame(MIN_PREDICTION_ROWS + 5)
    frame.loc[0, "final_marks"] = np.nan
    frame.loc[1, "mathematics_marks"] = np.nan
    outcome = train_final_mark_model(frame)
    assert outcome.status == "ok"
    assert outcome.rows_missing_target == 1
    assert outcome.rows_with_target == MIN_PREDICTION_ROWS + 4
    assert outcome.n_train + outcome.n_test == outcome.rows_with_target
    assert outcome.linear_mae >= 0
    assert outcome.linear_rmse >= outcome.linear_mae ** 0.5 * 0  # RMSE is non-negative
    assert outcome.linear_rmse >= 0
    assert outcome.baseline_mae >= 0
    assert "final_marks" not in outcome.features_used
    assert set(outcome.comparison["student_id"]).isdisjoint({"S000"})
    assert "estimated_final_marks" in outcome.comparison.columns
    assert "actual_final_marks" in outcome.comparison.columns
    assert "absolute_error" in outcome.comparison.columns
    assert (
        outcome.comparison["absolute_error"]
        == (outcome.comparison["estimated_final_marks"] - outcome.comparison["actual_final_marks"]).abs()
    ).all()
    assert outcome.pipeline is not None
    assert outcome.baseline_value is not None


def test_what_if_estimate_uses_the_trained_pipeline():
    frame = _modeling_frame(MIN_PREDICTION_ROWS + 8)
    outcome = train_final_mark_model(frame)
    assert outcome.status == "ok"
    low = estimate_final_marks(
        outcome,
        {
            "attendance_percentage": 40,
            "study_hours": 1,
            "internal_marks": 10,
            "mathematics_marks": 20,
            "programming_marks": 20,
            "database_marks": 20,
        },
    )
    high = estimate_final_marks(
        outcome,
        {
            "attendance_percentage": 98,
            "study_hours": 8,
            "internal_marks": 45,
            "mathematics_marks": 95,
            "programming_marks": 95,
            "database_marks": 95,
        },
    )
    assert low is not None and high is not None
    assert 0 <= low <= 100
    assert 0 <= high <= 100
    assert high > low


def _modeling_frame(rows: int) -> pd.DataFrame:
    records = []
    for index in range(rows):
        attendance = 50 + (index % 40)
        records.append(
            {
                "student_id": f"S{index:03d}",
                "student_name": f"Student {index}",
                "attendance_percentage": attendance,
                "study_hours": 1 + (index % 5),
                "internal_marks": 15 + (index % 20),
                "mathematics_marks": 40 + (index % 50),
                "programming_marks": 35 + (index % 55),
                "database_marks": 45 + (index % 45),
                "final_marks": attendance * 0.4 + (index % 7),
            }
        )
    return pd.DataFrame(records)
