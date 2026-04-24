from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
from solo.score import get_live_score, set_team_games_ref
import asyncio
from datetime import datetime
import io
import random

print("🔴 LOADING HANDLERS.PY")

active_votes = {}
bowling_tasks = {}

# ================= TEAM MODE VARIABLES =================
team_games = {}
team_hosts = {}
user_reports = {}

# Set team_games reference in score.py
set_team_games_ref(team_games)
print("🔴 Team games reference set in score.py")

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
    print(f"🔴 send_bowling_video called - chat: {chat_id}, bowler: {bowler.get('name')}")
    
    game = games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        print(f"🔴 Cannot send bowling video - game not in playing state")
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
        print(f"🔴 Bowling message sent to user {bowler['id']}")
    except Exception as e:
        print(f"🔴 Failed to send message to bowler: {e}")
    
    if chat_id in bowling_tasks:
        try:
            bowling_tasks[chat_id].cancel()
        except:
            pass
    
    task = asyncio.create_task(bowling_timeout_with_warnings(client, chat_id, bowler["id"], bowler["name"], None))
    bowling_tasks[chat_id] = task
    print(f"🔴 Bowling task created for chat {chat_id}")

# ================= SOLO MODE TIMEOUT =================
async def bowling_timeout_with_warnings(client, chat_id, user_id, bowler_name, message_id):
    print(f"🔴 bowling_timeout_with_warnings started for chat {chat_id}, user {user_id}")
    
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
                print(f"🔴 30s warning sent to {bowler_name}")
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
                print(f"🔴 10s warning sent to {bowler_name}")
            except:
                pass
    
    await asyncio.sleep(10)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            print(f"🔴 No response from bowler {bowler_name}, applying penalty")
            
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
            except Exception as e:
                print(f"Error sending 6 run video: {e}")
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
    print(f"🔴 bowling_timeout_with_warnings ended for chat {chat_id}")

# ================= TEAM MODE SEND BOWLING VIDEO =================
async def send_bowling_video_team(client, chat_id, bowler):
    print(f"🔴 send_bowling_video_team called - chat: {chat_id}")
    
    game = team_games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        print(f"🔴 Cannot send team bowling video - game not in playing state")
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
    print(f"🔴 Team bowling task created for chat {chat_id}")

# ================= TEAM MODE TIMEOUT =================
async def bowling_timeout_with_warnings_team(client, chat_id, user_id, bowler_name, message_id):
    print(f"🔴 bowling_timeout_with_warnings_team started for chat {chat_id}")
    
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
            print(f"🔴 No response from team bowler {bowler_name}, applying penalty")
            
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
            except Exception as e:
                print(f"Error sending 6 run video: {e}")
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs from {game['current_team']} team."
                )
            
            await client.send_message(chat_id, build_team_scoreboard_text(game))
            
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
    print(f"🔴 bowling_timeout_with_warnings_team ended for chat {chat_id}")

