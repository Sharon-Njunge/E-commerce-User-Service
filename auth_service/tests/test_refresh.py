import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.refresh_url = reverse('token-refresh')

    @patch('auth_service.api.views.requests.post')
    def test_refresh_token_success(self, mock_post):
        """Test successful token refresh"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }
        mock_post.return_value = mock_response

        refresh_payload = {
            'refresh_token': 'valid_refresh_token'
        }

        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('expires_in', response.data)

    @patch('auth_service.api.views.requests.post')
    def test_refresh_token_invalid_refresh_token(self, mock_post):
        """Test token refresh fails with invalid refresh token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Invalid refresh token'
        }
        mock_post.return_value = mock_response

        refresh_payload = {
            'refresh_token': 'invalid_refresh_token'
        }

        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    @patch('auth_service.api.views.requests.post')
    def test_refresh_token_expired_refresh_token(self, mock_post):
        """Test token refresh fails with expired refresh token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Refresh token expired'
        }
        mock_post.return_value = mock_response

        refresh_payload = {
            'refresh_token': 'expired_refresh_token'
        }

        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_missing_refresh_token(self):
        """Test token refresh fails with missing refresh token"""
        refresh_payload = {} 

        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)