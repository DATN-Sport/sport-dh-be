from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.user.models import User
from apps.utils.enum_type import StatusFieldEnum, SportTypeEnum


class SportCenter(models.Model):
    owner = models.ForeignKey(User, null=False, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=True)
    address = models.CharField(max_length=255, null=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.owner.full_name if self.owner else "None",
            "name": self.name,
            "address": self.address,
        }

class SportField(models.Model):
    sport_center = models.ForeignKey(SportCenter, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=True)
    address = models.CharField(max_length=255, null=False, blank=True)
    sport_type = models.CharField(max_length=255, choices=SportTypeEnum.choices(), default=SportTypeEnum.FOOTBALL)
    price = models.FloatField(null=False, blank=True)
    status = models.CharField(max_length=255, choices=StatusFieldEnum.choices(), default=StatusFieldEnum.INACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sport_center": self.sport_center.name,
            "name": self.name,
            "sport_type": self.sport_type,
            "price": self.price,
            "status": self.status,
        }


class ImageSport(models.Model):
    file = models.ImageField(upload_to='images/')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

