from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)  # ✅ Define `client` properly
SPREADSHEET_NAME = "items"  # ✅ Define spreadsheet name BEFORE using it
sh = client.open(SPREADSHEET_NAME)  # ✅ Now use `sh`


# Open the necessary sheets
SPREADSHEET_NAME = "items"
inventory_sheet = client.open(SPREADSHEET_NAME).worksheet("Inventory")
consumption_sheet = client.open(SPREADSHEET_NAME).worksheet("Consumption Log")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mrs')
def mrs():
    return render_template('mrs.html')

@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        items_data = inventory_sheet.get_all_records()
        return jsonify(items_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.json
        required_fields = ["Date", "Item Name", "Item Code", "Quantity", "Unit", "Consumed Area", "Shift"]
        
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Missing required fields or empty values"}), 400
        
        new_row = [data[field] for field in required_fields]
        consumption_sheet.append_row(new_row)
        return jsonify({"message": "Consumption logged successfully", "data": new_row})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/consumption-history', methods=['GET'])
def consumption_history():
    try:
        area = request.args.get('area', '').strip()
        date = request.args.get('date', '').strip()
        records = consumption_sheet.get_all_records()
        
        filtered_records = records
        if area:
            filtered_records = [r for r in records if r.get("Consumed Area", "").strip() == area]
        if date:
            filtered_records = [r for r in filtered_records if r.get("Date", "").strip() == date]

        return jsonify(filtered_records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tools')
def tools():
    return render_template('tools.html')


# Log Tool Entry (Default: Pending Status)
@app.route('/log-tool', methods=['POST'])
def log_tool():
    data = request.json
    tool_entry = [
        data["Tool Name"], data["Area"], data["In-Charge"],
        data["Receiver Name"], data["Contractor Name"],
        data["Date Issued"], "Pending"
    ]
    
    # ✅ Correct indentation
    log_sheet = client.open(SPREADSHEET_NAME).worksheet("Tools & Safety Log")
    pending_sheet = client.open(SPREADSHEET_NAME).worksheet("Tools Pending")
    
    log_sheet.append_row(tool_entry)
    pending_sheet.append_row(tool_entry)  # Also add to pending tools
    
    return jsonify({"message": "Tool logged successfully!"})

@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    data = request.json
    tool_name = data["Tool Name"]
    status = data["Status"]
    
    log_sheet = sh.worksheet("Tools & Safety Log")
    pending_sheet = sh.worksheet("Tools Pending")
    
    # Update status in Tools & Safety Log
    records = log_sheet.get_all_records()
    for i, record in enumerate(records, start=2):
        if record["Tool Name"] == tool_name and record["Status"] == "Pending":
            log_sheet.update_cell(i, 7, status)  # Column 7 is Status
            break
    
    # Remove from Tools Pending if status is Returned
    if status == "Returned":
        pending_records = pending_sheet.get_all_records()
        for i, record in enumerate(pending_records, start=2):
            if record["Tool Name"] == tool_name:
                pending_sheet.delete_rows(i)
                break
    
    return jsonify({"message": "Tool status updated successfully!"})

# Fetch Pending Tools
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    sheet = client.open(SPREADSHEET_NAME).worksheet("Tools Pending")  # ✅ Correct version
    records = sheet.get_all_records()
    return jsonify(records)


# Fetch Tools Inventory for Suggestions
def fetch_tools_inventory():
    sheet = sh.worksheet("Tools Inventory")
    records = sheet.get_all_records()
    return [record["Tool Name"] for record in records if "Tool Name" in record]

@app.route('/get-tools', methods=['GET'])
def get_tools():
    return jsonify(fetch_tools_inventory())

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/store')
def store():
    return render_template('store.html')

@app.route('/user')
def user():
    return render_template('user.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)


