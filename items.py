import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")

if not CREDENTIALS_FILE:
    print("Error: GOOGLE_CREDENTIALS_PATH not set")
else:
    print(f"Using credentials from: {CREDENTIALS_FILE}")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_key("1cVeYNtdjZxkofyMrJwsys1YEWfd6W3bFAdXHmWtLl7g")  # Your Google Sheet ID
        print("Connected to Google Sheets successfully!")
    except Exception as e:
        print(f"Error: {e}")


