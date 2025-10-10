from rest_framework_simplejwt.views import TokenVerifyView
from apps.user.view_container.cookie_auth import CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView
from django.urls import path, include


urlpatterns = [
    path('auth/login/', CookieTokenObtainPairView.as_view(), name='login_api'),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout_api"),
    path('', include('apps.user.urls')),
    path('', include('apps.sport_center.urls')),
]