# modules/post/presentation/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

from .models import (
    Post, Like, Comment, Media
)
from .serializers import PostSerializer, CommentSerializer, MediaSerializer

# Notification Service URL
NOTIFICATION_SERVICE_URL = "http://localhost:3004/api/notifications"


# =========================
# 📝 CREATE POST
# =========================
@api_view(['POST'])
def create_post(request):
    """
    Create a new post with optional multiple media files (images/voices)
    
    Request format (JSON):
    {
        "user_id": "uuid",
        "content": "text content",
        "visibility": "public|private|friends",
        "media": [
            {
                "url": "https://...",
                "media_type": "image|voice",
                "source": "upload|ai"
            }
        ]
    }
    """
    data = request.data.dict() if hasattr(request.data, 'dict') else request.data
    
    serializer = PostSerializer(data=data)

    if serializer.is_valid():
        post = serializer.save()
        
        # 🔥 Send notification when post is created
        try:
            notification_data = {
                "recipient_id": str(post.user_id),
                "sender_id": str(post.user_id),
                "type": "system",
                "title": "Your post was created successfully",
                "message": f"Posted: {post.content[:100]}",
                "data": {
                    "post_id": str(post.id),
                    "action": "post_created"
                }
            }
            
            print(f"🔔 Sending notification to: {NOTIFICATION_SERVICE_URL}/create/")
            print(f"📦 Notification data: {notification_data}")
            
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/create/",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Notification sent successfully!")
            else:
                print(f"❌ Notification failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            # Log error but don't fail the request
            print(f"❌ Notification error: {e}")
        
        return Response(PostSerializer(post).data, status=201)

    return Response(serializer.errors, status=400)


# =========================
# ✏️ UPDATE POST
# =========================
@api_view(['PUT', 'PATCH'])
def update_post(request, post_id):
    """
    Update an existing post (content, visibility, media)
    
    Request format (JSON):
    {
        "content": "updated text",
        "visibility": "public|private|friends",
        "media": [
            {
                "url": "https://...",
                "media_type": "image|voice",
                "source": "upload|ai"
            }
        ]
    }
    """
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)

    data = request.data.dict() if hasattr(request.data, 'dict') else request.data
    
    # Update post fields
    if 'content' in data:
        post.content = data['content']
    
    if 'visibility' in data:
        post.visibility = data['visibility']
    
    post.save()

    # Handle media updates (delete old, add new)
    if 'media' in data:
        # Delete existing media
        post.media.all().delete()
        
        # Create new media
        media_data = data['media']
        for index, m in enumerate(media_data):
            Media.objects.create(
                post=post,
                url=m.get('url'),
                media_type=m.get('media_type'),
                source=m.get('source', 'upload'),
                order=index
            )

    return Response(PostSerializer(post).data, status=200)

# Đếm số lượng bài post của user
@api_view(['GET'])
def get_user_post_count(request, user_id):
    try:
        count = Post.objects.filter(user_id=user_id, is_deleted=False).count()
        return Response({"post_count": count}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =========================
# 📄 GET FEED
# =========================
@api_view(['GET'])
def get_feed(request):
    posts = Post.objects.filter(is_deleted=False).order_by('-created_at')[:20]
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


# =========================
# ❤️ LIKE / UNLIKE
# =========================
@api_view(['POST'])
def toggle_like(request, post_id):
    user_id = request.data.get('user_id')

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)

    like, created = Like.objects.get_or_create(
        user_id=user_id,
        post=post
    )

    if not created:
        like.delete()
        post.like_count -= 1
        post.save()
        return Response({'message': 'unliked'})

    post.like_count += 1
    post.save()

    # 🔥 Send notification when someone likes a post
    if str(post.user_id) != str(user_id):  # Don't notify self-likes
        try:
            notification_data = {
                "recipient_id": str(post.user_id),
                "sender_id": str(user_id),
                "type": "like",
                "title": "Someone liked your post",
                "message": f"A user liked your post: '{post.content[:50]}...'",
                "data": {
                    "post_id": str(post_id),
                    "liker_id": str(user_id),
                    "action": "like",
                    "post_content": post.content[:100]
                }
            }
            
            print(f"🔔 Sending notification to: {NOTIFICATION_SERVICE_URL}/create/")
            print(f"📦 Notification data: {notification_data}")
            
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/create/",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Notification sent successfully!")
            else:
                print(f"❌ Notification failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Notification error: {e}")

    return Response({'message': 'liked'})


# =========================
# 💬 ADD COMMENT
# =========================
@api_view(['POST'])
def add_comment(request, post_id):
    user_id = request.data.get('user_id')
    content = request.data.get('content')
    parent_id = request.data.get('parent')

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)

    comment = Comment.objects.create(
        user_id=user_id,
        post=post,
        content=content,
        parent_id=parent_id
    )

    post.comment_count += 1
    post.save()

    # 🔥 Send notification when someone comments on a post
    if str(post.user_id) != str(user_id):  # Don't notify self-comments
        try:
            notification_data = {
                "recipient_id": str(post.user_id),
                "sender_id": str(user_id),
                "type": "comment",
                "title": "Someone commented on your post",
                "message": f"New comment: '{content[:70]}...'",
                "data": {
                    "post_id": str(post_id),
                    "comment_id": str(comment.id),
                    "commenter_id": str(user_id),
                    "action": "comment",
                    "comment_content": content[:150],
                    "post_content": post.content[:100]
                }
            }
            
            print(f"🔔 Sending notification to: {NOTIFICATION_SERVICE_URL}/create/")
            print(f"📦 Notification data: {notification_data}")
            
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/create/",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Notification sent successfully!")
            else:
                print(f"❌ Notification failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Notification error: {e}")

    return Response(CommentSerializer(comment).data, status=201)


# =========================
# 📄 GET COMMENTS
# =========================
@api_view(['GET'])
def get_comments(request, post_id):
    comments = Comment.objects.filter(
        post_id=post_id,
        parent=None
    ).order_by('-created_at')

    return Response(CommentSerializer(comments, many=True).data)


# =========================
# 🗑️ DELETE POST
# =========================
@api_view(['DELETE'])
def delete_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.is_deleted = True
        post.save()
        return Response({'message': 'deleted'})
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)