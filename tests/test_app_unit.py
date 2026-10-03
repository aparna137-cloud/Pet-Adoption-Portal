"""
===================================================================
PET ADOPTION PORTAL - UNIT & INTEGRATION TEST SUITE
Government Polytechnic Pune - Department of Computer Engineering
Course: Software Engineering and Testing (CM41206)
===================================================================
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
import database

class TestPetPortalUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        database.init_db()
        database.seed_db()

    def test_database_connection(self):
        """Verify SQLite database connection and PRAGMAs"""
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pets")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)

    def test_api_health(self):
        """Verify API health endpoint"""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('Government Polytechnic Pune', data['college'])

    def test_pet_detail_view(self):
        """Verify pet detail view retrieves pet data and medical history"""
        res = self.client.get('/pet/1')
        self.assertEqual(res.status_code, 200)
        content = res.data.decode('utf-8')
        self.assertIn('Buddy', content)
        self.assertIn('Golden Retriever', content)
        self.assertIn('Medical', content)
        self.assertIn('Vaccination Records', content)

    def test_export_requests_csv(self):
        """FR-07: Test CSV export of adoption requests"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'

        res = self.client.get('/export/requests')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.content_type)
        self.assertIn('attachment; filename=', res.headers.get('Content-Disposition'))
        csv_text = res.data.decode('utf-8')
        self.assertIn('Request ID,Applicant Name', csv_text)

    def test_export_pets_csv(self):
        """FR-07: Test CSV export of pet catalog"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'

        res = self.client.get('/export/pets')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.content_type)
        csv_text = res.data.decode('utf-8')
        self.assertIn('Pet ID,Pet Name,Category,Breed', csv_text)

    def test_export_income_csv(self):
        """FR-07: Test CSV export of income transactions"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'

        res = self.client.get('/export/income')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.content_type)
        csv_text = res.data.decode('utf-8')
        self.assertIn('Income ID,Date,Category,Amount (INR)', csv_text)

    def test_review_submission(self):
        """Test user submitting a review for a pet"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['name'] = 'Aparna Sunil Bhokare'

        res = self.client.post('/reviews/add/1', data={
            'rating': '5',
            'comment': 'Outstanding experience adopting through this portal!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        content = res.data.decode('utf-8')
        self.assertIn('Thank you for sharing your feedback', content)

    def test_add_medical_record_as_staff(self):
        """Test adding medical record for pet #1"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'staff'

        res = self.client.post('/admin/medical/add/1', data={
            'vaccination': 'Kennel Cough Booster',
            'health_status': 'Healthy',
            'record_date': '2026-10-02',
            'notes': 'Booster administered. Dog is cheerful and energetic.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        content = res.data.decode('utf-8')
        self.assertIn('Medical record appended successfully', content)

if __name__ == '__main__':
    unittest.main()
