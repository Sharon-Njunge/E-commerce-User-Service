from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "created_at"]
        read_only_fields = ["id", "email"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
