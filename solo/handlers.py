   from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus, ParseMode
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
from solo.score import get_live_score
import asyncio
from datetime import datetime
import random
import os

print("🔴 LOADING HANDLERS.PY - FINAL COMPLETE VERSION")

active_votes = {}
bowling_tasks = {}

# ================= TEAM MODE VARIABLES =================
team_games = {}
team_hosts = {}
user_reports = {}

# Store pending selections
pending_bowler_selection = {}
pending_batter_selection = {}
pending_captain_selection = {}

# Consecutive timeout counters for auto-remove
bowler_consecutive_timeouts = {}
batter_consecutive_timeouts = {}

COUNTDOWN_VIDEO_PATH = "assets/video/countdown.mp4"

def get_clickable_name(user_id, name, username=None):
    """Returns clickable name in Telegram format"""
    return f'<a href="tg://user?id={user_id}">{name}</a>'

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

def build_team_scoreboard(game):
    team_key = f"team_{game['current_team'].lower()}"
    players = game[team_key]
    
    scoreboard = f"🏏 **{game['current_team']} Team Scoreboard** 🏏\n\n"
    scoreboard += f"**Total:** {game['team_total']}/{game['team_wickets']}\n"
    scoreboard += f"**Balls:** {game['total_balls_in_inning']}\n"
    scoreboard += f"**Overs:** {game['total_balls_in_inning'] // 6}.{game['total_balls_in_inning'] % 6}\n\n"
    scoreboard += "**Players:**\n"
    
    for p in players:
        status = "❌" if p.get("out", False) else "🏏"
        player_name = get_clickable_name(p['id'], p.get('name', 'Unknown'))
        scoreboard += f"{status} {player_name}: {p['score']} ({p['balls']} balls)"
        if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
            scoreboard += f" [4s:{p['fours']} 6s:{p['sixes']}]"
        scoreboard += "\n"
    
    return scoreboard

def reset_bowler_consecutive_timeout(chat_id, user_id):
    """Reset consecutive timeout count for a bowler"""
    if chat_id in bowler_consecutive_timeouts:
        if user_id in bowler_consecutive_timeouts[chat_id]:
            bowler_consecutive_timeouts[chat_id][user_id] = 0

def reset_batter_consecutive_timeout(chat_id, user_id):
    """Reset consecutive timeout count for a batter"""
    if chat_id in batter_consecutive_timeouts:
        if user_id in batter_consecutive_timeouts[chat_id]:
            batter_consecutive_timeouts[chat_id][user_id] = 0

