import calendar

from apps.booking.models import Booking, RentalSlot
from apps.sport_center.models import SportCenter, SportField
from apps.user.serializer_container import (
    serializers, RoleSystemEnum, AppStatus, Response, status, timezone, StatusBookingEnum, date, StatusFieldEnum
)


class BookingDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    sport_field = serializers.SerializerMethodField()
    rental_slot = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'user', 'sport_field', 'rental_slot', 'status', 'price', 'booking_date']

    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'full_name': obj.user.full_name,
                'email': obj.user.email,
                'phone': obj.user.phone
            }
        return {}

    def get_sport_field(self, obj):
        if obj.sport_field:
            return {
                'id': obj.sport_field.id,
                'name': obj.sport_field.name,
                'sport_type': obj.sport_field.sport_type,
                'address': obj.sport_field.address
            }
        return {}

    def get_rental_slot(self, obj):
        if obj.rental_slot:
            return {
                'id': obj.rental_slot.id,
                'name': obj.rental_slot.name,
                'time_slot': obj.rental_slot.time_slot,
            }
        return {}


class BookingListTiniSerializer(serializers.ModelSerializer):
    rental_slot = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'sport_field', 'rental_slot', 'status', 'booking_date']

    def get_rental_slot(self, obj):
        if obj.rental_slot:
            return obj.rental_slot.time_slot
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['user', 'sport_field', 'rental_slot', 'booking_date', 'status']
        extra_kwargs = {
            'sport_field': {'required': True},
            'rental_slot': {'required': True},
        }

    def validate(self, validated_data):
        user = self.context['request'].user
        if user.role != RoleSystemEnum.ADMIN.value:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        return validated_data

    def create(self, validated_data):
        price = validated_data.get("sport_field").price
        validated_data["price"] = price
        booking_date = validated_data.get("booking_date")
        if not booking_date:
            validated_data["booking_date"] = timezone.now().date()
        instance = super().create(validated_data)
        return instance


class BookingBulkCreateSerializer(serializers.ModelSerializer):
    sport_center = serializers.PrimaryKeyRelatedField(queryset=SportCenter.objects.all())

    class Meta:
        model = Booking
        fields = ['sport_center', 'booking_date']
        extra_kwargs = {
            'sport_center': {'required': True},
            'booking_date': {'required': True},}

    def create(self, validated_data):
        sport_center = validated_data['sport_center']
        booking_date = validated_data['booking_date']
        sport_fields = SportField.objects.filter(sport_center=sport_center, status=StatusFieldEnum.ACTIVE.value).all()

        if not sport_fields.exists():
            raise serializers.ValidationError(AppStatus.NO_ACTIVE_SPORT_FIELDS_FOUND.message)

        sport_types = sport_fields.values_list('sport_type', flat=True).distinct()
        rental_slots = RentalSlot.objects.filter(name__in=sport_types)

        existing_bookings = Booking.objects.filter(
            sport_field__in=sport_fields,
            booking_date=booking_date
        ).values_list('sport_field_id', 'rental_slot_id')

        existing_set = set(existing_bookings)
        bookings_to_create = []
        skipped_count = 0

        for sport_field in sport_fields:
            matching_slots = rental_slots.filter(name=sport_field.sport_type)

            for rental_slot in matching_slots:
                if (sport_field.id, rental_slot.id) not in existing_set:
                    bookings_to_create.append(
                        Booking(
                            sport_field=sport_field,
                            rental_slot=rental_slot,
                            price=sport_field.price,
                            booking_date=booking_date,
                        )
                    )
                else:
                    skipped_count += 1

        created_bookings = []
        if bookings_to_create:
            created_bookings = Booking.objects.bulk_create(
                bookings_to_create,
                ignore_conflicts=True  # Bỏ qua nếu có conflict (optional)
            )

        return {
            'created_count': len(created_bookings),
            'skipped_count': skipped_count,
            'total_slots': len(created_bookings) + skipped_count,
            'booking_date': booking_date,
            'sport_center': {'id': sport_center.id, "name": sport_center.name}
        }


