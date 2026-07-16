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
headers = {
    "x-tts-access-token": app.SHOP_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

current_start = int(start_dt.timestamp())
end_time = int(end_dt.timestamp())
loop_count = 0

while current_start < end_time:
    loop_count += 1
    print(f"Loop {loop_count}, current_start: {current_start}")
    body_dict = {
        "page_size": 100, 
        "create_time_ge": current_start,
        "create_time_lt": end_time
    }
        
    body_str = json.dumps(body_dict, separators=(',', ':'))
    sign = app.generate_tiktok_shop_sign(app.SHOP_APP_SECRET, api_path, params, body_str)
    
    req_params = params.copy()
    req_params["sign"] = sign
    url = f"https://open-api.tiktokglobalshop.com{api_path}"
    
    res = requests.post(url, headers=headers, params=req_params, data=body_str)
    data = res.json()
    if data.get("code") == 0:
        orders = data.get("data", {}).get("orders", [])
        print(f"Fetched {len(orders)} orders")
        if not orders:
            break
        all_orders.extend(orders)
        
        if len(orders) < 100:
            break
            
        max_time = max([o.get("create_time", 0) for o in orders])
        if max_time <= current_start:
            current_start += 1
        else:
            current_start = max_time
    else:
        print("Error:", data.get("message"))
        break

# Deduplicate
unique_orders = {o.get("id", ""): o for o in all_orders if o.get("id")}
print(f"Total unique orders fetched: {len(unique_orders)}")
