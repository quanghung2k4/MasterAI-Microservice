from .views import get_all_users, get_user_by_id
from django.urls import path

from .views import (
    get_all_users,
    get_user_by_id,
    register,
    login,
    logout,
)

urlpatterns = [
    # 🔥 AUTH
    path('register/', register),
    path('login/', login),
    path('logout/', logout),

    # 👤 USERS
    path('', get_all_users),
    path('<uuid:user_id>/', get_user_by_id),

]