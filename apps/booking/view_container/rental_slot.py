from apps.booking.models import RentalSlot
from apps.booking.serializers import (
    serializers, RentalSlotDetailSerializer, RentalSlotSerializer
)
from apps.booking.view_container.filter import RentalSlotFilter
from apps.user.view_container import (
    Response, IsUser, ModelViewSet, status,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus
)


class RentalSlotViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = RentalSlot.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RentalSlotFilter
    ordering_fields = ['name', 'time_slot']
    ordering = ('name', 'time_slot')

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return RentalSlotSerializer
        return RentalSlotDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance.delete()
        return Response({"detail": "Time slot deleted successfully"}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


