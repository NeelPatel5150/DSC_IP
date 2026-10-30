"""Plotly figures. Each function returns None when the filtered data cannot draw that chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.analytics import correlation_matrix
from modules.config import GRADE_COLORS, RESULT_COLORS

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
