import os
from typing import Dict, Any
from datetime import timedelta, date, datetime

from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from rest_framework.fields import (  # NOQA # isort:skip
    BooleanField, CharField, ChoiceField, DateField, DateTimeField, DecimalField,
    DictField, DurationField, EmailField, Field, FileField, FilePathField, FloatField,
    HiddenField, HStoreField, IPAddressField, ImageField, IntegerField, JSONField,
    ListField, ModelField, MultipleChoiceField, ReadOnlyField,
    RegexField, SerializerMethodField, SlugField, TimeField, URLField, UUIDField,
)

from apps.utils.constant_status import AppStatus
from apps.utils.enum_type import RoleSystemEnum
from apps.utils.validate_data import validate_create_user

