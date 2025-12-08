from apps.booking.serializers import BookingStatsQuerySerializer
from apps.booking.utils.stats import get_booking_stats
from apps.user.view_container import (
    APIView,
    Response,
    openapi,
    swagger_auto_schema,
    status,
    IsOwner,
)


class BookingStatsView(APIView):
    """
    API thống kê doanh thu/booking cho admin & chủ sân.
    - Admin xem tất cả.
    - Chủ sân chỉ xem dữ liệu sport_center do mình sở hữu.
    """

    permission_classes = [IsOwner]

    @swagger_auto_schema(
        operation_summary="Thống kê booking/doanh thu",
        operation_description=(
            "Trả về tổng doanh thu, số booking, phân rã theo trạng thái, trung tâm, "
            "top sân. Cho phép lọc theo preset hoặc khoảng ngày."
        ),
        query_serializer=BookingStatsQuerySerializer(),
        responses={200: "OK"},
    )
    def get(self, request):
        serializer = BookingStatsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        stats = get_booking_stats(
            user=request.user,
            preset=serializer.validated_data.get("preset"),
            date_from=serializer.validated_data.get("date_from"),
            date_to=serializer.validated_data.get("date_to"),
            statuses=serializer.get_statuses(),
            limit_top_fields=serializer.get_limit_top_fields(),
        )
        return Response(stats, status=status.HTTP_200_OK)
