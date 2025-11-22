from apps.sport_center.models import SportCenter, SportField
from apps.user.view_container import (
    filters,
)


class SportCenterFilter(filters.FilterSet):
    owner = filters.UUIDFilter(field_name='owner')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    address = filters.CharFilter(field_name='address', lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SportCenter
        fields = ['owner', 'name', 'address']


class SportFieldFilter(filters.FilterSet):
    sport_center = filters.NumberFilter(field_name='sport_center')
    address = filters.CharFilter(field_name='address', lookup_expr='icontains')
    sport_type = filters.CharFilter(field_name='sport_type')
    price = filters.NumberFilter(field_name='price')
    price_lte = filters.NumberFilter(field_name='price', lookup_expr='lte')
    status = filters.CharFilter(field_name='status')

    center_name = filters.CharFilter(field_name='sport_center__name', lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SportField
        fields = ['sport_center', 'sport_type', 'price', 'price_lte', 'status']
