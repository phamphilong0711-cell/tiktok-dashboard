import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")

url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
headers = {"Access-Token": access_token}

params = {
    "advertiser_id": advertiser_id,
    "report_type": "TT_SHOP", 
    "data_level": "AUCTION_ADVERTISER",
    "dimensions": json.dumps(["stat_time_day"]),
    "metrics": json.dumps(["spend"]),
    "start_date": "2026-07-15",
    "end_date": "2026-07-22",
    "page_size": 1000
}
res = requests.get(url, headers=headers, params=params)
print("TT_SHOP dimensions: stat_time_day:", res.json())

params_nodim = {
    "advertiser_id": advertiser_id,
    "report_type": "TT_SHOP", 
    "data_level": "AUCTION_ADVERTISER",
    "metrics": json.dumps(["spend"]),
    "start_date": "2026-07-15",
    "end_date": "2026-07-22",
    "page_size": 1000
}
res_nodim = requests.get(url, headers=headers, params=params_nodim)
print("TT_SHOP no dimensions:", res_nodim.json())

