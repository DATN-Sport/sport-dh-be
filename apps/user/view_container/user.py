from apps.user.serializers import (
    serializers, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer, UserSettingUpdateSerializer
)
from apps.user.view_container import (
    Response, permissions, APIView, swagger_auto_schema, IsUser, ModelViewSet, action, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, User, RoleSystemEnum,
    AppStatus, UserFilter
)


class UserDetailViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserDetailSerializer

    @swagger_auto_schema(
        operation_description="Lấy thông tin chi tiết của user hiện tại",
        responses={
            200: UserDetailSerializer,
            401: 'Unauthorized - Cần đăng nhập'
        },
        security=[{'Basic': []}, {'Bearer': []}],
        tags=['user']
    )
    def get(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class UserViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update']:
            return UserUpdateSerializer
        elif self.action == 'update_settings':
            return UserSettingUpdateSerializer
        return UserDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        if request.user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put'],
        url_path='update/settings/',
    )
    @swagger_auto_schema(
        request_body=UserSettingUpdateSerializer,
        responses={200: UserDetailSerializer()}
    )
    def update_settings(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance = self.get_object()
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






