from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
from pydantic import BaseModel, EmailStr, constr
from pydantic.error_wrappers import ValidationError
from django.core.cache import cache
import time

# ----------------------------
# Pydantic schema
# ----------------------------
class LoginSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=50)

# ----------------------------
# Configurable rate-limiting
# ----------------------------
MAX_ATTEMPTS = 5           # Maximum failed login attempts
BLOCK_TIME = 300           # Block time in seconds (5 min)

# ----------------------------
# Auth0 login view
# ----------------------------
class Auth0LoginView(APIView):
    """
    Handles login with Auth0, includes:
    - Pydantic validation
    - Rate limiting
    - Failed login blocking
    """

    def post(self, request):
        # 1️⃣ Input validation
        try:
            data = LoginSchema(**request.data)
        except ValidationError as e:
            return Response({"error": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        email = data.email
        cache_key = f"login_attempts:{email}"

        # 2️⃣ Check if user is blocked
        attempts = cache.get(cache_key, {"count": 0, "blocked_until": 0})
        now = int(time.time())

        if attempts["blocked_until"] > now:
            return Response(
                {"error": f"Too many failed login attempts. Try again in {attempts['blocked_until'] - now} seconds."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 3️⃣ Auth0 login request
        payload = {
            "grant_type": "password",
            "username": email,
            "password": data.password,
            "audience": settings.AUTH0_AUDIENCE,
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "scope": "openid profile email",
            "connection": settings.AUTH0_CONNECTION,
        }

        url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
        response = requests.post(url, json=payload)

        # 4️⃣ Handle failed login
        if response.status_code != 200:
            attempts["count"] += 1

            # If max attempts exceeded, block user
            if attempts["count"] >= MAX_ATTEMPTS:
                attempts["blocked_until"] = now + BLOCK_TIME
                attempts["count"] = 0  # reset counter after block

            cache.set(cache_key, attempts, timeout=BLOCK_TIME)
            return Response(
                {"error": response.json()},
                status=response.status_code
            )

        # 5️⃣ Successful login, reset attempts
        cache.delete(cache_key)
        return Response(response.json(), status=status.HTTP_200_OK)
