import database
import sync_history
import time
from datetime import datetime

latest_time = database.get_latest_order_time()
now_ts = int(time.time())

if latest_time:
    print(f"Latest order in DB: {datetime.fromtimestamp(latest_time)}")
    print(f"Now: {datetime.fromtimestamp(now_ts)}")
    print("Syncing...")
    new_orders = sync_history.sync_chunk(latest_time, now_ts)
    if new_orders:
        database.save_orders_to_db(new_orders)
        print(f"Saved {len(new_orders)} new orders to DB!")
    else:
        print("No new orders found.")
else:
    print("DB is empty!")
