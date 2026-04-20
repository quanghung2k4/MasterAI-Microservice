# modules/post/presentation/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import (
    Post, Like, Comment, Media
)
from .serializers import PostSerializer, CommentSerializer, MediaSerializer


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

@api_view(['GET'])
def get_user_posts(request, user_id):
    """
    Lấy danh sách bài viết của một user cụ thể, có phân trang.
    """
    # 1. Truy vấn dữ liệu (Tối ưu với prefetch_related)
    posts = Post.objects.prefetch_related('media').filter(
        user_id=user_id,
        is_deleted=False
    ).order_by('-created_at')

    # 2. Khởi tạo bộ phân trang
    paginator = PageNumberPagination()
    paginator.page_size = 10  # Số lượng bài viết trên 1 trang (có thể tùy chỉnh)

    # 3. Áp dụng phân trang vào queryset
    paginated_posts = paginator.paginate_queryset(posts, request)

    # 4. Serialize dữ liệu
    serializer = PostSerializer(paginated_posts, many=True)

    # 5. Trả về response kèm theo thông tin phân trang (next, previous, count)
    return paginator.get_paginated_response(serializer.data)