# modules/post/presentation/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from rest_framework.pagination import PageNumberPagination

from .models import (
    Post, Like, Comment, Media, UserInteraction
)
from .serializers import PostSerializer, CommentSerializer, MediaSerializer
from django.core.cache import cache
from django.db.models import F
import cloudinary.uploader
from django.shortcuts import get_object_or_404
from django.db import transaction

# Notification Service URL
NOTIFICATION_SERVICE_URL = "http://localhost:3004/api/notifications"


# =========================
# 📝 CREATE POST
# =========================
@api_view(['POST'])
def create_post(request):
    cache.delete("feed:global")

    data = request.data.dict() if hasattr(request.data, 'dict') else request.data

    serializer = PostSerializer(data=data)

    if serializer.is_valid():
        post = serializer.save()

        # =========================
        # 🔥 UPLOAD MEDIA TO CLOUDINARY
        # =========================
        files = request.FILES.getlist('files')

        for index, file in enumerate(files):
            try:
                import cloudinary.uploader

                result = cloudinary.uploader.upload(
                    file,
                    resource_type="auto"  # 🔥 hỗ trợ image + audio
                )

                # detect loại media
                resource_type = result.get("resource_type", "")

                if resource_type == "image":
                    media_type = "image"
                elif resource_type in ["video", "raw"]:
                    media_type = "voice"
                else:
                    media_type = "image"

                Media.objects.create(
                    post=post,
                    url=result.get("secure_url"),
                    media_type=media_type,
                    source="upload",
                    order=index
                )

            except Exception as e:
                print("❌ Cloudinary upload error:", e)

        # =========================
        # 🔔 SEND NOTIFICATION
        # =========================
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

            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/create/",
                json=notification_data,
                timeout=5
            )

        except requests.exceptions.RequestException as e:
            print(f"❌ Notification error: {e}")

        return Response(PostSerializer(post).data, status=201)

    return Response(serializer.errors, status=400)

# =========================
# ✏️ UPDATE POST
# =========================
@api_view(['PUT', 'PATCH'])
def update_post(request, post_id):
    cache.delete("feed:global")
    cache.delete(f"post:{post_id}")

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)

    # 1. Cập nhật Content và Visibility
    post.content = request.data.get('content', post.content)
    post.visibility = request.data.get('visibility', post.visibility)
    post.save()

    # 2. Xử lý GIỮ LẠI ảnh cũ
    # Android sẽ gửi danh sách các URL ảnh cũ vẫn còn trên giao diện qua 'kept_media'
    kept_media_urls = request.data.getlist('kept_media')

    # Lấy tất cả media hiện tại của post
    current_media = post.media.all()

    for m in current_media:
        if m.url not in kept_media_urls:
            # Nếu URL của ảnh hiện tại không nằm trong danh sách giữ lại -> Xóa
            # Tùy chọn: Xóa file vật lý trên Cloudinary tại đây nếu muốn
            m.delete()

    # 3. Xử lý THÊM ảnh mới từ máy (Multipart files)
    files = request.FILES.getlist('files')
    if files:
        import cloudinary.uploader
        # Tính toán thứ tự tiếp theo (order) dựa trên số lượng ảnh đã giữ lại
        current_count = post.media.count()

        for index, file in enumerate(files):
            try:
                result = cloudinary.uploader.upload(file, resource_type="auto")
                resource_type = result.get("resource_type", "")
                media_type = "voice" if resource_type in ["video", "raw"] else "image"

                Media.objects.create(
                    post=post,
                    url=result.get("secure_url"),
                    media_type=media_type,
                    source="upload",
                    order=current_count + index # Đảm bảo thứ tự nối tiếp
                )
            except Exception as e:
                print(f"❌ Cloudinary upload error: {e}")

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
    cache_key = "feed:global"

    data = cache.get(cache_key)
    if data:
        return Response(data)

    posts = Post.objects.filter(
        is_deleted=False
    ).order_by('-created_at')[:20]

    serializer = PostSerializer(posts, many=True)

    cache.set(cache_key, serializer.data, timeout=60)

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
        # ❌ UNLIKE
        like.delete()
        post.like_count -= 1
        post.save()

        # 🔥 GHI NHẬN INTERACTION
        record_interaction(user_id, post_id, -5.0)

        return Response({'message': 'unliked'})

    # ✅ LIKE
    post.like_count += 1
    post.save()

    # 🔥 GHI NHẬN INTERACTION
    record_interaction(user_id, post_id, 5.0)

    # 🔔 Notification (giữ nguyên)
    if str(post.user_id) != str(user_id):
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

            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/create/",
                json=notification_data,
                timeout=5
            )

        except requests.exceptions.RequestException as e:
            print(f"❌ Notification error: {e}")

    return Response({'message': 'liked'})
