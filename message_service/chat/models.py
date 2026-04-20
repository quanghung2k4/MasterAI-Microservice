import uuid
from django.db import models

class UserStatus(models.Model):
    """Bảng lưu trạng thái Online/Offline của người dùng"""
    user_id = models.UUIDField(primary_key=True)
    is_online = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_status"

class Message(models.Model):
    """Bảng lưu trữ tin nhắn chi tiết"""
    MESSAGE_TYPES = (
        (0, 'Text'),
        (1, 'Image')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # room_id giúp query toàn bộ tin nhắn của 2 người
    room_id = models.CharField(max_length=100, db_index=True) 
    
    sender_id = models.UUIDField()
    receiver_id = models.UUIDField()
    
    text = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    message_type = models.IntegerField(choices=MESSAGE_TYPES, default=0)
    
    is_read = models.BooleanField(default=False) # Dùng để đếm unread_count
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ['timestamp'] # Sắp xếp cũ nhất lên trước để load vào chat