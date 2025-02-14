from django.db import models


class LogEntry(models.Model):
    message = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)
    LOG_LEVEL_CHOICES = [
        ("trace", "Trace"),
        ("debug", "Debug"),
        ("info", "Info"),
        ("warn", "Warn"),
        ("error", "Error"),
    ]

    log_level = models.CharField(max_length=5, choices=LOG_LEVEL_CHOICES)
    occurred_on = models.DateTimeField(auto_now_add=True)
    COMPONENT_CHOICES = [
        ("ui", "UI"),
        ("api", "API"),
    ]

    component = models.CharField(max_length=3, choices=COMPONENT_CHOICES)

    def __str__(self):
        return f"{self.occurred_on} - {self.log_level} - {self.message}"
