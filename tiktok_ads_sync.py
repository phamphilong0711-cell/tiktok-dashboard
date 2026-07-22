import os
import requests
import json
import datetime
from dotenv import load_dotenv
import database

# Đọc cấu hình từ file config.env
load_dotenv('config.env')

TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_ADVERTISER_ID = os.getenv("TIKTOK_ADVERTISER_ID")

def sync_tiktok_ads_spend(start_date: str, end_date: str):
    """
    Kéo chi phí từ TikTok Ads (Marketing API v1.3).
    start_date, end_date có định dạng YYYY-MM-DD
    """
    print(f"\n--- ĐỒNG BỘ CHI PHÍ TIKTOK ADS ({start_date} đến {end_date}) ---")
    
    if not TIKTOK_ACCESS_TOKEN or not TIKTOK_ADVERTISER_ID:
        print("Lỗi: Thiếu TIKTOK_ACCESS_TOKEN hoặc TIKTOK_ADVERTISER_ID trong config.env")
        return False
        
    url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
    headers = {
        "Access-Token": TIKTOK_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    params = {
        "advertiser_id": TIKTOK_ADVERTISER_ID,
        "report_type": "BASIC",
        "data_level": "AUCTION_ADVERTISER",
        "dimensions": json.dumps(["stat_time_day"]),
        "metrics": json.dumps(["spend"]),
        "start_date": start_date,
        "end_date": end_date,
        "page_size": 1000
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if data.get("code") != 0:
            print(f"Lỗi API TikTok Ads: {data.get('message')}")
            return False
            
        daily_spend = {}
        total_fetched = 0
        
        # Parse data
        records = data.get("data", {}).get("list", [])
        for item in records:
            date_start = item.get("dimensions", {}).get("stat_time_day")
            spend_str = item.get("metrics", {}).get("spend", "0")
            
            try:
                spend = float(spend_str)
            except ValueError:
                spend = 0
                
            # Convert YYYY-MM-DD HH:MM:SS format to YYYY-MM-DD if needed
            if date_start and " " in date_start:
                date_start = date_start.split(" ")[0]
                
            if spend > 0 and date_start:
                print(f"  - {date_start} | Chi phí: {spend:,.0f} đ")
                if date_start not in daily_spend:
                    daily_spend[date_start] = 0
                daily_spend[date_start] += spend
                total_fetched += spend
                
        print(f"--- Tổng chi phí TikTok Ads kéo được: {total_fetched:,.0f} đ ---")
        
        spend_records = []
        for date_str, spend in daily_spend.items():
            if spend > 0:
                spend_records.append({
                    "date": date_str,
                    "platform": "TikTok Ads",
                    "campaign": "Tổng hợp TikTok Ads",
                    "spend": spend
                })
                
        if spend_records:
            database.save_ads_spend(spend_records)
            print("Đã lưu thành công chi phí TikTok Ads vào CSDL!")
            
        return True

    except Exception as e:
        print(f"Lỗi kết nối TikTok Ads: {e}")
        return False

if __name__ == "__main__":
    # Test tự động kéo 14 ngày qua
    end_dt = datetime.datetime.now()
    start_dt = end_dt - datetime.timedelta(days=14)
    sync_tiktok_ads_spend(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
