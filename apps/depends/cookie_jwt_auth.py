"""
Cookie-based JWT Authentication for Django REST Framework
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import HTTP_HEADER_ENCODING
from django.utils.module_loading import import_string


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication class that reads tokens from HTTP-only cookies
    """
    
    def get_token_from_cookie(self, request):
        """
        Get JWT token from HTTP-only cookie
        """
        cookie_name = settings.JWT_ACCESS_TOKEN_COOKIE
        return request.COOKIES.get(cookie_name)
    
    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if authentication should succeed.
        Otherwise returns None.
        """
        # Try to get token from cookie first
        token = self.get_token_from_cookie(request)
        
        if token is None:
            return None
        
        return self.get_user(token), token
    
    def get_user(self, raw_token):
        """
        Attempt to authenticate with the provided token.
        """
        validated_token = self.get_validated_token(raw_token)
        return self.get_user_from_token(validated_token)
    
    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthTokenPath in settings.SIMPLE_JWT['AUTH_TOKEN_CLASSES']:
            AuthToken = import_string(AuthTokenPath)  # convert từ string sang class thật
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append({
                    'token_class': AuthToken.__name__,
                    'token_type': AuthToken.token_type,
                    'message': e.args[0]
                })

        raise InvalidToken({
            'detail': 'Given token not valid for any token type',
            'messages': messages,
        })
    
    def get_user_from_token(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[settings.SIMPLE_JWT['USER_ID_CLAIM']]
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = self.user_model.objects.get(**{settings.SIMPLE_JWT['USER_ID_FIELD']: user_id})
        except self.user_model.DoesNotExist:
            raise InvalidToken('User not found')

        if not user.is_active:
            raise InvalidToken('User is inactive')

        return user


class CookieRefreshJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication class for refresh tokens from HTTP-only cookies
    """
    
    def get_refresh_token_from_cookie(self, request):
        """
        Get JWT refresh token from HTTP-only cookie
        """
        cookie_name = settings.JWT_REFRESH_TOKEN_COOKIE
        return request.COOKIES.get(cookie_name)
    
    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and refresh token if authentication should succeed.
        Otherwise returns None.
        """
        # Try to get refresh token from cookie
        token = self.get_refresh_token_from_cookie(request)
        
        if token is None:
            return None
        
        return self.get_user(token), token
    
    def get_user(self, raw_token):
        """
        Attempt to authenticate with the provided refresh token.
        """
        from rest_framework_simplejwt.tokens import RefreshToken
        
        try:
            refresh_token = RefreshToken(raw_token)
            access_token = refresh_token.access_token
            return self.get_user_from_token(access_token)
        except TokenError as e:
            raise InvalidToken({'detail': e.args[0]})
    
    def get_user_from_token(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[settings.SIMPLE_JWT['USER_ID_CLAIM']]
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = self.user_model.objects.get(**{settings.SIMPLE_JWT['USER_ID_FIELD']: user_id})
        except self.user_model.DoesNotExist:
            raise InvalidToken('User not found')

        if not user.is_active:
            raise InvalidToken('User is inactive')

        return user

