import json
import time
from typing import Dict, List, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import load_pem_x509_certificate
from jose import jwt
from jose.constants import ALGORITHMS
import base64

class MockAuth0:
    def __init__(self, domain: str = "mock-auth0.com"):
        self.domain = domain
        self.private_key = self._generate_private_key()
        self.public_key = self.private_key.public_key()
        self.jwks = self._generate_jwks()
        self.tokens = {}
        self.users = {}
        self.refresh_tokens = {}
        
    def _generate_private_key(self):
        """Generate RSA private key for signing tokens"""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
    
    def _generate_jwks(self):
        """Generate JWKS (JSON Web Key Set)"""
        public_numbers = self.public_key.public_numbers()
        
        return {
            "keys": [{
                "kty": "RSA",
                "use": "sig",
                "kid": "mock-key-1",
                "alg": ALGORITHMS.RS256,
                "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes(256, byteorder='big')).decode('utf-8').rstrip('='),
                "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes(3, byteorder='big')).decode('utf-8').rstrip('=')
            }]
        }
    
    def get_jwks(self):
        """Return JWKS endpoint response"""
        return self.jwks
    
    def create_user(self, user_id: str, email: str, **kwargs):
        """Create a mock user"""
        user_data = {
            "sub": user_id,
            "email": email,
            "email_verified": kwargs.get('email_verified', True),
            "given_name": kwargs.get('given_name', ''),
            "family_name": kwargs.get('family_name', ''),
            "preferences": kwargs.get('preferences', {})
        }
        self.users[user_id] = user_data
        return user_data
    
    def issue_token(self, user_id: str, expires_in: int = 3600, token_type: str = "access"):
        """Issue a JWT token for a user"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        now = int(time.time())
        
        payload = {
            "iss": f"https://{self.domain}/",
            "sub": user_id,
            "aud": "mock-api-identifier",
            "iat": now,
            "exp": now + expires_in,
            "azp": "mock-client-id",
            "scope": "openid profile email",
            "gty": "password",
            "email": user["email"],
            "email_verified": user["email_verified"],
            "given_name": user.get("given_name", ""),
            "family_name": user.get("family_name", ""),
            "preferences": user.get("preferences", {})
        }
        
        # Add token type specific claims
        if token_type == "access":
            payload["type"] = "access"
        elif token_type == "refresh":
            payload["type"] = "refresh"
            payload["exp"] = now + 86400 * 7  # 7 days for refresh tokens
        
        # Sign the token
        headers = {"kid": "mock-key-1", "alg": ALGORITHMS.RS256}
        token = jwt.encode(
            payload, 
            self.private_key, 
            algorithm=ALGORITHMS.RS256,
            headers=headers
        )
        
        if token_type == "access":
            self.tokens[token] = payload
        elif token_type == "refresh":
            self.refresh_tokens[token] = payload
            
        return token
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode a JWT token"""
        try:
            # Verify using public key
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[ALGORITHMS.RS256],
                audience="mock-api-identifier",
                issuer=f"https://{self.domain}/"
            )
            
            # Check if token exists in our registry
            if token not in self.tokens and token not in self.refresh_tokens:
                raise jwt.JWTError("Token not recognized")
                
            return payload
        except jwt.JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def introspect_token(self, token: str) -> Dict:
        """Token introspection endpoint"""
        try:
            payload = self.verify_token(token)
            return {
                "active": True,
                "sub": payload["sub"],
                "aud": payload["aud"],
                "exp": payload["exp"],
                "iat": payload["iat"],
                "email": payload["email"],
                "email_verified": payload.get("email_verified", True)
            }
        except ValueError:
            return {"active": False}
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        if refresh_token not in self.refresh_tokens:
            raise ValueError("Invalid refresh token")
        
        payload = self.refresh_tokens[refresh_token]
        user_id = payload["sub"]
        
        new_access_token = self.issue_token(user_id, token_type="access")
        
        return {
            "access_token": new_access_token,
            "expires_in": 3600,
            "token_type": "Bearer"
        }

# Global mock instance
mock_auth0 = MockAuth0()