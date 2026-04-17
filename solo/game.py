# solo/game.py - Final Version

import time

games = {}

def create_game(chat_id):
    games[chat_id] = {
        "players": [],
        "status": "waiting",
        "mode": None,
        "current_batter": None,
        "current_bowler": None,
        "bowling_number": None,
        "start_time": time.time(),
        "game_over": False,
        "winner": None
    }

def join_game(chat_id, user):
    game = games.get(chat_id)
    if not game:
        return False
    
    if user.id in [p["id"] for p in game["players"]]:
        return False

    game["players"].append({
        "id": user.id,
        "name": user.first_name,
        "username": user.username,
        "score": 0,  # Using 'score' instead of 'runs'
        "balls": 0,
        "fours": 0,
        "sixes": 0,
        "out": False,
        "history": []
    })
    return True

def start_match(chat_id):
    game = games[chat_id]
    game["status"] = "playing"
    game["game_over"] = False

    players = game["players"]
    if len(players) > 0:
        game["current_batter"] = players[0].copy()
        game["current_bowler"] = players[1].copy() if len(players) > 1 else players[0].copy()

def set_bowling(chat_id, number):
    if chat_id in games:
        games[chat_id]["bowling_number"] = number

def play_ball(chat_id, bat_number):
    game = games.get(chat_id)
    if not game or game["status"] != "playing":
        return {"type": "error", "message": "Game not active"}
    
    bow = game.get("bowling_number")
    if bow is None:
        return {"type": "error", "message": "Bowling number not set"}
    
    # Find current batter in players list
    batter = None
    batter_index = None
    for i, player in enumerate(game["players"]):
        if player["id"] == game["current_batter"]["id"]:
            batter = player
            batter_index = i
            break
    
    if not batter:
        return {"type": "error", "message": "Batter not found"}
    
    result = {}

    # Check for OUT
    if bat_number == bow:
        batter["balls"] += 1
        batter["history"].append("W")
        batter["out"] = True
        result["type"] = "out"
        result["runs"] = 0
        
        # Check if game is over (all players out)
        active_players = [p for p in game["players"] if not p.get("out", False)]
        if len(active_players) == 0:
            # Find winner (player with highest score)
            winner = max(game["players"], key=lambda x: x.get("score", 0))
            game["game_over"] = True
            game["winner"] = winner
    else:
        # Runs scored
        runs = bat_number
        batter["score"] = batter.get("score", 0) + runs
        batter["balls"] += 1
        batter["history"].append(bat_number)

        if bat_number == 4:
            batter["fours"] = batter.get("fours", 0) + 1
        if bat_number == 6:
            batter["sixes"] = batter.get("sixes", 0) + 1

        result["type"] = "run"
        result["runs"] = runs
    
    # Update current batter in game
    game["current_batter"] = batter.copy()
    
    return result

def get_game(chat_id):
    return games.get(chat_id)
