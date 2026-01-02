from django.urls import path
from apps.chat.views import ChatbotViewSet, ChatHistoryViewSet, ChatSessionsViewSet

urlpatterns = [
    path('chat/', ChatbotViewSet.as_view(), name='chatbot'),
    path('chat/history/', ChatHistoryViewSet.as_view(), name='chat-history'),
    path('chat/sessions/', ChatSessionsViewSet.as_view(), name='chat-sessions'),
]

