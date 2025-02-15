from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = Flask(__name__)

# Load credentials
CREDENTIALS_FILE = "credentials.json"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Open sheets
inventory_sheet = client.open("items").worksheet("Inventory")
consumption_sheet = client.open("items").worksheet("Consumption Log")

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
