from apps.user.serializers import (
    UserDetailSerializer
)
from apps.user.view_container import (
    Response, permissions, APIView, swagger_auto_schema
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
        tags=['User']
    )
    def get(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

#
# class UserAdminListViewSet(APIView):
#     permission_classes = [permissions.]
