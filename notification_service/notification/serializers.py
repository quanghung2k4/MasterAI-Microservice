# notification/serializers.py

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient_id', 'type', 'title', 
            'message', 'is_read', 'created_at', 'sender'
        ]

    def get_sender(self, obj):
        # Chuyển các trường phẳng trong DB thành một Object lồng nhau trong JSON
        return {
            "id": obj.sender_id,
            "username": obj.sender_name,
            "avatar": obj.sender_avatar
        }

    def create(self, validated_data):
        # Xử lý khi nhận dữ liệu POST có chứa object 'sender'
        request = self.context.get('request')
        print("====================================")
        print(f"DỮ LIỆU NHẬN ĐƯỢC: {request.data if request else 'No Request'}")
        print("====================================")
        sender_data = request.data.get('sender', {})
        print(f"DEBUG - Sender Data: {sender_data}")
        validated_data['sender_id'] = sender_data.get('id')
        validated_data['sender_name'] = sender_data.get('username')
        validated_data['sender_avatar'] = sender_data.get('avatar')
        return super().create(validated_data)