import random
import calendar
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.user.models import User
from apps.utils.enum_type import RoleSystemEnum, SportTypeEnum, StatusBookingEnum, StatusFieldEnum
from apps.sport_center.models import SportCenter, SportField
from apps.booking.models import Booking, RentalSlot
from django.utils import timezone
from datetime import date, timedelta


class FakeUserView(APIView):
    """
    Tạo fake users cho demo/report.
    GET /api/fake_data/user/?count=40
    Tạo 40 user: 20 đầu (giữ nguyên), 20 sau (tên con trai)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        count = int(request.query_params.get('count', 40))
        created_users = []

        # Danh sách tên Việt Nam mẫu (nữ - cho 20 user đầu)
        first_names_female = ['Ngô Thị', 'Lê Thị', 'Hoàng Thị', 'Đặng Thị', 'Trần Thị', 'Phạm Thị']
        last_names_female = ['Nga', 'Hương', 'Lan', 'Mai', 'Hoa', 'Anh', 'Linh', 'Hạnh']
        
        # Danh sách tên Việt Nam mẫu (nam - cho 20 user sau)
        first_names_male = ['Trần Văn', 'Phạm Văn', 'Vũ Văn', 'Bùi Văn', 'Nguyễn Văn', 'Lê Văn', 'Hoàng Văn', 'Đặng Văn']
        last_names_male = ['Nam', 'Đức', 'Hùng', 'Tuấn', 'Dũng', 'Long', 'Minh', 'Quang', 'Sơn', 'Thành', 'Bảo', 'Khang']

        for i in range(1, count + 1):
            username = f"user_{i:02d}"
            email = f"{username}@gmail.com"
            
            # Kiểm tra user đã tồn tại chưa
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                created_users.append({
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'status': 'existed'
                })
                continue

            # Tạo full_name: 20 đầu (nữ), 20 sau (nam)
            if i <= 20:
                # 20 user đầu: tên nữ
                first_name = random.choice(first_names_female)
                last_name = random.choice(last_names_female)
            else:
                # 20 user sau: tên nam
                first_name = random.choice(first_names_male)
                last_name = random.choice(last_names_male)
            
            full_name = f"{first_name} {last_name}"

            user = User.objects.create(
                username=username,
                email=email,
                full_name=full_name,
                password=make_password('12345678'),
                role=RoleSystemEnum.USER.value,
                is_active=True,
            )

            created_users.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'status': 'created'
            })

        return Response({
            'message': f'Created/Found {len(created_users)} users (20 first: female names, 20 next: male names)',
            'count': len(created_users),
            'users': created_users
        }, status=status.HTTP_200_OK)


class FakeBookingView(APIView):
    """
    Tạo fake bookings cho demo/report.
    GET /api/fake_data/booking/?count=50
    """
    permission_classes = [AllowAny]

    def get(self, request):
        count = int(request.query_params.get('count', 50))
        created_bookings = []

        # Lấy users và fields có sẵn
        users = list(User.objects.filter(role=RoleSystemEnum.USER.value, is_active=True))
        fields = list(SportField.objects.filter(status=StatusFieldEnum.ACTIVE.value))
        slots = list(RentalSlot.objects.all())

        if not users:
            return Response({'error': 'No users found. Create users first.'}, status=status.HTTP_400_BAD_REQUEST)
        if not fields:
            return Response({'error': 'No sport fields found. Create sport fields first.'}, status=status.HTTP_400_BAD_REQUEST)
        if not slots:
            return Response({'error': 'No rental slots found. Create rental slots first.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tạo bookings trong 30 ngày gần đây
        today = timezone.localdate()
        statuses = [StatusBookingEnum.CONFIRMED.value, StatusBookingEnum.COMPLETED.value, StatusBookingEnum.PENDING.value]

        for i in range(count):
            user = random.choice(users)
            field = random.choice(fields)
            slot = random.choice(slots)
            booking_date = today - timedelta(days=random.randint(0, 30))
            booking_status = random.choice(statuses)

            booking = Booking.objects.create(
                user=user,
                sport_field=field,
                rental_slot=slot,
                price=field.price,
                booking_date=booking_date,
                status=booking_status,
            )

            created_bookings.append({
                'id': booking.id,
                'user': user.username,
                'sport_field': field.name,
                'booking_date': str(booking_date),
                'status': booking_status,
                'price': field.price
            })

        return Response({
            'message': f'Created {len(created_bookings)} bookings',
            'count': len(created_bookings),
            'bookings': created_bookings[:10]  # Chỉ trả về 10 đầu tiên để response không quá dài
        }, status=status.HTTP_200_OK)


class FakeBookingGenView(APIView):
    """
    Tạo booking từ tháng 6/2025 đến hiện tại cho TẤT CẢ trung tâm và sân.
    GET /api/fake_data/booking/gen/
    Cho phép tạo booking trong quá khứ (khác với bulk-create-month).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        start_year = 2025
        start_month = 10
        # Tạo đến hết tháng 2/2026
        end_year = 2026
        end_month = 2
        _, last_day = calendar.monthrange(end_year, end_month)
        end_date = date(end_year, end_month, last_day)
        
        # Lấy tất cả sport centers
        sport_centers = SportCenter.objects.all()
        
        if not sport_centers.exists():
            return Response({
                'error': 'No sport centers found. Create sport centers first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        total_created = 0
        total_skipped = 0
        centers_summary = []

        for sport_center in sport_centers:
            # Lấy tất cả sport fields active của center này
            sport_fields = SportField.objects.filter(
                sport_center=sport_center,
                status=StatusFieldEnum.ACTIVE.value
            ).select_related('sport_center')

            if not sport_fields.exists():
                continue

            # Lấy rental slots phù hợp với sport types
            # Logic: FOOTBALL -> name="FOOTBALL", các loại khác -> name="SPORT"
            rental_slot_names = []
            for sport_type in sport_fields.values_list('sport_type', flat=True).distinct():
                if sport_type == SportTypeEnum.FOOTBALL.value:
                    rental_slot_names.append(SportTypeEnum.FOOTBALL.value)
                else:
                    rental_slot_names.append("SPORT")
            
            rental_slots = RentalSlot.objects.filter(name__in=set(rental_slot_names))

            if not rental_slots.exists():
                continue

            center_created = 0
            center_skipped = 0

            # Lặp qua từng tháng từ 6/2025 đến hết tháng 2/2026
            current_date = date(start_year, start_month, 1)
            
            while current_date <= end_date:
                year = current_date.year
                month = current_date.month
                
                # Tính số ngày trong tháng
                _, num_days = calendar.monthrange(year, month)
                
                # Lấy tất cả bookings đã tồn tại trong tháng này cho center này
                existing_bookings = Booking.objects.filter(
                    sport_field__in=sport_fields,
                    booking_date__year=year,
                    booking_date__month=month
                ).values_list('sport_field_id', 'rental_slot_id', 'booking_date')
                
                existing_set = set(existing_bookings)
                bookings_to_create = []

                # Tạo booking cho tất cả ngày trong tháng
                for day in range(1, num_days + 1):
                    booking_date = date(year, month, day)
                    
                    # Chỉ tạo đến hết tháng 2/2026
                    if booking_date > end_date:
                        break

                    for sport_field in sport_fields:
                        # Logic matching: FOOTBALL -> "FOOTBALL", khác -> "SPORT"
                        if sport_field.sport_type == SportTypeEnum.FOOTBALL.value:
                            matching_slots = rental_slots.filter(name=SportTypeEnum.FOOTBALL.value)
                        else:
                            matching_slots = rental_slots.filter(name="SPORT")

                        for rental_slot in matching_slots:
                            booking_key = (sport_field.id, rental_slot.id, booking_date)

                            if booking_key not in existing_set:
                                bookings_to_create.append(
                                    Booking(
                                        sport_field=sport_field,
                                        rental_slot=rental_slot,
                                        price=sport_field.price,
                                        booking_date=booking_date,
                                        status=StatusBookingEnum.PENDING
                                    )
                                )
                            else:
                                center_skipped += 1

                # Bulk create bookings
                if bookings_to_create:
                    created = Booking.objects.bulk_create(
                        bookings_to_create,
                        batch_size=1000,
                        ignore_conflicts=True
                    )
                    center_created += len(created)

                # Chuyển sang tháng tiếp theo
                if month == 12:
                    current_date = date(year + 1, 1, 1)
                else:
                    current_date = date(year, month + 1, 1)

            total_created += center_created
            total_skipped += center_skipped

            centers_summary.append({
                'center_id': sport_center.id,
                'center_name': sport_center.name,
                'created': center_created,
                'skipped': center_skipped
            })

        return Response({
            'message': f'Generated bookings from {start_month}/{start_year} to {end_date}',
            'summary': {
                'total_created': total_created,
                'total_skipped': total_skipped,
                'date_range': {
                    'from': f'{start_month}/{start_year}',
                    'to': end_date.isoformat()
                }
            },
            'centers': centers_summary
        }, status=status.HTTP_200_OK)


class FakeBookingAssignUsersView(APIView):
    """
    Assign 40 users vào bookings:
    - 80% bookings từ 6/2025 đến hôm nay → assign cho 40 users
    - 40% bookings từ hôm nay đến 10/1/2026 → assign random cho 40 users
    - Update status thành CONFIRMED
    GET /api/fake_data/booking/assign_users/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.localdate()
        start_date = date(2025, 6, 1)
        end_date = date(2026, 1, 10)
        
        # Lấy 40 users (user_01 đến user_40)
        users = list(User.objects.filter(
            username__startswith='user_',
            role=RoleSystemEnum.USER.value,
            is_active=True
        ).order_by('username')[:40])
        
        if len(users) < 40:
            return Response({
                'error': f'Need 40 users, found only {len(users)}. Create users first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Phase 1: Bookings từ 6/2025 đến hôm nay (80%)
        bookings_past = Booking.objects.filter(
            booking_date__gte=start_date,
            booking_date__lt=today,
            status=StatusBookingEnum.PENDING.value,
            user__isnull=True
        )
        
        total_past = bookings_past.count()
        assign_count_past = int(total_past * 0.8)
        
        if assign_count_past > 0:
            bookings_to_assign_past = random.sample(list(bookings_past), min(assign_count_past, total_past))
            
            # Assign users và update status
            for booking in bookings_to_assign_past:
                booking.user = random.choice(users)
                booking.status = StatusBookingEnum.CONFIRMED.value
            
            # Bulk update
            Booking.objects.bulk_update(bookings_to_assign_past, ['user', 'status'], batch_size=1000)
            updated_past = len(bookings_to_assign_past)
        else:
            updated_past = 0

        # Phase 2: Bookings từ hôm nay đến 10/1/2026 (40%)
        bookings_future = Booking.objects.filter(
            booking_date__gte=today,
            booking_date__lte=end_date,
            status=StatusBookingEnum.PENDING.value,
            user__isnull=True
        )
        
        total_future = bookings_future.count()
        assign_count_future = int(total_future * 0.4)
        
        if assign_count_future > 0:
            bookings_to_assign_future = random.sample(list(bookings_future), min(assign_count_future, total_future))
            
            # Assign users và update status
            for booking in bookings_to_assign_future:
                booking.user = random.choice(users)
                booking.status = StatusBookingEnum.CONFIRMED.value
            
            # Bulk update
            Booking.objects.bulk_update(bookings_to_assign_future, ['user', 'status'], batch_size=1000)
            updated_future = len(bookings_to_assign_future)
        else:
            updated_future = 0

        return Response({
            'message': 'Assigned users to bookings successfully',
            'summary': {
                'users_count': len(users),
                'past_period': {
                    'date_range': {
                        'from': start_date.isoformat(),
                        'to': (today - timedelta(days=1)).isoformat()
                    },
                    'total_bookings': total_past,
                    'assigned': updated_past,
                    'percent': 80
                },
                'future_period': {
                    'date_range': {
                        'from': today.isoformat(),
                        'to': end_date.isoformat()
                    },
                    'total_bookings': total_future,
                    'assigned': updated_future,
                    'percent': 40
                },
                'total_assigned': updated_past + updated_future
            }
        }, status=status.HTTP_200_OK)


class FakeBookingSuccessView(APIView):
    """
    Cập nhật một số booking thành status COMPLETED/CONFIRMED (successful bookings).
    GET /api/fake_data/booking/success/?percent=30
    """
    permission_classes = [AllowAny]

    def get(self, request):
        percent = int(request.query_params.get('percent', 30))  # Mặc định 30%
        percent = max(0, min(100, percent))  # Giới hạn 0-100

        # Lấy bookings PENDING hoặc CONFIRMED
        bookings = Booking.objects.filter(
            status__in=[StatusBookingEnum.PENDING.value, StatusBookingEnum.CONFIRMED.value]
        )

        if not bookings.exists():
            return Response({
                'error': 'No bookings found to update.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Tính số lượng cần update
        total_count = bookings.count()
        update_count = int(total_count * percent / 100)

        # Random chọn bookings để update
        bookings_to_update = random.sample(list(bookings), min(update_count, total_count))

        completed_count = 0
        confirmed_count = 0

        for booking in bookings_to_update:
            # 50% COMPLETED, 50% CONFIRMED
            if random.choice([True, False]):
                booking.status = StatusBookingEnum.COMPLETED.value
                completed_count += 1
            else:
                booking.status = StatusBookingEnum.CONFIRMED.value
                confirmed_count += 1
            booking.save()

        return Response({
            'message': f'Updated {len(bookings_to_update)} bookings to success status',
            'summary': {
                'total_updated': len(bookings_to_update),
                'completed': completed_count,
                'confirmed': confirmed_count,
                'percent_applied': percent
            }
        }, status=status.HTTP_200_OK)
