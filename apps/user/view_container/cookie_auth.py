"""
Custom views for cookie-based JWT authentication
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from sport_dh.utils.cookie_utils import set_jwt_cookies, clear_jwt_cookies


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that sets JWT tokens as HTTP-only cookies
    """
    def post(self, request, *args, **kwargs):
        # Call parent's post method to get serializer and validate
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise e
        
        # Get the validated data
        validated_data = serializer.validated_data
        
        # Create response with user data
        response = Response({
            'user': validated_data.get('user'),
            'message': validated_data.get('message')
        }, status=status.HTTP_200_OK)
        
        # Set tokens as cookies
        if hasattr(serializer, 'access_token') and hasattr(serializer, 'refresh_token'):
            set_jwt_cookies(response, serializer.access_token, serializer.refresh_token)
        
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom refresh view that sets new JWT access token as HTTP-only cookie
    """
    def post(self, request, *args, **kwargs):
        # Extract refresh token from cookies or request body
        refresh_token = None
        
        # Try to get refresh token from cookies first
        if 'refresh_token' in request.COOKIES:
            refresh_token = request.COOKIES['refresh_token']
        # Fallback to request body
        elif 'refresh' in request.data:
            refresh_token = request.data['refresh']
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token not provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set the refresh token in request data for serializer
        request.data['refresh'] = refresh_token
        
        # Call parent's post method
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the validated data
        validated_data = serializer.validated_data
        
        # Create response
        response = Response({
            'message': validated_data.get('message')
        }, status=status.HTTP_200_OK)
        
        # Set new access token as cookie
        if hasattr(serializer, 'access_token'):
            set_jwt_cookies(response, serializer.access_token)
        
        return response


class LogoutView(TokenRefreshView):
    """
    Custom logout view that clears JWT cookies
    """
    def post(self, request, *args, **kwargs):
        response = Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
        # Clear all JWT cookies
        clear_jwt_cookies(response)
        
        return response

