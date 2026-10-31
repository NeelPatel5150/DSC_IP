# Student Academic Performance Analysis

Semester 7 Data Science individual project. A local Streamlit application that checks student records, stores them in SQLite, and calculates grades, pass rates, attendance relationships, review flags, and an optional estimate of final marks.

The bundled records are fictional. They are not real college results.

## Abstract

Colleges often keep marks and attendance in spreadsheets that are difficult to compare. This project turns a defined student table into calculated summaries: subject percentage, a documented letter grade, pass or fail, and a list of students who match transparent review rules. Users can search and edit records, upload a CSV or Excel file, open one student's report, and, when enough final marks exist, compare a linear regression model with a simple average baseline.

## Problem statement

Raw mark sheets do not by themselves show who passed, which subjects are weaker, or which students may need another look. Hand-calculated averages also hide a common mistake: treating a missing paper as zero. This project keeps those steps in tested Python functions and shows the results in one local dashboard.

## Motivation

The project is a complete data-science workflow for a college demonstration: load, validate, clean, store, analyze, visualize, and optionally model. The review flags and the model are decision-support tools. They are not judgments of a student's ability, and a correlation in the sample is not evidence of a cause.

## Objectives

1. Analyze academic performance from stored records.
2. Calculate averages, percentages, grades, and pass rates.
3. Compare subjects on a common scale.
4. Describe how attendance and study hours move with marks in the selected records.
5. Flag students who may benefit from additional support, and show the reason.
6. Provide an interactive dashboard.
7. Search, filter, add, edit, and delete records.
8. Build an individual report that does not reveal other students' marks.
9. Estimate final marks only when the labeled sample is large enough, and compare that estimate with a baseline.
10. Show how calculated indicators can support an academic review.

## Scope

Included: Streamlit pages, Pandas calculations, Plotly charts, CSV and `.xlsx` upload, SQLite storage, rule-based review flags, CSV and PDF report download, and a scikit-learn regression page.

Not included: login, public hosting, real student data, or an official college grade regulation. The letter-grade scale below is a demonstration scale.

## Features

- Dashboard cards calculated from the current database view.
- Empty state when no students are stored.
- Search by student ID or name, and filters for semester and department.
- Add, edit, profile, and confirmed delete.
- Upload validation for columns, duplicates, ranges, and blank marks. Blank marks stay missing.
- Academic averages, grade chart, pass/fail chart, ranking, and a subject comparison.
- Attendance, study-hours, and internal-versus-final charts, plus a correlation heatmap.
- Individual report with class averages only, exported as CSV or PDF.
- Review list with one written reason per matched rule.
- Optional linear regression for final marks, scored with MAE and RMSE against a mean baseline.

Prediction does not write estimates back into the mark table.

## Technology stack

Tested in this folder on Python 3.14.2 (Windows). The packages pinned in `requirements.txt` are the versions that were installed and used for the test run:

| Package | Version used |
| --- | --- |
| streamlit | 1.66.1 |
| pandas | 3.1.0 |
| numpy | 2.5.4 |
| plotly | 7.1.0 |
| openpyxl | 3.1.5 |
| scikit-learn | 1.9.1 |
| pytest | 9.1.1 |
| fpdf2 | 2.8.9 |

SQLite is the Python standard-library `sqlite3` module. No paid service is required.

## System architecture

`app.py` opens the multipage app. Each page in `pages/` collects input and calls library functions. Calculations do not live inside the page files.

```text
app.py
pages/          Streamlit screens
modules/        validation, grading, analytics, charts, reports, risk, prediction, SQLite
data/           fictional CSV and the generator
database/       app.db is created on first use and is gitignored
tests/          pytest for the library, not for the browser
```

Data flow: CSV or Excel, or the student form, goes through column cleanup and row checks. Valid rows are written with parameterized SQL. Pages read the tables back, add percentage and grade in memory, and pass the filtered rows to Plotly.

## Database schema

Foreign keys are enabled on every connection. Deleting a student removes that student's academic row and marks.

### students

| Column | Notes |
| --- | --- |
| student_id | Primary key |
| student_name | Required |
| semester | Required |
| department | Required |
| created_at | UTC timestamp, kept when the row is edited |

### academic_records

| Column | Notes |
| --- | --- |
| record_id | Integer primary key |
| student_id | Unique foreign key to students |
| attendance_percentage | 0 to 100 |
| study_hours | 0 to 16 hours per day |
| academic_term | Same value as semester in this version |

### subject_marks

