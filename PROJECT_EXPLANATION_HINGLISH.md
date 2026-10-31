# Student Academic Performance Analysis  
## Project Explanation + Dashboard Benefits + DSC Viva Q&A (Hinglish)

**Subject:** Data Science (DSC) — Semester 7 Individual Project  
**Institute context:** B.Tech / AIML–AIDS track — Data Science course  
**App name (UI):** Academic Desk  

Yeh document viva, external, aur self-study ke liye hai. Simple Hinglish mein pura project explain hai.

---

## 1. Project kya hai? (Short intro)

Yeh ek **local Streamlit web app** hai jo student academic records ko:

1. **load** karta hai (CSV / Excel / form),  
2. **validate + clean** karta hai,  
3. **SQLite** database mein store karta hai,  
4. **grades, pass rate, averages, rank** calculate karta hai,  
5. **charts / dashboard** dikhata hai,  
6. students ko **review flags** deta hai (support ke liye),  
7. optionally **final marks predict** karta hai (machine learning).

Sample data **fictional** hai — real college marksheet copy nahi ki gayi. App **localhost** par chalti hai (`127.0.0.1:8501`). Login nahi hai, isliye real student data load mat karna.

**Run karne ke liye:**

- Double-click: `run.bat` ya Desktop shortcut **Academic Desk**  
- Terminal: `.\run.ps1`

---

## 2. Problem statement (kyun banaya?)

College mein marks aur attendance aksar Excel sheets mein rehte hain. Unse manually:

- pass/fail nikalna mushkil,  
- missing paper ko galat tarah **0** maan lena common mistake,  
- weak students / low attendance quickly identify nahi hota,  
- ek student ka clean report banana time-taking.

Is project ka goal: **ek demo tool** banana jo data science workflow dikhaye — ingest → clean → store → analyze → visualize → optionally predict — aur teaching decision-support ke numbers calculate kare.

---

## 3. Objectives (kya achieve kiya?)

1. Stored records se academic performance analyze karna  
2. Average, percentage, letter grade, pass rate calculate karna  
3. Subjects ko common scale par compare karna  
4. Attendance / study hours aur marks ke beech relationship dikhana (correlation)  
5. Review rules se students flag karna (reason ke saath)  
6. Interactive dashboard dena  
7. Search, filter, add, edit, delete  
8. Individual report (CSV / PDF) — classmates ke names reveal nahi  
9. Enough data ho to final marks estimate (regression)  
10. Decision-support clearly batana — yeh judgment of ability nahi hai  

---

## 4. Technology stack — kaunsi cheez kyun?

| Tool | Role | Kyun use kiya? |
| --- | --- | --- |
| **Python** | Main language | DSC practicals + ML libraries ke saath fit |
| **Streamlit** | Dashboard UI | Fast multipage app, viva demo easy, browser mein open |
| **Pandas / NumPy** | Data tables + math | CSV handling, averages, filters |
| **Plotly** | Charts | Interactive graphs (pass/fail, grades, scatters, heatmap) |
| **SQLite (`sqlite3`)** | Database | Server install nahi chahiye; local file `database/app.db` |
| **scikit-learn** | Prediction | Linear regression + train/test + metrics |
| **openpyxl** | Excel upload | `.xlsx` support |
| **fpdf2** | PDF report | Individual report download |
| **pytest** | Automated tests | Grading / validation / DB logic verify |

**Architecture short:**

```text
app.py  →  pages/ (UI screens)  →  modules/ (real logic)
data/sample_students.csv  →  validation  →  SQLite
```

Pages mein calculation hardcode nahi — `modules/` ke functions call hote hain. Isse testing easy hoti hai.

---

## 5. Data pipeline (DSC Unit 8 / Practical 10 — ETL)

Flow:

```text
Student CSV / Excel upload
        ↓
   Read file (pandas)
        ↓
   Cleaning (headers, spaces, types)
        ↓
   Validation (ranges, duplicates, required columns)
        ↓
   Valid rows → SQLite (students + academic_records + subject_marks)
        ↓
   Dashboard / Analysis pages read DB → calculate → charts
```

**Important rules:**

