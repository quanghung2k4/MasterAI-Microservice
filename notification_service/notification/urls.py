from django.urls import path
from .views import *

urlpatterns = [
    # 🔔 NOTIFICATIONS
    path('', get_notifications),                      # GET all
    path('create/', create_notification),             # POST create
    path('<uuid:notification_id>/read/', mark_as_read),  # mark read
]