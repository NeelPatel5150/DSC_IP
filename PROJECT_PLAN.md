# Student Academic Performance Analysis

**Semester 7 Data Science (DSC) — Individual Academic Project**

Planning document only. This file defines the architecture, dataset schema, database schema, development phases, and installation requirements. Source code, the Streamlit application, and the sample dataset are later phases.

---

## 1. Project Overview

A local web application that turns fictional student academic records into calculated insights: averages, grades, pass rates, subject comparisons, attendance and study-habit relationships, individual reports, and rule-based academic-review flags. An optional machine-learning module estimates final marks only after the core analytics work.

The application is for college demonstration, project evaluation, and viva. It is a working system with real calculations, validation, and SQLite storage. It is a demonstration and must not be exposed publicly with real student records. Login is not part of this project.

| Role | Responsibility in this project |
| --- | --- |
| Data science | Cleaning, statistics, grading, risk rules, optional prediction |
| Full-stack | Streamlit UI, Plotly charts, SQLite persistence |
| Documentation | README, schema notes, tests, viva preparation |

**Synthetic data only.** Sample records are invented. They are not real college results. Machine-learning scores on this data are demonstrations and may not generalize to real students.

---

## 2. Problem Statement

Colleges collect marks, attendance, and study information in spreadsheets. Those files are hard to compare across subjects, easy to mis-grade when records are incomplete, and weak at showing which students may need support. This project builds one local tool that validates the data, stores it, calculates performance with documented rules, and presents the results for academic decision support.

## 3. Motivation

- Practice an end-to-end data-science workflow: ingest, validate, clean, analyze, visualize, persist, and optionally model.
- Show how calculated indicators can support teaching decisions without claiming they judge a student's ability.
- Produce a project that can be installed on Windows with Visual Studio Code and demonstrated offline.

## 4. Objectives

1. Analyze student academic performance from stored or uploaded records.
2. Calculate average marks, percentages, grades, and pass rates.
3. Compare performance across subjects.
4. Examine relationships between attendance, study hours, and marks.
5. Identify students who may benefit from additional academic support.
6. Display results on an interactive dashboard.
7. Search, filter, and inspect student records.
8. Generate an individual student performance report.
9. Optionally predict academic outcomes with scikit-learn after the core analytics exist.
10. Show how data science can support educational decision-making.

## 5. Scope

### In scope

- Streamlit application with sidebar navigation.
- Pandas and NumPy analysis of a defined student schema.
- Plotly charts that respond to filters.
- CSV upload, Excel upload where practical, validation, and a sample CSV template.
- Reusable cleaning module with documented assumptions.
- Configurable grade and pass rules, with a documented demonstration default.
- SQLite persistence using Python `sqlite3` and parameterized queries.
- Add, edit, view, search, filter, and confirmed delete of students.
- Individual report export as CSV, and PDF where practical.
- Rule-based academic-review flags with stated reasons.
- Optional regression module with train/test split, baseline comparison, MAE, and RMSE.
- Automated tests for calculations, grading, and validation.
- README suitable for setup, evaluation, and viva.

### Out of scope

- User login, roles, or public deployment.
- Real student data, institutional grade-book integration, or paid services.
- Claiming that attendance or study hours cause higher marks.
- Treating missing marks as zero.
- Fabricated accuracy scores, screenshots, or experimental findings.
- Hardcoded dashboard statistics.

---

## 6. Technology Stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python 3 | Modular, readable modules |
| UI | Streamlit | `streamlit run app.py` |
| Charts | Plotly | Interactive charts; custom CSS only where it improves the layout |
| Analysis | Pandas, NumPy | Load, clean, aggregate, correlate |
| Database | SQLite via `sqlite3` | Local file under `database/`; parameterized SQL |
| Machine learning | scikit-learn | Optional; Linear Regression or Random Forest Regressor |
| Tests | pytest | Core logic, not the whole UI |
| Editor | Visual Studio Code | Recommended |
| Environment | `venv` | Dependency isolation |
| Version control | Git | If available; do not commit real records or populated sensitive databases |

No extra web framework, cloud host, or paid API.

### Exact installation requirements

Python 3.10 or newer is the target. Packages and minimum versions:

