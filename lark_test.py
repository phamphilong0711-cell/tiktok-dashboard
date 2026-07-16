import requests
import json

APP_ID = 'cli_aadf09f72bf99eea'
APP_SECRET = 'rI3ImqUlLn3IrhEeo1eF4bN3Hzxrx7cq'
SPREADSHEET_TOKEN = 'JJLNsD2YphLAAatfoe6lNzHNgne'
SHEET_ID = 'XFj6B7'

def test_lark():
    # 1. Lấy Token
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, json=payload)
    data = response.json()
    if data.get("code") != 0:
        print("Lỗi lấy token:", data)
        return
        
    token = data["tenant_access_token"]
    print("Đã lấy token thành công!")
    
    # Lấy dữ liệu
    sheet_url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{SHEET_ID}!A8:AZ15"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    resp = requests.get(sheet_url, headers=headers)
    sheet_data = resp.json()
    if sheet_data.get("code") != 0:
        print("Lỗi lấy dữ liệu:", sheet_data)
        return
        
    values = sheet_data.get("data", {}).get("valueRange", {}).get("values", [])
    print("--- 5 DÒNG ĐẦU TIÊN CỦA FILE LARK ---")
    for idx, row in enumerate(values):
        print(f"Row {idx+1}: {row}")

if __name__ == "__main__":
    test_lark()
