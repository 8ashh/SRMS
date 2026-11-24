# Academic Performance Analytics & Student Record Management System (SRMS)

**Institution:** Madhav Institute of Technology & Science (MITS), Gwalior  
**Department:** Department of Computer Science & Engineering  
**Academic Session:** 2026–27  
**Category:** Academic Performance Analytics / Decision Support System  

---

## 1. Project Introduction

The **Academic Performance Analytics & Student Record Management System (SRMS)** is a modern, responsive web application designed for **Madhav Institute of Technology & Science (MITS), Gwalior**.

Rather than functioning solely as an electronic filing cabinet for marks and attendance, this system transforms routine student records into an **academic decision-support platform**. It empowers faculty and department heads with real-time analytics, automated statistical anomaly detection, and machine-learning grade forecasts to pinpoint students experiencing academic decline long before final examinations occur.

---

## 2. Problem Statement

In conventional academic institutions:
1. Student marks and classroom attendance are maintained in disjointed spreadsheets or legacy database systems.
2. Faculty only discover learning difficulties after semester-end examination grades are published—when it is too late for remedial intervention.
3. Class teachers lack automated tools to spot subtle downward trends (e.g., a student dropping 15% between internal tests).
4. Academic decision-makers lack cohort-level comparative analytics and standardized PDF/CSV dossier exports for departmental reviews.

---

## 3. Project Objectives

- **Early Academic Intervention:** Identify students at academic risk while time remains for mentoring and remedial classes.
- **Unified Student Record Management:** Provide complete CRUD operations for students, subjects, marks, and attendance.
- **Statistical Anomaly Detection:** Implement Z-score cohort benchmarking ($Z < -1.5$) and consecutive test drop alerts ($\ge 15\%$).
- **Predictive Machine Learning:** Forecast likely final semester performance from mid-term scores and attendance patterns.
- **Automated Reporting:** Generate formal, audited PDF dossiers and CSV data sheets in under three clicks.
- **Beginner-Friendly Architecture:** Built with clean, accessible Python, Flask, SQLite, and vanilla web standards so students can confidently explain the entire project during viva defense.

---

## 4. Six Core Functional Requirements

1. **FR-1: Student Profile & Enrollment Management**  
   Add, update, search, filter, and inspect enrolled students with unique roll number constraints and linked accounts.
2. **FR-2: Continuous Assessment & Marks Management**  
   Record, validate, update, and review internal test marks with automated percentage calculations handled strictly in Python.
3. **FR-3: Daily Attendance Tracking & Percentage Synthesis**  
   Log subject-wise attendance by date with real-time threshold categorization (Green $\ge 75\%$, Amber $60-74\%$, Red $< 60\%$).
4. **FR-4: Academic Analytics Engine**  
   Compute class averages, subject averages, grade distributions (A, B, C, F), pass/fail percentages, and sequential test trends using Pandas and NumPy.
5. **FR-5: Statistical Anomaly Detection**  
   Automated detection of declining performance using Z-score cohort comparison ($Z < -1.5$) and sequential score drops ($\ge 15\%$).
6. **FR-6: Predictive Grade Modelling & Reporting**  
   Scikit-Learn regression models (Linear Regression & Random Forest) evaluating MAE and $R^2$, paired with instant PDF/CSV report generation.

---

## 5. Technology Stack & Justification

| Layer | Technology | Justification |
| :--- | :--- | :--- |
| **Frontend UI** | HTML5, CSS3, Bootstrap 5 | Standard, lightweight, responsive UI framework without complex npm/build pipelines. |
| **Icons & Charts** | Bootstrap Icons, Chart.js 4.4 | Clean iconography and reactive visual analytics (bar, donut, line charts). |
| **Backend Framework**| Python 3 & Flask | High-readability Python microframework easily understood by beginner programmers. |
| **ORM & Database** | Flask-SQLAlchemy & SQLite | Portable, serverless relational database requiring zero external service setup. |
| **Security & Auth** | Werkzeug PBKDF2:SHA256 | Cryptographically secure salted password hashing and role-based session guards. |
| **Data Analytics** | Pandas & NumPy | Fast vector grouping, aggregations, standard deviations, and class means. |
| **Machine Learning**| Scikit-Learn | Transparent, interpretable regression algorithms (Linear Regression & Random Forest). |
| **PDF Reporting** | fpdf2 | Fast, pure-Python PDF rendering without heavy C dependencies or headless browsers. |
| **Automated Testing**| Pytest | Simple, reliable test runner with fixtures for testing services, models, and routes. |

