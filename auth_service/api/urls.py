from django.urls import path

# from auth_service.api import views
from . import views

urlpatterns = [
    path("users/", (views.get_users), name="api-get-users"),
    path("profile/", (views.get_profile), name="api-get-profile"),
    path("profile/update/", (views.update_profile), name="api-update-profile"),
    path("signup/", (views.signup), name="api-signup"),
]
