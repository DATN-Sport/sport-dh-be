"""
Cookie utilities for JWT authentication
"""
from django.conf import settings
from django.http import HttpResponse


def set_jwt_cookies(response: HttpResponse, access_token: str, refresh_token: str = None) -> None:
    """
    Set JWT tokens as HTTP-only cookies
    """
    # Set access token cookie
    response.set_cookie(
        settings.JWT_ACCESS_TOKEN_COOKIE,
        access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.JWT_COOKIE_SECURE,
        httponly=settings.JWT_COOKIE_HTTPONLY,
        samesite=settings.JWT_COOKIE_SAMESITE,
        domain=settings.JWT_COOKIE_DOMAIN,
        path=settings.JWT_COOKIE_PATH,
    )
    
    # Set refresh token cookie if provided
    if refresh_token:
        response.set_cookie(
            settings.JWT_REFRESH_TOKEN_COOKIE,
            refresh_token,
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            secure=settings.JWT_COOKIE_SECURE,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            samesite=settings.JWT_COOKIE_SAMESITE,
            domain=settings.JWT_COOKIE_DOMAIN,
            path=settings.JWT_COOKIE_PATH,
        )


def clear_jwt_cookies(response: HttpResponse) -> None:
    """
    Clear JWT token cookies by setting them to empty values with past expiration
    """
    response.set_cookie(
        settings.JWT_ACCESS_TOKEN_COOKIE,
        '',
        expires=0,
        secure=settings.JWT_COOKIE_SECURE,
        httponly=settings.JWT_COOKIE_HTTPONLY,
        samesite=settings.JWT_COOKIE_SAMESITE,
        domain=settings.JWT_COOKIE_DOMAIN,
        path=settings.JWT_COOKIE_PATH,
    )
    response.set_cookie(
        settings.JWT_REFRESH_TOKEN_COOKIE,
        '',
        expires=0,
        secure=settings.JWT_COOKIE_SECURE,
        httponly=settings.JWT_COOKIE_HTTPONLY,
        samesite=settings.JWT_COOKIE_SAMESITE,
        domain=settings.JWT_COOKIE_DOMAIN,
        path=settings.JWT_COOKIE_PATH,
    )

