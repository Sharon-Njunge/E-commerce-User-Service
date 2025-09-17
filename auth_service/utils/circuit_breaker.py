# auth_service/utils/circuit_breaker.py
import logging
import requests
import pybreaker
from django.core.cache import cache


logger = logging.getLogger(__name__)

auth0_breaker = pybreaker.CircuitBreaker(
    fail_max=3,        # after 3 failures -> open circuit
    reset_timeout=30,  # after 30s -> half-open
    name="Auth0CircuitBreaker"
)


@auth0_breaker
def call_auth0(url: str):
    """Call Auth0 with circuit breaker protection."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.text


def safe_auth0_call(url: str):
    """Wrapper with fallback to cache."""
    try:
        result = call_auth0(url)
        cache.set("auth0_last_success", result, timeout=3600)
        return "ok"
    except pybreaker.CircuitBreakerError:
        logger.warning("Circuit breaker OPEN - using fallback for Auth0")
        return cache.get("auth0_last_success") or "error: Auth0 unavailable"
    except Exception as e:
        logger.error(f"Auth0 call failed: {e}")
        return cache.get("auth0_last_success") or f"error: {str(e)}"
