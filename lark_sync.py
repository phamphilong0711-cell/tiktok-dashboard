import os
import requests
import datetime
from dotenv import load_dotenv
import database

# Load môi trường
load_dotenv("config.env")

def excel_date_to_datetime(excel_date):
    """Chuyển đổi số serial của Excel/Lark thành YYYY-MM-DD"""
    try:
        dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(excel_date))
        return dt.strftime('%Y-%m-%d')
    except:
        return None

def sync_lark_revenue():
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    spreadsheet_token = os.getenv("LARK_SPREADSHEET_TOKEN")
    sheet_id = os.getenv("LARK_SHEET_ID")
    
    if not all([app_id, app_secret, spreadsheet_token, sheet_id]):
        print("Lỗi: Thiếu cấu hình Lark API trong config.env")
        return False
        
    print("Đang kết nối Lark API lấy Token...")
    # 1. Lấy Token
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    response = requests.post(url, json=payload)
    data = response.json()
    if data.get("code") != 0:
        print("Lỗi lấy Lark Token:", data)
        return False
        
    token = data["tenant_access_token"]
    
    # 2. Lấy dữ liệu từ A10 đến AZ500
    print("Đang tải dữ liệu Báo Cáo Hàng Ngày...")
    sheet_url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}!A10:AZ500"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    resp = requests.get(sheet_url, headers=headers)
    sheet_data = resp.json()
    if sheet_data.get("code") != 0:
        print("Lỗi lấy dữ liệu Lark:", sheet_data)
        return False
        
    values = sheet_data.get("data", {}).get("valueRange", {}).get("values", [])
    all_metrics = []
    all_costs = []
    
    for row in values:
        if not row or not row[0]:
            continue
            
        date_val = excel_date_to_datetime(row[0])
        if not date_val:
            continue
            
        def safe_float(idx):
            if len(row) > idx and row[idx]:
                val = str(row[idx]).replace(',', '').replace(' ', '')
                try: 
                    if '+' in val:
                        return sum(float(x) for x in val.split('+') if x)
                    return float(val)
                except: 
                    return 0.0
            return 0.0
            
        def safe_int(idx):
            if len(row) > idx and row[idx]:
                try: return int(float(row[idx]))
                except: return 0
            return 0

        # Cấu hình map cột (Index: Tên Seller, Tên Source)
        # Nguồn gốc: Cột 2 (Shopee Dr), Cột 3 (Shopee 30Shine), Cột 4 (Shopee GL), Cột 5 (Tiktok), Cột 6 (Lazada), Cột 7 (Facebook)
        # Nguồn đơn: Cột 11 (Shopee Dr), Cột 12 (Shopee 30Shine), Cột 13 (Shopee GL), Cột 14 (Tiktok), Cột 15 (Lazada), Cột 16 (Facebook)
        mapping = [
            {"rev_idx": 2, "ord_idx": 11, "seller": "Shopee Dr", "source": "Shopee"},
            {"rev_idx": 3, "ord_idx": 12, "seller": "Shopee 30Shine", "source": "Shopee"},
            {"rev_idx": 4, "ord_idx": 13, "seller": "Shopee GL", "source": "Shopee"},
            {"rev_idx": 5, "ord_idx": 14, "seller": "Tiktok 30S", "source": "TikTok"},
            {"rev_idx": 6, "ord_idx": 15, "seller": "Lazada", "source": "Lazada"},
            {"rev_idx": 7, "ord_idx": 16, "seller": "Facebook", "source": "Facebook"},
        ]
        
        for m in mapping:
            rev = safe_float(m["rev_idx"])
            orders = safe_int(m["ord_idx"])
            
            if rev > 0 or orders > 0:
                aov = rev / orders if orders > 0 else 0
                
                all_metrics.append({
                    'date': date_val,
                    'source': m["source"],
                    'seller': m["seller"],
                    'revenue': rev,
                    'orders': orders,
                    'aov': aov,
                    'upsell': 0,
                    'final_revenue': rev
                })
                
        # Xử lý Chi phí (Ads Spend)
        shopee_cost = safe_float(27) + safe_float(28) + safe_float(29)
        tiktok_cost = safe_float(30)
        lazada_cost = safe_float(31)
        
        if shopee_cost > 0:
            all_costs.append({"date": date_val, "platform": "Shopee", "campaign": "Shopee (Lark)", "spend": shopee_cost})
        if tiktok_cost > 0:
            all_costs.append({"date": date_val, "platform": "TikTok Ads", "campaign": "TikTok (Lark)", "spend": tiktok_cost})
        if lazada_cost > 0:
            all_costs.append({"date": date_val, "platform": "Lazada", "campaign": "Lazada (Lark)", "spend": lazada_cost})
            
        # Xử lý Chi phí khác
        ttlk_shopee = safe_float(32)
        ttlk_tiktok = safe_float(33)
        booking = safe_float(34)
        media_mkt = safe_float(35)
        
        if ttlk_shopee > 0:
            all_costs.append({"date": date_val, "platform": "Khác - TTLK Shopee", "campaign": "TTLK Shopee", "spend": ttlk_shopee})
        if ttlk_tiktok > 0:
            all_costs.append({"date": date_val, "platform": "Khác - TTLK Tiktok", "campaign": "TTLK Tiktok", "spend": ttlk_tiktok})
        if booking > 0:
            all_costs.append({"date": date_val, "platform": "Khác - Booking", "campaign": "Booking", "spend": booking})
        if media_mkt > 0:
            all_costs.append({"date": date_val, "platform": "Khác - Media MKT", "campaign": "Media MKT", "spend": media_mkt})
                
    if all_metrics:
        database.save_daily_metrics(all_metrics)
        print(f"Đã lưu thành công {len(all_metrics)} bản ghi Doanh thu từ Lark API!")
        
    if all_costs:
        database.save_ads_spend(all_costs)
        print(f"Đã lưu thành công {len(all_costs)} bản ghi Chi phí từ Lark API!")
        
    if all_metrics or all_costs:
        return True
    else:
        print("Không tìm thấy dữ liệu hợp lệ trong file Lark.")
        return False

if __name__ == "__main__":
    sync_lark_revenue()
