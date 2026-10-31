"""Optional estimate of final marks from the other stored fields.

The target column ``final_marks`` is never used as an input. Rows without a
final mark are dropped and are not filled in. Feature medians are learned
from the training split only. Estimates are not written back to the database.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from modules.config import MIN_PREDICTION_ROWS, PREDICTION_FEATURES, PREDICTION_TARGET


@dataclass
class PredictionOutcome:
    status: str
    message: str
    rows_with_target: int
    rows_missing_target: int
    n_train: int
    n_test: int
    linear_mae: float | None
    linear_rmse: float | None
    linear_r2: float | None
    baseline_mae: float | None
    baseline_rmse: float | None
    baseline_r2: float | None
    comparison: pd.DataFrame | None
    features_used: list[str]
    pipeline: object | None = None
    baseline_value: float | None = None


def regression_scores(y_true: object, y_pred: object) -> dict[str, float | None]:
    """MAE, RMSE, and R². R² is None when the actual values do not vary."""
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(actual - predicted)))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    residual = float(np.sum((actual - predicted) ** 2))
    total = float(np.sum((actual - np.mean(actual)) ** 2))
    r2 = None if total == 0 else float(1.0 - residual / total)
    return {"mae": mae, "rmse": rmse, "r2": r2}


def _empty_outcome(status: str, message: str, with_target: int, missing_target: int) -> PredictionOutcome:
    return PredictionOutcome(
        status=status,
        message=message,
        rows_with_target=with_target,
        rows_missing_target=missing_target,
        n_train=0,
        n_test=0,
        linear_mae=None,
        linear_rmse=None,
        linear_r2=None,
        baseline_mae=None,
        baseline_rmse=None,
        baseline_r2=None,
        comparison=None,
        features_used=list(PREDICTION_FEATURES),
    )


def train_final_mark_model(df: pd.DataFrame, random_state: int = 42) -> PredictionOutcome:
    """Fit linear regression and compare it with a mean baseline on a held-out split."""
    if df is None or df.empty or PREDICTION_TARGET not in df.columns:
        return _empty_outcome("no_target", "Final marks are not available in this dataset.", 0, 0)

    working = df.copy()
    target = pd.to_numeric(working[PREDICTION_TARGET], errors="coerce")
    missing_target = int(target.isna().sum())
    model_rows = working.loc[target.notna()].copy()
    with_target = int(len(model_rows))

    if with_target < MIN_PREDICTION_ROWS:
        return _empty_outcome(
            "too_small",
            (
                f"Only {with_target} students have a recorded final mark. "
                f"This demonstration trains only when at least {MIN_PREDICTION_ROWS} labeled rows are available. "
                "A smaller sample can produce a score that looks precise and still does not generalize."
            ),
            with_target,
            missing_target,
        )

    y = pd.to_numeric(model_rows[PREDICTION_TARGET], errors="coerce")
    if int(y.nunique()) < 2:
        return _empty_outcome(
            "no_variance",
            "Final marks do not vary, so a regression model would not be meaningful.",
            with_target,
            missing_target,
        )

    feature_frame = model_rows.loc[:, ["student_id", "student_name", *PREDICTION_FEATURES]].copy()
    for column in PREDICTION_FEATURES:
        feature_frame[column] = pd.to_numeric(feature_frame[column], errors="coerce")

    features = [column for column in PREDICTION_FEATURES if feature_frame[column].notna().any()]
    if not features:
        return _empty_outcome(
            "no_features",
            "None of the prediction inputs have recorded values.",
            with_target,
            missing_target,
        )

    x_train, x_test, y_train, y_test = train_test_split(
        feature_frame,
        y,
        test_size=0.25,
        random_state=random_state,
    )
    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("model", LinearRegression()),
        ]
    )
    pipeline.fit(x_train[features], y_train)
    linear_pred = pipeline.predict(x_test[features])
    baseline_value = float(y_train.mean())
    baseline_pred = np.full(shape=len(y_test), fill_value=baseline_value, dtype=float)

    linear = regression_scores(y_test, linear_pred)
    baseline = regression_scores(y_test, baseline_pred)
    comparison = pd.DataFrame(
        {
            "student_id": x_test["student_id"].to_numpy(),
            "student_name": x_test["student_name"].to_numpy(),
            "actual_final_marks": y_test.to_numpy(),
            "estimated_final_marks": linear_pred,
            "baseline_estimate": baseline_pred,
            "residual": linear_pred - y_test.to_numpy(),
            "absolute_error": np.abs(linear_pred - y_test.to_numpy()),
        }
    ).sort_values("student_id").reset_index(drop=True)

    better = linear["mae"] < baseline["mae"]
    comparison_sentence = (
        "On this test split, linear regression has a lower MAE than the mean baseline."
        if better
        else "On this test split, linear regression does not beat the mean baseline on MAE."
    )
    dropped = [column for column in PREDICTION_FEATURES if column not in features]
    dropped_sentence = (
        f" These inputs were left out because every value was missing: {', '.join(dropped)}."
        if dropped
        else ""
    )
    message = (
        "The model estimates final marks from attendance, study hours, internal marks, "
        "and the three subject marks. The final mark is the target only, so it is not used as an input. "
        "Estimates are not examination results and are not saved. "
        f"{comparison_sentence} Training used {len(x_train)} rows and testing used {len(x_test)} rows. "
        f"{missing_target} rows were excluded because the final mark was missing.{dropped_sentence}"
    )
    return PredictionOutcome(
        status="ok",
        message=message,
        rows_with_target=with_target,
        rows_missing_target=missing_target,
        n_train=int(len(x_train)),
        n_test=int(len(x_test)),
        linear_mae=linear["mae"],
        linear_rmse=linear["rmse"],
        linear_r2=linear["r2"],
        baseline_mae=baseline["mae"],
        baseline_rmse=baseline["rmse"],
        baseline_r2=baseline["r2"],
        comparison=comparison,
        features_used=features,
        pipeline=pipeline,
        baseline_value=baseline_value,
    )


def estimate_final_marks(outcome: PredictionOutcome, feature_values: dict) -> float | None:
    """Estimate one final mark from what-if inputs. Does not write to the database."""
    pipeline = getattr(outcome, "pipeline", None)
    if outcome is None or outcome.status != "ok" or pipeline is None:
        return None
    if not outcome.features_used:
        return None
    row = {}
    for column in outcome.features_used:
        value = feature_values.get(column)
        if value is None or (isinstance(value, float) and np.isnan(value)):
            row[column] = np.nan
        else:
            row[column] = float(value)
    frame = pd.DataFrame([row], columns=outcome.features_used)
    predicted = float(pipeline.predict(frame)[0])
    return float(np.clip(predicted, 0.0, 100.0))