| Package | Minimum version | Used for |
| --- | --- | --- |
| streamlit | 1.32.0 | Application and pages |
| pandas | 2.2.0 | Tables and analysis |
| numpy | 1.26.0 | Numeric operations |
| plotly | 5.18.0 | Charts |
| openpyxl | 3.1.2 | Excel upload |
| scikit-learn | 1.4.0 | Optional prediction |
| pytest | 8.0.0 | Automated tests |

PDF export, if implemented, adds `fpdf2` at `2.7.0` or newer. If PDF proves awkward on Windows, CSV export remains the required download and PDF is documented as optional.

`requirements.txt` will list these with pinned versions once the environment is created and imports are verified. Versions above are the planning baseline, not measured install results.

---

## 7. Proposed Architecture

Single-process local app. The Streamlit entry point and pages call pure Python modules. Pages do not embed grading or validation formulas.

```text
student-academic-performance/
    app.py                          # Home dashboard and shared sidebar
    requirements.txt
    README.md
    .gitignore
    PROJECT_PLAN.md                 # This document

    pages/
        1_Student_Management.py
        2_Upload_Dataset.py
        3_Academic_Analysis.py
        4_Attendance_Analysis.py
        5_Student_Reports.py
        6_Risk_Identification.py
        7_Prediction.py
        8_About_Project.py

    modules/
        data_loader.py              # CSV, Excel, sample template
        data_cleaning.py            # Normalize, types, missing, duplicates
        validation.py               # Column, range, and row checks
        grading.py                  # Thresholds, grade, pass/fail
        analytics.py                # Averages, rates, rankings, correlations
        visualization.py            # Plotly figure builders
        reporting.py                # One-student report and export
        risk.py                     # Academic-review rules
        database.py                 # Schema init and CRUD
        prediction.py               # Optional model train and evaluate

    database/
        .gitkeep                    # app.db created at runtime, gitignored

    data/
        sample_students.csv         # Synthetic, labeled as fictional

    tests/
        test_analytics.py
        test_validation.py
        test_grading.py
        test_risk.py
```

The folder may live at the repository root (`d:\Codebase\SEM-7_AML_IP`) rather than inside an extra nested directory if that keeps imports simpler. Module names, dataset columns, and SQL columns must stay identical.

### Navigation

1. Dashboard (`app.py`)
2. Student Management
3. Upload Dataset
4. Academic Analysis
5. Attendance Analysis
6. Individual Reports
7. Risk Identification
8. Prediction (optional; disabled with an explanation if data is unsuitable)
9. About Project

### Data flow

```text
CSV / Excel upload  -->  preview  -->  validation report
                                      |
                         user removes or corrects invalid rows
                                      |
                         cleaning (no silent fill of marks with 0)
                                      |
                    SQLite: students, academic_records, subject_marks
                                      |
        dashboard | analysis | attendance | report | risk | prediction
                                      |
                         Plotly charts and downloadable report
```

Sample CSV can be loaded once on first run so the dashboard is demonstrable. Re-import of the same student ID updates only when the user confirms; it does not create a second student.

### UI principles

- Clean educational dashboard: sidebar, summary cards, filterable tables, consistent grade colors.
- Empty state when the database has no students. No fake totals.
- Success, warning, and error messages in plain language.
- Spinner for import, training, and report generation.
- Accessible chart titles, axis labels, legends, and hover text.
- Charts follow the active class, semester, and department filters.
- User-supplied names are shown as text, not executed as HTML or SQL.

---

## 8. Dataset Schema

### Sample file

`data/sample_students.csv` — synthetic, about 80 to 120 rows, mixed performance, clearly commented in the README as fictional.

Wide format is the upload format because it matches a typical college spreadsheet. The database stores subjects in long form.

| Column | Type | Rule |
| --- | --- | --- |
| student_id | string | Required, unique, pattern such as `S001` |
| student_name | string | Required, 2–80 characters |
| semester | string | Required category, for example `Semester 5` |
| department | string | Required category, for example `Computer Science` |
| attendance_percentage | float | Required, 0 to 100 inclusive |
| study_hours | float | Required, 0 to 16 inclusive (hours per day) |
| mathematics_marks | float | 0 to 100, or empty if the exam was not recorded |
| programming_marks | float | 0 to 100, or empty |
| database_marks | float | 0 to 100, or empty |
| internal_marks | float | 0 to 50, or empty |
| final_marks | float | 0 to 100, or empty |

