import uuid

from django.contrib.auth.models import User
from django.db import models


def generate_uuid():
    return uuid.uuid4().hex


class ChatSession(models.Model):
    unique_key = models.UUIDField(
        default=generate_uuid, editable=False, verbose_name="Unique key", unique=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    is_default_title = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    chat_session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.CharField(max_length=50)  # "User" or "Chatbot"
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