- Blank mark = **missing**, zero nahi  
- Invalid row import nahi hoti (jab tak skip checkbox na ho)  
- Existing student ID default skip; update checkbox se overwrite  
- Max upload ~5 MB; sirf `.csv` / `.xlsx`  
- SQL parameterized (`?`) — injection style mistakes avoid  

Yeh **Extract → Transform → Load** pipeline hai — syllabus ke Data Engineering / ETL practical se match.

---

## 6. Database design (kyun 3 tables?)

| Table | Kya store |
| --- | --- |
| `students` | ID, name, semester, department |
| `academic_records` | attendance %, study hours |
| `subject_marks` | subject-wise marks (long form) |

**Kyun marks alag table?**  
Ek student ke multiple subjects. Name har subject row mein repeat nahi hota. Foreign key + CASCADE delete: student delete → marks bhi clean.

---

## 7. Grading & analytics concepts (kaise calculate?)

### Subject percentage
Mathematics + Programming + Database ke **recorded** marks ka average (har paper /100). Blank paper skip. Internal ( /50 ) aur Final percentage mein nahi.

### Letter grades (demo scale, official college rule nahi)
O ≥ 90, A+ ≥ 80, A ≥ 70, B+ ≥ 60, B ≥ 50, C ≥ 40, else F.

### Pass / Fail
Har component apni maximum ka pass % (default 40%). Internal bhi check. No subject + no internal → **Incomplete** (pass rate se bahar).

### Rank
Same semester + department + same recorded subject set; group size ≥ 2. Rank full DB se; filter sirf list change karta hai.

### Review flags (“Needs academic review”)
Examples: attendance &lt; 75%, marks below pass, low overall %, missing result.  
Yeh **decision support** hai — student ki ability ka judgment nahi.

### Correlation
Pearson r attendance / study hours vs subject %, internal vs final.  
**Correlation ≠ causation** — viva mein yeh line zaroor bolna.

### Prediction
Features: attendance, study hours, internal, 3 subjects.  
Target: **final_marks** only (feature nahi).  
Train/test 75/25, seed 42, median impute train-only, MAE/RMSE vs mean baseline.  
Estimates DB mein save nahi hote.

---

## 8. Dashboard pages — kya dikhta hai?

| Page | Kaam |
| --- | --- |
| **Dashboard** | Summary cards (students, average, attendance, pass rate, passed/failed, highest, for review) + charts |
| **Student Management** | Add / edit / delete / profile |
| **Upload Dataset** | File preview, validation errors, import |
| **Academic Analysis** | Subject averages, grades, histogram, ranking, comparison |
| **Attendance Analysis** | Scatter + correlation heatmap |
| **Individual Reports** | Ek student report + CSV/PDF |
| **Risk Identification** | Flagged students + reasons |
| **Prediction** | Train model, MAE vs baseline |

Sidebar mein **Academic Desk** brand + **Grading rules** (pass %, attendance threshold, overall threshold).

---

## 9. Dashboard se kya benefit mila? (Benefits)

1. **Ek jagah overview** — 100 students ka pass rate, average, review count turant dikhta hai.  
2. **Filters** — semester / department / search se zoom-in.  
3. **Mistake kam** — blank mark zero nahi banta; validation galat marks rokta hai.  
4. **Transparency** — har review flag ke saath reason.  
5. **Privacy-minded report** — individual report mein dusre students ke names nahi.  
6. **Persistence** — SQLite se app band karke bhi data rehta hai.  
7. **Teaching support** — weak components / low attendance list milti hai.  
8. **ML demo** — regression vs baseline se model utility samajh aati hai.  
9. **Offline viva** — localhost, no paid cloud.  
10. **Tested logic** — pytest se grading / DB / report checks.

**Bottom line:** Dashboard sirf “pretty UI” nahi — calculated, filterable, explainable insights deta hai.

---

## 10. DSC syllabus se mapping (kaunsa concept kyun?)

