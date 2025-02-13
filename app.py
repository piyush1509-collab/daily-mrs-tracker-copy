import os
import json
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ✅ Load Google API Credentials from Environment Variable (No Change)
CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_FILE = "credentials.json"

if CREDENTIALS_CONTENT:
    try:
        parsed_json = json.loads(CREDENTIALS_CONTENT)
        if "private_key" in parsed_json:
            parsed_json["private_key"] = parsed_json["private_key"].replace("\\n", "\n")

        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(parsed_json, f, indent=4)

        print(f"✅ Credentials file successfully created at {CREDENTIALS_FILE}")

    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
    except Exception as e:
        print(f"❌ Error writing credentials.json: {e}")
else:
    print("❌ GOOGLE_CREDENTIALS_JSON is not set!")

# ✅ Serve Your Original Frontend Page
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Fix: API Route for Item Search
@app.route('/get-items')
def get_items():
    items = ["Item1", "Item2", "Item3", "Item4", "Item5"]  # Replace with actual logic (Google Sheets or Database)
    return jsonify(items)

# ✅ Fix: API Route for Logging Consumption
@app.route('/log-consumption', methods=['POST'])
def log_consumption():
    data = request.json
    item = data.get("item")
    area = data.get("area")
    quantity = data.get("quantity")
    date = data.get("date")

    if not all([item, area, quantity, date]):
        return jsonify({"error": "Missing required fields"}), 400

    # Replace with your actual logic (Save to Google Sheets or Database)
    print(f"Logged Consumption: {item}, {area}, {quantity}, {date}")

    return jsonify({"message": "Consumption logged successfully!"})

# ✅ Ensure Flask Runs Properly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
