from django.urls import path
from .views import UserListView

urlpatterns = [
    path("users/", UserListView.as_view(), name="list-users"),
    # Add more API endpoints from other apps here in the future
]
