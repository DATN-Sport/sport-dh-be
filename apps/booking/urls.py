from django.urls import path, include
from rest_framework import routers

from apps.booking.views import (
    RentalSlotViewSet,
)

rental_slot_center = routers.DefaultRouter(trailing_slash=False)
rental_slot_center.register('', RentalSlotViewSet)

urlpatterns = [
    path('rental_slot/', include(rental_slot_center.urls)),

]


