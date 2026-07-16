import os
import requests
import datetime
from dotenv import load_dotenv
import database
import json

# Load môi trường
load_dotenv("config.env")

def sync_facebook_ads_spend(start_date: str, end_date: str):
    """
    Kéo chi phí Facebook Ads từ start_date đến end_date
    Định dạng: YYYY-MM-DD
    """
    access_token = os.getenv("FB_ACCESS_TOKEN")
    ad_account_id = os.getenv("FB_AD_ACCOUNT_ID")
    
    if not access_token or not ad_account_id:
        print("Lỗi: Chưa cấu hình FB_ACCESS_TOKEN hoặc FB_AD_ACCOUNT_ID")
        return False
        
    url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
    
    params = {
        "access_token": access_token,
        "level": "campaign",
        "fields": "campaign_name,spend",
        "time_range": json.dumps({"since": start_date, "until": end_date}),
        "time_increment": 1, # Lấy theo từng ngày
        "limit": 1000
    }
    
    print(f"Đang kéo dữ liệu Facebook Ads từ {start_date} đến {end_date}...")
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"Lỗi API Facebook: {data['error']['message']}")
            return False
            
        daily_spend = {}
        total_fetched = 0
        
        for item in data.get("data", []):
            date_start = item.get("date_start")
            spend = float(item.get("spend", 0))
            campaign_name = item.get("campaign_name", "Unknown Campaign")
            
            if spend > 0:
                print(f"  - {date_start} | {campaign_name} | Chi phí: {spend:,.0f} đ")
                if date_start not in daily_spend:
                    daily_spend[date_start] = 0
                daily_spend[date_start] += spend
                total_fetched += spend
                
        print(f"--- Tổng chi phí Facebook Ads kéo được: {total_fetched:,.0f} đ ---")
        
        spend_records = []
        for date_str, spend in daily_spend.items():
            if spend > 0:
                spend_records.append({
                    "date": date_str,
                    "platform": "Facebook Ads",
                    "campaign": "Tổng hợp Facebook Ads",
                    "spend": spend
                })
                
        if spend_records:
            database.save_ads_spend(spend_records)
            print("Đã lưu thành công chi phí Facebook Ads vào CSDL!")
            
        return True

    except Exception as e:
        print(f"Lỗi kết nối Facebook Ads: {e}")
        return False

if __name__ == "__main__":
    # Test tự động kéo 14 ngày qua
    end_dt = datetime.datetime.now()
    start_dt = end_dt - datetime.timedelta(days=14)
    sync_facebook_ads_spend(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
