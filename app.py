import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
import datetime

st.set_page_config(page_title="Gensyn Peer Tracker", layout="wide")

st.title("🚀 Gensyn Peer Tracker Web Dashboard")

# ================= Google Sheets Setup =================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Streamlit Secrets থেকে Credentials নিয়ে আসা
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

client = gspread.authorize(creds)

SHEET_ID = '1ZBVcGNRqsH3gPy1ZS8P3CN04Hr9iFsrTm0p2dLPXk-g'
sheet = client.open_by_key(SHEET_ID).worksheet('Sheet1')

# ================= UI =================

# ইউজার তালিকা লোড করা
def load_users():
    users = []
    try:
        all_records = sheet.get_all_records()
        for row in all_records:
            username = row.get("Username")
            if username:
                users.append(username)
    except Exception as e:
        st.error(f"Google Sheets error: {e}")
    return users

users = load_users()

selected_user = st.selectbox("Select User", options=users)

peer_ids = []
if selected_user:
    try:
        all_records = sheet.get_all_records()
        for row in all_records:
            if row.get("Username") == selected_user:
                # Peers start from 4th column onwards
                for key, val in row.items():
                    if key not in ["Username", "Status", "Last Update"]:
                        if val and val.strip():
                            peer_ids.append(val.strip())
    except Exception as e:
        st.error(f"Error loading peers: {e}")

st.write(f"### Peer IDs for User: {selected_user}")
st.write(peer_ids if peer_ids else "No Peer IDs found.")

# ================= Peer Info Fetch =================

def fetch_peer_info(peer_id):
    url = f"https://dashboard.gensyn.ai/api/v1/peer?id={peer_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "peerName": data.get("peerName", "N/A"),
                "wins": data.get("score", 0),
                "reward": data.get("reward", 0),
                "peerId": peer_id
            }
        else:
            return None
    except Exception as e:
        return None

if st.button("Refresh Peer Data"):
    st.write("Fetching peer data...")
    data_rows = []
    for pid in peer_ids:
        info = fetch_peer_info(pid)
        if info:
            data_rows.append(info)
    if data_rows:
        st.write("### Peer Data")
        st.table(data_rows)
    else:
        st.warning("No data fetched.")

# ================= Status Bar =================

st.sidebar.header("App Status")
st.sidebar.write("Select a user to see their peers.")
st.sidebar.write(f"Total Users: {len(users)}")