Subject maximums used in percentage calculations:

| Subject column | Maximum | Examination type |
| --- | --- | --- |
| mathematics_marks | 100 | External subject |
| programming_marks | 100 | External subject |
| database_marks | 100 | External subject |
| internal_marks | 50 | Internal assessment |
| final_marks | 100 | Overall final examination |

`final_marks` is the prediction target when the optional model is trained. It is not an input feature. Subject marks and internal marks may be used as features only when the task is to estimate `final_marks` and those columns are not the same as the target.

Empty mark cells mean "result not recorded." A stored `0` means a genuine zero. Cleaning must not fill blanks with zero.

### Derived fields (calculated, never stored as user input)

| Field | Rule |
| --- | --- |
| subjects_attempted | Count of non-missing subject marks among the three subjects |
| subject_total | Sum of available subject marks |
| subject_maximum | 100 × subjects_attempted |
| subject_percentage | `subject_total / subject_maximum × 100` when at least one subject exists |
| overall_average | Mean of available values among the three subject marks |
| grade | From subject percentage using the table below |
| pass_fail | Pass when every recorded subject is ≥ pass mark and attendance is considered separately for risk, not as an automatic fail, unless the configured rule says otherwise |
| class_rank | Rank by subject percentage within the same semester and department, only among students with the same set of recorded subjects |

Students with different sets of recorded subjects are not forced into one ranking. The UI states the comparison group.

---

## 9. Grading and Risk Rules (Demonstration Defaults)

Official college rules are not assumed. These defaults are configurable in the app and documented in the About page.

### Grade from subject percentage

| Percentage | Grade |
| --- | --- |
| 90–100 | O |
| 80–89.99 | A+ |
| 70–79.99 | A |
| 60–69.99 | B+ |
| 50–59.99 | B |
| 40–49.99 | C |
| Below 40 | F |

### Pass rule

- Subject pass mark: **40 out of 100**.
- Internal pass mark: **20 out of 50** (same 40 percent idea).
- A student **passes** when every recorded subject and internal mark is at or above its pass mark.
- A student with any recorded component below its pass mark is **Fail**.
- A student with no recorded marks is **Incomplete**, not Fail and not Pass.
- Pass percentage = passed students / students with at least one recorded mark × 100.
- Incomplete students are excluded from the pass percentage and listed separately.

### Academic review flags

Wording: "Needs academic review" or "May benefit from additional support." These are decision-support indicators, not judgments of ability.

| Flag | Default rule |
| --- | --- |
| Low attendance | Attendance below **75%** |
| Below pass mark | Any recorded subject below 40, or internal below 20 |
| Low overall performance | Subject percentage below **50** when it can be calculated |
| Missing examination result | One or more subject mark cells empty |

Each flag stores a short reason. A student may have several reasons. The dashboard count is the number of distinct students with at least one flag.

---

## 10. Database Schema

SQLite file: `database/app.db` (created on startup, listed in `.gitignore`).

Foreign keys are enabled with `PRAGMA foreign_keys = ON` on every connection.

### `students`

| Column | Type | Constraint |
| --- | --- | --- |
| student_id | TEXT | PRIMARY KEY |
| student_name | TEXT | NOT NULL |
| semester | TEXT | NOT NULL |
| department | TEXT | NOT NULL |
| created_at | TEXT | NOT NULL, ISO-8601 UTC |

### `academic_records`

| Column | Type | Constraint |
| --- | --- | --- |
| record_id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| student_id | TEXT | NOT NULL, UNIQUE, FOREIGN KEY → students(student_id) ON DELETE CASCADE |
| attendance_percentage | REAL | NOT NULL, CHECK between 0 and 100 |
| study_hours | REAL | NOT NULL, CHECK between 0 and 16 |
| academic_term | TEXT | NOT NULL, same value as semester for this project |

One current academic row per student keeps the demo schema small. History of multiple terms is a future enhancement.

### `subject_marks`

| Column | Type | Constraint |
| --- | --- | --- |
| mark_id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| student_id | TEXT | NOT NULL, FOREIGN KEY → students(student_id) ON DELETE CASCADE |
| subject_name | TEXT | NOT NULL |
| marks_obtained | REAL | NULL allowed (missing result) |
| maximum_marks | REAL | NOT NULL |
| examination_type | TEXT | NOT NULL (`subject`, `internal`, or `final`) |
| | | UNIQUE(student_id, subject_name, examination_type) |

