"""
View để lấy danh sách booking PENDING (sân trống) theo format nested
cho chatbot sử dụng
"""
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from apps.depends.oauth2 import IsUser
from apps.booking.models import Booking
from apps.sport_center.models import SportCenter, SportField
from apps.utils.enum_type import StatusBookingEnum, StatusFieldEnum


class BookingAvailableView(APIView):
    """
    API lấy danh sách booking PENDING (sân trống) theo format nested
    Format: sport_center -> sport_field[] -> rental_slot[] (time_slot)
    """
    permission_classes = [IsUser]

    @swagger_auto_schema(
        operation_summary="Lấy danh sách sân trống (booking PENDING)",
        operation_description=(
            "Lấy danh sách booking PENDING (sân trống) theo format nested:\n"
            "- sport_center (name, address)\n"
            "  - sport_field[] (name, sport_type)\n"
            "    - rental_slot[] (time_slot - chỉ những slot trống từ booking PENDING)\n"
        ),
        manual_parameters=[
            openapi.Parameter(
                'booking_date',
                openapi.IN_QUERY,
                description="Ngày cần kiểm tra (YYYY-MM-DD). Mặc định là hôm nay",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                'address',
                openapi.IN_QUERY,
                description="Lọc theo địa chỉ (quận, khu vực)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Danh sách sân trống",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                    'sport_center': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'address': openapi.Schema(type=openapi.TYPE_STRING),
                            'owner': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                    'sport_field': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'sport_type': openapi.Schema(type=openapi.TYPE_STRING),
                                'rental_slot': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description='Danh sách khung giờ trống (CHỈ từ booking PENDING của sân này)',
                                    items=openapi.Schema(type=openapi.TYPE_STRING)
                                ),
                            }
                        )
                    ),
                            'booking_date': openapi.Schema(type=openapi.TYPE_STRING),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                            'price': openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    )
                )
            ),
        }
    )
    def get(self, request):
        """
        GET /api/booking/available/
        Lấy danh sách booking PENDING (sân trống) theo format nested
        """
        # Lấy booking_date từ query params, mặc định là hôm nay
        booking_date_str = request.query_params.get('booking_date')
        if booking_date_str:
            try:
                booking_date = date.fromisoformat(booking_date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            booking_date = date.today()

        # Lấy filter địa chỉ nếu có
        address_filter = request.query_params.get('address', '').strip()

        # Query booking PENDING của ngày được chọn - CHỈ lấy booking PENDING (sân trống)
        # Và CHỈ lấy sport_field có status ACTIVE
        bookings = Booking.objects.filter(
            status=StatusBookingEnum.PENDING.value,  # CHỈ lấy booking PENDING
            booking_date=booking_date,
            sport_field__status=StatusFieldEnum.ACTIVE.value  # CHỈ lấy sport_field ACTIVE
        ).select_related(
            'sport_field',
            'sport_field__sport_center',
            'sport_field__sport_center__owner',
            'rental_slot'
        ).prefetch_related(
            'sport_field__sport_center'
        )

        # Lọc theo địa chỉ nếu có
        if address_filter:
            bookings = bookings.filter(
                sport_field__sport_center__address__icontains=address_filter
            ) | bookings.filter(
                sport_field__address__icontains=address_filter
            )

        # Group by (sport_center, booking_date) -> sport_field -> rental_slot
        result_dict = {}
        
        for booking in bookings:
            # Validate
            if not booking.sport_field or not booking.sport_field.sport_center or not booking.rental_slot:
                continue
            
            sport_field = booking.sport_field
            sport_center = sport_field.sport_center
            rental_slot = booking.rental_slot
            
            # Key: (center_id, booking_date)
            key = (sport_center.id, booking.booking_date)
            
            # Khởi tạo center entry nếu chưa có
            if key not in result_dict:
                result_dict[key] = {
                    'sport_center': {
                        'id': sport_center.id,
                        'name': sport_center.name,
                        'address': sport_center.address,
                        'owner': str(sport_center.owner.id) if sport_center.owner else None,
                    },
                    'booking_date': booking.booking_date,
                    'price': booking.price,
                    'sport_fields': {}
                }
            
            # Khởi tạo field entry nếu chưa có
            field_id = sport_field.id
            if field_id not in result_dict[key]['sport_fields']:
                result_dict[key]['sport_fields'][field_id] = {
                    'id': sport_field.id,
                    'name': sport_field.name,
                    'sport_type': sport_field.sport_type,
                    'rental_slots': set()
                }
            
            # Thêm rental_slot vào set
            if rental_slot.time_slot:
                result_dict[key]['sport_fields'][field_id]['rental_slots'].add(rental_slot.time_slot)

        # Chuyển đổi sang format response
        result = []
        for key, data in result_dict.items():
            # Chuyển sport_fields từ dict sang list
            sport_fields = []
            for field_id, field_data in data['sport_fields'].items():
                rental_slots = sorted(list(field_data['rental_slots']))
                if rental_slots:  # Chỉ thêm field nếu có rental_slot
                    sport_fields.append({
                        'id': field_data['id'],
                        'name': field_data['name'],
                        'sport_type': field_data['sport_type'],
                        'rental_slot': rental_slots,
                    })
            
            # Chỉ thêm center nếu có sport_field
            if sport_fields:
                result.append({
                    'sport_center': data['sport_center'],
                    'sport_field': sport_fields,
                    'booking_date': data['booking_date'].isoformat(),
                    'status': StatusBookingEnum.PENDING.value,
                    'price': data['price'],
                })

        return Response(result, status=status.HTTP_200_OK)

