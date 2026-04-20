from .views import get_all_users, get_user_by_id
from django.urls import path

from .views import (
    get_all_users,
    get_user_by_id,
    register,
    login,
    logout,
    follow_user,
    unfollow_user,
    toggle_follow
)

urlpatterns = [
    #  AUTH
    path('register/', register),
    path('login/', login),
    path('logout/', logout),

    # 👥 FOLLOW/UNFOLLOW
    path('follow/', follow_user),
    path('unfollow/', unfollow_user),

    # 👤 USERS
    #  USERS
    path('', get_all_users),
    path('<uuid:user_id>/', get_user_by_id),
    # FOLLOW (API mới)
    path('<uuid:user_id>/follow/', toggle_follow, name='toggle_follow'),
]