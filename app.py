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
def get_consumption_history():
    try:
        sheet = sh.worksheet("Consumption Log")  # Ensure correct sheet name
        records = sheet.get_all_records()

        # Extract query parameters
        area_filter = request.args.get("area", "").strip()
        date_filter = request.args.get("date", "").strip()

        # Filter records based on area & date
        filtered_records = [
            record for record in records
            if (not area_filter or record.get("Consumed Area", "").strip() == area_filter)
            and (not date_filter or record.get("Date", "").strip() == date_filter)
        ]

        return jsonify(filtered_records)
    except Exception as e:
        print("Error fetching consumption history:", str(e))
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
        item_code = data["Item Code"]
        quantity = int(data["Quantity"])

        # Open the Inventory sheet
        inventory_sheet = sh.worksheet("Inventory")
        inventory_data = inventory_sheet.get_all_records()

        # Find the item in Inventory
        for idx, row in enumerate(inventory_data):
            if str(row["Item Code"]) == str(item_code):  # Match item code
                physical_stock = int(row["Physical Stock"])  # Current stock
                minimum_stock = int(row["Minimum Stock"])  # Minimum stock level
                
                # Check if requested quantity is available
                if quantity > physical_stock:
                    return jsonify({"error": "Requested quantity exceeds physical stock!"}), 400
                
                # Deduct quantity from physical stock
                new_stock = max(0, physical_stock - quantity)  # Ensure stock doesn't go negative
                inventory_sheet.update_cell(idx + 2, 3, new_stock)  # Update "Physical Stock" column
                
                # Show warning if stock is below minimum
                if new_stock <= minimum_stock:
                    return jsonify({"warning": f"Stock is low ({new_stock} left)!"})
                
                break

        # Log the consumption in Consumption Log
        log_sheet = sh.worksheet("Consumption Log")
        log_entry = [data["Date"], data["Item Name"], item_code, quantity, data["Unit"], data["Consumed Area"], data["Shift"]]
        log_sheet.append_row(log_entry)

        return jsonify({"message": "Consumption logged successfully!"})
    except Exception as e:
        print("Error logging consumption:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/AP-item-stocklist')
def ap_item_stocklist():
    return render_template('AP-item-stocklist')

@app.route('/inventory-stock-list')
def inventory_stock_list():
    return render_template('inventory_stock_list.html')

@app.route('/add-inventory')
def add_inventory():
    return render_template('add_inventory.html')

@app.route('/view-low-stock')
def view_low_stock():
    return render_template('view_low_stock.html')
@app.route('/new-area-wise-consumption', methods=['GET'])
def new_area_wise_consumption():
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()

        records = consumption_sheet.get_all_records()
        filtered_records = []

        for record in records:
            record_date = record.get("Date", "").strip()
            if start_date <= record_date <= end_date:
                filtered_records.append(record)

        # Group by Area and Sum Consumption
        consumption_data = {}
        for record in filtered_records:
            area = record.get("Consumed Area", "").strip()
            quantity = int(record.get("Quantity", 0))

            if area in consumption_data:
                consumption_data[area] += quantity
            else:
                consumption_data[area] = quantity

        return jsonify(consumption_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/area-wise-consumption', methods=['GET'])
def area_wise_consumption():
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        item_filter = request.args.get('item', '').strip().lower()

        records = consumption_sheet.get_all_records()
        consumption_data = {}

        for record in records:
            record_date = record.get("Date", "").strip()
            if start_date <= record_date <= end_date:
                area = record.get("Consumed Area", "").strip()
                quantity = int(record.get("Quantity", 0))

                # If searching by item name, filter it
                item_name = record.get("Item Name", "").strip().lower()
                if item_filter and item_filter not in item_name:
                    continue  

                if area in consumption_data:
                    consumption_data[area] += quantity
                else:
                    consumption_data[area] = quantity

        return jsonify(consumption_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/get-inventory', methods=['GET'])
def get_inventory():
    try:
        sheet = sh.worksheet("Inventory")  # Ensure sheet name is correct
        inventory_data = sheet.get_all_records()

        return jsonify(inventory_data)
    except Exception as e:
        print("Error fetching inventory:", str(e))
        return jsonify({"error": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
