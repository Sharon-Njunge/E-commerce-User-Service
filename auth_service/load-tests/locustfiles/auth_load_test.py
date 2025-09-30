import time
import json
import random
from locust import HttpUser, task, between, TaskSet, events
from locust.runners import MasterRunner, WorkerRunner
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class AuthTasks(TaskSet):
    """Authentication-related tasks"""
    
    def on_start(self):
        """Called when a user starts executing this TaskSet"""
        self.user_id = f"testuser_{self.user.__dict__.get('id', random.randint(1000, 9999))}"
        self.email = f"{self.user_id}@example.com"
        self.password = "testpassword123"
        self.access_token = None
        self.refresh_token = None
        
        # Pre-register user or ensure it exists
        self.ensure_user_exists()
    
    def ensure_user_exists(self):
        """Ensure test user exists in the system"""
        try:
            # Try to login first (user might exist)
            response = self.client.post(
                "/login/",
                json={
                    "email": self.email,
                    "password": self.password
                },
                name="Ensure user exists"
            )
            
            if response.status_code == 200:
                # User exists, store tokens
                data = response.json()
                self.access_token = data.get("accessToken")
                self.refresh_token = data.get("refreshToken")
                logger.info(f"User {self.email} exists, tokens acquired")
            else:
                # User doesn't exist, create via registration flow
                self.register_user()
                
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            self.register_user()
    
    def register_user(self):
        """Register a new user"""
        with self.client.post(
            "/api/auth/register/",
            json={
                "email": self.email,
                "password": self.password,
                "username": self.user_id
            },
            name="Register user",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                logger.info(f"Registered user: {self.email}")
            else:
                response.failure(f"Registration failed: {response.text}")
    
    @task(5)
    def login(self):
        """Login task - higher weight (more frequent)"""
        with self.client.post(
            "/login/",
            json={
                "email": self.email,
                "password": self.password
            },
            name="Login",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("accessToken")
                self.refresh_token = data.get("refreshToken")
                response.success()
                
                # Add custom metric for login duration
                events.request.fire(
                    request_type="LOGIN",
                    name="login_success",
                    response_time=response.elapsed.total_seconds() * 1000,
                    response_length=0
                )
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    @task(3)
    def access_profile(self):
        """Access user profile with valid token"""
        if not self.access_token:
            return
            
        with self.client.get(
            "/profile/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="Access profile",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile access failed: {response.status_code}")
    
    @task(2)
    def refresh_token(self):
        """Refresh access token"""
        if not self.refresh_token:
            return
            
        with self.client.post(
            "/api/auth/refresh/",
            json={"refreshToken": self.refresh_token},
            name="Refresh token",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("accessToken")
                response.success()
            else:
                response.failure(f"Token refresh failed: {response.status_code}")
    
    @task(1)
    def update_profile(self):
        """Update user profile (lower frequency)"""
        if not self.access_token:
            return
            
        with self.client.patch(
            "/profile/update/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"username": f"updated_{self.user_id}"},
            name="Update profile",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Profile update failed: {response.status_code}")

class AuthLoadTest(HttpUser):
    """Main load test class for authentication service"""
    
    tasks = [AuthTasks]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            "login_success": 0,
            "login_failure": 0,
            "requests_made": 0
        }

# Custom event handlers for detailed metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Track custom request metrics"""
    if exception:
        logger.error(f"Request failed: {name}, Exception: {exception}")
    else:
        logger.debug(f"Request successful: {name}, Response time: {response_time}ms")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    logger.info("Authentication load test starting")
    
    # Initialize custom stats
    if not isinstance(environment.runner, WorkerRunner):
        environment.runner.custom_stats = {
            "start_time": datetime.now(),
            "total_users": 0
        }

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    logger.info("Authentication load test completed")
    
    # Generate summary report
    if not isinstance(environment.runner, WorkerRunner):
        duration = datetime.now() - environment.runner.custom_stats["start_time"]
        logger.info(f"Test duration: {duration}")

# Custom failure ratio check
@events.quitting.add_listener
def check_failure_ratio(environment, **kwargs):
    """Check if failure ratio is within acceptable limits"""
    if environment.stats.total.fail_ratio > 0.05:
        logger.error(f"Test failed due to high failure ratio: {environment.stats.total.fail_ratio}")
        environment.process_exit_code = 1
    else:
        logger.info(f"Test passed with failure ratio: {environment.stats.total.fail_ratio}")