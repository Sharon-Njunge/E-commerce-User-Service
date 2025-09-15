
# Create your tests here.

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status
import json

User = get_user_model()


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/register/'

    def test_register_user_success(self):
        """Test successful user registration"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'firstName': 'John',
            'lastName': 'Doe'
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['firstName'], 'John')
        self.assertEqual(response.data['lastName'], 'Doe')
        self.assertTrue(User.objects.filter(email='test@example.com').exists())


class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_users_endpoint_requires_auth(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 401)  # No token, should fail



class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_url = '/api/profile/'
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def _create_session_with_user(self, user_data):
        """Helper method to create session with user data"""
        session = self.client.session
        session['user'] = {
            'userinfo': user_data
        }
        session.save()

    def test_get_profile_success(self):
        """Test getting user profile with valid session"""
        user_data = {
            'sub': 'auth0|123456',
            'email': 'test@example.com',
            'given_name': 'John',
            'family_name': 'Doe'
        }
        self._create_session_with_user(user_data)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['firstName'], 'John')
        self.assertEqual(response.data['lastName'], 'Doe')
        self.assertEqual(response.data['id'], 'auth0|123456')

    def test_update_profile_success(self):
        """Test updating user profile successfully"""
        user_data = {
            'id': 'auth0|123456',
            'email': 'test@example.com',
            'firstName': 'John',
            'lastName': 'Doe'
        }
        self._create_session_with_user(user_data)

        update_data = {
            'firstName': 'Jane',
            'lastName': 'Smith'
        }
        response = self.client.put(
            self.profile_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['firstName'], 'Jane')
        self.assertEqual(response.data['lastName'], 'Smith')


