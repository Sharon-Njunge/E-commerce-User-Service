from django.urls import path

from auth_service.api import views

app_name = "api"

    # Add more API endpoints from other apps here in the future
urlpatterns = [
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('users/', views.list_users, name='list_users'),
    path('register/', views.register_user, name='register'),
]