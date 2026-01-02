from django.urls import path
from apps.fake_data.views import (
    FakeUserView, 
    FakeBookingView, 
    FakeBookingGenView, 
    FakeBookingSuccessView,
    FakeBookingAssignUsersView
)

urlpatterns = [
    path('user/', FakeUserView.as_view(), name='fake_user'),
    path('booking/', FakeBookingView.as_view(), name='fake_booking'),
    path('booking/gen/', FakeBookingGenView.as_view(), name='fake_booking_gen'),
    path('booking/assign_users/', FakeBookingAssignUsersView.as_view(), name='fake_booking_assign_users'),
    path('booking/success/', FakeBookingSuccessView.as_view(), name='fake_booking_success'),
]
