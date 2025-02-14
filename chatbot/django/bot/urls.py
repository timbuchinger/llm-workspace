from django.urls import path

from . import views

app_name = "bot"

urlpatterns = [
    path("chats/", views.chat_list, name="chat_list"),
    path("chat/", views.chat_view, name="chat"),
    path("base/", views.base_view, name="base_view"),
    path("base2/", views.base2_view, name="base2_view"),
    path("home/", views.home_view, name="home_view"),
]
