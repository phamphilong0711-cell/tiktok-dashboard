import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("config.env")
access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
app_id = "7664524398862303248" # User's app id
secret = "8eba2da7fe7296247df0681980d4af5f4c49d1bc" # User's secret

url = "https://business-api.tiktok.com/open_api/v1.3/oauth2/advertiser/get/"
headers = {"Access-Token": access_token}
params = {"app_id": app_id, "secret": secret}
res = requests.get(url, headers=headers, params=params)
print(res.json())
