from __future__ import unicode_literals

from django.db import models


class Event(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    payload = models.TextField()
