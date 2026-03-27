from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Report, Notification, Category

User = get_user_model()


def get_token(client, username, password):
    res = client.post('/api/users/login/', {
        'username': username,
        'password': password
    })
    return res.data.get('token') or res.data.get('access')


# ─── AUTH TESTS ────────────────────────────────────────
class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        res = self.client.post('/api/users/register/', {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        print("✅ test_register passed")

    def test_login_returns_token(self):
        User.objects.create_user(
            username='loginuser', password='test1234', email='login@test.com'
        )
        res = self.client.post('/api/users/login/', {
            'username': 'loginuser',
            'password': 'test1234'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in res.data or 'access' in res.data)
        print("✅ test_login_returns_token passed")

    def test_login_wrong_password(self):
        User.objects.create_user(
            username='wronguser', password='correct123', email='w@test.com'
        )
        res = self.client.post('/api/users/login/', {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertNotEqual(res.status_code, status.HTTP_200_OK)
        print("✅ test_login_wrong_password passed")

    def test_unauthenticated_cannot_access_profile(self):
        res = self.client.get('/api/users/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        print("✅ test_unauthenticated_cannot_access_profile passed")


# ─── REPORT TESTS ──────────────────────────────────────
class ReportTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.citizen = User.objects.create_user(
            username='citizen1', password='test1234',
            email='citizen@test.com', role='citizen'
        )
        self.citizen2 = User.objects.create_user(
            username='citizen2', password='test1234',
            email='citizen2@test.com', role='citizen'
        )
        self.admin = User.objects.create_user(
            username='admin1', password='test1234',
            email='admin@test.com', role='admin'
        )
        self.technician = User.objects.create_user(
            username='tech1', password='test1234',
            email='tech@test.com', role='technician'
        )
        token = get_token(self.client, 'citizen1', 'test1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_report(self):
        res = self.client.post('/api/reports/', {
            'title': 'Nid de poule',
            'description': 'Grand trou dans la route',
            'category_type': 'pothole',
            'severity': 'high',
            'latitude': 30.42,
            'longitude': -9.59,
            'quartier': 'Hay Mohammadi'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], 'Nid de poule')
        print("✅ test_create_report passed")

    def test_critical_auto_set_when_severity_high(self):
        res = self.client.post('/api/reports/', {
            'title': 'Fuite grave',
            'description': 'Très grave',
            'category_type': 'water',
            'severity': 'high',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_critical'])
        print("✅ test_critical_auto_set passed")

    def test_citizen_sees_only_own_reports(self):
        # Citizen1 creates report
        self.client.post('/api/reports/', {
            'title': 'Mon rapport',
            'description': 'Test',
            'category_type': 'waste',
            'severity': 'low',
        })
        # Citizen2 creates report
        token2 = get_token(self.client, 'citizen2', 'test1234')
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        client2.post('/api/reports/', {
            'title': 'Rapport citizen2',
            'description': 'Test2',
            'category_type': 'lighting',
            'severity': 'medium',
        })
        # Citizen1 should only see own reports
        res = self.client.get('/api/reports/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for report in res.data:
            self.assertEqual(report['user_username'], 'citizen1')
        print("✅ test_citizen_sees_only_own_reports passed")

    def test_admin_sees_all_reports(self):
        self.client.post('/api/reports/', {
            'title': 'Rapport C1',
            'description': 'Test',
            'category_type': 'waste',
            'severity': 'low',
        })
        admin_token = get_token(self.client, 'admin1', 'test1234')
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        res = admin_client.get('/api/reports/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        print("✅ test_admin_sees_all_reports passed")

    def test_unauthenticated_blocked(self):
        self.client.credentials()
        res = self.client.get('/api/reports/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        print("✅ test_unauthenticated_blocked passed")

    def test_filter_by_status(self):
        self.client.post('/api/reports/', {
            'title': 'Test filter',
            'description': 'Test',
            'category_type': 'pothole',
            'severity': 'low',
        })
        res = self.client.get('/api/reports/?status=pending')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        print("✅ test_filter_by_status passed")

    def test_statistics_endpoint(self):
        admin_token = get_token(self.client, 'admin1', 'test1234')
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        res = admin_client.get('/api/reports/statistics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_reports', res.data)
        self.assertIn('by_category', res.data)
        self.assertIn('by_severity', res.data)
        print("✅ test_statistics_endpoint passed")


# ─── NOTIFICATION TESTS ────────────────────────────────
class NotificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='notifuser', password='test1234',
            email='notif@test.com', role='citizen'
        )
        token = get_token(self.client, 'notifuser', 'test1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_notifications_list(self):
        res = self.client.get('/api/reports/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        print("✅ test_notifications_list passed")

    def test_mark_notification_read(self):
        notif = Notification.objects.create(
            user=self.user,
            type='new_report',
            message='Test notification'
        )
        res = self.client.post(f'/api/reports/notifications/{notif.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        print("✅ test_mark_notification_read passed")


# ─── AI TESTS ──────────────────────────────────────────
class AITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='aiuser', password='test1234',
            email='ai@test.com', role='citizen'
        )
        token = get_token(self.client, 'aiuser', 'test1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_ai_analyze_mock(self):
        res = self.client.post('/api/reports/ai/analyze/', {
            'use_real_model': False
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('problem_type', res.data)
        self.assertIn('severity', res.data)
        self.assertIn('confidence', res.data)
        print("✅ test_ai_analyze_mock passed")

    def test_ai_analyze_saves_to_report(self):
        report_res = self.client.post('/api/reports/', {
            'title': 'Test AI',
            'description': 'Test',
            'category_type': 'pothole',
            'severity': 'low',
        })
        self.assertEqual(report_res.status_code, status.HTTP_201_CREATED)
        report_id = report_res.data['id']

        res = self.client.post('/api/reports/ai/analyze/', {
            'report_id': report_id,
            'use_real_model': False
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        detail = self.client.get(f'/api/reports/{report_id}/')
        self.assertIsNotNone(detail.data['ai_analysis'])
        print("✅ test_ai_analyze_saves_to_report passed")