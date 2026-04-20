# solo/handlers.py - Final Complete Working Version

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
from solo.score import get_live_score
import asyncio
from datetime import datetime
import io

active_votes = {}
bowling_tasks = {}

# ================= TEAM MODE VARIABLES =================
team_games = {}
team_hosts = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def bowling_timeout_with_warnings(client, chat_id, user_id, bowler_name, message_id):
    """Send warnings and penalty if bowler doesn't respond"""
    
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
                    player["history"].append("PENALTY(-6)")
                    break
            
            try:
                await client.send_video(
                    chat_id,
                    get_run_video(6),
                    caption=f"No message received from bowler, deducting 6 runs of bowler."
                )
            except Exception as e:
                print(f"Error sending 6 run video: {e}")
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs of bowler."
                )
            
            await client.send_message(chat_id, build_scoreboard(game["players"], is_final=False))
            
            game["bowling_number"] = None
            game["current_bowler_balls"] += 1
            game["total_balls_in_match"] += 1
            
            ball_mode = game.get("ball_mode", 3)
            if game["current_bowler_balls"] >= ball_mode:
                new_bowler_index = (game["current_bowler_index"] + 1) % len(game["players"])
                game["current_bowler_index"] = new_bowler_index
                game["current_bowler"] = game["players"][new_bowler_index].copy()
                game["current_bowler_balls"] = 0
            
            await send_bowling_video(client, chat_id, game["current_bowler"])
    
    if chat_id in bowling_tasks:
        del bowling_tasks[chat_id]

