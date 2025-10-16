from django.contrib.contenttypes.models import ContentType
from apps.sport_center.models import SportCenter, ImageSport
from apps.sport_center.serializers import (
    serializers, SportCenterDetailSerializer, SportCenterSerializer, ImageSportDeleteSerializer, delete_sport_images
)
from apps.sport_center.view_container.filter import SportCenterFilter
from apps.user.view_container import (
    Response, swagger_auto_schema, IsUser, IsOwner, ModelViewSet, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus, openapi, DestroyAPIView
)
from apps.utils.mapping_data import MappingData


class SportCenterViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = SportCenter.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SportCenterFilter
    ordering_fields = ['name', 'address', 'created_at']
    ordering = ('-created_at',)
    instance_ct = ContentType.objects.get_for_model(SportCenter)

    def get_queryset(self):
        return SportCenter.objects.select_related("owner")

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return SportCenterSerializer
        return SportCenterDetailSerializer

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
        instance_ct = ContentType.objects.get_for_model(SportCenter)
        images = ImageSport.objects.filter(object_id=instance.id, content_type_id=instance_ct.id).values('id', 'preview', 'file')
        image_map = {}
        for img in images:
            image_info = {
                'id': img['id'],
                'preview': img['preview'],
                'file': img['file']
            }
            image_map.setdefault(instance.id, []).append(image_info)
        serializer = self.get_serializer(instance, context={'image_map': image_map})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != RoleSystemEnum.ADMIN.value and request.user != instance.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        delete_sport_images(instance, SportCenter)
        instance.delete()
        return Response({"detail": "Sport Center deleted successfully"}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            sport_center_ids = [obj.id for obj in page]
        else:
            sport_center_ids = list(queryset.values_list('id', flat=True))

        instance_ct = ContentType.objects.get_for_model(SportCenter)
        images = (ImageSport.objects.filter(object_id__in=sport_center_ids, content_type_id=instance_ct.id)
                  .values('id', 'object_id', 'preview', 'file'))
        image_map = MappingData(obj_images=images).mapping_img()

        serializer = self.get_serializer(
            page if page is not None else queryset, many=True, context={'image_map': image_map})

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class ImageSportDeleteViewSet(DestroyAPIView):
    queryset = ImageSport.objects.all()
    Permission_classes = [IsOwner]
    serializer_class = ImageSportDeleteSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete(instance)
        return Response({"detail": "Image deleted successfully"}, status=status.HTTP_200_OK)

