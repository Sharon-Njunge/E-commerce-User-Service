
import pytest
import requests
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from auth_service.api.utils import call_auth0  # Fixed import path
from auth_service.api.constants import HTTP_200_OK

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

@pytest.mark.django_db
def test_retry_logic_success_after_failures():
    # Mock requests.get to fail twice then succeed
    with patch("auth_service.api.utils.requests.get") as mock_get:  # Fixed import path
        mock_get.side_effect = [
            requests.exceptions.RequestException("fail 1"),
            requests.exceptions.RequestException("fail 2"),
            type(
                "Response",
                (),
                {
                    "raise_for_status": lambda self: None,
                    "json": lambda self: {"ok": True},
                },
            )(),
        ]

        result = call_auth0("https://fake-auth0.com")
        assert result == {"ok": True}
        assert mock_get.call_count == 3
