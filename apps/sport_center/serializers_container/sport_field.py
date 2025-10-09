from django.contrib.contenttypes.models import ContentType

from apps.sport_center.models import SportField, SportCenter, ImageSport
from apps.user.serializer_container import (
    Q, serializers, RoleSystemEnum, AppStatus, Response, status
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

    def validate(self, validated_data):
        sport_center = validated_data.get('sport_center', None)
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value and user != sport_center.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        sport_field = SportField.objects.filter(name=validated_data["name"])
        if sport_field:
            raise serializers.ValidationError(AppStatus.SPORT_FIELD_WITH_INFO_EXIST.message)
        return validated_data

    @staticmethod
    def save_image(images, obj_model, obj_id):
        ct = ContentType.objects.get_for_model(obj_model)
        for img in images:
            ImageSport.objects.create(file=img, content_type=ct, object_id=obj_id)

    def create(self, validated_data):
        images = self.context['request'].FILES.getlist('images')
        validated_data['address'] = validated_data.get('sport_center').address
        sport_field = super().create(validated_data)
        self.save_image(images, SportField, sport_field.id)
        return sport_field

    def update(self, instance, validated_data):
        images = self.context['request'].FILES.getlist('images')
        self.save_image(images, SportField, instance.id)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return Response(status=status.HTTP_200_OK)
