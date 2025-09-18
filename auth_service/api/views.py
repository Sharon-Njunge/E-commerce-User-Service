import json
import requests

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings


def get_management_token():
    """Get Auth0 Management API token"""
    url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "audience": f"https://{settings.AUTH0_DOMAIN}/api/",
        "grant_type": "client_credentials"
    }
    response = requests.post(url, json=payload)
    return response.json().get("access_token")


@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not data.get("email") or not data.get("password"):
        return JsonResponse({"error": "Email and password required"}, status=400)

    token = get_management_token()
    if not token:
        return JsonResponse({"error": "Auth failed"}, status=500)

    url = f"https://{settings.AUTH0_DOMAIN}/api/users"
    headers = {"Authorization": f"Bearer {token}"}

    user_data = {
        "connection": "Username-Password-Authentication",
        "email": data["email"],
        "password": data["password"],
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "preferences": data.get("preferences", {}),
    }

    response = requests.post(url, json=user_data, headers=headers)

    if response.status_code == 201:
        user = response.json()
        return JsonResponse({
            "message": "User created",
            "user": {
                "id": user.get("id"),
                "email": user.get("email"),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
            }
        }, status=201)
    return JsonResponse({"error": "Registration failed"}, status=400)


@require_http_methods(["GET"])
def list_users(request):
    """List all users"""
    token = get_management_token()
    if not token:
        return JsonResponse({"error": "Auth failed"}, status=500)

    url = f"https://{settings.AUTH0_DOMAIN}/api/users"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch users"}, status=400)

    users = []
    for user in response.json():
        users.append({
            "id": user.get("id"),
            "email": user.get("email"),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "preferences": user.get("preferences", {}),
        })

    return JsonResponse({"users": users})


@require_http_methods(["GET"])
def get_profile(request):
    """Get current user's profile"""
    user_session = request.session.get("user")

    if not user_session:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    user_info = user_session.get("userinfo", {})

    return JsonResponse({
        "id": user_info.get("id"),
        "email": user_info.get("email"),
        "first_name": user_info.get("first_name", ""),
        "last_name": user_info.get("last_name", ""),
        "preferences": user_info.get("preferences", {}),
    })


@csrf_exempt
@require_http_methods(["PUT"])
def update_profile(request):
    """Update current user's profile"""
    user_session = request.session.get("user")

    if not user_session:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_id = user_session.get("userinfo", {}).get("id")
    token = get_management_token()

    if not token:
        return JsonResponse({"error": "Auth failed"}, status=500)

    url = f"https://{settings.AUTH0_DOMAIN}/api/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}

    update_data = {}
    if "first_name" in data:
        update_data["first_name"] = data["first_name"]
    if "last_name" in data:
        update_data["last_name"] = data["last_name"]
    if "preferences" in data:
        update_data["preferences"] = data["preferences"]

    response = requests.patch(url, json=update_data, headers=headers)

    if response.status_code == 200:
        return JsonResponse({"message": "Updated successfully"})
    return JsonResponse({"error": "Update failed"}, status=400)