`final_marks` is stored here with `subject_name = 'Final'` and `examination_type = 'final'` so it stays out of the three-subject average.

### Operations

- `init_db()` creates tables if missing.
- Insert, update, select, and delete use `?` parameters only.
- Delete asks for confirmation in the UI, then deletes the student; child rows cascade.
- Development reset: delete `database/app.db` and restart, or use a "Reload sample data" action that replaces rows only after confirmation.

---

## 11. Module Behavior

### Module 1 — Home Dashboard

Summary cards, each computed from the current database:

- Total students
- Overall average of subject percentages (students who have one)
- Average attendance
- Pass percentage
- Passed count
- Failed count
- Highest subject percentage
- Students flagged for academic review

Empty database: short explanation and a button path to load the sample CSV. No zeros presented as real performance.

### Module 2 — Student Management

- Searchable table of all students.
- Search by student ID or name.
- Filter by semester and department.
- Add, edit, and view one profile.
- Delete only after an explicit confirmation control.
- Forms validate the same rules as CSV import.

### Module 3 — Data Import and Validation

- Accept `.csv`, and `.xlsx` when `openpyxl` is installed.
- Reject other types and files larger than **5 MB**.
- Preview the first rows.
- Check required columns, dtypes, ranges, duplicate IDs in the file, duplicate IDs already in the database, and missing marks (reported, not auto-filled).
- Show valid row count, invalid row count, and row-level messages.
- User can drop invalid rows and import the rest, or cancel.
- Import of an existing ID is blocked unless the user chooses "Update existing records."
- Download `sample_students.csv` as the template.

### Module 4 — Data Cleaning

Reusable functions, assumptions written in docstrings and the README:

- Strip and lowercase column names, then map aliases (`Student ID` → `student_id`).
- Strip text fields.
- Convert numeric columns with errors as missing, then validation reports them.
- Do not coerce missing marks to 0.
- Collapse extra spaces in semester and department labels.
- Keep unknown extra columns out of the database and list them as ignored.

### Module 5 — Academic Performance Analysis

- Per-student average, total, maximum, percentage, grade, pass/fail.
- Subject-wise mean, min, and max using only non-missing marks.
- Grade distribution and pass/fail counts.
- Subject comparison bar chart.
- Ranking inside a comparable group, with the group described on screen.

### Module 6 — Attendance and Study Habits

- Scatter: attendance vs subject percentage.
- Scatter: study hours vs subject percentage.
- Scatter or bar: internal marks vs final marks when both exist.
- Correlation matrix for the numeric columns that are present.
- Pearson correlation with a one-sentence caution: correlation is not causation.
- If a column is absent, that chart is replaced by a message naming the missing field.

### Module 7 — Interactive Visualization

Plotly figures from `modules/visualization.py`:

- Subject-wise average bar chart
- Grade donut chart
- Subject-percentage histogram
- Attendance vs marks scatter
- Study hours vs marks scatter
- Selected students' subject comparison
- Pass / fail / incomplete bar chart
- Correlation heatmap when at least three numeric columns have data

Each figure has a title, axis labels, and hover fields. Filters change the dataframe before the figure is built.

### Module 8 — Individual Student Report

Select one student. Show ID, name, semester, department, each subject mark against the class average for that subject, total and percentage when calculable, grade, pass/fail/incomplete, attendance, study hours, stronger subjects (at or above class average), subjects below class average, and support suggestions tied to the risk rules.

Export CSV of that student's rows. PDF when `fpdf2` imports successfully. The report does not list other students' names or marks; class averages are aggregates only.

Suggestions are rule text, for example: "Attendance is below 75%. Additional support with class attendance may help." They are not personal diagnoses.

### Module 9 — Academic Risk Identification

Table of flagged students and the reason column. Filters match the rest of the app. Thresholds for attendance and overall percentage are editable and applied immediately. The page states that flags support review and are not final judgments.

### Module 10 — Prediction (optional)

Only after Modules 1–9 work.

