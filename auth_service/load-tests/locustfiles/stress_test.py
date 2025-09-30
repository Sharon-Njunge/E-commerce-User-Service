from locust import HttpUser, task, between
import random
import time

class StressTest(HttpUser):
    """Stress test to find breaking points"""
    
    wait_time = between(0.05, 0.2)  # Very aggressive load
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_timeout = 30  # Longer timeout for stress conditions
    
    @task(8)
    def stress_login(self):
        """High-frequency login attempts"""
        user_id = random.randint(1000000, 9999999)
        with self.client.post(
            "/login/",
            json={
                "email": f"stress_{user_id}@example.com",
                "password": "stresspassword"
            },
            name="Stress login",
            timeout=self.request_timeout,
            catch_response=True
        ) as response:
            # In stress test, we accept some failures
            if response.status_code < 500:
                response.success()
            else:
                response.failure(f"Server error: {response.status_code}")
    
    @task(5)
    def stress_profile_access(self):
        """High-frequency profile access with invalid tokens"""
        tokens = ["invalid_token", "expired_token", "malformed_token"]
        self.client.get(
            "/profile/",
            headers={"Authorization": f"Bearer {random.choice(tokens)}"},
            name="Stress profile access",
            timeout=self.request_timeout
        )
    
    @task(2)
    def stress_registration(self):
        """High-frequency user registration"""
        user_id = random.randint(1000000, 9999999)
        self.client.post(
            "/api/auth/register/",
            json={
                "email": f"stress_register_{user_id}@example.com",
                "password": "stresspass",
                "username": f"stress_user_{user_id}"
            },
            name="Stress registration",
            timeout=self.request_timeout
        )