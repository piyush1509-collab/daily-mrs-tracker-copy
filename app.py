from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
SPREADSHEET_NAME = "items"
sh = client.open(SPREADSHEET_NAME)

# Open necessary sheets
inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mrs')
def mrs():
    return render_template('mrs.html')

@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        items_data = inventory_sheet.get_all_records()
        return jsonify(items_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.json
        items = data["items"]
        consumed_area = data["Consumed Area"]
        shift = data["Shift"]
        date = data["Date"]
        area_incharge = data["Area-Incharge"]
        receiver = data["Receiver"]
        contractor = data["Contractor"]

        inventory_data = inventory_sheet.get_all_records()

        for item in items:
            item_code = item["Item Code"]
            item_name = item["Item Name"]
            quantity = int(item["Quantity"])
            unit = item["Unit"]

            for idx, row in enumerate(inventory_data):
                if str(row["Item Code"]) == str(item_code):
                    physical_stock = int(row["Physical Stock"])
                    
                    if quantity > physical_stock:
                        return jsonify({"error": f"Requested quantity of {item_name} exceeds available stock!"}), 400

                    new_stock = max(0, physical_stock - quantity)
                    inventory_sheet.update_cell(idx + 2, 3, new_stock)
                    break

            log_entry = [date, item_name, item_code, quantity, unit, consumed_area, shift, area_incharge, receiver, contractor]
            consumption_sheet.append_row(log_entry)

        return jsonify({"message": "All items logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
