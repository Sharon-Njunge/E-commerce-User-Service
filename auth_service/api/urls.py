from django.urls import path

from auth_service.api import views

from .views import (LoginAttemptsView, UserDetailView, UserListView,
                    UserPreferencesView, UserSessionsView)

app_name = 'api'

urlpatterns = [
    # User management endpoints
    path('v1/users/', UserListView.as_view(), name='user-list'),
    path('v1/users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('v1/users/<str:user_id>/preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    path('v1/users/<str:user_id>/sessions/', UserSessionsView.as_view(), name='user-sessions'),
    path('v1/users/<str:user_id>/login-attempts/', LoginAttemptsView.as_view(), name='user-login-attempts'),
    path("profile/<str:user_id>/", views.get_profile),
    path("profile/<str:user_id>/update/", views.update_profile),
    path("users/", views.list_all_users, name="list_users"),
]
