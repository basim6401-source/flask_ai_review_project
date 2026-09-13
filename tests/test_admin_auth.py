import unittest
import uuid

from app import ADMIN_PATH, AVAILABLE_TYPES, app, load_config, init_db, get_db_connection


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
        self.assertNotIn(b'Admin sign in', response.data)

    def test_authenticated_admin_home_has_no_admin_link(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.get('/')
        self.assertNotIn(b'Admin settings', response.data)
        self.assertNotIn(b'Admin sign in', response.data)

    def test_home_page_does_not_expose_business_type(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'DEFAULT_TYPE', response.data)
        self.assertNotIn(b'name="type"', response.data)
        self.assertNotIn(b'businessSelect', response.data)

    def test_admin_can_update_google_review_url(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        review_url = 'https://search.google.com/local/writereview?placeid=custom-place'
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Test Shop'],
            'shop_url': ['https://test.example'],
            'google_review_url': review_url
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/generate')
        self.assertEqual(response.get_json()['google_url'], review_url)

    def test_business_has_its_own_google_review_url(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        review_url = 'https://search.google.com/local/writereview?placeid=business-place'
        self.client.post(ADMIN_PATH, data={
            'shop_name': ['Business A'],
            'shop_url': ['https://business.example'],
            'shop_google_review_url': [review_url]
        })
        response = self.client.get('/generate?shop=Business%20A')
        self.assertEqual(response.get_json()['google_url'], review_url)

    def test_admin_page_only_exposes_business_review_url_fields(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.get(ADMIN_PATH)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="shop_google_review_url"', response.data)
        self.assertNotIn(b'id="googleReviewUrl"', response.data)

    def test_admin_page_has_existing_business_profiles_button(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.get(ADMIN_PATH)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Existing Business Profiles', response.data)
        self.assertIn(b'id="existingProfiles"', response.data)

    def test_business_directory_controls_quiz_types(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Directory Shop'],
            'shop_url': ['https://directory.example'],
            'shop_type_0': ['Dental Clinic', 'Gym'],
            'shop_google_review_url': ['https://search.google.com/local/writereview?placeid=directory']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertEqual(cfg['shops'][0]['types'], ['Dental Clinic', 'Gym'])
        self.assertIn('Dental Clinic', cfg['quiz_types'])
        self.assertIn('Gym', cfg['quiz_types'])
        page = self.client.get(ADMIN_PATH)
        self.assertNotIn(b'Quiz Types (select one or more)', page.data)

    def test_business_directory_can_save_without_business_url_field(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Name Only Business'],
            'shop_google_review_url': ['https://search.google.com/local/writereview?placeid=name-only']
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cfg = load_config()
        self.assertEqual(cfg['shops'][0]['name'], 'Name Only Business')
        self.assertEqual(cfg['shops'][0]['url'], '')

    def test_multiple_businesses_have_independent_google_review_urls(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        first_url = 'https://search.google.com/local/writereview?placeid=first-place'
        second_url = 'https://search.google.com/local/writereview?placeid=second-place'
        self.client.post(ADMIN_PATH, data={
            'shop_name': ['Business A', 'Business B'],
            'shop_url': ['https://first.example', 'https://second.example'],
            'shop_google_review_url': [first_url, second_url]
        })

        first_response = self.client.get('/generate?shop=Business%20A')
        second_response = self.client.get('/generate?shop=Business%20B')
        self.assertEqual(first_response.get_json()['google_url'], first_url)
        self.assertEqual(second_response.get_json()['google_url'], second_url)

    def test_business_directory_update_and_delete_actions(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        self.client.post(ADMIN_PATH, data={
            'shop_name': ['Business A', 'Business B'],
            'shop_url': ['https://first.example', 'https://second.example'],
            'shop_google_review_url': ['', ''],
            'directory_action': 'update:0'
        })
        self.assertEqual(load_config()['shops'][0]['name'], 'Business A')

        response = self.client.post(ADMIN_PATH, data={
            'shop_name': ['Business A', 'Business B'],
            'shop_url': ['https://first.example', 'https://second.example'],
            'shop_google_review_url': ['', ''],
            'directory_action': 'delete:0'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(load_config()['shops'][0]['name'], 'Business B')

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

    def test_owner_can_delete_granted_admin_access(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'huzaifa'
        username = f"delete_admin_{uuid.uuid4().hex[:8]}"
        self.client.post(f'{ADMIN_PATH}/admins', data={
            'first_name': 'Delete',
            'last_name': 'Me',
            'phone': '5550101',
            'username': username,
            'password': 'secure-password'
        })
        response = self.client.post(f'{ADMIN_PATH}/admins/delete', data={'username': username}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.client.get('/logout')
        response = self.client.post('/login', data={
            'username': username,
            'password': 'secure-password'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_owner_admin_access_cannot_be_deleted(self):
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'huzaifa'
        response = self.client.post(f'{ADMIN_PATH}/admins/delete', data={'username': 'huzaifa'}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('owner', response.headers.get('Location', ''))

    def test_generate_review_matches_business_type(self):
        response = self.client.get('/generate?type=Dental%20Clinic')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('reviews'))
        review_text = ' '.join(data['reviews']).lower()
        self.assertTrue(any(keyword in review_text for keyword in ['clinic', 'dental', 'teeth', 'treatment', 'check-up', 'cleaning']))
        self.assertNotIn('food', review_text)

    def test_home_improvement_quiz_types_are_available(self):
        new_types = [
            'Ceramic Tiles', 'Kitchen Accessories', 'Washroom Accessories',
            'Plumber Shop', 'Tools Shop', 'Sanitaryware Shop',
            'Bathroom Fittings', 'Hardware Shop', 'Electrical Shop',
            'Paint Shop', 'Flooring Shop', 'Modular Kitchen',
            'Building Materials', 'Plywood Shop', 'Lighting Shop'
        ]
        for quiz_type in new_types:
            self.assertIn(quiz_type, AVAILABLE_TYPES)
            response = self.client.get(f'/generate?type={quiz_type.replace(" ", "%20")}')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json().get('reviews'))

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
