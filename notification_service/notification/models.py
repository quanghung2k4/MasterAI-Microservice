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
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    sender_avatar = models.TextField(null=True, blank=True)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    message = models.TextField()

    data = models.JSONField(null=True, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Sắp xếp mặc định: Thông báo mới nhất (created_at giảm dần) sẽ hiện lên đầu
        ordering = ['-created_at']

        # Tên hiển thị trong trang Admin Django
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

        # Đánh index cho các trường thường xuyên dùng để lọc (tăng tốc độ truy vấn)
        indexes = [
            models.Index(fields=['recipient_id', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.type} to {self.recipient_id} - {self.title}"