from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)  # ✅ Define `client` properly
SPREADSHEET_NAME = "items"
sh = client.open(SPREADSHEET_NAME)

# Open necessary sheets
inventory_sheet = sh.worksheet("Inventory")
consumption_sheet = sh.worksheet("Consumption Log")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mrs')
def mrs():
    return render_template('mrs.html')

@app.route('/tools')
def tools():
    return render_template('tools.html')

@app.route('/store')
def store():
    return render_template('store.html')

@app.route('/user')
def user():
    return render_template('user.html')

# API to get items from inventory
@app.route('/get-items', methods=['GET'])
def get_items():
    try:
        items_data = inventory_sheet.get_all_records()
        return jsonify(items_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to get consumption history
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

# Log Tool Entry (Default: Pending Status)
@app.route('/log-tool', methods=['POST'])
def log_tool():
    try:
        data = request.json
        tool_entry = [
            data["Tool Name"], data["Area"], data["In-Charge"],
            data["Receiver Name"], data["Contractor Name"],
            data["Date Issued"], "Pending"
        ]
        
        log_sheet = sh.worksheet("Tools & Safety Log")
        pending_sheet = sh.worksheet("Tools Pending")
        
        log_sheet.append_row(tool_entry)
        pending_sheet.append_row(tool_entry)  # Also add to pending tools
        
        return jsonify({"message": "Tool logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify Tool Status
@app.route('/modify-tool-status', methods=['POST'])
def modify_tool_status():
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch Pending Tools
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    try:
        sheet = sh.worksheet("Tools Pending")
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch Tools Inventory for Suggestions
def fetch_tools_inventory():
    sheet = sh.worksheet("Tools Inventory")
    records = sheet.get_all_records()
    return [record["Tool Name"] for record in records if "Tool Name" in record]

@app.route('/get-tools', methods=['GET'])
def get_tools():
    return jsonify(fetch_tools_inventory())

@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    try:
        data = request.json
        consumption_entry = [
            data["Item Name"], data["Item Code"], data["Consumed Area"],
            data["Date"], data["Shift"], data["Quantity"], data["Unit"]
        ]
        
        consumption_sheet.append_row(consumption_entry)  # Save to Google Sheet
        
        return jsonify({"message": "Consumption logged successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
