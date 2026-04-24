from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
from solo.score import get_live_score
import asyncio
from datetime import datetime
import random

print("🔴 LOADING HANDLERS.PY - FINAL VERSION")

active_votes = {}
bowling_tasks = {}

# ================= TEAM MODE VARIABLES =================
team_games = {}
team_hosts = {}
user_reports = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ================= SOLO MODE SEND BOWLING VIDEO =================
async def send_bowling_video(client, chat_id, bowler):
    game = games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        return
    
    batter = game["current_batter"]
    bot_username = BOT_USERNAME
    dm_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Click to Bowl", url=dm_link)]
    ])
    
    bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
    
    await client.send_video(
        chat_id, 
        BOWLING_VIDEO,
        caption=f"{bowler_clickable} now you can send number on bot pm, You have 1 min.",
        reply_markup=keyboard
    )
    
    batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
    
    try:
        await client.send_message(
            bowler["id"],
            f"🎯 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
            disable_web_page_preview=True
        )
    except:
        pass
    
    if chat_id in bowling_tasks:
        try:
            bowling_tasks[chat_id].cancel()
        except:
            pass
    
    task = asyncio.create_task(bowling_timeout_with_warnings(client, chat_id, bowler["id"], bowler["name"], None))
    bowling_tasks[chat_id] = task

# ================= SOLO MODE TIMEOUT =================
async def bowling_timeout_with_warnings(client, chat_id, user_id, bowler_name, message_id):
    await asyncio.sleep(30)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 30 seconds left to send a number!"
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
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 10 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(10)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            
            for player in game["players"]:
                if player["id"] == user_id:
                    player["score"] -= 6
                    player["history"].append("-6")
                    break
            
            try:
                await client.send_video(
                    chat_id,
                    get_run_video(6),
                    caption=f"No message received from bowler, deducting 6 runs from {bowler_name}'s score."
                )
            except:
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs from {bowler_name}'s score."
                )
            
            await client.send_message(chat_id, build_scoreboard(game["players"], is_final=False))
            
            game["bowling_number"] = None
            game["current_bowler_balls"] += 1
            game["total_balls_in_match"] += 1
            
            await send_bowling_video(client, chat_id, game["current_bowler"])
    
    if chat_id in bowling_tasks:
        del bowling_tasks[chat_id]

# ================= TEAM MODE SEND BOWLING VIDEO =================
async def send_bowling_video_team(client, chat_id, bowler):
    game = team_games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        return
    
    batter = game["current_batter"]
    bot_username = BOT_USERNAME
    dm_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Click to Bowl", url=dm_link)]
    ])
    
    bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
    
    await client.send_video(
        chat_id, 
        BOWLING_VIDEO,
        caption=f"{bowler_clickable} now you can send number on bot pm, You have 1 min.",
        reply_markup=keyboard
    )
    
    batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
    
    try:
        await client.send_message(
            bowler["id"],
            f"🎯 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
            disable_web_page_preview=True
        )
    except:
        pass
    
    if chat_id in bowling_tasks:
        try:
            bowling_tasks[chat_id].cancel()
        except:
            pass
    
    task = asyncio.create_task(bowling_timeout_with_warnings_team(client, chat_id, bowler["id"], bowler["name"], None))
    bowling_tasks[chat_id] = task

# ================= TEAM MODE TIMEOUT =================
async def bowling_timeout_with_warnings_team(client, chat_id, user_id, bowler_name, message_id):
    await asyncio.sleep(30)
    game = team_games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 30 seconds left to send a number!"
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
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 10 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(10)
    game = team_games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            
            team_key = f"team_{game['current_team'].lower()}"
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
                    caption=f"No message received from bowler, deducting 6 runs from {game['current_team']} team."
                )
            except:
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs from {game['current_team']} team."
                )
            
            await client.send_message(chat_id, build_team_scoreboard(game))
            
            game["bowling_number"] = None
            game["current_bowler_balls"] += 1
            game["total_balls_in_inning"] += 1
            
            if game["current_bowler_balls"] >= 6:
                players = game[team_key]
                new_bowler_index = (game["current_bowler_index"] + 1) % len(players)
                game["current_bowler_index"] = new_bowler_index
                game["current_bowler"] = players[new_bowler_index].copy()
                game["current_bowler_balls"] = 0
            
            await send_bowling_video_team(client, chat_id, game["current_bowler"])
    
    if chat_id in bowling_tasks:
        del bowling_tasks[chat_id]