def register_handlers(app):

    # ================= START GROUP =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if await is_admin(client, chat_id, user_id):
            await select_game_menu(client, message)
        else:
            await vote_system(client, message)

    # ================= SCORE COMMAND =================
    @app.on_message(filters.command("score") & filters.group)
    async def score_cmd(client, message: Message):
        await get_live_score(client, message)

    # ================= START DM =================
    @app.on_message(filters.command("start") & filters.private)
    async def start_dm(client, message: Message):
        user_id = message.from_user.id
        
        for chat_id, game in games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply(
                        "🎯 **Send bowling number (1-6)**\n\n"
                        "Example: `4`\n\n"
                        "⏰ You have 60 seconds!"
                    )
                    return
        
        await message.reply(
            "🏏 **Welcome to Cricket Game Bot!**\n\n"
            "Use me in a group to play cricket games.\n"
            "Add me to a group and use /start there!\n\n"
            "**Commands:**\n"
            "/start - Start game (Admin) or Vote (Member)\n"
            "/joingame - Join an existing game\n"
            "/score - Check live score"
        )

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤Solo", callback_data="mode_solo"), InlineKeyboardButton("👥Team", callback_data="mode_team")],
            [InlineKeyboardButton("⭐️Start Auction", callback_data="mode_auction"), InlineKeyboardButton("🏆Tournament Mode", callback_data="mode_tournament")],
            [InlineKeyboardButton("Cancel", callback_data="mode_cancel")]
        ])
        
        caption = """Select game mode:"""
        
        try:
            await message.reply_photo(SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except:
            await message.reply(caption, reply_markup=keyboard)

    # ================= MODE HANDLER =================
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
        
        if action in ["auction", "tournament"]:
            await callback.answer(f"{action} mode coming soon!", show_alert=True)
            return
        
        if action == "solo":
            await ball_selection_menu(client, callback)

    # ================= TEAM MODE START =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
        ])
        
        caption = """🎉 New Game Alert! 🎉 

Who will be the game host for this match? 🤔"""
        
        try:
            await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
        except:
            await client.send_message(chat_id, caption, reply_markup=keyboard)
        await callback.answer()

    # ================= BECOME HOST =================
    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        # Check if there's an existing game that is still playing
        existing_game = team_games.get(chat_id)
        if existing_game and existing_game.get("status") == "playing":
            await callback.answer("❌ A match is currently in progress! Cannot change host.", show_alert=True)
            return
        
        # Clear any existing data
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        team_hosts[chat_id] = {
            "id": user.id,
            "name": user.first_name,
            "username": user.username
        }
        
        team_games[chat_id] = {
            "host_id": user.id,
            "host_name": user.first_name,
            "status": "waiting_host",
            "team_a": [],
            "team_b": [],
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
        await client.send_message(
            chat_id,
            f"👑 [{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏"
        )
        await callback.answer()

    # ================= CREATE TEAM COMMAND =================
    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        print(f"🔴 CREATE TEAM - Chat: {chat_id}, User: {user_id}")
        
        host = team_hosts.get(chat_id)
        if not host:
            await message.reply("❌ No game host found! Start team mode first.")
            return
        
        if host["id"] != user_id:
            await message.reply("❌ Only the game host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "waiting_host":
            await message.reply("❌ Teams already created!")
            return
        
        game["status"] = "team_creation_a"
        
        await message.reply(
            f"🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n"
        )
        
        asyncio.create_task(team_a_timer(client, chat_id))

    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game or game["status"] != "team_creation_a":
            await message.reply("❌ Team A is not open for joining!")
            return
        
        if host and host["id"] == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        if user.id in [p["id"] for p in game["team_a"]]:
            await message.reply("❌ You already joined Team A!")
            return
        
        if user.id in [p["id"] for p in game["team_b"]]:
            await message.reply("❌ You already joined Team B!")
            return
        
        game["team_a"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A!")

    # ================= TEAM A TIMER =================
    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, f"⏰ Time's up for Team A! ({len(game['team_a'])} players joined)\n\n🎉 Join Team B by sending /join_teamB 📣")

    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game or game["status"] != "team_creation_b":
            await message.reply("❌ Team B is not open for joining!")
            return
        
        if host and host["id"] == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        if user.id in [p["id"] for p in game["team_b"]]:
            await message.reply("❌ You already joined Team B!")
            return
        
        if user.id in [p["id"] for p in game["team_a"]]:
            await message.reply("❌ You already joined Team A!")
            return
        
        game["team_b"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B!")

    # ================= TEAM B TIMER =================
    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            game["status"] = "ready"
            await client.send_message(
                chat_id,
                f"✅ Teams are complete!\n\n"
                f"🏏 Team A: {len(game['team_a'])} players\n"
                f"🏏 Team B: {len(game['team_b'])} players\n\n"
                f"🎯 Type /start_match to begin the match!"
            )

    # ================= ADD TO TEAM A (HOST ONLY) =================
    @app.on_message(filters.command("add_A") & filters.group)
    async def add_to_team_a_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team A!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_a", "team_creation_b", "ready"]:
            await message.reply("❌ Cannot add players now!")
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
        
        if added_user.id in [p["id"] for p in game["team_a"]]:
            await message.reply(f"❌ {added_user.first_name} already in Team A!")
            return
        
        if added_user.id in [p["id"] for p in game["team_b"]]:
            await message.reply(f"❌ {added_user.first_name} already in Team B!")
            return
        
        game["team_a"].append({
            "id": added_user.id, "name": added_user.first_name, "username": added_user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current = len(game["team_a"])
        username_display = f"@{added_user.username}" if added_user.username else added_user.first_name
        await message.reply(f"added {username_display} to Team A! ({current} players)")

    # ================= ADD TO TEAM B (HOST ONLY) =================
    @app.on_message(filters.command("add_B") & filters.group)
    async def add_to_team_b_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team B!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_b", "ready"]:
            await message.reply("❌ Cannot add players to Team B now!")
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
        
        if added_user.id in [p["id"] for p in game["team_b"]]:
            await message.reply(f"❌ {added_user.first_name} already in Team B!")
            return
        
        if added_user.id in [p["id"] for p in game["team_a"]]:
            await message.reply(f"❌ {added_user.first_name} already in Team A!")
            return
        
        game["team_b"].append({
            "id": added_user.id, "name": added_user.first_name, "username": added_user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current = len(game["team_b"])
        username_display = f"@{added_user.username}" if added_user.username else added_user.first_name
        await message.reply(f"added {username_display} to Team B! ({current} players)")

    # ================= SHIFT TEAM (HOST ONLY) =================
    @app.on_message(filters.command("shift_Team") & filters.group)
    async def shift_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can shift players between teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_a", "team_creation_b", "ready"]:
            await message.reply("❌ Cannot shift players now!")
            return
        
        if not message.reply_to_message:
            await message.reply("❌ Please reply to a user's message to shift them!")
            return
        
        user_to_shift = message.reply_to_message.from_user
        username_display = f"@{user_to_shift.username}" if user_to_shift.username else user_to_shift.first_name
        
        in_team_a = False
        for p in game["team_a"]:
            if p["id"] == user_to_shift.id:
                in_team_a = True
                break
        
        if not in_team_a:
            in_team_b = False
            for p in game["team_b"]:
                if p["id"] == user_to_shift.id:
                    in_team_b = True
                    break
            if not in_team_b:
                await message.reply(f"❌ {username_display} is not in any team!")
                return
            current_team = "B"
            target_team = "A"
        else:
            current_team = "A"
            target_team = "B"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"Confirm shift to Team {target_team}", callback_data=f"shift_confirm_{user_to_shift.id}_{current_team}_{target_team}"),
                InlineKeyboardButton("Cancel", callback_data="shift_cancel")
            ]
        ])
        
        await message.reply(
            f"🔄 {username_display} is currently in Team {current_team}.\n"
            f"Do you want to shift them to Team {target_team}?",
            reply_markup=keyboard
        )

    # ================= SHIFT CONFIRM CALLBACK =================
    @app.on_callback_query(filters.regex("^shift_confirm_"))
    async def shift_confirm_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await callback.answer("❌ Only host can confirm shift!", show_alert=True)
            return
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ Game not found!", show_alert=True)
            return
        
        data = callback.data.split("_")
        user_to_shift_id = int(data[2])
        current_team = data[3]
        target_team = data[4]
        
        player = None
        if current_team == "A":
            for i, p in enumerate(game["team_a"]):
                if p["id"] == user_to_shift_id:
                    player = game["team_a"].pop(i)
                    game["team_b"].append(player)
                    break
        else:
            for i, p in enumerate(game["team_b"]):
                if p["id"] == user_to_shift_id:
                    player = game["team_b"].pop(i)
                    game["team_a"].append(player)
                    break
        
        if not player:
            await callback.answer("❌ Player not found!", show_alert=True)
            return
        
        username_display = f"@{player['username']}" if player['username'] else player['name']
        
        await callback.message.delete()
        await callback.message.reply(
            f"🔄 {username_display} shifted from Team {current_team} to Team {target_team}!\n\n"
            f"🏏 Team A: {len(game['team_a'])} players\n"
            f"🏏 Team B: {len(game['team_b'])} players"
        )
        await callback.answer("✅ Player shifted successfully!")

    # ================= SHIFT CANCEL CALLBACK =================
    @app.on_callback_query(filters.regex("^shift_cancel$"))
    async def shift_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Shift cancelled!")

    # ================= START MATCH =================
    @app.on_message(filters.command("start_match") & filters.group)
    async def start_match_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can start the match!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "ready":
            await message.reply("❌ Teams not ready!")
            return
        
        game["match_start_time"] = datetime.now()
        game["status"] = "playing"
        
        await message.reply("🚀 Match is starting...\n\n🏏 Team A will bat first!")
        
        await start_team_batting(client, chat_id, "A")

    # ================= END MATCH COMMAND =================
    @app.on_message(filters.command("end_match") & filters.group)
    async def end_match_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if user is host OR group admin
        host = team_hosts.get(chat_id)
        is_host = host and host["id"] == user_id
        is_group_admin = await is_admin(client, chat_id, user_id)
        
        if not (is_host or is_group_admin):
            await message.reply("❌ Only host or group admin can end the match!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game found!")
            return
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm", callback_data="end_match_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="end_match_cancel")
            ]
        ])
        
        await message.reply(
            "⚠️ Are you sure you want to end the match?",
            reply_markup=keyboard
        )

            # ================= END MATCH CONFIRM =================
    @app.on_callback_query(filters.regex("^end_match_confirm$"))
    async def end_match_confirm_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        # Check if user is host OR group admin
        host = team_hosts.get(chat_id)
        is_host = host and host["id"] == user_id
        is_group_admin = await is_admin(client, chat_id, user_id)
        
        if not (is_host or is_group_admin):
            await callback.answer("❌ Only host or group admin can end the match!", show_alert=True)
            return
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        # Create match report (with or without scores)
        from datetime import datetime
        current_time = datetime.now()
        
        if game.get("match_start_time") is None:
            # Match never started - just team info
            date_str = current_time.strftime('%Y-%m-%d')
            time_str = current_time.strftime('%H:%M:%S')
            
            match_report = f"""═══════════════════════════════
         🏏 MATCH CANCELLED 🏏
═══════════════════════════════

📅 Date: {date_str}
⏰ Time: {time_str}
👑 Host: {game['host_name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 TEAM INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏏 TEAM A: {len(game['team_a'])} players
🏏 TEAM B: {len(game['team_b'])} players

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         👥 TEAM A PLAYERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            for p in game["team_a"]:
                match_report += f"\n   🏏 {p['name']} - Not played"

            match_report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         👥 TEAM B PLAYERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            for p in game["team_b"]:
                match_report += f"\n   🏏 {p['name']} - Not played"

            match_report += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ℹ️ STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ❌ Match was cancelled before start!

═══════════════════════════════
      Match Cancelled!
═══════════════════════════════"""
            
            await callback.message.edit_text("🏏 Match ended successfully!")
            
        else:
            # Match started - full report with scores
            game["match_end_time"] = current_time
            game["game_over"] = True
            
            # Calculate winner
            if game["team_a_score"] > game["team_b_score"]:
                winner = "Team A"
                win_margin = f"{game['team_a_score'] - game['team_b_score']} runs"
            elif game["team_b_score"] > game["team_a_score"]:
                winner = "Team B"
                win_margin = f"{game['team_b_score'] - game['team_a_score']} runs"
            else:
                winner = "Match Tied"
                win_margin = "0 runs"
            
            start_time = game['match_start_time']
            date_str = start_time.strftime('%Y-%m-%d')
            time_str = start_time.strftime('%H:%M:%S')
            
            match_report = f"""═══════════════════════════════
         🏏 MATCH REPORT 🏏
═══════════════════════════════

📅 Date: {date_str}
⏰ Time: {time_str}
👑 Host: {game['host_name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 FINAL SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏏 TEAM A: {game['team_a_score']}/{game['team_a_wickets']}
🏏 TEAM B: {game['team_b_score']}/{game['team_b_wickets']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🏆 WINNER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   🎉 {winner} ({win_margin}) 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         👥 TEAM A PLAYERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            for p in game["team_a"]:
                status = "❌" if p.get("out", False) else "🏏"
                match_report += f"\n   {status} {p['name']} - {p.get('score', 0)} runs ({p.get('balls', 0)} balls)"
                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    match_report += f" (4s: {p.get('fours', 0)}, 6s: {p.get('sixes', 0)})"

            match_report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         👥 TEAM B PLAYERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            for p in game["team_b"]:
                status = "❌" if p.get("out", False) else "🏏"
                match_report += f"\n   {status} {p['name']} - {p.get('score', 0)} runs ({p.get('balls', 0)} balls)"
                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    match_report += f" (4s: {p.get('fours', 0)}, 6s: {p.get('sixes', 0)})"

            match_report += """

