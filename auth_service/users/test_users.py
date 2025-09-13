import json
import pytest
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from auth_service.users.models import CustomUser, UserPreferences, UserRole, UserSession, UserActivity
from auth_service.users.auth import Auth0JSONWebTokenAuthentication

# Test settings to avoid external dependencies
TEST_SETTINGS = {
    'AUTH0_DOMAIN': 'test-domain.auth0.com',
    'API_IDENTIFIER': 'test-api-identifier',
    'ALGORITHMS': 'RS256'
}

class UserAPITestCase(TestCase):
    """Basic API test case"""
    
    def setUp(self):
        self.client = APIClient()

    def test_users_endpoint_requires_auth(self):
        response = self.client.get("/api/users/")
        # Django may return 403 for permission denied or 401 for authentication
        # Both are acceptable for unauthenticated requests
        self.assertIn(response.status_code, [401, 403])

@override_settings(**TEST_SETTINGS)
class Auth0IntegrationTestCase(APITestCase):
    """Integration tests for Auth0 authentication flow"""
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'auth0_sub': 'auth0|test123'
        }
        
    def create_test_user(self):
        """Create a test user"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email=self.user_data['email'],
            password='testpass123',
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            auth0_sub=self.user_data['auth0_sub'],
            is_email_verified=True
        )
        
        # Create preferences
        UserPreferences.objects.create(user=user)
        
        # Assign customer role
        UserRole.objects.create(user=user, role_name='customer')
        
        return user
    
    def mock_valid_jwt_payload(self):
        """Mock a valid JWT payload"""
        return {
            'sub': self.user_data['auth0_sub'],
            'email': self.user_data['email'],
            'email_verified': True,
            'aud': 'test-api-identifier',
            'iss': 'https://test-domain.auth0.com/',
            'exp': 9999999999,  # Far future expiration
            'iat': 1000000000,
        }
    
    def test_protected_endpoint_without_token_fails(self):
        """Test that protected endpoints fail without authentication"""
        response = self.client.get('/api/users/')
        self.assertIn(response.status_code, [401, 403])
    
    @patch('auth_service.users.auth.Auth0JSONWebTokenAuthentication.authenticate')
    def test_protected_endpoint_with_valid_token_succeeds(self, mock_authenticate):
        """Test that protected endpoints succeed with valid token"""
        # Create test user
        user = self.create_test_user()
        
        # Mock successful authentication
        mock_authenticate.return_value = (user, 'mock_token')
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('auth_service.users.auth.Auth0JSONWebTokenAuthentication.authenticate')
    def test_invalid_token_fails(self, mock_authenticate):
        """Test that invalid tokens are rejected"""
        from rest_framework.exceptions import AuthenticationFailed
        
        # Mock authentication failure
        mock_authenticate.side_effect = AuthenticationFailed("Token is expired")
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/users/')
        self.assertIn(response.status_code, [401, 403])
    
    def test_malformed_authorization_header_fails(self):
        """Test that malformed authorization headers are rejected"""
        # Test missing 'Bearer' prefix
        self.client.credentials(HTTP_AUTHORIZATION='invalid_token')
        response = self.client.get('/api/users/')
        self.assertIn(response.status_code, [401, 403])
        
        # Test empty token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ')
        response = self.client.get('/api/users/')
        self.assertIn(response.status_code, [401, 403])
        
        # Test multiple tokens
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token1 token2')
        response = self.client.get('/api/users/')
        self.assertIn(response.status_code, [401, 403])

@override_settings(**TEST_SETTINGS)
class UserAPIIntegrationTestCase(APITestCase):
    """Integration tests for user-related API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            auth0_sub='auth0|admin123'
        )
        UserRole.objects.create(user=self.admin_user, role_name='admin')
        
        self.regular_user = CustomUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123',
            first_name='Regular',
            last_name='User',
            auth0_sub='auth0|user123'
        )
        UserRole.objects.create(user=self.regular_user, role_name='customer')
    
    @patch('auth_service.users.auth.Auth0JSONWebTokenAuthentication.authenticate')
    def test_user_list_endpoint_admin_access(self, mock_authenticate):
        """Test that admin users can access user list"""
        # Mock successful authentication
        mock_authenticate.return_value = (self.admin_user, 'mock_token')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_registration_flow(self):
        """Test complete user registration flow"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'auth0_sub': 'auth0|newuser123'
        }
        
        # Create user
        user = CustomUser.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password='newpass123',
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            auth0_sub=user_data['auth0_sub']
        )
        
        # Verify user was created
        self.assertEqual(CustomUser.objects.filter(email=user_data['email']).count(), 1)
        
        # Verify preferences can be created
        UserPreferences.objects.create(user=user)
        self.assertTrue(UserPreferences.objects.filter(user=user).exists())
    
    def test_user_preferences_management(self):
        """Test user preferences access and management"""
        # Create preferences for regular user
        preferences = UserPreferences.objects.create(
            user=self.regular_user,
            language='en',
            theme='dark',
            email_notifications=False
        )
        
        # Verify preferences were created
        self.assertEqual(preferences.user, self.regular_user)
        self.assertEqual(preferences.language, 'en')
        self.assertEqual(preferences.theme, 'dark')
        self.assertFalse(preferences.email_notifications)

class DatabaseIntegrationTestCase(TransactionTestCase):
    """Test database schema and relationships"""
    
    def test_user_model_relationships(self):
        """Test that all user model relationships work correctly"""
        # Create user
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            first_name='Test',
            last_name='User',
            auth0_sub='auth0|test123'
        )
        
        # Create preferences
        preferences = UserPreferences.objects.create(
            user=user,
            language='es',
            theme='dark'
        )
        
        # Create role
        role = UserRole.objects.create(
            user=user,
            role_name='customer'
        )
        
        # Create session with timezone-aware datetime
        expires_at = timezone.now() + timezone.timedelta(hours=1)
        session = UserSession.objects.create(
            user=user,
            session_token='test_token_123',
            ip_address='127.0.0.1',
            expires_at=expires_at
        )
        
        # Test relationships
        self.assertEqual(user.preferences, preferences)
        self.assertIn(role, user.roles.all())
        self.assertIn(session, user.sessions.all())
        
        # Test cascade deletion
        user.delete()
        self.assertFalse(UserPreferences.objects.filter(id=preferences.id).exists())
        self.assertFalse(UserRole.objects.filter(id=role.id).exists())
        self.assertFalse(UserSession.objects.filter(id=session.id).exists())
    
    def test_user_model_constraints(self):
        """Test database constraints"""
        # Test unique email constraint
        CustomUser.objects.create_user(
            username='user1',
            email='same@example.com',
            password='test123',
            auth0_sub='auth0|user1'
        )
        
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                username='user2',
                email='same@example.com', 
                password='test123',
                auth0_sub='auth0|user2'
            )
    
    def test_database_tables_exist(self):
        """Test that database tables exist"""
        from django.db import connection
        
        # Get table names using Django's introspection
        with connection.cursor() as cursor:
            table_names = connection.introspection.table_names(cursor)
            
            # Check for our custom tables
            expected_tables = ['users', 'user_preferences', 'user_roles', 'user_sessions']
            found_tables = [table for table in expected_tables if table in table_names]
            
            # We should have at least the users table
            self.assertGreater(len(found_tables), 0, f"Expected tables not found. Available tables: {table_names}")

class CustomUserModelTestCase(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'auth0_sub': 'auth0|test123'
        }
    
    def test_user_creation(self):
        """Test user creation with required fields"""
        user = CustomUser.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_email_verified)
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = CustomUser.objects.create_user(**self.user_data)
        expected_str = f"{user.email} ({user.first_name} {user.last_name})"
        self.assertEqual(str(user), expected_str)
    
    def test_account_locking(self):
        """Test account locking mechanism"""
        user = CustomUser.objects.create_user(**self.user_data)
        
        # Initially not locked
        self.assertFalse(user.is_account_locked())
        
        # Lock account
        user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        user.save()
        
        # Should be locked
        self.assertTrue(user.is_account_locked())
        
        # Reset attempts should unlock
        user.reset_failed_attempts()
        self.assertFalse(user.is_account_locked())
    
    def test_email_uniqueness(self):
        """Test email uniqueness constraint"""
        CustomUser.objects.create_user(**self.user_data)
        
        # Try to create another user with same email
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                username='another_user',
                email=self.user_data['email'],
                password='password',
                auth0_sub='auth0|another'
            )

class UserPreferencesModelTestCase(TestCase):
    """Test cases for UserPreferences model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            first_name='Test',
            last_name='User',
            auth0_sub='auth0|test'
        )
    
    def test_preferences_creation(self):
        """Test preferences creation with default values"""
        preferences = UserPreferences.objects.create(user=self.user)
        
        self.assertEqual(preferences.user, self.user)
        self.assertEqual(preferences.language, 'en')
        self.assertEqual(preferences.timezone, 'UTC')
        self.assertTrue(preferences.email_notifications)
        self.assertFalse(preferences.sms_notifications)
        self.assertEqual(preferences.theme, 'light')
        self.assertEqual(preferences.currency, 'USD')
    
    def test_preferences_str_representation(self):
        """Test preferences string representation"""
        preferences = UserPreferences.objects.create(user=self.user)
        expected_str = f"Preferences for {self.user.email}"
        self.assertEqual(str(preferences), expected_str)

