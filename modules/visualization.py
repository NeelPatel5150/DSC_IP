"""Plotly figures. Each function returns None when the filtered data cannot draw that chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.analytics import correlation_matrix
from modules.config import (
    ATTENDANCE_REVIEW_PERCENT,
    GRADE_COLORS,
    GRADE_MINIMUMS,
    RESULT_COLORS,
)

GRADE_ORDER = [grade for _minimum, grade in GRADE_MINIMUMS]

_LAYOUT = dict(
    template="plotly_white",
    margin=dict(l=48, r=20, t=52, b=48),
    height=360,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, sans-serif", size=13, color="#1C2833"),
    title=dict(font=dict(size=16, color="#16324F"), x=0, xanchor="left"),
)


def _finish(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(automargin=True, showgrid=False)
    fig.update_yaxes(automargin=True, gridcolor="#E6EDF3")
    return fig


def subject_average_chart(summary: pd.DataFrame):
    """Bar chart of average marks as a percentage of each component maximum."""
    if summary is None or summary.empty:
        return None
    chart = summary[summary["students_recorded"] > 0].copy()
    if chart.empty:
        return None
    fig = px.bar(
        chart,
        x="subject",
        y="average_percent",
        text=chart["average_percent"].map(lambda value: f"{value:.1f}%"),
        custom_data=["average", "maximum_marks", "students_recorded"],
        title="Average by component",
        labels={"subject": "Component", "average_percent": "Average (% of maximum)"},
    )
    fig.update_traces(
        hovertemplate=(
            "%{x}<br>Average: %{customdata[0]:.1f} / %{customdata[1]:.0f}"
            "<br>Recorded students: %{customdata[2]}<extra></extra>"
        ),
        marker_color="#1B3A4B",
    )
    fig.update_layout(yaxis_range=[0, 100])
    return _finish(fig)


def grade_donut(df: pd.DataFrame):
    if df is None or df.empty or "grade" not in df.columns:
        return None
    grades = df["grade"].dropna()
    if grades.empty:
        return None
    counts = grades.value_counts().rename_axis("grade").reset_index(name="students")
    counts["label"] = counts["grade"].astype(str) + " · " + counts["students"].astype(str)
    fig = px.pie(
        counts,
        names="label",
        values="students",
        hole=0.58,
        title="Grade distribution",
        color="grade",
        color_discrete_map=GRADE_COLORS,
    )
    fig.update_traces(textinfo="none", hovertemplate="%{label}<extra></extra>")
    fig = _finish(fig)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, xanchor="left"),
        margin=dict(l=24, r=16, t=52, b=88),
        height=400,
    )
    return fig


def percentage_histogram(df: pd.DataFrame):
    if df is None or df.empty or "subject_percentage" not in df.columns:
        return None
    series = df.dropna(subset=["subject_percentage"])
    if series.empty:
        return None
    fig = px.histogram(
        series,
        x="subject_percentage",
        nbins=10,
        title="Distribution of subject percentage",
        labels={"subject_percentage": "Subject percentage"},
    )
    fig.update_traces(marker_color="#1F618D")
    fig.update_layout(yaxis_title="Students")
    return _finish(fig)


def pass_fail_chart(df: pd.DataFrame):
    if df is None or df.empty or "result_status" not in df.columns:
        return None
    counts = (
        df["result_status"]
        .value_counts()
        .reindex(["Pass", "Fail", "Incomplete"])
        .fillna(0)
        .astype(int)
        .rename_axis("result")
        .reset_index(name="students")
    )
    if int(counts["students"].sum()) == 0:
        return None
    fig = px.bar(
        counts,
        x="result",
        y="students",
        color="result",
        title="Result counts",
        color_discrete_map=RESULT_COLORS,
        labels={"result": "Result", "students": "Students"},
    )
    fig.update_layout(showlegend=False)
    return _finish(fig)


def _semester_order(labels: list[str]) -> list[str]:
    def sort_key(label: str) -> tuple[int, str]:
        parts = str(label).split()
        try:
            return (int(parts[-1]), str(label))
        except (ValueError, IndexError):
            return (999, str(label))

    return sorted(labels, key=sort_key)


def semester_pass_rate_chart(df: pd.DataFrame):
    """Pass rate by semester. Incomplete students are left out of the rate."""
    if df is None or df.empty:
        return None
    needed = {"semester", "result_status"}
    if not needed.issubset(df.columns):
        return None
    decided = df[df["result_status"].isin(["Pass", "Fail"])].copy()
    if decided.empty:
        return None
    rows = []
    for semester, group in decided.groupby("semester", dropna=False):
        total = len(group)
        if total == 0:
            continue
        passed = int((group["result_status"] == "Pass").sum())
        rows.append(
            {
                "semester": semester,
                "pass_rate": round(100.0 * passed / total, 1),
                "passed": passed,
                "decided": total,
            }
        )
    if not rows:
        return None
    chart = pd.DataFrame(rows)
    chart["semester"] = pd.Categorical(
        chart["semester"],
        categories=_semester_order(chart["semester"].astype(str).tolist()),
        ordered=True,
    )
    chart = chart.sort_values("semester")
    fig = px.bar(
        chart,
        x="semester",
        y="pass_rate",
        text=chart["pass_rate"].map(lambda value: f"{value:.1f}%"),
        custom_data=["passed", "decided"],
        title="Pass rate by semester",
        labels={"semester": "Semester", "pass_rate": "Pass rate (%)"},
    )
    fig.update_traces(
        marker_color="#1E7F4F",
        hovertemplate=(
            "%{x}<br>Pass rate: %{y:.1f}%"
            "<br>Passed: %{customdata[0]} of %{customdata[1]} decided"
            "<extra></extra>"
        ),
    )
    fig.update_layout(yaxis_range=[0, 100])
    return _finish(fig)


def subject_percentage_box_by_semester(df: pd.DataFrame):
    """Box plot of subject percentage across semesters."""
    if df is None or df.empty:
        return None
    needed = {"semester", "subject_percentage"}
    if not needed.issubset(df.columns):
        return None
    chart = df.dropna(subset=["subject_percentage", "semester"]).copy()
    if chart.empty or chart["semester"].nunique() < 1:
        return None
    order = _semester_order(chart["semester"].astype(str).unique().tolist())
    chart["semester"] = pd.Categorical(chart["semester"], categories=order, ordered=True)
    chart = chart.sort_values("semester")
    fig = px.box(
        chart,
        x="semester",
        y="subject_percentage",
        points="outliers",
        title="Subject percentage by semester",
        labels={"semester": "Semester", "subject_percentage": "Subject percentage"},
    )
    fig.update_traces(marker_color="#1F618D", line_color="#16324F")
    fig.update_layout(yaxis_range=[0, 100])
    return _finish(fig)


def _scatter(df: pd.DataFrame, x_column: str, y_column: str, title: str, x_label: str, y_label: str):
    if df is None or df.empty:
        return None
    needed = [x_column, y_column, "student_id", "student_name"]
    if any(column not in df.columns for column in needed):
        return None
    chart = df.dropna(subset=[x_column, y_column])
    if len(chart) < 2:
        return None
    fig = px.scatter(
        chart,
        x=x_column,
        y=y_column,
        hover_data={"student_id": True, "student_name": True},
        title=title,
        labels={x_column: x_label, y_column: y_label},
    )
    fig.update_traces(marker=dict(size=10, color="#1B3A4B"))
    return _finish(fig)


def attendance_scatter(df: pd.DataFrame):
    return _scatter(
        df,
        "attendance_percentage",
        "subject_percentage",
        "Attendance and subject percentage",
        "Attendance %",
        "Subject percentage",
    )


def study_hours_scatter(df: pd.DataFrame):
    return _scatter(
        df,
        "study_hours",
        "subject_percentage",
        "Study hours and subject percentage",
        "Study hours per day",
        "Subject percentage",
    )


def internal_final_scatter(df: pd.DataFrame):
    return _scatter(
        df,
        "internal_marks",
        "final_marks",
        "Internal marks and final marks",
        "Internal marks (out of 50)",
        "Final marks (out of 100)",
    )


def correlation_heatmap(df: pd.DataFrame):
    columns = [
        ("attendance_percentage", "Attendance %"),
        ("study_hours", "Study hours"),
        ("subject_percentage", "Subject %"),
        ("internal_marks", "Internal"),
        ("final_marks", "Final"),
    ]
    present = [column for column, _label in columns if df is not None and column in df.columns]
    matrix = correlation_matrix(df, present) if df is not None else pd.DataFrame()
    if matrix.empty or matrix.shape[0] < 2:
        return None
    labels = dict(columns)
    renamed = matrix.rename(index=labels, columns=labels)
    fig = px.imshow(
        renamed,
        text_auto=".2f",
        color_continuous_scale="Blues",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title="Correlation heatmap",
        labels=dict(color="Pearson r"),
    )
    return _finish(fig)


def reason_chart(counts: pd.DataFrame):
    if counts is None or counts.empty:
        return None
    fig = px.bar(
        counts,
        x="students",
        y="reason",
        orientation="h",
        title="Students matched by each review rule",
        labels={"students": "Students", "reason": "Rule"},
    )
    fig.update_traces(marker_color="#B9770E")
    fig = _finish(fig)
    fig.update_layout(height=max(320, 52 * len(counts) + 90))
    return fig


def _attendance_band_order(threshold: float) -> list[str]:
    low_cut = float(threshold)
    mid_cut = 85.0
    return [
        f"Below {low_cut:.0f}%",
        f"{low_cut:.0f}% to under {mid_cut:.0f}%",
        f"{mid_cut:.0f}% and above",
    ]


def _attendance_band_label(value: float, threshold: float) -> str:
    low_cut = float(threshold)
    mid_cut = 85.0
    number = float(value)
    if number < low_cut:
        return f"Below {low_cut:.0f}%"
    if number < mid_cut:
        return f"{low_cut:.0f}% to under {mid_cut:.0f}%"
    return f"{mid_cut:.0f}% and above"


def attendance_bands_chart(df: pd.DataFrame, threshold: float = ATTENDANCE_REVIEW_PERCENT):
    """Pie chart of attendance bands: below review threshold, mid, and high."""
    if df is None or df.empty or "attendance_percentage" not in df.columns:
        return None
    series = df["attendance_percentage"].dropna()
    if series.empty:
        return None
    bands = [_attendance_band_label(value, threshold) for value in series]
    counts = (
        pd.Series(bands)
        .value_counts()
        .rename_axis("band")
        .reset_index(name="students")
    )
    order = _attendance_band_order(threshold)
    counts["band"] = pd.Categorical(counts["band"], categories=order, ordered=True)
    counts = counts.sort_values("band")
    counts["label"] = counts["band"].astype(str) + " · " + counts["students"].astype(str)
    colors = {
        order[0]: "#B23A48",
        order[1]: "#C47B17",
        order[2]: "#1E7F4F",
    }
    fig = px.pie(
        counts,
        names="label",
        values="students",
        color="band",
        color_discrete_map=colors,
        hole=0.45,
        title="Attendance bands",
    )
    fig.update_traces(textinfo="none", hovertemplate="%{label}<extra></extra>")
    fig = _finish(fig)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, xanchor="left"),
        margin=dict(l=24, r=16, t=52, b=88),
        height=400,
    )
    return fig


def subject_percentage_by_attendance_band_chart(
    df: pd.DataFrame,
    threshold: float = ATTENDANCE_REVIEW_PERCENT,
):
    """Bar chart of mean subject percentage inside each attendance band."""
    if df is None or df.empty:
        return None
    needed = {"attendance_percentage", "subject_percentage"}
    if not needed.issubset(df.columns):
        return None
    chart = df.dropna(subset=["attendance_percentage", "subject_percentage"]).copy()
    if chart.empty:
        return None
    chart["band"] = chart["attendance_percentage"].map(
        lambda value: _attendance_band_label(value, threshold)
    )
    order = _attendance_band_order(threshold)
    summary = (
        chart.groupby("band", observed=False)
        .agg(average_subject_percent=("subject_percentage", "mean"), students=("subject_percentage", "size"))
        .reset_index()
    )
    summary["band"] = pd.Categorical(summary["band"], categories=order, ordered=True)
    summary = summary.sort_values("band")
    if summary.empty:
        return None
    colors = {
        order[0]: "#B23A48",
        order[1]: "#C47B17",
        order[2]: "#1E7F4F",
    }
    fig = px.bar(
        summary,
        x="band",
        y="average_subject_percent",
        text=summary["average_subject_percent"].map(lambda value: f"{value:.1f}%"),
        custom_data=["students"],
        color="band",
        color_discrete_map=colors,
        title="Average subject % by attendance band",
        labels={"band": "Attendance band", "average_subject_percent": "Average subject %"},
    )
    fig.update_traces(
        hovertemplate=(
            "%{x}<br>Average subject %: %{y:.1f}"
            "<br>Students: %{customdata[0]}<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, 100])
    return _finish(fig)


def department_semester_result_sunburst(df: pd.DataFrame):
    """Sunburst: Department → Semester → Pass/Fail/Incomplete."""
    if df is None or df.empty:
        return None
    needed = {"department", "semester", "result_status"}
    if not needed.issubset(df.columns):
        return None
    chart = df.dropna(subset=["department", "semester", "result_status"]).copy()
    if chart.empty:
        return None
    counts = (
        chart.groupby(["department", "semester", "result_status"], dropna=False)
        .size()
        .reset_index(name="students")
    )
    if counts.empty or int(counts["students"].sum()) == 0:
        return None
    fig = px.sunburst(
        counts,
        path=["department", "semester", "result_status"],
        values="students",
        color="result_status",
        color_discrete_map=RESULT_COLORS,
        title="Department → semester → result",
    )
    fig.update_traces(
        hovertemplate="%{label}<br>Students: %{value}<extra></extra>",
    )
    fig = _finish(fig)
    fig.update_layout(height=460, margin=dict(l=20, r=20, t=52, b=20))
    return fig


def grades_by_semester_stacked(df: pd.DataFrame):
    """Stacked bar of letter grades within each semester."""
    if df is None or df.empty:
        return None
    needed = {"semester", "grade"}
    if not needed.issubset(df.columns):
        return None
    chart = df.dropna(subset=["semester", "grade"]).copy()
    if chart.empty:
        return None
    counts = (
        chart.groupby(["semester", "grade"], dropna=False)
        .size()
        .reset_index(name="students")
    )
    order = _semester_order(counts["semester"].astype(str).unique().tolist())
    counts["semester"] = pd.Categorical(counts["semester"], categories=order, ordered=True)
    present_grades = [grade for grade in GRADE_ORDER if grade in set(counts["grade"])]
    if not present_grades:
        present_grades = sorted(counts["grade"].astype(str).unique().tolist())
    counts["grade"] = pd.Categorical(counts["grade"], categories=present_grades, ordered=True)
    counts = counts.sort_values(["semester", "grade"])
    fig = px.bar(
        counts,
        x="semester",
        y="students",
        color="grade",
        barmode="stack",
        title="Grades by semester",
        color_discrete_map=GRADE_COLORS,
        labels={"semester": "Semester", "students": "Students", "grade": "Grade"},
        category_orders={"grade": present_grades, "semester": order},
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return _finish(fig)


def prediction_actual_vs_estimated_scatter(comparison: pd.DataFrame):
    """Scatter of actual vs estimated final marks on the test set."""
    if comparison is None or comparison.empty:
        return None
    needed = {"actual_final_marks", "estimated_final_marks"}
    if not needed.issubset(comparison.columns):
        return None
    chart = comparison.dropna(subset=["actual_final_marks", "estimated_final_marks"]).copy()
    if chart.empty:
        return None
    hover = [column for column in ("student_id", "student_name") if column in chart.columns]
    fig = px.scatter(
        chart,
        x="actual_final_marks",
        y="estimated_final_marks",
        hover_data=hover or None,
        title="Actual vs estimated final marks",
        labels={
            "actual_final_marks": "Actual final marks",
            "estimated_final_marks": "Estimated final marks",
        },
    )
    fig.update_traces(marker=dict(size=10, color="#1B3A4B"))
    low = float(min(chart["actual_final_marks"].min(), chart["estimated_final_marks"].min()))
    high = float(max(chart["actual_final_marks"].max(), chart["estimated_final_marks"].max()))
    pad = max(2.0, (high - low) * 0.05)
    low -= pad
    high += pad
    fig.add_shape(
        type="line",
        x0=low,
        y0=low,
        x1=high,
        y1=high,
        line=dict(color="#B23A48", width=2, dash="dash"),
    )
    fig.update_layout(xaxis_range=[low, high], yaxis_range=[low, high])
    return _finish(fig)


def prediction_residual_histogram(comparison: pd.DataFrame):
    """Histogram of estimated − actual residuals on the test set."""
    if comparison is None or comparison.empty:
        return None
    needed = {"actual_final_marks", "estimated_final_marks"}
    if not needed.issubset(comparison.columns):
        return None
    chart = comparison.dropna(subset=["actual_final_marks", "estimated_final_marks"]).copy()
    if chart.empty:
        return None
    chart["residual"] = chart["estimated_final_marks"].astype(float) - chart[
        "actual_final_marks"
    ].astype(float)
    fig = px.histogram(
        chart,
        x="residual",
        nbins=min(12, max(5, len(chart))),
        title="Residuals (estimated − actual)",
        labels={"residual": "Residual marks"},
    )
    fig.update_traces(marker_color="#1F618D")
    fig.update_layout(yaxis_title="Test students")
    fig.add_vline(x=0, line_dash="dash", line_color="#B23A48")
    return _finish(fig)


def top_bottom_subject_percentage_chart(df: pd.DataFrame, limit: int = 10):
    """Horizontal bars for the highest and lowest subject percentages."""
    if df is None or df.empty or "subject_percentage" not in df.columns:
        return None
    needed = {"student_id", "student_name", "subject_percentage"}
    if not needed.issubset(df.columns):
        return None
    ranked = df.dropna(subset=["subject_percentage"]).copy()
    if ranked.empty:
        return None
    take = min(limit, len(ranked))
    top = ranked.nlargest(take, "subject_percentage").assign(group="Top")
    bottom = ranked.nsmallest(take, "subject_percentage").assign(group="Bottom")
    chart = pd.concat([top, bottom], ignore_index=True)
    chart["label"] = (
        chart["student_name"].astype(str) + " (" + chart["student_id"].astype(str) + ")"
    )
    # Keep Top block above Bottom, each sorted by percentage.
    chart["group"] = pd.Categorical(chart["group"], categories=["Top", "Bottom"], ordered=True)
    chart = chart.sort_values(["group", "subject_percentage"], ascending=[True, True])
    fig = px.bar(
        chart,
        x="subject_percentage",
        y="label",
        color="group",
        orientation="h",
        title=f"Top and bottom {take} by subject percentage",
        labels={
            "subject_percentage": "Subject percentage",
            "label": "Student",
            "group": "Group",
        },
        color_discrete_map={"Top": "#1E7F4F", "Bottom": "#B23A48"},
    )
    fig.update_traces(
        hovertemplate="%{y}<br>Subject %: %{x:.1f}<extra></extra>",
    )
    fig = _finish(fig)
    fig.update_layout(
        height=max(380, 28 * len(chart) + 120),
        xaxis_range=[0, 100],
        yaxis=dict(categoryorder="array", categoryarray=chart["label"].tolist()),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=16, r=20, t=72, b=48),
    )
    return fig


def student_comparison_chart(df: pd.DataFrame, student_ids: list[str]):
    """Grouped bars for the three subject papers. Missing marks are left blank."""
    if df is None or df.empty or not student_ids:
        return None
    selected = df[df["student_id"].isin(student_ids)].copy()
    if selected.empty:
        return None
    long_rows = []
    subjects = (
        ("mathematics_marks", "Mathematics"),
        ("programming_marks", "Programming"),
        ("database_marks", "Database"),
    )
    for record in selected.to_dict(orient="records"):
        for column, label in subjects:
            value = record.get(column)
            long_rows.append(
                {
                    "student": f"{record['student_name']} ({record['student_id']})",
                    "subject": label,
                    "marks": None if pd.isna(value) else float(value),
                }
            )
    chart = pd.DataFrame(long_rows)
    fig = px.bar(
        chart,
        x="student",
        y="marks",
        color="subject",
        barmode="group",
        title="Subject marks for the selected students",
        labels={"student": "Student", "marks": "Marks out of 100", "subject": "Subject"},
    )
    fig.update_layout(yaxis_range=[0, 100])
    return _finish(fig)
