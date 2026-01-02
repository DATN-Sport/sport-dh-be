"""
View để lấy lịch sử chat và danh sách sessions
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404

from apps.depends.oauth2 import IsUser
from apps.chat.models import ChatSession, ChatMessage


class ChatHistoryViewSet(APIView):
    """
    API lấy lịch sử chat của một session
    Endpoint: /api/chat/history/
    """
    permission_classes = [IsUser]

    @swagger_auto_schema(
        operation_summary="Lấy lịch sử chat của một session",
        operation_description=(
            "Lấy danh sách tất cả messages trong một session chat.\n\n"
            "Yêu cầu: session_id (UUID)"
        ),
        manual_parameters=[
            openapi.Parameter(
                'session_id',
                openapi.IN_QUERY,
                description="ID phiên chat (UUID)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Danh sách messages",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'messages': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'role': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                    }
                )
            ),
            404: "Không tìm thấy session"
        }
    )
    def get(self, request):
        """
        GET /api/chat/history/?session_id=<uuid>
        Lấy lịch sử chat của một session
        """
        user = request.user if request.user.is_authenticated else None
        session_id = request.query_params.get("session_id")
        
        if not session_id:
            return Response(
                {"error": "Thiếu tham số 'session_id'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy session"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Kiểm tra quyền: user chỉ có thể xem session của chính mình
        if user and session.user and session.user != user:
            return Response(
                {"error": "Không có quyền truy cập session này"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Lấy tất cả messages của session
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            })
        
        return Response({
            "session_id": str(session.session_id),
            "messages": messages_data,
            "total": len(messages_data)
        })


class ChatSessionsViewSet(APIView):
    """
    API lấy danh sách sessions của user
    Endpoint: /api/chat/sessions/
    """
    permission_classes = [IsUser]

    @swagger_auto_schema(
        operation_summary="Lấy danh sách sessions của user",
        operation_description=(
            "Lấy danh sách tất cả chat sessions của user hiện tại.\n\n"
            "Mỗi session bao gồm: session_id, số lượng messages, thời gian tạo"
        ),
        responses={
            200: openapi.Response(
                description="Danh sách sessions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'sessions': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'message_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )
    def get(self, request):
        """
        GET /api/chat/sessions/
        Lấy danh sách sessions của user
        """
        user = request.user if request.user.is_authenticated else None
        
        if not user:
            return Response(
                {"error": "Yêu cầu đăng nhập"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Lấy tất cả sessions của user
        sessions = ChatSession.objects.filter(user=user).order_by('-updated_at')
        
        sessions_data = []
        for session in sessions:
            message_count = ChatMessage.objects.filter(session=session).count()
            sessions_data.append({
                "session_id": str(session.session_id),
                "message_count": message_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            })
        
        return Response({
            "sessions": sessions_data,
            "total": len(sessions_data)
        })

