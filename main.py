from fastapi import FastAPI, UploadFile, File
from typing import List
import chess.pgn
import io
from pymongo import MongoClient

app = FastAPI(title="Chanua Chess API")

# Connect to local MongoDB instance
# (Ensure your MongoDB Community Server service is running on your machine)
client = MongoClient("mongodb://localhost:27017/")
db = client["timodb1"]
games_collection = db["ChessPGNs"]

@app.get("/")
def root():
    return {"status": "API is online", "project": "Chanua Chess Backend"}


@app.post("/upload-pgn/")
# Notice we changed 'file' to 'files' and added 'List'
async def upload_pgn(files: List[UploadFile] = File(...)):
    total_games_parsed = 0
    
    # Loop through every file uploaded
    for file in files:
        contents = await file.read()
        pgn_text = contents.decode("utf-8")
        pgn_io = io.StringIO(pgn_text)
        
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break # Moves to the next file when the current one is done
                
            headers = dict(game.headers)
            
            game_url = headers.get("Site", "")
            game_id = game_url.split("/")[-1] if game_url else f"generated_{total_games_parsed}"
            
            headers["_id"] = game_id  
            
            games_collection.update_one({"_id": game_id}, {"$set": headers}, upsert=True)
            total_games_parsed += 1
            
    return {"status": "success", "games_parsed": total_games_parsed}

@app.get("/games/")
def get_all_games():
    # Retrieve all records from the collection
    games = list(games_collection.find())
    return {"games": games}