"""Shared Streamlit layout. Calculations stay in the other modules."""

from __future__ import annotations

import html
import math
from contextlib import contextmanager

import pandas as pd
import streamlit as st

from modules.analytics import apply_filters
from modules.config import (
    ATTENDANCE_REVIEW_PERCENT,
    DISPLAY_NAMES,
    OVERALL_REVIEW_PERCENT,
    PASS_PERCENT,
)
from modules.data_cleaning import is_blank

TABLE_COLUMNS = (
    "student_id",
    "student_name",
    "semester",
    "department",
    "attendance_percentage",
    "study_hours",
    "mathematics_marks",
    "programming_marks",
    "database_marks",
    "internal_marks",
    "final_marks",
    "subject_percentage",
    "grade",
    "result_status",
    "class_rank",
)

NUMERIC_COLUMNS = {
    "attendance_percentage",
    "study_hours",
    "mathematics_marks",
    "programming_marks",
    "database_marks",
    "internal_marks",
    "final_marks",
    "subject_percentage",
    "subject_total",
    "subject_maximum",
    "overall_average",
    "average",
    "highest",
    "lowest",
    "average_percent",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Source Sans 3", sans-serif;
        }
        html, body { max-width: 100%; overflow: hidden; }
        .stApp {
            background: #F3F6FA;
            overflow: hidden;
        }
        [data-testid="stAppViewContainer"] {
            max-width: 100vw;
            overflow: hidden;
        }
        [data-testid="stMain"] {
            min-width: 0 !important;
            max-width: 100%;
            height: 100vh;
            overflow-x: auto !important;
            overflow-y: auto !important;
        }
        [data-testid="stMainBlockContainer"],
        .block-container,
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="element-container"] {
            min-width: 0 !important;
            max-width: 100%;
        }
        .block-container {
            max-width: min(1180px, 100%);
            width: 100%;
            box-sizing: border-box;
            padding-top: 4.75rem !important;
            padding-bottom: 3rem;
            padding-left: 1.4rem;
            padding-right: 1.4rem;
        }
        .js-plotly-plot, .plotly, .plot-container, .svg-container {
            max-width: 100% !important;
        }
        [data-testid="stColumn"] { min-width: 0 !important; }
        .sap-grid, .sap-hero, .sap-note, .sap-rule { max-width: 100%; }
        header[data-testid="stHeader"] {
            background: #F3F6FA !important;
            border-bottom: 1px solid #D5DEE8;
            box-shadow: none;
            z-index: 100;
        }
        .stDeployButton, [data-testid="stAppDeployButton"] { display: none !important; }
        footer { display: none !important; }

        .stApp[data-test-script-state="running"]::before,
        .stApp[data-test-script-state="rerunRequested"]::before {
            content: "Loading";
            position: fixed;
            inset: 0;
            z-index: 100000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding-top: 3.4rem;
            background: #F3F6FA;
            color: #16324F;
            font-size: 1rem;
            font-weight: 700;
        }
        .stApp[data-test-script-state="running"]::after,
        .stApp[data-test-script-state="rerunRequested"]::after {
            content: "";
            position: fixed;
            top: calc(50% - 1.8rem);
            left: calc(50% - 0.9rem);
            z-index: 100001;
            width: 1.8rem;
            height: 1.8rem;
            border: 3px solid #D5DEE8;
            border-top-color: #16324F;
            border-radius: 50%;
            animation: sap-spin 0.7s linear infinite;
        }
        @keyframes sap-spin { to { transform: rotate(360deg); } }

        div[data-testid="stSpinner"] {
            background: #ffffff;
            border: 1px solid #D5DEE8;
            border-radius: 16px;
            padding: 0.9rem 1.1rem;
            box-shadow: 0 10px 28px rgba(20, 33, 43, 0.06);
        }

        section[data-testid="stSidebar"] {
            background: #F8FBFD;
            border-right: 1px solid #C5D0DC;
            box-shadow: inset -1px 0 0 #C5D0DC;
        }
        [data-testid="stSidebarUserContent"] {
            padding-bottom: 0.75rem !important;
        }
        section[data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarNav"] {
            scrollbar-width: none;
        }
        section[data-testid="stSidebar"]::-webkit-scrollbar,
        [data-testid="stSidebarContent"]::-webkit-scrollbar,
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar,
        [data-testid="stSidebarNav"]::-webkit-scrollbar {
            width: 0 !important;
            height: 0 !important;
            display: none;
        }
        [data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }
        [data-testid="stSidebarNav"] {
            padding-bottom: 0.7rem;
            margin-bottom: 0.85rem;
            border-bottom: 1px solid #C5D0DC;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 10px;
            margin: 0.12rem 0.45rem;
            padding-top: 0.42rem;
            padding-bottom: 0.42rem;
            transition: background 0.15s ease, color 0.15s ease;
        }
        [data-testid="stSidebarHeader"] {
            height: auto !important;
            min-height: 4.4rem;
            align-items: center;
            padding: 0.85rem 0.45rem 0.35rem 0.95rem;
        }
        [data-testid="stLogoSpacer"] {
            height: auto !important;
            min-height: 2.8rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.12rem;
        }
        [data-testid="stLogoSpacer"]::before {
            content: "Academic Desk";
            color: #16324F;
            font-size: 1.12rem;
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.01em;
        }
        [data-testid="stLogoSpacer"]::after {
            content: "Student performance";
            color: #5C6B78;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1.2;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #16324F !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNav"] a[aria-current="page"] p,
        [data-testid="stSidebarNav"] a[aria-current="page"] div {
            color: #ffffff !important;
        }
        .sap-brand {
            margin: 0.2rem 0.2rem 0.8rem;
            padding: 0.85rem 0.9rem;
            border-radius: 14px;
            background: #16324F;
            color: #F4F7FB;
        }
        .sap-brand span {
            display: block;
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #B7C9D6;
        }
        .sap-brand strong { font-size: 1.02rem; font-weight: 700; }

        .sap-hero {
            background: linear-gradient(135deg, #16324F 0%, #1F4E79 62%, #2E6F8E 100%);
            border-radius: 18px;
            padding: 1.25rem 1.35rem 1.3rem;
            margin: 0.15rem 0 1rem;
            box-shadow: 0 12px 30px rgba(22, 50, 79, 0.16);
            overflow: visible;
        }
        .sap-rule {
            height: 1px;
            margin: 0 0 1rem;
            background: #C5D0DC;
            border: 0;
        }
        .sap-kicker {
            margin: 0;
            color: #C5D7E4;
            font-size: 0.78rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .sap-title {
            margin: 0.2rem 0 0.25rem;
            color: #ffffff;
            font-size: 1.55rem;
            line-height: 1.25;
            font-weight: 700;
        }
        .sap-sub { margin: 0; color: #E4EEF5; font-size: 0.98rem; line-height: 1.45; }

        .sap-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.35rem 0 0.8rem;
        }
        .sap-card {
            background: #ffffff;
            border: 1px solid #E4EBF2;
            border-radius: 16px;
            padding: 0.85rem 0.95rem 0.8rem;
            box-shadow: 0 8px 22px rgba(20, 33, 43, 0.04);
            min-width: 0;
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }
        .sap-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 26px rgba(20, 33, 43, 0.08);
        }
        .sap-card-label {
            margin: 0;
            color: #5C6B78;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .sap-card-value {
            margin: 0.25rem 0 0.15rem;
            color: #14212B;
            font-size: 1.55rem;
            line-height: 1.1;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }
        .sap-card-hint { margin: 0; color: #7B8B98; font-size: 0.75rem; }
        .sap-navy { border-top: 3px solid #16324F; }
        .sap-teal { border-top: 3px solid #1F6F8B; }
        .sap-green { border-top: 3px solid #1E7F4F; }
        .sap-red { border-top: 3px solid #B23A48; }
        .sap-gold { border-top: 3px solid #C47B17; }

        .sap-note, .sap-empty {
            background: #ffffff;
            border: 1px solid #E4EBF2;
            border-radius: 14px;
            padding: 0.75rem 0.95rem;
            color: #3E5160;
            margin: 0.35rem 0 0.9rem;
        }
        .sap-empty-title {
            margin: 0 0 0.25rem;
            color: #16324F;
            font-weight: 700;
        }
        .sap-empty p:last-child { margin: 0; }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #E4EBF2;
            border-radius: 16px;
            padding: 0.7rem 0.85rem;
            box-shadow: 0 8px 22px rgba(20, 33, 43, 0.04);
        }
        div[data-testid="stMetric"] label { color: #5C6B78; }
        div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border: 1px solid #E4EBF2;
            border-radius: 14px;
            overflow: hidden;
            background: #ffffff;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 11px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 16px rgba(22, 50, 79, 0.12);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            background: #ffffff;
            border-color: #D5DEE8 !important;
        }
        div[data-baseweb="select"] > div {
            min-height: 2.7rem;
            align-items: center;
        }
        div[data-baseweb="select"] [class*="singleValue"],
        div[data-baseweb="select"] [class*="placeholder"],
        div[data-baseweb="select"] [class*="valueContainer"] {
            line-height: 1.4 !important;
            overflow: visible !important;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        div[data-baseweb="select"] svg { flex-shrink: 0; }

        @media (max-width: 1100px) {
            .sap-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .sap-title { font-size: 1.35rem; }
        }
        @media (max-width: 820px) {
            .block-container { padding-left: 0.85rem; padding-right: 0.85rem; }
            .sap-grid { grid-template-columns: 1fr; }
            .sap-card-value { font-size: 1.4rem; }
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.75rem !important; }
            [data-testid="stColumn"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def banner(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="sap-hero">
          <p class="sap-kicker">Academic desk</p>
          <p class="sap-title">{html.escape(title)}</p>
          <p class="sap-sub">{html.escape(subtitle)}</p>
        </div>
        <div class="sap-rule"></div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    if "pass_percent" not in st.session_state:
        st.session_state["pass_percent"] = float(PASS_PERCENT)
    if "attendance_threshold" not in st.session_state:
        st.session_state["attendance_threshold"] = float(ATTENDANCE_REVIEW_PERCENT)
    if "overall_threshold" not in st.session_state:
        st.session_state["overall_threshold"] = float(OVERALL_REVIEW_PERCENT)
    with st.sidebar.expander("Grading rules", expanded=False):
        st.number_input(
            "Pass mark (%)",
            min_value=1.0,
            max_value=100.0,
            step=1.0,
            key="pass_percent",
            help="Used for pass/fail and the below-pass review flag. Letter grades stay on the fixed scale.",
        )
        st.number_input(
            "Attendance review below (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="attendance_threshold",
        )
        st.number_input(
            "Subject % review below",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="overall_threshold",
        )
        st.caption("Flags support a review. They are not a judgment of ability.")
    # st.sidebar.caption("Local demo only. Do not load real student records.")


@contextmanager
def loading(message: str):
    """Show a labeled spinner while a slower step runs."""
    with st.spinner(message):
        yield


def open_records(pass_percent: float):
    """Read the database behind the page loader."""
    from modules.service import current_performance

    with loading("Loading student records…"):
        return current_performance(pass_percent=pass_percent)


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="sap-empty">
          <p class="sap-empty-title">{html.escape(title)}</p>
          <p>{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def current_settings() -> dict[str, float]:
    return {
        "pass_percent": float(st.session_state.get("pass_percent", PASS_PERCENT)),
        "attendance_threshold": float(
            st.session_state.get("attendance_threshold", ATTENDANCE_REVIEW_PERCENT)
        ),
        "overall_threshold": float(st.session_state.get("overall_threshold", OVERALL_REVIEW_PERCENT)),
    }


def flash(message: str, level: str = "success") -> None:
    st.session_state["flash"] = {"message": message, "level": level}


def render_flash() -> None:
    item = st.session_state.pop("flash", None)
    if not item:
        return
    renderer = {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}
    renderer.get(item["level"], st.info)(item["message"])


def prepare_page() -> dict[str, float]:
    inject_css()
    render_sidebar()
    render_flash()
    return current_settings()


def format_percent(value: object) -> str:
    if _missing_number(value):
        return "—"
    return f"{float(value):.1f}%"


def format_number(value: object) -> str:
    if _missing_number(value):
        return "—"
    return f"{float(value):.1f}"


def _missing_number(value: object) -> bool:
    if is_blank(value):
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def show_summary(summary: dict) -> None:
    cards = [
        ("Students", f"{summary['total_students']}", "In this view", "sap-navy"),
        ("Average", format_percent(summary["overall_average"]), "Subject percentage", "sap-teal"),
        ("Attendance", format_percent(summary["average_attendance"]), "Mean attendance", "sap-teal"),
        ("Pass rate", format_percent(summary["pass_percentage"]), "Pass and fail only", "sap-green"),
        ("Passed", f"{summary['passed']}", "Met the pass mark", "sap-green"),
        ("Failed", f"{summary['failed']}", "Below the pass mark", "sap-red"),
        ("Highest", format_percent(summary["highest"]), "Best subject %", "sap-gold"),
        ("For review", f"{summary['flagged']}", "At least one rule", "sap-gold"),
    ]
    pieces = []
    for label, value, hint, tone in cards:
        pieces.append(
            "<article class='sap-card "
            + tone
            + "'><p class='sap-card-label'>"
            + html.escape(label)
            + "</p><p class='sap-card-value'>"
            + html.escape(value)
            + "</p><p class='sap-card-hint'>"
            + html.escape(hint)
            + "</p></article>"
        )
    st.markdown("<section class='sap-grid'>" + "".join(pieces) + "</section>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sap-note'>Incomplete records are left out of the pass rate: "
        + html.escape(str(summary["incomplete"]))
        + ". The pass rate uses students with a Pass or Fail result only.</div>",
        unsafe_allow_html=True,
    )


def filter_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Semester, department, and search controls. The returned rows drive the charts."""
    if df is None or df.empty:
        return df
    semesters = ["All", *sorted(df["semester"].dropna().unique().tolist())]
    departments = ["All", *sorted(df["department"].dropna().unique().tolist())]
    if st.session_state.get("filter_semester") not in semesters:
        st.session_state["filter_semester"] = "All"
    if st.session_state.get("filter_department") not in departments:
        st.session_state["filter_department"] = "All"
    if "filter_query" not in st.session_state:
        st.session_state["filter_query"] = ""
    with st.container(border=True):
        first, second, third = st.columns(3)
        with first:
            st.selectbox("Semester", semesters, key="filter_semester")
        with second:
            st.selectbox("Department", departments, key="filter_department")
        with third:
            st.text_input("Search student ID or name", key="filter_query", placeholder="S001 or a name")
    return apply_filters(
        df,
        search=st.session_state["filter_query"],
        semester=st.session_state["filter_semester"],
        department=st.session_state["filter_department"],
    )


def display_table(df: pd.DataFrame, columns: tuple[str, ...] = TABLE_COLUMNS) -> None:
    if df is None or df.empty:
        st.info("No students match the current filters.")
        return
    available = [column for column in columns if column in df.columns]
    show = df.loc[:, available].copy()
    for column in show.columns:
        if column == "class_rank":
            show[column] = show[column].map(lambda value: None if is_blank(value) else int(value))
        elif column in NUMERIC_COLUMNS:
            show[column] = show[column].map(lambda value: None if is_blank(value) else round(float(value), 1))
    show = show.rename(columns=DISPLAY_NAMES)
    st.dataframe(show, width="stretch", hide_index=True)


def show_chart(figure, empty_message: str) -> None:
    with st.container(border=True):
        if figure is None:
            empty_state("Nothing to chart", empty_message)
            return
        st.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": "hover", "responsive": True},
        )
