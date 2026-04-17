# solo/game.py - Unlimited Players

import time

games = {}

def create_game(chat_id):
    games[chat_id] = {
        "players": [],
        "status": "waiting",
        "mode": None,
        "ball_mode": None,  # 1 or 3 balls
        "current_batter": None,
        "current_bowler": None,
        "bowling_number": None,
        "start_time": time.time(),
        "game_over": False,
        "winner": None,
        "current_bowler_balls": 0,
        "total_balls_in_match": 0,
        "current_batter_index": 0,
        "current_bowler_index": 0
    }

def join_game(chat_id, user):
    game = games.get(chat_id)
    if not game:
        return False
    
    # Check if already joined
    if user.id in [p["id"] for p in game["players"]]:
        return False

    game["players"].append({
        "id": user.id,
        "name": user.first_name,
        "username": user.username,
        "score": 0,
        "balls": 0,
        "fours": 0,
        "sixes": 0,
        "out": False,
        "history": []
    })
    return True

def start_match(chat_id):
    game = games.get(chat_id)
    if not game:
        return
    
    game["status"] = "playing"
    game["game_over"] = False
    game["current_bowler_balls"] = 0
    game["total_balls_in_match"] = 0
    
    players = game["players"]
    
    if len(players) > 0:
        game["current_batter"] = players[0].copy()
        game["current_batter_index"] = 0
        
        bowler_index = 1 if len(players) > 1 else 0
        game["current_bowler"] = players[bowler_index].copy()
        game["current_bowler_index"] = bowler_index

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
    
    # Find current batter
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
    is_out = (bat_number == bow)
    
    if is_out:
        # BATTER IS OUT
        batter["balls"] += 1
        batter["history"].append("W")
        batter["out"] = True
        result["type"] = "out"
        result["runs"] = 0
        
        # Find next batter who is not out
        next_batter_index = find_next_batter(game["players"], batter_index)
        
        if next_batter_index is not None:
            game["current_batter"] = game["players"][next_batter_index].copy()
            game["current_batter_index"] = next_batter_index
        else:
            game["game_over"] = True
            game["winner"] = find_winner(game["players"])
            return result
        
        game["current_bowler_balls"] += 1
        game["total_balls_in_match"] += 1
        
        ball_mode = game.get("ball_mode", 3)
        if game["current_bowler_balls"] >= ball_mode:
            change_bowler(game)
        
    else:
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
        
        game["current_bowler_balls"] += 1
        game["total_balls_in_match"] += 1
        
        ball_mode = game.get("ball_mode", 3)
        if game["current_bowler_balls"] >= ball_mode:
            change_bowler(game)
    
    game["current_batter"] = batter.copy()
    
    if check_game_over(game):
        game["game_over"] = True
        game["winner"] = find_winner(game["players"])
    
    return result

def find_next_batter(players, current_index):
    """Find next batter who is not out"""
    for i in range(len(players)):
        next_idx = (current_index + 1 + i) % len(players)
        if not players[next_idx].get("out", False):
            return next_idx
    return None

def change_bowler(game):
    """Change to next bowler"""
    players = game["players"]
    current_bowler_index = game["current_bowler_index"]
    
    next_bowler_index = current_bowler_index
    for i in range(len(players)):
        next_bowler_index = (next_bowler_index + 1) % len(players)
        if next_bowler_index != game["current_batter_index"]:
            break
    
    game["current_bowler"] = players[next_bowler_index].copy()
    game["current_bowler_index"] = next_bowler_index
    game["current_bowler_balls"] = 0

def check_game_over(game):
    """Check if game should end"""
    players = game["players"]
    active_batters = [p for p in players if not p.get("out", False)]
    return len(active_batters) == 0

def find_winner(players):
    """Find player with highest score"""
    if not players:
        return None
    return max(players, key=lambda x: x.get("score", 0))

def get_game(chat_id):
    return games.get(chat_id)
