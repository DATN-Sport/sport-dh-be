"""
URL configuration for sport_dh project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from drf_yasg import openapi

from drf_yasg.views import get_schema_view
from rest_framework import permissions

from sport_dh import settings

schema_view = get_schema_view(
    openapi.Info(
        title="Sport DH Django API",
        default_version='v1',
        description="API documentation for Sport DH Django",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@magiceyes.local"),
        license=openapi.License(name="BSD License"),
    ),

    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('sport_dh.urls_api')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

# Serve media files (user-uploaded) in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
