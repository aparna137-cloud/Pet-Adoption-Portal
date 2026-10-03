# Project Documentation: Pet Adoption Portal
**Department of Computer Engineering, Government Polytechnic Pune**  
**Course:** Software Engineering and Testing (CM41206)  
**Academic Year:** 2026–27  
**Submitted By:** Aparna Sunil Bhokare (2406026) & Anisha Ravindra Todkar (2406004), Division G3  
**Microproject Guide:** Smt. Anita Kshirsagar / Smt. Anita Ambilpure  
**Head of Department:** Smt. J. R. Hange  

---

## 1. Project Overview & Process Model

### 1.1 Project Overview
The **Pet Adoption Portal** is an enterprise-grade software application engineered to connect individuals interested in adopting companion animals with animal welfare shelters, rescue organizations, and administrative officers. The platform provides transparent pet profile discovery, veterinary health record tracking, adoption workflow processing, financial transparency monitoring, and comprehensive software testing lifecycle management.

### 1.2 Objectives
- Provide secure role-based registration and authentication (`Adopter`, `Shelter/NGO Staff`, `Administrator`).
- Allow shelter administrators to add, edit, and manage comprehensive pet listings with photos, personality tags, and care fees.
- Enable adopters to filter animals by species (Dogs, Cats, Rabbits, Birds), gender, age, and availability.
- Display detailed veterinary medical and vaccination histories for each animal.
- Facilitate end-to-end adoption request submissions and multi-stage lifecycle review (`Pending`, `Approved`, `Completed`, `Rejected`).
- Calculate shelter financials: Total Income, Total Adoption Requests, and Reserve Balance.
- Generate graphical analytics and reports using Matplotlib and dynamic interactive client charts.
- Export adoption, pet inventory, and financial logs to CSV format.
- Ensure defect management compliance through STLC logging and automated Selenium & JMeter test suites.

### 1.3 Selected Process Model: Waterfall Model
The Waterfall model was adopted for this project due to its structured sequential progression:
1. **Requirements Analysis:** Documented in SRS (FR-01 to FR-08, NFRs).
2. **System Design:** UML Behavioral & Structural modeling.
3. **Implementation:** Modular Python Flask architecture with SQLite database.
4. **Testing:** Unit testing, Selenium black box testing (SEL-01 to SEL-09), and JMeter regression testing.
5. **Deployment:** Production-ready local WSGI server demonstration at `http://127.0.0.1:5000`.
6. **Maintenance:** Defect tracking and resolution (e.g. BUG-001).

---

## 2. Software Requirement Specification (SRS)

### 2.1 Functional Requirements
- **FR-01 (User Registration & Login):** Secure password hashing (Werkzeug PBKDF2:SHA256) and role-based session authorization.
- **FR-02 (Pet Record Management):** Full CRUD capability for animal profiles with breed, age, gender, adoption care fees, and photographs.
- **FR-03 (Adoption Request Management):** Adopters submit applications with income, residence, and motivation details; staff reviews and updates status.
- **FR-04 (Income, Request & Balance Calculation):** Automatic tallying of revenue from adoption fees and public donations, total requests, and reserve balances.
- **FR-05 (Adoption Monitoring):** Real-time tracking of adoption status transitions from Available to Pending to Adopted.
- **FR-06 (Reports & Graphical Summaries):** Headless server-side Matplotlib chart generation (`/reports/chart.png`) and client-side Chart.js visualizations.
- **FR-07 (Data Export):** Export application records, pet listings, and transaction registries to standard CSV files.
- **FR-08 (Relational Storage with User ID):** Relational database foreign keys linking users, pets, medical records, reviews, and incomes.

### 2.2 Non-Functional Requirements
- **Usability:** Responsive, intuitive user interface adhering to modern CSS standards with glassmorphic cards and clear typography.
- **Performance:** Sub-50ms endpoint latencies under JMeter regression testing.
- **Security:** Hashed passwords, parameterized SQL queries preventing SQL injection, and strict input sanitization.
- **Reliability:** ACID compliant SQLite transactions with foreign key enforcement.
- **Maintainability:** Modular separation between database layer (`database.py`), application controller (`app.py`), and presentation templates.

---

## 3. Cost & Effort Estimation

### 3.1 Decomposition Cost Estimation
| Module | Estimated Effort |
|---|---|
| Registration and Login | 20 hours |
| Pet Listing Management | 25 hours |
| Adoption Request Management | 30 hours |
| Adoption Management | 25 hours |
| Reports and Graphs | 20 hours |
| Notifications & Alerts | 10 hours |
| Database Integration | 25 hours |
| Testing and Documentation | 25 hours |
| **Total Effort** | **180 person-hours** |

- **Assumed Rate:** ₹300 per person-hour
- **Estimated Cost:** $180 \times ₹300 = \mathbf{₹54,000}$

### 3.2 Basic COCOMO Estimation
- **Project Mode:** Organic Software Project
- **Estimated Size:** 10 KLOC
- **COCOMO Constants:** $a = 2.4$, $b = 1.05$, $c = 2.5$, $d = 0.38$
- **Effort Equation:**  
  $$\text{Effort} = 2.4 \times (10)^{1.05} \approx \mathbf{26.87 \text{ person-months}}$$
- **Development Time:**  
  $$\text{Development Time} = 2.5 \times (26.87)^{0.38} \approx \mathbf{8.87 \text{ months}}$$
- **Estimated Cost (at ₹50,000 / person-month):**  
  $$26.87 \times ₹50,000 = \mathbf{₹13,43,500}$$

---

## 4. Software Testing Life Cycle (STLC) & Verification

### 4.1 Automated Selenium Test Execution (Section 10)
Executed via `python tests/test_selenium.py`:
- `SEL-01`: Open home page -> Page loads (Status 200, checks title has "Pet") -> **PASS**
- `SEL-02`: Valid login -> Dashboard opens -> **PASS**
- `SEL-03`: Invalid login -> Error displayed -> **PASS**
- `SEL-04`: Empty income form -> Validation appears -> **PASS**
- `SEL-05`: Add income -> Record saved -> **PASS**
- `SEL-06`: Add adoption request -> Record saved -> **PASS**
- `SEL-07`: Negative amount -> Input rejected (Validates fix for BUG-001) -> **PASS**
- `SEL-08`: View report -> Report displayed with Matplotlib chart -> **PASS**
- `SEL-09`: Logout -> Session ends -> **PASS**

### 4.2 Apache JMeter Regression Testing (Section 11)
- **Test Plan:** `PetPortal_Regression_Test.jmx`
- **Runner:** `tests/run_regression_jmeter.py`
- **Output:** `tests/petportal_results.jtl`
- **Results:** 25 sample requests executed across 5 loops with 100% pass rate. Average latency 8.2 ms.

### 4.3 Defect Management
- **BUG-001:** "Negative adoption request amount accepted" (Severity: High, Priority: High).
- **Status:** Resolved with multi-layer input constraints (HTML5, JS, Flask, SQLite).
