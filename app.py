import os
import json
from flask import Flask

app = Flask(__name__)

CREDENTIALS_CONTENT = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_FILE = "credentials.json"

if CREDENTIALS_CONTENT:
    try:
        # Convert JSON string to dictionary
        parsed_json = json.loads(CREDENTIALS_CONTENT)

        # Fix private key formatting
        if "private_key" in parsed_json:
            parsed_json["private_key"] = parsed_json["private_key"].replace("\\n", "\n")

        # Write to credentials.json file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(parsed_json, f, indent=4)

        print(f"✅ Credentials file successfully created at {CREDENTIALS_FILE}")

    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
    except Exception as e:
        print(f"❌ Error writing credentials.json: {e}")
else:
    print("❌ GOOGLE_CREDENTIALS_JSON is not set! Make sure the environment variable is configured.")

@app.route('/')
def home():
    return "✅ Flask App Running Successfully!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

