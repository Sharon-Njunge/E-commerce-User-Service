from rest_framework import serializers
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", read_only=True)
    lastName = serializers.CharField(source="last_name", read_only=True)
    preferences = serializers.DictField(default=dict, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "firstName", "lastName", "preferences"]
        read_only_fields = ["id", "email"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", required=False)
    lastName = serializers.CharField(source="last_name", required=False)
    preferences = serializers.DictField(required=False)

    class Meta:
        model = User
        fields = ["firstName", "lastName", "preferences"]
