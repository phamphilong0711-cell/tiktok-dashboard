import sqlite3
import json
import os

DB_PATH = 'shop_data.db'

def export_to_json():
    if not os.path.exists(DB_PATH):
        print(f"Không tìm thấy database {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Doanh thu (nhóm theo ngày và kênh)
    cursor.execute('''
        SELECT date, source, SUM(revenue) as total_rev, SUM(orders) as total_orders, SUM(upsell) as total_upsell, SUM(final_revenue) as total_final
        FROM daily_metrics
        GROUP BY date, source
    ''')
    rev_rows = cursor.fetchall()
    revenue_data = [dict(r) for r in rev_rows]

    # 2. Chi phí
    cursor.execute('''
        SELECT date, platform, SUM(spend) as total_spend
        FROM ads_spend
        GROUP BY date, platform
    ''')
    spend_rows = cursor.fetchall()
    spend_data = [dict(r) for r in spend_rows]

    # 3. Mục tiêu tháng
    cursor.execute('SELECT month, target_revenue, target_cost_ratio FROM monthly_targets')
    target_rows = cursor.fetchall()
    targets = {r['month']: {"target_revenue": r['target_revenue'], "target_cost_ratio": r['target_cost_ratio']} for r in target_rows}

    conn.close()

    data = {
        "revenue_data": revenue_data,
        "spend_data": spend_data,
        "monthly_targets": targets
    }

    # Xuất ra thư mục templates/static hoặc thư mục gốc để GitHub Pages đọc
    # Github Pages thường đọc thư mục gốc. Ta sẽ lưu ở thư mục gốc.
    output_path = 'data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã xuất dữ liệu ra {output_path} thành công!")

if __name__ == '__main__':
    export_to_json()
