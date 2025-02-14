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
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("items").worksheet("Inventory")
        data = sheet.get_all_values()

        items = [{"Item Code": row[0], "Item Name": row[1]} for row in data[1:]]

        return jsonify(items)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Fetch Consumption History with Filtering by Area & Date
@app.route('/consumption-history', methods=['GET'])
def get_consumption_history():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("items").worksheet("Consumption Log")
        records = sheet.get_all_records()

        # ✅ Apply Filters (If Provided)
        area_filter = request.args.get("area")
        date_filter = request.args.get("date")

        if area_filter:
            records = [r for r in records if r["Consumed Area"].lower() == area_filter.lower()]

        if date_filter:
            records = [r for r in records if r["Date"] == date_filter]

        return jsonify(records)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
