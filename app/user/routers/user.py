from app.user.routers import *

from app.user.views import (
    UserDetailViewSet,
)

urlpatterns = [
    path('user/me/', UserDetailViewSet.as_view(), name='user-detail'),
]
