from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin", admin.site.urls),
    path("bot/", include("bot.urls")),
    path("api/", include("api.urls")),
    path("bot/", include("bot.urls", namespace="bot")),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
