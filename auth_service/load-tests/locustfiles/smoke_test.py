from locust import HttpUser, task, between
import logging

logger = logging.getLogger(__name__)

class SmokeTest(HttpUser):
    """Smoke test to verify basic functionality"""
    
    wait_time = between(1, 2)
    
    @task
    def health_check(self):
        """Check if service is healthy"""
        with self.client.get("/", name="Health check", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task
    def login_smoke_test(self):
        """Basic login functionality test"""
        self.client.post(
            "/login/",
            json={
                "email": "smoketest@example.com",
                "password": "password123"
            },
            name="Smoke test login"
        )

class QuickSmokeTest(HttpUser):
    """Even quicker smoke test for CI/CD"""
    wait_time = between(0.5, 1)
    
    @task
    def quick_check(self):
        self.client.get("/")