# =========================
# 💬 ADD COMMENT
# =========================
@api_view(['POST'])
def add_comment(request, post_id):
    cache.delete(f"comments:{post_id}")
    cache.delete("feed:global")
    user_id = request.data.get('user_id')
    sender_name = request.data.get('username', 'Người dùng') 
    sender_avatar = request.data.get('avatar', '')
    content = request.data.get('content')
    parent_id = request.data.get('parent')

    post = get_object_or_404(Post, id=post_id)
    comment = Comment.objects.create(user_id=user_id, post=post, content=content)
    
    post.comment_count += 1
    post.save()
    
    # AI: Ghi nhận tương tác
    record_interaction(user_id, post_id, 4.0)

    # 🔥 Send notification when someone comments on a post
    if str(post.user_id) != str(user_id):  # Don't notify self-comments
        try:
            notification_data = {
                "recipient_id": str(post.user_id),
                "sender": {
                    "id": str(user_id),
                    "username": sender_name,
                    "avatar": sender_avatar
                },
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

    serializer = CommentSerializer(comment)
    return Response(serializer.data, status=201)


# =========================
# 📄 GET COMMENTS
# =========================
@api_view(['GET'])
def get_comments(request, post_id):
    cache_key = f"comments:{post_id}"

    data = cache.get(cache_key)
    if data:
        return Response(data)

    comments = Comment.objects.filter(
        post_id=post_id,
        parent=None
    ).prefetch_related('replies') \
     .order_by('-created_at')

    serializer = CommentSerializer(comments, many=True)

    cache.set(cache_key, serializer.data, timeout=60)

    return Response(serializer.data)

# =========================
# 🗑️ DELETE POST
# =========================
@api_view(['DELETE'])
def delete_post(request, post_id):
    cache.delete("feed:global")
    cache.delete(f"post:{post_id}")
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


@api_view(['GET'])
def get_user_liked_posts(request, user_id):
    """
    Lấy danh sách bài viết mà một user đã thích, có phân trang.
    Sắp xếp theo thời gian like mới nhất.
    """
    # 1. Truy vấn dữ liệu: Lọc các bài post có chứa Like của user_id này
    # Dùng 'likes__user_id' để truy xuất ngược từ Post sang bảng Like
    posts = Post.objects.prefetch_related('media').filter(
        likes__user_id=user_id,
        is_deleted=False
    ).order_by('-likes__created_at') # Sắp xếp theo thời gian thả tim mới nhất

    # 2. Khởi tạo bộ phân trang
    paginator = PageNumberPagination()
    paginator.page_size = 10  # Số lượng bài viết trên 1 trang

    # 3. Áp dụng phân trang vào queryset
    paginated_posts = paginator.paginate_queryset(posts, request)

    # 4. Serialize dữ liệu
    serializer = PostSerializer(paginated_posts, many=True)

    # 5. Trả về response kèm theo thông tin phân trang
    return paginator.get_paginated_response(serializer.data)

from .ai.recommender import HybridRecommender

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from .ai.recommender import HybridRecommender

@api_view(['GET'])
def get_recommended_feed(request):
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    # Lấy 100 bài viết mới nhất để làm "nguyên liệu"
    posts_pool = Post.objects.filter(is_deleted=False).order_by('-created_at')[:100]

    recommender = HybridRecommender()
    smart_posts = recommender.recommend(user_id, posts_pool)

    serializer = PostSerializer(smart_posts, many=True)
    return Response(serializer.data)

# Ví dụ logic chèn vào hàm Like
def record_interaction(user_id, post_id, action_score):
    interaction, created = UserInteraction.objects.get_or_create(
        user_id=user_id,
        post_id=post_id,
        defaults={'score': 0}
    )

    if created:
        interaction.score = action_score
    else:
        interaction.score += action_score

    interaction.score = max(interaction.score, -100)
    interaction.save()