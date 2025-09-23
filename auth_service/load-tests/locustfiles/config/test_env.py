"""Test environment configuration"""
import os

class TestConfig:
    """Configuration for performance tests"""
    
    # Base URLs
    BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:8000')
    
    # Test parameters
    MAX_USERS = int(os.getenv('MAX_USERS', '1000'))
    SPAWN_RATE = int(os.getenv('SPAWN_RATE', '100'))
    RUN_TIME = os.getenv('RUN_TIME', '10m')
    
    # Thresholds
    MAX_FAILURE_RATE = float(os.getenv('MAX_FAILURE_RATE', '0.05'))
    MAX_RESPONSE_TIME_MS = int(os.getenv('MAX_RESPONSE_TIME_MS', '5000'))
    
    # Auth endpoints
    LOGIN_ENDPOINT = "/login/"
    REFRESH_ENDPOINT = "/api/auth/refresh/"
    PROFILE_ENDPOINT = "/profile/"
    REGISTER_ENDPOINT = "/api/auth/register/"
    
    # Test data
    TEST_USER_EMAIL = "loadtest@example.com"
    TEST_USER_PASSWORD = "loadtestpassword"