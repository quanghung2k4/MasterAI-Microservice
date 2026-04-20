from django.urls import path
from . import views

urlpatterns = [
    # Cập nhật trạng thái
    path('status/', views.update_online_status),
    
    # Lấy danh sách Inbox (truyền ID của người đang đăng nhập)
    path('inbox/<uuid:user_id>/', views.get_inbox),
    
    # Lấy lịch sử chat giữa 2 người
    path('history/<uuid:my_id>/<uuid:target_id>/', views.get_chat_history),
]