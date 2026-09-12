import unittest
import uuid

from app import ADMIN_PATH, app, load_config, init_db, get_db_connection


class AdminAuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_login_page_is_available(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Restricted Access', response.data)

    def test_home_page_generates_admin_sign_in_link(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/login"', response.data)

    def test_admin_requires_login(self):
        response = self.client.get(ADMIN_PATH, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    def test_valid_login_grants_access(self):
        response = self.client.post('/login', data={'username': 'huzaifa', 'password': 'admin123'}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(ADMIN_PATH, response.headers.get('Location', ''))

    def test_owner_can_grant_admin_access(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'huzaifa'
        username = f"test_admin_{uuid.uuid4().hex[:8]}"
        response = self.client.post(f'{ADMIN_PATH}/admins', data={
            'first_name': 'Amina',
            'last_name': 'Khan',
            'phone': '5550100',
            'username': username,
            'password': 'secure-password'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.client.get('/logout')
        response = self.client.post('/login', data={
            'username': username,
            'password': 'secure-password'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['admin_profile']['first_name'], 'Amina')
            self.assertEqual(sess['admin_profile']['last_name'], 'Khan')
            self.assertEqual(sess['admin_profile']['phone'], '5550100')

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
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Clinic Pro', 'North Spice'],
            'shop_url': ['https://clinic.example', 'https://spice.example'],
            'shop_type': ['Dental Clinic', 'South Indian Vegetarian'],
            'quiz_types': ['Dental Clinic', 'South Indian Vegetarian']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertEqual(cfg['shops'][0]['type'], 'Dental Clinic')
        self.assertEqual(cfg['shops'][1]['type'], 'South Indian Vegetarian')

    def test_admin_saves_multiple_types_for_each_business(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Clinic Pro', 'North Spice'],
            'shop_url': ['https://clinic.example', 'https://spice.example'],
            'shop_type_0': ['Dental Clinic', 'Gym'],
            'shop_type_1': ['South Indian Vegetarian', 'Biryani Shop'],
            'quiz_types': ['Dental Clinic', 'Gym', 'South Indian Vegetarian', 'Biryani Shop']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertEqual(cfg['shops'][0]['types'], ['Dental Clinic', 'Gym'])
        self.assertEqual(cfg['shops'][1]['types'], ['South Indian Vegetarian', 'Biryani Shop'])
        self.assertEqual(cfg['shops'][0]['type'], 'Dental Clinic')

    def test_custom_quiz_type_can_be_added(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Custom Shop'],
            'shop_url': ['https://custom.example'],
            'shop_type_0': ['Car Wash'],
            'quiz_types': ['Dental Clinic', 'Gym'],
            'custom_quiz_types': ['Car Wash, Bike Accessories']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertIn('Car Wash', cfg['quiz_types'])
        self.assertIn('Bike Accessories', cfg['quiz_types'])

    def test_database_is_initialized_and_persisted(self):
        init_db()
        conn = get_db_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('businesses', 'quiz_types') ORDER BY name").fetchall()
        self.assertEqual([row[0] for row in tables], ['businesses', 'quiz_types'])


if __name__ == '__main__':
    unittest.main()
