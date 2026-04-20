from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import httpx # Dùng để gọi sang User Service lấy Name/Avatar
from .models import Message, UserStatus

# Đổi thành URL của User Service
USER_SERVICE_URL = "http://127.0.0.1:3001/api/users" 

@api_view(['GET'])
def get_inbox(request, user_id):
    """
    API: Lấy danh sách những người đã nhắn tin
    """
    # 1. Tìm tất cả các phòng chat mà user này tham gia
    messages = Message.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    room_ids = messages.values_list('room_id', flat=True).order_by().distinct()

    inbox_list = []
    target_user_ids = []

    # 2. Gom dữ liệu cho từng phòng
    for room in room_ids:
        # Lấy tin nhắn cuối cùng
        last_msg = Message.objects.filter(room_id=room).order_by('-timestamp').first()
        if not last_msg:
            continue

        # Xác định ai là người đối diện
        target_id = last_msg.receiver_id if str(last_msg.sender_id) == str(user_id) else last_msg.sender_id
        target_user_ids.append(str(target_id))

        # Đếm số tin chưa đọc (Người gửi là người kia, và chưa đọc)
        unread_count = Message.objects.filter(
            room_id=room, 
            sender_id=target_id, 
            is_read=False
        ).count()

        # Kiểm tra trạng thái online
        status_obj = UserStatus.objects.filter(user_id=target_id).first()
        is_online = status_obj.is_online if status_obj else False

        inbox_list.append({
            "target_user_id": str(target_id),
            "is_online": is_online,
            "last_message": last_msg.text if last_msg.message_type == 0 else "[Hình ảnh]",
            "last_message_timestamp": last_msg.timestamp.isoformat(),
            "unread_count": unread_count,
            "last_sender_id": str(last_msg.sender_id)
        })

    # 3. GỌI SANG USER SERVICE ĐỂ LẤY TÊN VÀ AVATAR (Microservices Pattern)
    
    for item in inbox_list:
        t_id = item['target_user_id']
        try:
            # Gọi thẳng vào API bạn vừa cung cấp: http://127.0.0.1:3001/api/users/<ID>
            response = httpx.get(f"{USER_SERVICE_URL}/{t_id}/")
            
            if response.status_code == 200:
                user_info = response.json()
                
                # Trích xuất username và avatar_url từ cục JSON bạn vừa gửi
                item['target_user_name'] = user_info.get('username', 'Unknown')
                item['target_avatar_url'] = user_info.get('avatar_url', '') # Map đúng với model Android của bạn
                
        except Exception as e:
            print(f"Lỗi khi gọi User Service cho ID {t_id}:", e)
            item['target_user_name'] = 'Unknown'
            item['target_avatar_url'] = ''

    # Sắp xếp tin nhắn mới nhất lên đầu
    inbox_list.sort(key=lambda x: x['last_message_timestamp'], reverse=True)
    return Response(inbox_list, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_chat_history(request, my_id, target_id):
    """
    API: Lấy toàn bộ tin nhắn giữa 2 người (Message)
    """
    # Sinh ra room_id giống thuật toán trong WebSocket
    users = sorted([str(my_id), str(target_id)])
    room_name = f"chat_{users[0]}_{users[1]}"

    # Đánh dấu toàn bộ tin nhắn của người kia gửi cho mình là "Đã đọc"
    Message.objects.filter(room_id=room_name, sender_id=target_id, is_read=False).update(is_read=True)

    messages = Message.objects.filter(room_id=room_name)
    
    data = []
    for msg in messages:
        data.append({
            "id": str(msg.id),
            "senderId": str(msg.sender_id),
            "text": msg.text,
            "imageUrl": msg.image_url,
            "type": msg.message_type,
            "timestamp": int(msg.timestamp.timestamp() * 1000) # Đổi ra milliseconds cho Android
        })

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_online_status(request):
    """
    API: Cập nhật trạng thái online/offline (Android gọi ở onResume/onPause)
    """
    user_id = request.data.get('user_id')
    is_online = request.data.get('is_online', False)

    if not user_id:
        return Response({"error": "Thiếu user_id"}, status=status.HTTP_400_BAD_REQUEST)

    UserStatus.objects.update_or_create(
        user_id=user_id,
        defaults={'is_online': is_online}
    )

    return Response({"message": "Đã cập nhật trạng thái"}, status=status.HTTP_200_OK)