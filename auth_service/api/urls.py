from django.urls import path
from .views import UserListView
from . import views

urlpatterns = [
    path("users/", UserListView.as_view(), name="list-users"),
    path("health/", views.health_check, name="health-check"),

]
