from apps.user.routers import *

from apps.user.views import (
    UserDetailViewSet,
)

urlpatterns = [
    path('user/me/', UserDetailViewSet.as_view(), name='user-detail'),
]
