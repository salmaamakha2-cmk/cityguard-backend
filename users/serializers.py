from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'phone', 'role')
    
    def create(self, validated_data):
        # Set is_staff to True for admin and technician roles to show green check in Django Admin
        role = validated_data.get('role')
        if role in ['admin', 'technician']:
            validated_data['is_staff'] = True
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'profile_picture', 'date_joined', 'is_active')