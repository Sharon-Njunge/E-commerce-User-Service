# Minimal stub security utilities for local/dev. Replace with real implementation.
from functools import wraps
from django.http import HttpResponse

def rate_limit(limit=100, period=60):
    """
    Very small in-process rate-limit decorator for dev.
    Not suitable for production (use redis / shared storage).
    Usage: @rate_limit(limit=10, period=60)
    """
    def decorator(view_func):
        # naive in-memory counter keyed by view name (process-local)
        counters = {}
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            key = f"{view_func.__module__}:{view_func.__name__}"
            ctr, ts = counters.get(key, (0, None))
            import time
            now = int(time.time())
            if ts is None or now - ts >= period:
                ctr, ts = 0, now
            ctr += 1
            counters[key] = (ctr, ts)
            if ctr > limit:
                return HttpResponse("Too Many Requests", status=429)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# export names
__all__ = ["rate_limit"]
