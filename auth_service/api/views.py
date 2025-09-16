from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import ProfileUpdateSerializer, UserProfileSerializer

# Create your views here.


@api_view(["GET"])
def get_users(request):
    """Get list of users"""
    user_data = request.session.get("user")
    if not user_data:
        return Response(
            {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
        )

    return Response({"users": []})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)
    return Response(serializer.errors, status=400)


@api_view(["POST"])
def signup(request):
    """Handle user signup via Auth0"""
    signup_url = f"https://{settings.AUTH0_DOMAIN}/authorize?response_type=code&client_id={settings.AUTH0_CLIENT_ID}&redirect_uri={settings.AUTH0_CALLBACK_URL}&scope=openid profile email&screen_hint=signup"

    return Response(
        {"signup_url": signup_url, "message": "Redirect to this URL to complete signup"}
    )
