import json
from urllib.parse import quote_plus, urlencode
from authlib.integrations.django_client import OAuth
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from auth_service.settings import AUTH0_CALLBACK_URL, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_DOMAIN
from auth_service.users.models import UserProfile

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)


def index_view(request):
    """ Render the main application page with user session data."""
    return render(
        request,
        "auth/index.html",
        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
        },
    )


def login_view(request):
    """Redirect user to Auth0 login page."""
    return oauth.auth0.authorize_redirect(request, AUTH0_CALLBACK_URL)


def callback_view(request):
    """ Handle Auth0 callback after user authentication. Creates or retrieves user profile and saves session data."""
    token = oauth.auth0.authorize_access_token(request)
    user_info = token.get('userinfo', {})

    # Create or get user profile
    user_profile, created = UserProfile.objects.get_or_create(
        auth0_user_id=user_info['sub'],
        defaults={
            'email': user_info['email'],
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'preferences': user_info.get('preferences', {})
        }
    )

    request.session["user"] = token
    return redirect(request.build_absolute_uri(reverse("index")))


def logout_view(request):
    """Clear user session and redirect to Auth0 logout endpoint."""
    request.session.clear()

    return redirect(
        f"https://{AUTH0_DOMAIN}/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


def profile_view(request):
    """Get current authenticated user's profile information."""
    user_session = request.session.get("user")

    if not user_session:
        return JsonResponse(
            {"error": "No/invalid token"},
            status=401
        )

    user_info = user_session.get("userinfo", {})

    response_data = {
        "id": user_info.get("id"),
        "email": user_info.get("email"),
        "firstName": user_info.get("first_name", ""),
        "lastName": user_info.get("last_name", ""),
        "preferences": {}
    }

    return JsonResponse(response_data, status=200)


def get_profile(request, user_id):
    """Get a specific user's profile by their Auth0 user ID."""

    try:
        user = UserProfile.objects.get(auth0_user_id=user_id)
        return JsonResponse({
            "id": user.auth0_user_id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "preferences": user.preferences
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


@csrf_exempt
def update_profile(request, user_id):
    """Update a specific user's profile information."""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        user = UserProfile.objects.get(auth0_user_id=user_id)
        data = json.loads(request.body)

        user.first_name = data.get("firstName", user.first_name)
        user.last_name = data.get("lastName", user.last_name)
        user.email = data.get("email", user.email)
        user.preferences = data.get("preferences", user.preferences)
        user.save()

        return JsonResponse({"message": "Updated successfully"})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


def list_all_users(request):
    """Get a list of all user profiles in the system."""
    users = UserProfile.objects.all()
    user_list = []

    for user in users:
        user_list.append({
            "id": user.auth0_user_id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "preferences": user.preferences,
            "createdAt": user.created_at.isoformat()
        })

    return JsonResponse({"users": user_list, "count": len(user_list)})
