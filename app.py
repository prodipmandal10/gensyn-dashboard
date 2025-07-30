import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheet setup
JSON_KEY_FILE = 'sonic-base-458507-a2-3c235152e55a.json'
SHEET_ID = '1ZBVcGNRqsH3gPy1ZS8P3CN04Hr9iFsrTm0p2dLPXk-g'
SHEET_NAME = 'Sheet1'

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Streamlit UI
st.title("🧠 Gensyn Peer Tracker Web Dashboard")

peer_id = st.text_input("Enter Peer ID")
if st.button("Check Peer Status"):
    url = f"https://dashboard.gensyn.ai/api/v1/peer?id={peer_id}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"Peer Name: {data.get('peerName')}")
            st.info(f"Wins: {data.get('score')} | Reward: {data.get('reward')}")
        else:
            st.error("Failed to fetch peer info.")
    except Exception as e:
        st.error(f"Error: {e}")