*Why no React, Next.js, or MongoDB?*  
To avoid overengineering. A micro-project must prioritize code clarity, architectural understanding, and demonstrable viva concepts over unnecessary framework complexity.

---

## 6. Three-Layer Architecture

The application strictly adheres to a three-tier separation of concerns:

```
+-----------------------------------------------------------------------+
|                       PRESENTATION LAYER (Frontend)                   |
|  - HTML5 Templates (Jinja2 inheritance)                               |
|  - Bootstrap 5 + Midnight Navy Styling (style.css)                     |
|  - Chart.js Dashboard Visualizations (charts.js, main.js)             |
+-----------------------------------+-----------------------------------+
                                    | HTTP Requests (Form POST / GET)
                                    v
+-----------------------------------------------------------------------+
|                       APPLICATION LAYER (Backend Services)            |
|  - Routes: auth.py, admin.py, faculty.py, student.py, reports.py      |
|  - StudentService, MarksService, AttendanceService                    |
|  - AnalyticsService (Pandas / NumPy aggregation)                      |
|  - AnomalyService (Z-score & consecutive test drop detection)         |
|  - PredictionService (Scikit-Learn regression pipeline)               |
|  - AuditService (Governance logging)                                  |
+-----------------------------------+-----------------------------------+
                                    | SQLAlchemy ORM Queries
                                    v
+-----------------------------------------------------------------------+
|                       DATA LAYER (Persistence)                        |
|  - SQLite (instance/database.db)                                      |
|  - Models: Student, Subject, Mark, Attendance, User, AuditLog         |
|  - Foreign Key Constraints & Cascade Cleanup                          |
+-----------------------------------------------------------------------+
```

---

## 7. Database Tables & Schema Design

SQLite relational schema managed through SQLAlchemy models in `models.py`:

1. **`students`**:  
   - `student_id` (INTEGER PK), `roll_no` (VARCHAR(30) UNIQUE INDEX), `name` (VARCHAR(100)), `semester` (INTEGER), `section` (VARCHAR(10)), `created_at` (DATETIME).
2. **`subjects`**:  
   - `subject_id` (INTEGER PK), `code` (VARCHAR(20) UNIQUE INDEX), `name` (VARCHAR(100)), `created_at` (DATETIME).
3. **`marks`**:  
   - `mark_id` (INTEGER PK), `student_id` (FK students), `subject_id` (FK subjects), `test_no` (INTEGER), `score` (FLOAT), `max_score` (FLOAT), `created_at`, `updated_at`.  
   - **Constraint:** `UniqueConstraint('student_id', 'subject_id', 'test_no')`.
4. **`attendance`**:  
   - `att_id` (INTEGER PK), `student_id` (FK students), `subject_id` (FK subjects), `date` (DATE), `status` (VARCHAR(10)), `created_at`.  
   - **Constraint:** `UniqueConstraint('student_id', 'subject_id', 'date')`.
5. **`users`**:  
   - `user_id` (INTEGER PK), `username` (VARCHAR(50) UNIQUE), `password_hash` (VARCHAR(256)), `role` (`admin` | `faculty` | `student`), `student_id` (FK students, optional), `faculty_name` (VARCHAR(100)), `created_at`.
6. **`audit_logs`**:  
   - `log_id` (INTEGER PK), `user_id` (FK users), `action` (VARCHAR(50)), `module` (VARCHAR(50)), `record_id` (VARCHAR(50)), `timestamp` (DATETIME), `description` (TEXT).

---

## 8. Authentication & Role-Based Access Control (RBAC)

The system protects routes via Python decorators defined in `routes/auth.py`:
- `@login_required`: Checks if `user_id` exists in Flask session.
- `@role_required(['admin'])`: Restricts configuration and user provisioning to administrators.
- `@role_required(['admin', 'faculty'])`: Allows instructors and admins to enter marks, track attendance, and view cohort analytics.
- `@role_required(['student'])`: Confines student access strictly to personal academic records.
- **Student Data Isolation:** Students can never access or download records for any roll number other than their own linked `session['student_id']`. Unauthorized attempts trigger HTTP 403 Forbidden.

---

## 9. Academic Analytics Engine (Pandas & NumPy)

All analytics in `services/analytics_service.py` operate on live SQLite data:
- **Class Average:** Calculated per subject, test, and semester cohort.
- **Subject Averages:** Computes mean, minimum, maximum, and standard deviation ($\sigma$).
- **Grade Distribution:** Categorizes marks into Grade A ($\ge 75\%$), Grade B ($60–74\%$), Grade C ($40–59\%$), and Grade F ($< 40\%$) with configurable institution cutoffs.
- **Pass/Fail Statistics:** Evaluates total records meeting the configurable threshold ($\ge 40\%$).
- **Performance Trends:** Formats longitudinal test score averages across Test 1, Test 2, and Test 3 for Chart.js line charts.

