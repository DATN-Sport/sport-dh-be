from apps.user.models import User
from apps.user.serializer_container import (
    serializers, RoleSystemEnum, AppStatus, make_password, validate_create_user, settings
)


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
                                   'full_name': validated_data['full_name'], 'is_active': True})
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    avatar_upload = serializers.ImageField(required=False, write_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'address', 'role', 'phone', 'device_tokens', 'avatar_upload', 'avatar_url']

    @staticmethod
    def get_avatar_url(obj):
        if obj.avatar:
            return f"{settings.MEDIA_URL}{obj.avatar.name}"
        return None

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value and user.id != instance.id:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

        avatar_file = validated_data.pop('avatar_upload', None)
        if avatar_file:
            instance.avatar.delete(save=False)
            instance.avatar = avatar_file
        return super().update(instance, validated_data)


class UserSettingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['settings']

    def validate(self, setting):
        pass

    def update_settings_current_user(self, validated_data):
        user = self.context['request'].user
        self.validate(validated_data.get('settings', {}))
        return super().update(user, validated_data)
