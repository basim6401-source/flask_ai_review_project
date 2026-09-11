import unittest

from app import app, load_config, init_db, get_db_connection


class AdminAuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_login_page_is_available(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)

    def test_admin_requires_login(self):
        response = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    def test_valid_login_grants_access(self):
        response = self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin', response.headers.get('Location', ''))

    def test_generate_review_matches_business_type(self):
        response = self.client.get('/generate?type=Dental%20Clinic')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('reviews'))
        review_text = ' '.join(data['reviews']).lower()
        self.assertTrue(any(keyword in review_text for keyword in ['clinic', 'dental', 'teeth', 'treatment', 'check-up', 'cleaning']))
        self.assertNotIn('food', review_text)

    def test_admin_saves_business_type_per_shop(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.post('/admin', data={
            'shop_name': ['Clinic Pro', 'North Spice'],
            'shop_url': ['https://clinic.example', 'https://spice.example'],
            'shop_type': ['Dental Clinic', 'South Indian Vegetarian'],
            'quiz_types': ['Dental Clinic', 'South Indian Vegetarian']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertEqual(cfg['shops'][0]['type'], 'Dental Clinic')
        self.assertEqual(cfg['shops'][1]['type'], 'South Indian Vegetarian')

    def test_database_is_initialized_and_persisted(self):
        init_db()
        conn = get_db_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('businesses', 'quiz_types') ORDER BY name").fetchall()
        self.assertEqual([row[0] for row in tables], ['businesses', 'quiz_types'])


if __name__ == '__main__':
    unittest.main()
