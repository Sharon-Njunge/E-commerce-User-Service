import time
from django.core.cache import cache
from rest_framework.exceptions import Throttled, AuthenticationFailed


def rate_limit(request, key_prefix="auth", limit=5, window=60):
    """
    Limit requests to `limit` per `window` seconds per IP.
    """
    ip = request.META.get("REMOTE_ADDR")
    key = f"{key_prefix}:{ip}"
    data = cache.get(key, {"count": 0, "start": time.time()})

    if time.time() - data["start"] > window:
        data = {"count": 1, "start": time.time()}
    else:
        data["count"] += 1

    cache.set(key, data, timeout=window)

    if data["count"] > limit:
        raise Throttled(detail="Too many requests, slow down.")


def block_failed_login(request, username, max_attempts=3, window=300):
    """
    Block repeated failed logins for a given username/IP.
    """
    ip = request.META.get("REMOTE_ADDR")
    key = f"failed_login:{username}:{ip}"
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=window)

    if attempts > max_attempts:
        raise AuthenticationFailed("Too many failed login attempts. Try later.")
