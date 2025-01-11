# views.py
from django.http import JsonResponse
from django.shortcuts import render

from .models import ChatSession


def chat_list(request):
    chats = (
        ChatSession.objects.filter(user=request.user)
        .order_by("-created_at")
        .values("id", "title", "created_at")
    )
    return JsonResponse({"chats": list(chats)})


def chat_view(request):
    return render(request, "bot/chat.html")


def base_view(request):
    return render(request, "bot/sidebar_layout.html")


def base2_view(request):
    return render(request, "bot/base2.html")


def home_view(request):
    print("home view.")
    return render(request, "bot/home.html")
