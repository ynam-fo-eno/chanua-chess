from fastapi import FastAPI, UploadFile, File, Query
from typing import List
import chess.pgn
import io
import os
import uuid
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Chanua Chess API")

# Connect to MongoDB via Environment Variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Add robust fallback parameters if it is an Atlas link to clear SSL/TLS handshake alerts
if "mongodb+srv" in MONGO_URI:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
        retryWrites=True,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
else:
    # Standard fallback configuration for local machine development
    client = MongoClient(MONGO_URI)

db = client["timo_db_1"]  
games_collection = db["ChessPGNs"]

@app.get("/")
def root():
    return {"status": "API is online", "project": "Chanua Chess Backend"}


@app.post("/upload-pgn/")
async def upload_pgn(files: List[UploadFile] = File(...)):
    total_games_parsed = 0
    
    for file in files:
        contents = await file.read()
        pgn_text = contents.decode("utf-8")
        pgn_io = io.StringIO(pgn_text)
        
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
                
            headers = dict(game.headers)
            headers["moves"] = str(game.mainline_moves())
            
            # Robust unique ID check to handle games that lack standard Lichess URLs
            game_url = headers.get("Site", "")
            if game_url and "/" in game_url:
                game_id = game_url.split("/")[-1]
            else:
                game_id = str(uuid.uuid4())
            
            headers["_id"] = game_id  
            
            # Upsert into collection cleanly
            games_collection.update_one({"_id": game_id}, {"$set": headers}, upsert=True)
            total_games_parsed += 1
            
    return {"status": "success", "games_parsed": total_games_parsed}


@app.get("/games/")
def get_all_games():
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
    mongo_sort = -1 if sort == "Newest First" else 1
    cursor = games_collection.find().sort("Date", mongo_sort).skip(skip).limit(limit)
    
    games = []
    for game in cursor:
        game["_id"] = str(game["_id"])
        games.append(game)
        
    return games