
# Create your tests here.
import pytest
import requests
from unittest.mock import patch
from auth_service.api.utils import call_auth0
# from api.utils import call_auth0
from rest_framework.test import APIClient
from .constants import HTTP_200_OK

client = APIClient()


@pytest.mark.django_db
def test_retry_logic_success_after_failures():
    # Mock requests.get to fail twice then succeed
    with patch("api.utils.requests.get") as mock_get:
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


def test_health_check_endpoint():
    response = client.get("/api/v1/health/")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok"}
