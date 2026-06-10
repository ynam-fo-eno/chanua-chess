from fastapi import FastAPI, UploadFile, File, Query
from typing import List
import chess.pgn
import io
import os
from pymongo import MongoClient

app = FastAPI(title="Chanua Chess API")

# Connect to local MongoDB instance
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)


db = client["timo_db_1"]  
games_collection = db["ChessPGNs"]

@app.get("/")
def root():
    return {"status": "API is online", "project": "Chanua Chess Backend"}


@app.post("/upload-pgn/")
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
                break  # Moves to the next file when the current one is done
                
            headers = dict(game.headers)

            headers["moves"] = str(game.mainline_moves())
            game_url = headers.get("Site", "")
            game_id = game_url.split("/")[-1] if game_url else f"generated_{total_games_parsed}"
            
            headers["_id"] = game_id  
            
            games_collection.update_one({"_id": game_id}, {"$set": headers}, upsert=True)
            total_games_parsed += 1
            
    return {"status": "success", "games_parsed": total_games_parsed}


@app.get("/games/")
def get_all_games():
    # Retrieve all records from the collection and clean IDs for JSON compliance
    cursor = games_collection.find()
    games = []
    for game in cursor:
        game["_id"] = str(game["_id"])
        games.append(game)
    return {"games": games}


@app.get("/recent-games")
def get_recent_games(
    limit: int = Query(50), 
    sort: str = Query("Newest First"),
    skip: int = Query(0)
):
    # -1 tells Mongo to sort descending (newest), 1 sorts ascending (oldest)
    mongo_sort = -1 if sort == "Newest First" else 1
    
    # Query, sort by Lichess PGN Date field, and apply the limit directly to the database cursor
    cursor = games_collection.find().sort("Date", mongo_sort).skip(skip).limit(limit)
    
    games = []
    for game in cursor:
        game["_id"] = str(game["_id"])
        games.append(game)
        
    return games