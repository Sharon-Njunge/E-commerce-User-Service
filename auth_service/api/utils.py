
# api/utils.py
import requests
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential


# Configure circuit breaker
breaker = pybreaker.CircuitBreaker(
    fail_max=3,             # after 3 consecutive failures
    reset_timeout=30        # wait 30s before half-open retry
)


# Retry with exponential backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_auth0_raw(url, headers=None, data=None):
    response = requests.get(url, headers=headers, json=data, timeout=5)
    response.raise_for_status()
    return response.json()


def call_auth0(url, headers=None, data=None):
    """
    Wrapper that applies circuit breaker + retries + fallback.
    """
    try:
        return breaker.call(_call_auth0_raw, url, headers=headers, data=data)
    except pybreaker.CircuitBreakerError:
        # Circuit breaker is open — immediately fallback
        return {"error": "Auth0 service temporarily unavailable (circuit open)"}
    except Exception as e:
        # Retries failed
        return {"error": f"Auth0 request failed: {str(e)}"}