---

## 10. Statistical Anomaly Detection

Located in `services/anomaly_service.py`, combining two statistical methodologies:

### Method A: Z-score Anomaly Detection
Measures how many standard deviations a student's score deviates from the peer cohort in the exact same subject and test:
$$Z = \frac{X - \mu}{\sigma}$$
- $X$ = Student's percentage score.
- $\mu$ = Cohort mean score for that subject and test.
- $\sigma$ = Cohort standard deviation.
- **Anomaly Flag:** Triggered when $Z < -1.5$ (requires cohort sample size $\ge 3$ and $\sigma > 0$ to avoid false positives).

### Method B: Falling Performance Trend
Tracks sequential test evaluations for the same student in the same subject:
$$\Delta = \text{Score}_{\text{previous}} - \text{Score}_{\text{current}}$$
- **Anomaly Flag:** Triggered when marks drop by $\ge 15\%$ between consecutive tests.

### Risk Tiers
- **High Risk (Red):** Severe drop ($\ge 15\%$) combined with $Z \le -1.5$, or extreme negative deviation ($Z \le -2.0$).
- **Medium Risk (Amber):** Single anomaly indicator or low attendance ($< 60\%$).
- **Low Risk (Green):** Normal academic progress without active alerts.

---

## 11. Predictive Grade Modelling (Scikit-Learn)

Implemented in `services/prediction_service.py`:
- **Features ($X$):** Mid-term assessment percentage (`midterm_score`) and class attendance rate (`attendance_rate`).
- **Target ($y$):** Final semester percentage (`final_score`).
- **Models:** Evaluates and compares **Linear Regression** with **Random Forest Regressor** (50 estimators, max depth 5).
- **Validation:** 80% train / 20% test partition.
- **Evaluation Metrics:** Evaluated using Mean Absolute Error (MAE) and Coefficient of Determination ($R^2$).
- **Synthetic Demo Benchmark:** Includes clearly labeled synthetic cohort benchmark mode ($N=120$) for viva demonstration when historical semester-end final grades are still pending.
- **Transparency Safeguard:** Every prediction displays an explicit advisory banner: *"Notice: Estimated grades are academic decision-support indicators, not guaranteed final examination results."*

---

## 12. Reports & PDF Dossiers

`services/report_service.py` utilizes `fpdf2` and Python's `csv` module to generate:
1. **Student Academic Dossier (PDF & CSV):** Detailed student card, assessment ledger, attendance percentage, active warnings, and predicted outcome.
2. **Class Performance Report (PDF & CSV):** Enrolled counts, subject means, grade breakdown, and pass/fail distribution.
3. **Early Warning Risk Report (PDF & CSV):** Actionable list of flagged students categorized by risk tier and reason for faculty intervention.

---

## 13. Demo Credentials

The database comes pre-seeded with realistic demonstration accounts:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full access to administration, logs, and user management |
| **Faculty** | `faculty_sharma` | `faculty123` | Dr. Rajesh Sharma (CS Department) |
| **Faculty** | `faculty_verma` | `faculty123` | Prof. Sunita Verma (CS Department) |
| **Student (Star)** | `ai23001` | `AI23001@123` | Rahul Sharma (High marks, 95% attendance) |
| **Student (Declining)**| `ai23005` | `AI23005@123` | Rohan Gupta (Score drop: 84% $\rightarrow$ 60% $\rightarrow$ 40%) |
| **Student (Outlier)** | `ai23009` | `AI23009@123` | Vikram Meena (Low score: $Z < -1.5$ outlier) |
| **Student (Low Attnd)** | `ai23012` | `AI23012@123` | Pooja Tiwari (Low attendance: $< 55\%$) |

*Note: All demo accounts are fictional. One-click credential autofill buttons are conveniently available on the login page.*

---

## 14. Installation & Local Setup

### Prerequisites
- Python 3.9+ installed on your computer.

### Step 1: Clone or Open Project
```bash
cd /Users/jatinjadoun/.gemini/antigravity/scratch/academic-performance-system
```

### Step 2: Create and Activate Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed the Database
Populate the SQLite database with institutional demo records:
```bash
python seed_data.py
```

### Step 5: Launch the Application
```bash
python app.py
```
Open your web browser and navigate to:  
👉 **`http://localhost:5001`**

---

## 15. Running Automated Tests

Run the full automated test suite using Pytest:
```bash
PYTHONPATH=. pytest -v
```