def build_team_scoreboard(game):
    team_key = f"team_{game['current_team'].lower()}"
    players = game[team_key]
    
    scoreboard = f"🏏 **{game['current_team']} Team Scoreboard** 🏏\n\n"
    scoreboard += f"**Total:** {game['team_total']}/{game['team_wickets']}\n"
    scoreboard += f"**Balls:** {game['total_balls_in_inning']}\n\n"
    scoreboard += "**Players:**\n"
    
    for p in players:
        status = "❌" if p.get("out", False) else "🏏"
        scoreboard += f"{status} {p['name']}: {p['score']} ({p['balls']} balls)"
        if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
            scoreboard += f" [4s:{p['fours']} 6s:{p['sixes']}]"
        scoreboard += "\n"
    
    return scoreboard

def register_handlers(app):
    print("🔴 REGISTERING HANDLERS...")

    # ================= START COMMAND =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
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
                    await message.reply("🎯 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
                    return
        
        for chat_id, game in team_games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply("🎯 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
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
/end_match - End current match (Admin)
/solo_leave - Leave solo game

**TEAM MODE:**
/create_team - Create teams (Host only)
/join_teamA - Join Team A
/join_teamB - Join Team B
/choose_cap - Choose team captains (Host)
/add_A @user - Add player to Team A
/add_B @user - Add player to Team B
/shift_Team - Shift player between teams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 EXTRA COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/user_info - Get your user information
/user_ranks - View player rankings
/member_lists - View group members list
/startgame - Start new game (Admin)
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

    # ================= USER INFO COMMAND =================
    @app.on_message(filters.command("user_info") & filters.group)
    async def user_info_cmd(client, message: Message):
        from pyrogram.enums import ParseMode
        
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
        
        if username:
            user_mention = f'<a href="tg://user?id={user_id}">@{username}</a>'
        else:
            user_mention = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        stats_text = f"""🏏 Stats Summary
👤 User: {user_mention}
🆔 User ID: {user_id}
─────⊱◈◈◈⊰─────
🏆 Highest Score: {highest_score} ({highest_score_balls} Balls)
📊 Runs: {total_runs} ({matches_played})
🎯 Wickets: {wickets}
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
            await message.reply(stats_text)

    # ================= USER RANKS COMMAND =================
    @app.on_message(filters.command("user_ranks") & filters.group)
    async def user_ranks_cmd(client, message: Message):
        from pyrogram.enums import ParseMode
        from database import get_or_create_user
        
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
        
        if username:
            clickable_name = f'<a href="tg://user?id={user_id}">@{username}</a>'
        else:
            clickable_name = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        stats_text = f"""🏏 Stats for {clickable_name}
📊 Runs: {total_runs} ({matches_played} matches)
🎯 Wickets: {wickets}
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
            text = "🎯 **Highest Wickets Leaderboard** 🎯\n\n"
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
        
        if username:
            clickable_name = f'<a href="tg://user?id={user_id}">@{username}</a>'
        else:
            clickable_name = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        stats_text = f"""🏏 Stats for {clickable_name}
📊 Runs: {total_runs} ({matches_played} matches)
🎯 Wickets: {wickets}
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
        players_count = len(game["players"])
        
        await message.reply(f"🎉 {user.first_name}, you've joined the solo game! (Player {players_count}) 👍")

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
            host_text += f"{i}. [{p['name']}](tg://user?id={p['id']})\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text)
        except:
            await client.send_message(chat_id, host_text)
        
        batter = game["current_batter"]
        bowler = game["current_bowler"]
        
        await client.send_message(chat_id, f"🎯 Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batter!")
        await client.send_message(chat_id, f"🎯 Hey [{bowler['name']}](tg://user?id={bowler['id']}), now you're bowling!")
        
        await asyncio.sleep(1)
        await send_bowling_video(client, chat_id, bowler)

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
            [InlineKeyboardButton("🎯 Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎯 Solo Play - 3 Ball", callback_data="ball_3")]
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
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        game["status"] = "waiting"
        game["players"] = []
        
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
            else:
                await client.send_message(chat_id, f"✅ Time's up! {players_count} players joined. Starting game...")
                await start_game_match(client, chat_id)

    # ================= TEAM MODE START =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        
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
            "winner": None
        }
        
        await callback.message.delete()
        
        await client.send_message(chat_id, f"👑 [{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏")
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
        if game and game.get("status") == "team_creation_a":
            game["status"] = "team_creation_b"
            team_a_count = len(game.get("team_a", []))
            await client.send_message(chat_id, f"⏰ Time's up for Team A! ({team_a_count} players joined)\n\n📣 Join Team B by sending /join_teamB\n⏰ You have 50 seconds for Team B")
            asyncio.create_task(team_b_timer(client, chat_id))

    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game.get("status") == "team_creation_b":
            game["status"] = "captain_selection"
            team_a_count = len(game.get("team_a", []))
            team_b_count = len(game.get("team_b", []))
            
            host = team_hosts.get(chat_id)
            if host:
                host_mention = f"[{host['name']}](tg://user?id={host['id']})"
            else:
                host_mention = "Game host"
            
            await client.send_message(
                chat_id,
                f"👋 Hey, {host_mention} now members are joined the teams! 🎉 Choose Team captains user /choose_cap 📝"
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
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A! (Total: {len(game['team_a'])} players)")

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
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B! (Total: {len(game['team_b'])} players)")

    @app.on_message(filters.command("add_A") & filters.group)
    async def add_to_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
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
        
        for p in game.get("team_a", []):
            if p["id"] == added_user.id:
                await message.reply(f"❌ Already in Team A!")
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
        await message.reply(f"added {added_user.first_name} to Team A! ({len(game['team_a'])} players)")

    @app.on_message(filters.command("add_B") & filters.group)
    async def add_to_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
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
        
        for p in game.get("team_b", []):
            if p["id"] == added_user.id:
                await message.reply(f"❌ Already in Team B!")
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
        await message.reply(f"added {added_user.first_name} to Team B! ({len(game['team_b'])} players)")

    # ================= START TOSS FUNCTION =================
    async def start_toss(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        cap_a_name = game['captain_a']['name']
        cap_b_name = game['captain_b']['name']
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 HEADS", callback_data="toss_heads")],
            [InlineKeyboardButton("🪙 TAILS", callback_data="toss_tails")]
        ])
        
        await client.send_message(
            chat_id,
            f"🎉 **Captains Selected!** 🎉\n\n"
            f"🏏 Team A Captain: {cap_a_name}\n"
            f"🏏 Team B Captain: {cap_b_name}\n\n"
            f"🪙 **TOSS TIME!** 🪙\n\n"
            f"{cap_a_name}, choose Heads or Tails:",
            reply_markup=keyboard
        )
        
        game["status"] = "toss"

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
        
        # Sirf 2 inline buttons
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

    # ================= CHOOSE CAPTAIN A CALLBACK =================
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
        
        # Check if user is in Team A
        user_name = None
        for player in game["team_a"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_a"] = player
                break
        
        if not user_name:
            await callback.answer("❌ You are not in Team A!", show_alert=True)
            return
        
        await callback.answer(f"✅ {user_name} is now Team A Captain!")
        
        # Check if both captains selected
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cap_cancel")]
            ])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"✅ Team A Captain: {user_name}\n"
                f"⚠️ Team B Captain: Not selected yet\n\n"
                f"Team B members click 'Team B Captain' button to become captain.",
                reply_markup=keyboard
            )

    # ================= CHOOSE CAPTAIN B CALLBACK =================
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
        
        # Check if user is in Team B
        user_name = None
        for player in game["team_b"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_b"] = player
                break
        
        if not user_name:
            await callback.answer("❌ You are not in Team B!", show_alert=True)
            return
        
        await callback.answer(f"✅ {user_name} is now Team B Captain!")
        
        # Check if both captains selected
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cap_cancel")]
            ])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"⚠️ Team A Captain: Not selected yet\n"
                f"✅ Team B Captain: {user_name}\n\n"
                f"Team A members click 'Team A Captain' button to become captain.",
                reply_markup=keyboard
            )

    @app.on_callback_query(filters.regex("^cap_cancel$"))
    async def cap_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Captain selection cancelled!")

    @app.on_callback_query(filters.regex("^noop$"))
    async def noop_callback(client, callback):
        await callback.answer()

    # ================= MEMBER LISTS COMMAND =================
    @app.on_message(filters.command("member_lists") & filters.group)
    async def member_lists_cmd(client, message: Message):
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
                        admins.append(f"@{m.user.username}" if m.user.username else m.user.first_name)
                    else:
                        members.append(f"@{m.user.username}" if m.user.username else m.user.first_name)
                
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
                
                await message.reply(text)
            except Exception as e:
                await message.reply(f"❌ Error: {e}")
            return
        
        # Team mode active
        if team_game:
            host_name = "Unknown"
            if host:
                host_name = f"[{host['name']}](tg://user?id={host['id']})"
            
            current_team = team_game.get("current_team", "None")
            batting_team = current_team if current_team != "None" else "None"
            
            if batting_team == "A":
                bowling_team = "B"
            elif batting_team == "B":
                bowling_team = "A"
            else:
                bowling_team = "None"
            
            innings_status = f"Innings {batting_team}" if batting_team != "None" else "Innings None"
            
            cap_a = team_game.get("captain_a")
            cap_b = team_game.get("captain_b")
            
            cap_a_name = f"[{cap_a['name']}](tg://user?id={cap_a['id']})" if cap_a else "Unknown"
            cap_b_name = f"[{cap_b['name']}](tg://user?id={cap_b['id']})" if cap_b else "Unknown"
            
            team_a_list = ""
            for i, p in enumerate(team_game.get("team_a", []), 1):
                player_name = f"[{p['name']}](tg://user?id={p['id']})"
                if cap_a and p["id"] == cap_a["id"]:
                    team_a_list += f"{i}. {player_name} [🧢] MEMBER OF TEAM A\n"
                else:
                    team_a_list += f"{i}. {player_name} MEMBER OF TEAM A\n"
            
            team_b_list = ""
            for i, p in enumerate(team_game.get("team_b", []), 1):
                player_name = f"[{p['name']}](tg://user?id={p['id']})"
                if cap_b and p["id"] == cap_b["id"]:
                    team_b_list += f"{i}. {player_name} [🧢] MEMBER OF TEAM B\n"
                else:
                    team_b_list += f"{i}. {player_name} MEMBER OF TEAM B\n"
            
            text = f"""👽 **Game Host:** {host_name}

🏏 **Batting:** Team {batting_team} ({innings_status})
🎯 **Bowling:** Team {bowling_team}

🎩 **Team A Captain:** {cap_a_name}
👒 **Team B Captain:** {cap_b_name}

🔵 **Team A**
{team_a_list if team_a_list else '   No players'}

🔴 **Team B**
{team_b_list if team_b_list else '   No players'}"""
            
            await message.reply(text)
        
        # Solo mode active
        elif solo_game:
            host_name = "Unknown"
            if solo_game.get("host_id"):
                host_name = f"[{solo_game['host_name']}](tg://user?id={solo_game['host_id']})"
            
            players = solo_game.get("players", [])
            current_batter = solo_game.get("current_batter")
            current_bowler = solo_game.get("current_bowler")
            
            batter_name = f"[{current_batter['name']}](tg://user?id={current_batter['id']})" if current_batter else "None"
            bowler_name = f"[{current_bowler['name']}](tg://user?id={current_bowler['id']})" if current_bowler else "None"
            
            players_list = ""
            for i, p in enumerate(players, 1):
                player_name = f"[{p['name']}](tg://user?id={p['id']})"
                status = "❌ OUT" if p.get("out", False) else "🏏 PLAYING"
                players_list += f"{i}. {player_name} - {status}\n"
            
            text = f"""👽 **Game Host:** {host_name}

🏏 **Solo Mode**

🎯 **Current Batter:** {batter_name}
⚾ **Current Bowler:** {bowler_name}

📊 **Players List:**
{players_list if players_list else '   No players'}"""
            
            await message.reply(text)

    # ================= TOSS CALLBACK =================
    @app.on_callback_query(filters.regex("^toss_"))
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
        
        cap_a_id = game['captain_a']['id']
        cap_a_name = game['captain_a']['name']
        cap_a_username = game['captain_a'].get('username')
        cap_a_display = f"@{cap_a_username}" if cap_a_username else cap_a_name
        
        cap_b_id = game['captain_b']['id']
        cap_b_name = game['captain_b']['name']
        cap_b_username = game['captain_b'].get('username')
        cap_b_display = f"@{cap_b_username}" if cap_b_username else cap_b_name
        
        toss_video_url = TOSS_VIDEO
        
        await callback.message.delete()
        
        cap_a_clickable = f"[{cap_a_display}](tg://user?id={cap_a_id})"
        cap_b_clickable = f"[{cap_b_display}](tg://user?id={cap_b_id})"
        
        if choice == toss_result:
            winner_clickable = cap_a_clickable
            winner_team = "A"
        else:
            winner_clickable = cap_b_clickable
            winner_team = "B"
        
        caption_text = f"🪙 The coin shows: {toss_result.upper()}!\n\n"
        caption_text += f"🅰️ - {cap_a_clickable} chose {choice.upper()}\n"
        caption_text += f"🅱️ {cap_b_clickable} got {toss_result.upper()}\n\n"
        caption_text += f"🏆 {winner_clickable} from Team {winner_team} won the toss!\n\n"
        caption_text += f"🏆 {winner_clickable}, please choose to Bat or Bowl:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 BAT FIRST", callback_data="toss_bat")],
            [InlineKeyboardButton("⚾ BOWL FIRST", callback_data="toss_bowl")]
        ])
        
        await client.send_video(
            chat_id,
            toss_video_url,
            caption=caption_text,
            reply_markup=keyboard
        )
        
        game["toss_winner"] = winner_team

    @app.on_callback_query(filters.regex("^toss_bat$|^toss_bowl$"))
    async def toss_decision_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        decision = callback.data.split("_")[1]
        toss_winner = game.get("toss_winner")
        
        if toss_winner == "A" and game["captain_a"]["id"] != user_id:
            await callback.answer("❌ Only Team A captain can decide!", show_alert=True)
            return
        elif toss_winner == "B" and game["captain_b"]["id"] != user_id:
            await callback.answer("❌ Only Team B captain can decide!", show_alert=True)
            return
        
        game["toss_decision"] = decision
        
        if decision == "bat":
            batting_team = toss_winner
        else:
            batting_team = "A" if toss_winner == "B" else "B"
        
        await callback.message.delete()
        
        team_name = "Team A" if batting_team == "A" else "Team B"
        await client.send_message(chat_id, f"✅ {'BAT FIRST' if decision == 'bat' else 'BOWL FIRST'} selected!\n\n🏏 {team_name} will bat first!\n\n📊 Now select number of overs:")
        
        await select_overs(client, chat_id, batting_team)

    async def select_overs(client, chat_id, batting_team):
        game = team_games.get(chat_id)
        if not game:
            return
        
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
        
        await client.send_message(chat_id, f"📊 **Select number of overs:**\n\nChoose overs (1 to 20 overs per side):", reply_markup=keyboard)
        
        game["status"] = "over_selection"
        game["batting_first"] = batting_team

    @app.on_callback_query(filters.regex("^over_"))
    async def over_selection_callback(client, callback):
        chat_id = callback.message.chat.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "over_selection":
            await callback.answer("❌ No over selection in progress!", show_alert=True)
            return
        
        overs = int(callback.data.split("_")[1])
        game["overs"] = overs
        game["total_balls_limit"] = overs * 6
        
        await callback.message.delete()
        
        batting_team = game["batting_first"]
        team_name = "Team A" if batting_team == "A" else "Team B"
        
        await client.send_message(chat_id, f"✅ Match set! {overs} overs per side.\n\n🚀 Match is starting...\n🏏 {team_name} will bat first!\n\nLet the game begin! 🎉")
        
        game["match_start_time"] = datetime.now()
        game["status"] = "playing"
        
        await start_team_batting(client, chat_id, batting_team)

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
            game["current_bowler"] = players[game["current_bowler_index"]].copy()
        
        game["current_bowler_balls"] = 0
        game["bowling_number"] = None
        game["team_total"] = 0
        game["team_wickets"] = 0
        game["total_balls_in_inning"] = 0
        
        batter_clickable = f"[{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})"
        bowler_clickable = f"[{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})"
        
        await client.send_message(chat_id, f"🏏 **Team {team} Batting**\n\nBatter: {batter_clickable}\nBowler: {bowler_clickable}")
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message: Message):
        text = message.text.strip()
        
        if text.startswith('/'):
            return
        
        chat_id = message.chat.id
        print(f"🔴 BATTING MSG - Chat: {chat_id}, Text: {text}")
        
        # Solo mode
        game = games.get(chat_id)
        if game:
            if game.get("status") != "playing" or game.get("game_over") or game.get("bowling_number") is None:
                return
            
            batter = game.get("current_batter")
            if not batter or message.from_user.id != batter.get("id"):
                return
            
            if not text.isdigit() or int(text) not in range(1, 7):
                return await message.reply(INVALID_NUMBER)
            
            try:
                await message.reply("👍")
            except:
                pass
            
            bat = int(text)
            result = play_ball(chat_id, bat)
            bow = game.get("bowling_number", "?")
            game["bowling_number"] = None
            bowler = game["current_bowler"]
            
            if result["type"] == "out":
                try:
                    await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
                except:
                    await message.reply(OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
                
                if game.get("game_over"):
                    await message.reply(build_scoreboard(game["players"], is_final=True))
                    if chat_id in games:
                        del games[chat_id]
                    return
                
                await message.reply(build_scoreboard(game["players"], is_final=False))
                
                new_batter = game["current_batter"]
                new_bowler = game["current_bowler"]
                await client.send_message(chat_id, f"🎯 New batter: [{new_batter['name']}](tg://user?id={new_batter['id']})\n🎯 New bowler: [{new_bowler['name']}](tg://user?id={new_bowler['id']})")
                await send_bowling_video(client, chat_id, game["current_bowler"])
            else:
                try:
                    await message.reply_video(get_run_video(result["runs"]))
                except:
                    await message.reply_video(get_run_video(result["runs"]))
                
                if not game.get("game_over"):
                    await send_bowling_video(client, chat_id, bowler)
            return
        
        # Team mode
        team_game = team_games.get(chat_id)
        if not team_game:
            return
        
        if team_game.get("status") != "playing" or team_game.get("game_over") or team_game.get("bowling_number") is None:
            return
        
        batter = team_game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        try:
            await message.reply("👍")
        except:
            pass
        
        bat = int(text)
        bow = team_game.get("bowling_number", "?")
        team_game["bowling_number"] = None
        bowler = team_game["current_bowler"]
        team_key = f"team_{team_game['current_team'].lower()}"
        
        if bat == bow:
            batter["out"] = True
            team_game["team_wickets"] += 1
            
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            
            active_batters = [p for p in team_game[team_key] if not p.get("out", False)]
            
            if not active_batters or team_game["team_wickets"] >= len(team_game[team_key]):
                # Innings over logic...
                if team_game["current_team"] == "A":
                    team_game["team_a_score"] = team_game["team_total"]
                    team_game["team_a_wickets"] = team_game["team_wickets"]
                    await client.send_message(chat_id, f"🏏 **Team A Innings Complete!**\n\nTotal: {team_game['team_a_score']}/{team_game['team_a_wickets']}\n\nTeam B needs {team_game['team_a_score'] + 1} runs to win!\n\nStarting Team B innings...")
                    await start_team_batting(client, chat_id, "B")
                else:
                    team_game["team_b_score"] = team_game["team_total"]
                    team_game["team_b_wickets"] = team_game["team_wickets"]
                    
                    if team_game["team_b_score"] > team_game["team_a_score"]:
                        winner = "Team B"
                    elif team_game["team_b_score"] < team_game["team_a_score"]:
                        winner = "Team A"
                    else:
                        winner = "Match Tied"
                    
                    team_game["game_over"] = True
                    team_game["winner"] = winner
                    await client.send_message(chat_id, build_team_scoreboard(team_game))
                    await client.send_message(chat_id, f"🏆 **Match Over!**\n\nWinner: {winner}\n\nTeam A: {team_game['team_a_score']}/{team_game['team_a_wickets']}\nTeam B: {team_game['team_b_score']}/{team_game['team_b_wickets']}")
                    
                    if chat_id in team_games:
                        del team_games[chat_id]
                    if chat_id in team_hosts:
                        del team_hosts[chat_id]
                return
            
            # Find next batter...
            next_batter_index = team_game["current_batter_index"] + 1
            for i in range(next_batter_index, len(team_game[team_key])):
                if not team_game[team_key][i].get("out", False):
                    team_game["current_batter_index"] = i
                    team_game["current_batter"] = team_game[team_key][i].copy()
                    await client.send_message(chat_id, f"🎯 New batter: [{team_game['current_batter']['name']}](tg://user?id={team_game['current_batter']['id']})")
                    break
            
            await client.send_message(chat_id, build_team_scoreboard(team_game))
            team_game["current_bowler_balls"] += 1
            team_game["total_balls_in_inning"] += 1
            
            if team_game["current_bowler_balls"] >= 6:
                players = team_game[team_key]
                new_bowler_index = (team_game["current_bowler_index"] + 1) % len(players)
                team_game["current_bowler_index"] = new_bowler_index
                team_game["current_bowler"] = players[new_bowler_index].copy()
                team_game["current_bowler_balls"] = 0
                await client.send_message(chat_id, f"🔄 New bowler: [{team_game['current_bowler']['name']}](tg://user?id={team_game['current_bowler']['id']})")
            
            await send_bowling_video_team(client, chat_id, team_game["current_bowler"])
        else:
            runs = bat
            batter["score"] += runs
            batter["balls"] += 1
            if runs == 4:
                batter["fours"] += 1
            elif runs == 6:
                batter["sixes"] += 1
            batter["history"].append(f"{runs}")
            team_game["team_total"] += runs
            team_game["total_balls_in_inning"] += 1
            
            try:
                await message.reply_video(get_run_video(runs))
            except:
                await message.reply_video(get_run_video(runs))
            
            if team_game["current_team"] == "B" and team_game["team_total"] > team_game["team_a_score"]:
                team_game["team_b_score"] = team_game["team_total"]
                team_game["game_over"] = True
                team_game["winner"] = "Team B"
                await client.send_message(chat_id, build_team_scoreboard(team_game))
                await client.send_message(chat_id, f"🏆 **Team B Wins!**\n\nTarget: {team_game['team_a_score'] + 1}\nTeam B: {team_game['team_b_score']}\n\nTeam B wins!")
                
                if chat_id in team_games:
                    del team_games[chat_id]
                if chat_id in team_hosts:
                    del team_hosts[chat_id]
                return
            
            await client.send_message(chat_id, build_team_scoreboard(team_game))
            team_game["current_bowler_balls"] += 1
            
            if team_game["current_bowler_balls"] >= 6:
                players = team_game[team_key]
                new_bowler_index = (team_game["current_bowler_index"] + 1) % len(players)
                team_game["current_bowler_index"] = new_bowler_index
                team_game["current_bowler"] = players[new_bowler_index].copy()
                team_game["current_bowler_balls"] = 0
                await client.send_message(chat_id, f"🔄 New bowler: [{team_game['current_bowler']['name']}](tg://user?id={team_game['current_bowler']['id']})")
            
            await send_bowling_video_team(client, chat_id, team_game["current_bowler"])

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        print(f"🔴 BOWLING DM - User: {user_id}, Text: {text}")
        
        if text.startswith("/start"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        num = int(text)
        
        for chat_id, game in games.items():
            if game.get("status") != "playing" or game.get("game_over"):
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            if game.get("bowling_number") is not None:
                await message.reply("❌ You already bowled! Wait for your next turn.")
                return
            
            if chat_id in bowling_tasks:
                bowling_tasks[chat_id].cancel()
                del bowling_tasks[chat_id]
            
            set_bowling(chat_id, num)
            await message.reply(f"✅ Bowling number {num} sent to game!")
            
            batter = game["current_batter"]
            batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
            await client.send_video(chat_id, BATTING_VIDEO, caption=f"Hey {batter_clickable}, now you're batting! Send number (1-6) in GROUP")
            return
        
        for chat_id, game in team_games.items():
            if game.get("status") != "playing" or game.get("game_over"):
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            if game.get("bowling_number") is not None:
                await message.reply("❌ You already bowled! Wait for your next turn.")
                return
            
            if chat_id in bowling_tasks:
                bowling_tasks[chat_id].cancel()
                del bowling_tasks[chat_id]
            
            game["bowling_number"] = num
            await message.reply(f"✅ Bowling number {num} sent to game!")
            
            batter = game["current_batter"]
            batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
            await client.send_message(chat_id, f"🎯 Bowler bowled {num}! Now {batter_clickable}, send your batting number (1-6) in GROUP")
            return
        
        await message.reply("❌ No active game found where you are the bowler!")

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
