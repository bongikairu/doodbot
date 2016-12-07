from __future__ import unicode_literals

from django.db import models


class Event(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=32, blank=True, null=True, default=None)
    payload = models.TextField()
