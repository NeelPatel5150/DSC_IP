"""Train a small regression model on the stored final marks. Nothing is written back."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from modules.config import MIN_PREDICTION_ROWS, PREDICTION_FEATURES, PREDICTION_TARGET
from modules.prediction import train_final_mark_model
from modules.ui import banner, empty_state, loading, open_records, prepare_page

settings = prepare_page()
banner(
    "Performance Estimate",
    "Optional model. Estimated final marks are shown separately from the stored examination marks.",
)

st.caption(
    "Inputs: attendance, study hours, internal marks, and the three subject marks. "
    "Target: final marks. Rows without a final mark are left out and are not filled with a guess. "
    f"Training starts only when at least {MIN_PREDICTION_ROWS} labeled rows are available. "
    "Results on this fictional sample are a demonstration and may not generalize to real students."
)

performance = open_records(settings["pass_percent"])
if performance.empty:
    empty_state("No records yet", "Load or add student records before training a model.")
    st.stop()

if PREDICTION_TARGET not in performance.columns:
    st.warning("This dataset has no final marks column, so the estimate cannot be trained.")
    st.stop()

labeled = int(performance[PREDICTION_TARGET].notna().sum())
st.write(
    f"Stored students: {len(performance)}. Students with a recorded final mark: {labeled}. "
    f"Students excluded because the final mark is missing: {len(performance) - labeled}."
)

signature = pd.util.hash_pandas_object(
    performance.loc[:, ["student_id", *PREDICTION_FEATURES, PREDICTION_TARGET]],
    index=False,
).sum()

if st.button("Train and evaluate", type="primary"):
    with loading("Splitting the labeled rows and fitting the models…"):
        outcome = train_final_mark_model(performance)
    st.session_state["prediction_outcome"] = outcome
    st.session_state["prediction_signature"] = signature

outcome = st.session_state.get("prediction_outcome")
if outcome is None or st.session_state.get("prediction_signature") != signature:
    st.info("Choose Train and evaluate to calculate MAE and RMSE on a held-out split. No score is stored in advance.")
    st.stop()

if outcome.status != "ok":
    st.warning(outcome.message)
    st.stop()

st.success(outcome.message)
metrics = pd.DataFrame(
    [
        {
            "Model": "Linear regression",
            "MAE": round(outcome.linear_mae, 2),
            "RMSE": round(outcome.linear_rmse, 2),
            "R2": None if outcome.linear_r2 is None else round(outcome.linear_r2, 3),
        },
        {
            "Model": "Mean baseline",
            "MAE": round(outcome.baseline_mae, 2),
            "RMSE": round(outcome.baseline_rmse, 2),
            "R2": None if outcome.baseline_r2 is None else round(outcome.baseline_r2, 3),
        },
    ]
)
st.dataframe(metrics, width="stretch", hide_index=True)
st.caption(
    "MAE is the average absolute difference between estimated and actual final marks on the test rows. "
    "RMSE gives more weight to large misses. R² can look unstable on a small synthetic test split, "
    "so MAE against the baseline is the comparison that matters here. "
    "The baseline predicts the training-set average for every test student."
)

st.subheader("Test-set estimates")
st.caption(
    "Actual final marks are the stored examination values. "
    "Estimated final marks come from the model and are not saved as results."
)
show = outcome.comparison.copy()
for column in ("actual_final_marks", "estimated_final_marks", "baseline_estimate"):
    show[column] = show[column].map(lambda value: round(float(value), 1))
show = show.rename(
    columns={
        "student_id": "Student ID",
        "student_name": "Student name",
        "actual_final_marks": "Actual final marks",
        "estimated_final_marks": "Estimated final marks",
        "baseline_estimate": "Baseline estimate",
    }
)
st.dataframe(show, width="stretch", hide_index=True)
