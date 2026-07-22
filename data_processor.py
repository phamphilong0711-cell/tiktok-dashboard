import pandas as pd
import glob
import os
import sqlite3
from datetime import datetime
import database

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'data_uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def parse_date(date_str):
    try:
        # Xử lý các định dạng ngày khác nhau
        if isinstance(date_str, datetime):
            return date_str.strftime('%Y-%m-%d')
        # Thêm các xử lý định dạng khác nếu cần
        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
    except:
        return None

# Đã gỡ bỏ hàm đọc file tblTmdtSource cũ vì đã chuyển sang Lark API

# Hàm xử lý file chi phí thủ công đã bị gỡ bỏ do chuyển sang tự động qua API và Lark
def run_etl():
    print("Bắt đầu xử lý dữ liệu (ETL)...")
    database.init_db()
    
    # 1. Kéo doanh thu và chi phí từ Lark API
    import lark_sync
    print("Bắt đầu kéo dữ liệu (Lark API)...")
    lark_sync.sync_lark_revenue()
    
    # 2. Kéo Chi phí Google Ads tự động qua API (14 ngày gần nhất)
    import google_ads_sync
    import facebook_ads_sync
    from datetime import datetime, timedelta
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=14)
    print("Bắt đầu kéo dữ liệu Google Ads API...")
    google_ads_sync.sync_google_ads_spend(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    
    print("Bắt đầu kéo dữ liệu Facebook Ads API...")
    facebook_ads_sync.sync_facebook_ads_spend(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    
    print("Bắt đầu kéo dữ liệu TikTok Ads API...")
    import tiktok_ads_sync
    tiktok_ads_sync.sync_tiktok_ads_spend(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    
    print("Bắt đầu xuất file tĩnh data.json...")
    import export_json
    export_json.export_to_json()

    print("Hoàn tất ETL!")

if __name__ == "__main__":
    run_etl()
