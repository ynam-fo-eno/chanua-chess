import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Chanua Chess Dashboard", layout="wide")
st.title("漏 Chanua Chess Performance Dashboard")

# Address pointing to your local FastAPI server instance
BACKEND_URL = "http://127.0.0.1:8000"

# --- Section 1: Data Syncing ---
# --- Section 1: Data Syncing ---
st.header("1. Sync Data Store")

# Add accept_multiple_files=True
uploaded_files = st.file_uploader("Select your Lichess Bullet PGN chunks", type=["pgn"], accept_multiple_files=True)

# Check if the list is not empty
if uploaded_files:
    if st.button("Process & Load into MongoDB"):
        with st.spinner(f"Transmitting {len(uploaded_files)} files to API for extraction..."):
            
            # Package all uploaded files into a list format requests can send
            files_payload = [
                ("files", (file.name, file.getvalue(), "text/plain")) 
                for file in uploaded_files
            ]
            
            try:
                response = requests.post(f"{BACKEND_URL}/upload-pgn/", files=files_payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Success! Processed and synced {data['games_parsed']} games across {len(uploaded_files)} files to MongoDB.")
                else:
                    st.error("Error processing files via API.")
            except requests.exceptions.ConnectionError:
                st.error("Connection failed. Is the FastAPI server running?")

# --- Section 2: Data Visualizations ---
st.write("---")
st.header("2. Analytical Reporting")

if st.button("Fetch Current Metrics"):
    with st.spinner("Querying database records..."):
        try:
            response = requests.get(f"{BACKEND_URL}/games/")
            if response.status_code == 200:
                games_list = response.json().get("games", [])
                
                if games_list:
                    # Convert raw JSON records into a structural pandas DataFrame
                    df = pd.DataFrame(games_list)
                    
                    # Highlight high-level metadata
                    total_games = len(df)
                    st.metric(label="Total Bullet Games Recorded", value=total_games)
                    
                    st.subheader("Recent Game Ledger")
                    # Dynamically slice relevant structural columns for view
                    display_cols = [col for col in ["Date", "White", "Black", "Result", "TimeControl"] if col in df.columns]
                    st.dataframe(df[display_cols].tail(15))
                else:
                    st.warning("Database repository is currently empty. Run a sync step above.")
            else:
                st.error("API error encountered during database read.")
        except requests.exceptions.ConnectionError:
            st.error("Unable to query records. Ensure your backend server is active.")