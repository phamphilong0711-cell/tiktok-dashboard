import app

print("Fetching shop cipher...")
cipher = app.get_shop_cipher()
print("Cipher:", cipher)

print("Fetching shop data...")
data = app.fetch_shop_data()
print("Data:", data)