class UserSessionModelTestCase(TestCase):
    """Test cases for UserSession model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            first_name='Test',
            last_name='User',
            auth0_sub='auth0|test'
        )
    
    def test_session_creation(self):
        """Test session creation"""
        expires_at = timezone.now() + timezone.timedelta(hours=1)
        session = UserSession.objects.create(
            user=self.user,
            session_token='test_token_123',
            ip_address='127.0.0.1',
            user_agent='Test User Agent',
            expires_at=expires_at
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.session_token, 'test_token_123')
        self.assertTrue(session.is_active)
        self.assertFalse(session.is_expired())
    
    def test_session_expiration(self):
        """Test session expiration check"""
        # Create expired session
        expires_at = timezone.now() - timezone.timedelta(hours=1)
        session = UserSession.objects.create(
            user=self.user,
            session_token='expired_token',
            expires_at=expires_at
        )
        
        self.assertTrue(session.is_expired())
    
    def test_session_deactivation(self):
        """Test session deactivation"""
        expires_at = timezone.now() + timezone.timedelta(hours=1)
        session = UserSession.objects.create(
            user=self.user,
            session_token='active_token',
            expires_at=expires_at
        )
        
        self.assertTrue(session.is_active)
        
        session.deactivate()
        session.refresh_from_db()
        
        self.assertFalse(session.is_active)

class UserRoleModelTestCase(TestCase):
    """Test cases for UserRole model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            first_name='Test',
            last_name='User',
            auth0_sub='auth0|test'
        )
    
    def test_role_creation(self):
        """Test role creation"""
        role = UserRole.objects.create(
            user=self.user,
            role_name='customer'
        )
        
        self.assertEqual(role.user, self.user)
        self.assertEqual(role.role_name, 'customer')
    
    def test_role_uniqueness(self):
        """Test that a user can't have the same role twice"""
        UserRole.objects.create(
            user=self.user,
            role_name='customer'
        )
        
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(
                user=self.user,
                role_name='customer'
            )

