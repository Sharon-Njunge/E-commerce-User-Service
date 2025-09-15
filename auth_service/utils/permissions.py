from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """Check if JWT contains the required permission"""

    required_permission = None  # class attribute

    def has_permission(self, request, view):
        payload = getattr(request, "user", None)
        if not payload:
            return False

        if self.required_permission:
            return self.required_permission in payload.get("permissions", [])
        return True


# Factory for convenience
def permission_required(permission):
    class CustomPermission(HasPermission):
        required_permission = permission
    return CustomPermission