def register_handlers(app):
    print("🔴 REGISTERING HANDLERS...")

    # ================= START COMMAND =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if game already running
        if chat_id in games and games[chat_id].get("status") in ["playing", "waiting"]:
            await message.reply("❌ A game is already running in this group! Use /end_match to end it first.")
            return
        
        if chat_id in team_games and team_games[chat_id].get("status") in ["playing", "waiting_host", "team_creation_a", "team_creation_b", "captain_selection", "toss", "waiting_startgame", "over_selection", "waiting_bowler", "waiting_batter"]:
            await message.reply("❌ A team game is already running in this group! Use /end_match to end it first.")
            return
        
        if await is_admin(client, chat_id, user_id):
            await select_game_menu(client, message)
        else:
            await vote_system(client, message)

    @app.on_message(filters.command("start") & filters.private)
    async def start_dm(client, message: Message):
        user_id = message.from_user.id
        
        for chat_id, game in games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply("🎾 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
                    return
        
        for chat_id, game in team_games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply("🎾 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
                    return
        
        await message.reply("🏏 **Welcome to Cricket Game Bot!**\n\nUse me in a group to play cricket games.\nAdd me to a group and use /start there!\n\n**Commands:**\n/start - Start game (Admin) or Vote (Member)\n/joingame - Join a solo game\n/score - Check live score")

    @app.on_message(filters.command("score") & filters.group)
    async def score_cmd(client, message: Message):
        await get_live_score(client, message)

    @app.on_message(filters.command("help") & filters.group)
    async def help_cmd(client, message: Message):
        help_text = """🏏 **Cricket Game Bot Commands** 🏏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎮 GAME MODES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**SOLO MODE:**
/start - Start game (Admin) or Vote (Member)
/joingame - Join solo game (min 2 players)
/score - Check live score
/end_match - End current match (Admin/Host)
/solo_leave - Leave solo game

**TEAM MODE:**
/create_team - Create teams (Host only)
/join_teamA - Join Team A
/join_teamB - Join Team B
/choose_cap - Choose team captains (Host)
/add_A @user - Add player to Team A
/add_B @user - Add player to Team B
/shift_team <number> - Shift player between teams (Host)
/end_match - End current match (Admin/Host)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 EXTRA COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/user_info - Get your user information (reply to get others info)
/user_ranks - View player rankings
/members - View team members & player numbers
/startgame - Start new game (Host)
/matches - View active matches
/live_matches - View live match updates
/host_change @user - Change game host
/full_score - View complete scorecard
/report_user @user - Report a user
/report_stats - View report statistics (Admin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ℹ️ INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Solo mode requires minimum 2 players
• 3 balls per bowler in solo mode
• Bot must be admin in group

🏏 **Enjoy the game!** 🏏"""
        
        await message.reply(help_text)

    # ================= END MATCH COMMAND =================
    @app.on_message(filters.command("end_match") & filters.group)
    async def end_match_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        is_admin_user = await is_admin(client, chat_id, user_id)
        
        solo_game = games.get(chat_id)
        if solo_game and solo_game.get("status") in ["playing", "waiting"]:
            if not is_admin_user:
                host_id = solo_game.get("host_id")
                if host_id != user_id:
                    await message.reply("❌ Only admin or game host can end the match!")
                    return
            
            if solo_game.get("status") == "playing" and not solo_game.get("game_over"):
                players = solo_game.get("players", [])
                final_scoreboard = build_scoreboard(players, is_final=True)
                
                await client.send_message(
                    chat_id,
                    final_scoreboard,
                    parse_mode=ParseMode.HTML
                )
            
            del games[chat_id]
            if chat_id in bowler_consecutive_timeouts:
                del bowler_consecutive_timeouts[chat_id]
            if chat_id in bowling_tasks:
                try:
                    bowling_tasks[chat_id].cancel()
                except:
                    pass
                del bowling_tasks[chat_id]
            
            await message.reply("✅ Solo match has been ended successfully!")
            return
        
        team_game = team_games.get(chat_id)
        if team_game and team_game.get("status") in ["playing", "waiting_host", "team_creation_a", "team_creation_b", "captain_selection", "toss", "waiting_startgame", "over_selection", "waiting_bowler", "waiting_batter"]:
            host = team_hosts.get(chat_id)
            
            if not is_admin_user:
                if not host or host.get("id") != user_id:
                    await message.reply("❌ Only admin or game host can end the match!")
                    return
            
            if team_game.get("status") == "playing" and not team_game.get("game_over"):
                team_a_score = team_game.get("team_a_score", 0)
                team_a_wickets = team_game.get("team_a_wickets", 0)
                team_b_score = team_game.get("team_b_score", 0)
                team_b_wickets = team_game.get("team_b_wickets", 0)
                
                final_text = f"🏏 **Match Ended by Admin/Host!** 🏏\n\n"
                final_text += f"📊 **Final Score:**\n"
                final_text += f"🏏 Team A: {team_a_score}/{team_a_wickets}\n"
                final_text += f"🏏 Team B: {team_b_score}/{team_b_wickets}\n\n"
                
                if team_a_score > team_b_score:
                    final_text += f"🏆 **Team A wins the match!** 🏆"
                elif team_b_score > team_a_score:
                    final_text += f"🏆 **Team B wins the match!** 🏆"
                elif team_a_score == team_b_score and (team_a_score > 0 or team_b_score > 0):
                    final_text += f"🤝 **Match Tied!** 🤝"
                else:
                    final_text += f"⚠️ Match ended before completion!"
                
                await client.send_message(chat_id, final_text)
            
            del team_games[chat_id]
            if chat_id in team_hosts:
                del team_hosts[chat_id]
            if chat_id in bowler_consecutive_timeouts:
                del bowler_consecutive_timeouts[chat_id]
            if chat_id in bowling_tasks:
                try:
                    bowling_tasks[chat_id].cancel()
                except:
                    pass
                del bowling_tasks[chat_id]
            
            await message.reply("✅ Team match has been ended successfully!")
            return
        
        await message.reply("❌ No active match found in this group!")

    # ================= USER INFO COMMAND =================
    @app.on_message(filters.command("user_info") & filters.group)
    async def user_info_cmd(client, message: Message):
        from pyrogram.enums import ParseMode
        
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        else:
            user = message.from_user
        
        user_id = user.id
        name = user.first_name
        username = user.username
        
        from database import get_or_create_user
        user_data = await get_or_create_user(user_id, name, username)
        
        highest_score = user_data.get("highest_score", 0)
        highest_score_balls = user_data.get("highest_score_balls", 0)
        total_runs = user_data.get("total_runs", 0)
        total_balls = user_data.get("total_balls", 0)
        wickets = user_data.get("wickets", 0)
        centuries = user_data.get("centuries", 0)
        fifties = user_data.get("fifties", 0)
        matches_played = user_data.get("matches_played", 0)
        
        strike_rate = round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0.0
        
        user_mention = get_clickable_name(user_id, name, username)
        
        stats_text = f"""🏏 Stats Summary
👤 User: {user_mention}
🆔 User ID: {user_id}
─────⊱◈◈◈⊰─────
🏆 Highest Score: {highest_score} ({highest_score_balls} Balls)
📊 Runs: {total_runs} ({matches_played})
🎾 Wickets: {wickets}
🔥 Centuries: {centuries}
⭐ Fifties: {fifties}
⚡ Strike Rate: {strike_rate}
─────⊱◈◈◈⊰─────"""
        
        try:
            await client.send_photo(
                message.chat.id,
                USER_STATS_IMAGE,
                caption=stats_text,
                has_spoiler=True,
                parse_mode=ParseMode.HTML
            )
        except:
            await message.reply(stats_text, parse_mode=ParseMode.HTML)

    # ================= USER RANKS COMMAND =================
    @app.on_message(filters.command("user_ranks") & filters.group)
    async def user_ranks_cmd(client, message: Message):
        from database import get_or_create_user
        from pyrogram.enums import ParseMode
        
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        else:
            user = message.from_user
        
        user_id = user.id
        name = user.first_name
        username = user.username
        
        user_data = await get_or_create_user(user_id, name, username)
        
        highest_score = user_data.get("highest_score", 0)
        highest_score_balls = user_data.get("highest_score_balls", 0)
        best_game_host = user_data.get("best_game_host", 0)
        total_runs = user_data.get("total_runs", 0)
        wickets = user_data.get("wickets", 0)
        sixes = user_data.get("sixes", 0)
        fours = user_data.get("fours", 0)
        centuries = user_data.get("centuries", 0)
        fifties = user_data.get("fifties", 0)
        ducks = user_data.get("ducks", 0)
        hat_tricks = user_data.get("hat_tricks", 0)
        matches_played = user_data.get("matches_played", 0)
        
        clickable_name = get_clickable_name(user_id, name, username)
        
        stats_text = f"""🏏 Stats for {clickable_name}
📊 Runs: {total_runs} ({matches_played} matches)
🎾 Wickets: {wickets}
💥 Sixes: {sixes}
✨ Fours: {fours}
🔥 Centuries: {centuries}
⭐ Fifties: {fifties}
🦆 Ducks: {ducks}
🎩 Hat-tricks: {hat_tricks}
🏏 Highest Score: {highest_score} ({highest_score_balls} balls)
🧑‍✈️ Best Game Host: {best_game_host}"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Highest Scores", callback_data="rank_scores"), InlineKeyboardButton("Highest Wickets", callback_data="rank_wickets")],
            [InlineKeyboardButton("Highest Sixes", callback_data="rank_sixes"), InlineKeyboardButton("Highest Fours", callback_data="rank_fours")],
            [InlineKeyboardButton("Highest Fifties", callback_data="rank_fifties"), InlineKeyboardButton("Highest Centuries", callback_data="rank_centuries")],
            [InlineKeyboardButton("Hat-tricks", callback_data="rank_hattricks"), InlineKeyboardButton("Best Game Host", callback_data="rank_host")],
            [InlineKeyboardButton("Best Players", callback_data="rank_players"), InlineKeyboardButton("Best Captains", callback_data="rank_captains")]
        ])
        
        try:
            await client.send_photo(
                message.chat.id,
                USER_RANKS_IMAGE,
                caption=stats_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except:
            await message.reply(stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    # ================= RANK BUTTON HANDLERS =================
    @app.on_callback_query(filters.regex("^rank_"))
    async def rank_buttons_handler(client, callback: CallbackQuery):
        from database import get_all_users_stats
        from pyrogram.enums import ParseMode
        
        action = callback.data.split("_")[1]
        all_users = await get_all_users_stats()
        
        if action == "scores":
            sorted_users = sorted(all_users, key=lambda x: x.get("highest_score", 0), reverse=True)[:10]
            text = "🏏 **Highest Scores Leaderboard** 🏏\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("highest_score", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('highest_score', 0)} runs\n"
        elif action == "wickets":
            sorted_users = sorted(all_users, key=lambda x: x.get("wickets", 0), reverse=True)[:10]
            text = "🎾 **Highest Wickets Leaderboard** 🎾\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("wickets", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('wickets', 0)} wickets\n"
        elif action == "sixes":
            sorted_users = sorted(all_users, key=lambda x: x.get("sixes", 0), reverse=True)[:10]
            text = "💥 **Highest Sixes Leaderboard** 💥\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("sixes", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('sixes', 0)} sixes\n"
        elif action == "fours":
            sorted_users = sorted(all_users, key=lambda x: x.get("fours", 0), reverse=True)[:10]
            text = "✨ **Highest Fours Leaderboard** ✨\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("fours", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('fours', 0)} fours\n"
        elif action == "fifties":
            sorted_users = sorted(all_users, key=lambda x: x.get("fifties", 0), reverse=True)[:10]
            text = "⭐ **Highest Fifties Leaderboard** ⭐\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("fifties", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('fifties', 0)} fifties\n"
        elif action == "centuries":
            sorted_users = sorted(all_users, key=lambda x: x.get("centuries", 0), reverse=True)[:10]
            text = "🔥 **Highest Centuries Leaderboard** 🔥\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("centuries", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('centuries', 0)} centuries\n"
        elif action == "hattricks":
            sorted_users = sorted(all_users, key=lambda x: x.get("hat_tricks", 0), reverse=True)[:10]
            text = "🎩 **Hat-tricks Leaderboard** 🎩\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("hat_tricks", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('hat_tricks', 0)} hat-tricks\n"
        elif action == "host":
            sorted_users = sorted(all_users, key=lambda x: x.get("best_game_host", 0), reverse=True)[:10]
            text = "🎮 **Best Game Host Leaderboard** 🎮\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("best_game_host", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('best_game_host', 0)} times\n"
        elif action == "players":
            sorted_users = sorted(all_users, key=lambda x: x.get("total_runs", 0), reverse=True)[:10]
            text = "🏆 **Best Players (Most Runs)** 🏆\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("total_runs", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('total_runs', 0)} runs\n"
        elif action == "captains":
            sorted_users = sorted(all_users, key=lambda x: x.get("best_captain", 0), reverse=True)[:10]
            text = "🧢 **Best Captains Leaderboard** 🧢\n\n"
            for i, user in enumerate(sorted_users, 1):
                if user.get("best_captain", 0) > 0:
                    text += f"{i}. {user.get('name', 'Unknown')}: {user.get('best_captain', 0)} wins\n"
        else:
            text = "Coming soon!"
        
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Stats", callback_data="back_to_ranks")]])
        
        await callback.message.edit_caption(caption=text, reply_markup=back_button, parse_mode=ParseMode.HTML)
        await callback.answer()

    @app.on_callback_query(filters.regex("^back_to_ranks$"))
    async def back_to_ranks_callback(client, callback: CallbackQuery):
        from database import get_or_create_user
        from pyrogram.enums import ParseMode
        
        user = callback.from_user
        user_id = user.id
        name = user.first_name
        username = user.username
        
        user_data = await get_or_create_user(user_id, name, username)
        
        highest_score = user_data.get("highest_score", 0)
        highest_score_balls = user_data.get("highest_score_balls", 0)
        best_game_host = user_data.get("best_game_host", 0)
        total_runs = user_data.get("total_runs", 0)
        wickets = user_data.get("wickets", 0)
        sixes = user_data.get("sixes", 0)
        fours = user_data.get("fours", 0)
        centuries = user_data.get("centuries", 0)
        fifties = user_data.get("fifties", 0)
        ducks = user_data.get("ducks", 0)
        hat_tricks = user_data.get("hat_tricks", 0)
        matches_played = user_data.get("matches_played", 0)
        
        clickable_name = get_clickable_name(user_id, name, username)
        
        stats_text = f"""🏏 Stats for {clickable_name}
📊 Runs: {total_runs} ({matches_played} matches)
🎾 Wickets: {wickets}
💥 Sixes: {sixes}
✨ Fours: {fours}
🔥 Centuries: {centuries}
⭐ Fifties: {fifties}
🦆 Ducks: {ducks}
🎩 Hat-tricks: {hat_tricks}
🏏 Highest Score: {highest_score} ({highest_score_balls} balls)
🧑‍✈️ Best Game Host: {best_game_host}"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Highest Scores", callback_data="rank_scores"), InlineKeyboardButton("Highest Wickets", callback_data="rank_wickets")],
            [InlineKeyboardButton("Highest Sixes", callback_data="rank_sixes"), InlineKeyboardButton("Highest Fours", callback_data="rank_fours")],
            [InlineKeyboardButton("Highest Fifties", callback_data="rank_fifties"), InlineKeyboardButton("Highest Centuries", callback_data="rank_centuries")],
            [InlineKeyboardButton("Hat-tricks", callback_data="rank_hattricks"), InlineKeyboardButton("Best Game Host", callback_data="rank_host")],
            [InlineKeyboardButton("Best Players", callback_data="rank_players"), InlineKeyboardButton("Best Captains", callback_data="rank_captains")]
        ])
        
        await callback.message.edit_caption(caption=stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer()

    # ================= JOIN GAME COMMAND =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        print(f"🔴 JOIN GAME - Chat: {chat_id}, User: {user.id}")
        
        game = games.get(chat_id)
        
        if not game:
            await message.reply("❌ No active solo game! Use /start and select Solo mode first.")
            return
        
        if game.get("status") != "waiting":
            await message.reply("❌ Game already started! Cannot join now.")
            return
        
        for p in game.get("players", []):
            if p["id"] == user.id:
                await message.reply("❌ You already joined this game!")
                return
        
        player_data = {
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "score": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "history": []
        }
        
        if "players" not in game:
            game["players"] = []
        
        game["players"].append(player_data)
        
        clickable_name = get_clickable_name(user.id, user.first_name, user.username)
        await message.reply(f"✅ {clickable_name} Joined Successfully!", parse_mode=ParseMode.HTML)

    async def start_game_match(client, chat_id):
        print(f"🔴 START GAME MATCH - Chat: {chat_id}")
        
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        players_count = len(game["players"])
        
        if players_count < 2:
            await client.send_message(chat_id, f"❌ Minimum 2 players required! Current: {players_count}/2")
            if chat_id in games:
                del games[chat_id]
            return
        
        start_match(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        host_text = "🏏 **SOLO CRICKET** 🏏\n\n**Players List:**\n"
        for i, p in enumerate(players, 1):
            clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
            host_text += f"{i}. {clickable}\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text, parse_mode=ParseMode.HTML)
        except:
            await client.send_message(chat_id, host_text, parse_mode=ParseMode.HTML)
        
        batter = game["current_batter"]
        bowler = game["current_bowler"]
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        bowler_clickable = get_clickable_name(bowler['id'], bowler['name'], bowler.get('username'))
        
        await client.send_message(chat_id, f"🏏 Hey {batter_clickable}, now you're batter!", parse_mode=ParseMode.HTML)
        await client.send_message(chat_id, f"🎾 Hey {bowler_clickable}, now you're bowling!", parse_mode=ParseMode.HTML)
        
        await asyncio.sleep(1)
        await send_bowling_video_solo(client, chat_id, bowler)

    # ================= SOLO MODE SEND BOWLING VIDEO =================
    async def send_bowling_video_solo(client, chat_id, bowler):
        game = games.get(chat_id)
        if not game or game.get("status") != "playing" or game.get("game_over"):
            return
        
        batter = game["current_batter"]
        bot_username = BOT_USERNAME
        dm_link = f"https://t.me/{bot_username}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎾 Click to Bowl", url=dm_link)]
        ])
        
        bowler_name = bowler.get('name')
        bowler_id = bowler['id']
        bowler_clickable = get_clickable_name(bowler_id, bowler_name, bowler.get('username'))
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"Hey {bowler_clickable}, You're Bowler",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        
        try:
            await client.send_message(
                bowler["id"],
                f"🎾 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        if chat_id in bowling_tasks:
            try:
                bowling_tasks[chat_id].cancel()
            except:
                pass
        
        task = asyncio.create_task(bowling_timeout_solo(client, chat_id, bowler["id"], bowler_name, bowler_clickable))
        bowling_tasks[chat_id] = task

    async def bowling_timeout_solo(client, chat_id, user_id, bowler_name, bowler_clickable):
        await asyncio.sleep(30)
        game = games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                try:
                    await client.send_message(
                        chat_id,
                        f"⚠️ Warning: {bowler_clickable}, you have 30 seconds left to send a number!",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        
        await asyncio.sleep(20)
        game = games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                try:
                    await client.send_message(
                        chat_id,
                        f"⚠️ Warning: {bowler_clickable}, you have 10 seconds left to send a number!",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        
        await asyncio.sleep(10)
        game = games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                
                if chat_id not in bowler_consecutive_timeouts:
                    bowler_consecutive_timeouts[chat_id] = {}
                if user_id not in bowler_consecutive_timeouts[chat_id]:
                    bowler_consecutive_timeouts[chat_id][user_id] = 0
                
                bowler_consecutive_timeouts[chat_id][user_id] += 1
                current_timeout = bowler_consecutive_timeouts[chat_id][user_id]
                
                if current_timeout >= 2:
                    player_removed = False
                    removed_player = None
                    for i, player in enumerate(game["players"]):
                        if player["id"] == user_id:
                            removed_player = player
                            game["players"].pop(i)
                            player_removed = True
                            break
                    
                    if player_removed:
                        await client.send_message(
                            chat_id,
                            f"❌ {bowler_clickable} has been removed from the game due to 2 consecutive timeouts!",
                            parse_mode=ParseMode.HTML
                        )
                        
                        if user_id in bowler_consecutive_timeouts[chat_id]:
                            del bowler_consecutive_timeouts[chat_id][user_id]
                        
                        current_batter = game.get("current_batter", {})
                        if current_batter.get("id") == user_id:
                            active_players = [p for p in game["players"] if not p.get("out", False)]
                            if len(active_players) == 0:
                                await client.send_message(chat_id, "🏏 Game ended! No players left!")
                                if chat_id in games:
                                    del games[chat_id]
                                return
                            new_batter = active_players[0]
                            game["current_batter"] = new_batter
                            new_batter_clickable = get_clickable_name(new_batter['id'], new_batter['name'], new_batter.get('username'))
                            await client.send_message(chat_id, f"🎾 New batter: {new_batter_clickable}", parse_mode=ParseMode.HTML)
                        
                        active_players = [p for p in game["players"] if not p.get("out", False)]
                        if len(active_players) < 2:
                            await client.send_message(chat_id, "🏏 Game ended due to insufficient players!")
                            if len(active_players) == 1:
                                winner = active_players[0]
                                winner_clickable = get_clickable_name(winner['id'], winner['name'], winner.get('username'))
                                await client.send_message(chat_id, f"🏆 {winner_clickable} wins the game!", parse_mode=ParseMode.HTML)
                            if chat_id in games:
                                del games[chat_id]
                            return
                        
                        active_bowlers = [p for p in active_players if p["id"] != game["current_batter"]["id"]]
                        if len(active_bowlers) == 0:
                            active_bowlers = active_players
                        
                        new_bowler = active_bowlers[0] if len(active_bowlers) > 0 else active_players[0]
                        if new_bowler:
                            game["current_bowler"] = new_bowler
                            await send_bowling_video_solo(client, chat_id, new_bowler)
                        return
                else:
                    for player in game["players"]:
                        if player["id"] == user_id:
                            player["score"] -= 6
                            player["history"].append("-6")
                            break
                    
                    try:
                        await client.send_video(
                            chat_id,
                            get_run_video(6),
                            caption=f"No message received from bowler, deducting 6 runs from {bowler_clickable}'s score. (Consecutive timeout {current_timeout}/2)",
                            parse_mode=ParseMode.HTML
                        )
                    except:
                        await client.send_message(
                            chat_id,
                            f"No message received from bowler, deducting 6 runs from {bowler_name}'s score. (Consecutive timeout {current_timeout}/2)"
                        )
                    
                    await client.send_message(chat_id, build_scoreboard(game["players"], is_final=False))
                    
                    game["bowling_number"] = None
                    game["current_bowler_balls"] += 1
                    game["total_balls_in_match"] += 1
                    
                    if game["current_bowler"]["id"] == game["current_batter"]["id"]:
                        players = game["players"]
                        current_index = game.get("current_bowler_index", 0)
                        new_index = (current_index + 1) % len(players)
                        game["current_bowler_index"] = new_index
                        game["current_bowler"] = players[new_index].copy()
                    
                    await send_bowling_video_solo(client, chat_id, game["current_bowler"])
        
        if chat_id in bowling_tasks:
            del bowling_tasks[chat_id]

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Solo", callback_data="mode_solo"), InlineKeyboardButton("👥 Team", callback_data="mode_team")],
            [InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel")]
        ])
        
        caption = "🏏 **Select Game Mode** 🏏\n\nChoose how you want to play:"
        
        try:
            await message.reply_photo(SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except:
            await message.reply(caption, reply_markup=keyboard)

    @app.on_callback_query(filters.regex("^mode_"))
    async def mode_handler(client, callback: CallbackQuery):
        action = callback.data.split("_")[1]
        
        if action == "cancel":
            await callback.message.delete()
            await callback.answer("Cancelled")
            return
        
        if action == "team":
            await callback.message.delete()
            await callback.answer("Opening Team Mode...")
            await team_mode_start(client, callback)
            return
        
        if action == "solo":
            await ball_selection_menu(client, callback)

    async def ball_selection_menu(client, callback):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎾 Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎾 Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = "🏏 **Choose Bowling Mode** 🏏\n\n• Solo Play - 1 Ball\n• Solo Play - 3 Ball"
        
        await callback.message.delete()
        
        try:
            await callback.message.reply_photo(SOLO_PLAY_IMG, caption=caption, reply_markup=keyboard)
        except:
            await callback.message.reply(caption, reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^ball_"))
    async def ball_handler(client, callback: CallbackQuery):
        ball_mode = int(callback.data.split("_")[1])
        chat_id = callback.message.chat.id
        
        # Check if game already exists
        if chat_id in games:
            await callback.answer("❌ A game is already running in this group!", show_alert=True)
            return
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        game["status"] = "waiting"
        game["players"] = []
        game["host_id"] = callback.from_user.id
        
        await callback.message.delete()
        await client.send_message(chat_id, "🎉 Solo game created! Join the game using /joingame (2 minutes to join)\n⏰")
        asyncio.create_task(start_join_timer(client, chat_id))

    async def start_join_timer(client, chat_id):
        await asyncio.sleep(60)
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"1 minute left! {players_count} players joined. Send /joingame to join!")
        
        await asyncio.sleep(30)
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"30 seconds left! {players_count} players joined. /joingame fast!!")
        
        await asyncio.sleep(20)
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"Last 10 seconds! {players_count} players joined. /joingame !!")
        
        await asyncio.sleep(10)
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            
            if players_count < 2:
                await client.send_message(chat_id, f"❌ Minimum 2 players required! Current: {players_count}/2\n⚠️ Game cancelled!")
                if chat_id in games:
                    del games[chat_id]
                if chat_id in bowler_consecutive_timeouts:
                    del bowler_consecutive_timeouts[chat_id]
            else:
                await client.send_message(chat_id, f"✅ Time's up! {players_count} players joined. Starting game...")
                await start_game_match(client, chat_id)

    # ================= TEAM MODE START =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        
        # Check if game already exists
        if chat_id in team_games:
            await callback.answer("❌ A team game is already running in this group!", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
        ])
        
        caption = "🎉 **New Game Alert!** 🎉 \n\nWho will be the game host for this match? 🤔"
        
        try:
            await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
        except:
            await client.send_message(chat_id, caption, reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_games and team_games[chat_id].get("status") == "playing":
            await callback.answer("❌ A match is currently in progress!", show_alert=True)
            return
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        team_hosts[chat_id] = {"id": user.id, "name": user.first_name, "username": user.username}
        
        team_games[chat_id] = {
            "host_id": user.id,
            "host_name": user.first_name,
            "status": "waiting_host",
            "team_a": [],
            "team_b": [],
            "captain_a": None,
            "captain_b": None,
            "team_a_score": 0,
            "team_b_score": 0,
            "team_a_wickets": 0,
            "team_b_wickets": 0,
            "current_team": None,
            "game_over": False,
            "winner": None,
            "batting_order": [],
            "batting_order_names": [],
            "ball_mode": 1,
            "overs": 0,
            "target": 0
        }
        
        await callback.message.delete()
        
        host_clickable = get_clickable_name(user.id, user.first_name, user.username)
        await client.send_message(chat_id, f"👑 {host_clickable} is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏", parse_mode=ParseMode.HTML)
        await callback.answer()

    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        print(f"🔴 CREATE TEAM - Chat: {chat_id}, User: {user_id}")
        
        host = team_hosts.get(chat_id)
        if not host:
            await message.reply("❌ No game host found! First use /start and select Team mode, then click 'I'm the Host' button.")
            return
        
        if host.get("id") != user_id:
            await message.reply("❌ Only the game host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "waiting_host":
            await message.reply("❌ Teams already created or no active game!")
            return
        
        game["team_a"] = []
        game["team_b"] = []
        game["status"] = "team_creation_a"
        
        await message.reply("🎉 Team creation is underway!\n\n📣 Join Team A by sending /join_teamA\n⏰ You have 50 seconds for Team A")
        
        asyncio.create_task(team_a_timer(client, chat_id))

    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            team_a_count = len(game.get("team_a", []))
            await client.send_message(chat_id, f"⏰ Time's up for Team A! ({team_a_count} players joined)\n\n📣 Join Team B by sending /join_teamB\n⏰ You have 50 seconds for Team B")
            asyncio.create_task(team_b_timer(client, chat_id))

    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            game["status"] = "captain_selection"
            team_a_count = len(game.get("team_a", []))
            team_b_count = len(game.get("team_b", []))
            
            host = team_hosts.get(chat_id)
            if host:
                host_clickable = get_clickable_name(host['id'], host['name'], host.get('username'))
                host_mention = host_clickable
            else:
                host_mention = "Game host"
            
            await client.send_message(
                chat_id,
                f"👋 Hey, {host_mention} now members are joined the teams! 🎉 Choose Team captains using /choose_cap 📝",
                parse_mode=ParseMode.HTML
            )

    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "team_creation_a":
            await message.reply("❌ Team A is not open for joining!")
            return
        
        host = team_hosts.get(chat_id)
        if host and host.get("id") == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        for p in game.get("team_b", []):
            if p["id"] == user.id:
                await message.reply("❌ You are already in Team B! You cannot join Team A.")
                return
        
        for p in game.get("team_a", []):
            if p["id"] == user.id:
                await message.reply("❌ You already joined Team A!")
                return
        
        player_data = {
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "score": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "history": []
        }
        
        if "team_a" not in game:
            game["team_a"] = []
        
        game["team_a"].append(player_data)
        
        clickable_name = get_clickable_name(user.id, user.first_name, user.username)
        await message.reply(f"✅ {clickable_name} Joined Successfully!", parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "team_creation_b":
            await message.reply("❌ Team B is not open for joining!")
            return
        
        host = team_hosts.get(chat_id)
        if host and host.get("id") == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        for p in game.get("team_a", []):
            if p["id"] == user.id:
                await message.reply("❌ You are already in Team A! You cannot join Team B.")
                return
        
        for p in game.get("team_b", []):
            if p["id"] == user.id:
                await message.reply("❌ You already joined Team B!")
                return
        
        player_data = {
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "score": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "history": []
        }
        
        if "team_b" not in game:
            game["team_b"] = []
        
        game["team_b"].append(player_data)
        
        clickable_name = get_clickable_name(user.id, user.first_name, user.username)
        await message.reply(f"✅ {clickable_name} Joined Successfully!", parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("add_A") & filters.group)
    async def add_to_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team A!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        added_user = None
        if message.reply_to_message:
            added_user = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                added_user = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not added_user:
            await message.reply("❌ Usage: /add_A @username or reply to a user's message")
            return
        
        for p in game.get("team_b", []):
            if p["id"] == added_user.id:
                added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
                await message.reply(f"❌ {added_clickable} is already in Team B!", parse_mode=ParseMode.HTML)
                return
        
        for p in game.get("team_a", []):
            if p["id"] == added_user.id:
                added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
                await message.reply(f"❌ Already in Team A!", parse_mode=ParseMode.HTML)
                return
        
        player_data = {
            "id": added_user.id,
            "name": added_user.first_name,
            "username": added_user.username,
            "score": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "history": []
        }
        
        if "team_a" not in game:
            game["team_a"] = []
        
        game["team_a"].append(player_data)
        added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
        await message.reply(f"✅ {added_clickable} Added Successfully!", parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("add_B") & filters.group)
    async def add_to_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team B!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        added_user = None
        if message.reply_to_message:
            added_user = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                added_user = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not added_user:
            await message.reply("❌ Usage: /add_B @username or reply to a user's message")
            return
        
        for p in game.get("team_a", []):
            if p["id"] == added_user.id:
                added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
                await message.reply(f"❌ {added_clickable} is already in Team A!", parse_mode=ParseMode.HTML)
                return
        
        for p in game.get("team_b", []):
            if p["id"] == added_user.id:
                added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
                await message.reply(f"❌ Already in Team B!", parse_mode=ParseMode.HTML)
                return
        
        player_data = {
            "id": added_user.id,
            "name": added_user.first_name,
            "username": added_user.username,
            "score": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "history": []
        }
        
        if "team_b" not in game:
            game["team_b"] = []
        
        game["team_b"].append(player_data)
        added_clickable = get_clickable_name(added_user.id, added_user.first_name, added_user.username)
        await message.reply(f"✅ {added_clickable} Added Successfully!", parse_mode=ParseMode.HTML)

    # ================= SHIFT TEAM COMMAND =================
    @app.on_message(filters.command("shift_team") & filters.group)
    async def shift_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can shift players!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/shift_team <number>`\nExample: `/shift_team 1`\n\nUse /members to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        player = None
        current_team = None
        player_index = None
        
        for i, p in enumerate(game.get("team_a", [])):
            if i + 1 == player_num:
                player = p
                current_team = "A"
                player_index = i
                break
        
        if not player:
            offset = len(game.get("team_a", []))
            for i, p in enumerate(game.get("team_b", [])):
                if offset + i + 1 == player_num:
                    player = p
                    current_team = "B"
                    player_index = i
                    break
        
        if not player:
            await message.reply(f"❌ Player number {player_num} not found! Use /members to see player numbers.")
            return
        
        player_clickable = get_clickable_name(player['id'], player['name'], player.get('username'))
        
        if current_team == "A":
            game["team_a"].pop(player_index)
            game["team_b"].append(player)
            await message.reply(f"✅ {player_clickable} Shifted Successfully!", parse_mode=ParseMode.HTML)
        else:
            game["team_b"].pop(player_index)
            game["team_a"].append(player)
            await message.reply(f"✅ {player_clickable} Shifted Successfully!", parse_mode=ParseMode.HTML)
        
        await client.send_message(chat_id, "📊 Teams updated! Use /members to see new team lists.")

    # ================= REMOVE PLAYER COMMAND =================
    @app.on_message(filters.command("remove_player") & filters.group)
    async def remove_player_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can remove players!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/remove_player <number>`\nExample: `/remove_player 1`\n\nUse /members to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        player = None
        current_team = None
        player_index = None
        
        for i, p in enumerate(game.get("team_a", [])):
            if i + 1 == player_num:
                player = p
                current_team = "A"
                player_index = i
                break
        
        if not player:
            offset = len(game.get("team_a", []))
            for i, p in enumerate(game.get("team_b", [])):
                if offset + i + 1 == player_num:
                    player = p
                    current_team = "B"
                    player_index = i
                    break
        
        if not player:
            await message.reply(f"❌ Player number {player_num} not found! Use /members to see player numbers.")
            return
        
        player_clickable = get_clickable_name(player['id'], player['name'], player.get('username'))
        
        if current_team == "A":
            game["team_a"].pop(player_index)
        else:
            game["team_b"].pop(player_index)
        
        await message.reply(f"✅ {player_clickable} Removed Successfully!", parse_mode=ParseMode.HTML)
        
        await client.send_message(chat_id, "📊 Teams updated! Use /members to see new team lists.")

    # ================= CHOOSE CAPTAIN COMMAND =================
    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only game host can start captain selection!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game found!")
            return
        
        if game.get("captain_a") and game.get("captain_b"):
            await message.reply("❌ Captains already selected!")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")],
            [InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cap_cancel")]
        ])
        
        await message.reply(
            "🏏 **Game Host, please choose captains for Team A and Team B:**\n\n"
            "Team A members click 'Team A Captain' button to become captain.\n"
            "Team B members click 'Team B Captain' button to become captain.",
            reply_markup=keyboard
        )

    @app.on_callback_query(filters.regex("^choose_cap_a$"))
    async def choose_cap_a_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_a"):
            await callback.answer("❌ Team A captain already selected!", show_alert=True)
            return
        
        user_name = None
        for player in game["team_a"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_a"] = player
                break
        
        if not user_name:
            await callback.answer("❌ You are not in Team A!", show_alert=True)
            return
        
        user_clickable = get_clickable_name(user_id, user_name)
        await callback.answer(f"✅ {user_name} is now Team A Captain!")
        
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cap_cancel")]
            ])
            cap_a_clickable = get_clickable_name(game["captain_a"]["id"], game["captain_a"]["name"], game["captain_a"].get("username"))
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"✅ Team A Captain: {cap_a_clickable}\n"
                f"⚠️ Team B Captain: Not selected yet\n\n"
                f"Team B members click 'Team B Captain' button to become captain.",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

    @app.on_callback_query(filters.regex("^choose_cap_b$"))
    async def choose_cap_b_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_b"):
            await callback.answer("❌ Team B captain already selected!", show_alert=True)
            return
        
        user_name = None
        for player in game["team_b"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_b"] = player
                break
        
        if not user_name:
            await callback.answer("❌ You are not in Team B!", show_alert=True)
            return
        
        user_clickable = get_clickable_name(user_id, user_name)
        await callback.answer(f"✅ {user_name} is now Team B Captain!")
        
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cap_cancel")]
            ])
            cap_b_clickable = get_clickable_name(game["captain_b"]["id"], game["captain_b"]["name"], game["captain_b"].get("username"))
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"⚠️ Team A Captain: Not selected yet\n"
                f"✅ Team B Captain: {cap_b_clickable}\n\n"
                f"Team A members click 'Team A Captain' button to become captain.",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

    @app.on_callback_query(filters.regex("^cap_cancel$"))
    async def cap_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Captain selection cancelled!")

    # ================= START TOSS FUNCTION =================
    async def start_toss(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        cap_a_name = game['captain_a']['name']
        cap_b_name = game['captain_b']['name']
        cap_a_clickable = get_clickable_name(game['captain_a']['id'], cap_a_name, game['captain_a'].get('username'))
        cap_b_clickable = get_clickable_name(game['captain_b']['id'], cap_b_name, game['captain_b'].get('username'))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 HEADS", callback_data="toss_heads")],
            [InlineKeyboardButton("🪙 TAILS", callback_data="toss_tails")]
        ])
        
        await client.send_message(
            chat_id,
            f"🎉 **Captains Selected!** 🎉\n\n"
            f"🏏 Team A Captain: {cap_a_clickable}\n"
            f"🏏 Team B Captain: {cap_b_clickable}\n\n"
            f"🪙 **TOSS TIME!** 🪙\n\n"
            f"{cap_a_clickable}, choose Heads or Tails:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
        game["status"] = "toss"

    @app.on_callback_query(filters.regex("^toss_heads$|^toss_tails$"))
    async def toss_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "toss":
            await callback.answer("❌ No toss in progress!", show_alert=True)
            return
        
        if game["captain_a"]["id"] != user_id:
            await callback.answer("❌ Only Team A captain can do the toss!", show_alert=True)
            return
        
        choice = callback.data.split("_")[1]
        toss_result = random.choice(["heads", "tails"])
        
        toss_video_url = TOSS_VIDEO
        
        await callback.message.delete()
        
        if choice == toss_result:
            winner_team = "A"
            looser_team = "B"
        else:
            winner_team = "B"
            looser_team = "A"
        
        cap_a_clickable = get_clickable_name(game['captain_a']['id'], game['captain_a']['name'], game['captain_a'].get('username'))
        cap_b_clickable = get_clickable_name(game['captain_b']['id'], game['captain_b']['name'], game['captain_b'].get('username'))
        
        caption_text = f"🪙 The coin shows: {toss_result.upper()}!\n\n"
        caption_text += f"🅰️ - {cap_a_clickable} chose {choice.upper()}\n"
        caption_text += f"🅱️ - {cap_b_clickable} got {toss_result.upper()}\n\n"
        caption_text += f"🏆 Team {winner_team} won the toss & Choose The Bowling First\n\n"
        caption_text += f"🏏 Team {looser_team}: Batting\n"
        caption_text += f"🧤 Team {winner_team}: Bowling"
        
        game["batting_first"] = looser_team
        game["toss_winner"] = winner_team
        
        await client.send_video(chat_id, toss_video_url, caption=caption_text, parse_mode=ParseMode.HTML)
        
        game["status"] = "waiting_startgame"

    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can start the game!")
            return
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "waiting_startgame":
            await message.reply("❌ Toss not completed yet!")
            return
        
        await select_overs(client, chat_id, game["batting_first"])

    async def select_overs(client, chat_id, batting_team):
        game = team_games.get(chat_id)
        if not game:
            print(f"❌ select_overs: No game found for {chat_id}")
            return
        
        print(f"✅ select_overs called for {chat_id}, batting_team={batting_team}")
        
        buttons = []
        row = []
        for i in range(1, 21):
            row.append(InlineKeyboardButton(f"{i}", callback_data=f"over_{i}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        await client.send_message(
            chat_id, 
            f"📊 **Select number of overs:**\n\nChoose overs (1 to 20 overs per side):", 
            reply_markup=keyboard
        )
        
        game["status"] = "over_selection"
        game["batting_first"] = batting_team
        
        print(f"✅ Over selection message sent, status set to over_selection")

    @app.on_callback_query(filters.regex("^over_"))
    async def over_selection_callback(client, callback):
        chat_id = callback.message.chat.id
        print(f"🔴 OVER SELECTION - Chat: {chat_id}, Data: {callback.data}")
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "over_selection":
            await callback.answer("❌ No over selection in progress!", show_alert=True)
            return
        
        overs = int(callback.data.split("_")[1])
        game["overs"] = overs
        game["total_balls_limit"] = overs * 6
        
        await callback.message.delete()
        
        host = team_hosts.get(chat_id)
        host_clickable = get_clickable_name(host['id'], host['name'], host.get('username')) if host else "Host"
        
        batting_team = game["batting_first"]
        batting_name = "Team A" if batting_team == "A" else "Team B"
        bowling_name = "Team B" if batting_team == "A" else "Team A"
        
        cap_a_clickable = get_clickable_name(game['captain_a']['id'], game['captain_a']['name'], game['captain_a'].get('username')) if game['captain_a'] else 'Captain A'
        cap_b_clickable = get_clickable_name(game['captain_b']['id'], game['captain_b']['name'], game['captain_b'].get('username')) if game['captain_b'] else 'Captain B'
        
        await client.send_message(
            chat_id, 
            f"🎉 **Match Set!** 🎉\n\n"
            f"👑 Host: {host_clickable}\n"
            f"🏏 Overs: {overs} Over match\n\n"
            f"🏏 {batting_name} will bat first!\n"
            f"🧤 {bowling_name} will bowl first!\n\n"
            f"{cap_a_clickable} Send Bowler\n"
            f"{cap_b_clickable} Send Strikers & Non-striker Batsman",
            parse_mode=ParseMode.HTML
        )
        
        game["current_team"] = batting_team
        game["status"] = "waiting_bowler"

    @app.on_message(filters.command("bowling") & filters.group)
    async def bowling_selection_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        batting_team = game.get("current_team")
        bowling_team = "B" if batting_team == "A" else "A"
        
        if bowling_team == "A":
            captain = game.get("captain_a")
        else:
            captain = game.get("captain_b")
        
        if not captain or captain["id"] != user_id:
            await message.reply("❌ Only captain can choose bowler!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/bowling <number>`\nExample: `/bowling 1`\n\nUse /members to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        team_key = f"team_{bowling_team.lower()}"
        players = game.get(team_key, [])
        
        if player_num < 1 or player_num > len(players):
            await message.reply(f"❌ Invalid number! Team {bowling_team} has {len(players)} players. Use /members")
            return
        
        selected_bowler = players[player_num - 1].copy()
        game["current_bowler"] = selected_bowler
        game["current_bowler_index"] = player_num - 1
        game["current_bowler_balls"] = 0
        
        bowler_clickable = get_clickable_name(selected_bowler['id'], selected_bowler['name'], selected_bowler.get('username'))
        
        await message.reply(f"⚾ Hey {bowler_clickable}, You're Bowler", parse_mode=ParseMode.HTML)
        
        game["status"] = "waiting_batter"

    @app.on_message(filters.command("batting") & filters.group)
    async def batting_selection_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        batting_team = game.get("current_team")
        
        if batting_team == "A":
            captain = game.get("captain_a")
        else:
            captain = game.get("captain_b")
        
        if not captain or captain["id"] != user_id:
            await message.reply("❌ Only captain can choose batsman!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/batting <number>`\nExample: `/batting 1`\n\nUse /members to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        team_key = f"team_{batting_team.lower()}"
        players = game.get(team_key, [])
        
        if player_num < 1 or player_num > len(players):
            await message.reply(f"❌ Invalid number! Team {batting_team} has {len(players)} players.")
            return
        
        selected_batter = players[player_num - 1].copy()
        
        if selected_batter.get("out", False):
            batter_clickable = get_clickable_name(selected_batter['id'], selected_batter['name'], selected_batter.get('username'))
            await message.reply(f"❌ {batter_clickable} is already OUT!", parse_mode=ParseMode.HTML)
            return
        
        if not game.get("current_batter"):
            game["current_batter"] = selected_batter
            game["current_batter_index"] = player_num - 1
            game["batting_order"] = [player_num - 1]
            game["batting_order_names"] = [selected_batter['name']]
            
            batter_clickable = get_clickable_name(selected_batter['id'], selected_batter['name'], selected_batter.get('username'))
            await message.reply(f"🏏 Hey {batter_clickable}, You're 1st Batsman", parse_mode=ParseMode.HTML)
            
            await message.reply("📝 Choose the second batsman using /batting <number>")
            
        elif len(game.get("batting_order", [])) == 1:
            if player_num - 1 in game["batting_order"]:
                await message.reply("❌ This player already selected as batsman!")
                return
            
            game["batting_order"].append(player_num - 1)
            game["batting_order_names"].append(selected_batter['name'])
            
            batter_clickable = get_clickable_name(selected_batter['id'], selected_batter['name'], selected_batter.get('username'))
            await message.reply(f"🏏 Hey {batter_clickable}, You're 2nd Batsman", parse_mode=ParseMode.HTML)
            
            await message.reply("⏰ Get ready, the game is starting in 10 seconds!")
            
            if os.path.exists(COUNTDOWN_VIDEO_PATH):
                await client.send_video(chat_id, COUNTDOWN_VIDEO_PATH, caption="🎬 Get Ready!")
            else:
                for i in range(10, 0, -1):
                    await client.send_message(chat_id, f"⏰ {i} seconds left...")
                    await asyncio.sleep(1)
            
            await asyncio.sleep(1)
            
            game["team_total"] = 0
            game["team_wickets"] = 0
            game["total_balls_in_inning"] = 0
            game["bowling_number"] = None
            game["status"] = "playing"
            
            await start_team_match(client, chat_id)
        
        else:
            await message.reply("❌ Both batsmen already selected!")

    async def start_team_match(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        batter = game["current_batter"]
        bowler = game["current_bowler"]
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        bowler_clickable = get_clickable_name(bowler['id'], bowler['name'], bowler.get('username'))
        
        await client.send_message(chat_id, f"🎾 Hey {bowler_clickable}, now you're bowling!\n\nNow, type /batting to choose the batting member!", parse_mode=ParseMode.HTML)
        await client.send_message(chat_id, f"🏏 Hey {batter_clickable}, now you're batter!", parse_mode=ParseMode.HTML)
        
        await asyncio.sleep(2)
        
        await send_bowling_video_team(client, chat_id, bowler)

    async def send_bowling_video_team(client, chat_id, bowler):
        game = team_games.get(chat_id)
        if not game or game.get("status") != "playing" or game.get("game_over"):
            return
        
        batter = game["current_batter"]
        bot_username = BOT_USERNAME
        dm_link = f"https://t.me/{bot_username}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎾 Click to Bowl", url=dm_link)]
        ])
        
        bowler_clickable = get_clickable_name(bowler['id'], bowler['name'], bowler.get('username'))
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"Hey {bowler_clickable}, You're Bowler",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        
        try:
            await client.send_message(
                bowler["id"],
                f"🎾 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        if chat_id in bowling_tasks:
            try:
                bowling_tasks[chat_id].cancel()
            except:
                pass
        
        task = asyncio.create_task(bowling_timeout_with_warnings_team(client, chat_id, bowler["id"], bowler['name'], bowler_clickable))
        bowling_tasks[chat_id] = task

    async def bowling_timeout_with_warnings_team(client, chat_id, user_id, bowler_name, bowler_clickable):
        await asyncio.sleep(30)
        game = team_games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                try:
                    await client.send_message(
                        chat_id,
                        f"⚠️ Warning: {bowler_clickable}, you have 30 seconds left to send a number!",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        
        await asyncio.sleep(20)
        game = team_games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                try:
                    await client.send_message(
                        chat_id,
                        f"⚠️ Warning: {bowler_clickable}, you have 10 seconds left to send a number!",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        
        await asyncio.sleep(10)
        game = team_games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                
                if chat_id not in bowler_consecutive_timeouts:
                    bowler_consecutive_timeouts[chat_id] = {}
                if user_id not in bowler_consecutive_timeouts[chat_id]:
                    bowler_consecutive_timeouts[chat_id][user_id] = 0
                
                bowler_consecutive_timeouts[chat_id][user_id] += 1
                current_timeout = bowler_consecutive_timeouts[chat_id][user_id]
                
                bowling_team = "B" if game["current_team"] == "A" else "A"
                team_key = f"team_{bowling_team.lower()}"
                
                if current_timeout >= 2:
                    player_removed = False
                    removed_player_name = None
                    for i, player in enumerate(game[team_key]):
                        if player["id"] == user_id:
                            removed_player_name = player.get('name')
                            game[team_key].pop(i)
                            player_removed = True
                            break
                    
                    if player_removed:
                        await client.send_message(
                            chat_id,
                            f"❌ {bowler_clickable} has been removed from the game due to 2 consecutive timeouts!",
                            parse_mode=ParseMode.HTML
                        )
                        
                        if user_id in bowler_consecutive_timeouts[chat_id]:
                            del bowler_consecutive_timeouts[chat_id][user_id]
                        
                        if len(game[team_key]) == 0:
                            winner = "A" if bowling_team == "B" else "B"
                            await end_match_team(client, chat_id, winner)
                            return
                        
                        current_batter = game.get("current_batter", {})
                        available_bowlers = [p for p in game[team_key] if p["id"] != current_batter.get("id")]
                        
                        if len(available_bowlers) == 0:
                            available_bowlers = game[team_key]
                        
                        new_bowler = available_bowlers[0].copy() if len(available_bowlers) > 0 else game[team_key][0].copy()
                        if new_bowler:
                            game["current_bowler"] = new_bowler
                            game["current_bowler_index"] = 0
                            game["current_bowler_balls"] = 0
                            await send_bowling_video_team(client, chat_id, new_bowler)
                        return
                else:
                    for player in game[team_key]:
                        if player["id"] == user_id:
                            player["score"] -= 6
                            player["history"].append("-6")
                            break
                    
                    game["team_total"] = sum(p["score"] for p in game[team_key])
                    
                    try:
                        await client.send_video(
                            chat_id,
                            get_run_video(6),
                            caption=f"No message received from bowler, deducting 6 runs from {bowling_team} team. (Consecutive timeout {current_timeout}/2)"
                        )
                    except:
                        await client.send_message(
                            chat_id,
                            f"No message received from bowler, deducting 6 runs from {bowling_team} team. (Consecutive timeout {current_timeout}/2)"
                        )
                    
                    await client.send_message(chat_id, build_team_scoreboard(game))
                    
                    game["bowling_number"] = None
                    game["current_bowler_balls"] += 1
                    game["total_balls_in_inning"] += 1
                    
                    if game["current_bowler_balls"] >= 6:
                        players = game[team_key]
                        current_batter = game.get("current_batter", {})
                        new_bowler_index = (game["current_bowler_index"] + 1) % len(players)
                        
                        start_index = new_bowler_index
                        while players[new_bowler_index].get("out", False) or players[new_bowler_index]["id"] == current_batter.get("id"):
                            new_bowler_index = (new_bowler_index + 1) % len(players)
                            if new_bowler_index == start_index:
                                break
                        
                        game["current_bowler_index"] = new_bowler_index                    
                        game["current_bowler"] = players[new_bowler_index].copy()
                        game["current_bowler_balls"] = 0
                    
                    await send_bowling_video_team(client, chat_id, game["current_bowler"])
        
        if chat_id in bowling_tasks:
            del bowling_tasks[chat_id]

    async def send_batting_video_team(client, chat_id, batter, bowler_number):
        game = team_games.get(chat_id)
        if not game or game.get("status") != "playing":
            return
        
        balls = game.get("total_balls_in_inning", 0)
        overs = balls // 6
        remaining_balls = balls % 6
        over_display = f"{overs}.{remaining_balls}"
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        
        await client.send_video(
            chat_id,
            BATTING_VIDEO,
            caption=f"Batter :- {batter_clickable}\n\nOver {over_display}",
            parse_mode=ParseMode.HTML
        )
        
        try:
            await client.send_message(
                batter["id"],
                f"🏏 Send batting number (1-6):\n\n⏰ You have 60 seconds!"
            )
        except:
            pass

    @app.on_message(filters.private & filters.text)
    async def game_numbers_dm(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        if text.startswith("/"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply("❌ Send number 1-6 only!")
        
        num = int(text)
        
        for chat_id, game in games.items():
            if game.get("status") != "playing":
                continue
            
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                game["bowling_number"] = num
                reset_bowler_consecutive_timeout(chat_id, user_id)
                await message.reply(f"✅ Bowling number {num} sent!")
                
                if chat_id in bowling_tasks:
                    try:
                        bowling_tasks[chat_id].cancel()
                    except:
                        pass
                    del bowling_tasks[chat_id]
                
                batter = game["current_batter"]
                batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
                await client.send_video(chat_id, BATTING_VIDEO, caption=f"Hey {batter_clickable}, now you're batting! Send number (1-6) in GROUP", parse_mode=ParseMode.HTML)
                return
        
        for chat_id, game in team_games.items():
            if game.get("status") != "playing":
                continue
            
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                game["bowling_number"] = num
                reset_bowler_consecutive_timeout(chat_id, user_id)
                await message.reply(f"✅ Bowling number {num} sent!")
                
                if chat_id in bowling_tasks:
                    try:
                        bowling_tasks[chat_id].cancel()
                    except:
                        pass
                    del bowling_tasks[chat_id]
                
                batter = game["current_batter"]
                await send_batting_video_team(client, chat_id, batter, num)
                return
        
        for chat_id, game in team_games.items():
            if game.get("status") != "playing":
                continue
            
            current_batter = game.get("current_batter", {})
            if current_batter.get("id") == user_id and game.get("bowling_number") is not None:
                bowled_num = game["bowling_number"]
                game["bowling_number"] = None
                
                if num == bowled_num:
                    await process_out_team(client, chat_id, current_batter)
                else:
                    await process_runs_team(client, chat_id, current_batter, num)
                
                await message.reply(f"✅ Batting number {num} sent!")
                return
        
        await message.reply("❌ No active game or not your turn!")

    async def process_out_team(client, chat_id, batter):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{game['current_team'].lower()}"
        bowler = game["current_bowler"]
        
        for p in game[team_key]:
            if p["id"] == batter["id"]:
                p["out"] = True
                p["history"].append("W")
                break
        
        game["team_wickets"] += 1
        
        batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
        
        try:
            await client.send_video(
                chat_id, 
                OUT_VIDEO, 
                caption=f"❌ Out {batter_clickable}",
                parse_mode=ParseMode.HTML
            )
        except:
            await client.send_message(chat_id, f"❌ Out {batter_clickable}", parse_mode=ParseMode.HTML)
        
        active_batters = [p for p in game[team_key] if not p.get("out", False)]
        
        if len(active_batters) == 0 or game["team_wickets"] >= len(game[team_key]):
            await end_innings_team(client, chat_id)
            return
        
        batting_order = game.get("batting_order", [])
        current_index_in_order = None
        
        for idx, player_idx in enumerate(batting_order):
            if player_idx == game["current_batter_index"]:
                current_index_in_order = idx
                break
        
        next_batter_index = None
        if current_index_in_order is not None:
            for i in range(current_index_in_order + 1, len(batting_order)):
                player_idx = batting_order[i]
                if not game[team_key][player_idx].get("out", False):
                    next_batter_index = player_idx
                    break
        
        if next_batter_index is None:
            for i, p in enumerate(game[team_key]):
                if not p.get("out", False):
                    next_batter_index = i
                    break
        
        if next_batter_index is not None:
            game["current_batter_index"] = next_batter_index
            game["current_batter"] = game[team_key][next_batter_index].copy()
            
            next_batter = game["current_batter"]
            next_batter_clickable = get_clickable_name(next_batter['id'], next_batter['name'], next_batter.get('username'))
            next_batter_number = next_batter_index + 1
            
            await client.send_message(chat_id, f"🎾 Next Batsman: {next_batter_number} {next_batter_clickable}", parse_mode=ParseMode.HTML)
            
            if next_batter_index not in batting_order:
                game["batting_order"].append(next_batter_index)
            
            await send_bowling_video_team(client, chat_id, game["current_bowler"])
        else:
            await end_innings_team(client, chat_id)

    async def process_runs_team(client, chat_id, batter, runs):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{game['current_team'].lower()}"
        
        for p in game[team_key]:
            if p["id"] == batter["id"]:
                p["score"] += runs
                p["balls"] += 1
                if runs == 4:
                    p["fours"] += 1
                elif runs == 6:
                    p["sixes"] += 1
                p["history"].append(str(runs))
                break
        
        game["team_total"] += runs
        game["total_balls_in_inning"] += 1
        game["current_bowler_balls"] += 1
        
        try:
            await client.send_video(chat_id, get_run_video(runs))
        except:
            await client.send_message(chat_id, f"🏏 {runs} runs!")
        
        if game["current_team"] == "B":
            target = game.get("target", 0)
            if target > 0 and game["team_total"] >= target:
                await end_match_team(client, chat_id, "B")
                return
        
        if game["total_balls_in_inning"] >= game["total_balls_limit"] and game["total_balls_limit"] > 0:
            await end_innings_team(client, chat_id)
            return
        
        if game["current_bowler_balls"] >= 6:
            await change_bowler_team(client, chat_id)
        else:
            await client.send_message(chat_id, build_team_scoreboard(game))
            await send_bowling_video_team(client, chat_id, game["current_bowler"])

    async def change_bowler_team(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        bowling_team = "B" if game["current_team"] == "A" else "A"
        team_key = f"team_{bowling_team.lower()}"
        players = game[team_key]
        
        current_index = game.get("current_bowler_index", 0)
        new_index = (current_index + 1) % len(players)
        
        current_batter = game.get("current_batter", {})
        start_index = new_index
        
        while (players[new_index].get("out", False) or players[new_index]["id"] == current_batter.get("id")) and new_index != start_index:
            new_index = (new_index + 1) % len(players)
        
        if players[new_index].get("out", False) or players[new_index]["id"] == current_batter.get("id"):
            new_index = (current_index + 1) % len(players)
        
        game["current_bowler_index"] = new_index
        game["current_bowler"] = players[new_index].copy()
        game["current_bowler_balls"] = 0
        
        bowler = game["current_bowler"]
        bowler_clickable = get_clickable_name(bowler['id'], bowler['name'], bowler.get('username'))
        
        await client.send_message(chat_id, f"🔄 Over complete! New bowler: {bowler_clickable}", parse_mode=ParseMode.HTML)
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    async def end_innings_team(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        if game["current_team"] == "A":
            game["team_a_score"] = game["team_total"]
            game["team_a_wickets"] = game["team_wickets"]
            overs_played = game["total_balls_in_inning"]
            game["team_a_overs"] = f"{overs_played // 6}.{overs_played % 6}"
            
            target = game["team_a_score"] + 1
            
            await client.send_message(
                chat_id,
                f"🏏 **Team A Innings Complete!**\n\n"
                f"📊 Score: {game['team_a_score']}/{game['team_a_wickets']}\n"
                f"📈 Overs: {game['team_a_overs']} / {game['overs']} overs\n\n"
                f"🎾 **Team B needs {target} runs to win!**\n\n"
                f"⚾ Host: Use /bowling <number> to choose first bowler for Team B\n"
                f"📝 Use /members to see player numbers"
            )
            
            game["current_team"] = "B"
            game["current_batter"] = None
            game["current_bowler"] = None
            game["batting_order"] = []
            game["batting_order_names"] = []
            game["team_total"] = 0
            game["team_wickets"] = 0
            game["total_balls_in_inning"] = 0
            game["bowling_number"] = None
            game["status"] = "waiting_bowler"
            game["target"] = target
            game["game_over"] = False
            
        else:
            game["team_b_score"] = game["team_total"]
            game["team_b_wickets"] = game["team_wickets"]
            overs_played = game["total_balls_in_inning"]
            game["team_b_overs"] = f"{overs_played // 6}.{overs_played % 6}"
            
            if game["team_b_score"] > game["team_a_score"]:
                winner = "B"
            elif game["team_b_score"] < game["team_a_score"]:
                winner = "A"
            else:
                winner = "Tie"
            
            await end_match_team(client, chat_id, winner)

    async def end_match_team(client, chat_id, winner):
        game = team_games.get(chat_id)
        if not game:
            return
        
        game["game_over"] = True
        
        winner_name = "Team A" if winner == "A" else "Team B" if winner == "B" else "Match Tied"
        
        final_text = f"🏆 **Team {winner_name} wins this game!** 🎉\n\n"
        final_text += f"🏆 Game Results 🏆\n"
        final_text += f"Winner: {winner_name}\n\n"
        final_text += f"Team A: {game['team_a_score']}/{game['team_a_wickets']} ({game.get('team_a_overs', '0.0')} overs)\n"
        final_text += f"Team B: {game['team_b_score']}/{game['team_b_wickets']} ({game.get('team_b_overs', '0.0')} overs)\n\n"
        
        final_text += "╭━─━─━─━─≪✠≫─━─━─━─━╮\n\n"
        
        final_text += "───────⊱ Tᴇᴀᴍ - A ⊰──────\n\n"
        for p in game.get("team_a", []):
            player_clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
            final_text += f"✴️ {player_clickable} = {p['score']}({p['balls']})\n"
            final_text += f"  ╰⊚ ID : {p['id']}\n"
            if p.get('out', False):
                final_text += f"    ╰⊚ (W)\n"
        final_text += f"\n╭──────── • ◆ • ─────────\n"
        final_text += f"ᴛᴇᴀᴍ A sᴄᴏʀᴇ = {game['team_a_score']}/{game['team_a_wickets']} ʀᴜɴs | ᴏᴠᴇʀs: {game.get('team_a_overs', '0.0')}\n"
        final_text += f"╰──────── • ◆ • ─────────\n\n"
        
        final_text += f"× •-•-•-•-•-••-•-•⟮ 🏏 ⟯•-•-•-•-•-•-•-•-• ×\n\n"
        
        final_text += "───────⊱ Tᴇᴀᴍ - B ⊰──────\n\n"
        for p in game.get("team_b", []):
            player_clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
            final_text += f"✴️ {player_clickable} = {p['score']}({p['balls']})\n"
            final_text += f"  ╰⊚ ID : {p['id']}\n"
            if p.get('out', False):
                final_text += f"    ╰⊚ (W)\n"
        final_text += f"\n╭──────── • ◆ • ─────────\n"
        final_text += f"ᴛᴇᴀᴍ B sᴄᴏʀᴇ = {game['team_b_score']}/{game['team_b_wickets']} ʀᴜɴs | ᴏᴠᴇʀs: {game.get('team_b_overs', '0.0')}\n"
        final_text += f"╰──────── • ◆ • ─────────\n\n"
        
        host = team_hosts.get(chat_id, {})
        host_clickable = get_clickable_name(host.get('id', 0), host.get('name', 'Unknown'), host.get('username'))
        final_text += f"༺═────────────────═༻\n\n"
        final_text += f"👑Host: {host_clickable}"
        
        await client.send_message(chat_id, final_text, parse_mode=ParseMode.HTML)
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        if chat_id in bowler_consecutive_timeouts:
            del bowler_consecutive_timeouts[chat_id]

    @app.on_message(filters.command("swap") & filters.group)
    async def swap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can swap!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        if game.get("game_over"):
            await message.reply("❌ Game already over!")
            return
        
        if game.get("current_team") == "B" and game.get("team_total") > 0:
            await message.reply("❌ Second innings already in progress! Cannot swap.")
            return
        
        if game.get("team_a_score") > 0 or game.get("team_a_wickets") > 0:
            if game.get("status") == "waiting_bowler" or game.get("current_team") == "B":
                await message.reply("⚠️ Second innings starting! Please choose bowler by /bowling <number>")
                return
        
        host_clickable = get_clickable_name(host['id'], host['name'], host.get('username'))
        await client.send_message(chat_id, f"⚠️ Innings changed! Hey {host_clickable}, Please choose the bowler by command /bowling.", parse_mode=ParseMode.HTML)
        await end_innings_team(client, chat_id)

    @app.on_message(filters.command("members") & filters.group)
    async def members_cmd(client, message: Message):
        chat_id = message.chat.id
        
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not solo_game and not team_game:
            try:
                total = 0
                admins = []
                members = []
                bots = []
                
                async for m in client.get_chat_members(chat_id):
                    total += 1
                    if m.user.is_bot:
                        bots.append(m.user.first_name)
                    elif m.status.value in ['administrator', 'creator']:
                        admin_name = get_clickable_name(m.user.id, m.user.first_name, m.user.username)
                        admins.append(admin_name)
                    else:
                        member_name = get_clickable_name(m.user.id, m.user.first_name, m.user.username)
                        members.append(member_name)
                
                text = f"📊 **Group Members**\n\n"
                text += f"👥 Total Members: {total}\n"
                text += f"👑 Admins: {len(admins)}\n"
                text += f"👤 Members: {len(members)}\n"
                text += f"🤖 Bots: {len(bots)}\n\n"
                
                if admins:
                    text += "**👑 Admins:**\n" + "\n".join(admins[:10]) + "\n\n"
                if members:
                    text += "**👤 Members (First 10):**\n" + "\n".join(members[:10]) + "\n\n"
                if bots:
                    text += "**🤖 Bots:**\n" + "\n".join(bots)
                
                await message.reply(text, parse_mode=ParseMode.HTML)
            except Exception as e:
                await message.reply(f"❌ Error: {e}")
            return
        
        if team_game:
            host_clickable = get_clickable_name(host['id'], host['name'], host.get('username')) if host else "Unknown"
            
            current_team = team_game.get("current_team", "None")
            batting_team = current_team if current_team != "None" else "None"
            
            if batting_team == "A":
                bowling_team = "B"
            elif batting_team == "B":
                bowling_team = "A"
            else:
                bowling_team = "None"
            
            innings_status = f" Innings {batting_team}" if batting_team != "None" else ""
            
            cap_a = team_game.get("captain_a")
            cap_b = team_game.get("captain_b")
            
            cap_a_name = get_clickable_name(cap_a['id'], cap_a['name'], cap_a.get('username')) if cap_a else "None"
            cap_b_name = get_clickable_name(cap_b['id'], cap_b['name'], cap_b.get('username')) if cap_b else "None"
            
            team_a_list = ""
            for i, p in enumerate(team_game.get("team_a", []), 1):
                player_clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
                if cap_a and p["id"] == cap_a["id"]:
                    team_a_list += f"{i}. {player_clickable} (🧢)\n"
                else:
                    team_a_list += f"{i}. {player_clickable}\n"
            
            team_b_list = ""
            for i, p in enumerate(team_game.get("team_b", []), 1):
                player_clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
                if cap_b and p["id"] == cap_b["id"]:
                    team_b_list += f"{i}. {player_clickable} (🧢)\n"
                else:
                    team_b_list += f"{i}. {player_clickable}\n"
            
            text = f"👑 **Host:** {host_clickable}\n\n"
            
            text += f"🎩 **Captain A (🧢):** {cap_a_name}\n"
            text += f"👒 **Captain B:** {cap_b_name}\n\n"
            
            text += "🔵 **Team A**\n"
            text += team_a_list if team_a_list else "   No players\n"
            text += "\n"
            
            text += "🔴 **Team B**\n"
            text += team_b_list if team_b_list else "   No players\n"
            
            await message.reply(text, parse_mode=ParseMode.HTML)
        
        elif solo_game:
            host_name = solo_game.get("host_name", "Unknown")
            host_clickable = get_clickable_name(0, host_name) if host_name != "Unknown" else "Unknown"
            
            players = solo_game.get("players", [])
            current_batter = solo_game.get("current_batter")
            current_bowler = solo_game.get("current_bowler")
            
            batter_clickable = get_clickable_name(current_batter['id'], current_batter['name'], current_batter.get('username')) if current_batter else "None"
            bowler_clickable = get_clickable_name(current_bowler['id'], current_bowler['name'], current_bowler.get('username')) if current_bowler else "None"
            
            players_list = ""
            for i, p in enumerate(players, 1):
                player_clickable = get_clickable_name(p['id'], p['name'], p.get('username'))
                status = "❌ OUT" if p.get("out", False) else "🏏 PLAYING"
                players_list += f"{i}. {player_clickable} - {status}\n"
            
            text = f"👽 **Game Host:** {host_clickable}\n\n"
            text += f"🏏 **Solo Mode**\n\n"
            text += f"🎾 **Current Batter:** {batter_clickable}\n"
            text += f"⚾ **Current Bowler:** {bowler_clickable}\n\n"
            text += f"📊 **Players List:**\n{players_list if players_list else '   No players'}"
            
            await message.reply(text, parse_mode=ParseMode.HTML)

    # ================= START TEAM BATTING =================
    async def start_team_batting(client, chat_id, team):
        print(f"🔴 START_TEAM_BATTING - Chat: {chat_id}, Team: {team}")
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{team.lower()}"
        players = game[team_key]
        
        for p in players:
            p["score"] = 0
            p["balls"] = 0
            p["fours"] = 0
            p["sixes"] = 0
            p["out"] = False
            p["history"] = []
        
        game["current_team"] = team
        game["current_batter_index"] = 0
        game["current_batter"] = players[0].copy()
        
        if len(players) == 1:
            game["current_bowler_index"] = 0
            game["current_bowler"] = players[0].copy()
        else:
            game["current_bowler_index"] = 1 if len(players) > 1 else 0
            if game["current_bowler_index"] == game["current_batter_index"]:
                game["current_bowler_index"] = (game["current_bowler_index"] + 1) % len(players)
            game["current_bowler"] = players[game["current_bowler_index"]].copy()
        
        game["current_bowler_balls"] = 0
        game["bowling_number"] = None
        game["team_total"] = 0
        game["team_wickets"] = 0
        game["total_balls_in_inning"] = 0
        
        batter_clickable = get_clickable_name(game['current_batter']['id'], game['current_batter']['name'], game['current_batter'].get('username'))
        bowler_clickable = get_clickable_name(game['current_bowler']['id'], game['current_bowler']['name'], game['current_bowler'].get('username'))
        
        await client.send_message(chat_id, f"🏏 **Team {team} Batting**\n\nBatter: {batter_clickable}\nBowler: {bowler_clickable}", parse_mode=ParseMode.HTML)
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    # ================= BATTING (group message) =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message: Message):
        text = message.text.strip()
        
        if text.startswith('/'):
            return
        
        if not text.isdigit():
            return
        num = int(text)
        if num < 1 or num > 6:
            return
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        print(f"🔴 BATTING MSG - Chat: {chat_id}, User: {user_id}, Text: {text}")
        
        team_game = team_games.get(chat_id)
        if team_game:
            if team_game.get("status") != "playing" or team_game.get("game_over"):
                return
            
            if team_game.get("bowling_number") is None:
                await message.reply("⏳ Wait for bowler to bowl first!")
                return
            
            batter = team_game.get("current_batter")
            if not batter or batter.get("id") != user_id:
                await message.reply("❌ You are not the current batter!")
                return
            
            try:
                await message.reply("👍")
            except:
                pass
            
            bat = num
            bow = team_game.get("bowling_number")
            team_game["bowling_number"] = None
            
            if bat == bow:
                await process_out_team(client, chat_id, batter)
            else:
                await process_runs_team(client, chat_id, batter, bat)
            return
        
        game = games.get(chat_id)
        if game:
            if game.get("status") != "playing" or game.get("game_over") or game.get("bowling_number") is None:
                return
            
            batter = game.get("current_batter")
            if not batter or message.from_user.id != batter.get("id"):
                return
            
            try:
                await message.reply("👍")
            except:
                pass
            
            bat = num
            result = play_ball(chat_id, bat)
            game["bowling_number"] = None
            bowler = game["current_bowler"]
            
            if result["type"] == "out":
                batter_clickable = get_clickable_name(batter['id'], batter['name'], batter.get('username'))
                
                try:
                    await message.reply_video(OUT_VIDEO, caption=f"❌ Out {batter_clickable}")
                except:
                    await message.reply(f"❌ Out {batter_clickable}")
                
                # Mark current batter as out
                for p in game["players"]:
                    if p["id"] == batter["id"]:
                        p["out"] = True
                        break
                
                game["wickets"] = game.get("wickets", 0) + 1
                
                # Get all players
                all_players = game["players"]
                active_players = [p for p in all_players if not p.get("out", False)]
                
                # IMPORTANT: For 2 players game, when one is out, swap roles and continue
                if len(active_players) == 1:
                    # Only one player left (the bowler)
                    # Swap roles: remaining player becomes batter, out player becomes bowler
                    remaining_player = active_players[0]
                    out_player = None
                    for p in all_players:
                        if p.get("out", False):
                            out_player = p
                            break
                    
                    if remaining_player and out_player:
                        # Remaining player becomes batter
                        game["current_batter"] = remaining_player
                        # Out player becomes bowler (still out can bowl)
                        game["current_bowler"] = out_player
                        game["current_bowler_balls"] = 0
                        
                        remaining_clickable = get_clickable_name(remaining_player['id'], remaining_player['name'], remaining_player.get('username'))
                        out_clickable = get_clickable_name(out_player['id'], out_player['name'], out_player.get('username'))
                        
                        await client.send_message(chat_id, f"🔄 Roles Swapped!\n🏏 New Batter: {remaining_clickable}\n🎾 New Bowler: {out_clickable}", parse_mode=ParseMode.HTML)
                        
                        # Show scoreboard
                        await client.send_message(chat_id, build_scoreboard(all_players, is_final=False), parse_mode=ParseMode.HTML)
                        
                        # Send bowling video to new bowler
                        await send_bowling_video_solo(client, chat_id, out_player)
                        return
                
                # If no active players left, game over
                if len(active_players) == 0:
                    final_scoreboard = build_scoreboard(all_players, is_final=True)
                    await client.send_message(chat_id, final_scoreboard, parse_mode=ParseMode.HTML)
                    if chat_id in games:
                        del games[chat_id]
                    if chat_id in bowler_consecutive_timeouts:
                        del bowler_consecutive_timeouts[chat_id]
                    return
                
                # Show updated scoreboard
                await client.send_message(chat_id, build_scoreboard(all_players, is_final=False), parse_mode=ParseMode.HTML)
                
                # Find next batter
                next_batter = None
                for p in all_players:
                    if not p.get("out", False) and p["id"] != bowler["id"]:
                        next_batter = p
                        break
                
                if next_batter is None:
                    for p in all_players:
                        if not p.get("out", False):
                            next_batter = p
                            break
                
                if next_batter:
                    game["current_batter"] = next_batter
                    next_batter_clickable = get_clickable_name(next_batter['id'], next_batter['name'], next_batter.get('username'))
                    await client.send_message(chat_id, f"🎾 Next Batsman: {next_batter_clickable}", parse_mode=ParseMode.HTML)
                    
                    # Select new bowler
                    active_bowlers = [p for p in all_players if not p.get("out", False) and p["id"] != next_batter["id"]]
                    if len(active_bowlers) == 0:
                        active_bowlers = [p for p in all_players if not p.get("out", False)]
                    
                    new_bowler = active_bowlers[0] if active_bowlers else all_players[0]
                    game["current_bowler"] = new_bowler
                    game["current_bowler_balls"] = 0
                    
                    new_bowler_clickable = get_clickable_name(new_bowler['id'], new_bowler['name'], new_bowler.get('username'))
                    await client.send_message(chat_id, f"⚾ New bowler: {new_bowler_clickable}", parse_mode=ParseMode.HTML)
                    await send_bowling_video_solo(client, chat_id, game["current_bowler"])
                else:
                    final_scoreboard = build_scoreboard(all_players, is_final=True)
                    await client.send_message(chat_id, final_scoreboard, parse_mode=ParseMode.HTML)
                    if chat_id in games:
                        del games[chat_id]
                    if chat_id in bowler_consecutive_timeouts:
                        del bowler_consecutive_timeouts[chat_id]
                return
            else:
                # Not out - add runs
                try:
                    await message.reply_video(get_run_video(result["runs"]))
                except:
                    await message.reply(f"🏏 {result['runs']} runs!")
                
                game["current_bowler_balls"] = game.get("current_bowler_balls", 0) + 1
                
                # Check if over complete (6 balls)
                if game["current_bowler_balls"] >= 6:
                    all_players = game["players"]
                    current_batter = game["current_batter"]
                    
                    # Find new bowler
                    active_bowlers = [p for p in all_players if not p.get("out", False) and p["id"] != current_batter["id"]]
                    if len(active_bowlers) == 0:
                        active_bowlers = [p for p in all_players if not p.get("out", False)]
                    
                    # Rotate to next bowler
                    current_bowler_id = game["current_bowler"]["id"]
                    new_bowler = None
                    
                    for i, p in enumerate(active_bowlers):
                        if p["id"] == current_bowler_id:
                            next_idx = (i + 1) % len(active_bowlers)
                            new_bowler = active_bowlers[next_idx]
                            break
                    
                    if new_bowler is None and len(active_bowlers) > 0:
                        new_bowler = active_bowlers[0]
                    
                    if new_bowler:
                        game["current_bowler"] = new_bowler
                        game["current_bowler_balls"] = 0
                        
                        new_bowler_clickable = get_clickable_name(new_bowler['id'], new_bowler['name'], new_bowler.get('username'))
                        await client.send_message(chat_id, f"🔄 Over complete! New bowler: {new_bowler_clickable}", parse_mode=ParseMode.HTML)
                
                if not game.get("game_over"):
                    await send_bowling_video_solo(client, chat_id, game["current_bowler"])
            return

    # ================= VOTE SYSTEM =================
    
    async def vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"Voting in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        caption = "🗳️ **VOTING REQUIRED!** 🗳️\n\nYou are not an admin. 3 votes needed.\n\nCurrent votes: 0/3"
        
        try:
            msg = await message.reply_photo(VOTE_IMG, caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
        except:
            msg = await message.reply(caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
        
        active_votes[chat_id]["msg_id"] = msg.id
        asyncio.create_task(auto_cancel_vote(client, chat_id))

    @app.on_callback_query(filters.regex("^vote$"))
    async def vote_handler(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        vote = active_votes.get(chat_id)
        if not vote or not vote.get("active"):
            return await callback.answer("No active voting!", show_alert=True)
        
        if user.id in vote["users"]:
            return await callback.answer("Already voted!", show_alert=True)
        
        vote["users"].append(user.id)
        vote["count"] += 1
        
        if vote["count"] >= 3:
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            vote["active"] = False
            await callback.answer("Voting successful!")
        else:
            voters = []
            for uid in vote["users"]:
                try:
                    u = await client.get_users(uid)
                    voters.append(f"• {u.first_name}")
                except:
                    voters.append(f"• User_{uid}")
            
            caption = f"🗳️ **VOTING REQUIRED!** 🗳️\n\nYou are not an admin. 3 votes needed.\n\nCurrent votes: {vote['count']}/3\n\n**Voters:**\n{chr(10).join(voters)}"
            
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
            except:
                await callback.message.edit_text(caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
            await callback.answer(f"Voted! ({vote['count']}/3)")

    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote = active_votes.get(chat_id)
        if vote and vote.get("active") and vote["count"] < 3:
            try:
                await client.edit_message_caption(chat_id, vote["msg_id"], caption=f"❌ Voting expired! Got {vote['count']}/3 votes.\nUse /start again.")
            except:
                pass
            vote["active"] = False

    print("🔴 ✅ ALL HANDLERS REGISTERED SUCCESSFULLY!")
