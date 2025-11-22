from django.contrib.contenttypes.models import ContentType

from apps.sport_center.models import SportCenter, ImageSport
from apps.user.serializer_container import (
    Q, serializers, RoleSystemEnum, AppStatus, Response, status, os, settings, delete_file
)


def delete_sport_images(instance, instance_model):
    instance_ct = ContentType.objects.get_for_model(instance_model)
    # Get all ImageSport records related to this SportCenter
    image_sports = ImageSport.objects.filter(
        content_type=instance_ct,
        object_id=instance.id
    )
    # Delete media files and ImageSport records
    for image_sport in image_sports:
        if image_sport.file:
            # Get the full path to the file
            file_path = os.path.join(settings.MEDIA_ROOT, str(image_sport.file))
            file_path_pr = os.path.join(settings.MEDIA_ROOT, str(image_sport.preview))

            delete_file(file_path)
            delete_file(file_path_pr)

        image_sport.delete()


class SportCenterDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    total_field = serializers.IntegerField(read_only=True)

    class Meta:
        model = SportCenter
        fields = ['id', 'owner', 'images', 'name', 'address', 'total_field', 'created_at']

    def get_images(self, obj):
        image_map = self.context.get('image_map', {})
        return image_map.get(obj.id, [])

    @staticmethod
    def get_owner(obj):
        if obj.owner:
            return {
                'id': obj.owner.id,
                'full_name': obj.owner.full_name,
                'phone': obj.owner.phone
            }
        return {}


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
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return Response(status=status.HTTP_200_OK, data={"detail": "Update center successfully"})
