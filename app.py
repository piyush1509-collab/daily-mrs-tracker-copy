from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__, template_folder='.')

file_path = os.path.join(os.getcwd(), "static", "items.xlsx")

def ensure_file():
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Item Code", "Item Name", "Consumed Area", "Date", "Quantity", "Shift"])
        df.to_excel(file_path, sheet_name="Consumption Log", index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_items', methods=['GET'])
def get_items():
    try:
        df = pd.read_excel(file_path, sheet_name="Master List")
        items = df[['Item Code', 'Item Name']].dropna().to_dict(orient='records')
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/consume', methods=['POST'])
def consume_item():
    """Log consumed item and update 'Consumption Log' in items.xlsx."""
    try:
        data = request.json
        print(f"📥 Received Data: {data}")  # Debugging

        if not data or not all(k in data for k in ['item_code', 'consumed_area', 'date', 'quantity', 'shift']):
            print("❌ Error: Missing required fields!")  # Debugging
            return jsonify({"error": "Missing required fields!"}), 400

        item_code = str(data['item_code']).strip()
        consumed_area = data['consumed_area']
        consumption_date = data['date']
        quantity = data['quantity']
        shift = data['shift']

        if not item_code:
            print("❌ Error: Item Code is missing!")  # Debugging
            return jsonify({"error": "Item Code is required!"}), 400

        if not quantity.isdigit():
            print("❌ Error: Invalid Quantity!")  # Debugging
            return jsonify({"error": "Quantity must be a valid number!"}), 400

        # Load Master List to get Item Name
        df_items = pd.read_excel(file_path, sheet_name="Master List")
        df_items['Item Code'] = df_items['Item Code'].astype(str).str.strip()
        item_row = df_items[df_items['Item Code'] == item_code]

        if item_row.empty:
            print("❌ Error: Item not found in Master List!")  # Debugging
            return jsonify({"error": "Item not found!"}), 404

        # Load or Create "Consumption Log"
        try:
            df_log = pd.read_excel(file_path, sheet_name="Consumption Log")
        except Exception:
            print("⚠️ Warning: 'Consumption Log' sheet not found, creating a new one.")
            df_log = pd.DataFrame(columns=["Item Code", "Item Name", "Consumed Area", "Date", "Quantity", "Shift"])

        # Add New Entry
        new_entry = {
            "Item Code": item_code,
            "Item Name": item_row.iloc[0]["Item Name"],
            "Consumed Area": consumed_area,
            "Date": consumption_date,
            "Quantity": int(quantity),
            "Shift": shift
        }
        df_log = pd.concat([df_log, pd.DataFrame([new_entry])], ignore_index=True)

        # Save Back to "Consumption Log"
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_log.to_excel(writer, sheet_name="Consumption Log", index=False)

        print("✅ Consumption Logged Successfully!")  # Debugging
        return jsonify({"message": "Consumption logged successfully!"})
    
    except Exception as e:
        print(f"❌ Error in consume_item: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500





if __name__ == '__main__':
    ensure_file()
    app.run(debug=True)
