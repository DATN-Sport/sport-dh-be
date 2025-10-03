from apps.user.models import User
from apps.user.serializer_container.user import UserDetailSerializer
from apps.user.serializer_container import (
    serializers, AppStatus, make_password, RefreshToken
)


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True, "min_length": 8}}

    def create(self, validated_data):
        user = User.objects.filter(username=validated_data["username"]).first()

        if user:
            raise serializers.ValidationError(AppStatus.USERNAME_ALREADY_EXIST.message)
        user = User.objects.filter(email=validated_data["email"]).first()
        if user:
            raise serializers.ValidationError(AppStatus.EMAIL_ALREADY_EXIST.message)

        password = validated_data.pop('password')
        hashed_password = make_password(password)

        instance = super().create({**validated_data, 'password': hashed_password,
                                   'full_name': validated_data['username'], 'is_active': False})
        return instance


class UserVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'verify_code']
        extra_kwargs = {
            'email': {'validators': []}
        }

    def update(self, instance, validated_data):
        email = validated_data.get("email")
        verify_code = validated_data.get("verify_code")
        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError(AppStatus.EMAIL_NOT_EXIST.message)
        if user.verify_code != verify_code:
            raise serializers.ValidationError(AppStatus.INVALID_VERIFY_CODE.message)

        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserDetailSerializer(user).data
        }
