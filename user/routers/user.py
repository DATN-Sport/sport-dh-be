from user.routers import *

from user.views import (
    UserDetailViewSet,
)

urlpatterns = [
    path('user/me/', UserDetailViewSet.as_view(), name='user-detail'),
]
