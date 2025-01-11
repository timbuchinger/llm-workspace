from django.urls import path, re_path

from . import consumers

websocket_urlpatterns = [
    path("ws/chat/", consumers.ChatConsumer.as_asgi()),
    path("ws/chat/<str:chat_id>/", consumers.ChatConsumer.as_asgi()),
]
