from apps.user.models import User
from rest_framework import serializers
from apps.utils.constant_status import AppStatus


def validate_create_user(validated_data):
    user = User.objects.filter(username=validated_data["username"]).first()
    if user:
        raise serializers.ValidationError(AppStatus.USERNAME_ALREADY_EXIST.message)
    user = User.objects.filter(email=validated_data["email"]).first()
    if user:
        raise serializers.ValidationError(AppStatus.EMAIL_ALREADY_EXIST.message)
