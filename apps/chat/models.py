import uuid
from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """
    Model lưu thông tin phiên chat
    Mỗi session có thể có nhiều messages
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_sessions'
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_chatsession'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        user_name = self.user.full_name if self.user else "Anonymous"
        return f"ChatSession({user_name}) - {self.session_id}"


class ChatMessage(models.Model):
    """
    Model lưu từng message trong chat
    Role: 'user' hoặc 'assistant' (theo chuẩn OpenAI)
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(
        ChatSession,
        related_name='messages',
        on_delete=models.CASCADE
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_chatmessage'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

