import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'shop_data.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_metrics (
        date TEXT,
        source TEXT,
        seller TEXT,
        revenue REAL,
        orders INTEGER,
        aov REAL,
        upsell REAL,
        final_revenue REAL,
        PRIMARY KEY (date, source, seller)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ads_spend (
        date TEXT,
        platform TEXT,
        campaign TEXT,
        spend REAL,
        PRIMARY KEY (date, platform, campaign)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_targets (
        month TEXT PRIMARY KEY,
        target_revenue REAL,
        target_cost_ratio REAL
    )
    ''')
    
    conn.commit()
    conn.close()

def save_daily_metrics(metrics_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for m in metrics_list:
        cursor.execute('''
        INSERT OR REPLACE INTO daily_metrics (date, source, seller, revenue, orders, aov, upsell, final_revenue)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (m['date'], m.get('source', ''), m.get('seller', ''), m.get('revenue', 0), m.get('orders', 0), m.get('aov', 0), m.get('upsell', 0), m.get('final_revenue', 0)))
    conn.commit()
    conn.close()

def save_ads_spend(spend_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for s in spend_list:
        cursor.execute('''
        INSERT OR REPLACE INTO ads_spend (date, platform, campaign, spend)
        VALUES (?, ?, ?, ?)
        ''', (s['date'], s['platform'], s.get('campaign', 'Unknown'), s.get('spend', 0)))
    conn.commit()
    conn.close()

def get_monthly_target(month_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT target_revenue, target_cost_ratio FROM monthly_targets WHERE month = ?', (month_str,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"target_revenue": row[0], "target_cost_ratio": row[1]}
    return None

def set_monthly_target(month_str, target_rev, target_cost):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO monthly_targets (month, target_revenue, target_cost_ratio)
    VALUES (?, ?, ?)
    ''', (month_str, float(target_rev), float(target_cost)))
    conn.commit()
    conn.close()

def query_dashboard_data(start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Lấy Doanh thu
    cursor.execute('''
        SELECT date, source, SUM(revenue) as total_rev, SUM(orders) as total_orders, SUM(upsell) as total_upsell, SUM(final_revenue) as total_final
        FROM daily_metrics
        WHERE date >= ? AND date <= ?
        GROUP BY date, source
    ''', (start_date, end_date))
    revenue_rows = cursor.fetchall()
    
    # Lấy Chi phí
    cursor.execute('''
        SELECT date, platform, SUM(spend) as total_spend
        FROM ads_spend
        WHERE date >= ? AND date <= ?
        GROUP BY date, platform
    ''', (start_date, end_date))
    spend_rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(r) for r in revenue_rows], [dict(r) for r in spend_rows]

if __name__ == "__main__":
    print("Khởi tạo Database Mới...")
    init_db()
    print("Hoàn tất!")
