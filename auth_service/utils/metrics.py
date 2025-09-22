import time
from functools import wraps
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect application metrics"""
    
    @staticmethod
    def increment_counter(name, labels=None, value=1):
        """Increment a counter metric"""
        key = f"metric:counter:{name}"
        if labels:
            key += ":" + ":".join(f"{k}={v}" for k, v in labels.items())
        
        current = cache.get(key, 0)
        cache.set(key, current + value, timeout=86400)  # 24 hours
    
    @staticmethod
    def record_histogram(name, value, labels=None):
        """Record a histogram value"""
        key = f"metric:histogram:{name}"
        if labels:
            key += ":" + ":".join(f"{k}={v}" for k, v in labels.items())
        
        # Store recent values for percentile calculation
        values = cache.get(key, [])
        values.append(value)
        
        # Keep only last 1000 values
        if len(values) > 1000:
            values = values[-1000:]
        
        cache.set(key, values, timeout=86400)
    
    @staticmethod
    def set_gauge(name, value, labels=None):
        """Set a gauge metric"""
        key = f"metric:gauge:{name}"
        if labels:
            key += ":" + ":".join(f"{k}={v}" for k, v in labels.items())
        
        cache.set(key, value, timeout=86400)

def track_timing(metric_name, labels=None):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                MetricsCollector.increment_counter(f"{metric_name}_total", labels)
                return result
            except Exception as e:
                error_labels = dict(labels) if labels else {}
                error_labels['error'] = e.__class__.__name__
                MetricsCollector.increment_counter(f"{metric_name}_errors", error_labels)
                raise
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to ms
                MetricsCollector.record_histogram(f"{metric_name}_duration_ms", duration, labels)
        return wrapper
    return decorator

def track_user_action(action_name):
    """Track user actions for analytics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                MetricsCollector.increment_counter('user_actions_total', {'action': action_name})
                logger.info(f'User action: {action_name}', extra={'action': action_name})
                return result
            except Exception as e:
                MetricsCollector.increment_counter('user_actions_errors', {
                    'action': action_name,
                    'error': e.__class__.__name__
                })
                raise
        return wrapper
    return decorator

# Updated settings.py for logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'auth_service.utils.logging.JSONFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/auth-service.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'DEBUG',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/auth-service-errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'auth_service': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'auth_service.requests': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'auth_service.errors': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'auth_service.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Production alert thresholds documentation
ALERT_THRESHOLDS = {
    'error_rate': {
        'warning': 0.05,  # 5% error rate
        'critical': 0.10,  # 10% error rate
        'description': 'HTTP 5xx error rate over 5-minute window'
    },
    'response_time': {
        'warning': 1000,  # 1 second
        'critical': 3000,  # 3 seconds
        'description': '95th percentile response time in milliseconds'
    },
    'database_connections': {
        'warning': 80,  # 80% of pool
        'critical': 95,  # 95% of pool
        'description': 'Database connection pool utilization percentage'
    },
    'memory_usage': {
        'warning': 80,  # 80% memory usage
        'critical': 95,  # 95% memory usage
        'description': 'Memory usage percentage'
    },
    'failed_logins': {
        'warning': 100,  # 100 failed logins per hour
        'critical': 500,  # 500 failed logins per hour
        'description': 'Failed login attempts per hour - possible brute force attack'
    },
    'cache_hit_rate': {
        'warning': 0.85,  # 85% hit rate
        'critical': 0.70,  # 70% hit rate
        'description': 'Cache hit rate - lower values indicate performance issues'
    }
}