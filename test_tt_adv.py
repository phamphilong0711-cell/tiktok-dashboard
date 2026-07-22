import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")

url = "https://business-api.tiktok.com/open_api/v1.3/advertiser/info/"
headers = {"Access-Token": access_token}
params = {"advertiser_ids": json.dumps([advertiser_id])}

res = requests.get(url, headers=headers, params=params)
print("Advertiser Info:", res.json())

# Also check lifetime spend or something?
url2 = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
params2 = {
    "advertiser_id": advertiser_id,
    "report_type": "BASIC",
    "data_level": "AUCTION_ADVERTISER",
    "dimensions": json.dumps(["stat_time_day"]),
    "metrics": json.dumps(["spend"]),
    "start_date": "2024-01-01",  # Long time ago
    "end_date": "2026-07-22",
    "page_size": 1000
}
res2 = requests.get(url2, headers=headers, params=params2)
print("Lifetime Spend Data:", res2.json())
