import random
import time

games = {}

def create_game(chat_id):
    games[chat_id] = {
        "players": [],
        "status": "waiting",
        "scores": {},
        "current_batter": None,
        "current_bowler": None,
        "bowling_number": None,
        "start_time": time.time()
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
        "runs": 0,
        "balls": 0,
        "fours": 0,
        "sixes": 0,
        "history": []
    })
    return True

def start_match(chat_id):
    game = games[chat_id]
    game["status"] = "playing"

    players = game["players"]
    game["current_batter"] = players[0]
    game["current_bowler"] = players[1] if len(players) > 1 else players[0]

def set_bowling(chat_id, number):
    games[chat_id]["bowling_number"] = number

def play_ball(chat_id, bat_number):
    game = games[chat_id]
    bow = game["bowling_number"]
    batter = game["current_batter"]

    result = {}

    if bat_number == bow:
        batter["balls"] += 1
        batter["history"].append("W")
        result["type"] = "out"
    else:
        batter["runs"] += bat_number
        batter["balls"] += 1
        batter["history"].append(bat_number)

        if bat_number == 4:
            batter["fours"] += 1
        if bat_number == 6:
            batter["sixes"] += 1

        result["type"] = "run"
        result["runs"] = bat_number

    return result
