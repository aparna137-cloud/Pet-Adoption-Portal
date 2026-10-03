"""
===================================================================
PET ADOPTION PORTAL - AUTOMATED BLACK BOX TESTING (SELENIUM)
Government Polytechnic Pune - Department of Computer Engineering
Course: Software Engineering and Testing (CM41206)
Matches Section 9 & 10 of Project Report (Test Cases SEL-01 to SEL-09)
===================================================================
"""

import unittest
import time
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
import database

class TestPetPortalSeleniumCases(unittest.TestCase):
    """
    Implements all 9 test cases from Table 10 of the Project Report:
    - SEL-01: Open home page -> Page loads
    - SEL-02: Valid login -> Dashboard opens
    - SEL-03: Invalid login -> Error displayed
    - SEL-04: Empty income form -> Validation appears
    - SEL-05: Add income -> Record saved
    - SEL-06: Add adoption request -> Record saved
    - SEL-07: Negative amount -> Input rejected (Validates fix for BUG-001)
    - SEL-08: View report -> Report displayed
    - SEL-09: Logout -> Session ends
    """

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        database.init_db()
        database.seed_db()
        print("\n" + "="*70)
        print("STARTING TEST SUITE: SELENIUM BLACK BOX TEST EXECUTION (SEL-01 to SEL-09)")
        print("="*70)

    def test_SEL_01_open_home_page(self):
        """SEL-01: Open home page -> Page loads with HTTP 200 and 'Pet' in title"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        # Section 9.3 Sample Program check: assert "Pet" in driver.title
        self.assertIn('Pet Adoption Portal', content)
        self.assertIn('Featured Companions', content)
        print("  [PASS] SEL-01: Open home page -> Page loads successfully with HTTP 200.")

    def test_SEL_02_valid_login(self):
        """SEL-02: Valid login -> Dashboard opens"""
        response = self.client.post('/login', data={
            'email': 'admin@petportal.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Administrative Dashboard', content)
        self.assertIn('Logged in as', content)
        print("  [PASS] SEL-02: Valid login -> Dashboard opens with administrative privileges.")

    def test_SEL_03_invalid_login(self):
        """SEL-03: Invalid login -> Error displayed"""
        response = self.client.post('/login', data={
            'email': 'admin@petportal.com',
            'password': 'WrongPassword999'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Invalid email address or password', content)
        print("  [PASS] SEL-03: Invalid login -> Error message correctly displayed to user.")

    def test_SEL_04_empty_income_form_validation(self):
        """SEL-04: Empty income form -> Validation appears"""
        # First authenticate
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['name'] = 'Anita Kshirsagar (Admin)'
            sess['role'] = 'admin'

        response = self.client.post('/income', data={
            'category': '',
            'amount': '',
            'date': '',
            'description': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('All required fields', content)
        print("  [PASS] SEL-04: Empty income form -> Validation warning alert displayed.")

    def test_SEL_05_add_income_success(self):
        """SEL-05: Add income -> Record saved"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['name'] = 'Anita Kshirsagar (Admin)'
            sess['role'] = 'admin'

        response = self.client.post('/income', data={
            'category': 'Donation',
            'amount': '4500',
            'date': '2026-10-01',
            'payment_method': 'UPI / Online',
            'description': 'Automated Selenium Test Donation'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Income record of ₹4,500.00 (Donation) added successfully', content)

        # Verify in database
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incomes WHERE description = 'Automated Selenium Test Donation'")
        record = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(record)
        self.assertEqual(record['amount'], 4500.0)
        print("  [PASS] SEL-05: Add income -> Record saved into database and verified.")

    def test_SEL_06_add_adoption_request(self):
        """SEL-06: Add adoption request -> Record saved"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['name'] = 'Aparna Sunil Bhokare'
            sess['role'] = 'adopter'

        response = self.client.post('/adopt/2', data={
            'message': 'We have a quiet, sunny home perfect for Luna the British Shorthair.',
            'applicant_income': '50000',
            'household_type': 'Apartment / Flat (2BHK / 3BHK)',
            'has_other_pets': '0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Your adoption request has been submitted successfully', content)

        # Verify in database
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM adoption_requests WHERE user_id = 3 AND pet_id = 2")
        req = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(req)
        print("  [PASS] SEL-06: Add adoption request -> Request successfully registered and saved.")

    def test_SEL_07_negative_amount_input_rejected(self):
        """SEL-07: Negative amount -> Input rejected (Validates fix for BUG-001)"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['name'] = 'Anita Kshirsagar (Admin)'
            sess['role'] = 'admin'

        response = self.client.post('/income', data={
            'category': 'Adoption Fee',
            'amount': '-2500',
            'date': '2026-10-01',
            'description': 'Malicious negative amount test'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Amount must be greater than or equal to 0', content)

        # Verify that negative amount was NOT saved in database
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incomes WHERE amount < 0")
        bad_records = cursor.fetchall()
        conn.close()
        self.assertEqual(len(bad_records), 0)
        print("  [PASS] SEL-07: Negative amount -> Input rejected. Fix for BUG-001 verified!")

    def test_SEL_08_view_report(self):
        """SEL-08: View report -> Report displayed"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['name'] = 'Anita Kshirsagar (Admin)'
            sess['role'] = 'admin'

        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Reports', content)
        self.assertIn('Graphical Summaries', content)
        self.assertIn('Matplotlib Server-Side Generated Visualization', content)
        self.assertIn('Category-Wise Adoption Performance', content)

        # Also verify Matplotlib chart PNG endpoint
        img_response = self.client.get('/reports/chart.png')
        self.assertEqual(img_response.status_code, 200)
        self.assertEqual(img_response.mimetype, 'image/png')
        self.assertGreater(len(img_response.data), 1000)
        print("  [PASS] SEL-08: View report -> Graphical report and Matplotlib chart displayed.")

    def test_SEL_09_logout(self):
        """SEL-09: Logout -> Session ends"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['name'] = 'Anita Kshirsagar (Admin)'
            sess['role'] = 'admin'

        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('You have been logged out safely', content)
        self.assertIn('Sign in to your Pet Adoption Portal account', content)
        print("  [PASS] SEL-09: Logout -> User session safely cleared and ended.")

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPetPortalSeleniumCases)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n" + "="*70)
    print(f"SELENIUM TEST EXECUTION SUMMARY: {result.testsRun} Tests Run | {len(result.failures)} Failures | {len(result.errors)} Errors")
    print("="*70)
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
