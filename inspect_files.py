import pandas as pd
import glob
import os

files = [
    "/home/pham-phi-long-109/Downloads/tblTmdtSource_2026-07-13.xlsx",
    "/home/pham-phi-long-109/Downloads/Chi phí 6-12.7/creative data for product campaigns 2026-07-06 00 ~ 2026-07-12 23.xlsx",
    "/home/pham-phi-long-109/Downloads/Chi phí 6-12.7/income_20260713090449(UTC+7).xlsx",
    "/home/pham-phi-long-109/Downloads/Chi phí 6-12.7/livestream data for live campaigns 2026-07-06 00 ~ 2026-07-12 23.xlsx"
]

print("=== INSPECTING EXCEL FILES ===")
for f in files:
    print(f"\n--- File: {os.path.basename(f)} ---")
    try:
        df = pd.read_excel(f, nrows=5)
        print("Columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict() if not df.empty else "Empty")
    except Exception as e:
        print("Error reading:", e)

