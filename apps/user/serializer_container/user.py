from apps.user.models import User
from apps.user.serializer_container import serializers


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}, 'verify_code': {'write_only': True}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}, 'verify_code': {'write_only': True}}
        read_only_field = ['id', 'created_at']

    # --------------------VALIDATION-------------------------
    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            pass

