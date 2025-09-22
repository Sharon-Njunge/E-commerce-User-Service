from django.urls import path
from auth_service import api
from .views import UserDetailView, UserListView

namespace=api

urlpatterns = [
    path("v1/users/", UserListView.as_view(), name="user-list"),
    path("v1/users/<str:user_id>/", UserDetailView.as_view(), name="user-detail"),
]