from rest_framework.generics import CreateAPIView

from apps.booking.models import Booking
from apps.booking.serializers import (
    serializers, BookingDetailSerializer, BookingCreateSerializer, BookingListTiniSerializer,
    BookingBulkCreateSerializer, BookingUpdateSerializer
)
from apps.booking.view_container.filter import BookingFilter
from apps.user.view_container import (
    Response, IsUser, ModelViewSet, status, IsOwner,
    LimitOffsetPagination, MultiPartParser, FormParser, DjangoFilterBackend, OrderingFilter, RoleSystemEnum,
    AppStatus
)


class BookingViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = Booking.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookingFilter
    ordering_fields = ['price', 'booking_date', 'status', 'created_at']
    ordering = ('booking_date', )

    def get_queryset(self):
        return Booking.objects.select_related('user', 'sport_field', 'rental_slot')

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'update':
            return BookingUpdateSerializer
        return BookingDetailSerializer

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


class BookingListTiniViewSet(ModelViewSet):
    permission_classes = [IsUser]
    queryset = Booking.objects.all()
    serializer_class = BookingListTiniSerializer
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookingFilter
    ordering_fields = ['price', 'booking_date', 'status', 'created_at']
    ordering = ('booking_date',)

    def get_queryset(self):
        return Booking.objects.select_related('rental_slot')


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingBulkCreateViewSet(CreateAPIView):
    permission_classes = [IsOwner]
    queryset = Booking.objects.all()
    serializer_class = BookingBulkCreateSerializer

