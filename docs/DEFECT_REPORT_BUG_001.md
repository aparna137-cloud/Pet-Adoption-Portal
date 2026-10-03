# Defect Report: BUG-001
**Department of Computer Engineering, Government Polytechnic Pune**  
**Course:** Software Engineering and Testing (CM41206)  
**Project:** Pet Adoption Portal  
**Document Type:** Formal Defect Tracking & STLC Closure Report

---

## 1. Defect Identification
| Field | Value |
|---|---|
| **Defect ID** | BUG-001 |
| **Title** | Negative adoption request amount accepted |
| **Module** | Adoption Request Management & Financial Tracking (`incomes`, `adoption_requests`) |
| **Severity** | **High** (Causes data corruption, incorrect financial reporting and balance calculation) |
| **Priority** | **High** (Must be resolved before Release Build demonstration) |
| **Reporter** | Anisha Ravindra Todkar (2406004) / Aparna Sunil Bhokare (2406026) |
| **Assigned To** | Lead Software Developer & Database Architect |
| **Status** | **Verified & Closed** |
| **Report Date** | 2026-09-24 |
| **Closure Date** | 2026-09-25 |

---

## 2. Environment Details
- **Operating System:** Windows 11 / Linux (Ubuntu 22.04 LTS)
- **Runtime:** Python 3.13
- **Framework:** Flask 3.1.3
- **Database:** SQLite 3 with Foreign Key & Check Constraints
- **Test Automation:** Selenium WebDriver & Python unittest

---

## 3. Steps to Reproduce
1. Start the Pet Adoption Portal application at `http://127.0.0.1:5000`.
2. Log into the system using valid user or administrative credentials.
3. Navigate to the **Financials & Income** page (`/income`) or open the **Adoption Request Form** (`/adopt/<pet_id>`).
4. In the numeric Amount / Income field, enter a negative number (e.g., `-2500` or `-50000`).
5. Fill remaining required fields and click **"Save Income Record"** or **"Submit Adoption Request"**.

---

## 4. Expected vs. Actual Result

### Expected Result
The system must reject negative numbers at both the client-side form level and backend controller level.  
A clear validation warning must be displayed:  
> *"Amount must be greater than or equal to 0. Negative amounts are not allowed."*  
No negative entry should be inserted into the database.

### Actual Result (Prior to Fix)
The form accepted negative input values without validation. Negative transactions reduced total revenue erroneously and violated accounting integrity.

---

## 5. Root Cause Analysis (RCA)
- Missing client-side HTML5 input validation constraint (`min="0"`).
- Missing server-side controller check in `app.py` verifying `amount >= 0`.
- Missing database level DDL constraint `CHECK(amount >= 0)`.

---

## 6. Code Fix & Resolution

### A. Database DDL Constraint (`database.py`)
```sql
CREATE TABLE IF NOT EXISTS incomes (
    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),  -- Enforced positive constraint
    date DATE NOT NULL,
    description TEXT,
    payment_method TEXT DEFAULT 'UPI / NetBanking',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
);
```

### B. Controller Validation (`app.py`)
```python
# SEL-07 & BUG-001 Fix: Reject negative amount
if amount < 0:
    flash('Amount must be greater than or equal to 0. Negative amounts are not allowed.', 'danger')
    return redirect(url_for('income'))
```

### C. Client-Side JavaScript Validation (`static/js/main.js`)
```javascript
if (amountValue < 0) {
    e.preventDefault();
    showError('Amount cannot be negative. Please enter an amount of 0 or greater.', errorContainer);
    return;
}
```

---

## 7. Verification & Regression Testing
- **Selenium Test Case:** `SEL-07` in `tests/test_selenium.py` specifically submits a negative amount of `-2500` and verifies:
  1. HTTP response code is 200 with flash message alert.
  2. Database query `SELECT * FROM incomes WHERE amount < 0` returns `0` records.
- **Result:** **PASS** (Executed in automated suite with 0 failures).
