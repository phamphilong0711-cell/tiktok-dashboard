import app
import json
import requests
from datetime import datetime
import time

start_dt = datetime.strptime("2026-07-01", "%Y-%m-%d").replace(hour=0, minute=0, second=0)
end_dt = datetime.strptime("2026-07-06", "%Y-%m-%d").replace(hour=23, minute=59, second=59)

api_path = "/order/202309/orders/search"
timestamp = str(int(time.time()))

params = {
    "app_key": app.SHOP_APP_KEY,
    "timestamp": timestamp,
    "shop_cipher": app.get_shop_cipher(),
    "page_size": 100
}

all_orders = []
page_token = ""
headers = {
    "x-tts-access-token": app.SHOP_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

loop_count = 0
while True:
    loop_count += 1
    print(f"Loop {loop_count}, page_token: {page_token}")
    body_dict = {
        "page_size": 100, 
        "create_time_ge": int(start_dt.timestamp()),
        "create_time_lt": int(end_dt.timestamp())
    }
    if page_token:
        body_dict["page_token"] = page_token
        
    body_str = json.dumps(body_dict, separators=(',', ':'))
    sign = app.generate_tiktok_shop_sign(app.SHOP_APP_SECRET, api_path, params, body_str)
    
    req_params = params.copy()
    req_params["sign"] = sign
    url = f"https://open-api.tiktokglobalshop.com{api_path}"
    
    res = requests.post(url, headers=headers, params=req_params, data=body_str)
    data = res.json()
    print("Code:", data.get("code"))
    if data.get("code") == 0:
        orders = data.get("data", {}).get("orders", [])
        print(f"Fetched {len(orders)} orders")
        if not orders:
            break
        all_orders.extend(orders)
        
        next_token = data.get("data", {}).get("next_page_token", "")
        if next_token:
            page_token = next_token
        else:
            break
    else:
        print("Error message:", data.get("message"))
        break

print("Total orders fetched:", len(all_orders))
