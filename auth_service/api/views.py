from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from auth_service.settings import AUTH0_DOMAIN
from auth_service.utils.permissions import HasAuth0Permission
from auth_service.api.utils import call_auth0


class UserListView(APIView):
    """List all users from Auth0"""
    permission_classes = [IsAuthenticated, HasAuth0Permission]
   
    def get_permissions(self):
        permissions = super().get_permissions()
        for permission in permissions:
            if isinstance(permission, HasAuth0Permission):
                permission.required_permission = "read:users"
        return permissions

    def get(self, reuest):
        """List all users from Auth0"""
        try:
            auth0_url = "https://{AUTH0_DOMAIN}/api/v1/users"
            users_data = call_auth0(auth0_url)
            
            if not users_data:
                return Response({"users": [], "total": 0}, status=200)
            
            formatted_users = []
            for user in users_data:
                formatted_users.append({
                    "user_id": user.get("user_id"),
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "email_verified": user.get("email_verified"),
                    "created_at": user.get("created_at")
                })
            
            return Response({
                "users": formatted_users,
                "total": len(formatted_users)
            }, status=200)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve users: {str(e)}"},
                status=500
            )


class UserDetailView(APIView):
    """Get and update individual user from Auth0"""
    permission_classes = [IsAuthenticated, HasAuth0Permission]
    
    def get_permissions(self):
        permissions = super().get_permissions()
        for permission in permissions:
            if isinstance(permission, HasAuth0Permission):
                permission.required_permission = "read:users"
        return permissions
    
    def get(self, request, user_id):
        """Retrieve user information in Auth0"""
        try:
            auth0_url = f"https://{AUTH0_DOMAIN}/api/v1/users/{user_id}"
            user_data = call_auth0(auth0_url)
            
            if not user_data:
                return Response(
                    {"error": "User not found"}, 
                    status=404
                )
            
            formatted_user = {
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "email_verified": user_data.get("email_verified"),
                "created_at": user_data.get("created_at"),
            }
            
            return Response(formatted_user, status=200)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user: {str(e)}"},
                status=404
            )
    
    def put(self, request, user_id):
        """Update user information in Auth0"""
        permissions = self.get_permissions()
        for permission in permissions:
            if isinstance(permission, HasAuth0Permission):
                permission.required_permission = "update:users"
        
        try:
            update_data = {}
            if "name" in request.data:
                update_data["name"] = request.data["name"]
            if "email" in request.data:
                update_data["email"] = request.data["email"]
            
            auth0_url = f"https://{AUTH0_DOMAIN}/api/v1/users/{user_id}"
            updated_user = call_auth0(auth0_url, method="PATCH", data=update_data)
          
            if not updated_user:
                return Response(
                    {"error": "Failed to update user"},
                    status=400
                )
            
            formatted_user = {
                "email": updated_user.get("email"),
                "name": updated_user.get("name"),
            }
           
            return Response(formatted_user, status=200)
          
        except Exception as e:
            return Response(
                {"error": f"Failed to update user: {str(e)}"},
                status=400
       )