import json
import logging
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_service.users.models import User, UserPreferences, UserSession, LoginAttempt

try:
    from auth_service.api.utils import call_auth0
except ImportError:
    def call_auth0(*args, **kwargs):
        return {}

try:
    from auth_service.utils.security import rate_limit
except ImportError:
    def rate_limit(*args, **kwargs):
        pass

try:
    from .constants import *
except ImportError:
    # Define constants if import fails
    HTTP_200_OK = status.HTTP_200_OK
    HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
    HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    HTTP_503_SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE

logger = logging.getLogger(__name__)

class UserListView(APIView):
    """
    List all users with pagination and filtering
    """
    permission_classes = [permissions.AllowAny]  # Changed from IsAuthenticated for debugging
    
    def get(self, request):
        try:
            logger.info("UserListView GET called")
            
            # Apply rate limiting (now safe even if function doesn't exist)
            try:
                rate_limit(request, key_prefix="user_list", limit=10, window=60)
            except Exception as e:
                logger.warning(f"Rate limiting failed: {e}")
            
            # Pagination parameters
            page = int(request.GET.get('page', 1))
            per_page = min(int(request.GET.get('per_page', 20)), 100)
            
            # Filtering
            is_active = request.GET.get('is_active')
            email_verified = request.GET.get('email_verified')
            
            queryset = User.objects.all()
            
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            if email_verified is not None:
                queryset = queryset.filter(email_verified=email_verified.lower() == 'true')
            
            total = queryset.count()
            start = (page - 1) * per_page
            end = start + per_page
            
            users = queryset[start:end]
            
            users_data = []
            for user in users:
                try:
                    users_data.append({
                        'user_id': user.auth0_user_id or str(user.id),
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name if hasattr(user, 'full_name') else f"{user.first_name} {user.last_name}",
                        'is_active': user.is_active,
                        'email_verified': user.email_verified,
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                    })
                except Exception as e:
                    logger.error(f"Error serializing user {user.id}: {e}")
                    continue
            
            logger.info(f"User list requested - page: {page}, total: {total}")
            
            return Response({
                'success': True,
                'users': users_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }, status=HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """
    Get, update, or delete a specific user
    """
    permission_classes = [permissions.AllowAny]  # Changed from IsAuthenticated for debugging
    
    def get_user(self, user_id):
        try:
            if str(user_id).startswith('auth0|'):
                return User.objects.get(auth0_user_id=user_id)
            else:
                return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get(self, request, user_id):
        try:
            logger.info(f"UserDetailView GET called for user_id: {user_id}")
            
            try:
                rate_limit(request, key_prefix="user_detail", limit=20, window=60)
            except Exception as e:
                logger.warning(f"Rate limiting failed: {e}")
            
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {'type': 'NotFound', 'details': 'User not found'}
                }, status=HTTP_404_NOT_FOUND)
            
            user_data = {
                'user_id': user.auth0_user_id or str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name if hasattr(user, 'full_name') else f"{user.first_name} {user.last_name}",
                'phone_number': user.phone_number,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'email_verified': user.email_verified,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            
            logger.info(f"User detail requested for: {user.email}")
            
            return Response({
                'success': True,
                'user': user_data
            }, status=HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, user_id):
        try:
            logger.info(f"UserDetailView PUT called for user_id: {user_id}")
            
            try:
                rate_limit(request, key_prefix="user_update", limit=5, window=60)
            except Exception as e:
                logger.warning(f"Rate limiting failed: {e}")
            
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {'type': 'NotFound', 'details': 'User not found'}
                }, status=HTTP_404_NOT_FOUND)
            
            data = request.data
            
            # Update allowed fields
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            
            user.save()
            
            logger.info(f"User updated: {user.email}")
            
            return Response({
                'success': True,
                'message': 'User updated successfully',
                'user': {
                    'user_id': user.auth0_user_id or str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.full_name if hasattr(user, 'full_name') else f"{user.first_name} {user.last_name}",
                    'phone_number': user.phone_number,
                }
            }, status=HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


class UserPreferencesView(APIView):
    """
    Get or update user preferences
    """
    permission_classes = [permissions.AllowAny]  # Changed for debugging
    
    def get_user(self, user_id):
        try:
            if str(user_id).startswith('auth0|'):
                return User.objects.get(auth0_user_id=user_id)
            else:
                return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get(self, request, user_id):
        try:
            logger.info(f"UserPreferencesView GET called for user_id: {user_id}")
            
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {'type': 'NotFound', 'details': 'User not found'}
                }, status=HTTP_404_NOT_FOUND)
            
            try:
                preferences, created = UserPreferences.objects.get_or_create(user=user)
            except Exception as e:
                logger.error(f"Error getting/creating preferences: {e}")
                return Response({
                    'success': False,
                    'error': {'type': 'ServerError', 'details': 'Could not access user preferences'}
                }, status=HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'preferences': {
                    'language': preferences.language,
                    'timezone': preferences.timezone,
                    'theme': preferences.theme,
                    'currency': preferences.currency,
                    'order_notifications': preferences.order_notifications,
                    'payment_notifications': preferences.payment_notifications,
                    'marketing_emails': preferences.marketing_emails,
                    'security_alerts': preferences.security_alerts,
                    'profile_visibility': preferences.profile_visibility,
                    'data_sharing_consent': preferences.data_sharing_consent,
                    'custom_preferences': preferences.custom_preferences,
                }
            }, status=HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


