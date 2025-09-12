from django.test import TestCase

# Create your tests here.

from django.test import TestCase
from rest_framework.test import APIClient

class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_users_endpoint_requires_auth(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 401)  # No token, should fail
