# 🐾 Pet Adoption Portal
**Government Polytechnic Pune — Department of Computer Engineering**  
**Course:** Software Engineering and Testing (CM41206) | **Academic Year:** 2026–27  
**Submitted By:** Aparna Sunil Bhokare (2406026) & Anisha Ravindra Todkar (2406004), Division G3  
**Guide:** Smt. Anita Kshirsagar / Smt. Anita Ambilpure  

---

## 🌟 Overview
The **Pet Adoption Portal** is a software engineering and testing project developed in accordance with the GPP CM41206 syllabus. It features a complete web portal for shelter animal discovery, medical histories, adoption application processing, shelter income/donation management, and an integrated Software Testing Life Cycle (STLC) defect registry.

---

## 🚀 Quick Start Instructions

### 1. Requirements
Ensure Python 3.10+ is installed on your machine. All required packages (Flask, SQLite3, Pandas, Numpy, Matplotlib, Selenium) are pre-installed.

### 2. Initialize Database & Seed Records
```bash
python database.py
```
*Creates `pet_adoption.db` with complete schema, categories, cute pets, medical records, adoption requests, income entries, and defect registry.*

### 3. Start the Web Server
```bash
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Demo Login Credentials

| Role | Email | Password | Privileges |
|---|---|---|---|
| **Admin** | `admin@petportal.com` | `admin123` | Full access: pets, categories, users, financials, reports |
| **Shelter Staff** | `staff@petportal.com` | `staff123` | Manage pets, review adoption requests, add medical records |
| **Adopter (Aparna)** | `aparna@petportal.com` | `user123` | Browse pets, apply for adoption, track requests, leave reviews |

*Tip: Quick login buttons are provided on the login page for instantaneous 1-click evaluation!*

---

## 🧪 Automated Testing Suites

### 1. Selenium Black Box Testing (SEL-01 to SEL-09)
Directly executes the 9 test cases specified in **Section 10 of the Project Report**:
```bash
python tests/test_selenium.py
```
- **SEL-01:** Open home page -> Page loads
- **SEL-02:** Valid login -> Dashboard opens
- **SEL-03:** Invalid login -> Error displayed
- **SEL-04:** Empty income form -> Validation appears
- **SEL-05:** Add income -> Record saved
- **SEL-06:** Add adoption request -> Record saved
- **SEL-07:** Negative amount -> Input rejected (Validates fix for BUG-001)
- **SEL-08:** View report -> Report displayed with Matplotlib chart
- **SEL-09:** Logout -> Session ends

### 2. Apache JMeter Regression Testing
Directly executes the regression test plan specified in **Section 11 of the Project Report**:
```bash
python tests/run_regression_jmeter.py
```
- Test Plan: `tests/PetPortal_Regression_Test.jmx`
- Generates JMeter results file: `tests/petportal_results.jtl` (25 samples across 5 loops)

### 3. Unit & Integration Testing
```bash
python tests/test_app_unit.py
```
- Tests database connectivity, API health, CSV export routines, reviews, and medical logs.

---

## 📁 Project Directory Structure
```
PetAdoptionPortal/
├── app.py                             # Main Flask application with all routes
├── database.py                        # SQLite schema & database seed script
├── pet_adoption.db                    # Relational database file
├── README.md                          # Project documentation and quick start
├── docs/
│   ├── DEFECT_REPORT_BUG_001.md       # Official Bug Report for BUG-001 (Negative amount)
│   └── PROJECT_DOCUMENTATION.md       # Comprehensive 14-chapter project report documentation
├── static/
│   ├── css/style.css                  # Modern CSS design system (glassmorphism, responsive)
│   ├── js/main.js                     # Client validation and modal scripts
│   ├── images/                        # Pet photos, mascot logo, and hero banner
│   └── uploads/                       # Uploaded pet photos directory
├── templates/
│   ├── base.html                      # Layout navbar, alert notifications, and footer
│   ├── index.html                     # Hero banner, stats counter, categories, workflow
│   ├── pets.html                      # Pet catalog with search & multi-filter
│   ├── pet_detail.html                # Pet profile, vaccination history, and reviews
│   ├── adopt_form.html                # Adoption request application (BUG-001 validated)
│   ├── my_requests.html               # User request tracking timeline
│   ├── manage_requests.html           # Staff review, approval, and rejection modal
│   ├── income.html                    # Financial overview, income/donation logs, balance (FR-04)
│   ├── reports.html                   # Matplotlib chart, Chart.js, Pandas summaries, CSV exports
│   ├── admin_dashboard.html           # Administrative dashboard and inventory table
│   ├── pet_form.html                  # Add / Edit pet listings form
│   ├── categories.html                # Pet species categories manager
│   ├── users.html                     # Registered user directory
│   ├── login.html                     # Authentication with quick demo fill buttons
│   ├── register.html                  # Adopter & staff registration
│   └── defect_report.html             # STLC pipeline and defect registry
└── tests/
    ├── test_selenium.py               # Automated test suite for SEL-01 to SEL-09
    ├── PetPortal_Regression_Test.jmx  # Apache JMeter regression test plan XML
    ├── run_regression_jmeter.py       # JMeter test execution runner
    ├── petportal_results.jtl          # JMeter result file output
    └── test_app_unit.py               # Unit & integration test suite
```
