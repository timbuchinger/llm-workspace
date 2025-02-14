import randomname
from bot.models import ChatMessage, ChatSession
from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import LogEntry
from .serializers import (
    ChatMessageSerializer,
    ChatSessionSerializer,
    GroupSerializer,
    LogEntrySerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChatSessionViewSet(viewsets.ViewSet):
    """
    API endpoint that allows chat sessions to be viewed or edited.
    """

    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        chat_sessions = (
            ChatSession.objects.filter(user=request.user, is_deleted=False)
            .all()
            .order_by("-created_at")
        )
        serializer = ChatSessionSerializer(chat_sessions, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        chat_session = ChatSession.objects.get(
            user=request.user, unique_key=pk, is_deleted=False
        )
        serializer = ChatSessionSerializer(chat_session, many=False)
        return Response(serializer.data)

    def create(self, request):
        name = randomname.get_name()
        chat_session = ChatSession.objects.create(user=request.user, title=name)
        serializer = ChatSessionSerializer(chat_session, many=False)
        return Response(serializer.data)

    # @transaction.atomic
    def destroy(self, request, pk):
        with transaction.atomic():
            count = ChatSession.objects.filter(
                user=request.user, is_deleted=False
            ).count()

            chat_session = ChatSession.objects.get(
                user=request.user, unique_key=pk, is_deleted=False
            )
            chat_session.is_deleted = True
            chat_session.save()
            count = ChatSession.objects.filter(
                user=request.user, is_deleted=False
            ).count()

        transaction.commit()
        serializer = ChatSessionSerializer(chat_session, many=False)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ViewSet):
    """
    API endpoint that allows chat messages to be viewed or edited.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, chat_session_id: str):
        chat_messages = ChatMessage.objects.filter(
            user=request.user, chat_session_id=chat_session_id
        ).order_by("-created_at")
        serializer = ChatSessionSerializer(chat_messages, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        chat_message = ChatMessage.objects.get(
            chat_session__user=request.user, id=pk, is_deleted=False
        )
        serializer = ChatMessageSerializer(chat_message, many=False)
        return Response(serializer.data)

    def create(self, request):
        chat_session = ChatSession.objects.get(
            user=request.user,
            unique_key=request.data["chat_session_id"],
            is_deleted=False,
        )
        chat_message = ChatMessage.objects.create(
            sender="User",
            chat_session=chat_session,
            content=request.data["content"],
        )
        serializer = ChatMessageSerializer(chat_message)
        return Response(serializer.data)


class LogEntryViewSet(viewsets.ViewSet):
    """
    API endpoint that allows log entries to be viewed or created.
    """

    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        component_type = request.query_params.get("component_type")
        loglevel = request.query_params.get("loglevel")
        log_entries = LogEntry.objects.all()

        if component_type:
            log_entries = log_entries.filter(component_type=component_type)
        if loglevel:
            log_entries = log_entries.filter(loglevel=loglevel)

        serializer = LogEntrySerializer(log_entries, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = LogEntrySerializer(data=request.data)
        if serializer.is_valid():
            log_entry = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
