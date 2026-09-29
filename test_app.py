import sys
import unittest
from app import app
from aws_config import aws_mgr

class TravelGoTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TravelGo', response.data)
        self.assertIn(b'Bus', response.data)

    def test_02_search_bus(self):
        response = self.client.get('/search?type=bus&source=Hyderabad&destination=Bangalore')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'VRL Travels', response.data)

    def test_03_bus_seats(self):
        response = self.client.get('/bus/BUS-101/seats')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'L01', response.data)

    def test_04_hotel_details(self):
        response = self.client.get('/hotel/HTL-001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The Grand Palace Resort', response.data)

    def test_05_login_and_dashboard(self):
        # Login with demo credentials
        res = self.client.post('/auth/login', data={
            'email': 'demo@travelgo.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Personal Travel History', res.data)

    def test_06_complete_booking_flow_and_sns(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'demo@travelgo.com'
            sess['user_name'] = 'Alex Morgan'

        # Submit booking
        response = self.client.post('/booking/process', data={
            'type': 'bus',
            'source': 'Hyderabad',
            'destination': 'Bangalore',
            'date': '2026-10-15',
            'seat': 'L-08 (Window)',
            'details': 'VRL Travels • Multi-Axle Volvo',
            'price': '1312.50',
            'payment_method': 'UPI / Google Pay'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking Confirmed!', response.data)
        self.assertIn(b'AWS SNS Real-Time Email Triggered', response.data)

    def test_07_sns_api_test(self):
        response = self.client.post('/api/sns-test')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['sent'])
        self.assertIn('AWS SNS', data['provider'])

if __name__ == '__main__':
    unittest.main()
