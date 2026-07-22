import requests, json
url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
headers = {"Access-Token": "d1acc31a7ccb6a32d77666a87d3ef4345c03d7f7"}
params = {
    "advertiser_id": "7444857279880609808",
    "report_type": "BASIC",
    "data_level": "AUCTION_ADVERTISER",
    "dimensions": json.dumps(["stat_time_day"]),
    "metrics": json.dumps(["spend"]),
    "start_date": "2026-07-15",
    "end_date": "2026-07-21",
    "page_size": 1000
}
res = requests.get(url, headers=headers, params=params)
print(res.text)
