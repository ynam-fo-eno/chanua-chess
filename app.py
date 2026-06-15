import streamlit as st
import requests
import pandas as pd

# 1. Initialize State Tracking for Navigation
if "selected_game" not in st.session_state:
    st.session_state.selected_game = None

if "current_page" not in st.session_state:
    st.session_state.current_page = 0  # Page 0 is the first page

# Global Page Settings
st.set_page_config(page_title="Chanua Chess Dashboard", layout="wide")
BACKEND_URL = "https://otanimnaynek-chanua-chess-api.hf.space"


# ==========================================
# PAGE ROUTE A: SCORESHEET VIEW
# ==========================================
if st.session_state.selected_game is not None:
    game = st.session_state.selected_game
    
    # Back navigation button
    if st.button("⬅ Back to Ledger!"):
        st.session_state.selected_game = None
        st.rerun()
        
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #FFD700;'>📜 OFFICIAL CHESS SCORESHEET</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Metadata Header Card Look
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown(f"#### ⚪ White: **{game.get('White', 'Unknown')}**")
        st.markdown(f"🏆 Rating: `{game.get('WhiteElo', '?')}`")
        st.markdown(f"📅 Date: `{game.get('Date', 'N/A')}`")
        st.markdown(f"📍 Event: *{game.get('Event', 'Lichess Match')}*")
    with meta_col2:
        st.markdown(f"#### ⚫ Black: **{game.get('Black', 'Unknown')}**")
        st.markdown(f"🏆 Rating: `{game.get('BlackElo', '?')}`")
        st.markdown(f"📊 Result: <span style='color: #00ff00; font-weight: bold; font-size: 20px;'>{game.get('Result', '*')}</span>", unsafe_allow_html=True)
        st.markdown(f"⏱️ Time Control: `{game.get('TimeControl', 'N/A')}`")
        
    st.markdown("---")
    st.subheader("Move Log Notation")
    
    raw_moves = game.get("moves", "")
    if raw_moves:
        tokens = raw_moves.split()
        grid_col1, grid_col2 = st.columns(2)
        
        # Split layout into two parallel text panels to reduce screen scrolling
        halfway_point = len(tokens) // 2
        
        with grid_col1:
            st.markdown("**Move # | White | Black**")
            st.markdown("---")
            for i in range(0, min(halfway_point, len(tokens)), 3):
                if i < len(tokens):
                    move_num = tokens[i]
                    w_move = tokens[i+1] if i+1 < len(tokens) else ""
                    b_move = tokens[i+2] if i+2 < len(tokens) else ""
                    st.markdown(f"`{move_num}` **{w_move}** | {b_move}")
                
        with grid_col2:
            st.markdown("**Move # | White | Black**")
            st.markdown("---")
            # Continue the second half of the game moves in column 2
            start_index = halfway_point - (halfway_point % 3)
            for i in range(max(start_index, 3), len(tokens), 3):
                if i < len(tokens):
                    move_num = tokens[i]
                    w_move = tokens[i+1] if i+1 < len(tokens) else ""
                    b_move = tokens[i+2] if i+2 < len(tokens) else ""
                    st.markdown(f"`{move_num}` **{w_move}** | {b_move}")
    else:
        st.info("No inline notation logs found for this specific game entry. Ensure your backend parses game.mainline_moves().")


