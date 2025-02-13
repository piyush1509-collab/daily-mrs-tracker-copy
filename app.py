import os
import json
import gspread
from flask import Flask, render_template, jsonify
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

# ✅ Fixed: Extract items correctly from Google Sheets
@app.route('/get-items')
def get_items():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("YourGoogleSheetName").worksheet("Sheet1")  # Change to actual sheet name
        items = sheet.col_values(1)  # Assuming item names are in the first column

        if not items:
            return jsonify({"error": "No items found in the sheet"}), 404

        return jsonify(items)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Fixed: Add `/consumption-history` Route
@app.route('/consumption-history')
def get_consumption_history():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("YourGoogleSheetName").worksheet("ConsumptionHistory")  # Change to actual sheet name
        records = sheet.get_all_records()

        if not records:
            return jsonify({"error": "No consumption history found"}), 404

        return jsonify(records)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
