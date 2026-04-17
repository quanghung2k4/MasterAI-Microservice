from django.shortcuts import render

# ai_service/views.py
import os
import io
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types
from .models import AIGeneration
from django.core.files.base import ContentFile
import uuid
from django.conf import settings
from django.views.decorators.http import require_POST


# Import thư viện Cloudinary
import cloudinary
import cloudinary.uploader

# Cấu hình Cloudinary (Khuyến nghị để trong settings.py, nhưng khởi tạo ở đây để bạn dễ hình dung)
cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_API_SECRET'),
  secure = True
)

# Tốt nhất bạn nên lưu API Key trong biến môi trường (Environment Variables)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

@csrf_exempt
def generate_image_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Chỉ chấp nhận phương thức POST'}, status=405)

    # 1. Lấy dữ liệu từ Request
    user_id = request.POST.get('user_id')
    prompt = request.POST.get('prompt', '')
    aspect_ratio = request.POST.get('aspect_ratio', '1:1') # Hỗ trợ: "1:1", "9:16", "16:9", "3:4", "4:3"
    resolution = request.POST.get('resolution', '1K')      # "1K" hoặc "2K"
    uploaded_image = request.FILES.get('image', None)      # File ảnh tùy chọn

    if not prompt:
        return JsonResponse({'error': 'Thiếu tham số bắt buộc: prompt'}, status=400)
    gen_type = 'avatar' if uploaded_image else 'image'
    new_gen = AIGeneration.objects.create(
        user_id=user_id, # Đã thêm
        generation_type=gen_type,
        prompt="prompt", 
        media_url="https://res.cloudinary.com/dldcklb9x/image/upload/v1776360281/image/dz2dfsy1arhy7ny45ccf.png",
        aspect_ratio=aspect_ratio,
        resolution_config=resolution
    )
    return JsonResponse({
                    'generation_id':new_gen.id,
                    'success': True,
                    'message': 'Sinh ảnh thành công',
                    'media_url': new_gen.media_url,
                    'aspect_ratio': aspect_ratio,
                    'resolution_config': resolution
                })

    if uploaded_image:
        # Xây dựng chỉ thị nền tảng (Base Instruction) yêu cầu AI giữ nguyên đối tượng
        base_instruction = (
            "Create a highly detailed avatar portrait. "
            "CRITICAL INSTRUCTION: You MUST strictly preserve the core identity, facial features, "
            "and main subjects from the attached reference image. Do not change the person's basic likeness. "
        )
        # Ghép chỉ thị nền tảng với ý tưởng tùy chỉnh của người dùng
        final_prompt = f"{base_instruction} Apply the following style and concept: {prompt}."
    # 2. Khởi tạo Client và gọi Gemini API

    # Logic xử lý độ phân giải:
    final_prompt = prompt
    if resolution == '2K':
         final_prompt += ", highly detailed, 2K resolution, ultra-crisp"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        # 2. Xây dựng mảng contents (Chìa khóa để dùng Nano Banana)
        # Bắt đầu với câu lệnh prompt bằng chữ
        contents = [final_prompt]

        # Nếu có ảnh tải lên, biến nó thành Part để đẩy vào mảng contents
        if uploaded_image:
            img_bytes = uploaded_image.read()
            image_part = types.Part.from_bytes(
                data=img_bytes,
                mime_type=uploaded_image.content_type or 'image/jpeg'
            )
            contents.append(image_part)

        # 3. Gọi API bằng generate_content với mô hình sinh ảnh Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash-image', # Mô hình Nano Banana tối ưu cho tốc độ
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"], # Ép model trả về kết quả là ảnh (thay vì chữ)
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio
                )
            )
        )

        # 4. Trích xuất và Upload ảnh lên Cloudinary
        # Kết quả từ generate_content được gói trong candidates
        if response.candidates and response.candidates[0].content.parts:
            image_data = None
            
            # Quét qua các phần tử trả về để tìm dữ liệu ảnh
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    break
            
            if image_data:
                file_stream = io.BytesIO(image_data)

                # Gọi hàm upload của Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file_stream, 
                    folder="image", # Phân loại thư mục trên Cloudinary cho gọn
                    resource_type="image"          # Định dạng tài nguyên
                )
                new_gen = AIGeneration.objects.create(
                    user_id=user_id, 
                    generation_type=gen_type,
                    prompt=final_prompt, 
                    media_url=secure_url,
                    aspect_ratio=aspect_ratio,
                    resolution_config=resolution
                )
                return JsonResponse({
                    'generation_id':new_gen.id,
                    'success': True,
                    'message': 'Sinh ảnh thành công',
                    'media_url': upload_result.get("secure_url"),
                    'aspect_ratio': aspect_ratio,
                    'resolution_config': resolution
                })
        else:
            return JsonResponse({'error': 'Không có ảnh nào được sinh ra từ API'}, status=500)

    except Exception as e:
        return JsonResponse({'error': f'Lỗi từ hệ thống AI: {str(e)}'}, status=500)
    

# Lấy API Key từ biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

