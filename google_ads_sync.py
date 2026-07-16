import os
import datetime
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from dotenv import load_dotenv
import database

# Load môi trường
load_dotenv("config.env")

def get_google_ads_client():
    customer_id = os.getenv("GOOGLE_CUSTOMER_ID").replace("-", "")
    credentials = {
        "developer_token": os.getenv("GOOGLE_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
        "login_customer_id": customer_id,
        "use_proto_plus": True
    }
    return GoogleAdsClient.load_from_dict(credentials)

def get_client_accounts(client, manager_id):
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          customer_client.client_customer,
          customer_client.level,
          customer_client.manager,
          customer_client.descriptive_name,
          customer_client.id
        FROM customer_client
        WHERE customer_client.level <= 1
    """
    client_ids = []
    try:
        response = ga_service.search(customer_id=manager_id, query=query)
        for row in response:
            if not row.customer_client.manager:
                client_ids.append(str(row.customer_client.id))
    except Exception as e:
        print(f"Lỗi khi lấy danh sách tài khoản con: {e}")
    return client_ids

def sync_google_ads_spend(start_date: str, end_date: str):
    """
    Kéo chi phí Google Ads từ start_date đến end_date
    Định dạng: YYYY-MM-DD
    """
    manager_id = os.getenv("GOOGLE_CUSTOMER_ID").replace("-", "")
    
    if not manager_id:
        print("Lỗi: Chưa cấu hình GOOGLE_CUSTOMER_ID")
        return False
        
    client = get_google_ads_client()
    ga_service = client.get_service("GoogleAdsService")
    
    # 4 Chiến dịch mục tiêu
    target_campaigns = [
        "Adsplus_Shopping_cpc",
        "Adsplus_Search_30Shine Shop_ROAS 350",
        "Adsplus_Pmax_all product_ROAS",
        "Adsplus_Pmax_tạo kiểu tóc_tệp mở rộng_all sp"
    ]
    
    campaigns_str = ", ".join([f"'{c}'" for c in target_campaigns])

    query = f"""
        SELECT
            campaign.name,
            segments.date,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND campaign.name IN ({campaigns_str})
    """
    
    print(f"Đang kéo dữ liệu Google Ads từ {start_date} đến {end_date}...")
    
    client_accounts = get_client_accounts(client, manager_id)
    if not client_accounts:
        client_accounts = [manager_id] # Fallback
        
    daily_spend = {}
    total_fetched = 0
    
    for customer_id in client_accounts:
        try:
            response = ga_service.search_stream(customer_id=customer_id, query=query)
            for batch in response:
                for row in batch.results:
                    date_str = row.segments.date
                    cost = row.metrics.cost_micros / 1000000.0
                    
                    if date_str not in daily_spend:
                        daily_spend[date_str] = 0
                    daily_spend[date_str] += cost
                    total_fetched += cost
                    print(f"  - {date_str} | Account {customer_id} | {row.campaign.name} | Chi phí: {cost:,.0f} đ")
        except GoogleAdsException as ex:
            # Bỏ qua lỗi tài khoản con không có quyền hoặc không active
            continue

    # Lưu vào SQLite Database
    print(f"--- Tổng chi phí Google Ads kéo được: {total_fetched:,.0f} đ ---")
    
    spend_records = []
    for date_str, spend in daily_spend.items():
        if spend > 0:
            spend_records.append({
                "date": date_str,
                "platform": "Google Ads",
                "campaign": "Tổng hợp Google Ads",
                "spend": spend
            })
            print(f"Chuẩn bị lưu vào DB: Ngày {date_str} - Chi phí: {spend:,.0f} đ")
            
    if spend_records:
        database.save_ads_spend(spend_records)
        print("Đã lưu thành công vào CSDL!")
            
    return True

if __name__ == "__main__":
    # Test tự động kéo 14 ngày qua
    end_dt = datetime.datetime.now()
    start_dt = end_dt - datetime.timedelta(days=14)
    
    sync_google_ads_spend(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
