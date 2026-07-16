import app
from datetime import datetime
import json
import requests

start_dt = datetime.strptime("2026-07-01", "%Y-%m-%d").replace(hour=0, minute=0, second=0)
end_dt = datetime.strptime("2026-07-06", "%Y-%m-%d").replace(hour=23, minute=59, second=59)

api_path = "/order/202309/orders/search"
params = {
    "app_key": app.SHOP_APP_KEY,
    "timestamp": str(int(start_dt.timestamp())),
    "shop_cipher": app.get_shop_cipher(),
    "page_size": 100
}

body_dict = {
    "page_size": 100, 
    "create_time_ge": int(start_dt.timestamp()),
    "create_time_lt": int(end_dt.timestamp())
}

body_str = json.dumps(body_dict, separators=(',', ':'))
sign = app.generate_tiktok_shop_sign(app.SHOP_APP_SECRET, api_path, params, body_str)
req_params = params.copy()
req_params["sign"] = sign
url = f"https://open-api.tiktokglobalshop.com{api_path}"
headers = {
    "x-tts-access-token": app.SHOP_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

res = requests.post(url, headers=headers, params=req_params, data=body_str)
data = res.json()
print("Keys in data:", data.get("data", {}).keys())
print("next_page_token:", data.get("data", {}).get("next_page_token"))
print("more:", data.get("data", {}).get("more"))
print("orders length:", len(data.get("data", {}).get("orders", [])))
