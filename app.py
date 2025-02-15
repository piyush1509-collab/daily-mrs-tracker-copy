import os
import json
import gspread
from flask import Flask, request, jsonify, render_template
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Load credentials from environment variable
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON", "{}"))

# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open Google Sheet
sheet = client.open("items")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get-items")
def get_items():
    inventory_sheet = sheet.worksheet("Inventory")
    data = inventory_sheet.get_all_records()
    return jsonify(data)

@app.route("/consumption-history")
def consumption_history():
    log_sheet = sheet.worksheet("Consumption Log")
    data = log_sheet.get_all_records()
    return jsonify(data)

@app.route("/log-consumption", methods=["POST"])
def log_consumption():
    try:
        data = request.json
        log_sheet = sheet.worksheet("Consumption Log")

        # Append data to sheet
        log_sheet.append_row([
            data["Item name"], 
            data["Item code"], 
            data["QTY"], 
            data["Consumed Area"], 
            data["Date"], 
            data["Shift"]
        ])
        
        return jsonify({"success": True, "message": "Consumption logged successfully!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
