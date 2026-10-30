"""Project background, demonstration rules, and limits. No live statistics are hardcoded here."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from modules.config import GRADE_MINIMUMS, PASS_PERCENT
from modules.ui import banner, prepare_page

prepare_page()
banner(
    "About This Project",
    "Semester 7 Data Science individual project. The application is a local demonstration.",
)

st.subheader("What it does")
st.write(
    "The app stores fictional or user-supplied academic records, checks them, and calculates "
    "averages, letter grades, pass rates, attendance relationships, individual reports, and review flags. "
    "An optional linear regression estimates final marks and is compared with a mean baseline."
)

st.subheader("Demonstration grading scale")
st.write(
    "No official college regulation is included. Letter grades use the fixed scale below. "
    f"The default pass mark is {PASS_PERCENT:.0f}% of a component's maximum. "
    "The sidebar can change the pass mark. Doing that changes pass/fail and the below-pass flag. "
    "It does not move the letter-grade boundaries."
)
bands = []
previous = None
for minimum, grade in GRADE_MINIMUMS:
    if previous is None:
        label = f"{minimum:.0f} and above"
    else:
        label = f"{minimum:.0f} up to, but not including, {previous:.0f}"
    bands.append({"Subject percentage": label, "Grade": grade})
    previous = minimum
st.dataframe(pd.DataFrame(bands), width="stretch", hide_index=True)
st.write(
    "Subject percentage uses Mathematics, Programming, and Database only, and only the papers that were recorded. "
    "A missing paper is skipped. It is not scored as zero. Internal marks are out of 50 and count toward pass/fail. "
    "Final marks are kept for the report and the optional model. They do not change the pass/fail status. "
    "A student with no recorded subject mark and no internal mark is Incomplete, not Fail."
)

st.subheader("Review flags")
st.write(
    "A student is listed as needing academic review when attendance is below the sidebar threshold, "
    "a recorded subject or internal mark is below the pass mark, the subject percentage is below the sidebar threshold, "
    "or an examination result is missing. The page states the reason. "
    "The flag means the student may benefit from additional support. It is not a judgment of ability."
)

st.subheader("Data and storage")
st.write(
    "The bundled CSV in data/sample_students.csv is synthetic. The names and marks were generated for this project. "
    "They are not real college results. SQLite stores students, one academic row, and one row per mark component "
    "in database/app.db. That file is created on first use and is not meant to be committed when it holds records. "
    "To reset it during development, stop the app, delete database/app.db, and start again, "
    "or use the confirmed reset on the Upload Dataset page."
)

st.subheader("Safety")
st.warning(
    "This demonstration has no login. Do not expose it on a public network and do not load real student records. "
    "Uploads are limited to CSV and Excel files of 5 MB. Database writes use parameterized queries."
)

st.subheader("What the model does not do")
st.write(
    "The prediction page estimates final marks from the other fields. It splits labeled rows into training and test sets, "
    "learns medians on the training split only, and reports MAE and RMSE against a baseline that always predicts "
    "the training average. Estimates are not written into the mark table and are not guaranteed outcomes. "
    "A correlation on the attendance page does not show that attendance or study hours cause higher marks."
)

st.subheader("Questions a reviewer may ask")
st.write(
    "Why keep a blank mark different from zero? Because zero is a real score and a blank means the result was not recorded."
)
st.write(
    "Why is the pass percentage not based on every student? Incomplete students have no recorded subject or internal mark, "
    "so counting them as failures would invent a result."
)
st.write(
    "Why compare the model with the average? A model that cannot beat 'predict the training average' is not useful on this split."
)
