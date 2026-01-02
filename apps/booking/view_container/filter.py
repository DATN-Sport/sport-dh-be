from datetime import date

from apps.booking.models import RentalSlot, Booking
from apps.user.view_container import filters
from apps.utils.enum_type import RoleSystemEnum


class RentalSlotFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    time_slot = filters.CharFilter(field_name='time_slot', lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = RentalSlot
        fields = ['name', 'time_slot']


class BookingFilter(filters.FilterSet):
    user = filters.UUIDFilter(field_name='user')
    sport_field = filters.NumberFilter(field_name='sport_field')
    rental_slot = filters.NumberFilter(field_name='rental_slot')
    price = filters.NumberFilter(field_name='price')
    booking_date = filters.DateFromToRangeFilter(field_name='booking_date')
    booking_date_ = filters.DateFilter(field_name='booking_date')
    month = filters.NumberFilter(method='filter_by_month')
    year = filters.NumberFilter(method='filter_by_year')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

        data = self.data or {}
        has_any_filter = any(data.values())

        if not has_any_filter:
            # Gán giá trị mặc định cho booking_date_
            self.data = self.data.copy()
            self.data['booking_date_'] = date.today()

    def filter_by_month(self, queryset, name, value):
        return queryset.filter(booking_date__month=value)

    def filter_by_year(self, queryset, name, value):
        return queryset.filter(booking_date__year=value)

    class Meta:
        model = Booking
        fields = ['user', 'sport_field', 'rental_slot', 'price', 'booking_date', 'status', 'month', 'year']


class BookingManageFilter(filters.FilterSet):
    user = filters.CharFilter(
        field_name='user__email',
        lookup_expr='iexact'
    )
    owner = filters.UUIDFilter(field_name="sport_field__sport_center__owner")
    sport_center = filters.NumberFilter(field_name="sport_field__sport_center")
    sport_field = filters.NumberFilter(field_name='sport_field')
    rental_slot = filters.NumberFilter(field_name='rental_slot')
    price = filters.NumberFilter(field_name='price')
    booking_date = filters.DateFromToRangeFilter(field_name='booking_date')
    booking_date_ = filters.DateFilter(field_name='booking_date')
    month = filters.NumberFilter(method='filter_by_month')
    year = filters.NumberFilter(method='filter_by_year')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')

    def __init__(self, request, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

        data = self.data or {}
        has_any_filter = any(data.values())

        if not has_any_filter:
            # Gán giá trị mặc định cho booking_date_
            self.data = self.data.copy()
            self.data['booking_date_'] = date.today()

        user = getattr(request, "user", None)
        if user.role == RoleSystemEnum.OWNER.value:
            mutable_data = self.data.copy()
            mutable_data["owner"] = str(user.id)
            self.data = mutable_data

    def filter_by_month(self, queryset, name, value):
        return queryset.filter(booking_date__month=value)

    def filter_by_year(self, queryset, name, value):
        return queryset.filter(booking_date__year=value)

    class Meta:
        model = Booking
        fields = ['user', 'sport_field', 'rental_slot', 'price', 'booking_date', 'status', 'month', 'year']