| DSC topic / unit | Project mein use | Kyun relevant? |
| --- | --- | --- |
| **Unit 1** Data Science life cycle | End-to-end pipeline | Poora IP life cycle dikhata hai |
| **Unit 3** Stats basics | Mean, rates, Pearson correlation | Academic summaries + relationships |
| **Unit 6** Data integrity / scaling ideas | Validation, clean headers, missing handling | Dirty data se galat grade na aaye |
| **Unit 8** Data pipelines / warehousing idea | ETL into SQLite | Practical “CSV → SQLite” |
| **Unit 10** Visualization + capstone + model + report | Streamlit + Plotly + regression + PDF | Capstone style deliverable |
| **Project type 2** Predictive analytics | Linear regression, MAE, RMSE | Optional ML module |

**Jo is IP mein deep cover nahi:** PySpark/Hadoop, ARIMA, SVD/matrix demos, Power BI/Tableau, gradient descent from scratch. Ek individual project mein sab units zaroori nahi — focus **pipeline + analytics + viz + optional ML** par hai.

---

## 11. Sample results (fictional file — viva numbers)

Default rules par `sample_students.csv` (100 students) se approximate:

- Pass 62, Fail 37, Incomplete 1 → pass % ~62.6%  
- Mean subject % ~53.5%, mean attendance ~77.9%  
- Highest ~92.7%, review flags ~68 students  
- Correlations (approx): attendance–marks r≈0.32; study–marks r≈0.49; internal–final r≈0.61  
- Model (ek run): linear MAE ~9.86 vs baseline MAE ~13.34  

Yeh numbers **is synthetic sample** ke hain — real college claim mat banana.

---

## 12. Limitations (honest viva points)

- Demo grade scale, official regulation nahi  
- Synthetic data → real cohort pe generalise mat karo  
- No login / no multi-user security  
- Ek term per student  
- Final marks pass/fail decide nahi karte (design choice)  
- R² chhote test set par over-read mat karo — MAE vs baseline zyada useful  

---

## 13. Viva questions + answers (DSC based)

### A. Project overview

**Q1. Aapka project kya hai?**  
**A:** Student Academic Performance Analysis — local Streamlit app jo student data validate karke SQLite mein store karti hai, phir grades, pass rates, charts, review flags, aur optional final-mark prediction dikhati hai.

**Q2. Yeh Data Science IP kyun count hota hai?**  
**A:** Isme data pipeline (ETL), cleaning/validation, descriptive stats, correlation, visualization, aur predictive modelling hai — Data Science life cycle ke major steps.

**Q3. Real data kyun nahi use kiya?**  
**A:** App mein login nahi; local DB open rehti hai. Real student privacy risk hai. Synthetic data se demo + tests safe rehte hain.

---

### B. Data pipeline / Engineering (Unit 8)

**Q4. ETL / ELT aapne kaise implement kiya?**  
**A:** Extract = CSV/Excel read; Transform = canonicalize columns, parse numbers, validate ranges; Load = parameterized insert into SQLite tables.

**Q5. SQLite kyun?**  
**A:** Lightweight, no separate server, foreign keys, ek file (`app.db`), college laptop pe easy demo.

**Q6. Marks alag table mein kyun?**  
**A:** One-to-many: ek student, kai subjects. Normalization — name duplicate nahi.

**Q7. Blank mark ko zero kyun nahi banaya?**  
**A:** Zero real score ho sakta hai. Blank = “not recorded”. Zero fill average ko wrongly lower karta hai aur false fail create kar sakta hai.

---

### C. Statistics / Analysis (Unit 3)

**Q8. Subject percentage ka formula?**  
**A:** Recorded subject marks ka mean (Math/Programming/Database). Internal aur final is percentage mein nahi.

**Q9. Incomplete student pass % mein kyun nahi?**  
**A:** Na subject, na internal → result Incomplete. Pass rate = passed / (passed + failed).

**Q10. Correlation causation kyun nahi?**  
**A:** Pearson r sirf linear association dikhata hai selected rows par. Cause prove nahi karta — confounders ho sakte hain.

**Q11. Rank kaise?**  
**A:** Same semester + department + same recorded subject set, group ≥ 2. Rank full DB se; filter list change karta hai, renumber nahi.

---

### D. Visualization / Dashboard (Unit 10)

