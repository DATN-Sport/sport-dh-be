from django.urls import path, include
from rest_framework import routers

from apps.user.views import (
    RegisterViewSet,
    VerifyCodeViewSet,
    UserDetailViewSet,
    UserViewSet
)

router_user = routers.DefaultRouter(trailing_slash=False)
router_user.register('', UserViewSet)

urlpatterns = [
    path('auth/register/', RegisterViewSet.as_view(), name='register-user'),
    path('auth/veryfi_code/', VerifyCodeViewSet.as_view(), name='verify-code'),
    path('user/me/', UserDetailViewSet.as_view(), name='user-detail'),
    path('user/', include(router_user.urls)),
]


