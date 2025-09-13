import json
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import resolve
from django.conf import settings

logger = logging.getLogger(__name__)

class StructuredLoggingMiddleware(MiddlewareMixin):
    """Middleware for structured JSON logging with correlation IDs"""
    
    def process_request(self, request):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        request.start_time = time.time()
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Log structured request
        log_data = {
            'event_type': 'http_request',
            'correlation_id': correlation_id,
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'client_ip': client_ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'timestamp': time.time(),
        }
        
        # Add user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user_id'] = str(request.user.id)
            log_data['user_email'] = request.user.email
        
        logger.info('HTTP Request', extra={'structured': log_data})
        
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time') and hasattr(request, 'correlation_id'):
            duration = time.time() - request.start_time
            
            # Add response time header
            response['X-Response-Time'] = f"{duration:.3f}s"
            response['X-Correlation-ID'] = request.correlation_id
            
            # Log structured response
            log_data = {
                'event_type': 'http_response',
                'correlation_id': request.correlation_id,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
                'timestamp': time.time(),
            }
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error('HTTP Response', extra={'structured': log_data})
            elif response.status_code >= 400:
                logger.warning('HTTP Response', extra={'structured': log_data})
            else:
                logger.info('HTTP Response', extra={'structured': log_data})
        
        return response
    
    def process_exception(self, request, exception):
        if hasattr(request, 'correlation_id'):
            log_data = {
                'event_type': 'http_exception',
                'correlation_id': request.correlation_id,
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'path': request.path,
                'method': request.method,
                'timestamp': time.time(),
            }
            
            logger.error('HTTP Exception', extra={'structured': log_data})
        
        return None
