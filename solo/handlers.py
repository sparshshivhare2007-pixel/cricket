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
import random

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
        
        # Check solo mode games
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
        
        # Check team mode games
        for chat_id, game in team_games.items():
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
            [InlineKeyboardButton("👤 Solo", callback_data="mode_solo"), InlineKeyboardButton("👥 Team", callback_data="mode_team")],
            [InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel")]
        ])
        
        caption = """🏏 **Select Game Mode** 🏏

Choose how you want to play:"""

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
        
        if action == "solo":
            await ball_selection_menu(client, callback)

    # ================= TEAM MODE START =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
        ])
        
        caption = """🎉 **New Game Alert!** 🎉 

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
        
        existing_game = team_games.get(chat_id)
        if existing_game and existing_game.get("status") == "playing":
            await callback.answer("❌ A match is currently in progress! Cannot change host.", show_alert=True)
            return
        
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
        
        # TEAM IMAGE with caption
        try:
            await client.send_photo(
                chat_id,
                TEAM_CHAPU_IMG,  # config mein TEAM_CHAPU_IMG = "your_image_url"
                caption="🏏 **Team Mode Activated!** 🏏\n\nUse /create_team to start creating teams!"
            )
        except:
            await client.send_message(
                chat_id,
                "🏏 **Team Mode Activated!** 🏏\n\nUse /create_team to start creating teams!"
            )
        
        await callback.answer()

    # ================= CREATE TEAM COMMAND =================
    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
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
            asyncio.create_task(team_b_timer(client, chat_id))

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
            game["status"] = "captain_selection"
            await client.send_message(
                chat_id,
                f"👋 Hey, now members are joined the teams! 🎉 Choose Team captains user /choose_cap 📝"
            )

    # ================= CHOOSE CAPTAIN COMMAND =================
    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Sirf HOST hi /choose_cap command use kar sakta hai
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
        
        # Sirf 2 buttons - members click karenge
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")],
            [InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")]
        ])
        
        await message.reply(
            "🏏 **Captain Selection!** 🏏\n\n"
            "Team A members click 'Team A Captain' button to become captain.\n"
            "Team B members click 'Team B Captain' button to become captain.\n\n"
            "Click on your team's button!",
            reply_markup=keyboard
        )

    # ================= CHOOSE CAPTAIN A (Members click) =================
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
        user_name = ""
        for player in game["team_a"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_a"] = player
                break
        else:
            await callback.answer("❌ You are not in Team A!", show_alert=True)
            return
        
        await callback.answer(f"✅ {user_name} is now Team A Captain!")
        
        # Check if both captains selected
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            # Team A button gayab, sirf Team B button rahega
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")]
            ])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"✅ Team A Captain: {user_name}\n"
                f"⚠️ Team B Captain: Not selected yet\n\n"
                f"Team B members click 'Team B Captain' button to become captain.",
                reply_markup=keyboard
            )

    # ================= CHOOSE CAPTAIN B (Members click) =================
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
        user_name = ""
        for player in game["team_b"]:
            if player["id"] == user_id:
                user_name = player["name"]
                game["captain_b"] = player
                break
        else:
            await callback.answer("❌ You are not in Team B!", show_alert=True)
            return
        
        await callback.answer(f"✅ {user_name} is now Team B Captain!")
        
        # Check if both captains selected
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            # Team B button gayab, sirf Team A button rahega
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")]
            ])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n"
                f"⚠️ Team A Captain: Not selected yet\n"
                f"✅ Team B Captain: {user_name}\n\n"
                f"Team A members click 'Team A Captain' button to become captain.",
                reply_markup=keyboard
            )

    # ================= START TOSS =================
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

    # ================= TOSS CALLBACK =================
    @app.on_callback_query(filters.regex("^toss_"))
    async def toss_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "toss":
            await callback.answer("❌ No toss in progress!", show_alert=True)
            return
        
        # Only Team A captain can do toss
        if game["captain_a"]["id"] != user_id:
            await callback.answer("❌ Only Team A captain can do the toss!", show_alert=True)
            return
        
        choice = callback.data.split("_")[1]  # "heads" or "tails"
        toss_result = random.choice(["heads", "tails"])
        
        cap_a_name = game['captain_a']['name']
        cap_b_name = game['captain_b']['name']
        
        toss_video_url = TOSS_VIDEO  # config mein TOSS_VIDEO dalna
        
        await callback.message.delete()
        
        if choice == toss_result:
            winner = "A"
            winner_name = cap_a_name
            
            await client.send_video(
                chat_id,
                toss_video_url,
                caption=f"🪙 The coin shows: {toss_result.upper()}!\n\n"
                        f"🅰️ - {cap_a_name} chose {choice.upper()}\n"
                        f"🅱️ {cap_b_name} got {toss_result.upper()}\n\n"
                        f"🏆 - {winner_name} from Team A won the toss!\n\n"
                        f"🏆 - {winner_name}, please choose to Bat or Bowl:"
            )
        else:
            winner = "B"
            winner_name = cap_b_name
            
            await client.send_video(
                chat_id,
                toss_video_url,
                caption=f"🪙 The coin shows: {toss_result.upper()}!\n\n"
                        f"🅰️ - {cap_a_name} chose {choice.upper()}\n"
                        f"🅱️ {cap_b_name} got {toss_result.upper()}\n\n"
                        f"🏆 - {winner_name} from Team B won the toss!\n\n"
                        f"🏆 - {winner_name}, please choose to Bat or Bowl:"
            )
        
        # Decision buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 BAT FIRST", callback_data="toss_bat")],
            [InlineKeyboardButton("⚾ BOWL FIRST", callback_data="toss_bowl")]
        ])
        
        await client.send_message(chat_id, "Choose your option:", reply_markup=keyboard)
        game["toss_winner"] = winner

    # ================= TOSS DECISION =================
    @app.on_callback_query(filters.regex("^toss_bat$|^toss_bowl$"))
    async def toss_decision_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        decision = callback.data.split("_")[1]  # "bat" or "bowl"
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
        await select_overs(client, chat_id, batting_team)

    # ================= SELECT OVERS =================
    async def select_overs(client, chat_id, batting_team):
        game = team_games.get(chat_id)
        if not game:
            return
        
        # 20 buttons (1 to 20 overs)
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

    # ================= OVER SELECTION CALLBACK =================
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
        
        await client.send_message(
            chat_id,
            f"✅ Match set! {overs} overs per side.\n\n"
            f"🚀 Match is starting...\n"
            f"🏏 {team_name} will bat first!\n\n"
            f"Let the game begin! 🎉"
        )
        
        game["match_start_time"] = datetime.now()
        game["status"] = "playing"
        
        await start_team_batting(client, chat_id, batting_team)

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
        
        await client.send_message(chat_id, f"🏏 **Team {team} Batting**\n\nBatter: [{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})\nBowler: [{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})")
        
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    # ================= SEND BOWLING VIDEO TEAM =================
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
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"[{bowler['name']}](tg://user?id={bowler['id']}) now you can send number on bot pm, You have 1 min.",
            reply_markup=keyboard
        )
        
        try:
            await client.send_message(
                bowler["id"],
                f"🎯 Current batter: [{batter['name']}](tg://user?id={batter['id']})\n\nSend Your number (1-6):",
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

    # ================= BOWLING TIMEOUT WITH WARNINGS TEAM =================
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
                        player["history"].append("PENALTY(-6)")
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

    # ================= BUILD TEAM SCOREBOARD =================
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

    # ================= BOWLING DM (Updated for team mode) =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm_team(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        if text.startswith("/start"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        num = int(text)
        
        # Check solo mode games first
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
        
        # Check team mode games
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
            await client.send_message(
                chat_id,
                f"🎯 Bowler bowled {num}! Now [{batter['name']}](tg://user?id={batter['id']}), send your batting number (1-6) in GROUP"
            )
            return
        
        await message.reply("❌ No active game found where you are the bowler!")

    # ================= BATTING FOR TEAM MODE =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg_team(client, message):
        chat_id = message.chat.id
        
        # Check solo mode first
        game = games.get(chat_id)
        if game:
            if game.get("status") != "playing" or game.get("game_over") or game.get("bowling_number") is None:
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
                await client.send_message(chat_id, f"🎯 Hey [{new_batter['name']}](tg://user?id={new_batter['id']}), now you're batter!")
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
                        await client.send_message(chat_id, f"🔄 Bowler changed! Now bowling: [{new_bowler['name']}](tg://user?id={new_bowler['id']})")
                        await send_bowling_video(client, chat_id, new_bowler)
                    else:
                        await send_bowling_video(client, chat_id, bowler)
            return
        
        # Check team mode
        team_game = team_games.get(chat_id)
        if not team_game:
            return
        
        if team_game.get("status") != "playing" or team_game.get("game_over"):
            return
        if team_game.get("bowling_number") is None:
            return
        
        batter = team_game.get("current_batter")
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
        bow = team_game.get("bowling_number", "?")
        team_game["bowling_number"] = None
        
        bowler = team_game["current_bowler"]
        team_key = f"team_{team_game['current_team'].lower()}"
        
        if bat == bow:
            batter["out"] = True
            team_game["team_wickets"] += 1
            
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            
            active_batters = [p for p in team_game[team_key] if not p.get("out", False)]
            
            if len(active_batters) == 0 or team_game["team_wickets"] >= len(team_game[team_key]):
                team_game["status"] = "innings_break"
                
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
                await message.reply_video(get_run_video(runs), caption=RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{runs} run{'s' if runs > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{runs} run{'s' if runs > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            
            if team_game["current_team"] == "B" and team_game["team_total"] > team_game["team_a_score"]:
                team_game["team_b_score"] = team_game["team_total"]
                team_game["game_over"] = True
                team_game["winner"] = "Team B"
                
                await client.send_message(chat_id, build_team_scoreboard(team_game))
                await client.send_message(chat_id, f"🏆 **Team B Wins!**\n\nTarget: {team_game['team_a_score'] + 1}\nTeam B: {team_game['team_b_score']}\n\nTeam B wins by {len(team_game[team_key]) - team_game['team_wickets']} wickets!")
                
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

    # ================= BALL SELECTION MENU =================
    async def ball_selection_menu(client, callback):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎯 Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = """🏏 **Choose Bowling Mode** 🏏

