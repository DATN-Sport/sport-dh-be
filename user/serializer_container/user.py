from user.models import User
from user.serializer_container import serializers


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}, 'verify_code': {'write_only': True}}


class UserUpdateSerializer(serializers.ModelSerializer):
    pass
