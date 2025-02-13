import os
import json
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ✅ Fix: Load Google API Credentials from Environment Variable
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
    print("❌ GOOGLE_CREDENTIALS_JSON is not set! Make sure the environment variable is configured.")

# ✅ Fix: Serve Frontend Page
@app.route('/')
def home():
    return render_template('index.html')

# ✅ API: Fetch Item Names (Replace with actual logic)
@app.route('/get-items')
def get_items():
    items = ["Item1", "Item2", "Item3", "Item4", "Item5"]  # Replace with database/Google Sheets logic
    return jsonify(items)

# ✅ API: Fetch Consumption History (Replace with actual logic)
@app.route('/consumption_history')
def consumption_history():
    history = [
        {"item": "Item1", "area": "GASZONE", "date": "2025-02-13", "quantity": 5},
        {"item": "Item2", "area": "UTILITY", "date": "2025-02-12", "quantity": 3},
    ]  # Replace with actual logic
    return jsonify(history)

# ✅ Fix: Run Flask Properly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

