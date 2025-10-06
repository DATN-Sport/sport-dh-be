from apps.user.models import User
from apps.user.serializer_container import serializers, RoleSystemEnum, AppStatus, make_password, validate_create_user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}, 'verify_code': {'write_only': True}}


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'role', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True, "min_length": 8}}

    def create(self, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        validate_create_user(validated_data)

        password = validated_data.pop('password')
        hashed_password = make_password(password)
        if validated_data['role'] == RoleSystemEnum.ADMIN.value:
            validated_data['is_superuser'] = True

        instance = super().create({**validated_data, 'password': hashed_password,
                                   'full_name': validated_data['username'], 'is_active': True})
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    avatar_upload = serializers.ImageField(required=True, allow_null=False, write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'address', 'device_tokens', 'avatar_upload']


