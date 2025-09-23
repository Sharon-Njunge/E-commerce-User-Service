from django.urls import path
from auth_service import api
from auth_service.api import views


namespace = api

urlpatterns = [
    path("profile/<str:user_id>/", views.get_profile),
    path("profile/<str:user_id>/update/", views.update_profile),
    path("users/", views.list_all_users, name="list_users"),
]