═══════════════════════════════
      Match Ended Successfully!
═══════════════════════════════"""
            
            await callback.message.edit_text("🏏 Match ended successfully!")
        
        # Send report as text file
        report_bytes = io.BytesIO(match_report.encode('utf-8'))
        report_bytes.name = f"match_report_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        await client.send_document(
            chat_id,
            report_bytes,
            caption="📄 Game data saved before ending the match."
        )
        
        # Clean up
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        await callback.answer("✅ Match ended!")
        
    # ================= END MATCH CANCEL =================
    @app.on_callback_query(filters.regex("^end_match_cancel$"))
    async def end_match_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Match end cancelled!")

    # ================= TEAM BATTING =================
    async def start_team_batting(client, chat_id, team):
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
        game["current_bowler_index"] = 1 if len(players) > 1 else 0
        game["current_bowler"] = players[game["current_bowler_index"]].copy()
        game["current_bowler_balls"] = 0
        game["bowling_number"] = None
        game["team_total"] = 0
        game["team_wickets"] = 0
        game["status"] = "playing"
        
        await client.send_message(chat_id, f"🏏 **Team {team} Batting**\n\nBatter: [{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})\nBowler: [{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})")
        
        await send_bowling_video(client, chat_id, game["current_bowler"])

    # ================= BALL SELECTION MENU =================
    async def ball_selection_menu(client, callback):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = """🥎 Choose the Bowling mode:

Solo Play - 1 Ball
Solo Play - 3 Ball"""
        
        await callback.message.delete()
        
        try:
            await callback.message.reply_photo(
                SOLO_PLAY_IMG,
                caption=caption,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending solo play image: {e}")
            await callback.message.reply(
                caption,
                reply_markup=keyboard
            )
        await callback.answer()

    # ================= BALL SELECTION HANDLER =================
    @app.on_callback_query(filters.regex("^ball_"))
    async def ball_handler(client, callback: CallbackQuery):
        action = callback.data.split("_")[1]
        
        ball_mode = int(action)
        chat_id = callback.message.chat.id
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        
        await callback.message.delete()
        
        await client.send_message(
            chat_id,
            f"🎉Game created! Join the game using /joingame (2 minutes to join)\n⏰"
        )
        
        asyncio.create_task(start_join_timer(client, chat_id))

    # ================= JOIN TIMER =================
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
            
            if players_count < 1:
                await client.send_message(chat_id, "No players joined! Game cancelled.")
                if chat_id in games:
                    del games[chat_id]
            else:
                await client.send_message(chat_id, f"Time's up! Starting game with {players_count} players...")
                await start_game_match(client, chat_id)

    # ================= VOTE SYSTEM =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"Voting in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        caption = """VOTING REQUIRED!