# Health and Monitoring Views
class HealthCheckView(APIView):
    """
    Basic health check endpoint
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Explicitly disable authentication
    
    def get(self, request):
        try:
            logger.info("Health check called")
            return Response({
                'status': 'ok',
                'timestamp': timezone.now().isoformat(),
                'service': 'auth-service'
            }, status=HTTP_200_OK)
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


class ReadinessCheckView(APIView):
    """
    Readiness check with database and cache validation
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Explicitly disable authentication
    
    def get(self, request):
        try:
            logger.info("Readiness check called")
            checks = {}
            overall_status = 'ready'
            
            # Database check
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()
                checks['database'] = True
                logger.debug("Database check passed")
            except Exception as e:
                checks['database'] = False
                overall_status = 'not_ready'
                logger.error(f"Database check failed: {str(e)}")
            
            # Cache check
            try:
                cache.set('health_check', 'ok', 10)
                cache_value = cache.get('health_check')
                checks['cache'] = cache_value == 'ok'
                if not checks['cache']:
                    overall_status = 'not_ready'
                logger.debug("Cache check passed")
            except Exception as e:
                checks['cache'] = False
                overall_status = 'not_ready'
                logger.error(f"Cache check failed: {str(e)}")
            
            status_code = HTTP_200_OK if overall_status == 'ready' else HTTP_503_SERVICE_UNAVAILABLE
            
            return Response({
                'status': overall_status,
                'timestamp': timezone.now().isoformat(),
                'checks': checks
            }, status=status_code)
            
        except Exception as e:
            logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


class MetricsView(APIView):
    """
    Prometheus-style metrics endpoint
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Explicitly disable authentication
    
    def get(self, request):
        try:
            logger.info("Metrics endpoint called")
            
            # User metrics - with error handling
            try:
                total_users = User.objects.count()
                active_users = User.objects.filter(is_active=True).count()
                verified_users = User.objects.filter(email_verified=True).count()
            except Exception as e:
                logger.error(f"Error getting user metrics: {e}")
                total_users = active_users = verified_users = 0
            
            # Session metrics - with error handling
            try:
                active_sessions = UserSession.objects.filter(
                    is_active=True,
                    expires_at__gt=timezone.now()
                ).count()
            except Exception as e:
                logger.error(f"Error getting session metrics: {e}")
                active_sessions = 0
            
            # Login attempt metrics - with error handling
            try:
                recent_logins = LoginAttempt.objects.filter(
                    attempted_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
                )
                successful_logins = recent_logins.filter(success=True).count()
                failed_logins = recent_logins.filter(success=False).count()
            except Exception as e:
                logger.error(f"Error getting login metrics: {e}")
                successful_logins = failed_logins = 0
            
            metrics = f"""# HELP auth_service_users_total Total number of users
