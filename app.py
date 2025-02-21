import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = "credentials.json"

if not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(f"'{CREDENTIALS_FILE}' not found. Ensure it's in the working directory.")

try:
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    print("✅ Successfully authenticated with Google Sheets API.")
except Exception as e:
    raise Exception(f"❌ Google Sheets authentication failed: {str(e)}")

app = Flask(__name__)

SPREADSHEET_NAME = "items"

try:
    sh = gc.open(SPREADSHEET_NAME)
    print(f"✅ Successfully accessed spreadsheet: {SPREADSHEET_NAME}")
except Exception as e:
    raise Exception(f"❌ Error accessing spreadsheet: {str(e)}")

inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")
tools_inventory_sheet = sh.worksheet("Tools Inventory")
tools_log_sheet = sh.worksheet("Tools & Safety Log")
tools_pending_sheet = sh.worksheet("Tools Pending")

@app.route('/')
def dashboard():
    return render_template("index.html"), 200

@app.route('/mrs')
def mrs():
    return render_template("mrs.html")

@app.route('/tools')
def tools():
    return render_template("tools.html")

# Fetch Tool Names for Log Tool Entry
@app.route('/get-tools', methods=['GET'])
def get_tools():
    try:
        tools_data = tools_inventory_sheet.get_all_records()
        tool_names = [row["Tool Name"] for row in tools_data if "Tool Name" in row]
        return jsonify(tool_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Log Tool Entry (Store Section)
@app.route('/log-tool-entry', methods=['POST'])
def log_tool_entry():
    try:
        data = request.json
        tool_data = [
            data['Date'], data['Tool Name'], data['Area'], 
            data['In-Charge'], data['Receiver Name'], 
            data['Contractor'], "Pending"
        ]
        
        tools_log_sheet.append_row(tool_data)  # Save to "Tools & Safety Log"
        tools_pending_sheet.append_row(tool_data)  # Save to "Tools Pending"
        
        return jsonify({"message": "✅ Tool entry logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify Tool Status
@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    try:
        data = request.json
        area = data['Area']
        new_status = data['Status']
        
        pending_tools = tools_pending_sheet.get_all_records()
        
        for i, row in enumerate(pending_tools, start=2):
            if row["Area"] == area and row["Status"] == "Pending":
                tools_pending_sheet.update_cell(i, 7, new_status)
                if new_status == "Returned":
                    tools_pending_sheet.delete_rows(i)
                return jsonify({"message": f"✅ Status updated for tools in area '{area}' to {new_status}."})

        return jsonify({"message": "⚠ No tools found in the specified area or already updated."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch Pending Tools for User Section
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    try:
        area = request.args.get('area', '')
        pending_tools = tools_pending_sheet.get_all_records()
        
        if area:
            pending_tools = [row for row in pending_tools if row["Area"] == area]

        return jsonify(pending_tools)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

