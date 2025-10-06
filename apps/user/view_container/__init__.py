import os

from datetime import timedelta
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password, check_password

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import (viewsets, mixins, status, permissions, generics)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.generics import GenericAPIView, RetrieveAPIView, ListAPIView, CreateAPIView, UpdateAPIView

from apps.user.models import *
from apps.utils.constant_status import Enum
from apps.utils.constant_status import AppStatus
from apps.depends.oauth2 import IsAdmin, IsOwner, IsUser
from apps.utils.dynamic_param import DynamicQueryParams
from apps.user.view_container.filter_user import UserFilter
from apps.utils.send_mail import sent_mail_verification, TypeEmailEnum
