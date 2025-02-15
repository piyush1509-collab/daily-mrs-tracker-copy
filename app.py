from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ✅ Define Google Sheets API Scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ✅ Load Google Credentials from Environment Variable
CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not CREDENTIALS_CONTENT:
    raise FileNotFoundError("❌ GOOGLE_CREDENTIALS_JSON environment variable is missing!")

creds_dict = json.loads(CREDENTIALS_CONTENT)  # Convert string to dictionary
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)  # Use dict

# ✅ Authorize Google Sheets Client
client = gspread.authorize(creds)

# ✅ Open the Google Sheets (Make sure to replace with your actual sheet name)
sheet_inventory = client.open("items").worksheet("Inventory")  # Sheet for item codes
sheet_consumption = client.open("items").worksheet("Consumption Log")  # Sheet for logging consumption


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        data = inventory_sheet.get_all_records()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received", "success": False})
        
        row = [
            data.get("Item name", ""),
            data.get("Item code", ""),
            data.get("QTY", 1),
            data.get("Unit", "Each"),
            data.get("Consumed Area", ""),
            data.get("Date", ""),
            data.get("Shift", "")
        ]
        consumption_sheet.append_row(row)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False})

@app.route('/consumption-history', methods=['GET'])
def consumption_history():
    try:
        data = consumption_sheet.get_all_records()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
