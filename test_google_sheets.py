import gspread
from oauth2client.service_account import ServiceAccountCredentials

try:
    print("🔄 Connecting to Google Sheets...")

    # ✅ Connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # ✅ Check Available Sheets
    sheet_names = [sheet.title for sheet in client.open("items").worksheets()]
    print("✅ Available Google Sheets:", sheet_names)

    # ✅ Test Fetching Data from "Inventory"
    inventory_sheet = client.open("items").worksheet("Inventory")
    inventory_data = inventory_sheet.get_all_records()
    print("✅ Inventory Data (First 5 rows):", inventory_data[:5])

    # ✅ Test Fetching Data from "Consumption Log"
    consumption_sheet = client.open("items").worksheet("Consumption Log")
    consumption_data = consumption_sheet.get_all_records()
    print("✅ Consumption History (First 5 records):", consumption_data[:5])

except Exception as e:
    print(f"❌ Error: {e}")
