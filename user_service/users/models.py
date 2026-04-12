from django.db import models

# Create your models here.
from django.db import models
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True)
    password = models.CharField(max_length=255)
    avatar_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "users"
class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower_id = models.UUIDField()
    following_id = models.UUIDField()

    class Meta:
        db_table = "follow"
        unique_together = ('follower_id', 'following_id')