import requests
import json
from flask import Flask, request
import os
from dotenv import load_dotenv

# Load sẵn cấu hình từ config.env
load_dotenv("config.env")

# ==========================================
# THÔNG TIN APP CỦA TIKTOK SHOP
# Đảm bảo bạn đã điền vào file config.env
# ==========================================
APP_KEY = os.getenv("TIKTOK_SHOP_APP_KEY", "")
APP_SECRET = os.getenv("TIKTOK_SHOP_APP_SECRET", "")

app = Flask(__name__)

@app.route('/')
def home():
    if not APP_KEY or not APP_SECRET or "điền_" in APP_KEY:
        return "<h2>Lỗi: Bạn chưa điền TIKTOK_SHOP_APP_KEY và TIKTOK_SHOP_APP_SECRET vào file config.env</h2>"

    # Bước 1: Tạo đường link ủy quyền cho TikTok Shop
    # Lưu ý: Có thể cần thay đổi domain tùy thuộc vào khu vực (region), thường dùng services.tiktokshop.com
    auth_url = f"https://services.tiktokshop.com/open/authorize?app_key={APP_KEY}"
    
    return f'''
    <h2>Công cụ lấy Access Token cho TikTok Shop</h2>
    <p>Hãy đảm bảo bạn đã cấu hình Redirect URI của ứng dụng TikTok Shop (trong Partner Center) về địa chỉ: <b>http://localhost:5002/callback</b></p>
    <a href="{auth_url}" target="_blank" style="padding: 10px 20px; background: #000; color: white; text-decoration: none; border-radius: 5px;">Nhấn vào đây để Cấp Quyền TikTok Shop</a>
    '''

@app.route('/callback')
def callback():
    # Bước 2: Bắt auth_code (hoặc code) từ TikTok Shop
    auth_code = request.args.get('code') or request.args.get('auth_code')
    if not auth_code:
        return "Lỗi: Không nhận được mã code từ TikTok Shop. Vui lòng thử lại!"
    
    # Bước 3: Đổi auth_code lấy Access Token
    url = "https://auth.tiktok-shops.com/api/v2/token/get"
    params = {
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "auth_code": auth_code,
        "grant_type": "authorized_code"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("code") == 0 and "data" in data:
        access_token = data['data'].get('access_token')
        
        return f'''
        <h2 style="color: green;">Lấy Access Token của SHOP Thành Công!</h2>
        <p>Hãy copy đoạn mã dưới đây và dán vào dòng <b>TIKTOK_SHOP_ACCESS_TOKEN</b> trong file <b>config.env</b> của bạn:</p>
        <div style="background: #f4f4f4; padding: 20px; border-radius: 8px; word-break: break-all;">
            <p>{access_token}</p>
        </div>
        <p><i>Lưu ý: Đừng chia sẻ token này cho người khác!</i></p>
        '''
    else:
        return f"<h3>Lỗi khi đổi token TikTok Shop:</h3><pre>{json.dumps(data, indent=4)}</pre>"

if __name__ == '__main__':
    print("=====================================================")
    print("Đang khởi động công cụ lấy Access Token TIKTOK SHOP...")
    print("Truy cập vào link sau trên trình duyệt: http://localhost:5002")
    print("=====================================================\n")
    # Chạy ở port 5002 để không trùng với port 5001 của Ads
    app.run(port=5002)
