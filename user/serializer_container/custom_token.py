from user.models import User

from user.serializer_container import (
    AppStatus, serializers, TokenObtainPairSerializer, TokenRefreshSerializer, RefreshToken, authenticate, Dict, Any
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(max_length=256, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        username = attrs.get('username')
        password = attrs.get('password')

        if not username:
            raise serializers.ValidationError(AppStatus.ENTER_USERNAME_OR_EMAIL.message)
        username = username

        user = authenticate(request=self.context.get('request'), username=username, password=password)
        if not user or user.is_delete:
            raise serializers.ValidationError(AppStatus.USERNAME_OR_PASSWORD_INCORRECT.message)
        data = super().validate(attrs)

        data["user"] = user.to_dict()
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        refresh = attrs.get('refresh')
        if not refresh:
            raise serializers.ValidationError(AppStatus.NOT_REFRESH.message)
        refresh_token = RefreshToken(refresh)

        data = {
            'refresh': str(refresh_token),
            'access': str(refresh_token.access_token),
        }
        return data

