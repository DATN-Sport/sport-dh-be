from apps.booking.models import RentalSlot
from apps.user.serializer_container import (
    serializers, RoleSystemEnum, AppStatus, Response, status
)


class RentalSlotDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = RentalSlot
        fields = '__all__'

    def get_images(self, obj):
        image_map = self.context.get('image_map', {})
        return image_map.get(obj.id, [])


class RentalSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalSlot
        fields = ['name', 'time_slot']

    def validate(self, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return Response(status=status.HTTP_200_OK)
