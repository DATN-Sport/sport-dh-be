from apps.sport_center.models import SportCenter
from apps.user.serializers import (
    serializers, SportCenterDetailSerializer, SportCenterCreateSerializer, SportCenterUpdateSerializer,
)
from apps.user.view_container import (
    Response, permissions, APIView, swagger_auto_schema, IsUser, IsOwner, IsAdmin, ModelViewSet, action, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus, SportCenterFilter
)


class SportCenterViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = SportCenter.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SportCenterFilter
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'create':
            return SportCenterCreateSerializer
        elif self.action in ['update']:
            return SportCenterUpdateSerializer
        return SportCenterDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != RoleSystemEnum.ADMIN.value or request.use != instance.owner:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user = request.user

        if user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)






