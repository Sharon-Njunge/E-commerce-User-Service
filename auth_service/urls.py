from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({"status": "healthy", "service": "user-service"}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def ready_check(request):
    """Readiness check endpoint"""
    return JsonResponse({"status": "ready", "service": "user-service"}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def metrics(request):
    """Basic metrics endpoint"""
    return JsonResponse({"metrics": {"requests": 0, "uptime": "unknown"}}, status=200)


schema_view = get_schema_view(
    openapi.Info(
        title="E-commerce User Service API",
        default_version="v1",
        description="API documentation for E-commerce User Service",
    ),
    public=True, 
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("auth_service.api.urls")),  
    
    path("health/", health_check, name="health-check"),
    path("ready/", ready_check, name="ready-check"),
    path("metrics/", metrics, name="metrics"),
    
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    
    path("api/schema/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]