- Features: `attendance_percentage`, `study_hours`, `internal_marks`, and the three subject marks when present.
- Target: `final_marks`.
- Drop rows where the target is missing. Do not impute the target.
- Median-impute feature gaps inside the training pipeline only, fit on the training split.
- `train_test_split` with `test_size=0.25` and `random_state=42`.
- Models: Linear Regression and a simple baseline that predicts the training-set mean.
- If the cleaned row count is under **40**, skip training and explain that the sample is too small.
- Metrics: MAE and RMSE on the test set. R² shown only with a note that it can mislead on a small synthetic set.
- Predictions labeled "Estimated final marks" and kept separate from stored `final_marks`.
- No claim that an estimate is the student's real result.

---

## 12. Error Handling and Safety

- Validate every form and upload before writing SQL.
- Malformed CSV/Excel returns a message and leaves the database unchanged.
- Parameterized queries only.
- Confirm before delete and before replacing existing IDs.
- Empty selections show an empty state.
- File type and 5 MB size limit.
- No passwords, no real student files in Git.
- About page states: demonstration only; do not host it publicly with real records.

---

## 13. Testing Plan

Automated tests (pytest) cover logic modules with in-memory dataframes and, for the database, a temporary SQLite file.

| # | Scenario | Where it is checked |
| --- | --- | --- |
| 1 | Application imports without error | Manual: `streamlit run app.py` |
| 2 | Dashboard numbers match a known fixture | `test_analytics.py` plus manual UI |
| 3 | Empty dataset produces no fake statistics | Analytics returns an empty summary; manual UI |
| 4 | Valid CSV is accepted | `test_validation.py` |
| 5 | Wrong column names return messages | `test_validation.py` |
| 6 | Duplicate student IDs are flagged | `test_validation.py` |
| 7 | Marks below 0 or above maximum are flagged | `test_validation.py` |
| 8 | Blank marks stay missing, not zero | `test_validation.py` and cleaning tests |
| 9 | Average and percentage match hand calculation | `test_analytics.py` |
| 10 | Grade and pass/fail boundaries | `test_grading.py` |
| 11 | Search and filters | `test_analytics.py` or a small filter helper test |
| 12 | Insert survives a new connection | `test` against temp SQLite |
| 13 | Report uses only the selected student | `test` on `reporting.py` |
| 14 | Charts receive the filtered frame | Manual UI check; figure builders accept a dataframe |
| 15 | MAE/RMSE computed on a tiny fixed set | `test` for the metric helper if prediction is built |

The README will report only tests that were actually run, including the command and the pass/fail count from that run. Untested items stay listed as manual checks.

---

## 14. Documentation to Write After the App Exists

`README.md` will include:

- Title, abstract, problem statement, motivation, objectives, scope
- Features, separating finished work from optional or future work
- Technology stack and architecture
- Data flow and database schema
- Dataset description (synthetic)
- Windows + Visual Studio Code installation and run steps
- Screenshot section with placeholders until real captures exist
- Testing methodology and the actual pytest result
- Observations from the sample run, limitations, future enhancements, conclusion
- Demonstration checklist
- Short viva questions and answers

No invented screenshot, institutional rule, or accuracy figure.

