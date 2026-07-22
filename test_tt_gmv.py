import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")
store_id = os.getenv("TIKTOK_SHOP_ID")

url = "https://business-api.tiktok.com/open_api/v1.3/gmv_max/report/get/"
headers = {"Access-Token": access_token}
params = {
    "advertiser_id": advertiser_id,
    "store_ids": json.dumps([store_id]),
    "dimensions": json.dumps(["campaign_id"]),
    "metrics": json.dumps(["cost"]),
    "start_date": "2026-07-08",
    "end_date": "2026-07-22",
    "page_size": 1000
}
res = requests.get(url, headers=headers, params=params)
print("GMV Max Report:", res.json())
