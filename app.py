import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# Define the correct scopes for Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Path to the credentials file
CREDENTIALS_FILE = "credentials.json"

# Check if credentials file exists
if not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(f"'{CREDENTIALS_FILE}' not found. Ensure it's in the working directory.")

# Authenticate using service account credentials
try:
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    print("Successfully authenticated with Google Sheets API.")
except Exception as e:
    raise Exception(f"Google Sheets authentication failed: {str(e)}")

# Initialize Flask app
app = Flask(__name__)

# Open the Google Spreadsheet
SPREADSHEET_NAME = "items"

try:
    sh = gc.open(SPREADSHEET_NAME)
    print(f"Successfully accessed spreadsheet: {SPREADSHEET_NAME}")
except Exception as e:
    raise Exception(f"Error accessing spreadsheet: {str(e)}")

# Load Sheets
inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")
tools_inventory_sheet = sh.worksheet("Tools Inventory")
tools_pending_sheet = sh.worksheet("Tools Pending")
tools_safety_log_sheet = sh.worksheet("Tools & Safety Log")  # Ensure this sheet exists

# Routes
@app.route('/')
def dashboard():
    return render_template("index.html")

@app.route('/tools')
def tools():
    return render_template("tools.html")

# Fetch tool names from Tools Inventory
@app.route('/get-tools', methods=['GET'])
def get_tools():
    try:
        tools_data = tools_inventory_sheet.get_all_records()
        tool_names = [row["Tool Name"] for row in tools_data if "Tool Name" in row]
        return jsonify(tool_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Log tool entry into Tools Pending and Tools & Safety Log
@app.route('/log-tool-entry', methods=['POST'])
def log_tool_entry():
    try:
        data = request.json
        entry = [data['Date'], data['Tool Name'], data['Area'], data['In-Charge'], data['Receiver Name'], data['Contractor'], "Pending"]
        tools_pending_sheet.append_row(entry)
        tools_safety_log_sheet.append_row(entry)  # Log in Tools & Safety Log
        return jsonify({"message": "Tool entry logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch all pending tools
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    try:
        pending_tools = tools_pending_sheet.get_all_records()
        return jsonify(pending_tools)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify Tool Status with area-wise and date-wise filter
@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    try:
        data = request.json
        area = data['Area']
        date = data.get('Date', None)  # Optional date filter
        new_status = data['Status']
        
        safety_log_data = tools_safety_log_sheet.get_all_records()
        for i, row in enumerate(safety_log_data, start=2):  # Skip header row
            if row["Area"] == area and row["Status"] == "Pending" and (date is None or row["Date"] == date):
                tools_safety_log_sheet.update_cell(i, 7, new_status)  # Update "Status" column
                return jsonify({"message": f"Status updated for tools in area '{area}' to {new_status}."})
        
        return jsonify({"message": "No tools found in the specified area or already updated."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)

