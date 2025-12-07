from django_ratelimit.decorators import ratelimit

from apps.utils.chat_bot import ask_fpt
from apps.user.view_container import (
    Response, AllowAny, openapi, APIView, swagger_auto_schema, status, uuid, IsUser
)

from django.utils.decorators import method_decorator
from apps.user.models import User, ChatSession, ChatMessage
from apps.booking.models import Booking
from django.conf import settings as st


# ---- APIView ----
@method_decorator(ratelimit(key='user', rate=f'{st.CHAT_LIMIT_PER_MINUTE}/m', block=True), name='post')
class ChatbotViewSet(APIView):
    permission_classes = [IsUser]

    """
    Chatbot local sử dụng Ollama (phi3-mini)
    Endpoint chính: /api/chatbot/
    """

    @swagger_auto_schema(
        operation_summary="Chat với chatbot local (phi3-mini)",
        operation_description=(
            "Chatbot này sử dụng mô hình **phi3-mini** chạy qua **Ollama local**.\n\n"
            "Nhập câu hỏi vào tham số `q` (body hoặc query param)."
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
                description="Session chatbot",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Kết quả trả về từ chatbot",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'question': openapi.Schema(type=openapi.TYPE_STRING),
                        'answer': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Thiếu tham số 'q'"
        }
    )
    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        question = request.data.get("q") or request.query_params.get("q")
        session_id = request.data.get("session_id") or request.query_params.get("session_id")

        session, _ = ChatSession.objects.get_or_create(
            user=user,
            session_id=session_id or str(uuid.uuid4())
        )

        booking_history_qs = Booking.objects.filter(user=user).select_related(
            "sport_field",
            "sport_field__sport_center",
            "rental_slot"
        ).order_by("booking_date")[:10]

        booking_history = []
        for booking in booking_history_qs:
            sport_field = booking.sport_field
            sport_center = sport_field.sport_center if sport_field else None
            booking_history.append({
                "id": booking.id,
                "price": booking.price,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                "status": booking.status,
                "rental_slot": booking.rental_slot.time_slot if booking.rental_slot else None,
                "sport_field": {
                    "id": sport_field.id,
                    "name": sport_field.name,
                    "address": sport_field.address,
                    "sport_type": sport_field.sport_type,
                    "sport_center": {
                        "id": sport_center.id,
                        "name": sport_center.name,
                    } if sport_center else None,
                } if sport_field else None,
            })

        answer = ask_fpt(question=question, booking_history=booking_history)

        ChatMessage.objects.create(session=session, role="user", content=question)
        ChatMessage.objects.create(session=session, role="model", content=answer)

        return Response({
            "session_id": session.session_id,
            "question": question,
            "answer": answer
        })

