import os
import json
import gspread
from flask import Flask, request, jsonify, render_template
from google.oauth2.service_account import Credentials

app = Flask(__name__)

credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not credentials_json:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is not set.")
print(credentials_json)  # Debugging: Check if the variable is populated
credentials_info = json.loads(credentials_json)


# Load credentials from environment variable
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not credentials_json:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is not set.")

credentials_info = json.loads(credentials_json)
credentials = Credentials.from_service_account_info(credentials_info)

# Authorize the gspread client
client = gspread.authorize(credentials)

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
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)

