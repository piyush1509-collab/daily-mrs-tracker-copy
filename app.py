import os
import json
import gspread
from flask import Flask, render_template, jsonify, request
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_FILE = "credentials.json"

if CREDENTIALS_CONTENT:
    try:
        parsed_json = json.loads(CREDENTIALS_CONTENT)
        if "private_key" in parsed_json:
            parsed_json["private_key"] = parsed_json["private_key"].replace("\\n", "\n")

        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(parsed_json, f, indent=4)

        print(f"✅ Credentials file successfully created at {CREDENTIALS_FILE}")

    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
    except Exception as e:
        print(f"❌ Error writing credentials.json: {e}")
else:
    print("❌ GOOGLE_CREDENTIALS_JSON is not set! Make sure the environment variable is configured.")

@app.route('/')
def home():
    return render_template('index.html')

# ✅ Fetch Items from "Inventory" Sheet (Auto-Suggestion)
@app.route('/get-items')
def get_items():
    try:
        # ✅ Connect to Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        # ✅ Fetch Data from "Inventory"
        sheet = client.open("items").worksheet("Inventory")
        data = sheet.get_all_records()

        # ✅ Ensure correct JSON format
        items = [{"Item Name": row["Item Name"], "Item Code": row["Item Code"]} for row in data]

        return jsonify(items)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

from flask import request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import traceback  # 🔹 Import traceback for debugging

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        if request.content_type != "application/json":
            return jsonify({"success": False, "error": "Content-Type must be 'application/json'"}), 415

        data = request.get_json(force=True)  

        item_name = data.get("Item name")
        item_code = data.get("Item code")
        consumed_area = data.get("Consumed Area")
        date = data.get("Date")
        shift = data.get("Shift")
        qty = data.get("QTY", 1)

        if not (item_name and item_code and consumed_area and date and shift):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # ✅ Connect to Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        # ✅ Append data to "Consumption Log"
        sheet = client.open("items").worksheet("Consumption Log")
        sheet.append_row([item_name, item_code, qty, consumed_area, date, shift])

        return jsonify({"success": True})

    except Exception as e:
        error_details = traceback.format_exc()  # 🔹 Capture full error traceback
        print(f"❌ Error logging consumption: {error_details}")  # 🔹 Print error in logs
        return jsonify({"success": False, "error": str(e)}), 500


# ✅ Fetch Consumption History with Filtering by Area & Date
@app.route('/consumption-history')
def consumption_history():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("items").worksheet("Consumption Log")
        data = sheet.get_all_records()

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
