import app
from datetime import datetime

start_dt = datetime.strptime("2026-07-01", "%Y-%m-%d").replace(hour=0, minute=0, second=0)
end_dt = datetime.strptime("2026-07-06", "%Y-%m-%d").replace(hour=23, minute=59, second=59)
print("Testing fetch...")
try:
    res = app.fetch_shop_data(start_dt.timestamp(), end_dt.timestamp(), start_dt, end_dt)
    print("Done. Status:", res.get("status"))
except Exception as e:
    print("Error:", e)
