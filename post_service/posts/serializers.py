# modules/post/presentation/serializers.py

from rest_framework import serializers
from .models import (
    Post, Media, Like, Comment
)


# =========================
# MEDIA
# =========================
class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id', 'url', 'media_type', 'source',
            'ai_metadata', 'order'
        ]


# =========================
# COMMENT
# =========================
class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user_id', 'content',
            'parent', 'replies', 'created_at'
        ]

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data


# =========================
# POST
# =========================
class PostSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, required=False)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'user_id', 'content',
            'visibility',
            'like_count', 'comment_count',
            'media', 'comments',
            'created_at'
        ]

    def create(self, validated_data):
        media_data = validated_data.pop('media', [])

        post = Post.objects.create(**validated_data)

        for index, m in enumerate(media_data):
            m['order'] = index  # Override order value
            Media.objects.create(
                post=post,
                **m
            )

        return post