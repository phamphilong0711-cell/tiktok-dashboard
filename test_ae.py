import lark_sync
data = lark_sync.fetch_sheet_data(lark_sync.LARK_SPREADSHEET_TOKEN, lark_sync.LARK_SHEET_ID)
if data:
    header = data[0]
    print(f"Header length: {len(header)}")
    if len(header) > 30:
        print(f"Column AE header: {header[30]}")
    else:
        print("Not enough columns!")
    
    # Print last 3 rows date and col AE
    for row in data[-3:]:
        date = row[0] if len(row) > 0 else "Unknown"
        ae = row[30] if len(row) > 30 else "N/A"
        print(f"{date} - AE: {ae}")
