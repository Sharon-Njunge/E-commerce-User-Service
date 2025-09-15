import os
import requests
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AUTH0_JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"


class Auth0JWTAuthentication(BaseAuthentication):
    """
    Custom authentication class for validating Auth0-issued JWTs.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise exceptions.AuthenticationFailed(
                "Invalid Authorization header format."
            )

        token = parts[1]

        try:
            # Fetch JWKS keys from Auth0
            jwks = requests.get(AUTH0_JWKS_URL).json()
            unverified_header = jwt.get_unverified_header(token)

            rsa_key = next(
                (key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]),
                None,
            )

            if not rsa_key:
                raise exceptions.AuthenticationFailed(
                    "Invalid header. No matching JWK."
                )

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired.")
        except JWTClaimsError:
            raise exceptions.AuthenticationFailed(
                "Incorrect claims. Check audience and issuer."
            )
        except JWTError as e:
            raise exceptions.AuthenticationFailed(
                f"Unable to parse authentication token: {str(e)}"
            )

        # return (user, auth) → user can be mapped from payload["sub"]
        return (AnonymousUser(), token)
