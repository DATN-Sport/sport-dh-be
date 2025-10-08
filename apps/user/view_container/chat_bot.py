from apps.utils.chat_bot import ask_gemini
from apps.user.view_container import (
    Response, AllowAny, openapi, APIView, swagger_auto_schema, status
)


# ---- APIView ----
class ChatbotViewSet(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
        question = request.data.get("q") or request.query_params.get("q")
        if not question:
            return Response(
                {"error": "Thiếu tham số 'q'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        answer = ask_gemini(question=question)
        return Response({
            "question": question,
            "answer": answer
        })