The test suite executes 22 comprehensive test cases covering:
- Authentication, sessions, and logout flows.
- Role-based route protection and student data isolation.
- Student, subject, marks, and attendance CRUD and input validation.
- Anomaly detection (Z-scores and falling performance trends).
- Machine learning regression training, MAE, $R^2$, and output bounds.

---

## 16. Project Structure

```
academic-performance-system/
├── app.py                      # Flask Application Factory & CLI commands
├── config.py                   # System thresholds & configuration
├── extensions.py               # SQLAlchemy extension initialization
├── models.py                   # Relational database models (6 tables)
├── seed_data.py                # Database population script with demo records
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable reference
├── .gitignore                  # Git ignore rules
│
├── routes/                     # Application Blueprints
│   ├── auth.py                 # Login, logout, session guards & RBAC decorators
│   ├── admin.py                # Admin dashboard, user & academic management
│   ├── faculty.py              # Faculty dashboard, marks & attendance entry
│   ├── student.py              # Student portal & personal dossier
│   └── reports.py              # PDF and CSV download streaming routes
│
├── services/                   # Business Logic & Processing Layer
│   ├── student_service.py      # Student validation, search & CRUD
│   ├── subject_service.py      # Subject & course management
│   ├── marks_service.py        # Mark recording & percentage calculation
│   ├── attendance_service.py   # Daily attendance & percentage calculations
│   ├── analytics_service.py    # Pandas/NumPy analytics engine
│   ├── anomaly_service.py      # Z-score & falling trend anomaly detector
│   ├── prediction_service.py   # Scikit-Learn regression grade predictor
│   ├── report_service.py       # fpdf2 PDF and CSV generator
│   └── audit_service.py        # Tamper-evident activity logging
│
├── templates/                  # Presentation Layer (Jinja2 HTML Templates)
│   ├── base.html               # Master layout with Bootstrap & Chart.js
│   ├── login.html              # Modern login page with credential helper
│   ├── components/             # Reusable UI components (sidebar, navbar, alerts)
│   ├── admin/                  # 10 Admin management and analytics templates
│   ├── faculty/                # 9 Faculty evaluation templates
│   ├── student/                # 6 Student portal templates
│   └── errors/                 # 403, 404, and 500 error pages
│
├── static/                     # Static Web Assets
│   ├── css/style.css           # Custom Midnight Navy styling
│   └── js/
│       ├── main.js             # Mobile toggles & auto-dismiss notices
│       └── charts.js           # Chart.js visualizer wrappers
│
├── instance/
│   ├── database.db             # SQLite database file
│   └── ml_models/              # Persisted joblib ML regressor files
│
└── tests/                      # Automated Pytest Suite
    ├── conftest.py             # Test fixtures with isolated in-memory DB
    ├── test_auth.py            # RBAC and session tests
    ├── test_students.py        # Student CRUD and validation tests
    ├── test_marks.py           # Marks calculation & validation tests
    ├── test_attendance.py      # Attendance logic & date constraint tests
    ├── test_analytics.py       # Statistics & grade distribution tests
    ├── test_anomalies.py       # Anomaly Z-score & drop tests
    └── test_predictions.py    # Scikit-learn regression tests
```

---

## 17. Deployment Instructions

To deploy to beginner-friendly persistent cloud hosting (e.g., Render, Railway, PythonAnywhere, or a standard VPS):
1. **Repository Setup:** Push the repository to GitHub.
2. **Environment Variables:** Set `SECRET_KEY` and `FLASK_ENV=production`.
3. **Persistent Disk:** When deploying on Render or Railway, attach a persistent storage volume to `/instance` so the SQLite database is preserved across restarts and redeployments.
4. **WSGI Server:** Launch with Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn "app:create_app()" --bind 0.0.0.0:$PORT
   ```

---

## 18. Project Limitations & Future Scope

### Current Limitations
- **Local SQLite Storage:** SQLite is lightweight and optimal for demonstration and micro-project evaluation, but high-concurrency production deployments (e.g., > 20,000 active students) benefit from migrating to PostgreSQL.
- **Mid-term Feature Correlation:** ML predictions rely on mid-term test scores and attendance percentages; qualitative factors (e.g., assignment submissions, lab viva scores) can be added as feature dimensions.

### Future Scope
- **SMS & Email Notifications:** Automated alerts sent to faculty mentors when students trigger High Risk warnings.
- **Biometric / RFID Hardware Integration:** Direct synchronization with classroom attendance card scanners.
- **Semester CGPA Forecasting:** Extending regression models across multi-semester transcript histories.
