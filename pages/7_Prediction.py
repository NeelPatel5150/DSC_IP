"""Train a small regression model on the stored final marks. Nothing is written back."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from modules.config import (
    MIN_PREDICTION_ROWS,
    PREDICTION_FEATURES,
    PREDICTION_TARGET,
    STUDY_HOURS_MAX,
)
from modules.prediction import estimate_final_marks, train_final_mark_model
from modules.ui import banner, empty_state, loading, open_records, prepare_page, show_chart
from modules.visualization import (
    prediction_actual_vs_estimated_scatter,
    prediction_residual_histogram,
)


def _feature_default(value: object, fallback: float) -> float:
    if value is None or pd.isna(value):
        return fallback
    return float(value)

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

st.subheader("Test-set charts")
st.caption(
    "Points near the dashed line are close estimates. "
    "Residuals near zero mean the estimate matched the stored final mark."
)
left, right = st.columns(2)
with left:
    show_chart(
        prediction_actual_vs_estimated_scatter(outcome.comparison),
        "No test-set pairs to plot actual against estimated marks.",
    )
with right:
    show_chart(
        prediction_residual_histogram(outcome.comparison),
        "No residuals to plot for this test split.",
    )

st.subheader("Test-set estimates")
st.caption(
    "Actual final marks are the stored examination values. "
    "Estimated final marks come from the model and are not saved as results. "
    "Absolute error is |estimated − actual|. Smaller is better for that student."
)
show = outcome.comparison.copy()
if "absolute_error" not in show.columns:
    show["absolute_error"] = (
        show["estimated_final_marks"].astype(float) - show["actual_final_marks"].astype(float)
    ).abs()
show = show.loc[
    :,
    [
        "student_id",
        "student_name",
        "actual_final_marks",
        "estimated_final_marks",
        "absolute_error",
    ],
]
for column in ("actual_final_marks", "estimated_final_marks", "absolute_error"):
    show[column] = show[column].map(lambda value: round(float(value), 1))
show = show.rename(
    columns={
        "student_id": "Student ID",
        "student_name": "Student name",
        "actual_final_marks": "Actual final marks",
        "estimated_final_marks": "Estimated final marks",
        "absolute_error": "Absolute error",
    }
)
st.dataframe(show, width="stretch", hide_index=True)

st.subheader("What-if for one student")
if getattr(outcome, "pipeline", None) is None:
    st.info("Train and evaluate again to unlock the what-if explorer for one student.")
    st.stop()
st.caption(
    "Change the inputs below to see how the estimated final mark moves. "
    "This does not change the stored examination marks and is not saved."
)
student_ids = performance["student_id"].tolist()
selected_id = st.selectbox(
    "Student",
    student_ids,
    format_func=lambda value: (
        f"{value} — {performance.loc[performance['student_id'] == value, 'student_name'].iloc[0]}"
    ),
    key="whatif_student_id",
)
student = performance.loc[performance["student_id"] == selected_id].iloc[0]

first, second, third = st.columns(3)
with first:
    attendance = st.number_input(
        "Attendance %",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        value=_feature_default(student.get("attendance_percentage"), 75.0),
        key=f"whatif_attendance_{selected_id}",
    )
    study_hours = st.number_input(
        "Study hours per day",
        min_value=0.0,
        max_value=float(STUDY_HOURS_MAX),
        step=0.5,
        value=_feature_default(student.get("study_hours"), 3.0),
        key=f"whatif_study_{selected_id}",
    )
with second:
    mathematics = st.number_input(
        "Mathematics / 100",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        value=_feature_default(student.get("mathematics_marks"), 50.0),
        key=f"whatif_math_{selected_id}",
    )
    programming = st.number_input(
        "Programming / 100",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        value=_feature_default(student.get("programming_marks"), 50.0),
        key=f"whatif_prog_{selected_id}",
    )
with third:
    database = st.number_input(
        "Database / 100",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        value=_feature_default(student.get("database_marks"), 50.0),
        key=f"whatif_db_{selected_id}",
    )
    internal = st.number_input(
        "Internal / 50",
        min_value=0.0,
        max_value=50.0,
        step=1.0,
        value=_feature_default(student.get("internal_marks"), 25.0),
        key=f"whatif_internal_{selected_id}",
    )

what_if_values = {
    "attendance_percentage": attendance,
    "study_hours": study_hours,
    "mathematics_marks": mathematics,
    "programming_marks": programming,
    "database_marks": database,
    "internal_marks": internal,
}
estimate = estimate_final_marks(outcome, what_if_values)
stored_final = student.get(PREDICTION_TARGET)

metric_left, metric_mid, metric_right = st.columns(3)
with metric_left:
    st.metric(
        "Estimated final marks",
        "—" if estimate is None else f"{estimate:.1f}",
    )
with metric_mid:
    if stored_final is None or pd.isna(stored_final):
        st.metric("Stored final marks", "Not recorded")
    else:
        st.metric("Stored final marks", f"{float(stored_final):.1f}")
with metric_right:
    baseline = getattr(outcome, "baseline_value", None)
    st.metric(
        "Baseline estimate",
        "—" if baseline is None else f"{float(baseline):.1f}",
    )
st.caption(
    "Estimated final marks use the trained linear model and the what-if inputs above. "
    "Stored final marks stay as they are in the database."
)
