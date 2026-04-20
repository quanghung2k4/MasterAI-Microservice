from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Nhận 2 param: my_id và target_id
    re_path(r'ws/chat/(?P<my_id>[^/]+)/(?P<target_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]