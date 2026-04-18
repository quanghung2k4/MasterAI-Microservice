from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from .models import User,Follow
import requests
from .serializers import UserSerializer

# Giả sử POST_SERVICE đang chạy ở cổng 3002
POST_SERVICE_URL = "http://localhost:3002/api/posts/count/"

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