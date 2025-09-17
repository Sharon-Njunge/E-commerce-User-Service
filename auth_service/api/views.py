
# Create your views here.

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.db import connection
import requests
from django.views.decorators.csrf import csrf_exempt
# from auth_service.api.utils import call_auth0
from pybreaker import CircuitBreaker
from rest_framework.decorators import authentication_classes


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"users": []})


# Circuit breaker config
breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

AUTH0_HEALTH_URL = "https://<your-domain>.auth0.com/.well-known/openid-configuration"


# Helper function to check Auth0 with breaker
def call_auth0(url):
    try:
        resp = breaker.call(requests.get, url, timeout=5)
        if resp.status_code == 200:
            return {"auth0": "ok"}
        return {"error": f"status {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@csrf_exempt
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
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

    # Auth0 check (with circuit breaker)
    simulate_fail = request.query_params.get("fail") == "true"
    if simulate_fail:
        status["auth0"] = "simulated failure"
    else:
        auth0_response = call_auth0(AUTH0_HEALTH_URL)
        if "error" in auth0_response:
            status["auth0"] = auth0_response["error"]

    overall = "ok" if all(v == "ok" for v in status.values()) else "error"

    return JsonResponse({
        "status": overall,
        "checks": status
    })
