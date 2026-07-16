import os
import time
import hashlib
import hmac
import json
from flask import Flask, render_template, jsonify, request
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import database
import sync_history

load_dotenv("config.env")

app = Flask(__name__)

# Config Ads
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_ADVERTISER_ID = os.getenv("TIKTOK_ADVERTISER_ID", "")

# Config Shop
SHOP_APP_KEY = os.getenv("TIKTOK_SHOP_APP_KEY", "")
SHOP_APP_SECRET = os.getenv("TIKTOK_SHOP_APP_SECRET", "")
SHOP_ACCESS_TOKEN = os.getenv("TIKTOK_SHOP_ACCESS_TOKEN", "")
SHOP_CIPHER_CACHE = os.getenv("TIKTOK_SHOP_ID", "")

def generate_tiktok_shop_sign(app_secret, api_path, params, body=""):
    sorted_keys = sorted(params.keys())
    param_string = "".join([f"{k}{params[k]}" for k in sorted_keys])
    message = f"{app_secret}{api_path}{param_string}{body}{app_secret}"
    signature = hmac.new(
        app_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_shop_cipher():
    global SHOP_CIPHER_CACHE
    # Chỉ sử dụng cache nếu cipher bắt đầu bằng 'ROW_' hoặc 'VNM_' (định dạng chuẩn của cipher), không phải ID số
    if SHOP_CIPHER_CACHE and not SHOP_CIPHER_CACHE.isdigit() and "điền_" not in SHOP_CIPHER_CACHE:
        return SHOP_CIPHER_CACHE
        
    api_path = "/authorization/202309/shops"
    timestamp = str(int(time.time()))
    params = {"app_key": SHOP_APP_KEY, "timestamp": timestamp}
    sign = generate_tiktok_shop_sign(SHOP_APP_SECRET, api_path, params, "")
    req_params = params.copy()
    req_params["sign"] = sign
    
    headers = {"x-tts-access-token": SHOP_ACCESS_TOKEN}
    url = f"https://open-api.tiktokglobalshop.com{api_path}"
    try:
        res = requests.get(url, headers=headers, params=req_params)
        data = res.json()
        if data.get("code") == 0:
            shops = data.get("data", {}).get("shops", [])
            if shops:
                SHOP_CIPHER_CACHE = shops[0].get("cipher")
                return SHOP_CIPHER_CACHE
    except Exception as e:
        print("Exception lấy shop cipher:", e)
    return None

def process_shop_orders(orders, start_dt, end_dt):
    daily_revenue = {}
    products = {}
    total_revenue = 0
    daily_products_dict = {}
    
    current_dt = start_dt
    while current_dt <= end_dt:
        daily_revenue[current_dt.strftime("%d/%m")] = 0
        current_dt += timedelta(days=1)
        
    for order in orders:
        # Bỏ qua đơn Huỷ và Chưa thanh toán
        status = order.get("status", "")
        if status in ["CANCEL", "CANCELLED", "UNPAID"]:
            continue
            
        create_time = order.get("create_time", 0)
        date_str = datetime.fromtimestamp(create_time).strftime("%d/%m")
        payment_amount = float(order.get("payment", {}).get("total_amount", 0))
        total_revenue += payment_amount
        
        if date_str in daily_revenue:
            daily_revenue[date_str] += payment_amount
            
        line_items = order.get("line_items", [])
        for item in line_items:
            # Ưu tiên seller_sku, nếu không có thì lấy sku_name, cuối cùng lấy product_name
            seller_sku = item.get("seller_sku", "").strip()
            sku_name = item.get("sku_name", "").strip()
            product_name = item.get("product_name", "Sản phẩm khác").strip()
            
            sku_id = item.get("sku_id", "")
            
            # Chọn tên hiển thị và mã SKU
            display_name = sku_name if sku_name else product_name
            display_sku = seller_sku if seller_sku else sku_id
            
            price = float(item.get("sale_price", 0)) * int(item.get("quantity", 1))
            quantity = int(item.get("quantity", 1))
            
            if display_name not in products:
                products[display_name] = 0
            products[display_name] += price
            
            # Gom nhóm theo Ngày + Mã SKU
            group_key = f"{date_str}_{display_sku}"
            if group_key not in daily_products_dict:
                daily_products_dict[group_key] = {
                    "date": date_str,
                    "name": display_name,
                    "sku": display_sku,
                    "quantity": 0,
                    "revenue": 0
                }
            
            daily_products_dict[group_key]["quantity"] += quantity
            daily_products_dict[group_key]["revenue"] += price

    sorted_products = sorted(products.items(), key=lambda x: x[1], reverse=True)
    top_products = [{"name": p[0][:30] + "...", "revenue_share": p[1]} for p in sorted_products[:4]]
    
    # Chuyển dict thành list và sắp xếp theo ngày (giảm dần) -> doanh thu (giảm dần)
    daily_products = list(daily_products_dict.values())
    daily_products = sorted(daily_products, key=lambda x: (x['date'], x['revenue']), reverse=True)
    
    return {
        "status": "success",
        "data": {
            "total_revenue": total_revenue,
            "daily_revenue": daily_revenue,
            "top_products": top_products,
            "daily_details": daily_products
        }
    }

def fetch_shop_data(start_time, end_time, start_dt, end_dt):
    if not SHOP_ACCESS_TOKEN or "điền_" in SHOP_ACCESS_TOKEN:
        return {"status": "error", "message": "Chưa có Shop Token"}
        
    cipher = get_shop_cipher()
    if not cipher:
        return {"status": "error", "message": "Không lấy được Shop Cipher"}
        
    api_path = "/order/202309/orders/search"
    timestamp = str(int(time.time()))
    
    params = {
        "app_key": SHOP_APP_KEY,
        "timestamp": timestamp,
        "shop_cipher": cipher,
        "page_size": 100
    }
    
    all_orders = []
    
    headers = {
        "x-tts-access-token": SHOP_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    current_start = int(start_time)
    end_time_int = int(end_time)
    
    while current_start < end_time_int:
        body_dict = {
            "page_size": 100, 
            "create_time_ge": current_start,
            "create_time_lt": end_time_int
        }
            
        body_str = json.dumps(body_dict, separators=(',', ':'))
        sign = generate_tiktok_shop_sign(SHOP_APP_SECRET, api_path, params, body_str)
        
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
                if not all_orders:
                    return {"status": "error", "message": data.get("message")}
                break
        except Exception as e:
            if not all_orders:
                return {"status": "error", "message": str(e)}
            break
            
    # Lọc trùng lặp đơn hàng (Deduplicate theo order_id)
    unique_orders = {o.get("id", ""): o for o in all_orders if o.get("id")}
    all_orders = list(unique_orders.values())
    
    return process_shop_orders(all_orders, start_dt, end_dt)

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/api/settings/target", methods=['GET', 'POST'])
def manage_targets():
    if request.method == 'POST':
        data = request.json
        month_str = data.get('month') # Format 'YYYY-MM'
        target_rev = data.get('target_revenue', 0)
        target_cost = data.get('target_cost_ratio', 0)
        if month_str:
            database.set_monthly_target(month_str, target_rev, target_cost)
            return jsonify({"status": "success", "message": "Đã lưu mục tiêu"})
        return jsonify({"status": "error", "message": "Thiếu tháng"}), 400
    
    month_str = request.args.get('month')
    if month_str:
        target = database.get_monthly_target(month_str)
        if target:
            return jsonify({"status": "success", "data": target})
    return jsonify({"status": "success", "data": {"target_revenue": 0, "target_cost_ratio": 0}})

@app.route("/api/dashboard-data")
def get_dashboard_data():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    today = datetime.now()
    if not start_str or not end_str:
        end_dt = today.replace(hour=23, minute=59, second=59)
        start_dt = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0)
    else:
        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            end_dt = datetime.strptime(end_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except:
            end_dt = today.replace(hour=23, minute=59, second=59)
            start_dt = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0)

    # Truy vấn dữ liệu ETL
    rev_data, spend_data = database.query_dashboard_data(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    
    total_rev = sum([r.get('total_rev', 0) or 0 for r in rev_data])
    total_orders = sum([r.get('total_orders', 0) or 0 for r in rev_data])
    total_upsell = sum([r.get('total_upsell', 0) or 0 for r in rev_data])
    total_final = sum([r.get('total_final', 0) or 0 for r in rev_data])
    
    # Doanh thu / đơn
    aov = total_rev / total_orders if total_orders > 0 else 0
    # Doanh thu / ngày
    days_diff = (end_dt - start_dt).days + 1
    daily_avg = total_rev / days_diff if days_diff > 0 else 0
    
    # Nhóm theo Nguồn (Pie Chart) Doanh thu
    source_distribution = {}
    for r in rev_data:
        src = r.get('source', 'Unknown')
        source_distribution[src] = source_distribution.get(src, 0) + (r.get('total_rev', 0) or 0)
    
    pie_chart = [{"name": k, "value": v} for k, v in source_distribution.items() if v > 0]
    
    # Nhóm theo Nguồn (Pie Chart) Chi phí và Tách Chi phí khác
    spend_distribution = {}
    other_costs_list = []
    total_spend = 0
    total_other_costs = 0
    
    for s in spend_data:
        plat = s.get('platform', 'Unknown')
        val = s.get('total_spend', 0) or 0
        
        if plat.startswith('Khác - '):
            cost_name = plat.replace('Khác - ', '')
            other_costs_list.append({"name": cost_name, "spend": val})
            total_other_costs += val
        else:
            spend_distribution[plat] = spend_distribution.get(plat, 0) + val
            total_spend += val
            
    spend_pie_chart = [{"name": k, "value": v} for k, v in spend_distribution.items() if v > 0]
    
    # Tính CIR theo từng kênh
    cir_by_channel = {}
    for src, rev in source_distribution.items():
        spend = 0
        if src == 'Shopee': spend = spend_distribution.get('Shopee', 0) + spend_distribution.get('SHOPEE_ADS', 0)
        elif src == 'TikTok': spend = spend_distribution.get('TikTok Ads', 0) + spend_distribution.get('TIKTOK_ADS', 0)
        elif src == 'Lazada': spend = spend_distribution.get('Lazada', 0)
        elif src == 'Facebook': spend = spend_distribution.get('Facebook', 0) + spend_distribution.get('Facebook Ads', 0)
        elif src == 'Web/App': spend = spend_distribution.get('Google Ads', 0)
        
        cir = (spend / rev * 100) if rev > 0 else 0
        cir_by_channel[src] = {"revenue": rev, "spend": spend, "cir": cir}
        
    # Xử lý trường hợp Google Ads có chi phí nhưng chưa có doanh thu Web/App
    google_spend = spend_distribution.get('Google Ads', 0)
    if 'Web/App' not in source_distribution and google_spend > 0:
        cir_by_channel['Google'] = {"revenue": 0, "spend": google_spend, "cir": 0}
    
    # Nhóm theo Ngày (Line Chart)
    daily_trends = {}
    for r in rev_data:
        d = r.get('date')
        if d not in daily_trends:
            daily_trends[d] = {"date": d, "revenue": 0, "orders": 0, "spend": 0}
        daily_trends[d]["revenue"] += (r.get('total_rev', 0) or 0)
        daily_trends[d]["orders"] += (r.get('total_orders', 0) or 0)
        
    for s in spend_data:
        plat = s.get('platform', '')
        if plat.startswith('Khác - '): continue # Không cộng chi phí khác vào line chart quảng cáo
        
        d = s.get('date')
        if d not in daily_trends:
            daily_trends[d] = {"date": d, "revenue": 0, "orders": 0, "spend": 0}
        daily_trends[d]["spend"] += (s.get('total_spend', 0) or 0)
        
    trend_list = sorted(list(daily_trends.values()), key=lambda x: x['date'])
    
    # Lấy Target tháng và tính Luỹ kế (MTD)
    month_str = start_dt.strftime('%Y-%m')
    target = database.get_monthly_target(month_str)
    target_rev = target['target_revenue'] if target else 0
    target_cost_ratio = target['target_cost_ratio'] if target else 0
    
    mtd_start = end_dt.replace(day=1, hour=0, minute=0, second=0)
    mtd_rev_data, mtd_spend_data = database.query_dashboard_data(mtd_start.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    mtd_revenue = sum([r.get('total_rev', 0) or 0 for r in mtd_rev_data])
    mtd_spend = 0
    for s in mtd_spend_data:
        if not s.get('platform', '').startswith('Khác - '):
            mtd_spend += (s.get('total_spend', 0) or 0)
    mtd_cost_ratio = (mtd_spend / mtd_revenue * 100) if mtd_revenue > 0 else 0
    
    dashboard_data = {
        "summary": {
            "total_revenue": total_rev,
            "total_orders": total_orders,
            "aov": aov,
            "daily_avg": daily_avg,
            "upsell": total_upsell,
            "final_revenue": total_final,
            "total_spend": total_spend,
            "cost_ratio": (total_spend / total_rev * 100) if total_rev > 0 else 0,
            "target_revenue": target_rev,
            "target_cost_ratio": target_cost_ratio,
            "mtd_revenue": mtd_revenue,
            "mtd_spend": mtd_spend,
            "mtd_cost_ratio": mtd_cost_ratio
        },
        "sources": pie_chart,
        "spend_sources": spend_pie_chart,
        "trends": trend_list,
        "cir_by_channel": cir_by_channel,
        "other_costs": other_costs_list,
        "total_other_costs": total_other_costs
    }

    return jsonify({"status": "success", "data": dashboard_data})

def get_mock_data(start_dt, end_dt, days_diff):
    trends = []
    daily_details = []
    current_dt = start_dt
    
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%d/%m")
        
        spend = 300000 + (current_dt.day * 15000)
        ad_rev = 1200000 + (current_dt.day * 50000)
        real_rev = 3000000 + (current_dt.day * 120000)
        
        trends.append({
            "date": date_str,
            "spend": spend,
            "ad_revenue": ad_rev,
            "real_revenue": real_rev
        })
        
        daily_details.append({"date": date_str, "name": "Dầu gội phủ bạc", "sku": "DG-01", "quantity": 15, "revenue": real_rev * 0.45})
        daily_details.append({"date": date_str, "name": "Sáp vuốt tóc", "sku": "SVT-02", "quantity": 25, "revenue": real_rev * 0.30})
        daily_details.append({"date": date_str, "name": "Gôm xịt tóc", "sku": "GXT-03", "quantity": 10, "revenue": real_rev * 0.15})
        daily_details.append({"date": date_str, "name": "Sản phẩm khác", "sku": "OTHER", "quantity": 5, "revenue": real_rev * 0.10})
        
        current_dt += timedelta(days=1)
        if len(trends) > 60: 
            break
            
    total_spend = sum(t['spend'] for t in trends)
    total_ad_rev = sum(t['ad_revenue'] for t in trends)
    total_real_rev = sum(t['real_revenue'] for t in trends)
    
    daily_details = sorted(daily_details, key=lambda x: x['date'], reverse=True)
            
    # Tính mô phỏng growth dựa vào số ngày để hợp logic
    growth_multiplier = -1 if days_diff == 7 else 1
    
    return {
        "summary": {
            "spend": total_spend,
            "spend_growth": round(2.4 * growth_multiplier, 1),
            "ad_revenue": total_ad_rev,
            "ad_revenue_growth": round(5.1 * growth_multiplier, 1),
            "real_revenue": total_real_rev,
            "real_revenue_growth": round(8.2 * growth_multiplier, 1),
            "roas": round(total_ad_rev / total_spend, 1) if total_spend > 0 else 0,
            "roas_growth": round(1.1 * growth_multiplier, 1),
            "impressions": 150000 * days_diff,
            "clicks": 4500 * days_diff,
            "ctr": 3.0
        },
        "trends": trends,
        "daily_details": daily_details,
        "top_creatives": [
            {"id": "Vid01", "name": "Review sản phẩm A", "spend": 300000 * days_diff, "roas": 4.5, "ctr": 4.2},
            {"id": "Vid02", "name": "Unbox nhanh sản phẩm B", "spend": 250000 * days_diff, "roas": 3.8, "ctr": 3.5},
            {"id": "Vid03", "name": "Livestream highlight", "spend": 200000 * days_diff, "roas": 5.0, "ctr": 5.1}
        ],
        "product_distribution": [
            {"name": "Dầu gội phủ bạc", "revenue_share": 45},
            {"name": "Sáp vuốt tóc", "revenue_share": 30},
            {"name": "Gôm xịt tóc", "revenue_share": 15},
            {"name": "Khác", "revenue_share": 10}
        ]
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
