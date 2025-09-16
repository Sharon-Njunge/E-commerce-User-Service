import json

from django.test import TestCase, tag
from rest_framework.test import APIClient


class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_profile_success(self):
        """Test GET profile with valid session"""
        session = self.client.session
        session["user"] = {
            "userinfo": {
                "sub": "auth0|123456",
                "email": "test@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "preferences": {"theme": "dark"},
            }
        }
        session.save()

        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], "auth0|123456")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["firstName"], "John")
        self.assertEqual(data["lastName"], "Doe")
        self.assertEqual(data["preferences"], {"theme": "dark"})

    def test_update_profile_success(self):
        """Test PUT profile update with valid data"""
        session = self.client.session
        session["user"] = {
            "userinfo": {
                "sub": "auth0|123456",
                "email": "test@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "preferences": {},
            }
        }
        session.save()

        update_data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "preferences": {"theme": "light"},
        }

        response = self.client.put(
            "/api/profile/update/",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Profile updated successfully")

        # Check session was updated
        updated_session = self.client.session
        userinfo = updated_session["user"]["userinfo"]
        self.assertEqual(userinfo["given_name"], "Jane")
        self.assertEqual(userinfo["family_name"], "Smith")
        self.assertEqual(userinfo["preferences"], {"theme": "light"})

    def test_signup(self):
        """Test POST signup returns Auth0 signup URL"""
        response = self.client.post("/api/signup/")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("signup_url", data)
        self.assertIn("https://", data["signup_url"])
        self.assertIn("screen_hint=signup", data["signup_url"])
        self.assertEqual(data["message"], "Redirect to this URL to complete signup")

    @tag("integration")
    def test_session_persistence_across_replicas(self):
        """Test that sessions work with multiple replicas"""
        # Simulate user session
        session = self.client.session
        session["user"] = {
            "userinfo": {
                "sub": "auth0|scaling_test",
                "email": "scaling@test.com",
                "given_name": "Scale",
                "family_name": "Test",
                "preferences": {"scaling": True},
            }
        }
        session.save()

        # Test profile retrieval works with session
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["email"], "scaling@test.com")
        self.assertEqual(data["firstName"], "Scale")
        self.assertEqual(data["lastName"], "Test")
        self.assertEqual(data["preferences"], {"scaling": True})

        # Test profile update works across replicas
        update_data = {"preferences": {"scaling": True, "replicas": 3}}
        response = self.client.put(
            "/api/profile/update/",
            data=json.dumps(update_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