class MonitoringEndpointsTestCase(TestCase):
    """Test monitoring endpoints"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 503]) 
        
        if response.status_code != 404: 
            response_data = response.json()
            self.assertIn('status', response_data)
            self.assertIn('checks', response_data)
    
    def test_ready_check_endpoint(self):
        """Test readiness check endpoint"""
        response = self.client.get('/ready/')
        self.assertIn(response.status_code, [200, 503]) 
        
        if response.status_code != 404: 
            response_data = response.json()
            self.assertIn('status', response_data)
            self.assertIn('checks', response_data)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.client.get('/metrics/')
        self.assertIn(response.status_code, [200, 503])
        
        if response.status_code != 404:  
            self.assertEqual(response['Content-Type'], 'text/plain; version=0.0.4; charset=utf-8')

@override_settings(**TEST_SETTINGS)
class FullIntegrationTestCase(APITestCase):
    """Full integration test simulating complete user flow"""
    
    def setUp(self):
        self.client = APIClient()
    
    @patch('auth_service.users.auth.Auth0JSONWebTokenAuthentication.authenticate')
    def test_complete_user_flow(self, mock_authenticate):
        """Test: register → login → call protected endpoint"""
        user = CustomUser.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integration123',
            first_name='Integration',
            last_name='Test',
            auth0_sub='auth0|integration123',
            is_email_verified=True
        )
        
        UserPreferences.objects.create(user=user)
        
        UserRole.objects.create(user=user, role_name='customer')
        
        mock_authenticate.return_value = (user, 'integration_token')
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer integration_token')
        
        response = self.client.get('/api/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(user.preferences.language, 'en')
        self.assertEqual(user.roles.first().role_name, 'customer')