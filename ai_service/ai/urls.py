from django.urls import path
from . import views

urlpatterns = [
    # --- Nhóm 1: Các tính năng Sinh nội dung (POST) ---
    path('generate-image/', views.generate_image_api, name='generate_image'),
    path('enhance-prompt/', views.enhance_image_prompt, name='enhance-prompt'),
    path('add-asset/', views.add_asset_api, name='add_asset'),

    # --- Nhóm 2: Các tính năng Lấy dữ liệu (GET) ---
    path('generations/', views.get_generations_api, name='get_generations'),
    path('assets/', views.get_assets_api, name='get_assets'),
]