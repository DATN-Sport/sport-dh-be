from apps.user.models import User
from apps.user.view_container import (
    filters,
)


class UserFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    full_name = filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    role = filters.CharFilter(field_name='role', lookup_expr='icontains')
    is_active = filters.BooleanFilter(field_name='is_active', lookup_expr='contains')
    is_delete = filters.BooleanFilter(field_name='is_delete', lookup_expr='contains')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['name', 'full_name', 'role', 'is_active', 'is_delete']



