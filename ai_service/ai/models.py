import uuid
from django.db import models
from django.utils import timezone

class AIGeneration(models.Model):
    TYPE_CHOICES = (
        ('image', 'Tạo ảnh'),
        ('avatar', 'Tạo avatar'),
        ('audio', 'Âm thanh'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user_id = models.CharField(max_length=50, db_index=True, help_text="ID của User từ Auth Service") 
    
    generation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='image')
    prompt = models.TextField()
    media_url = models.URLField(max_length=500)
    aspect_ratio = models.CharField(max_length=20, null=True, blank=True)
    resolution_config = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ai_generations'
        ordering = ['-created_at']

class UserAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ĐÃ MỞ KHÓA
    user_id = models.CharField(max_length=50, db_index=True)
    
    generation = models.ForeignKey(AIGeneration, on_delete=models.SET_NULL, null=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=AIGeneration.TYPE_CHOICES, default='image')
    media_url = models.URLField(max_length=500)
    prompt = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_assets'
        ordering = ['-created_at']