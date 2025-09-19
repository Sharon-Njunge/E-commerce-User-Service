
# Create your views here.

from rest_framework.views import APIView
# from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# from .constants import HTTP_200_OK
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.db import connection
import requests
from .constants import AUTH0_HEALTH_URL
from auth_service.utils.permissions import HasAuth0Permission


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"users": []})


@api_view(["GET"])
@permission_classes([AllowAny])
# api/views.py
def health_check(request):
    status = {
        "database": "ok",
        "auth0": "ok",
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as e:
        status["database"] = f"error: {str(e)}"

    # Auth0 check
    try:
        resp = requests.get(AUTH0_HEALTH_URL, timeout=5)
        resp.raise_for_status()
        status["auth0"] = "ok"
    except Exception as e:
        status["auth0"] = f"error: {str(e)}"

    overall = "ok" if all(v == "ok" for v in status.values()) else "error"

    return JsonResponse({
        "status": overall,
        "checks": status
    })


class OrdersView(APIView):
    permission_classes = [IsAuthenticated, HasAuth0Permission]
    HasAuth0Permission.required_permission = "create:orders"

    def get(self, request):
        return Response({"msg": "You are allowed to create orders!"})


class UsersView(APIView):
    permission_classes = [IsAuthenticated, HasAuth0Permission]
    HasAuth0Permission.required_permission = "read:users"

    def get(self, request):
        return Response({"msg": "You are allowed to read users!"})