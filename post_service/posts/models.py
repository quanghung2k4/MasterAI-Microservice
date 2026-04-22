# modules/post/infrastructure/models.py

import uuid
from django.db import models


# =========================
# 📌 POST (Aggregate Root)
# =========================
class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField()  # lấy từ user_service

    content = models.TextField(blank=True)  # status text

    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='public'
    )

    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_deleted']),  # 🔥 thêm
            models.Index(fields=['is_deleted', '-created_at']),  # 🔥 feed cực nhanh
        ]

    def __str__(self):
        return f"Post {self.id} by {self.user_id}"


# =========================
# 📌 MEDIA (Image / Avatar / Voice)
# =========================
class Media(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('avatar', 'Avatar'),
        ('voice', 'Voice'),
    ]

    SOURCE_TYPE = [
        ('upload', 'Upload'),
        ('ai', 'AI Generated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media'
    )

    url = models.TextField()

    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE,
        default='upload'
    )

    #metadata cho AI (prompt, model, duration...)
    ai_metadata = models.JSONField(null=True, blank=True)

    #thứ tự hiển thị (giống Instagram carousel)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'media'
        ordering = ['order']


# =========================
# ❤️ LIKE
# =========================
class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField()

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'likes'
        unique_together = ('user_id', 'post')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['post']),
            models.Index(fields=['user_id', 'post']),  # 🔥 tối ưu liked posts
        ]


# =========================
# 💬 COMMENT
# =========================
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField()

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    content = models.TextField()

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user_id']),
            models.Index(fields=['post', '-created_at']),  # 🔥 load comment nhanh
        ]


# =========================
# 🔖 BOOKMARK (optional nhưng nên có)
# =========================
class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField()

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookmarks'
        unique_together = ('user_id', 'post')


# =========================
# 🔁 SHARE (repost)
# =========================
class Share(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField()

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='shares'
    )

    shared_content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shares'