from apps.booking.models import RentalSlot, Booking
from apps.user.view_container import filters


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
    sport_field = filters.NumberFilter(field_name='sport_field')
    rental_slot = filters.NumberFilter(field_name='rental_slot')
    price = filters.NumberFilter(field_name='price')
    booking_date = filters.DateFromToRangeFilter(field_name='booking_date')
    month = filters.NumberFilter(method='filter_by_month')
    year = filters.NumberFilter(method='filter_by_year')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    def filter_by_month(self, queryset, name, value):
        return queryset.filter(booking_date__month=value)

    def filter_by_year(self, queryset, name, value):
        return queryset.filter(booking_date__year=value)

    class Meta:
        model = Booking
        fields = ['sport_field', 'rental_slot', 'price', 'booking_date', 'status', 'month', 'year']
