from django.urls import include, path
from rest_framework import routers

from .views import (
    ChatMessageViewSet,
    ChatSessionViewSet,
    GroupViewSet,
    LogEntryViewSet,
    UserViewSet,
)

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"chat-session", ChatSessionViewSet, "chat-session")
router.register(r"chat-message", ChatMessageViewSet, "chat-message")
router.register(r"log-entry", LogEntryViewSet, "log-entry")


urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
