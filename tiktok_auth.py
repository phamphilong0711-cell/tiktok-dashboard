import requests
import json
from flask import Flask, request, redirect

# ==========================================
# 1. ĐIỀN THÔNG TIN APP CỦA BẠN VÀO ĐÂY
# ==========================================
APP_ID = 7494588084948339259
SECRET = 066a3871e77d2ee4a1a526d70d5071795b59510a

# Đảm bảo bạn đã thêm URL này vào mục "Redirect URI" trong cài đặt App trên TikTok Developer Portal
REDIRECT_URI = "http://localhost:5001/callback" 

# ==========================================

app = Flask(__name__)

@app.route('/')
def home():
    # Bước 1: Tạo đường link ủy quyền
    auth_url = (
        f"https://ads.tiktok.com/marketing_api/auth?"
        f"app_id={APP_ID}&"
        f"state=your_custom_state&"
        f"redirect_uri={REDIRECT_URI}"
    )
    return f'''
    <h2>Công cụ lấy Access Token TikTok Ads</h2>
    <p>Vui lòng đảm bảo bạn đã cấu hình <b>{REDIRECT_URI}</b> làm Redirect URI trong tài khoản Developer của TikTok.</p>
    <a href="{auth_url}" style="padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px;">Nhấn vào đây để Đăng nhập & Ủy quyền</a>
    '''

@app.route('/callback')
def callback():
    # Bước 2: TikTok gọi lại callback URL kèm theo auth_code
    auth_code = request.args.get('auth_code')
    if not auth_code:
        return "Lỗi: Không nhận được auth_code từ TikTok. Vui lòng thử lại!"
    
    # Bước 3: Đổi auth_code lấy Access Token
    url = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
    payload = {
        "app_id": APP_ID,
        "secret": SECRET,
        "auth_code": auth_code
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("code") == 0:
        access_token = data['data']['access_token']
        advertiser_id = data['data'].get('advertiser_ids', ['Không có'])[0]
        
        # In ra màn hình để copy
        return f'''
        <h2 style="color: green;">Lấy Access Token Thành Công!</h2>
        <p>Hãy copy 2 thông số dưới đây và dán vào file <b>config.env</b> của bạn:</p>
        <div style="background: #f4f4f4; padding: 20px; border-radius: 8px;">
            <p><b>TIKTOK_ACCESS_TOKEN</b> = {access_token}</p>
            <p><b>TIKTOK_ADVERTISER_ID</b> = {advertiser_id}</p>
        </div>
        <p><i>Lưu ý: Đừng chia sẻ token này cho người khác! Có thể tắt tool này đi được rồi.</i></p>
        '''
    else:
        return f"<h3>Lỗi khi đổi token:</h3><pre>{json.dumps(data, indent=4)}</pre>"

if __name__ == '__main__':
    print("=====================================================")
    print("Đang khởi động công cụ lấy Access Token...")
    print(f"1. Hãy đảm bảo bạn đã điền APP_ID và SECRET trong file tiktok_auth.py")
    print(f"2. Vào TikTok Developer Portal, thêm {REDIRECT_URI} vào danh sách Redirect URI.")
    print("3. Truy cập vào link sau trên trình duyệt: http://localhost:5001")
    print("=====================================================\n")
    app.run(port=5001)
