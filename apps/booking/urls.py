from django.urls import path, include
from rest_framework import routers

from apps.booking.views import (
    RentalSlotViewSet,
    BookingViewSet,
    BookingListTiniViewSet,
    BookingManageViewSet
)


rental_slot_router = routers.DefaultRouter(trailing_slash=False)
booking_router = routers.DefaultRouter(trailing_slash=False)
booking_manage_router = routers.DefaultRouter(trailing_slash=False)

rental_slot_router.register('', RentalSlotViewSet)
booking_router.register('', BookingViewSet)
booking_manage_router.register('', BookingManageViewSet)

urlpatterns = [
    path('rental_slot/', include(rental_slot_router.urls)),
    path('booking/', include(booking_router.urls)),
    path('booking_manage/', include(booking_manage_router.urls)),
    path('booking/list/', BookingListTiniViewSet.as_view({'get': 'list'}), name='booking_list'),


]


