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

print("🔴 LOADING HANDLERS.PY - FINAL COMPLETE VERSION")

active_votes = {}
bowling_tasks = {}

team_games = {}
team_hosts = {}
user_reports = {}

# Store selected batters (1st, 2nd, etc.)
selected_batters = {}
pending_bowler_selection = {}
pending_batter_selection = {}
bowling_numbers_store = {}
batting_numbers_store = {}

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
        await message.reply("🏏 **Welcome to Cricket Game Bot!**\n\nUse me in a group to play cricket games.")

    @app.on_message(filters.command("help") & filters.group)
    async def help_cmd(client, message: Message):
        help_text = """🏏 **Cricket Game Bot Commands** 🏏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎮 TEAM MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/start - Start game (Admin)
/create_team - Create teams (Host)
/join_teamA - Join Team A
/join_teamB - Join Team B
/choose_cap - Choose captains (Host)
/startgame - Start toss & overs (Host)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎯 GAME COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/choose_bat - Toss winner choose BAT first
/choose_bowl - Toss winner choose BOWL first
/bowling <number> - Choose bowler (Host)
/batting <number> - Choose batter (Host)
/swap - Change innings (Host)
/member_lists - View team members

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎮 SOLO MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/joingame - Join solo game
/score - Check live score

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Bot must be admin in group
• Send numbers in bot PM when asked

🏏 **Enjoy the game!** 🏏"""
        
        await message.reply(help_text)

    @app.on_message(filters.command("member_lists") & filters.group)
    async def member_lists_cmd(client, message: Message):
        chat_id = message.chat.id
        team_game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not team_game:
            await message.reply("❌ No active team game!")
            return
        
        host_name = f"[{host['name']}](tg://user?id={host['id']})" if host else "Unknown"
        
        text = f"👽 **Game Host:** {host_name}\n\n"
        
        current_team = team_game.get('current_team', 'None')
        if current_team != 'None':
            text += f"🏏 **Batting:** Team {current_team}\n"
            text += f"🎯 **Bowling:** Team {'B' if current_team == 'A' else 'A'}\n\n"
        else:
            text += f"🏏 **Status:** {team_game.get('status', 'Unknown')}\n\n"
        
        cap_a = team_game.get("captain_a")
        cap_b = team_game.get("captain_b")
        
        text += f"🎩 **Team A Captain:** {cap_a['name'] if cap_a else 'None'}\n"
        text += f"👒 **Team B Captain:** {cap_b['name'] if cap_b else 'None'}\n\n"
        
        text += "🔵 **Team A**\n"
        for i, p in enumerate(team_game.get("team_a", []), 1):
            text += f"{i}. {p['name']}"
            if cap_a and p["id"] == cap_a["id"]:
                text += " [🧢]"
            text += "\n"
        
        text += "\n🔴 **Team B**\n"
        for i, p in enumerate(team_game.get("team_b", []), 1):
            text += f"{i}. {p['name']}"
            if cap_b and p["id"] == cap_b["id"]:
                text += " [🧢]"
            text += "\n"
        
        await message.reply(text)

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Solo", callback_data="mode_solo"), InlineKeyboardButton("👥 Team", callback_data="mode_team")],
            [InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel")]
        ])
        
        await message.reply("🏏 **Select Game Mode**", reply_markup=keyboard)

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
            [InlineKeyboardButton("🎯 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎯 3 Ball", callback_data="ball_3")]
        ])
        
        await callback.message.delete()
        await callback.message.reply("🏏 **Choose Bowling Mode**", reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^ball_"))
    async def ball_handler(client, callback: CallbackQuery):
        ball_mode = int(callback.data.split("_")[1])
        chat_id = callback.message.chat.id
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["status"] = "waiting"
        game["players"] = []
        
        await callback.message.delete()
        await client.send_message(chat_id, "🎉 Solo game created! Use /joingame to join (2 minutes)")
        
        asyncio.create_task(solo_join_timer(client, chat_id))

    async def solo_join_timer(client, chat_id):
        await asyncio.sleep(120)
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            if len(game.get("players", [])) < 2:
                await client.send_message(chat_id, "❌ Not enough players! Game cancelled.")
                if chat_id in games:
                    del games[chat_id]
            else:
                await start_solo_match(client, chat_id)

    async def start_solo_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        start_match(chat_id)
        game = games[chat_id]
        
        players_text = "🏏 **SOLO CRICKET** 🏏\n\n**Players:**\n"
        for i, p in enumerate(game["players"], 1):
            players_text += f"{i}. {p['name']}\n"
        
        await client.send_message(chat_id, players_text)
        
        batter = game["current_batter"]
        bowler = game["current_bowler"]
        
        await client.send_message(chat_id, f"🎯 Batter: {batter['name']}\n⚾ Bowler: {bowler['name']}")
        await send_bowling_video_solo(client, chat_id, bowler)

    async def send_bowling_video_solo(client, chat_id, bowler):
        game = games.get(chat_id)
        if not game or game.get("status") != "playing":
            return
        
        bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"{bowler_clickable} now you can send a number in the bot PM. You have 1 min."
        )
        
        try:
            await client.send_message(
                bowler["id"],
                f"🎯 Send bowling number (1-6):\n\n⏰ You have 60 seconds!"
            )
        except:
            pass

    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            await message.reply("❌ No active solo game!")
            return
        
        for p in game.get("players", []):
            if p["id"] == user.id:
                await message.reply("❌ Already joined!")
                return
        
        game["players"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✅ {user.first_name} joined! ({len(game['players'])} players)")

    # ================= TEAM MODE START =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
        ])
        
        await client.send_message(chat_id, "🎉 **Who will be the game host?**", reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_games:
            await callback.answer("❌ Game already in progress!", show_alert=True)
            return
        
        team_hosts[chat_id] = {"id": user.id, "name": user.first_name, "username": user.username}
        
        team_games[chat_id] = {
            "host_id": user.id, "host_name": user.first_name,
            "status": "waiting_host",
            "team_a": [], "team_b": [],
            "captain_a": None, "captain_b": None,
            "team_a_score": 0, "team_b_score": 0,
            "team_a_wickets": 0, "team_b_wickets": 0,
            "current_team": None, "game_over": False,
            "current_batter": None, "current_bowler": None,
            "bowling_number": None, "team_total": 0, "team_wickets": 0,
            "total_balls_in_inning": 0, "current_bowler_balls": 0,
            "current_batter_index": 0, "current_bowler_index": 0,
            "overs": 0, "ball_mode": 1, "toss_winner": None,
            "batting_first": None, "batting_order": []
        }
        
        await callback.message.delete()
        await client.send_message(chat_id, f"👑 [{user.first_name}](tg://user?id={user.id}) is the host! Use /create_team to start.")
        await callback.answer()

    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "waiting_host":
            await message.reply("❌ No active game!")
            return
        
        game["team_a"] = []
        game["team_b"] = []
        game["status"] = "team_creation_a"
        
        await message.reply("📣 Join Team A: /join_teamA\n⏰ 50 seconds")
        asyncio.create_task(team_a_timer(client, chat_id))

    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, "📣 Join Team B: /join_teamB\n⏰ 50 seconds")
            asyncio.create_task(team_b_timer(client, chat_id))

    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            game["status"] = "captain_selection"
            await client.send_message(chat_id, "✅ Teams created! Use /choose_cap to select captains.")

    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "team_creation_a":
            await message.reply("❌ Team A is not open!")
            return
        
        host = team_hosts.get(chat_id)
        if host and host["id"] == user.id:
            await message.reply("❌ Host cannot join teams!")
            return
        
        for p in game.get("team_a", []):
            if p["id"] == user.id:
                await message.reply("❌ Already in Team A!")
                return
        
        game["team_a"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✅ {user.first_name} joined Team A! ({len(game['team_a'])} players)")

    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "team_creation_b":
            await message.reply("❌ Team B is not open!")
            return
        
        host = team_hosts.get(chat_id)
        if host and host["id"] == user.id:
            await message.reply("❌ Host cannot join teams!")
            return
        
        for p in game.get("team_b", []):
            if p["id"] == user.id:
                await message.reply("❌ Already in Team B!")
                return
        
        game["team_b"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✅ {user.first_name} joined Team B! ({len(game['team_b'])} players)")

    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can choose captains!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "captain_selection":
            await message.reply("❌ No active game!")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 Team A Captain", callback_data="cap_a")],
            [InlineKeyboardButton("🏏 Team B Captain", callback_data="cap_b")]
        ])
        
        await message.reply("🏏 **Select captains:**", reply_markup=keyboard)

    @app.on_callback_query(filters.regex("^cap_"))
    async def cap_selection_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        team = callback.data.split("_")[1].upper()
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No game!", show_alert=True)
            return
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await callback.answer("❌ Only host can select!", show_alert=True)
            return
        
        if team == "A" and game.get("captain_a"):
            await callback.answer("❌ Team A captain already selected!", show_alert=True)
            return
        if team == "B" and game.get("captain_b"):
            await callback.answer("❌ Team B captain already selected!", show_alert=True)
            return
        
        if team == "A":
            await callback.message.reply("👑 **Team A members:** Send /iamcaptain to become captain!")
        else:
            await callback.message.reply("👑 **Team B members:** Send /iamcaptain to become captain!")
        
        pending_captain_selection[chat_id] = team
        await callback.answer()

    pending_captain_selection = {}

    @app.on_message(filters.command("iamcaptain") & filters.group)
    async def iam_captain_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        
        team = pending_captain_selection.get(chat_id)
        if not team:
            await message.reply("❌ No captain selection in progress!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            return
        
        if team == "A":
            for p in game["team_a"]:
                if p["id"] == user.id:
                    game["captain_a"] = p
                    await message.reply(f"✅ {user.first_name} is now Team A Captain!")
                    break
            else:
                await message.reply("❌ You are not in Team A!")
                return
        else:
            for p in game["team_b"]:
                if p["id"] == user.id:
                    game["captain_b"] = p
                    await message.reply(f"✅ {user.first_name} is now Team B Captain!")
                    break
            else:
                await message.reply("❌ You are not in Team B!")
                return
        
        if game.get("captain_a") and game.get("captain_b"):
            del pending_captain_selection[chat_id]
            await client.send_message(chat_id, f"✅ Both captains selected!\n\nTeam A: {game['captain_a']['name']}\nTeam B: {game['captain_b']['name']}\n\nHost use /startgame to begin!")

    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can start the game!")
            return
        
        game = team_games.get(chat_id)
        if not game or not game.get("captain_a") or not game.get("captain_b"):
            await message.reply("❌ Captains not selected! Use /choose_cap first.")
            return
        
        await start_toss(client, chat_id)

    async def start_toss(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 HEADS", callback_data="toss_heads")],
            [InlineKeyboardButton("🪙 TAILS", callback_data="toss_tails")]
        ])
        
        await client.send_message(
            chat_id,
            f"🎉 **TOSS TIME!** 🎉\n\n"
            f"🏏 Team A Captain: {game['captain_a']['name']}\n"
            f"🏏 Team B Captain: {game['captain_b']['name']}\n\n"
            f"🪙 {game['captain_a']['name']}, choose Heads or Tails:",
            reply_markup=keyboard
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
            await callback.answer("❌ Only Team A captain can toss!", show_alert=True)
            return
        
        choice = callback.data.split("_")[1]
        toss_result = random.choice(["heads", "tails"])
        
        await callback.message.delete()
        
        if choice == toss_result:
            winner = game['captain_a']
            winner_team = "A"
        else:
            winner = game['captain_b']
            winner_team = "B"
        
        game["toss_winner"] = winner_team
        
        await client.send_message(
            chat_id,
            f"🪙 The coin shows: {toss_result.upper()}!\n\n"
            f"🅰️ - {game['captain_a']['name']} chose {choice.upper()}\n"
            f"🅱️ - {game['captain_b']['name']} got {toss_result.upper()}\n\n"
            f"🏆 [{winner['name']}](tg://user?id={winner['id']}) from Team {winner_team} won the toss!\n\n"
            f"🏆 Please choose to Bat or Bowl:\n"
            f"/choose_bat - BAT FIRST\n"
            f"/choose_bowl - BOWL FIRST"
        )
        
        game["status"] = "toss_decision"

    @app.on_message(filters.command("choose_bat") & filters.group)
    async def choose_bat_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "toss_decision":
            await message.reply("❌ No toss decision pending!")
            return
        
        toss_winner = game.get("toss_winner")
        winner_captain = game["captain_a"] if toss_winner == "A" else game["captain_b"]
        
        if winner_captain["id"] != user_id:
            await message.reply("❌ Only toss winner can choose!")
            return
        
        batting_team = toss_winner
        game["batting_first"] = batting_team
        
        await message.reply(
            f"🏏 Team {'A' if batting_team == 'A' else 'B'} chose to BAT first!\n"
            f"⚾ Team {'B' if batting_team == 'A' else 'A'} will BOWL first.\n\n"
            f"🏏 Batting: Team {'A' if batting_team == 'A' else 'B'}\n"
            f"🧤 Bowling: Team {'B' if batting_team == 'A' else 'A'}\n\n"
            f"Select overs (1-20):"
        )
        
        await select_overs(client, chat_id, batting_team)

    @app.on_message(filters.command("choose_bowl") & filters.group)
    async def choose_bowl_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "toss_decision":
            await message.reply("❌ No toss decision pending!")
            return
        
        toss_winner = game.get("toss_winner")
        winner_captain = game["captain_a"] if toss_winner == "A" else game["captain_b"]
        
        if winner_captain["id"] != user_id:
            await message.reply("❌ Only toss winner can choose!")
            return
        
        batting_team = "B" if toss_winner == "A" else "A"
        game["batting_first"] = batting_team
        
        await message.reply(
            f"⚾ Team {'A' if toss_winner == 'A' else 'B'} chose to BOWL first!\n"
            f"🏏 Team {'A' if batting_team == 'A' else 'B'} will BAT first.\n\n"
            f"🏏 Batting: Team {'A' if batting_team == 'A' else 'B'}\n"
            f"🧤 Bowling: Team {'A' if toss_winner == 'A' else 'B'}\n\n"
            f"Select overs (1-20):"
        )
        
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
        
        await client.send_message(chat_id, "📊 **Select number of overs:**", reply_markup=keyboard)
        
        game["status"] = "over_selection"
        game["batting_first"] = batting_team

    @app.on_callback_query(filters.regex("^over_"))
    async def over_selection_callback(client, callback):
        chat_id = callback.message.chat.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "over_selection":
            await callback.answer("❌ No over selection!", show_alert=True)
            return
        
        overs = int(callback.data.split("_")[1])
        game["overs"] = overs
        game["total_balls_limit"] = overs * 6
        
        await callback.message.delete()
        
        batting_team = game["batting_first"]
        
        await client.send_message(
            chat_id,
            f"✅ Match set! {overs} overs per side.\n\n"
            f"🏏 Team {'A' if batting_team == 'A' else 'B'} will bat first!\n\n"
            f"Host: Use /bowling <number> to choose first bowler\n"
            f"Example: /bowling 1"
        )
        
        game["status"] = "waiting_bowler"
        pending_bowler_selection[chat_id] = batting_team

    @app.on_message(filters.command("bowling") & filters.group)
    async def bowling_selection_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can choose bowler!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/bowling <number>`\nExample: `/bowling 1`\n\nUse /member_lists to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        # Determine which team is bowling
        batting_team = game.get("current_team") or game.get("batting_first")
        bowling_team = "B" if batting_team == "A" else "A"
        team_key = f"team_{bowling_team.lower()}"
        
        players = game.get(team_key, [])
        if player_num < 1 or player_num > len(players):
            await message.reply(f"❌ Invalid number! Team {bowling_team} has {len(players)} players. Use /member_lists")
            return
        
        selected_bowler = players[player_num - 1].copy()
        game["current_bowler"] = selected_bowler
        game["current_bowler_index"] = player_num - 1
        game["current_bowler_balls"] = 0
        
        bowler_clickable = f"[{selected_bowler['name']}](tg://user?id={selected_bowler['id']})"
        
        await message.reply(f"⚾ Bowler selected: {bowler_clickable}\n\nNow choose batter using /batting <number>")
        
        game["status"] = "waiting_batter"
        pending_batter_selection[chat_id] = batting_team

    @app.on_message(filters.command("batting") & filters.group)
    async def batting_selection_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can choose batter!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Usage: `/batting <number>`\nExample: `/batting 1`\n\nUse /member_lists to see player numbers.")
            return
        
        try:
            player_num = int(args[1])
        except:
            await message.reply("❌ Invalid number!")
            return
        
        batting_team = game.get("current_team") or game.get("batting_first")
        team_key = f"team_{batting_team.lower()}"
        
        players = game.get(team_key, [])
        if player_num < 1 or player_num > len(players):
            await message.reply(f"❌ Invalid number! Team {batting_team} has {len(players)} players.")
            return
        
        selected_batter = players[player_num - 1].copy()
        
        # Check if already selected
        if selected_batter.get("out", False):
            await message.reply(f"❌ {selected_batter['name']} is already OUT!")
            return
        
        # Check if this is first or second batter
        if not game.get("current_batter"):
            # First batter
            game["current_batter"] = selected_batter
            game["current_batter_index"] = player_num - 1
            game["batting_order"] = [player_num - 1]
            
            batter_clickable = f"[{selected_batter['name']}](tg://user?id={selected_batter['id']})"
            await message.reply(f"🏏 First batter selected: {batter_clickable}\n\nChoose second batter using /batting <number>")
            
        elif len(game.get("batting_order", [])) == 1:
            # Second batter
            if player_num - 1 in game["batting_order"]:
                await message.reply("❌ This player already selected as batter!")
                return
            
            game["batting_order"].append(player_num - 1)
            
            batter_clickable = f"[{selected_batter['name']}](tg://user?id={selected_batter['id']})"
            await message.reply(f"🏏 Second batter selected: {batter_clickable}\n\nGet ready, the game is starting in 10 seconds!")
            
            # Start the game
            await asyncio.sleep(3)
            
            game["current_team"] = batting_team
            game["team_total"] = 0
            game["team_wickets"] = 0
            game["total_balls_in_inning"] = 0
            game["bowling_number"] = None
            game["status"] = "playing"
            game["ball_mode"] = 1  # 1 ball per bowler in team mode? aap change kar sakte ho
            
            # Send bowling video
            await send_bowling_video_team(client, chat_id, game["current_bowler"])
        
        else:
            await message.reply("❌ Both batters already selected!")

    async def send_bowling_video_team(client, chat_id, bowler):
        game = team_games.get(chat_id)
        if not game or game.get("status") != "playing":
            return
        
        bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
        
        await client.send_video(
            chat_id,
            BOWLING_VIDEO,
            caption=f"{bowler_clickable} now you can send a number in the bot PM. You have 1 min."
        )
        
        try:
            await client.send_message(
                bowler["id"],
                f"🎯 Send bowling number (1-6):\n\n⏰ You have 60 seconds!"
            )
        except:
            pass
        
        # Set timeout
        if chat_id in bowling_tasks:
            try:
                bowling_tasks[chat_id].cancel()
            except:
                pass
        
        task = asyncio.create_task(bowling_timeout_team(client, chat_id, bowler["id"], bowler["name"]))
        bowling_tasks[chat_id] = task

    async def bowling_timeout_team(client, chat_id, user_id, bowler_name):
        await asyncio.sleep(60)
        game = team_games.get(chat_id)
        if game and game.get("status") == "playing":
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                await client.send_message(chat_id, f"⚠️ No response from {bowler_name}! Host use /swap to change.")
        
        if chat_id in bowling_tasks:
            del bowling_tasks[chat_id]

    async def send_batting_video_team(client, chat_id, batter, bowler_number):
        game = team_games.get(chat_id)
        if not game or game.get("status") != "playing":
            return
        
        ball_mode = game.get("ball_mode", 1)
        batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
        
        await client.send_video(
            chat_id,
            BATTING_VIDEO,
            caption=f"Now Batter: {batter_clickable} can send a number (0-6)\n\nOVER BALLS = {ball_mode}"
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
        
        if text.startswith("/start"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply("❌ Send number 1-6 only!")
        
        num = int(text)
        
        # Check for bowling
        for chat_id, game in team_games.items():
            if game.get("status") != "playing":
                continue
            
            current_bowler = game.get("current_bowler", {})
            if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
                game["bowling_number"] = num
                await message.reply(f"✅ Bowling number {num} sent!")
                
                # Cancel timeout
                if chat_id in bowling_tasks:
                    try:
                        bowling_tasks[chat_id].cancel()
                    except:
                        pass
                    del bowling_tasks[chat_id]
                
                # Send batting video
                batter = game["current_batter"]
                await send_batting_video_team(client, chat_id, batter, num)
                return
        
        # Check for batting
        for chat_id, game in team_games.items():
            if game.get("status") != "playing":
                continue
            
            current_batter = game.get("current_batter", {})
            if current_batter.get("id") == user_id and game.get("bowling_number") is not None:
                bowled_num = game["bowling_number"]
                game["bowling_number"] = None
                
                if num == bowled_num:
                    # OUT
                    await process_out_team(client, chat_id, current_batter)
                else:
                    # Runs
                    await process_runs_team(client, chat_id, current_batter, num)
                
                await message.reply(f"✅ Batting number {num} sent!")
                return
        
        await message.reply("❌ No active game or not your turn!")

    async def process_out_team(client, chat_id, batter):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{game['current_team'].lower()}"
        
        # Mark batter out
        for p in game[team_key]:
            if p["id"] == batter["id"]:
                p["out"] = True
                p["history"].append("W")
                break
        
        game["team_wickets"] += 1
        
        await client.send_message(chat_id, f"❌ **OUT!** {batter['name']} is out!")
        
        # Check if inning over
        active_batters = [p for p in game[team_key] if not p.get("out", False)]
        
        if not active_batters or game["team_wickets"] >= len(game[team_key]):
            # Inning over
            await end_innings_team(client, chat_id)
            return
        
        # Check if next batter is already selected (from batting order)
        batting_order = game.get("batting_order", [])
        current_index = game.get("current_batter_index", 0)
        
        # Find next batter from batting order
        next_index = None
        for idx in batting_order:
            if idx > current_index and not game[team_key][idx].get("out", False):
                next_index = idx
                break
        
        if next_index is None:
            # Find any non-out batter
            for i, p in enumerate(game[team_key]):
                if not p.get("out", False):
                    next_index = i
                    break
        
        if next_index is not None:
            game["current_batter_index"] = next_index
            game["current_batter"] = game[team_key][next_index].copy()
            
            await client.send_message(
                chat_id,
                f"🎯 New batter: [{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})"
            )
            
            # Continue game with same bowler
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
        
        # Check for win in second innings
        if game["current_team"] == "B" and game["team_total"] > game["team_a_score"]:
            await end_match_team(client, chat_id, "B")
            return
        
        # Check if over complete (6 balls)
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
        
        # Find next bowler (not out)
        current_index = game.get("current_bowler_index", 0)
        new_index = (current_index + 1) % len(players)
        
        # Skip if out
        while players[new_index].get("out", False) and new_index != current_index:
            new_index = (new_index + 1) % len(players)
        
        game["current_bowler_index"] = new_index
        game["current_bowler"] = players[new_index].copy()
        game["current_bowler_balls"] = 0
        
        await client.send_message(
            chat_id,
            f"🔄 Over complete! New bowler: [{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})"
        )
        
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    async def end_innings_team(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{game['current_team'].lower()}"
        
        if game["current_team"] == "A":
            game["team_a_score"] = game["team_total"]
            game["team_a_wickets"] = game["team_wickets"]
            
            await client.send_message(
                chat_id,
                f"🏏 **Team A Innings Complete!**\n\n"
                f"Total: {game['team_a_score']}/{game['team_a_wickets']}\n"
                f"Overs: {game['total_balls_in_inning'] // 6}.{game['total_balls_in_inning'] % 6}\n\n"
                f"Team B needs {game['team_a_score'] + 1} runs to win!\n\n"
                f"Host: Use /bowling <number> to choose first bowler for Team B"
            )
            
            # Reset for Team B batting
            game["current_team"] = "B"
            game["current_batter"] = None
            game["current_bowler"] = None
            game["batting_order"] = []
            game["team_total"] = 0
            game["team_wickets"] = 0
            game["total_balls_in_inning"] = 0
            game["bowling_number"] = None
            game["status"] = "waiting_bowler"
            
        else:
            game["team_b_score"] = game["team_total"]
            game["team_b_wickets"] = game["team_wickets"]
            
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
        
        await client.send_message(
            chat_id,
            f"🏆 **Match Over!** 🏆\n\n"
            f"Winner: {winner_name}\n\n"
            f"Team A: {game['team_a_score']}/{game['team_a_wickets']}\n"
            f"Team B: {game['team_b_score']}/{game['team_b_wickets']}\n\n"
            f"📊 {build_team_scoreboard(game)}"
        )
        
        # Cleanup
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        if chat_id in pending_bowler_selection:
            del pending_bowler_selection[chat_id]
        if chat_id in pending_batter_selection:
            del pending_batter_selection[chat_id]

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
        
        # Force end current innings and swap
        await end_innings_team(client, chat_id)

    # ================= SOLO MODE SCORE =================
    @app.on_message(filters.command("score") & filters.group)
    async def score_cmd(client, message: Message):
        await get_live_score(client, message)

    # ================= VOTE SYSTEM =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"Voting in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote", callback_data="vote")]])
        msg = await message.reply("🗳️ **VOTE REQUIRED!** (3 votes needed)\n\n0/3 votes", reply_markup=keyboard)
        
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
            await callback.message.edit_text(f"🗳️ **VOTE REQUIRED!** (3 votes needed)\n\n{vote['count']}/3 votes")
            await callback.answer(f"Voted! ({vote['count']}/3)")

    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote = active_votes.get(chat_id)
        if vote and vote.get("active") and vote["count"] < 3:
            try:
                await client.edit_message_text(chat_id, vote["msg_id"], f"❌ Voting expired! Got {vote['count']}/3 votes.")
            except:
                pass
            vote["active"] = False

    print("🔴 ✅ ALL HANDLERS REGISTERED SUCCESSFULLY!")
