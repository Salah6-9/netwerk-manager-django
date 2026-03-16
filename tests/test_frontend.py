from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class FrontendSmokeTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_test",
            password="testpass123"
        )

        self.employee = User.objects.create_user(
            username="employee_test",
            password="testpass123"
        )

    def test_dashboard_requires_login(self):
        """Dashboard يجب أن يعيد redirect بدون تسجيل دخول"""
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_for_admin(self):
        """Admin يستطيع الوصول للـ Dashboard"""
        self.client.force_login(self.admin)
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_stats_htmx_endpoint(self):
        """HTMX endpoint الخاص بالـ Dashboard يعمل"""
        self.client.force_login(self.admin)
        response = self.client.get("/dashboard/stats/")
        self.assertEqual(response.status_code, 200)

    def test_notifications_counter_endpoint(self):
        """Endpoint عداد الإشعارات يعمل"""
        self.client.force_login(self.admin)
        response = self.client.get("/notifications/count/")
        self.assertEqual(response.status_code, 200)

    def test_metrics_api_requires_login(self):
        """Metrics API يجب أن يكون محمي"""
        response = self.client.get("/api/device-metrics/1/")
        self.assertEqual(response.status_code, 302)

    def test_metrics_api_rbac(self):
        """الموظف لا يرى بيانات جهاز لا يملكه"""
        self.client.force_login(self.employee)
        response = self.client.get("/api/device-metrics/999/")
        self.assertIn(response.status_code, [403, 404])
