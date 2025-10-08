from apps.sport_center.models import SportCenter, ImageSport
from apps.sport_center.serializers import (
    serializers, SportCenterDetailSerializer, SportCenterSerializer,
)
from apps.sport_center.view_container.filter import SportCenterFilter
from apps.user.view_container import (
    Response, permissions, APIView, swagger_auto_schema, IsUser, IsOwner, IsAdmin, ModelViewSet, action, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus, openapi
)


class SportCenterViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = SportCenter.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SportCenterFilter
    ordering_fields = ['name', 'address', 'created_at']
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return SportCenterSerializer
        return SportCenterDetailSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='images',
                in_=openapi.IN_FORM,
                description='List of image files',
                type=openapi.TYPE_FILE,
                required=False,
                multiple=True,
            ),
        ],
        consumes=['multipart/form-data'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != RoleSystemEnum.ADMIN.value and request.user != instance.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        sport_center_ids = queryset.values_list('id', flat=True)
        images = ImageSport.objects.filter(object_id__in=sport_center_ids).values('object_id', 'file')
        image_map = {}
        for img in images:
            image_map.setdefault(img['object_id'], []).append(img['file'])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'image_map': image_map})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'image_map': image_map})
        return Response(serializer.data)


