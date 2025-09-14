# auth_service/utils/auth0.py
import os
import jwt
import requests
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
            raise exceptions.AuthenticationFailed("Invalid Authorization header format.")

        token = parts[1]

        try:
            # Fetch JWKS keys from Auth0
            jwks = requests.get(AUTH0_JWKS_URL).json()
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
                raise exceptions.AuthenticationFailed("Invalid header. No matching JWK.")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired.")
        except jwt.JWTClaimsError:
            raise exceptions.AuthenticationFailed("Incorrect claims. Check audience and issuer.")
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Unable to parse authentication token: {str(e)}")

        return (payload, None)