### Setup commands (Windows, PowerShell, from the project folder)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
pytest
```

The database file is created on first launch. To reset sample data during development, stop the app, delete `database\app.db`, and start again.

### Troubleshooting notes to include in the README

- `Activate.ps1` blocked by execution policy: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.
- `streamlit` not found: the virtual environment is not active, or dependencies were not installed.
- Port 8501 in use: `streamlit run app.py --server.port 8502`.
- Excel upload fails: confirm `openpyxl` is installed and the sheet has a header row.

---

## 15. Development Plan

Work stops at the end of a phase until that phase runs.

| Phase | Deliverable | Done when |
| --- | --- | --- |
| 1 | This plan: schema, rules, architecture | Columns and grade rules are fixed |
| 2 | Folders, `requirements.txt`, `venv`, `.gitignore`, empty `app.py` that opens | `streamlit run app.py` shows a placeholder home page |
| 3 | Sample CSV, loader, validation, cleaning | pytest validation tests pass |
| 4 | Grading and analytics | Hand-checked averages and grades pass tests |
| 5 | Dashboard cards and Plotly charts | Sample data fills cards from code, not constants |
| 6 | Search, filters, individual report, CSV export | One known student matches the report |
| 7 | SQLite init and CRUD | Restart the app; the added student is still there |
| 8 | Risk page with reasons | A low-attendance fixture is flagged for the right reason |
| 9 | Prediction page | Metrics come from a real fit, or the page explains the data is too small |
| 10 | Full pytest plus manual pass over the test table | Failures fixed or documented |
| 11 | README, About page, demo checklist, viva Q&A | A classmate can install from the README |

### Phase 2 first runnable slice

- `app.py` with sidebar and an empty-state dashboard.
- `modules/database.py` creating the three tables.
- `data/sample_students.csv` with a modest synthetic set.
- One validation function and one grading function with tests.

Later phases add pages without changing column names.

---

## 16. Expected Deliverables

1. Python source under `app.py`, `pages/`, and `modules/`.
2. Working Streamlit app.
3. Synthetic `data/sample_students.csv`.
4. SQLite initialization in `modules/database.py`.
5. `requirements.txt`.
6. `README.md`.
7. Automated tests.
8. Schema section in the README (also defined in this plan).
9. Architecture section in the README.
10. Charts inside the running app (screenshots added only after capture).
11. Limitations and future scope.
12. Demonstration checklist.
13. Viva questions with short answers.

### Demonstration checklist (for the evaluation day)

- [ ] Virtual environment active and `streamlit run app.py` opens the dashboard.
- [ ] Sample data loaded; every summary card matches a quick pandas check.
- [ ] Empty database shows the empty state.
- [ ] Upload the sample CSV and show the validation summary.
- [ ] Upload a file with a bad column and a mark of 150; show the errors.
- [ ] Add a student, restart the app, and show the row is still stored.
- [ ] Filter by semester and show the chart change.
- [ ] Open one student report and export CSV.
- [ ] Open risk flags and read the reasons aloud.
- [ ] Open prediction and explain MAE, RMSE, the baseline, and the synthetic-data limit.
- [ ] State that flags and predictions are decision support, not final results.

### Viva questions (concise answers)

1. **Why SQLite?** One local file, no server, enough for structured student and mark tables, and easy to reset during development.
2. **Why store marks in a separate table?** One student has many subjects. A child table avoids repeating the student's name on every mark and allows a fixed set of queries.
3. **Why not fill missing marks with zero?** Zero is a real score. A blank means the result is absent. Filling it would lower averages and create false failures.
4. **How is percentage calculated?** Sum of recorded subject marks divided by 100 times the number of those subjects. Students missing a subject are not given a fake denominator.
5. **How does pass/fail work in the demo?** Each recorded component must meet 40 percent of its maximum. No marks at all means Incomplete, not Fail.
6. **What does a risk flag mean?** A transparent rule fired, such as attendance under 75 percent. It suggests review. It does not measure ability.
7. **Does correlation mean attendance causes marks?** No. The charts describe the sample only.
8. **How is leakage avoided in the model?** `final_marks` is only the target. The train/test split happens before the imputer is fit. The imputer learns medians from the training rows.
9. **Why a mean baseline?** It shows whether Linear Regression beats always predicting the average. A model that loses to the baseline is not useful.
10. **What are the main limits?** Synthetic data, no authentication, one term per student, demonstration grade rules, and a small sample for machine learning.

### Future enhancements (not in the first build)

- Multiple academic terms per student.
- Official grade-rule import.
- Login and role-based access before any real data is used.
- PDF report styling.
- A held-out real dataset, only with permission, to re-evaluate the model.

---

## 17. Limitations (known before coding)

- Grade boundaries are demonstration defaults, not a specific college regulation.
- The sample is fictional, so findings describe the file, not a real cohort.
- One machine and one SQLite file; no concurrent multi-user editing.
- Prediction quality on fewer than a few dozen rows is weak even when the code is correct.
- Without login, the app is unsafe for real student records.

---

## 18. Current Status

The application, fictional sample, tests, and README are in the project folder.

| Item | Status |
| --- | --- |
| Planning document | Written (`PROJECT_PLAN.md`) |
| Application code | Implemented |
| Sample dataset | `data/sample_students.csv`, 100 fictional rows |
| Tests | `pytest` — 36 passed on Python 3.14.2 |
| README | Written |
| Runtime check | Modules were executed against the sample. Open the app with `streamlit run app.py` for the interface. |
