import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")

url = "https://business-api.tiktok.com/open_api/v1.3/campaign/get/"
headers = {"Access-Token": access_token}
params = {
    "advertiser_id": advertiser_id,
    "page_size": 100
}
res = requests.get(url, headers=headers, params=params)
camps = res.json().get("data", {}).get("list", [])
camps.sort(key=lambda x: x.get("modify_time", ""), reverse=True)

for c in camps[:10]:
    print(c["campaign_name"], c["operation_status"], c["objective_type"], c["modify_time"])
