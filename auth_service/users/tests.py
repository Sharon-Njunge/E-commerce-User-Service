from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_users_endpoint_requires_auth(self):
        url = reverse("users-list")  # assumes you registered a DRF router
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)  # No token → should fail
