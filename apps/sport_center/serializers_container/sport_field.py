from django.contrib.contenttypes.models import ContentType

from apps.sport_center.models import SportField, ImageSport, SportCenter
from apps.user.serializer_container import (
    serializers, RoleSystemEnum, AppStatus, Response, status, os, settings
)


class SportFieldDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = SportField
        fields = ['id', 'sport_center', 'images', 'name', 'address', 'sport_type', 'price', 'status', 'created_at']

    def get_images(self, obj):
        image_map = self.context.get('image_map', {})
        return image_map.get(obj.id, [])


class SportFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportField
        fields = ['sport_center', 'name', 'price', 'status', 'sport_type']

    def validate_permission(self, validated_data):
        sport_center = validated_data.get('sport_center', None)
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value and user != sport_center.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

    def validate_update(self, instance):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value and user != instance.sport_center.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

    def validate_create(self, validated_data):
        self.validate_permission(validated_data)
        sport_field = SportField.objects.filter(name=validated_data["name"], sport_center=validated_data["sport_center"])
        if sport_field:
            raise serializers.ValidationError(AppStatus.SPORT_FIELD_WITH_INFO_EXIST.message)
        return validated_data

    @staticmethod
    def save_image(images, obj_model, obj_id):
        ct = ContentType.objects.get_for_model(obj_model)
        for img in images:
            ImageSport.objects.create(file=img, content_type=ct, object_id=obj_id)

    def create(self, validated_data):
        self.validate_create(validated_data)
        images = self.context['request'].FILES.getlist('images')
        validated_data['address'] = validated_data.get('sport_center').address
        sport_field = super().create(validated_data)
        self.save_image(images, SportField, sport_field.id)
        return sport_field

    def update(self, instance, validated_data):
        self.validate_update(instance)
        images = self.context['request'].FILES.getlist('images')
        self.save_image(images, SportField, instance.id)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class ImageSportDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageSport
        fields = ['id']

    @staticmethod
    def delete_file(instance):
        file_path = os.path.join(settings.MEDIA_ROOT, str(instance.file))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")

    def validate_permission(self, instance):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value:
            model_sport = instance.content_type.model
            if model_sport == 'sportfield' and user != SportField.objects.get(id=instance.object_id).sport_center.owner:
                return serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
            elif model_sport == 'sportcenter' and user != SportCenter.objects.get(id=instance.object_id).owner:
                return serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

    def delete(self, instance):
        self.validate_permission(instance)
        self.delete_file(instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
