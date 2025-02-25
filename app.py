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

        # Ensure we always return an array, even if empty
        if not isinstance(records, list):
            return jsonify([])  # Return an empty list instead of an error
        
        filtered_records = records if records else []

        if area:
            filtered_records = [r for r in filtered_records if r.get("Consumed Area", "").strip() == area]
        if date:
            filtered_records = [r for r in filtered_records if r.get("Date", "").strip() == date]

        return jsonify(filtered_records)  # ✅ Always return an array
    except Exception as e:
        return jsonify([])  # ✅ Return an empty array on error to prevent forEach error


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
        return_date = data.get("Return Date", "")  # Get return date or empty if not provided

        log_sheet = sh.worksheet("Tools & Safety Log")
        pending_sheet = sh.worksheet("Tools Pending")

        # Update status & return date in Tools & Safety Log
        records = log_sheet.get_all_records()
        for i, record in enumerate(records, start=2):
            if record["Tool Name"] == tool_name and record["Status"] == "Pending":
                log_sheet.update(f"G{i}", [[status]])  # Column G is "Status"
                log_sheet.update(f"H{i}", [[return_date]])  # Column H is "Return Date"
                break
        
        # Remove from Tools Pending if status is "Returned"
        if status == "Returned":
            pending_records = pending_sheet.get_all_records()
            for i, record in enumerate(pending_records, start=2):
                if record["Tool Name"] == tool_name:
                    pending_sheet.delete_rows(i)
                    break
        
        return jsonify({"message": "Tool status updated successfully!"})
    except Exception as e:
        print("Error modifying tool status:", str(e))
        return jsonify({"error": str(e)}), 500

# Fetch Pending Tools
@app.route('/get-pending-tools', methods=['GET'])
def get_pending_tools():
    try:
        sheet = sh.worksheet("Tools Pending")
        records = sheet.get_all_records()

        # Debugging: Print the API response
        print("Pending Tools Data:", records)

        return jsonify(records if isinstance(records, list) else [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Fetch Tools Inventory for Suggestions
def fetch_tools_inventory():
    sheet = sh.worksheet("Tools Inventory")
    records = sheet.get_all_records()
    return [record["Tool Name"] for record in records if "Tool Name" in record]

@app.route('/get-tools', methods=['GET'])
def get_tools():
    try:
        sheet = sh.worksheet("Tools Inventory")  # Ensure "Tools Inventory" exists in your spreadsheet
        tools = sheet.col_values(1)[1:]  # Get all tool names (skip header)
        return jsonify(tools)
    except Exception as e:
        print("Error fetching tool names:", str(e))
        return jsonify({"error": str(e)}), 500


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
@app.route('/AP-item-stocklist')
def ap_item_stocklist():
    return render_template('ap_item_stocklist.html')

@app.route('/inventory-stock-list')
def inventory_stock_list():
    return render_template('inventory_stock_list.html')

@app.route('/add-inventory')
def add_inventory():
    return render_template('add_inventory.html')

@app.route('/view-low-stock')
def view_low_stock():
    return render_template('view_low_stock.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
