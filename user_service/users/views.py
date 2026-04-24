from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from .models import User,Follow
import requests
from .serializers import UserSerializer
from django.http import JsonResponse
from django.db.models import Q
from .models import User

# Giả sử POST_SERVICE đang chạy ở cổng 3002
POST_SERVICE_URL = "http://localhost:3002/api/posts/count/"

# Notification Service URL
NOTIFICATION_SERVICE_URL = "http://localhost:3004/api/notifications"

@api_view(['POST'])
def toggle_follow(request, user_id):
    """
    API để Follow hoặc Unfollow một người dùng.
    - user_id (trên URL): ID của người được theo dõi (following_id)
    - follower_id (trong Body): ID của người đang thao tác
    """
    follower_id = request.data.get('follower_id')

    if not follower_id:
        return Response({'error': 'Thiếu follower_id trong body'}, status=status.HTTP_400_BAD_REQUEST)

    # Chuyển đổi về string để so sánh an toàn, tránh việc user tự follow chính mình
    if str(follower_id) == str(user_id):
        return Response({'error': 'Bạn không thể tự theo dõi chính mình'}, status=status.HTTP_400_BAD_REQUEST)

    # Kiểm tra xem record follow này đã tồn tại chưa
    follow_record = Follow.objects.filter(follower_id=follower_id, following_id=user_id).first()

    if follow_record:
        # Nếu đã follow rồi -> Xoá record (Unfollow)
        follow_record.delete()
        return Response({
            'message': 'Đã bỏ theo dõi',
            'is_following': False
        }, status=status.HTTP_200_OK)
    else:
        # Nếu chưa follow -> Tạo record mới (Follow)
        Follow.objects.create(follower_id=follower_id, following_id=user_id)
        return Response({
            'message': 'Đã theo dõi thành công',
            'is_following': True
        }, status=status.HTTP_201_CREATED)

# GET ALL USERS
@api_view(['GET'])
def get_all_users(request):
    users = User.objects.all().order_by('-created_at')
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


# GET USER BY ID
@api_view(['GET'])
def get_user_by_id(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # 1. Xử lý trạng thái is_followed
    current_user_id = request.query_params.get('current_user_id')
    is_followed = False
    
    if current_user_id:
        is_followed = Follow.objects.filter(
            follower_id=current_user_id, 
            following_id=user_id
        ).exists()

    # 2. Đếm số lượng follower và following
    follower_count = Follow.objects.filter(following_id=user_id).count()
    following_count = Follow.objects.filter(follower_id=user_id).count()

    # 3. Giao tiếp với Post Service để lấy post_count
    post_count = 0
    try:
        response = requests.get(f"{POST_SERVICE_URL}{user_id}/", timeout=3)
        if response.status_code == 200:
            post_count = response.json().get("post_count", 0)
    except requests.exceptions.RequestException as e:
        # Xử lý lỗi nếu Post Service bị chết (fallback về 0)
        print(f"Lỗi gọi Post Service: {e}")

    # 4. Trả về format chuẩn
    data = {
        "id": str(target_user.id),
        "username": target_user.username,
        "email": target_user.email,
        "avatar_url": target_user.avatar_url,
        "is_followed": is_followed,
        "post_count": post_count,
        "follower_count": follower_count,
        "following_count": following_count
    }

    return Response(data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def register(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    avatar_url = request.data.get("avatar_url")

    # 🔍 Validate
    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    if email and User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=400)

    # 🔐 Hash password
    hashed_password = make_password(password)

    # 🆕 Create user
    user = User.objects.create(
        username=username,
        email=email,
        password=hashed_password,
        avatar_url=avatar_url
    )

    return Response({
        "message": "Register successful",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at
        }
    }, status=201)


@csrf_exempt
@api_view(['POST'])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Missing username or password"}, status=400)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # 🔥 So sánh password đã hash
    if not check_password(password, user.password):
        return Response({"error": "Wrong password"}, status=401)

    return Response({
        "message": "Login successful",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url
        }
    })




@csrf_exempt
@api_view(['POST'])
def logout(request):
    return Response({
        "message": "Logout successful"
    })


# =========================
# 👥 FOLLOW / UNFOLLOW
# =========================
@csrf_exempt
@api_view(['POST'])
def follow_user(request):
    """
    Follow a user
    
    Request format (JSON):
    {
        "follower_id": "uuid",
        "following_id": "uuid"
    }
    """
    follower_id = request.data.get('follower_id')
    following_id = request.data.get('following_id')
    
    # Validate
    if not follower_id or not following_id:
        return Response({"error": "follower_id and following_id are required"}, status=400)
    
    if follower_id == following_id:
        return Response({"error": "Cannot follow yourself"}, status=400)
    
    try:
        following_user = User.objects.get(id=following_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    
    # Create or get follow relationship
    follow, created = Follow.objects.get_or_create(
        follower_id=follower_id,
        following_id=following_id
    )
    
    if not created:
        return Response({"error": "Already following this user"}, status=400)
    
    # 🔥 Send notification to followed user
    try:
        notification_data = {
            "recipient_id": str(following_id),
            "sender_id": str(follower_id),
            "type": "follow",
            "title": "Someone followed you",
            "message": "A user started following you",
            "data": {
                "follower_id": str(follower_id),
                "action": "follow"
            }
        }
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/create/",
            json=notification_data,
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print(f"Notification error: {e}")
    
    return Response({"message": "Following"}, status=201)


@csrf_exempt
@api_view(['POST'])
def unfollow_user(request):
    """
    Unfollow a user
    
    Request format (JSON):
    {
        "follower_id": "uuid",
        "following_id": "uuid"
    }
    """
    follower_id = request.data.get('follower_id')
    following_id = request.data.get('following_id')
    
    # Validate
    if not follower_id or not following_id:
        return Response({"error": "follower_id and following_id are required"}, status=400)
    
    try:
        follow = Follow.objects.get(
            follower_id=follower_id,
            following_id=following_id
        )
        follow.delete()
        return Response({"message": "Unfollowed"}, status=200)
    except Follow.DoesNotExist:
        return Response({"error": "Not following this user"}, status=404)
    
def search_users(request):
    if request.method == 'GET':
        # Lấy từ khóa tìm kiếm 'q' từ URL (VD: ?q=hung)
        query = request.GET.get('q', '').strip()
        
        if query:
            # Tìm kiếm không phân biệt hoa thường (icontains)
            # Tìm theo username hoặc email
            users = User.objects.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        else:
            # Nếu không truyền 'q' hoặc 'q' rỗng, có thể trả về mảng rỗng hoặc tất cả
            users = User.objects.none() 

        # Format dữ liệu trả về cho Android
        user_list = []
        for user in users:
            user_list.append({
                "id": str(user.id), # Ép kiểu UUID sang chuỗi
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })

        # safe=False cho phép trả về một mảng JSON (List) thay vì một Object
        return JsonResponse(user_list, safe=False, status=200)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)