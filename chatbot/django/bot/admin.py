from bot.models import ChatMessage, ChatSession
from django.contrib import admin


class ChatSessionAdmin(admin.ModelAdmin):
    pass


class ChatMessageAdmin(admin.ModelAdmin):
    pass


admin.site.register(ChatSession, ChatSessionAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
