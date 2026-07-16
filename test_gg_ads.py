import os
from google.ads.googleads.client import GoogleAdsClient
from dotenv import load_dotenv

load_dotenv("config.env")

credentials = {
    "developer_token": os.getenv("GOOGLE_DEVELOPER_TOKEN"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
    "use_proto_plus": True
}

customer_id = os.getenv("GOOGLE_CUSTOMER_ID")

def test_google_ads():
    try:
        client = GoogleAdsClient.load_from_dict(credentials)
        googleads_service = client.get_service("GoogleAdsService")
        
        query = """
            SELECT
                campaign.id,
                campaign.name,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
        """
        
        print(f"Đang gọi API Google Ads cho Customer ID: {customer_id}...")
        response = googleads_service.search(customer_id=customer_id, query=query)
        
        target_camps = [
            "Adsplus_Shopping_cpc",
            "Adsplus_Search_30Shine Shop_ROAS 350",
            "Adsplus_Pmax_all product_ROAS",
            "Adsplus_Pmax_tạo kiểu tóc_tệp mở rộng_all sp"
        ]
        
        found = 0
        for row in response:
            name = row.campaign.name
            if name in target_camps or found < 10:
                cost = row.metrics.cost_micros / 1000000.0
                print(f"[{name}] - Cost: {cost:,.0f} VND - Clicks: {row.metrics.clicks}")
                found += 1
                
        print("XONG!")
        
    except Exception as e:
        print("LỖI GOOGLE ADS API:", e)

if __name__ == "__main__":
    test_google_ads()
