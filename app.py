import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# Define Google Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Credentials file path
CREDENTIALS_FILE = "credentials.json"

# Authenticate with Google Sheets
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
tools_log_sheet = sh.worksheet("Tools & Safety Log")
tools_pending_sheet = sh.worksheet("Tools Pending")

# ================== MRS SECTION ==================

# Fetch item names and codes from Inventory sheet
@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        inventory_data = inventory_sheet.get_all_records()
        items = [{"Item Name": row["Item Name"], "Item Code": row["Item Code"]} for row in inventory_data]
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Log consumption entry
@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.json
        consumption_sheet.append_row([
            data['Date'], data['Item Name'], data['Item Code'],
            data['Quantity'], data['Unit'], data['Consumed Area'], data['Shift']
        ])
        return jsonify({"message": "Consumption logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch consumption history
@app.route('/get-consumption-history', methods=['GET'])
def get_consumption_history():
    try:
        consumption_data = consumption_sheet.get_all_records()
        return jsonify(consumption_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================== TOOLS SECTION ==================

# Fetch tool names from Tools Inventory
@app.route('/get-tools', methods=['GET'])
def get_tools():
    try:
        tools_data = tools_inventory_sheet.get_all_records()
        tool_names = [row["Tool Name"] for row in tools_data if "Tool Name" in row]
        return jsonify(tool_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Log new tool entry into Tools & Safety Log
@app.route('/log-tool-entry', methods=['POST'])
def log_tool_entry():
    try:
        data = request.json
        tools_log_sheet.append_row([
            data['Date'], data['Tool Name'], data['Area'], 
            data['In-Charge'], data['Receiver Name'], 
            data['Contractor'], "Pending"
        ])
        tools_pending_sheet.append_row([
            data['Date'], data['Tool Name'], data['Area'], 
            data['In-Charge'], data['Receiver Name'], 
            data['Contractor'], "Pending"
        ])
        return jsonify({"message": "Tool entry logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch all tools from Tools & Safety Log
@app.route('/get-tool-log', methods=['GET'])
def get_tool_log():
    try:
        tools_log = tools_log_sheet.get_all_records()
        return jsonify(tools_log)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify tool status in Tools & Safety Log and remove from Tools Pending if updated
@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    try:
        data = request.json
        area = data['Area']
        new_status = data['Status']
        tools_log = tools_log_sheet.get_all_records()
        pending_tools = tools_pending_sheet.get_all_records()

        for i, row in enumerate(tools_log, start=2):  # Skip header row
            if row["Area"] == area and row["Status"] == "Pending":
                tools_log_sheet.update_cell(i, 7, new_status)  # Update "Status" column

        # Remove tool from pending sheet if status is changed
        for i, row in enumerate(pending_tools, start=2):
            if row["Area"] == area and row["Status"] == "Pending":
                tools_pending_sheet.delete_rows(i)
                break  # Avoid shifting index issues by breaking after deletion

        return jsonify({"message": f"Status updated for tools in area '{area}' to {new_status}."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch only pending tools from Tools Pending
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    try:
        pending_tools = tools_pending_sheet.get_all_records()
        return jsonify(pending_tools)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  
    app.run(host="0.0.0.0", port=port)

