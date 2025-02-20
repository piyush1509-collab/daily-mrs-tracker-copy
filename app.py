from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime

app = Flask(__name__)

# Debugging to check the environment variable
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not credentials_json:
    raise ValueError("Environment variable GOOGLE_APPLICATION_CREDENTIALS_JSON is not set or is empty.")

print("First 100 characters of GOOGLE_APPLICATION_CREDENTIALS_JSON:", credentials_json[:100])  # Debug log

credentials_info = json.loads(credentials_json)
print("private_key starts with:", credentials_info.get("private_key", "")[:20])  # Debug log

# Authorize credentials
credentials = Credentials.from_service_account_info(credentials_info)
gc = gspread.authorize(credentials)

# Open the Google Spreadsheet
SPREADSHEET_NAME = "items"
sh = gc.open(SPREADSHEET_NAME)

# Sheets
inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")
tools_inventory_sheet = sh.worksheet("Tools Inventory")
tools_pending_sheet = sh.worksheet("Tools Pending")  # Ensure this sheet exists

# Routes
@app.route('/')
def dashboard():
    return render_template("index.html")

@app.route('/mrs')
def mrs():
    return render_template("mrs.html")

@app.route('/tools')
def tools():
    return render_template("tools.html")

# Fetch item names and codes for MRS from the Inventory sheet
@app.route('/get-mrs-items', methods=['GET'])
def get_mrs_items():
    try:
        inventory_data = inventory_sheet.get_all_records()
        items = [{"Item name": row["Item Name"], "Item code": row["Item Code"]} for row in inventory_data]
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch consumption history for MRS
@app.route('/get-consumption-history', methods=['GET'])
def get_consumption_history():
    try:
        consumption_data = consumption_sheet.get_all_records()
        return jsonify(consumption_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch tool names for Tools section
@app.route('/get-tools', methods=['GET'])
def get_tools():
    try:
        tools_data = tools_inventory_sheet.get_all_records()
        tool_names = [row["Tool Name"] for row in tools_data if "Tool Name" in row]
        return jsonify(tool_names)  # Send tool names as JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Log tool entry into Tools Pending
@app.route('/log-tool-entry', methods=['POST'])
def log_tool_entry():
    try:
        data = request.json
        tools_pending_sheet.append_row([
            data['Date'], data['Tool Name'], data['Area'], 
            data['In-Charge'], data['Receiver Name'], 
            data['Contractor'], "Pending"
        ])
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

# Modify Tool Status in "Tools Pending"
@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    try:
        data = request.json
        tool_name = data['Tool Name']
        new_status = data['Status']
        pending_tools = tools_pending_sheet.get_all_records()
        
        for i, row in enumerate(pending_tools, start=2):  # Skip header row
            if row["Tool Name"] == tool_name and row["Status"] == "Pending":
                tools_pending_sheet.update_cell(i, 7, new_status)  # Update "Status" column
                return jsonify({"message": f"Tool '{tool_name}' status updated to {new_status}."})

        return jsonify({"message": "Tool not found or already updated."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)
