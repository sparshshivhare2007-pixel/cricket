import motor.motor_asyncio
from datetime import datetime
import os
from bson import ObjectId

# MongoDB connection - FIXED for localhost
# Change from mongodb://localhost:27017 to 127.0.0.1
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = "cricket_bot"

# Collections
USERS_COLLECTION = "users"
MATCHES_COLLECTION = "matches"
SOLO_GAMES_COLLECTION = "solo_games"
TEAM_GAMES_COLLECTION = "team_games"
REPORTS_COLLECTION = "reports"

# Global client
client = None
db = None

# Collections
users = None
matches = None
solo_games = None
team_games = None
reports = None


async def init_db():
    """Initialize database connection and collections"""
    global client, db, users, matches, solo_games, team_games, reports
    
    try:
        # Add serverSelectionTimeoutMS to avoid long waiting
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Check connection
        await client.admin.command('ping')
        print("✅ MongoDB ping successful!")
        
        db = client[DB_NAME]
        
        users = db[USERS_COLLECTION]
        matches = db[MATCHES_COLLECTION]
        solo_games = db[SOLO_GAMES_COLLECTION]
        team_games = db[TEAM_GAMES_COLLECTION]
        reports = db[REPORTS_COLLECTION]
        
        # Create indexes
        await users.create_index("user_id", unique=True)
        await users.create_index("username")
        await matches.create_index("chat_id")
        await matches.create_index("match_id")
        await solo_games.create_index("chat_id")
        await team_games.create_index("chat_id")
        await reports.create_index("reported_user_id")
        
        print("✅ MongoDB connected and indexes created!")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️ Bot will run WITHOUT database. Stats will not be saved.")
        return False


async def close_db():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed!")


# ================= USER STATS FUNCTIONS =================

async def get_user(user_id):
    """Get user by ID"""
    if users is None:
        return None
    return await users.find_one({"user_id": user_id})


async def get_or_create_user(user_id, name, username=None):
    """Get user or create if not exists"""
    if users is None:
        # Return dummy data if DB not connected
        return {
            "user_id": user_id,
            "name": name,
            "username": username,
            "highest_score": 0,
            "highest_score_balls": 0,
            "best_game_host": 0,
            "total_runs": 0,
            "total_balls": 0,
            "wickets": 0,
            "sixes": 0,
            "fours": 0,
            "centuries": 0,
            "fifties": 0,
            "ducks": 0,
            "hat_tricks": 0,
            "man_of_match": 0,
            "best_captain": 0,
            "matches_played": 0,
            "runs_conceded": 0,
            "overs_bowled": 0
        }
    
    user = await get_user(user_id)
    if not user:
        user_data = {
            "user_id": user_id,
            "name": name,
            "username": username,
            "highest_score": 0,
            "highest_score_balls": 0,
            "best_game_host": 0,
            "total_runs": 0,
            "total_balls": 0,
            "wickets": 0,
            "sixes": 0,
            "fours": 0,
            "centuries": 0,
            "fifties": 0,
            "ducks": 0,
            "hat_tricks": 0,
            "man_of_match": 0,
            "best_captain": 0,
            "matches_played": 0,
            "runs_conceded": 0,
            "overs_bowled": 0,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        await users.insert_one(user_data)
        return user_data
    return user


async def update_user_stats(user_id, stats_data):
    """Update user stats"""
    if users is None:
        return
    await users.update_one(
        {"user_id": user_id},
        {
            "$inc": stats_data,
            "$set": {"last_updated": datetime.now()}
        }
    )


async def update_user_highest_score(user_id, score, balls):
    """Update highest score if current score is higher"""
    if users is None:
        return False
    user = await get_user(user_id)
    if user and score > user.get("highest_score", 0):
        await users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "highest_score": score,
                    "highest_score_balls": balls
                }
            }
        )
        return True
    return False


async def increment_best_game_host(user_id):
    """Increment best game host count"""
    if users is None:
        return
    await users.update_one(
        {"user_id": user_id},
        {"$inc": {"best_game_host": 1}}
    )


async def increment_hat_trick(user_id):
    """Increment hat-trick count"""
    if users is None:
        return
    await users.update_one(
        {"user_id": user_id},
        {"$inc": {"hat_tricks": 1}}
    )


async def update_match_stats(user_id, runs_scored=0, balls_played=0, wickets_taken=0,
                             sixes=0, fours=0, is_duck=False, is_fifty=False,
                             is_century=False, runs_conceded=0, overs_bowled=0,
                             is_man_of_match=False, is_best_captain=False):
    """Update stats after a match"""
    if users is None:
        return
    
    stats_data = {
        "matches_played": 1,
        "total_runs": runs_scored,
        "total_balls": balls_played,
        "wickets": wickets_taken,
        "sixes": sixes,
        "fours": fours,
        "runs_conceded": runs_conceded,
        "overs_bowled": overs_bowled
    }
    
    if is_duck:
        stats_data["ducks"] = 1
    if is_fifty:
        stats_data["fifties"] = 1
    if is_century:
        stats_data["centuries"] = 1
    if is_man_of_match:
        stats_data["man_of_match"] = 1
    if is_best_captain:
        stats_data["best_captain"] = 1
    
    await update_user_stats(user_id, stats_data)
    await update_user_highest_score(user_id, runs_scored, balls_played)


# ================= GET ALL USERS STATS (FOR LEADERBOARDS) =================

