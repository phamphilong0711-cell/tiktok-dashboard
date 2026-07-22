import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")

url = "https://business-api.tiktok.com/open_api/v1.3/tt_shop/get/"
headers = {"Access-Token": access_token}
params = {
    "advertiser_id": advertiser_id
}
res = requests.get(url, headers=headers, params=params)
print("Shops:", res.json())
