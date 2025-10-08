from django.urls import path, include
from rest_framework import routers

from apps.sport_center.views import (
    SportCenterViewSet,
)

router_sport_center = routers.DefaultRouter(trailing_slash=False)
router_sport_center.register('', SportCenterViewSet)

urlpatterns = [
    path('sport_center/', include(router_sport_center.urls)),

]


