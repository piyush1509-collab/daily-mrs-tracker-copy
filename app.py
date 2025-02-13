import os

# Get the path to the credentials file from the environment variable
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")

if not CREDENTIALS_FILE or not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(f"Error: Credentials file not found at {CREDENTIALS_FILE}")

from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import os

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")

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


