from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed
from auth_service.utils.auth0 import Auth0JWTAuthentication


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/api/v1/protected/"):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Authorization header missing or invalid.")

            token = auth_header.split(" ")[1]
            validator = Auth0JWTAuthentication()
            payload = validator.authenticate_token(token)
            request.auth = payload
