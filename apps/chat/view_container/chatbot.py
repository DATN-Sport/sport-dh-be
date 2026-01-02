"""
View xử lý API chatbot với chat history đầy đủ
"""
import uuid
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from apps.depends.oauth2 import IsUser
from apps.chat.models import ChatSession, ChatMessage
from apps.chat.services import ask_chatbot, build_command_context
from apps.booking.models import Booking


@method_decorator(
    ratelimit(key='user', rate=f'{settings.CHAT_LIMIT_PER_MINUTE}/m', block=True),
    name='post'
)
class ChatbotViewSet(APIView):
    """
    API Chatbot với chat history đầy đủ
    Endpoint: /api/chat/
    """
    permission_classes = [IsUser]

    @swagger_auto_schema(
        operation_summary="Chat với chatbot AI",
        operation_description=(
            "Chatbot hỗ trợ khách hàng DaiHiep Sport sử dụng FPT AI.\n\n"
            "Chatbot sẽ nhớ lịch sử cuộc trò chuyện trong cùng một session.\n"
            "Nếu không có session_id, hệ thống sẽ tạo session mới.\n"
            "Nếu có session_id, chatbot sẽ tiếp tục cuộc trò chuyện từ lịch sử trước đó."
        ),
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description="Câu hỏi hoặc nội dung muốn hỏi chatbot",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                'session_id',
                openapi.IN_QUERY,
                description="ID phiên chat (UUID). Nếu không có sẽ tạo mới",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'q': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Câu hỏi'
                ),
                'session_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='ID phiên chat (UUID)'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Kết quả trả về từ chatbot",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'question': openapi.Schema(type=openapi.TYPE_STRING),
                        'answer': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Thiếu tham số 'q'"
        }
    )
    def post(self, request):
        """
        POST /api/chat/
        Gửi câu hỏi đến chatbot và nhận câu trả lời
        """
        user = request.user if request.user.is_authenticated else None
        
        # Lấy question từ body hoặc query params
        question = request.data.get("q") or request.query_params.get("q")
        if not question:
            return Response(
                {"error": "Thiếu tham số 'q' (câu hỏi)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lấy hoặc tạo session
        session_id = request.data.get("session_id") or request.query_params.get("session_id")
        
        if session_id:
            try:
                # Tìm session theo session_id
                session = ChatSession.objects.get(session_id=session_id)
                # Kiểm tra quyền: user chỉ có thể truy cập session của chính mình
                if user and session.user and session.user != user:
                    return Response(
                        {"error": "Không có quyền truy cập session này"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ChatSession.DoesNotExist:
                # Nếu không tìm thấy, tạo session mới
                session = ChatSession.objects.create(
                    user=user,
                    session_id=session_id
                )
        else:
            # Tạo session mới
            session = ChatSession.objects.create(
                user=user,
                session_id=uuid.uuid4()
            )
        
        # Lấy booking history của user (nếu đã đăng nhập)
        booking_history = []
        if user:
            booking_history_qs = Booking.objects.filter(user=user).select_related(
                "sport_field",
                "sport_field__sport_center",
                "rental_slot"
            ).order_by("-booking_date")[:10]
            
            for booking in booking_history_qs:
                sport_field = booking.sport_field
                sport_center = sport_field.sport_center if sport_field else None
                booking_history.append({
                    "id": str(booking.id),
                    "price": booking.price,
                    "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                    "status": booking.status,
                    "rental_slot": booking.rental_slot.time_slot if booking.rental_slot else None,
                    "sport_field": {
                        "id": str(sport_field.id) if sport_field else None,
                        "name": sport_field.name if sport_field else None,
                        "address": sport_field.address if sport_field else None,
                        "sport_type": sport_field.sport_type if sport_field else None,
                        "sport_center": {
                            "id": str(sport_center.id) if sport_center else None,
                            "name": sport_center.name if sport_center else None,
                        } if sport_center else None,
                    } if sport_field else None,
                })
        
        # Gọi chatbot service với chat history
        command_context = build_command_context(question, user, booking_history)
        question_for_ai = command_context.ai_prompt if command_context else question
        system_messages = command_context.system_messages if command_context else None

        answer = ask_chatbot(
            question=question_for_ai,
            session=session,
            booking_history=booking_history if booking_history else None,
            command_context=system_messages,
        )
        
        # Lưu message vào database
        ChatMessage.objects.create(session=session, role="user", content=question)
        ChatMessage.objects.create(session=session, role="assistant", content=answer)
        
        return Response({
            "session_id": str(session.session_id),
            "question": question,
            "answer": answer
        })

