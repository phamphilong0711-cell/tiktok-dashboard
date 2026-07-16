import os
import time
import hashlib
import hmac
import json
import requests
from dotenv import load_dotenv

load_dotenv("config.env")

SHOP_APP_KEY = os.getenv("TIKTOK_SHOP_APP_KEY", "")
SHOP_APP_SECRET = os.getenv("TIKTOK_SHOP_APP_SECRET", "")
SHOP_ACCESS_TOKEN = os.getenv("TIKTOK_SHOP_ACCESS_TOKEN", "")

def generate_tiktok_shop_sign(app_secret, api_path, params, body=""):
    sorted_keys = sorted(params.keys())
    param_string = "".join([f"{k}{params[k]}" for k in sorted_keys])
    message = f"{app_secret}{api_path}{param_string}{body}{app_secret}"
    return hmac.new(app_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

print("Token:", SHOP_ACCESS_TOKEN[:10] + "...")

api_path = "/authorization/202309/shops"
params = {"app_key": SHOP_APP_KEY, "timestamp": str(int(time.time()))}
sign = generate_tiktok_shop_sign(SHOP_APP_SECRET, api_path, params, "")
req_params = params.copy()
req_params["sign"] = sign
headers = {"x-tts-access-token": SHOP_ACCESS_TOKEN}
url = f"https://open-api.tiktokglobalshop.com{api_path}"

print("Fetching shops...")
res = requests.get(url, headers=headers, params=req_params)
data = res.json()
print("Shops response:", json.dumps(data, indent=2))

if data.get("code") == 0 and data.get("data", {}).get("shops"):
    shop = data["data"]["shops"][0]
    cipher = shop.get("cipher")
    print("\nUsing cipher:", cipher)
    
    # Try fetching orders
    api_path = "/order/202309/orders/search"
    params = {
        "app_key": SHOP_APP_KEY,
        "timestamp": str(int(time.time())),
        "shop_cipher": cipher,
        "page_size": 100
    }
    body_dict = {
        "page_size": 100,
        "create_time_ge": int(time.time()) - 30*86400,
        "create_time_lt": int(time.time())
    }
    body_str = json.dumps(body_dict, separators=(',', ':'))
    sign = generate_tiktok_shop_sign(SHOP_APP_SECRET, api_path, params, body_str)
    
    req_params = params.copy()
    req_params["sign"] = sign
    headers["Content-Type"] = "application/json"
    url = f"https://open-api.tiktokglobalshop.com{api_path}"
    
    print("\nFetching orders...")
    res = requests.post(url, headers=headers, params=req_params, data=body_str)
    print("Orders response:", json.dumps(res.json(), indent=2))
