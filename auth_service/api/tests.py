
import pytest
import requests
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from auth_service.api.utils import call_auth0  # Fixed import path
from auth_service.api.constants import HTTP_200_OK
import json
from django.test import TestCase, Client
from auth_service.users.models import UserProfile

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

@pytest.mark.django_db
def test_retry_logic_success_after_failures():
    # Mock requests.get to fail twice then succeed
    with patch("auth_service.api.utils.requests.get") as mock_get:  # Fixed import path
        mock_get.side_effect = [
            requests.exceptions.RequestException("fail 1"),
            requests.exceptions.RequestException("fail 2"),
            type(
                "Response",
                (),
                {
                    "raise_for_status": lambda self: None,
                    "json": lambda self: {"ok": True},
                },
            )(),
        ]

        result = call_auth0("https://fake-auth0.com")
        assert result == {"ok": True}
        assert mock_get.call_count == 3
class AuthTests(TestCase):
    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.user = UserProfile.objects.create(
            auth0_user_id="test-user-123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            preferences={"theme": "dark"},
        )

    def test_get_profile_success(self):
        """Test getting a user profile."""
        response = self.client.get("/api/profile/test-user-123/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["firstName"], "John")

    def test_get_profile_not_found(self):
        """Test getting non-existent user."""
        response = self.client.get("/api/profile/fake-user/")
        self.assertEqual(response.status_code, 404)

    def test_update_profile(self):
        """Test updating a profile."""
        update_data = {"firstName": "Jane", "lastName": "Smith"}

        response = self.client.post(
            "/api/profile/test-user-123/update/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        # Check database was updated
        updated_user = UserProfile.objects.get(auth0_user_id="test-user-123")
        self.assertEqual(updated_user.first_name, "Jane")

    def test_list_users(self):
        """Test listing all users."""
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["users"]), 1)

    def test_profile_no_session(self):
        """Test profile endpoint without login."""
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, 401)

    def test_index_page(self):
        """Test index page loads."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
