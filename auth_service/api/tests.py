import json
from django.test import TestCase, Client
from auth_service.users.models import UserProfile


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
