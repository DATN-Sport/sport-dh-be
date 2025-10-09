from apps.sport_center.models import SportCenter, SportField
from apps.user.view_container import (
    filters,
)


class SportCenterFilter(filters.FilterSet):
    owner = filters.CharFilter(field_name='owner', lookup_expr='icontains')
    name = filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    address = filters.CharFilter(field_name='email', lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SportCenter
        fields = ['owner', 'name', 'address']


class SportFieldFilter(filters.FilterSet):
    sport_center = filters.CharFilter(field_name='sport_center', lookup_expr='icontains')
    address = filters.CharFilter(field_name='address', lookup_expr='icontains')
    sport_type = filters.CharFilter(field_name='sport_type', lookup_expr='icontains')
    price = filters.CharFilter(field_name='price', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status', lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SportField
        fields = ['sport_center', 'address', 'sport_type', 'price', 'status']
