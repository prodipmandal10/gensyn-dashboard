import streamlit as st
import requests
import datetime
import time
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ====== GOOGLE SHEET SETUP ======
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = "1ZBVc2S0xO1QvZahGJ7ZIn8GpQqkNnJ2I2Mck8zVnHAY"  # ✅ আপনার Sheet ID এখানেই বসানো
SHEET_NAME = "Sheet1"

# Authenticate with secrets.toml
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)
sheet = sheet_service.spreadsheets()

# ====== GLOBAL STATE ======
if "user_peers" not in st.session_state:
    st.session_state.user_peers = {}

if "peer_data" not in st.session_state:
    st.session_state.peer_data = {}

if "last_win_time" not in st.session_state:
    st.session_state.last_win_time = {}

# ====== FUNCTIONS ======

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
        st.error(f"❌ Google Sheet Error: {e}")

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
        pass
    return None

def monitor_peers(user):
    st.toast("🔄 Monitoring started...", icon="🔍")
    stop_time = time.time() + 60 * 5  # Run for 5 minutes max or until stopped manually
    while time.time() < stop_time:
        for pid in st.session_state.user_peers.get(user, []):
            info = fetch_peer_info(pid)
            if info:
                old_wins = st.session_state.peer_data.get(pid, {}).get("wins", 0)
                new_wins = info.get("wins", 0)

                if new_wins > old_wins:
                    timestamp = datetime.datetime.now().isoformat()
                    append_to_sheet([
                        user, pid, info['peerName'], old_wins, new_wins,
                        info['reward'], timestamp
                    ])
                    st.success(f"🎉 Win Detected! {pid[-6:]} - {new_wins} wins")
                st.session_state.peer_data[pid] = info
                st.session_state.last_win_time[pid] = datetime.datetime.now()
        time.sleep(30)

# ====== UI ======

st.title("📊 Gensyn Peer Tracker (Streamlit)")

# User Input
user = st.text_input("Enter your User Name")
if user and user not in st.session_state.user_peers:
    st.session_state.user_peers[user] = []

peer_input = st.text_area("Add Peer IDs (space-separated)")
if st.button("➕ Add Peer IDs"):
    if user:
        new_ids = peer_input.strip().split()
        st.session_state.user_peers[user].extend(pid for pid in new_ids if pid not in st.session_state.user_peers[user])
        st.success(f"{len(new_ids)} peer IDs added.")
    else:
        st.warning("Please enter user name first.")

# Display Peers
if user:
    st.subheader(f"🔍 Peers for {user}")
    peer_list = st.session_state.user_peers.get(user, [])
    for pid in peer_list:
        data = st.session_state.peer_data.get(pid, {})
        st.write(f"• {pid} | Name: {data.get('peerName','-')} | Wins: {data.get('wins','-')} | Reward: {data.get('reward','-')}")

# Start Monitoring
if st.button("▶️ Start Monitoring"):
    if user and st.session_state.user_peers.get(user):
        monitor_peers(user)
    else:
        st.error("Please add at least one peer ID.")

# Check status last 1hr
if st.button("🕐 View 1 Hour Status"):
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
    result = ""
    for u, plist in st.session_state.user_peers.items():
        for pid in plist:
            info = st.session_state.peer_data.get(pid)
            last = st.session_state.last_win_time.get(pid)
            if info and last and last > cutoff:
                result += f"{u} - {pid[-6:]} - {info['wins']} wins\n"
    st.text_area("1 Hour Active Peers", result or "No peers with wins in last 1 hour.")

# Check Stopped Peers
if st.button("⛔ View 2 Hour Stop List"):
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=2)
    stopped = ""
    for u, plist in st.session_state.user_peers.items():
        for pid in plist:
            last = st.session_state.last_win_time.get(pid)
            info = st.session_state.peer_data.get(pid)
            if info and (not last or last < cutoff):
                stopped += f"{u} - {pid[-6:]} - {info['wins']} wins\n"
    st.text_area("Stopped Peers (2hr+)", stopped or "No stopped peers.")
