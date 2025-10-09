from django.urls import path, include
from rest_framework import routers

from apps.sport_center.views import (
    SportCenterViewSet,
    SportFieldViewSet
)

router_sport_center = routers.DefaultRouter(trailing_slash=False)
router_sport_field = routers.DefaultRouter(trailing_slash=False)
router_sport_center.register('', SportCenterViewSet)
router_sport_field.register('', SportFieldViewSet)

urlpatterns = [
    path('sport_center/', include(router_sport_center.urls)),
    path('sport_field/', include(router_sport_field.urls)),

]