**Q12. Dashboard ka benefit?**  
**A:** Decision-makers ko turant summary + charts milte hain; filters se segment view; review count action list deta hai.

**Q13. Plotly kyun, matplotlib nahi?**  
**A:** Streamlit ke saath interactive charts (hover, responsive) viva demo ke liye better.

**Q14. Streamlit kyun?**  
**A:** Python-only UI, multipage nav, fast prototype — DSC student ke liye practical capstone UI.

---

### E. Risk / decision support

**Q15. Risk flag ka matlab?**  
**A:** Published rule match hui (jaise attendance &lt; 75%). Additional academic support suggest — ability judgment nahi.

**Q16. Letter grade aur Pass/Fail differ kaise?**  
**A:** Letter sirf subject % se. Pass/Fail internal + pass-threshold bhi check karta hai. Sidebar pass % badalne se Pass/Fail change ho sakta hai, letter scale fixed rehti hai.

---

### F. Machine Learning (Unit 10 / Project list 2)

**Q17. Prediction features kya hain?**  
**A:** Attendance, study hours, internal marks, three subject marks. Target = final marks. Target feature nahi banaya (no leakage).

**Q18. Train/test aur imputation?**  
**A:** 75/25 split, `random_state=42`. Median imputer train data par fit, phir test par apply — test se learn nahi.

**Q19. Baseline kyun?**  
**A:** “Har student ko training mean do” — agar regression isse better MAE na de, model useful nahi us split par.

**Q20. Predictions DB mein kyun nahi save?**  
**A:** Estimate examination mark nahi hai. Confusion avoid; decision-support separate rehta hai.

**Q21. Minimum 40 labeled rows kyun?**  
**A:** Chhote sample pe unstable metrics; project deliberately refuse karta hai jab data kam ho.

---

### G. Integrity / safety (Unit 6 style)

**Q22. Upload validation kya check karti hai?**  
**A:** Required columns, ID format, attendance 0–100, study hours range, marks max, in-file duplicate IDs, file size/type.

**Q23. SQL injection kaise avoid?**  
**A:** Parameterized queries with `?` placeholders; string concatenate nahi.

---

### H. Testing & demo

**Q24. Tests kya prove karte hain?**  
**A:** Validation, grading edge cases, analytics, risk reasons, SQLite CRUD, report/PDF, prediction metrics — browser click tests alag manual.

**Q25. Demo pe kya dikhaoge?**  
**A:** Sample load → dashboard cards → filter → bad CSV reject → one report (no classmate names) → risk reasons → model MAE vs baseline → bolna “support tool, final judgment nahi”.

---

## 14. One-minute speech (memorize)

> Mera DSC individual project Academic Desk hai. Yeh Streamlit app student CSV ko validate aur clean karke SQLite mein load karti hai. Phir subject percentage, letter grades, pass-fail, ranks, aur Plotly charts calculate karti hai. Attendance aur study hours ke saath Pearson correlation dikhati hai, lekin causation claim nahi karti. Rule-based review flags decision support ke liye hain. Optional linear regression final marks estimate karti hai aur MAE ko mean baseline se compare karti hai. Data synthetic hai, login nahi hai, isliye real records nahi. Yeh project Data Science life cycle, ETL pipeline, statistics, visualization, aur predictive analytics concepts use karta hai.

---

## 15. Folder map (quick)

| Path | Meaning |
| --- | --- |
| `app.py` | Entry + page navigation |
| `pages/` | UI screens |
| `modules/` | cleaning, validation, grading, analytics, risk, charts, DB, prediction, UI |
| `data/sample_students.csv` | Fictional dataset |
| `database/app.db` | Local SQLite (gitignore) |
| `tests/` | pytest |
| `run.bat` / `run.ps1` | One-click / terminal start |
| `README.md` | English technical README |
| `PROJECT_EXPLANATION_HINGLISH.md` | Yeh viva guide |

---

**Tip:** Viva mein numbers ratne se zyada **why** bolna — blank≠0, correlation≠cause, target leakage avoid, baseline compare, synthetic data. Examiner ko process aur honesty pasand aati hai.
