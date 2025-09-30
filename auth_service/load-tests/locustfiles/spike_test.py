from locust import HttpUser, task, between
import random

class SpikeTest(HttpUser):
    """Test system behavior under sudden load spikes"""
    
    wait_time = between(0.1, 0.5)  # Very short wait times to simulate spike
    
    def on_start(self):
        self.user_id = random.randint(100000, 999999)
        self.email = f"spikeuser_{self.user_id}@example.com"
    
    @task(10)
    def rapid_login_attempts(self):
        """Simulate rapid login attempts during spike"""
        self.client.post(
            "/login/",
            json={
                "email": self.email,
                "password": "spikepassword"
            },
            name="Spike login"
        )
    
    @task(3)
    def token_refresh_spike(self):
        """Simulate token refresh requests during spike"""
        self.client.post(
            "/api/auth/refresh/",
            json={"refreshToken": "mock_refresh_token"},
            name="Spike token refresh"
        )
    
    @task(1)
    def profile_access_spike(self):
        """Simulate profile access during spike"""
        self.client.get(
            "/profile/",
            headers={"Authorization": "Bearer mock_token"},
            name="Spike profile access"
        )