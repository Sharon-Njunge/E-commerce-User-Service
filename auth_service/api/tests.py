import json
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

class RegisterUserTests(TestCase):
    """Test user registration endpoint"""

    def setUp(self):
        self.register_url = reverse('api:register')
        self.valid_payload = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

    @patch('auth_service.api.views.get_management_token')
    @patch('auth_service.api.views.requests.post')
    def test_register_user_success(self, mock_post, mock_token):
        """Test successful user registration"""
        mock_token.return_value = 'fake_token'
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'id': 'auth0|123',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'preferences': {},
        }

        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertIn('user', response.json())

    def test_register_user_missing_fields(self):
        """Test registration with missing required fields"""
        invalid_payload = {'email': 'test@example.com'}

        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @patch('auth_service.api.views.get_management_token')
    def test_register_user_auth_failed(self, mock_token):
        """Test registration when Auth0 token fails"""
        mock_token.return_value = None

        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'Auth failed')


class ListUsersTests(TestCase):
    """Test list users endpoint"""

    def setUp(self):
        self.list_url = reverse('api:list_users')

    @patch('auth_service.api.views.get_management_token')
    @patch('auth_service.api.views.requests.get')
    def test_list_users_success(self, mock_get, mock_token):
        """Test successful users listing"""
        mock_token.return_value = 'fake_token'
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'user_id': 'auth0|123',
                'email': 'user1@example.com',
                'given_name': 'John',
                'family_name': 'Doe',
                'created_at': '2023-01-01T00:00:00Z'
            },
            {
                'user_id': 'auth0|456',
                'email': 'user2@example.com',
                'given_name': 'Jane',
                'family_name': 'Smith',
                'created_at': '2023-01-02T00:00:00Z'
            }
        ]

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.json())
        self.assertEqual(len(response.json()['users']), 2)

    @patch('auth_service.api.views.get_management_token')
    def test_list_users_auth_failed(self, mock_token):
        """Test listing users when Auth0 token fails"""
        mock_token.return_value = None

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'Auth failed')


class GetProfileTests(TestCase):
    """Test get profile endpoint"""

    def setUp(self):
        self.profile_url = reverse('api:get_profile')

    def test_get_profile_success(self):
        """Test successful profile retrieval"""
        session = self.client.session
        session['user'] = {
            'userinfo': {
                'id': 'auth0|123',
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'preferences': {},
            }
        }
        session.save()

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['id'], 'auth0|123')

    def test_get_profile_not_authenticated(self):
        """Test getting profile when not authenticated"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Not authenticated')


class UpdateProfileTests(TestCase):
    """Test update profile endpoint"""

    def setUp(self):
        self.update_url = reverse('api:update_profile')
        self.valid_payload = {
            'first_name': 'Jane',
            'last_name': 'Smith',
        }
    @patch('auth_service.api.views.get_management_token')
    @patch('auth_service.api.views.requests.patch')
    def test_update_profile_success(self, mock_patch, mock_token):
        """Test successful profile update"""
        session = self.client.session
        session['user'] = {
            'userinfo': {
                'id': 'auth0|123',
                'email': 'test@example.com'
            }
        }
        session.save()

        mock_token.return_value = 'fake_token'
        mock_patch.return_value.status_code = 200

        response = self.client.put(
            self.update_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Updated successfully')

    def test_update_profile_not_authenticated(self):
        """Test updating profile when not authenticated"""
        response = self.client.put(
            self.update_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Not authenticated')

    @patch('auth_service.api.views.get_management_token')
    def test_update_profile_auth_failed(self, mock_token):
        """Test updating profile when Auth0 token fails"""
        session = self.client.session
        session['user'] = {
            'userinfo': {
                'sub': 'auth0|123',
                'email': 'test@example.com'
            }
        }
        session.save()

        mock_token.return_value = None

        response = self.client.put(
            self.update_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'Auth failed')