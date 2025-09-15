import json
from urllib.request import urlopen

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError


class Auth0JSONWebTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for validating Auth0 JWT tokens.
    Returns a tuple (user, token) if authentication succeeds,
    or raises AuthenticationFailed otherwise.
    """

    def authenticate(self, request):
        auth = request.headers.get("Authorization")
        if not auth:
            return None

        parts = auth.split()
        if parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed(
                "Authorization header must start with Bearer"
            )
        if len(parts) == 1:
            raise exceptions.AuthenticationFailed("Token not found")
        if len(parts) > 2:
            raise exceptions.AuthenticationFailed(
                "Authorization header must be Bearer token"
            )

        token = parts[1]
        return self._authenticate_credentials(token)

    def _authenticate_credentials(self, token):
        # Fetch JWKS
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks = json.loads(urlopen(jwks_url).read())

        # Get key from token header
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next(
            (key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]),
            None,
        )

        if not rsa_key:
            raise exceptions.AuthenticationFailed("Unable to find appropriate key")

        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[settings.ALGORITHMS],
                audience=settings.API_IDENTIFIER,
                issuer=f"https://{settings.AUTH0_DOMAIN}/",
            )
        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token is expired")
        except JWTClaimsError:
            raise exceptions.AuthenticationFailed("Incorrect claims")
        except JWTError:
            raise exceptions.AuthenticationFailed("Unable to parse token")

        # At this point you could lookup a Django user from payload["sub"]
        user = AnonymousUser()
        return (user, token)
