import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from auth_service.users.models import UserProfile

User = get_user_model()


class UserRegistrationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('user-register')
        self.valid_payload = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'auth0_user_id': 'auth0|123456789'
        }

    @patch('auth_service.api.views.auth0_management_get_user')
    @patch('auth_service.api.views.auth0_management_create_user')
    def test_register_new_user_success(self, mock_create_user, mock_get_user):
        """Test successful user registration"""
        mock_get_user.return_value = None  
        mock_create_user.return_value = {
            'user_id': 'auth0|123456789',
            'email': 'test@example.com'
        }

        response = self.client.post(self.register_url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        
        self.assertTrue(UserProfile.objects.filter(email='test@example.com').exists())

    @patch('auth_service.api.views.auth0_management_get_user')
    def test_register_duplicate_email(self, mock_get_user):
        """Test registration fails with duplicate email"""
        UserProfile.objects.create(
            email='test@example.com',
            auth0_user_id='auth0|existinguser',
            first_name='Existing',
            last_name='User'
        )

        mock_get_user.return_value = None

        response = self.client.post(self.register_url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('email', response.data)

    def test_register_missing_required_fields(self):
        """Test registration fails with missing required fields"""
        invalid_payload = {
            'first_name': 'John',
            'last_name': 'Doe'
        }

        response = self.client.post(self.register_url, invalid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('auth_service.api.views.auth0_management_get_user')
    @patch('auth_service.api.views.auth0_management_create_user')
    def test_register_invalid_email_format(self, mock_create_user, mock_get_user):
        """Test registration fails with invalid email format"""
        mock_get_user.return_value = None
        
        invalid_payload = {
            'email': 'invalid-email',
            'first_name': 'John',
            'last_name': 'Doe',
            'auth0_user_id': 'auth0|123456789'
        }

        response = self.client.post(self.register_url, invalid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    @patch('auth_service.api.views.auth0_management_get_user')
    def test_register_auth0_user_already_exists(self, mock_get_user):
        """Test registration fails when Auth0 user already exists"""
        mock_get_user.return_value = {
            'user_id': 'auth0|existinguser',
            'email': 'test@example.com'
        }

        response = self.client.post(self.register_url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('auth0_user_id', response.data)