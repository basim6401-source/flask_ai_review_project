import unittest

from app import app


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


if __name__ == '__main__':
    unittest.main()
