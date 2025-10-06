from apps.user.serializer_container import (
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
        
        # Generate tokens using parent validation
        data = super().validate(attrs)
        
        # Store tokens for cookie setting (will be handled in the view)
        self.access_token = data['access']
        self.refresh_token = data['refresh']
        
        # Return user data only (tokens will be set as cookies)
        return {
            "user": user.to_dict(),
            "message": "Login successful. Tokens set as cookies."
        }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        refresh = attrs.get('refresh')
        if not refresh:
            raise serializers.ValidationError(AppStatus.NOT_REFRESH.message)
        
        refresh_token = RefreshToken(refresh)
        new_access_token = str(refresh_token.access_token)
        
        # Store new access token for cookie setting
        self.access_token = new_access_token
        
        # Return success message only (token will be set as cookie)
        return {
            'message': 'Token refreshed successfully. New access token set as cookie.'
        }

