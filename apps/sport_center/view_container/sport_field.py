from apps.sport_center.models import SportField, ImageSport, SportCenter
from apps.sport_center.serializers import (
    serializers, SportFieldDetailSerializer, SportFieldSerializer, delete_sport_images
)
from apps.sport_center.view_container.filter import SportFieldFilter
from apps.user.view_container import (
    Response, swagger_auto_schema, IsUser, ModelViewSet, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus, openapi
)
from apps.utils.mapping_data import MappingData


class SportFieldViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = SportField.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SportFieldFilter
    ordering_fields = ['name', 'address', 'price', 'created_at']
    ordering = ('-created_at',)

    def get_queryset(self):
        return SportField.objects.select_related('sport_center')

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return SportFieldSerializer
        return SportFieldDetailSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='images', in_=openapi.IN_FORM, description='List of image files', type=openapi.TYPE_FILE,
                required=False, multiple=True,
            ),
        ],
        consumes=['multipart/form-data'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='images', in_=openapi.IN_FORM, description='List of image files', type=openapi.TYPE_FILE,
                required=False, multiple=True,
            ),
        ],
        consumes=['multipart/form-data'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        images = ImageSport.objects.filter(object_id=instance.id).values('id', 'file')
        image_map = {}
        for img in images:
            image_info = {
                'id': img['id'],
                'file': img['file']
            }
            image_map.setdefault(instance.id, []).append(image_info)
        serializer = self.get_serializer(instance, context={'image_map': image_map})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != RoleSystemEnum.ADMIN.value and request.user != instance.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        delete_sport_images(instance, SportField)
        instance.delete()
        return Response({"detail": "Sport Field deleted successfully"}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            sport_field_ids = [obj.id for obj in page]
        else:
            sport_field_ids = list(queryset.values_list('id', flat=True))

        images = (ImageSport.objects.filter(object_id__in=sport_field_ids).
                  values('id', 'object_id', 'file', 'preview'))
        image_map = MappingData(obj_images=images).mapping_img()

        serializer = self.get_serializer(
            page if page is not None else queryset, many=True, context={'image_map': image_map})

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


