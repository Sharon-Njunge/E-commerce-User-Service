from rest_framework import permissions


class HasAuth0Permission(permissions.BasePermission):
    """
    Check if the JWT token has the required Auth0 permission.
    Usage:
        permission_classes = [HasAuth0Permission]
        required_permission = "create:orders"
    """

    required_permission = None

    def has_permission(self, request, view):
        token_payload = request.user  # comes from Auth0JWTAuthentication
        if not token_payload:
            return False

        token_permissions = token_payload.get("permissions", [])
        if self.required_permission:
            return self.required_permission in token_permissions

        return True
    
