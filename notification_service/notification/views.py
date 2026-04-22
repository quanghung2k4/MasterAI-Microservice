from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification
from .serializers import NotificationSerializer


# CREATE + REALTIME
@api_view(['POST'])
def create_notification(request):
    serializer = NotificationSerializer(data=request.data)

    if serializer.is_valid():
        notification = serializer.save()

        # gửi realtime
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{notification.recipient_id}",
            {
                "type": "send_notification",
                "data": NotificationSerializer(notification).data
            }
        )

        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


# 📄 GET
@api_view(['GET'])
def get_notifications(request):
    user_id = request.GET.get('user_id')

    data = Notification.objects.filter(
        recipient_id=user_id
    ).order_by('-created_at')[:20]

    return Response(NotificationSerializer(data, many=True).data)


# MARK AS READ
@api_view(['PUT', 'PATCH'])
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=404)
    
    notification.is_read = True
    notification.save()
    
    return Response(NotificationSerializer(notification).data, status=200)