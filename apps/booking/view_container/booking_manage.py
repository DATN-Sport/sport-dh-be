from apps.booking.models import Booking
from apps.booking.serializers import (
    serializers, BookingManageDetailSerializer, BookingCreateSerializer, BookingListTiniSerializer,
    BookingBulkCreateSerializer, BookingBulkCreateMonthSerializer
)
from apps.booking.view_container.filter import BookingFilter, BookingManageFilter
from apps.user.view_container import (
    Response, IsUser, ModelViewSet, status, IsOwner,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus, action
)


class BookingManageViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = Booking.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookingManageFilter
    ordering_fields = ['price', 'booking_date', 'status', 'created_at']
    ordering = ('booking_date', )

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.select_related(
            'user',
            'sport_field',
            'sport_field__sport_center',
            'rental_slot'
        )

        if user.role == RoleSystemEnum.OWNER.value:
            qs = qs.filter(sport_field__sport_center__owner=user)
        elif user.role == RoleSystemEnum.USER.value:
            qs = qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        if self.action == 'bulk_create_day':
            return BookingBulkCreateSerializer
        if self.action == 'bulk_create_month':
            return BookingBulkCreateMonthSerializer
        return BookingManageDetailSerializer

    def get_object(self):
        booking_id = self.kwargs['pk']
        booking = Booking.objects.filter(id=booking_id).first()
        if not booking:
            raise serializers.ValidationError(AppStatus.INVALID_ID.message)
        return booking

    @action(detail=False, methods=['post'], url_path='bulk-create-day/')
    def bulk_create_day(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {'message': 'Bookings created successfully','data': result},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='bulk-create-month/')
    def bulk_create_month(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {'message': f'Bookings created successfully for {result["num_days"]} days','data': result},
            status=status.HTTP_200_OK
        )

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
