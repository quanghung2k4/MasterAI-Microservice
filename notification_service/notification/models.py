import uuid
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    recipient_id = models.UUIDField()
    sender_id = models.UUIDField(null=True, blank=True)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    message = models.TextField()

    data = models.JSONField(null=True, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)