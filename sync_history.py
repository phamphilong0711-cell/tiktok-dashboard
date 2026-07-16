import app
import database
from datetime import datetime, timedelta
import json
import requests
import time

def sync_chunk(start_time, end_time):
    api_path = "/order/202309/orders/search"
    timestamp = str(int(time.time()))
    
    params = {
        "app_key": app.SHOP_APP_KEY,
        "timestamp": timestamp,
        "shop_cipher": app.get_shop_cipher(),
        "page_size": 100
    }
    
    headers = {
        "x-tts-access-token": app.SHOP_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    current_start = int(start_time)
    end_time_int = int(end_time)
    all_orders = []
    
    while current_start < end_time_int:
        body_dict = {
            "page_size": 100, 
            "create_time_ge": current_start,
            "create_time_lt": end_time_int
        }
            
        body_str = json.dumps(body_dict, separators=(',', ':'))
        sign = app.generate_tiktok_shop_sign(app.SHOP_APP_SECRET, api_path, params, body_str)
        
        req_params = params.copy()
        req_params["sign"] = sign
        url = f"https://open-api.tiktokglobalshop.com{api_path}"
        
        try:
            res = requests.post(url, headers=headers, params=req_params, data=body_str)
            data = res.json()
            if data.get("code") == 0:
                orders = data.get("data", {}).get("orders", [])
                if not orders:
                    break
                all_orders.extend(orders)
                
                if len(orders) < 100:
                    break
                    
                max_time = max([o.get("create_time", 0) for o in orders])
                if max_time <= current_start:
                    current_start += 1
                else:
                    current_start = max_time
            else:
                print("API Error:", data.get("message"))
                break
        except Exception as e:
            print("Request Exception:", e)
            break
            
    # Lọc trùng lặp
    unique_orders = {o.get("id", ""): o for o in all_orders if o.get("id")}
    return list(unique_orders.values())

def sync_historical_data():
    database.init_db()
    
    # Từ 01/01/2026 đến 30/06/2026
    start_dt = datetime.strptime("2026-01-01", "%Y-%m-%d").replace(hour=0, minute=0, second=0)
    final_end_dt = datetime.strptime("2026-06-30", "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    
    # Để tránh timeout hoặc payload quá lớn, chia nhỏ mỗi lần quét 30 ngày
    current_chunk_start = start_dt
    total_synced = 0
    
    print("BẮT ĐẦU ĐỒNG BỘ DỮ LIỆU LỊCH SỬ (01/01/2026 - 30/06/2026)")
    print("-" * 50)
    
    while current_chunk_start < final_end_dt:
        current_chunk_end = current_chunk_start + timedelta(days=30)
        if current_chunk_end > final_end_dt:
            current_chunk_end = final_end_dt
            
        print(f"Đang quét từ {current_chunk_start.strftime('%d/%m/%Y')} đến {current_chunk_end.strftime('%d/%m/%Y')}...")
        
        orders = sync_chunk(current_chunk_start.timestamp(), current_chunk_end.timestamp())
        if orders:
            database.save_orders_to_db(orders)
            total_synced += len(orders)
            print(f" -> Đã lưu {len(orders)} đơn hàng.")
        else:
            print(" -> Không có đơn hàng nào.")
            
        current_chunk_start = current_chunk_end + timedelta(seconds=1)
        # Nghỉ 1 giây để tránh Rate Limit của TikTok API
        time.sleep(1)
        
    print("-" * 50)
    print(f"ĐỒNG BỘ HOÀN TẤT. Tổng cộng: {total_synced} đơn hàng đã lưu vào CSDL.")

if __name__ == "__main__":
    sync_historical_data()
