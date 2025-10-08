from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import status

from apps.sport_center.models import SportCenter, ImageSport
from apps.user.serializer_container import (
    serializers, RoleSystemEnum, AppStatus, make_password, validate_create_user, settings, Response
)


class SportCenterDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = SportCenter
        fields = ['id', 'owner', 'images', 'name', 'address', 'created_at']

    def get_images(self, obj):
        image_map = self.context.get('image_map', {})
        return image_map.get(obj.id, [])


class SportCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportCenter
        fields = ['owner', 'name', 'address']

    def validate_create(self, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        sport_center = SportCenter.objects.filter(
            Q(name=validated_data["name"]) | Q(address=validated_data["address"])).first()
        if sport_center:
            raise serializers.ValidationError(AppStatus.SPORT_CENTER_WITH_INFO_EXIST.message)
        if validated_data["owner"].role not in [RoleSystemEnum.ADMIN.value, RoleSystemEnum.OWNER.value]:
            raise serializers.ValidationError(AppStatus.OWNER_SPORT_CENTER_MUST_ROLE_OWNER.message)
        return

    @staticmethod
    def save_image(images, obj_model, object_id):
        ct = ContentType.objects.get_for_model(obj_model)
        for img in images:
            ImageSport.objects.create(file=img, content_type=ct, object_id=object_id)

    def create(self, validated_data):
        self.validate_create(validated_data)
        images = self.context['request'].FILES.getlist('images')
        sport_center = super().create(validated_data)
        self.save_image(images, SportCenter, sport_center.id)
        return sport_center

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value and user != instance.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        images = self.context['request'].FILES.getlist('images')
        self.save_image(images, SportCenter, instance.id)
        return Response(status=status.HTTP_200_OK)
