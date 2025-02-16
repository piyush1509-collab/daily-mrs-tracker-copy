import os
import json
import gspread
from flask import Flask, request, jsonify, render_template
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Load credentials from environment variable
with open("credentials.json") as f:
    creds_dict = json.load(f)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the Google Sheets
db = client.open("items")
inventory_sheet = db.worksheet("Inventory")
consumption_sheet = db.worksheet("Consumption Log")

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/get-items", methods=["GET"])
def get_items():
    try:
        data = inventory_sheet.get_all_records()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/log-consumption", methods=["POST"])
def log_consumption():
    try:
        data = request.json
        row = [
            data["Item name"], data["Item code"], data["QTY"],
            data["Unit"], data["Consumed Area"], data["Date"], data["Shift"]
        ]
        consumption_sheet.append_row(row)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False})

@app.route("/consumption-history", methods=["GET"])
def consumption_history():
    try:
        area = request.args.get("area")
        date = request.args.get("date")
        records = consumption_sheet.get_all_records()
        
        if area:
            records = [r for r in records if r["Consumed Area"] == area]
        if date:
            records = [r for r in records if r["Date"] == date]
        
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