| Column | Notes |
| --- | --- |
| mark_id | Integer primary key |
| student_id | Foreign key to students |
| subject_name | Mathematics, Programming, Database, Internal, or Final |
| marks_obtained | Null when the result was not recorded |
| maximum_marks | 100, or 50 for Internal |
| examination_type | subject, internal, or final |

One student has one academic row and up to five mark rows. The student name is not copied onto every mark.

Reset during development: stop the app, delete `database/app.db`, and start again. The Upload Dataset page can also replace stored rows with the fictional sample after a confirmation checkbox.

## Dataset

`data/sample_students.csv` has 180 generated rows across Semester 1–8 (random counts per semester). The first line says the file is synthetic. Regenerate it with:

```powershell
.\.venv\Scripts\python.exe -m data.generate_sample
```

That command rewrites the CSV only. It does not change the database.

Columns: `student_id`, `student_name`, `semester`, `department`, `attendance_percentage`, `study_hours`, `mathematics_marks`, `programming_marks`, `database_marks`, `internal_marks`, `final_marks`.

Departments are Computer Science, Information Technology, and Data Science. Semesters run from Semester 1 through Semester 8. A few rows are fixed so a demonstration can show a high scorer (`S001`), a fail (`S040`), a missing mathematics mark (`S097`), an incomplete record (`S098`), a genuine zero (`S099`), and attendance of 74% (`S100`).

## Grading rules

These rules are not an official college policy. They are the rules the code uses.

Letter grade from subject percentage:

| Subject percentage | Grade |
| --- | --- |
| 90 and above | O |
| 80 up to 90 | A+ |
| 70 up to 80 | A |
| 60 up to 70 | B+ |
| 50 up to 60 | B |
| 40 up to 50 | C |
| Below 40 | F |

Subject percentage uses Mathematics, Programming, and Database only, and only the papers that have a mark. Each is out of 100. A blank paper is skipped. It is not added as zero, so two different students are not forced onto the same total.

Internal marks are out of 50. They count toward pass/fail. They are not part of the subject percentage. Final marks are stored for the report and for the model. They do not change pass/fail.

Default pass mark: 40% of that component's maximum (40/100 on a subject paper, 20/50 on the internal). The sidebar can change this percentage. A higher pass mark can make a student Fail while the letter grade stays the same, because the letter scale does not move.

A student with no recorded subject mark and no internal mark is Incomplete. Incomplete students are left out of the pass percentage. Pass percentage is passed students divided by students whose result is Pass or Fail.

Class rank is calculated only inside the same semester, department, and set of recorded subjects, and only when that group has at least two students. Rank uses the full database. A filter changes who is listed. It does not renumber ranks. Chart averages do use the filter.

## Attendance and the model

Pearson correlation is shown only when at least five complete pairs vary. The sentence under each chart states that the number describes the selected rows and does not show a cause.

The prediction page uses attendance, study hours, internal marks, and the three subject marks as inputs. `final_marks` is the target and is not an input. Rows without a final mark are dropped. Medians for missing inputs are learned on the training split only. The split is 75% train and 25% test, `random_state=42`. The baseline predicts the training average for every test student. Training is refused below 40 labeled rows. Estimates are not saved.

## Installation

The steps below were used on Windows PowerShell. Visual Studio Code can open this folder and use the `.venv` interpreter.