async def get_all_users_stats():
    """Get all users statistics from database for leaderboards"""
    if users is None:
        return []
    users_list = []
    async for doc in users.find({}):
        user_data = {k: v for k, v in doc.items() if k != '_id'}
        users_list.append(user_data)
    return users_list


# ================= SOLO GAME FUNCTIONS =================

async def save_solo_game(chat_id, game_data):
    """Save completed solo game to database"""
    if solo_games is None:
        return None
    game_record = {
        "chat_id": chat_id,
        "players": game_data.get("players", []),
        "ball_mode": game_data.get("ball_mode", 3),
        "total_balls": game_data.get("total_balls_in_match", 0),
        "winner": game_data.get("winner"),
        "start_time": game_data.get("start_time"),
        "end_time": datetime.now(),
        "status": "completed"
    }
    await solo_games.insert_one(game_record)
    return game_record


# Continue with other functions (they already have checks)...


async def get_solo_games(chat_id, limit=10):
    """Get recent solo games for a chat"""
    if solo_games is None:
        return []
    cursor = solo_games.find({"chat_id": chat_id}).sort("end_time", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ================= TEAM GAME FUNCTIONS =================

async def save_team_game(chat_id, game_data):
    """Save completed team game to database"""
    if team_games is None:
        return None
    game_record = {
        "chat_id": chat_id,
        "team_a": game_data.get("team_a", []),
        "team_b": game_data.get("team_b", []),
        "team_a_score": game_data.get("team_a_score", 0),
        "team_b_score": game_data.get("team_b_score", 0),
        "team_a_wickets": game_data.get("team_a_wickets", 0),
        "team_b_wickets": game_data.get("team_b_wickets", 0),
        "overs": game_data.get("overs", 0),
        "toss_winner": game_data.get("toss_winner"),
        "toss_decision": game_data.get("toss_decision"),
        "winner": game_data.get("winner"),
        "start_time": game_data.get("match_start_time"),
        "end_time": datetime.now(),
        "status": "completed"
    }
    await team_games.insert_one(game_record)
    return game_record


async def get_team_games(chat_id, limit=10):
    """Get recent team games for a chat"""
    if team_games is None:
        return []
    cursor = team_games.find({"chat_id": chat_id}).sort("end_time", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ================= MATCH FUNCTIONS =================

async def save_match(chat_id, match_data):
    """Save any match (solo or team) to database"""
    if matches is None:
        return None
    match_record = {
        "chat_id": chat_id,
        "match_type": match_data.get("type"),
        "data": match_data,
        "created_at": datetime.now()
    }
    await matches.insert_one(match_record)
    return match_record


async def get_match_history(chat_id, limit=20):
    """Get match history for a chat"""
    if matches is None:
        return []
    cursor = matches.find({"chat_id": chat_id}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ================= REPORT FUNCTIONS =================

async def save_report(chat_id, reported_user_id, reporter_id, reason):
    """Save a user report"""
    if reports is None:
        return None
    report_data = {
        "chat_id": chat_id,
        "reported_user_id": reported_user_id,
        "reporter_id": reporter_id,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.now()
    }
    await reports.insert_one(report_data)
    return report_data


async def get_user_reports(reported_user_id, limit=10):
    """Get reports for a user"""
    if reports is None:
        return []
    cursor = reports.find({"reported_user_id": reported_user_id}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_all_reports(chat_id, limit=50):
    """Get all reports for a chat"""
    if reports is None:
        return []
    cursor = reports.find({"chat_id": chat_id}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ================= LEADERBOARD FUNCTIONS =================

async def get_top_batters(limit=10):
    """Get top batters by runs"""
    if users is None:
        return []
    cursor = users.find().sort("total_runs", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_top_bowlers(limit=10):
    """Get top bowlers by wickets"""
    if users is None:
        return []
    cursor = users.find().sort("wickets", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_top_all_rounders(limit=10):
    """Get top all-rounders by (runs + wickets*20)"""
    if users is None:
        return []
    pipeline = [
        {"$addFields": {
            "all_round_score": {"$add": ["$total_runs", {"$multiply": ["$wickets", 20]}]}
        }},
        {"$sort": {"all_round_score": -1}},
        {"$limit": limit}
    ]
    cursor = users.aggregate(pipeline)
    return await cursor.to_list(length=limit)


async def get_user_rank(user_id, stat_field="total_runs"):
    """Get user rank based on a statistic"""
    if users is None:
        return None
    users_list = await users.find().sort(stat_field, -1).to_list(length=None)
    for i, user in enumerate(users_list, 1):
        if user["user_id"] == user_id:
            return i
    return None


# ================= UTILITY FUNCTIONS =================

async def get_all_users(limit=100):
    """Get all users"""
    if users is None:
        return []
    cursor = users.find().limit(limit)
    return await cursor.to_list(length=limit)


async def delete_user(user_id):
    """Delete a user (admin only)"""
    if users is None:
        return False
    result = await users.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def get_stats_summary():
    """Get overall bot statistics"""
    if users is None:
        return {
            "total_users": 0,
            "total_matches": 0,
            "total_solo_games": 0,
            "total_team_games": 0,
            "total_reports": 0
        }
    
    total_users = await users.count_documents({})
    total_matches = await matches.count_documents({}) if matches else 0
    total_solo_games = await solo_games.count_documents({}) if solo_games else 0
    total_team_games = await team_games.count_documents({}) if team_games else 0
    total_reports = await reports.count_documents({}) if reports else 0
    
    return {
        "total_users": total_users,
        "total_matches": total_matches,
        "total_solo_games": total_solo_games,
        "total_team_games": total_team_games,
        "total_reports": total_reports
    }
