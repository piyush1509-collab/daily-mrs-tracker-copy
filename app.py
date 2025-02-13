import os
import json

CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_FILE = "credentials.json"

if CREDENTIALS_CONTENT:
    try:
        # Convert string back to JSON
        parsed_json = json.loads(CREDENTIALS_CONTENT)

        # Write JSON to credentials.json file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(parsed_json, f, indent=4)
        
        print(f"✅ Credentials file successfully created at {CREDENTIALS_FILE}")
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
    except Exception as e:
        print(f"❌ Error writing credentials.json: {e}")
else:
    print("❌ GOOGLE_CREDENTIALS_JSON is not set! Make sure the environment variable is configured.")

from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import os

import json
import os

CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_FILE = "credentials.json"

# Create credentials.json dynamically at runtime
if CREDENTIALS_CONTENT:
    with open(CREDENTIALS_FILE, "w") as f:
        f.write(CREDENTIALS_CONTENT)



if not CREDENTIALS_FILE or not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(f"Error: Credentials file not found at {CREDENTIALS_FILE}")

gc = gspread.service_account(filename=CREDENTIALS_FILE)


sheet = gc.open_by_key("1cVeYNtdjZxkofyMrJwsys1YEWfd6W3bFAdXHmWtLl7g")

inventory_sheet = sheet.worksheet("Inventory")
consumption_sheet = sheet.worksheet("Consumption Log")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_items', methods=['GET'])
def get_items():
    """Fetch items from the Inventory sheet"""
    data = inventory_sheet.get_all_records()
    return jsonify(data)

@app.route('/consume', methods=['POST'])
def consume_item():
    """Log consumed items in Google Sheets"""
    data = request.json
    item_name = data.get("item_name")
    item_code = data.get("item_code")
    quantity = data.get("quantity")
    area = data.get("consumed_area")
    shift = data.get("shift")
    date = data.get("date")

    if not all([item_name, item_code, quantity, area, shift, date]):
        return jsonify({"error": "Missing data"}), 400

    # Append data to Consumption Log sheet
    consumption_sheet.append_row([item_name, item_code, quantity, area, date, shift])
    return jsonify({"message": "Consumption logged successfully"})

@app.route('/consumption_history', methods=['GET'])
def get_consumption_history():
    """Fetch consumption history from Google Sheets"""
    data = consumption_sheet.get_all_records()
    return jsonify(data)

from waitress import serve

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)


