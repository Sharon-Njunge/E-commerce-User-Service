import pytest
import os
from django.test import TestCase
from unittest.mock import patch, MagicMock
from tests.mocks.auth0_mock import mock_auth0, MockAuth0
from tests.mocks.email_mock import mock_email_service, MockEmailService

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    # Mock environment variables
    with patch.dict(os.environ, {
        'AUTH0_DOMAIN': 'mock-auth0.com',
        'AUTH0_CLIENT_ID': 'mock-client-id',
        'AUTH0_CLIENT_SECRET': 'mock-client-secret',
        'API_IDENTIFIER': 'mock-api-identifier',
        'ALGORITHMS': 'RS256'
    }):
        yield

@pytest.fixture
def auth0_mock():
    """Provide a fresh Auth0 mock instance for each test"""
    mock_instance = MockAuth0()
    
    with patch('auth_service.users.auth.Auth0JSONWebTokenAuthentication._get_jwks') as mock_jwks:
        with patch('auth_service.views.oauth') as mock_oauth:
            # Mock JWKS endpoint
            mock_jwks.return_value = mock_instance.get_jwks()['keys']
            
            # Mock OAuth client
            mock_oauth_client = MagicMock()
            mock_oauth.auth0 = mock_oauth_client
            mock_oauth_client.authorize_access_token.return_value = {
                'userinfo': mock_instance.users.get('test-user-id', {})
            }
            
            yield mock_instance

@pytest.fixture
def email_mock():
    """Provide a fresh email mock instance for each test"""
    mock_instance = MockEmailService()
    
    with patch('auth_service.api.views.email_service', mock_instance):
        with patch('auth_service.users.auth.email_service', mock_instance):
            yield mock_instance

@pytest.fixture
def authenticated_user(auth0_mock):
    """Create and authenticate a test user"""
    user_data = auth0_mock.create_user(
        user_id="test-user-123",
        email="test@example.com",
        given_name="Test",
        family_name="User",
        preferences={"theme": "dark"}
    )
    
    access_token = auth0_mock.issue_token("test-user-123")
    refresh_token = auth0_mock.issue_token("test-user-123", token_type="refresh")
    
    return {
        'user_data': user_data,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'auth0_mock': auth0_mock
    }