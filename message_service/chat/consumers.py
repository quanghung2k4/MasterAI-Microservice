import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, UserStatus

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy ID từ URL (Android sẽ truyền lên)
        self.my_id = self.scope['url_route']['kwargs']['my_id']
        self.target_id = self.scope['url_route']['kwargs']['target_id']

        # Thuật toán tạo tên phòng duy nhất cho 2 người
        users = sorted([str(self.my_id), str(self.target_id)])
        self.room_group_name = f"chat_{users[0]}_{users[1]}"

        # Cập nhật DB thành Online
        await self.update_user_status(self.my_id, True)

        # Phát thông báo Online cho người kia trong phòng
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': self.my_id,
                'is_online': True
            }
        )

        # Tham gia phòng
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"[{self.my_id}] đã kết nối vào phòng {self.room_group_name}")

    async def disconnect(self, close_code):
        # Rời phòng
        # Cập nhật DB thành Offline
        await self.update_user_status(self.my_id, False)

        # Phát thông báo Offline cho người kia
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': self.my_id,
                'is_online': False
            }
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"[{self.my_id}] đã ngắt kết nối")

    # Nhận tin nhắn từ Android gửi lên
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        msg_type = data.get('type', 0) # 0 là Text, 1 là Image
        image_url = data.get('image_url', None)

        # Tạo thời gian chuẩn UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # TODO: Sau này bạn gọi model Database để lưu tin nhắn ở đây

        # LƯU VÀO DATABASE BẰNG HÀM ASYNC
        await self.save_message(
            room_id=self.room_group_name,
            sender_id=self.my_id,
            receiver_id=self.target_id,
            text=message,
            image_url=image_url,
            msg_type=msg_type
        )

        # Phát tin nhắn đó cho cả 2 người trong phòng
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',       # SỬA Ở ĐÂY: Trỏ đúng tên hàm
                'message_type': msg_type,
                'message': message,
                'image_url':image_url,
                'sender_id': self.my_id,
                'timestamp': now_utc
            }
        )

    # Hàm gửi ngược tin nhắn về Android
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'message_type': event.get('message_type', 0), # THÊM DÒNG NÀY
            'image_url': event.get('image_url'),          # THÊM DÒNG NÀY
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))
    @database_sync_to_async
    def save_message(self, room_id, sender_id, receiver_id, text, image_url, msg_type):
        Message.objects.create(
            room_id=room_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            text=text,
            image_url=image_url,
            message_type=msg_type
        )
    # Hàm xử lý gửi trạng thái về Android
    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'is_online': event['is_online']
        }))

    # Helper: Cập nhật DB bằng async
    @database_sync_to_async
    def update_user_status(self, user_id, is_online):
        UserStatus.objects.update_or_create(
            user_id=user_id,
            defaults={'is_online': is_online}
        )    