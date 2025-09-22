import logging
import json
import uuid
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
import threading

# Thread-local storage for request ID
_thread_local = threading.local()

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': 'auth-service',
            'version': '1.0.0',
        }
        
        # Add request ID if available
        request_id = getattr(_thread_local, 'request_id', None)
        if request_id:
            log_data['request_id'] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
            
        return json.dumps(log_data, default=str)

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to add request ID and log requests"""
    
    def process_request(self, request):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        _thread_local.request_id = request_id
        
        # Store start time for duration calculation
        request._start_time = datetime.utcnow()
        
        # Log incoming request
        logger = logging.getLogger('auth_service.requests')
        logger.info('Request started', extra={
            'method': request.method,
            'path': request.path,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
        })
    
    def process_response(self, request, response):
        # Calculate request duration
        if hasattr(request, '_start_time'):
            duration = (datetime.utcnow() - request._start_time).total_seconds() * 1000
        else:
            duration = 0
        
        # Log response
        logger = logging.getLogger('auth_service.requests')
        logger.info('Request completed', extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': round(duration, 2),
            'ip_address': self.get_client_ip(request),
        })
        
        # Clean up thread local
        if hasattr(_thread_local, 'request_id'):
            delattr(_thread_local, 'request_id')
        
        return response
    
    def process_exception(self, request, exception):
        # Log exceptions
        logger = logging.getLogger('auth_service.errors')
        logger.error(f'Request failed with exception: {str(exception)}', 
                    exc_info=True, extra={
                        'method': request.method,
                        'path': request.path,
                        'ip_address': self.get_client_ip(request),
                        'exception_type': exception.__class__.__name__,
                    })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')

