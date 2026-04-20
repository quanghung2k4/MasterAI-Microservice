from django.urls import path
from .views import (
    create_post,
    get_feed,
    toggle_like,
    get_comments,
    add_comment,
    update_post,
    delete_post,
    get_user_post_count,
    get_user_posts
)

urlpatterns = [
    path('', create_post, name='create_post'),
    path('feed/', get_feed, name='get_feed'),
    path('<uuid:post_id>/like/', toggle_like, name='toggle_like'),
    path('<uuid:post_id>/comments/', get_comments, name='get_comments'),
    path('<uuid:post_id>/comment/', add_comment, name='add_comment'),
    path('<uuid:post_id>/update/', update_post, name='update_post'),
    path('<uuid:post_id>/', delete_post, name='delete_post'),
    path('count/<uuid:user_id>/', get_user_post_count, name='post-count'),
    
    path('user/<uuid:user_id>/', get_user_posts, name='get_user_posts'),
]
