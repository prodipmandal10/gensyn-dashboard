import streamlit as st
import requests
import datetime
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===== Google Sheet Setup =====
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1ZBVcS3dEwbXt_rA1yCJdGMiYWEqNdl12C3mbzXyUG28'  # ✅ Your Sheet ID
SHEET_NAME = 'Sheet1'

# ===== Google Auth from Streamlit Secrets =====
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)
sheet = sheet_service.spreadsheets()

# ===== Peer Storage =====
if "user_peers" not in st.session_state:
    st.session_state.user_peers = {}
if "peer_data" not in st.session_state:
    st.session_state.peer_data = {}
if "peer_last_win" not in st.session_state:
    st.session_state.peer_last_win = {}

# ===== Functions =====
def fetch_peer_info(pid):
    try:
        url = f"https://dashboard.gensyn.ai/api/v1/peer?id={pid}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {
                "peerName": d.get("peerName", "N/A"),
                "wins": d.get("score", 0),
                "reward": d.get("reward", 0)
            }
    except:
        return None

def append_to_sheet(values):
    try:
        body = {'values': [values]}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
    except Exception as e:
        st.error(f"Sheet Write Error: {e}")

# ===== UI =====
st.title("📊 Gensyn Peer Tracker (Web)")
st.markdown("Track your Peer wins, rewards and live status synced to Google Sheets.")

# User select or input
username = st.text_input("Enter your username", key="username")
if username and username not in st.session_state.user_peers:
    st.session_state.user_peers[username] = []

# Peer Add
if username:
    peer_input = st.text_input("Add Peer IDs (space separated)")
    if st.button("Add Peer IDs"):
        new_peers = peer_input.strip().split()
        for pid in new_peers:
            if pid not in st.session_state.user_peers[username]:
                st.session_state.user_peers[username].append(pid)
        st.success(f"Added {len(new_peers)} peers to {username}")

# Display Table
if username and st.session_state.user_peers.get(username):
    st.subheader("Your Peer Status")
    data_rows = []
    for pid in st.session_state.user_peers[username]:
        info = fetch_peer_info(pid)
        if info:
            old = st.session_state.peer_data.get(pid, {}).get("wins", 0)
            new = info.get("wins", 0)
            # If win increased
            if new > old:
                append_to_sheet([
                    username, pid, info['peerName'],
                    old, new, info['reward'],
                    datetime.datetime.now().isoformat()
                ])
            st.session_state.peer_data[pid] = info
            st.session_state.peer_last_win[pid] = datetime.datetime.now()
            data_rows.append({
                "Peer ID": pid,
                "Name": info['peerName'],
                "Wins": info['wins'],
                "Reward": info['reward']
            })
    if data_rows:
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No peer data available.")

# 1HR Filter
if st.button("✅ 1HR Win Status"):
    st.subheader("Last 1HR Winners")
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
    found = False
    for pid, info in st.session_state.peer_data.items():
        last = st.session_state.peer_last_win.get(pid)
        if last and last > cutoff:
            st.write(f"{pid[-6:]} - {info['wins']} wins")
            found = True
    if not found:
        st.info("No peer has won in last 1 hour.")

# 2HR Inactive
if st.button("🛑 2HR Stop List"):
    st.subheader("No Wins in Last 2 Hours")
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=2)
    found = False
    for pid, info in st.session_state.peer_data.items():
        last = st.session_state.peer_last_win.get(pid)
        if not last or last < cutoff:
            st.write(f"{pid[-6:]} - {info['wins']} wins")
            found = True
    if not found:
        st.info("No peers are inactive.")