@csrf_exempt
def enhance_image_prompt(request):
    if request.method == "POST":
        try:
            user_prompt = request.POST.get("prompt")
            if not user_prompt:
                return JsonResponse({"error": "Vui lòng cung cấp 'prompt' trong payload."}, status=400)
            
            if not GEMINI_API_KEY:
                return JsonResponse({"error": "Chưa cấu hình GEMINI_API_KEY."}, status=500)

            # Khởi tạo Client theo tiêu chuẩn mới
            client = genai.Client(api_key=GEMINI_API_KEY)

            instructions = (
                "Bạn là một chuyên gia Prompt Engineering cho các AI tạo ảnh như Midjourney, DALL-E. "
                "Hãy nâng cấp ý tưởng ban đầu của người dùng thành một prompt bằng Tiếng Việt vừa đủ để prompt ảnh, không quá 40 từ"
                "Bổ sung các yếu tố: phong cách nghệ thuật, ánh sáng, góc máy, màu sắc"
                "Chỉ trả về nội dung prompt đã được nâng cấp, tuyệt đối không giải thích thêm.\n\n"
                f"Ý tưởng ban đầu: '{user_prompt}'"
            )

            # Gọi API qua client.models (Sử dụng gemini-2.0-flash hoặc 1.5-flash)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=instructions,
            )

            return JsonResponse({
                "status": "success",
                "original_prompt": user_prompt,
                "enhanced_prompt": response.text.strip()
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Dữ liệu JSON gửi lên không hợp lệ."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Lỗi gọi API: {str(e)}"}, status=500)

    return JsonResponse({"error": "Method Not Allowed."}, status=405)

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import AIGeneration, UserAsset

# ==========================================
# 1. API LẤY LỊCH SỬ (CÓ PHÂN TRANG)
# ==========================================
@require_GET
def get_generations_api(request):
    try:
        user_id = request.GET.get('user_id')
        gen_type = request.GET.get('type', None) # Ví dụ: 'avatar', 'image'
        
        # Ép kiểu an toàn cho phân trang
        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('limit', 10))

        if not user_id:
            return JsonResponse({"success": False, "error": "Thiếu user_id để xác thực"}, status=401)

        # Truy vấn lịch sử của user đó
        queryset = AIGeneration.objects.filter(user_id=user_id)
        if gen_type:
            queryset = queryset.filter(generation_type=gen_type)

        # Cắt trang
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)

        data = []
        for item in page_obj:
            data.append({
                "id": str(item.id),
                "type": item.generation_type,
                "prompt": item.prompt,
                "media_url": item.media_url,
                "aspect_ratio": item.aspect_ratio,
                "resolution": item.resolution_config,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({
            "success": True,
            "data": data,
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous()
            }
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)



@require_GET
def get_assets_api(request):
    try:
        user_id = request.GET.get('user_id')
        asset_type = request.GET.get('type', None)

        if not user_id:
            return JsonResponse({"success": False, "error": "Thiếu user_id để xác thực"}, status=401)

        # Truy vấn toàn bộ tài sản của user đó
        queryset = UserAsset.objects.filter(user_id=user_id)
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)

        # Quét toàn bộ queryset, KHÔNG dùng Paginator
        data = []
        for item in queryset:
            data.append({
                "id": str(item.id),
                "type": item.asset_type,
                "media_url": item.media_url,
                "prompt": item.prompt,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # Trả về toàn bộ mảng data và đính kèm tổng số lượng (rất hữu ích cho giao diện)
        return JsonResponse({
            "success": True,
            "data": data,
            "total_items": queryset.count() # Dùng con số này để hiển thị cái Badge (ví dụ số 8) trên UI
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def add_asset_api(request):
    """API lưu một bản ghi từ lịch sử vào danh sách Assets yêu thích"""
    try:
        # 1. Lấy dữ liệu từ Body (Hỗ trợ cả Form-data và JSON)
        user_id = request.POST.get('user_id')
        generation_id = request.POST.get('generation_id')

        if not user_id or not generation_id:
            return JsonResponse({"success": False, "error": "Thiếu user_id hoặc generation_id"}, status=400)

        # 2. Kiểm tra xem bản ghi gốc có tồn tại không
        try:
            source_gen = AIGeneration.objects.get(id=generation_id)
        except AIGeneration.DoesNotExist:
            return JsonResponse({"success": False, "error": "Không tìm thấy bản ghi gốc trong lịch sử"}, status=404)

        # 3. Kiểm tra xem đã tồn tại trong Asset chưa (tránh lưu trùng)
        exists = UserAsset.objects.filter(user_id=user_id, generation_id=source_gen.id).exists()
        if exists:
            return JsonResponse({"success": True, "message": "Đã tồn tại trong tài nguyên"})

        # 4. Tạo bản ghi mới trong UserAsset
        new_asset = UserAsset.objects.create(
            user_id=user_id,
            generation=source_gen,
            asset_type=source_gen.generation_type,
            media_url=source_gen.media_url,
            prompt=source_gen.prompt
        )

        return JsonResponse({
            "success": True, 
            "message": "Đã thêm vào tài nguyên của bạn",
            "asset_id": str(new_asset.id)
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)