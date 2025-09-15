from django.conf import settings
import requests
from pydantic import BaseModel, EmailStr, constr
from pydantic.error_wrappers import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from auth_service.utils.permissions import HasPermission


class OrdersView(APIView):
    permission_classes = [HasPermission("read:orders")]

    def get(self, request):
        return Response(
            {"message": f"Orders visible to {request.user['sub']}"}
        )


class AdminUsersView(APIView):
    permission_classes = [HasPermission("manage:users")]

    def get(self, request):
        return Response({"message": "Admin can manage users"})


AUTH0_DOMAIN = settings.AUTH0_DOMAIN
AUTH0_CLIENT_ID = settings.AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET = settings.AUTH0_CLIENT_SECRET
AUTH0_AUDIENCE = settings.AUTH0_AUDIENCE
AUTH0_CONNECTION = settings.AUTH0_CONNECTION


class LoginSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=50)


class LoginThrottle(AnonRateThrottle):
    rate = "5/minute"


class Auth0LoginView(APIView):
    """
    Handles login using Auth0 Resource Owner Password Grant.
    """

    throttle_classes = [LoginThrottle]

    def post(self, request):
        try:
            data = LoginSchema(**request.data)
        except ValidationError as e:
            return Response(
                {"error": e.errors()},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = {
            "grant_type": "password",
            "username": data.email,
            "password": data.password,
            "audience": settings.AUTH0_AUDIENCE,
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "scope": "openid profile email",
            "connection": settings.AUTH0_CONNECTION,
        }

        url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            return Response(
                {"error": response.json()},
                status=response.status_code,
            )

        return Response(response.json(), status=status.HTTP_200_OK)
