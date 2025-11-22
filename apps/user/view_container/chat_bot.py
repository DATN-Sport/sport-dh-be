from apps.utils.chat_bot import ask_gemini
from apps.user.view_container import (
    Response, AllowAny, openapi, APIView, swagger_auto_schema, status, uuid, IsUser
)
from apps.user.models import User, ChatSession, ChatMessage
from apps.booking.models import Booking


# ---- APIView ----
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

        booking_history = Booking.objects.filter(user=user).order_by("booking_date")[:10]
        booking_history = list(booking_history.values())

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages.order_by("created_at")[:20]
        ]

        answer = ask_gemini(question=question, history=history, booking_history=booking_history)

        ChatMessage.objects.create(session=session, role="user", content=question)
        ChatMessage.objects.create(session=session, role="model", content=answer)

        return Response({
            "session_id": session.session_id,
            "question": question,
            "answer": answer
        })

