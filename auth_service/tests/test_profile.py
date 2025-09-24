import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from auth_service.users.models import UserProfile
import jwt
import time


class UserProfileTests(APITestCase):
    def setUp(self):
        self.profile_url = reverse('user-profile')
        self.update_profile_url = reverse('user-profile-update')
        
        # Create a test user
        self.user = UserProfile.objects.create(
            email='test@example.com',
            auth0_user_id='auth0|123456789',
            first_name='John',
            last_name='Doe'
        )
        
        # Create a valid JWT token for testing
        self.valid_token = self._create_valid_jwt_token()

    def _create_valid_jwt_token(self):
        """Helper method to create a valid JWT token"""
        payload = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com',
            'exp': time.time() + 3600,  # 1 hour from now
            'iat': time.time(),
            'iss': 'https://your-domain.auth0.com/'
        }
        # This is a mock token - in real tests, you'd use your actual JWT signing
        return 'mock_valid_jwt_token'

    def _create_expired_jwt_token(self):
        """Helper method to create an expired JWT token"""
        payload = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com',
            'exp': time.time() - 3600,  # 1 hour ago
            'iat': time.time() - 7200,
            'iss': 'https://your-domain.auth0.com/'
        }
        return 'mock_expired_jwt_token'

    @patch('auth_service.users.auth.verify_token')
    def test_get_profile_success(self, mock_verify_token):
        """Test successful profile retrieval with valid token"""
        # Mock token verification
        mock_verify_token.return_value = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com'
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.valid_token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)

    def test_get_profile_no_token(self):
        """Test profile retrieval fails without token"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('auth_service.users.auth.verify_token')
    def test_get_profile_invalid_token(self, mock_verify_token):
        """Test profile retrieval fails with invalid token"""
        # Mock token verification failure
        mock_verify_token.side_effect = Exception('Invalid token')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('auth_service.users.auth.verify_token')
    def test_get_profile_expired_token(self, mock_verify_token):
        """Test profile retrieval fails with expired token"""
        # Mock token verification for expired token
        mock_verify_token.side_effect = jwt.ExpiredSignatureError('Token expired')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._create_expired_jwt_token()}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('auth_service.users.auth.verify_token')
    def test_update_profile_success(self, mock_verify_token):
        """Test successful profile update with valid token"""
        # Mock token verification
        mock_verify_token.return_value = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com'
        }

        update_data = {
            'first_name': 'Jane',
            'last_name': 'Smith'
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.valid_token}')
        response = self.client.patch(self.update_profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['last_name'], 'Smith')
        
        # Verify the user was updated in database
        updated_user = UserProfile.objects.get(id=self.user.id)
        self.assertEqual(updated_user.first_name, 'Jane')
        self.assertEqual(updated_user.last_name, 'Smith')

    @patch('auth_service.users.auth.verify_token')
    def test_update_profile_partial_data(self, mock_verify_token):
        """Test successful profile update with partial data"""
        # Mock token verification
        mock_verify_token.return_value = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com'
        }

        update_data = {
            'first_name': 'Jane'  # Only update first name
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.valid_token}')
        response = self.client.patch(self.update_profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['last_name'], 'Doe')  # Should remain unchanged

    @patch('auth_service.users.auth.verify_token')
    def test_update_profile_invalid_data(self, mock_verify_token):
        """Test profile update fails with invalid data"""
        # Mock token verification
        mock_verify_token.return_value = {
            'sub': 'auth0|123456789',
            'email': 'test@example.com'
        }

        invalid_data = {
            'email': 'invalid-email-format'  # Invalid email format
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.valid_token}')
        response = self.client.patch(self.update_profile_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('auth_service.users.auth.verify_token')
    def test_update_profile_nonexistent_user(self, mock_verify_token):
        """Test profile update fails for non-existent user"""
        # Mock token verification for user that doesn't exist in our DB
        mock_verify_token.return_value = {
            'sub': 'auth0|nonexistent',
            'email': 'nonexistent@example.com'
        }

        update_data = {
            'first_name': 'Jane'
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.valid_token}')
        response = self.client.patch(self.update_profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)