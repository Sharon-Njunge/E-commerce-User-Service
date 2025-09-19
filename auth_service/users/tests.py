
# Create your tests here.

from django.test import TestCase
from rest_framework.test import APIClient
# from django.urls import reverse

import pytest
import requests
from unittest.mock import patch
from auth_service.api.utils import call_auth0
# from api.utils import call_auth0

client = APIClient()


class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_users_endpoint_requires_auth(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)  # No token, should fail


def test_error_handler_returns_consistent_json(db):
    # Hit a non-existent endpoint to trigger 404
    response = client.get("/api/v1/nonexistent/")

    assert response.status_code == 404
    body = response.json()

    assert "success" in body
    assert body["success"] is False
    assert "error" in body
    assert body["error"]["type"] == "NotFound"


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
