from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the necessary sheets
SPREADSHEET_NAME = "items"
inventory_sheet = client.open(SPREADSHEET_NAME).worksheet("Inventory")
consumption_sheet = client.open(SPREADSHEET_NAME).worksheet("Consumption Log")

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
        new_row = [
            data.get("Date"),
            data.get("Item Name"),
            data.get("Item Code"),
            data.get("Quantity"),
            data.get("Unit"),
            data.get("Consumed Area"),
            data.get("Shift")
        ]
        consumption_sheet.append_row(new_row)
        return jsonify({"message": "Consumption logged successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/consumption-history', methods=['GET'])
def consumption_history():
    try:
        area = request.args.get('area', '')
        date = request.args.get('date', '')
        records = consumption_sheet.get_all_records()
        
        if area:
            records = [r for r in records if r.get("Consumed Area") == area]
        if date:
            records = [r for r in records if r.get("Date") == date]

        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)



