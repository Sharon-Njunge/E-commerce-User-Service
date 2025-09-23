import requests
from django.conf import settings
from jose import jwt
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class Auth0JWTAuthentication(BaseAuthentication):
    """
    Custom authentication class for validating Auth0 JWT tokens.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()

        if parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed(
                "Authorization header must start with Bearer"
            )
        elif len(parts) == 1:
            raise exceptions.AuthenticationFailed("Token not found")
        elif len(parts) > 2:
            raise exceptions.AuthenticationFailed(
                "Authorization header must be Bearer token"
            )

        token = parts[1]

        try:
            payload = self.decode_jwt(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")

        return (payload, token)  # user, auth

    def decode_jwt(self, token):
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if not rsa_key:
            raise exceptions.AuthenticationFailed("Unable to find appropriate key.")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return payload
