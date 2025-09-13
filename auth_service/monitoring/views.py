import psutil
import time
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from auth_service.users.models import CustomUser, UserSession


@require_http_methods(["GET"])
@never_cache
def health_check(request):
    """Basic health check endpoint"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        # Test cache connection
        cache.set("health_check_key", "ok", 10)
        cache_result = cache.get("health_check_key")
        cache_status = "healthy" if cache_result == "ok" else "unhealthy"
    except Exception as e:
        cache_status = f"unhealthy: {str(e)}"

    # Overall health
    is_healthy = db_status == "healthy" and cache_status == "healthy"

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "service": "auth-service",
        "checks": {"database": db_status, "cache": cache_status},
    }

    status_code = 200 if is_healthy else 503
    return JsonResponse(health_data, status=status_code)


@require_http_methods(["GET"])
@never_cache
def ready_check(request):
    """Readiness check - more comprehensive than health check"""
    checks = {}
    all_ready = True

    # Database readiness
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_users_customuser")
            user_count = cursor.fetchone()[0]
        checks["database"] = {"status": "ready", "user_count": user_count}
    except Exception as e:
        checks["database"] = {"status": "not_ready", "error": str(e)}
        all_ready = False

    # Cache readiness
    try:
        cache.set("readiness_check", "ready", 10)
        cache_result = cache.get("readiness_check")
        if cache_result == "ready":
            checks["cache"] = {"status": "ready"}
        else:
            checks["cache"] = {
                "status": "not_ready",
                "error": "Cache not responding correctly",
            }
            all_ready = False
    except Exception as e:
        checks["cache"] = {"status": "not_ready", "error": str(e)}
        all_ready = False

    # System resources
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        checks["resources"] = {
            "status": "ready",
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "cpu_percent": psutil.cpu_percent(interval=1),
        }

        # Mark as not ready if resources are critically low
        if memory.percent > 95 or disk.percent > 95:
            checks["resources"]["status"] = "not_ready"
            all_ready = False

    except Exception as e:
        checks["resources"] = {"status": "not_ready", "error": str(e)}
        all_ready = False

    ready_data = {
        "status": "ready" if all_ready else "not_ready",
        "timestamp": time.time(),
        "checks": checks,
    }

    status_code = 200 if all_ready else 503
    return JsonResponse(ready_data, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
def metrics_endpoint(request):
    """Prometheus-style metrics endpoint"""
    try:
        # Database metrics
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        verified_users = CustomUser.objects.filter(is_email_verified=True).count()
        active_sessions = UserSession.objects.filter(is_active=True).count()

        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_percent = psutil.cpu_percent(interval=1)

        # Database connection metrics
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            active_connections = cursor.fetchone()[0]

        # Generate Prometheus-style metrics
        metrics = [
            "# HELP auth_service_users_total Total number of registered users",
            "# TYPE auth_service_users_total gauge",
            f"auth_service_users_total {total_users}",
            "",
            "# HELP auth_service_users_active Number of active users",
            "# TYPE auth_service_users_active gauge",
            f"auth_service_users_active {active_users}",
            "",
            "# HELP auth_service_users_verified Number of verified users",
            "# TYPE auth_service_users_verified gauge",
            f"auth_service_users_verified {verified_users}",
            "",
            "# HELP auth_service_sessions_active Number of active sessions",
            "# TYPE auth_service_sessions_active gauge",
            f"auth_service_sessions_active {active_sessions}",
            "",
            "# HELP auth_service_memory_usage_percent Memory usage percentage",
            "# TYPE auth_service_memory_usage_percent gauge",
            f"auth_service_memory_usage_percent {memory.percent}",
            "",
            "# HELP auth_service_disk_usage_percent Disk usage percentage",
            "# TYPE auth_service_disk_usage_percent gauge",
            f"auth_service_disk_usage_percent {disk.percent}",
            "",
            "# HELP auth_service_cpu_usage_percent CPU usage percentage",
            "# TYPE auth_service_cpu_usage_percent gauge",
            f"auth_service_cpu_usage_percent {cpu_percent}",
            "",
            "# HELP auth_service_db_connections_active Active DB connections",
            "# TYPE auth_service_db_connections_active gauge",
            f"auth_service_db_connections_active {active_connections}",
            "",
            "# HELP auth_service_up Service availability",
            "# TYPE auth_service_up gauge",
            "auth_service_up 1",
        ]

        response_text = "\n".join(metrics)
        return JsonResponse(
            response_text,
            content_type="text/plain; version=0.0.4; charset=utf-8",
            safe=False,
        )

    except Exception:
        # Return error metric
        error_metrics = [
            "# HELP auth_service_up Service availability",
            "# TYPE auth_service_up gauge",
            "auth_service_up 0",
        ]
        response_text = "\n".join(error_metrics)
        return JsonResponse(
            response_text,
            content_type="text/plain; version=0.0.4; charset=utf-8",
            status=503,
            safe=False,
        )
