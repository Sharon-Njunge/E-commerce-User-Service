from django.urls import path
from .views import OrdersView, AdminUsersView, Auth0LoginView

urlpatterns = [
    path("orders/", OrdersView.as_view(), name="orders"),
    path("admin/users/", AdminUsersView.as_view(), name="admin-users"),
    path("api/v1/auth/login/", Auth0LoginView.as_view(), name="auth0-login"),

]
