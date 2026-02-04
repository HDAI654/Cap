from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class RotationSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    device = serializers.CharField()


class RevokeSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    session_id = serializers.CharField()