class BookingBulkCreateMonthSerializer(serializers.ModelSerializer):
    sport_center = serializers.PrimaryKeyRelatedField(queryset=SportCenter.objects.all(), required=True)
    month = serializers.IntegerField(
        required=True, min_value=1, max_value=12,
        error_messages={
            'required': 'Month is required.',
            'min_value': 'Month must be between 1 and 12.',
            'max_value': 'Month must be between 1 and 12.',
        }
    )
    year = serializers.IntegerField(
        required=True, min_value=2025, max_value=2100,
        error_messages={
            'required': 'Year is required.',
            'min_value': 'Year must be at least 2024.',
        }
    )

    class Meta:
        model = Booking
        fields = ['sport_center', 'month', 'year']

    def validate(self, attrs):
        month = attrs['month']
        year = attrs['year']

        try:
            first_day = date(year, month, 1)
        except ValueError:
            raise serializers.ValidationError({
                'month': 'Invalid month/year combination.'
            })

        today = timezone.now().date()
        if first_day < date(today.year, today.month, 1):
            raise serializers.ValidationError({
                'month': 'Cannot create bookings for past months.'
            })

        return attrs

    def create(self, validated_data):
        sport_center = validated_data['sport_center']
        month = validated_data['month']
        year = validated_data['year']

        # 1. Tính số ngày trong tháng
        _, num_days = calendar.monthrange(year, month)
        today = timezone.now().date()

        dates_in_month = []
        for day in range(1, num_days + 1):
            booking_date = date(year, month, day)
            # Chỉ tạo booking cho ngày hôm nay trở đi
            if booking_date >= today:
                dates_in_month.append(booking_date)

        if not dates_in_month:
            raise serializers.ValidationError(AppStatus.NO_VALID_DATES_IN_THIS_MONTH.message)

        sport_fields = SportField.objects.filter(
            sport_center=sport_center,
            status=StatusFieldEnum.ACTIVE.value
        ).select_related('sport_center')

        if not sport_fields.exists():
            raise serializers.ValidationError(AppStatus.NO_ACTIVE_SPORT_FIELDS_FOUND.message)

        sport_types = sport_fields.values_list('sport_type', flat=True).distinct()
        rental_slots = RentalSlot.objects.filter(name__in=sport_types)

        if not rental_slots.exists():
            raise serializers.ValidationError(AppStatus.NO_RENTAL_SLOTS_FOUND.message)

        existing_bookings = Booking.objects.filter(
            sport_field__in=sport_fields,
            booking_date__year=year,
            booking_date__month=month
        ).values_list('sport_field_id', 'rental_slot_id', 'booking_date')

        existing_set = set(existing_bookings)
        bookings_to_create = []
        skipped_count = 0

        for booking_date in dates_in_month:
            for sport_field in sport_fields:
                matching_slots = rental_slots.filter(name=sport_field.sport_type)

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
                        skipped_count += 1

        created_bookings = []
        if bookings_to_create:
            created_bookings = Booking.objects.bulk_create(
                bookings_to_create,
                batch_size=1000,  # Tạo từng batch 1000 records
                ignore_conflicts=True
            )

        return {
            'created_count': len(created_bookings),
            'skipped_count': skipped_count,
            'total_slots': len(created_bookings) + skipped_count,
            'month': month,
            'year': year,
            'num_days': len(dates_in_month),
            'sport_center': {'id': sport_center.id, "name": sport_center.name}
        }


class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['user', 'status']
        extra_kwargs = {
            'status': {'required': True},
        }

    def update(self, instance, validated_data):
        user = validated_data.get("user")
        status_update = validated_data.get("status")
        user_current = self.context["request"].user
        if user and user_current.role == RoleSystemEnum.ADMIN.value:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            return Response(status=status.HTTP_200_OK, data={})
        elif user:
            raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        else:
            if instance.status == StatusBookingEnum.PENDING.value and status_update == StatusBookingEnum.CONFIRMED.value:
                instance.status = status_update
                instance.user = user_current
            elif instance.status == StatusBookingEnum.CONFIRMED.value and status_update == StatusBookingEnum.PENDING.value:
                instance.status = status_update
                instance.user = None
            else:
                raise serializers.ValidationError(AppStatus.PERMISSION_DENIED.message)
        instance.save()
        return instance