# ==========================================
# PAGE ROUTE B: MAIN LEDGER DASHBOARD
# ==========================================
else:
    st.title("🫗 Chanua Chess Performance Dashboard")
    
    # --- Section 1: Data Syncing ---
    st.header("1. Sync Data Store")
    uploaded_files = st.file_uploader("Select your Lichess Bullet PGN chunks", type=["pgn"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Process & Load into MongoDB"):
            with st.spinner(f"Transmitting {len(uploaded_files)} files to API for extraction..."):
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
                        st.error(f"Error processing files via API. Server returned status code: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("Connection failed. Is the FastAPI server running?")

    st.write("---")
    
    # 2. Analytical Reporting
    st.header("2. Analytical Reporting")

    if st.button("Fetch All Stored Games"):
        with st.spinner("Quarrying MongoDB Atlas cloud..."):
            try:
                response = requests.get(f"{BACKEND_URL}/games/")
                if response.status_code == 200:
                    data = response.json()
                    games_list = data.get("games", [])
                    
                    if games_list:
                        st.success(f"Found {len(games_list)} games in the cluster!")
                        df = pd.DataFrame(games_list)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("The database is completely empty. Sync some PGN chunks first!")
                else:
                    st.error(f"Failed to connect. HTTP Status Code: {response.status_code}")
            except Exception as e:
                st.error(f"Connection framework engine failed: {e}")
                
    st.write("---")

    # --- Section 3: Interactive Ledger & Improved Rendering Loop ---
    st.header("3. Game Ledger Interface")
    
    def reset_page():
        st.session_state.current_page = 0

    # Dynamic Query Controls
    ctrl_col1, ctrl_col2 = st.columns(2)
    with ctrl_col1:
        sort_order = st.selectbox("Order By Date", ["Newest First", "Oldest First"], on_change=reset_page)
    with ctrl_col2:
        game_limit = st.slider("Games per Page", min_value=10, max_value=100, value=20, step=10, on_change=reset_page)

    # Calculate how many records MongoDB should skip over
    skip_value = st.session_state.current_page * game_limit

    # Execute dynamic sorted API request with pagination params
    try:
        ledger_res = requests.get(f"{BACKEND_URL}/recent-games?limit={game_limit}&sort={sort_order}&skip={skip_value}")
        if ledger_res.status_code == 200:
            recent_games_list = ledger_res.json()
            
            if recent_games_list:
                # Generate clean table headers using layout columns
                header_cols = st.columns([2, 3, 3, 2, 2, 2])
                header_cols[0].markdown("**Date**")
                header_cols[1].markdown("**⚪ White**")
                header_cols[2].markdown("**⚫ Black**")
                header_cols[3].markdown("**Result**")
                header_cols[4].markdown("**Time**")
                header_cols[5].markdown("**Action**")
                st.markdown("<hr style='margin: 5px 0px;' />", unsafe_allow_html=True)
                
                # Loop through each game item
                for game_item in recent_games_list:
                    row_cols = st.columns([2, 3, 3, 2, 2, 2])
                    row_cols[0].write(game_item.get("Date", "N/A"))
                    row_cols[1].write(game_item.get("White", "Unknown"))
                    row_cols[2].write(game_item.get("Black", "Unknown"))
                    row_cols[3].write(game_item.get("Result", "*"))
                    row_cols[4].write(game_item.get("TimeControl", "N/A"))
                    
                    if row_cols[5].button("View Sheet", key=f"btn_{game_item.get('_id')}"):
                        st.session_state.selected_game = game_item
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- PAGINATION BUTTON INTERFACE ---
                pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])
                
                with pag_col1:
                    if st.session_state.current_page > 0:
                        if st.button("⬅️ Previous Page"):
                            st.session_state.current_page -= 1
                            st.rerun()
                            
                with pag_col2:
                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>Viewing Page {st.session_state.current_page + 1}</p>", unsafe_allow_html=True)
                    
                with pag_col3:
                    if len(recent_games_list) == game_limit:
                        if st.button("Next Page ➡️"):
                            st.session_state.current_page += 1
                            st.rerun()
            else:
                st.warning("No records found matching current query configurations.")
                if st.session_state.current_page > 0:
                    if st.button("Return to Page 1"):
                        reset_page()
                        st.rerun()
        else:
            st.error("API error reading recent records endpoint.")
    except requests.exceptions.ConnectionError:
        st.error("Unable to stream live game database cursor elements.")