from django.urls import path

from auth_service.users.views import RegisterView, ProfileView
from .views import UserListView

urlpatterns = [
    path("users/", UserListView.as_view(), name="list-users"),
    path("/register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    # Add more API endpoints from other apps here in the future
]
