
import pytest
import requests
from unittest.mock import patch
from rest_framework.test import APIClient
from auth_service.api.utils import call_auth0
from auth_service.api.constants import HTTP_200_OK

client = APIClient()


@pytest.mark.django_db
def test_health_check_endpoint():
    """
    Ensure the /health endpoint responds with correct structure.
    """
    response = client.get("/api/v1/health/")
    assert response.status_code == HTTP_200_OK

    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "auth0" in data["checks"]


@pytest.mark.django_db
def test_retry_logic_success_after_failures():
    """
    Simulate transient failures where Auth0 call fails twice then succeeds.
    """
    with patch("api.utils.requests.get") as mock_get:
        # Fail twice, then succeed
        mock_get.side_effect = [
            requests.exceptions.RequestException("fail 1"),
            requests.exceptions.RequestException("fail 2"),
            type("Response", (), {
                "raise_for_status": lambda self: None,
                "json": lambda self: {"ok": True}
            })()
        ]

        result = call_auth0("https://fake-auth0.com")
        assert result == {"ok": True}
        assert mock_get.call_count == 3  # retried 3 times


@pytest.mark.django_db
def test_retry_logic_all_failures_triggers_fallback():
    """
    Simulate all retries failing, expect fallback response.
    """
    with patch("api.utils.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("fail")

        result = call_auth0("https://fake-auth0.com")
        assert "error" in result
        assert mock_get.call_count >= 3  # retried before giving up


@pytest.mark.django_db
def test_circuit_breaker_remains_open():
    """
    After repeated failures, circuit breaker should open and short-circuit
    without making external calls on subsequent attempts.
    """
    with patch("api.utils.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("fail")

        # First call: tries + fails → breaker opens
        call_auth0("https://fake-auth0.com")

        # Reset mock call count
        mock_get.reset_mock()

        # Second call: should be short-circuited immediately
        result = call_auth0("https://fake-auth0.com")
        assert "error" in result
        mock_get.assert_not_called()