From the folder that contains `app.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run the activate command again.

The database file is created the first time a page reads or writes students. No separate migration command is required.

## Execution

```powershell
streamlit run app.py
```

The tested command, without relying on activation, is:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

On 26 October 2026, that command reported `36 passed` on Python 3.14.2. The tests cover validation, grading, averages, filters, review reasons, SQLite insert/update/delete, report contents, PDF generation, and prediction metrics. They do not click through the browser.

## Project screenshots

Screenshots are not stored in this repository. During a demonstration, capture the dashboard after loading the sample, the upload error list, one student report, the review table, and the prediction metrics. Those views are produced by the running app from the database, not from numbers typed into the page.

## Testing methodology

Automated tests live in `tests/` and call the library with small tables and a temporary SQLite file. The sample-file test checks that `data/sample_students.csv` is labeled synthetic and that every row passes the same validator used by the upload page.

Manual checks still worth doing in the browser:

- The dashboard empty state before any import.
- Loading the sample, then restarting the app and confirming the rows are still there.
- Uploading a file with a bad column or a mark above the maximum.
- Changing the semester filter and confirming the chart counts change.
- Opening one report and confirming another student's name is absent.
- Training the model and reading MAE against the baseline.

## Results and observations

The figures below were calculated from `data/sample_students.csv` in this project, with the default pass mark of 40%, attendance review below 75%, and subject-percentage review below 50%. They describe this fictional file only.

| Measure | Value |
| --- | --- |
| Students | 100 |
| Passed | 62 |
| Failed | 37 |
| Incomplete | 1 |
| Pass percentage | 62.63% |
| Mean subject percentage | 53.47% |
| Mean attendance | 77.88% |
| Highest subject percentage | 92.67% |
| Students matching at least one review rule | 68 |

Letter grades in the file: B 33, C 27, B+ 16, F 14, A 6, A+ 2, O 1, and 1 student with no subject percentage.

Review rules matched 38 students on attendance, 41 on a mark below the pass mark, 41 on subject percentage, and 24 on a missing result. A student can match more than one rule.

On the 99 students with a subject percentage, attendance and subject percentage had a weak positive Pearson correlation (r = 0.32, n = 99). Study hours and subject percentage had a moderate positive correlation (r = 0.49, n = 99). Internal marks and final marks had a moderate positive correlation (r = 0.61, n = 89). None of these results shows that one variable causes another.

One model run, with `random_state=42`, used 71 training rows and 24 test rows. Five students had no final mark and were excluded. Linear regression MAE was 9.86 and RMSE was 12.66 (R² 0.392). The mean baseline MAE was 13.34 and RMSE was 16.38. On this split the regression had a lower MAE than the baseline. That is a property of this synthetic split, not a guarantee for other students. Running the page again on the same stored sample reproduces the split because the random seed is fixed. Changing the stored rows changes the scores.

## Limitations

- The grade scale is a demonstration default.
- The sample is fictional, so the correlations and the model scores do not describe a real cohort.
- There is no login. Do not put the app on a public network or load real student records.
- One SQLite file is not a multi-user system.
- Each student has one current term. Older terms are not stored.
- Final marks do not affect pass/fail, which can surprise a reader who expects the final paper to decide the result. The report and the About page state this.
- R² on 24 synthetic test rows is easy to over-read. MAE against the baseline is the comparison the page emphasizes.
- PDF text is limited to characters the built-in Helvetica font can draw. Other characters are replaced.

## Future enhancements

- Several academic terms per student.
- A grade scale supplied by the college, if one is provided.
- Login and separate roles before any real data is used.
- A held-out set of real records, only with permission, before anyone trusts the model.

## Conclusion

The application calculates performance from the records it stores, rejects impossible marks, and keeps a missing paper distinct from a zero. Review flags and the regression estimate are shown with their rules and their limits, so a demonstration can explain both the number and what the number does not mean.

## Demonstration checklist

- [ ] Activate the virtual environment and run `streamlit run app.py`.
- [ ] Show the empty dashboard, then load the fictional sample.
- [ ] Read the summary cards and compare one of them with a filter, such as a single semester.
- [ ] Upload a small CSV with a mark of 150 and show the error. Confirm nothing was imported.
- [ ] Add a student, stop the app, start it again, and show that the row is still stored.
- [ ] Open one report, download the CSV, and point out that classmates' names are absent.
- [ ] Open the review page and read a reason aloud.
- [ ] Train the model and compare its MAE with the baseline.
- [ ] State that flags and estimates support a review. They are not final academic decisions.

## Viva questions

1. **Why SQLite?** One local file is enough for three related tables, foreign keys, and a reset during development. No database server is required.
2. **Why are marks in their own table?** One student has many subjects. The child table avoids repeating the student's name on every mark.
3. **Why not store a blank mark as zero?** Zero is a real score. A blank means the result is absent. Filling it would lower the average and can create a false failure.
4. **How is subject percentage calculated?** Sum of the recorded subject marks, divided by 100 times how many of those subjects were recorded. Internal and final marks are not in that total.
5. **How can the letter grade and the pass/fail result differ?** The letter grade uses subject percentage. Pass/fail also checks the internal mark against the sidebar pass percentage.
6. **Who is left out of the pass percentage?** Students with no recorded subject or internal mark. They are Incomplete, not Fail.
7. **What does a review flag mean?** A published rule matched, for example attendance below 75%. It means the student may benefit from additional support. It is not a measure of ability.
8. **Does the attendance chart show that attendance causes marks?** No. It is a Pearson correlation on the rows currently in view.
9. **How does the model avoid using the answer as an input?** `final_marks` is the target only. The train/test split happens before the median imputer is fit, and the imputer is fit on the training rows.
10. **Why compare with the training average?** If the regression cannot beat "always guess the training average" on the test rows, it is not useful on that split.

## Safety

Uploads are limited to `.csv` and `.xlsx` files of 5 MB. SQL uses `?` placeholders. Deletes and the sample reset ask for confirmation. User-supplied names are shown as text. This demonstration has no authentication.
