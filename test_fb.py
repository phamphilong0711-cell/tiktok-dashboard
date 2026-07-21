import requests
import json
from datetime import datetime, timedelta

def load_env():
    env = {}
    with open('config.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                env[k] = v
    return env

def check_fb():
    env = load_env()
    access_token = env.get("FB_ACCESS_TOKEN")
    ad_account_id = env.get("FB_AD_ACCOUNT_ID")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
    params = {
        "access_token": access_token,
        "level": "campaign",
        "fields": "campaign_name,spend",
        "time_range": json.dumps({"since": start_date, "until": end_date}),
        "time_increment": 1,
        "limit": 1000
    }
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    if "error" in data:
        print("Lỗi FB:", data["error"])
        return
        
    total_spend = 0
    with open('fb_test_out.txt', 'w', encoding='utf-8') as f:
        for item in data.get("data", []):
            d = item.get("date_start")
            s = float(item.get("spend", 0))
            c = item.get("campaign_name")
            if s > 0:
                f.write(f"{d} | {c} | {s}\n")
                total_spend += s
        f.write(f"\nTOTAL SPEND 14 DAYS: {total_spend}\n")
    print(f"Total spend: {total_spend}")

check_fb()
