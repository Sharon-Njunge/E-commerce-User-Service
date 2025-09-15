# from django.contrib import admin
# from django.urls import path, include
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#     openapi.Info(
#         title="User & Auth Service",
#         default_version='v1',
#         description="User & Authentication API",
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/", include("auth_service.api.urls")),
#     # path("api/", include("")),
#     path("swagger/", schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
#     path("redoc/", schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
# ]

# auth_service/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from auth_service.monitoring import views as monitoring_views

schema_view = get_schema_view(
    openapi.Info(
        title="E-commerce User Service API",
        default_version="v1",
        description="API documentation for E-commerce User Service",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", monitoring_views.health_check, name="health-check"),
    path("ready/", monitoring_views.ready_check, name="ready-check"),
    path("metrics/", monitoring_views.metrics_endpoint, name="metrics"),
    path("api/", include("auth_service.api.urls")),
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    path("api-schema/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]