• Solo Play - 1 Ball (Single ball per bowler)
• Solo Play - 3 Ball (Three balls per bowler)"""
        
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
            f"🎉 Game created! Join the game using /joingame (2 minutes to join)\n⏰"
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
        
        caption = """🗳️ **VOTING REQUIRED!** 🗳️

You are not an admin. 3 votes needed.

Current votes: 0/3"""
        
        try:
            msg = await message.reply_photo(
                VOTE_IMG, 
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]])
            )
        except:
            msg = await message.reply(
                caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]])
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
            caption = f"""🗳️ **VOTING REQUIRED!** 🗳️

You are not an admin. 3 votes needed.

Current votes: {vote['count']}/3

**Voters:**
{chr(10).join(voters)}"""
            
            try:
                await callback.message.edit_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]])
                )
            except:
                await callback.message.edit_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]])
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
                    caption=f"❌ Voting expired! Got {vote['count']}/3 votes.\nUse /start again."
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
            await message.reply(f"🎉 {message.from_user.first_name}, you've joined the game! (Player {players_count}) 👍")

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
        
        host_text = "🏏 **SOLO TREE COMMUNITY** 🏏\n\n"
        host_text += "**Players List:**\n"
        for i, p in enumerate(players, 1):
            name = f"@{p['username']}" if p.get("username") else p["name"]
            host_text += f"{i}. {name}\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text)
        except:
            await client.send_message(chat_id, host_text)
        
        batter = game["current_batter"]
        await client.send_message(chat_id, f"🎯 Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batter!")
        
        bowler = game["current_bowler"]
        await client.send_message(chat_id, f"🎯 Hey [{bowler['name']}](tg://user?id={bowler['id']}), now you're bowling!")
        
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
                f"🎯 Current batter: [{batter['name']}](tg://user?id={batter['id']})\n\nSend Your number (1-6):",
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
