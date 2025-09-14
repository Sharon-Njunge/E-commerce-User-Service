from rest_framework.permissions import BasePermission

class HasPermission(BasePermission):
    """Check if JWT contains required permission"""

    def __init__(self, required_permission=None):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        payload = getattr(request, "user", None)
        if not payload:
            return False

        if self.required_permission:
            return self.required_permission in payload.get("permissions", [])
        return True
