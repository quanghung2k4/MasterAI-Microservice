import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy ID từ URL (Android sẽ truyền lên)
        self.my_id = self.scope['url_route']['kwargs']['my_id']
        self.target_id = self.scope['url_route']['kwargs']['target_id']

        # Thuật toán tạo tên phòng duy nhất cho 2 người
        users = sorted([str(self.my_id), str(self.target_id)])
        self.room_group_name = f"chat_{users[0]}_{users[1]}"

        # Tham gia phòng
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"[{self.my_id}] đã kết nối vào phòng {self.room_group_name}")

    async def disconnect(self, close_code):
        # Rời phòng
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"[{self.my_id}] đã ngắt kết nối")

    # Nhận tin nhắn từ Android gửi lên
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Tạo thời gian chuẩn UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # TODO: Sau này bạn gọi model Database để lưu tin nhắn ở đây

        # Phát tin nhắn đó cho cả 2 người trong phòng
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.my_id,
                'timestamp': now_utc
            }
        )

    # Hàm gửi ngược tin nhắn về Android
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))