from bot.models import LogEntry
from django.contrib import admin


class LogEntryAdmin(admin.ModelAdmin):
    pass


admin.site.register(LogEntry, LogEntryAdmin)
