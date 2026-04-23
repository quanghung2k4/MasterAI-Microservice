import re
from underthesea import text_normalize

def clean_vietnamese_text(text):
    if not text:
        return ""
    
    # 1. Chuẩn hóa dấu tiếng Việt (ví dụ: hòa và hoà)
    text = text_normalize(text)
    
    # 2. Chuyển về chữ thường
    text = text.lower()
    
    # 3. Xóa các ký tự đặc biệt, icon, link web
    text = re.sub(r'http\S+', '', text) # Xóa link
    text = re.sub(r'[^\w\s]', ' ', text) # Xóa dấu câu, icon
    
    # 4. Xóa khoảng trắng thừa
    text = " ".join(text.split())
    
    return text