You are not an admin. 3 votes needed.

Current votes: 0/3"""
        
        try:
            msg = await message.reply_photo(
                VOTE_IMG, 
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
            )
        except:
            msg = await message.reply(
                caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
            )
        
        active_votes[chat_id]["msg_id"] = msg.id
        asyncio.create_task(auto_cancel_vote(client, chat_id))

    # ================= VOTE BUTTON =================
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
        
        voters = []
        for uid in vote["users"]:
            try:
                u = await client.get_users(uid)
                name = u.first_name if u.first_name else f"User_{uid}"
                voters.append(f"• {name}")
            except:
                voters.append(f"• User_{uid}")
        
        if vote["count"] >= 3:
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            vote["active"] = False
            await callback.answer("Voting successful!")
        else:
            caption = f"""VOTING REQUIRED!

You are not an admin. 3 votes needed.

Current votes: {vote['count']}/3

Voters:
{chr(10).join(voters)}"""
            
            try:
                await callback.message.edit_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
                )
            except:
                await callback.message.edit_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
                )
            await callback.answer(f"Voted! ({vote['count']}/3)")

    # ================= AUTO CANCEL VOTE =================
    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote = active_votes.get(chat_id)
        if vote and vote.get("active") and vote["count"] < 3:
            try:
                await client.edit_message_caption(
                    chat_id, vote["msg_id"],
                    caption=f"Voting expired! Got {vote['count']}/3 votes.\nUse /start again."
                )
            except:
                pass
            vote["active"] = False

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return await message.reply("No active game! Use /start")
        
        if game.get("status") != "waiting":
            return await message.reply("Game already started!")
        
        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            players_count = len(game["players"])
            await message.reply(f"🎉{message.from_user.first_name}, you've joined the game! (Player {players_count}) 👍")

    # ================= START GAME MATCH =================
    async def start_game_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        players_count = len(game["players"])
        if players_count < 1:
            await client.send_message(chat_id, "No players to start the game!")
            return
        
        start_match(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        host_text = "SOLO TREE COMMUNITY\n\nUnknown Host\n\nSolo Players\n\n"
        for i, p in enumerate(players, 1):
            name = f"@{p['username']}" if p.get("username") else p["name"]
            host_text += f"{i}. {name}\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text)
        except:
            await client.send_message(chat_id, host_text)
        
        batter = game["current_batter"]
        await client.send_message(chat_id, f"Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batter!")
        
        bowler = game["current_bowler"]
        await client.send_message(chat_id, f"Hey [{bowler['name']}](tg://user?id={bowler['id']}), now you're bowling!")
        
        await asyncio.sleep(1)
        await send_bowling_video(client, chat_id, bowler)

    # ================= SEND BOWLING VIDEO =================
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
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"[{bowler['name']}](tg://user?id={bowler['id']}) now you can send number on bot pm, You have 1 min.",
            reply_markup=keyboard
        )
        
        try:
            await client.send_message(
                bowler["id"],
                f"Current batter: [{batter['name']}](tg://user?id={batter['id']})\n\nSend Your number:",
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

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
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
            await client.send_video(
                chat_id, 
                BATTING_VIDEO,
                caption=f"Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batting! Send number (1-6) in GROUP"
            )
            return
        
        await message.reply("❌ No active game found where you are the bowler!")

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return
        if game.get("status") != "playing":
            return
        if game.get("game_over"):
            return
        if game.get("bowling_number") is None:
            return
        
        batter = game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        
        text = message.text.strip()
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        try:
            await client.send_reaction(message.chat.id, message.id, "👍")
        except:
            pass
        
        bat = int(text)
        result = play_ball(chat_id, bat)
        bow = game.get("bowling_number", "?")
        game["bowling_number"] = None
        
        bowler = game["current_bowler"]
        ball_mode = game.get("ball_mode", 3)
        
        if result["type"] == "out":
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            
            if game.get("game_over"):
                final_text = build_scoreboard(game["players"], is_final=True)
                await message.reply(final_text)
                if chat_id in games:
                    del games[chat_id]
                return
            
            await message.reply(build_scoreboard(game["players"], is_final=False))
            
            new_batter = game["current_batter"]
            await client.send_message(chat_id, f"Hey [{new_batter['name']}](tg://user?id={new_batter['id']}), now you're batter!")
            await client.send_message(chat_id, f"New batsman: [{new_batter['name']}](tg://user?id={new_batter['id']})\n\nGet ready for the next ball ⚾")
            
            if not game.get("game_over"):
                new_bowler = game["current_bowler"]
                await send_bowling_video(client, chat_id, new_bowler)
            
        else:
            try:
                await message.reply_video(get_run_video(result["runs"]), caption=RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            
            if not game.get("game_over"):
                if game["current_bowler_balls"] >= ball_mode:
                    await message.reply(build_scoreboard(game["players"], is_final=False))
                    new_bowler = game["current_bowler"]
                    await client.send_message(chat_id, f"Bowler changed! Now bowling: [{new_bowler['name']}](tg://user?id={new_bowler['id']})")
                    await send_bowling_video(client, chat_id, new_bowler)
                else:
                    await send_bowling_video(client, chat_id, bowler)
