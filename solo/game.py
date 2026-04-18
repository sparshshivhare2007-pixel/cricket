# solo/game.py - Fixed Bowler Change After Out

import time

games = {}

def create_game(chat_id):
    games[chat_id] = {
        "players": [],
        "status": "waiting",
        "mode": None,
        "ball_mode": None,
        "current_batter": None,
        "current_bowler": None,
        "current_batter_index": 0,
        "current_bowler_index": 0,
        "bowling_number": None,
        "start_time": time.time(),
        "game_over": False,
        "winner": None,
        "current_bowler_balls": 0,
        "total_balls_in_match": 0
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
        game["current_batter_index"] = 0
        game["current_batter"] = players[0].copy()
        
        # Bowler index - next player (index 1)
        bowler_index = 1 if len(players) > 1 else 0
        game["current_bowler_index"] = bowler_index
        game["current_bowler"] = players[bowler_index].copy()

def set_bowling(chat_id, number):
    if chat_id in games:
        games[chat_id]["bowling_number"] = number

def find_next_batter(players, current_index):
    """Find next batter who is NOT OUT"""
    for i in range(1, len(players) + 1):
        next_idx = (current_index + i) % len(players)
        if not players[next_idx].get("out", False):
            return next_idx
    return None

def find_next_bowler(players, current_bowler_index, current_batter_index):
    """Find next bowler who is NOT OUT and NOT the current batter"""
    for i in range(1, len(players) + 1):
        next_idx = (current_bowler_index + i) % len(players)
        if not players[next_idx].get("out", False) and next_idx != current_batter_index:
            return next_idx
    # If no other player, return next active player (could be same as batter if only one left)
    for i in range(1, len(players) + 1):
        next_idx = (current_bowler_index + i) % len(players)
        if not players[next_idx].get("out", False):
            return next_idx
    return current_bowler_index

def play_ball(chat_id, bat_number):
    game = games.get(chat_id)
    if not game or game["status"] != "playing":
        return {"type": "error", "message": "Game not active"}
    
    bow = game.get("bowling_number")
    if bow is None:
        return {"type": "error", "message": "Bowling number not set"}
    
    # Get current batter
    batter_index = game["current_batter_index"]
    batter = game["players"][batter_index].copy()
    
    result = {}
    is_out = (bat_number == bow)
    
    if is_out:
        # BATTER IS OUT
        game["players"][batter_index]["balls"] += 1
        game["players"][batter_index]["history"].append("W")
        game["players"][batter_index]["out"] = True
        result["type"] = "out"
        result["runs"] = 0
        
        # Check how many active players left
        active_players = [p for p in game["players"] if not p.get("out", False)]
        
        if len(active_players) == 0:
            # ALL OUT - GAME OVER
            game["game_over"] = True
            game["winner"] = max(game["players"], key=lambda x: x.get("score", 0))
            return result
        elif len(active_players) == 1:
            # Only one player left - GAME OVER, he is winner
            game["game_over"] = True
            game["winner"] = active_players[0]
            return result
        else:
            # Find next batter who is not out
            next_batter_index = find_next_batter(game["players"], batter_index)
            
            if next_batter_index is not None:
                game["current_batter_index"] = next_batter_index
                game["current_batter"] = game["players"][next_batter_index].copy()
            else:
                game["game_over"] = True
                game["winner"] = max(game["players"], key=lambda x: x.get("score", 0))
                return result
        
        # Update bowler ball count
        game["current_bowler_balls"] += 1
        game["total_balls_in_match"] += 1
        
        # ALWAYS CHANGE BOWLER AFTER OUT (regardless of balls completed)
        # Find new bowler (not the new batter)
        new_bowler_index = find_next_bowler(
            game["players"], 
            game["current_bowler_index"], 
            game["current_batter_index"]
        )
        game["current_bowler_index"] = new_bowler_index
        game["current_bowler"] = game["players"][new_bowler_index].copy()
        game["current_bowler_balls"] = 0
        
    else:
        # RUNS SCORED - NOT OUT
        runs = bat_number
        game["players"][batter_index]["score"] += runs
        game["players"][batter_index]["balls"] += 1
        game["players"][batter_index]["history"].append(bat_number)

        if bat_number == 4:
            game["players"][batter_index]["fours"] += 1
        if bat_number == 6:
            game["players"][batter_index]["sixes"] += 1

        result["type"] = "run"
        result["runs"] = runs
        
        # Update current batter
        game["current_batter"] = game["players"][batter_index].copy()
        
        # Update bowler ball count
        game["current_bowler_balls"] += 1
        game["total_balls_in_match"] += 1
        
        # Check if bowler completed his overs (only then change bowler on runs)
        ball_mode = game.get("ball_mode", 3)
        if game["current_bowler_balls"] >= ball_mode:
            # Change bowler
            new_bowler_index = find_next_bowler(
                game["players"], 
                game["current_bowler_index"], 
                game["current_batter_index"]
            )
            game["current_bowler_index"] = new_bowler_index
            game["current_bowler"] = game["players"][new_bowler_index].copy()
            game["current_bowler_balls"] = 0
    
    return result

def get_game(chat_id):
    return games.get(chat_id)