def build_team_scoreboard_text(game):
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
    print("🔴 REGISTERING HANDLERS IN register_handlers()")

    # ================= START COMMAND =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        print(f"🔴 START COMMAND - Chat: {chat_id}, User: {user_id}")
        
        if await is_admin(client, chat_id, user_id):
            await select_game_menu(client, message)
        else:
            await vote_system(client, message)

    @app.on_message(filters.command("start") & filters.private)
    async def start_dm(client, message: Message):
        user_id = message.from_user.id
        print(f"🔴 START DM - User: {user_id}")
        
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
        print(f"🔴 SCORE COMMAND - Chat: {message.chat.id}")
        await get_live_score(client, message)

    @app.on_message(filters.command("help") & filters.group)
    async def help_cmd(client, message: Message):
        print(f"🔴 HELP COMMAND - Chat: {message.chat.id}")
        help_text = """🏏 **Cricket Game Bot Commands** 🏏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎮 GAME MODES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**SOLO MODE:**
/start - Start game (Admin) or Vote (Member)
/joingame - Join solo game (min 4 players)
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
/batting <pos> - Change batting order (Captain)
/bowling <pos> - Change bowling order (Captain)
/cap_change @user - Change team captain (Host)
/add_cap @user - Add a captain (Host)
/rm_cap @user - Remove a captain (Host)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ℹ️ INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Solo mode requires minimum 4 players
• 3 balls per bowler in solo mode
• 6 balls per over in team mode
• Bot must be admin in group

🏏 **Enjoy the game!** 🏏"""
        
        await message.reply(help_text)
        
    # ================= USER INFO COMMAND =================
    @app.on_message(filters.command("user_info") & filters.group)
    async def user_info_cmd(client, message: Message):
        from pyrogram.enums import ParseMode
        print(f"🔴 USER_INFO COMMAND - Chat: {message.chat.id}")
        
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
        except Exception as e:
            print(f"Error sending image: {e}")
            await message.reply(stats_text.replace(user_mention, f"@{username}" if username else name))

    # ================= JOIN GAME COMMAND (WORKING WITH DEBUG) =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        print(f"🔴 JOIN GAME COMMAND - Chat ID: {chat_id}")
        
        game = games.get(chat_id)
        print(f"🔴 Game exists: {game is not None}")
        
        if not game:
            print(f"🔴 No game found for chat {chat_id}")
            return await message.reply("❌ No active solo game! Use /start and select Solo mode first.")
        
        print(f"🔴 Game status: {game.get('status')}")
        print(f"🔴 Current players: {len(game.get('players', []))}")
        
        if game.get("status") != "waiting":
            print(f"🔴 Game already started, status: {game.get('status')}")
            return await message.reply("❌ Game already started! Cannot join now.")
        
        user = message.from_user
        print(f"🔴 User: {user.first_name} (ID: {user.id})")
        
        # Check if already joined
        for p in game.get("players", []):
            if p["id"] == user.id:
                print(f"🔴 User already joined")
                return await message.reply("❌ You already joined this game!")
        
        # Add player directly
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
        print(f"🔴 Player added! Total players: {players_count}")
        
        await message.reply(f"🎉 {user.first_name}, you've joined the solo game! (Player {players_count}) 👍")
        
        # Auto start when 4 players join
        if players_count >= 4:
            print(f"🔴 Auto-starting game with {players_count} players")
            await client.send_message(chat_id, f"✅ {players_count} players joined! Starting game in 3 seconds...")
            await asyncio.sleep(3)
            await start_game_match(client, chat_id)

    async def start_game_match(client, chat_id):
        print(f"🔴 START_GAME_MATCH called for chat: {chat_id}")
        
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            print(f"🔴 Cannot start - Game status: {game.get('status') if game else 'No game'}")
            return
        
        players_count = len(game["players"])
        print(f"🔴 Players count: {players_count}")
        
        if players_count < 4:
            print(f"🔴 Not enough players: {players_count}/4")
            await client.send_message(chat_id, f"❌ Minimum 4 players required to start the game! 👥\n\nCurrent players: {players_count}/4\n⚠️ Game cancelled!")
            if chat_id in games:
                del games[chat_id]
            return
        
        print(f"🔴 Starting match...")
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
        print(f"🔴 SELECT_GAME_MENU called")
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
        print(f"🔴 MODE HANDLER - Action: {action}")
        
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
        print(f"🔴 BALL_SELECTION_MENU called")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎯 Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = "🏏 **Choose Bowling Mode** 🏏\n\n• Solo Play - 1 Ball (Single ball per bowler)\n• Solo Play - 3 Ball (Three balls per bowler)"
        
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
        print(f"🔴 BALL HANDLER - Ball mode: {ball_mode}, Chat: {chat_id}")
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        
        await callback.message.delete()
        await client.send_message(chat_id, "🎉 Solo game created! Join the game using /joingame (2 minutes to join)\n⏰")
        asyncio.create_task(start_join_timer(client, chat_id))

    async def start_join_timer(client, chat_id):
        print(f"🔴 START_JOIN_TIMER started for chat: {chat_id}")
        
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
            print(f"🔴 Timer ended - Players: {players_count}")
            
            if players_count < 4:
                await client.send_message(chat_id, f"❌ Minimum 4 players required to start the game! 👥\n\nCurrent players: {players_count}/4\n⚠️ Game cancelled due to insufficient players.")
                if chat_id in games:
                    del games[chat_id]
            else:
                await client.send_message(chat_id, f"✅ Time's up! {players_count} players joined. Starting game...")
                await start_game_match(client, chat_id)
        
        print(f"🔴 START_JOIN_TIMER ended for chat: {chat_id}")

    # ================= TEAM MODE FUNCTIONS =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        print(f"🔴 TEAM_MODE_START called for chat: {chat_id}")
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]])
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
        print(f"🔴 TEAM_BECOME_HOST - Chat: {chat_id}, User: {user.id}")
        
        existing_game = team_games.get(chat_id)
        if existing_game and existing_game.get("status") == "playing":
            await callback.answer("❌ A match is currently in progress! Cannot change host.", show_alert=True)
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
            "toss_winner": None,
            "toss_decision": None,
            "overs": 0,
            "team_a_score": 0,
            "team_b_score": 0,
            "team_a_wickets": 0,
            "team_b_wickets": 0,
            "current_team": None,
            "target": None,
            "game_over": False,
            "winner": None,
            "match_start_time": None,
            "match_end_time": None,
            "total_balls": 0,
            "team_a_name": "Team A",
            "team_b_name": "Team B"
        }
        
        await callback.message.delete()
        
        try:
            await client.send_photo(chat_id, TEAM_CHAPU_IMG, caption=f"[{user.first_name}](tg://user?id={user.id}) is now the game host!\n\nUse /create_team to start team creation.\n\n🏏 Let's get the match started!")
        except:
            await client.send_message(chat_id, f"[{user.first_name}](tg://user?id={user.id}) is now the game host!\n\nUse /create_team to start team creation.\n\n🏏 Let's get the match started!")
        
        await callback.answer()

    # ================= CREATE TEAM COMMAND =================
    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        print(f"🔴 CREATE_TEAM - Chat: {chat_id}, User: {user_id}")
        
        host = team_hosts.get(chat_id)
        if not host:
            await message.reply("❌ No game host found! First use /start and select Team mode, then click 'I'm the Host' button.")
            return
        
        if host.get("id") != user_id:
            await message.reply("❌ Only the game host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active team game found! Please start team mode again.")
            return
        
        if game.get("status") != "waiting_host":
            await message.reply("❌ Teams already created or game already started!")
            return
        
        # Initialize teams
        game["team_a"] = []
        game["team_b"] = []
        game["status"] = "team_creation_a"
        game["host_id"] = user_id
        
        await message.reply("🎉 Team creation is underway!\n\n📣 Join Team A by sending /join_teamA\n⏰ You have 50 seconds for Team A\n\n🏏 Let's get started!")
        
        asyncio.create_task(team_a_timer(client, chat_id))

    async def team_a_timer(client, chat_id):
        print(f"🔴 TEAM_A_TIMER started for chat: {chat_id}")
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game.get("status") == "team_creation_a":
            game["status"] = "team_creation_b"
            team_a_count = len(game.get("team_a", []))
            await client.send_message(
                chat_id, 
                f"⏰ Time's up for Team A! ({team_a_count} players joined)\n\n📣 Join Team B by sending /join_teamB\n⏰ You have 50 seconds for Team B"
            )
            asyncio.create_task(team_b_timer(client, chat_id))
        print(f"🔴 TEAM_A_TIMER ended for chat: {chat_id}")

    async def team_b_timer(client, chat_id):
        print(f"🔴 TEAM_B_TIMER started for chat: {chat_id}")
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game.get("status") == "team_creation_b":
            game["status"] = "captain_selection"
            team_a_count = len(game.get("team_a", []))
            team_b_count = len(game.get("team_b", []))
            await client.send_message(
                chat_id, 
                f"⏰ Time's up for Team B! ({team_b_count} players joined)\n\n👥 Final Teams:\n🏏 Team A: {team_a_count} players\n🏏 Team B: {team_b_count} players\n\n🎯 Now choose team captains using /choose_cap"
            )
        print(f"🔴 TEAM_B_TIMER ended for chat: {chat_id}")

    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        print(f"🔴 JOIN_TEAM_A - Chat: {chat_id}, User: {user.id}")
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active team game found!")
            return
        
        if game.get("status") != "team_creation_a":
            await message.reply("❌ Team A registration is closed! Only Team B is open now.")
            return
        
        host = team_hosts.get(chat_id)
        if host and host.get("id") == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        for p in game.get("team_a", []):
            if p["id"] == user.id:
                await message.reply("❌ You already joined Team A!")
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
        
        if "team_a" not in game:
            game["team_a"] = []
        
        game["team_a"].append(player_data)
        current_count = len(game["team_a"])
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A! (Total: {current_count} players)")

    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        print(f"🔴 JOIN_TEAM_B - Chat: {chat_id}, User: {user.id}")
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active team game found!")
            return
        
        if game.get("status") != "team_creation_b":
            await message.reply("❌ Team B is not open for joining yet! Wait for Team A to complete.")
            return
        
        host = team_hosts.get(chat_id)
        if host and host.get("id") == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        for p in game.get("team_a", []):
            if p["id"] == user.id:
                await message.reply("❌ You already joined Team A! Cannot join Team B.")
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
        current_count = len(game["team_b"])
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B! (Total: {current_count} players)")

    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        print(f"🔴 CHOOSE_CAP - Chat: {chat_id}, User: {user_id}")
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can start captain selection!")
            return
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "captain_selection":
            await message.reply("❌ Captain selection not available now! Make sure teams are created.")
            return
        
        if game.get("captain_a") and game.get("captain_b"):
            await message.reply("❌ Captains already selected!")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏆 Choose Team A Captain", callback_data="choose_cap_a")],
            [InlineKeyboardButton("🏆 Choose Team B Captain", callback_data="choose_cap_b")]
        ])
        
        await message.reply("**🏏 Select Captains**\n\nClick below to choose captains for each team:", reply_markup=keyboard)

    @app.on_callback_query(filters.regex("^choose_cap_a$"))
    async def choose_cap_a_callback(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        print(f"🔴 CHOOSE_CAP_A - Chat: {chat_id}, User: {user_id}")
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_a"):
            await callback.answer("❌ Team A captain already selected!", show_alert=True)
            return
        
        for player in game.get("team_a", []):
            if player["id"] == user_id:
                game["captain_a"] = player.copy()
                await callback.answer(f"✅ You are now Team A Captain!")
                
                if game.get("captain_a") and game.get("captain_b"):
                    await callback.message.delete()
                    await start_toss(client, chat_id)
                else:
                    await callback.message.edit_text(
                        f"🏏 **Captain Selection**\n\n✅ Team A Captain: {game['captain_a']['name']}\n⚠️ Team B Captain: Not selected yet\n\nTeam B members click below to become captain:",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 Choose Team B Captain", callback_data="choose_cap_b")]])
                    )
                return
        
        await callback.answer("❌ You are not in Team A! Only Team A members can be captain.", show_alert=True)

    @app.on_callback_query(filters.regex("^choose_cap_b$"))
    async def choose_cap_b_callback(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        print(f"🔴 CHOOSE_CAP_B - Chat: {chat_id}, User: {user_id}")
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_b"):
            await callback.answer("❌ Team B captain already selected!", show_alert=True)
            return
        
        for player in game.get("team_b", []):
            if player["id"] == user_id:
                game["captain_b"] = player.copy()
                await callback.answer(f"✅ You are now Team B Captain!")
                
                if game.get("captain_a") and game.get("captain_b"):
                    await callback.message.delete()
                    await start_toss(client, chat_id)
                else:
                    await callback.message.edit_text(
                        f"🏏 **Captain Selection**\n\n⚠️ Team A Captain: Not selected yet\n✅ Team B Captain: {game['captain_b']['name']}\n\nTeam A members click below to become captain:",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 Choose Team A Captain", callback_data="choose_cap_a")]])
                    )
                return
        
        await callback.answer("❌ You are not in Team B! Only Team B members can be captain.", show_alert=True)

    async def start_toss(client, chat_id):
        print(f"🔴 START_TOSS called for chat: {chat_id}")
        
        game = team_games.get(chat_id)
        if not game:
            return
        
        game["status"] = "toss"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 HEADS", callback_data="toss_heads")],
            [InlineKeyboardButton("🪙 TAILS", callback_data="toss_tails")]
        ])
        
        cap_a_name = game['captain_a']['name']
        cap_b_name = game['captain_b']['name']
        
        await client.send_message(
            chat_id, 
            f"🏏 **TOSS TIME** 🏏\n\nTeam A Captain: {cap_a_name}\nTeam B Captain: {cap_b_name}\n\n{cap_a_name}, choose Heads or Tails:",
            reply_markup=keyboard
        )

    # Continue with toss callbacks and other handlers...
    # (Add remaining toss handlers, batting, bowling, end_match, vote system, etc.)

    # ================= VOTE SYSTEM =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        print(f"🔴 VOTE_SYSTEM called for chat: {chat_id}")
        
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
        print(f"🔴 VOTE_HANDLER - Chat: {chat_id}, User: {user.id}")
        
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

    print("🔴 ALL HANDLERS REGISTERED SUCCESSFULLY!")
