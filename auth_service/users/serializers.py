# auth_service/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'firstName', 'lastName']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        # Use email as username since Django's User model requires username
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(password=password, **validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName']
        read_only_fields = ['id', 'email']