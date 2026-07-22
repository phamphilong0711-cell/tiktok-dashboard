import sqlite3
import os
import requests
import datetime
from dotenv import load_dotenv

load_dotenv("config.env")

# 1. Lấy dữ liệu Lark (Cột AE - Index 30)
app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")
spreadsheet_token = os.getenv("LARK_SPREADSHEET_TOKEN")
sheet_id = os.getenv("LARK_SHEET_ID")

url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
token = response.json()["tenant_access_token"]

sheet_url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}!A10:AZ500"
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(sheet_url, headers=headers)
values = resp.json().get("data", {}).get("valueRange", {}).get("values", [])

lark_costs = {}
for row in values:
    if not row or not row[0]: continue
    try:
        dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(row[0]))
        date_str = dt.strftime('%Y-%m-%d')
        
        ae_val = 0
        if len(row) > 30 and row[30]:
            try:
                if '+' in str(row[30]):
                    ae_val = sum([float(x.strip()) for x in str(row[30]).split('+') if x.strip()])
                else:
                    ae_val = float(str(row[30]).replace(',', ''))
            except:
                pass
        if ae_val > 0:
            lark_costs[date_str] = ae_val
    except Exception as e:
        continue

# 2. Lấy dữ liệu API từ SQLite (CHỈ TIKTOK ADS)
conn = sqlite3.connect('shop_data.db')
cursor = conn.cursor()
cursor.execute("SELECT date, SUM(spend) FROM ads_spend WHERE platform = 'TikTok Ads' GROUP BY date")
api_costs = {row[0]: row[1] for row in cursor.fetchall()}
conn.close()

# 3. So sánh
print("\n" + "="*75)
print(f"{'NGÀY':<15} | {'LARK (AE) - TIKTOK':<20} | {'TỰ ĐỘNG (TIKTOK API)':<20} | {'CHÊNH LỆCH'}")
print("="*75)

all_dates = sorted(list(set(list(lark_costs.keys()) + list(api_costs.keys()))))
for d in all_dates[-14:]:
    lark = lark_costs.get(d, 0)
    api = api_costs.get(d, 0)
    diff = api - lark
    diff_str = f"+{diff:,.0f}" if diff > 0 else f"{diff:,.0f}"
    
    print(f"{d:<15} | {lark:>17,.0f} đ | {api:>17,.0f} đ | {diff_str:>12} đ")
print("="*75)
