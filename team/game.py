# Team game logic
import time

team_games = {}

def create_team_game(chat_id, host_id, host_name):
    team_games[chat_id] = {
        "host_id": host_id,
        "host_name": host_name,
        "status": "waiting_host",  # waiting_host, team_creation_a, team_creation_b, ready, playing, game_over
        "team_a": [],
        "team_b": [],
        "team_a_score": 0,
        "team_b_score": 0,
        "team_a_wickets": 0,
        "team_b_wickets": 0,
        "target": None,
        "current_team": None,
        "current_batter": None,
        "current_bowler": None,
        "bowling_number": None,
        "current_bowler_balls": 0,
        "total_balls": 0,
        "ball_mode": 3,  # Default 3 balls per bowler
        "start_time": time.time(),
        "game_over": False,
        "winner": None
    }

def join_team_a(chat_id, user):
    game = team_games.get(chat_id)
    if not game or game["status"] != "team_creation_a":
        return False, "Team A joining not open"
    
    if len(game["team_a"]) >= 11:
        return False, "Team A is full"
    
    if user.id in [p["id"] for p in game["team_a"]] or user.id in [p["id"] for p in game["team_b"]]:
        return False, "Already joined a team"
    
    game["team_a"].append({
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
    return True, len(game["team_a"])

def join_team_b(chat_id, user):
    game = team_games.get(chat_id)
    if not game or game["status"] != "team_creation_b":
        return False, "Team B joining not open"
    
    if len(game["team_b"]) >= 11:
        return False, "Team B is full"
    
    if user.id in [p["id"] for p in game["team_a"]] or user.id in [p["id"] for p in game["team_b"]]:
        return False, "Already joined a team"
    
    game["team_b"].append({
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
    return True, len(game["team_b"])

def set_team_bowling(chat_id, number):
    if chat_id in team_games:
        team_games[chat_id]["bowling_number"] = number

def get_team_game(chat_id):
    return team_games.get(chat_id)

def delete_team_game(chat_id):
    if chat_id in team_games:
        del team_games[chat_id]
