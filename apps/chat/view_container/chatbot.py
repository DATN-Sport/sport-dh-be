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
from apps.chat.services import ask_chatbot, get_available_bookings, parse_user_booking_intent, create_booking_from_intent
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
                # Kiểm tra quyền: nếu user không khớp, tạo session mới (user đã đổi tài khoản)
                if user and session.user and session.user != user:
                    # User đã đổi tài khoản, tạo session mới
                    session = ChatSession.objects.create(
                        user=user,
                        session_id=uuid.uuid4()
                    )
                elif user and not session.user:
                    # Session cũ là anonymous, gán user mới vào
                    session.user = user
                    session.save()
            except ChatSession.DoesNotExist:
                # Nếu không tìm thấy, tạo session mới
                session = ChatSession.objects.create(
                    user=user,
                    session_id=uuid.uuid4()
                )
        else:
            # Tạo session mới
            session = ChatSession.objects.create(
                user=user,
                session_id=uuid.uuid4()
            )

        
        # Lấy dữ liệu booking available (sân trống) - luôn lấy để chatbot có thể trả lời
        available_bookings = get_available_bookings()
        
        # Kiểm tra xem user có muốn đặt sân không (parse từ câu hỏi)
        booking_intent = None
        if user:
            booking_intent = parse_user_booking_intent(question, available_bookings)
        
        # Nếu có booking intent, xử lý đặt sân trực tiếp
        if booking_intent and user:
            booking_result = create_booking_from_intent(user, booking_intent)
            
            if booking_result.get('success'):
                answer = (
                    f"✅ Đã đặt sân thành công {booking_result.get('booking_id')}!\n\n"
                    f"📅 Sân: {booking_result.get('sport_field_name')}\n"
                    f"🏟️ Trung tâm: {booking_result.get('center_name')}\n"
                    f"📆 Ngày: {booking_result.get('booking_date')}\n"
                    f"⏰ Khung giờ: {booking_result.get('rental_slot')}\n"
                    f"💰 Giá: {booking_result.get('price'):,.0f}đ\n\n"
                    f"Cảm ơn bạn đã sử dụng dịch vụ!"
                )
            else:
                error_msg = booking_result.get('error', 'Không thể đặt sân')
                answer = f"❌ {error_msg}\n\nVui lòng kiểm tra lại thông tin hoặc chọn khung giờ khác."
        else:
            # Gọi chatbot service với chat history và available bookings
            answer = ask_chatbot(
                question=question,
                session=session,
                booking_history=None,
                available_bookings=available_bookings,
                command_context=None,
                user=user,
            )
        
        # Lưu message vào database
        ChatMessage.objects.create(session=session, role="user", content=question)
        ChatMessage.objects.create(session=session, role="assistant", content=answer)
        
        return Response({
            "session_id": str(session.session_id),
            "question": question,
            "answer": answer
        })

