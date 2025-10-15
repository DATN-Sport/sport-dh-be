import os
import uuid

from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin

from apps.utils.enum_type import RoleSystemEnum


# Custom UserManager class
class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=RoleSystemEnum.ADMIN.value, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not email:
            raise ValueError("Superuser must have an email.")
        if not username:
            raise ValueError("Superuser must have a username.")

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')

        return self._create_user(username, email, password, **extra_fields)

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_active', False)
        extra_fields.setdefault('is_superuser', False)

        if not email:
            raise ValueError("User must have an email.")

        return self._create_user(username, email, password, **extra_fields)


def user_avatar_path(instance, filename):
    return os.path.join('user', 'avatar', str(instance.id), filename)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=False, blank=False, unique=True)
    password = models.CharField(max_length=128, blank=True)
    username = models.CharField(max_length=128, null=False, blank=False, unique=True)
    full_name = models.CharField(max_length=128, null=True, blank=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=False)
    role = models.CharField(max_length=128, choices=RoleSystemEnum.choices(), default=RoleSystemEnum.USER.value)
    settings = models.JSONField(default=dict, null=True, blank=True)  # Sửa default thành `dict`
    is_active = models.BooleanField(default=False, blank=True)
    address = models.CharField(max_length=256, null=True, blank=False)
    phone = models.CharField(max_length=30, null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'email']  # Bổ sung `email` để `createsuperuser` yêu cầu email

    verify_code = models.CharField(max_length=10, blank=True)
    device_tokens = models.JSONField(default=dict, null=True, blank=True)  # Sửa default thành `dict`
    is_delete = models.BooleanField(default=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_superuser": self.is_superuser,
            "settings": self.settings,
            "is_active": self.is_active,
            "role": self.role,
        }

    def info(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "avatar": self.avatar,
            "role": self.role,
        }
