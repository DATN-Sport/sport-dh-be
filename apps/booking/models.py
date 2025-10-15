from django.db import models

from apps.sport_center.models import SportField
from apps.user.models import User
from apps.utils.enum_type import StatusBookingEnum


class RentalSlot(models.Model):
    name = models.CharField(max_length=255, null=False, blank=True)
    time_slot = models.CharField(max_length=100, null=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "time_slot": self.time_slot,
        }


class Booking(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    sport_field = models.ForeignKey(SportField, null=False, blank=True, on_delete=models.CASCADE)
    rental_slot = models.ForeignKey(RentalSlot, null=False, blank=True, on_delete=models.CASCADE)

    price = models.FloatField(null=False, blank=False)
    booking_date = models.DateField(null=False, blank=True)
    status = models.CharField(max_length=255, choices=StatusBookingEnum.choices(), default=StatusBookingEnum.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.full_name if self.user else "None",
            "sport_field": self.sport_field.name,
            "address": self.sport_field.address,
            "price": self.price,
            "booking_date": self.booking_date,
            "rental_slot": self.rental_slot.time_slot,
            "status": self.status,
        }