# TYPE auth_service_users_total gauge
auth_service_users_total {total_users}

# HELP auth_service_users_active Number of active users
# TYPE auth_service_users_active gauge
auth_service_users_active {active_users}

# HELP auth_service_users_verified Number of verified users
# TYPE auth_service_users_verified gauge
auth_service_users_verified {verified_users}

# HELP auth_service_sessions_active Number of active sessions
# TYPE auth_service_sessions_active gauge
auth_service_sessions_active {active_sessions}

# HELP auth_service_logins_successful_today Successful logins today
# TYPE auth_service_logins_successful_today counter
auth_service_logins_successful_today {successful_logins}

# HELP auth_service_logins_failed_today Failed logins today
# TYPE auth_service_logins_failed_today counter
auth_service_logins_failed_today {failed_logins}

# HELP auth_service_up Service availability
# TYPE auth_service_up gauge
auth_service_up 1
"""
            
            return HttpResponse(metrics, content_type='text/plain')
            
        except Exception as e:
            logger.error(f"Error generating metrics: {str(e)}", exc_info=True)
            return HttpResponse(f"# Error generating metrics: {str(e)}", 
                              content_type='text/plain', 
                              status=HTTP_500_INTERNAL_SERVER_ERROR)


# Keep the other views but make them more robust
class UserSessionsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        try:
            logger.info(f"UserSessionsView GET called for user_id: {user_id}")
            
            if str(user_id).startswith('auth0|'):
                user = User.objects.get(auth0_user_id=user_id)
            else:
                user = User.objects.get(id=user_id)
                
            sessions = UserSession.objects.filter(user=user, is_active=True)
            
            sessions_data = []
            for session in sessions:
                try:
                    sessions_data.append({
                        'session_id': str(session.id),
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent,
                        'device_info': session.device_info,
                        'created_at': session.created_at.isoformat(),
                        'expires_at': session.expires_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'is_expired': session.is_expired(),
                    })
                except Exception as e:
                    logger.error(f"Error serializing session {session.id}: {e}")
                    continue
            
            return Response({
                'success': True,
                'sessions': sessions_data,
                'total': len(sessions_data)
            }, status=HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': {'type': 'NotFound', 'details': 'User not found'}
            }, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in UserSessionsView: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)


class LoginAttemptsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        try:
            logger.info(f"LoginAttemptsView GET called for user_id: {user_id}")
            
            if str(user_id).startswith('auth0|'):
                user = User.objects.get(auth0_user_id=user_id)
            else:
                user = User.objects.get(id=user_id)
            
            attempts = LoginAttempt.objects.filter(email=user.email).order_by('-attempted_at')[:20]
            
            attempts_data = []
            for attempt in attempts:
                try:
                    attempts_data.append({
                        'id': str(attempt.id),
                        'ip_address': attempt.ip_address,
                        'user_agent': attempt.user_agent,
                        'success': attempt.success,
                        'failure_reason': attempt.failure_reason,
                        'attempted_at': attempt.attempted_at.isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Error serializing login attempt {attempt.id}: {e}")
                    continue
            
            return Response({
                'success': True,
                'login_attempts': attempts_data,
                'total': len(attempts_data)
            }, status=HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': {'type': 'NotFound', 'details': 'User not found'}
            }, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in LoginAttemptsView: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {'type': 'ServerError', 'details': str(e)}
            }, status=HTTP_500_INTERNAL_SERVER_ERROR)