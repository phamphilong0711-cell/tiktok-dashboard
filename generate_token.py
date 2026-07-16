import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv("config.env")

def get_refresh_token():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Lỗi: Không tìm thấy Client ID hoặc Client Secret trong config.env")
        return
        
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }
    
    scopes = ["https://www.googleapis.com/auth/adwords"]
    
    print("Đang khởi tạo Local Server để xác thực OAuth...")
    flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes)
    
    # Chạy server ở port 8080 và chờ user click vào link
    credentials = flow.run_local_server(port=8080, open_browser=False)
    
    print("\n" + "="*50)
    print("ỦY QUYỀN THÀNH CÔNG!")
    print("Đây là Refresh Token mới của bạn:")
    print("-" * 50)
    print(credentials.refresh_token)
    print("-" * 50)
    
    with open("refresh_token.txt", "w") as f:
        f.write(credentials.refresh_token)
        
    print("Đã lưu token vào file refresh_token.txt")
    print("="*50 + "\n")

if __name__ == "__main__":
    get_refresh_token()
