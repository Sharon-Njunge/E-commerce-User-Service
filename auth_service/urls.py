from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="E-commerce User Service API",
        default_version="v1",
        description="API documentation for E-commerce User Service",
    ),
    public=True,  # 👈 this allows public access
    permission_classes=(permissions.AllowAny,),
)

app_name = "api"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("auth_service.api.urls")),  # adjust if your app has urls.py
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]
