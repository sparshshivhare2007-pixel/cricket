# team/handlers.py - Complete Flow

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
import asyncio

team_games = {}
team_hosts = {}

TEAM_SIZE = 11

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ================= TEAM MODE START FUNCTION =================
async def team_mode_start(client, callback):
    chat_id = callback.message.chat.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
    ])
    
    caption = """**🏏 SOLO TREE COMMUNITY**

**🔴 TEAM MATCH**

**⭐ New Game Alert! ⭐**

Who will be the game host for this match? 😉

Click below to become the host 🏆"""
    
    try:
        await client.send_photo(
            chat_id,
            TEAM_PLAY_IMG,
            caption=caption,
            reply_markup=keyboard
        )
    except:
        await client.send_message(
            chat_id,
            caption,
            reply_markup=keyboard
        )
    await callback.answer()

def register_team_handlers(app):

    # ================= STEP 1: TEAM MODE START =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback: CallbackQuery):
        await team_mode_start(client, callback)

    # ================= STEP 2: BECOME HOST =================
    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_hosts:
            await callback.answer(f"Host already selected! {team_hosts[chat_id]['name']} is the host.", show_alert=True)
            return
        
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
            "team_a_captain": None,
            "team_b_captain": None,
            "current_team": None,
            "innings": None
        }
        
        await callback.message.delete()
        
        caption = f"👑 [{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏"
        
        await client.send_message(
            chat_id,
            caption,
            disable_web_page_preview=True
        )
        await callback.answer()

    # ================= STEP 3: CREATE TEAM COMMAND =================
    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host:
            return await message.reply("❌ No game host found! Start team mode first.")
        
        if host["id"] != user_id:
            return await message.reply("❌ Only the game host can create teams!")
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "waiting_host":
            return await message.reply("❌ Teams already created or game in progress!")
        
        game["status"] = "team_creation_a"
        
        await message.reply(
            f"🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n"
            f"👥 Need {TEAM_SIZE} players for Team A\n"
            f"⏰ You have 50 seconds to join Team A!"
        )
        
        asyncio.create_task(team_a_timer(client, chat_id))

    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        if not game or game["status"] != "team_creation_a":
            return await message.reply("❌ Team A is not open for joining right now!")
        
        if user.id in [p["id"] for p in game["team_a"]]:
            return await message.reply("❌ You already joined Team A!")
        
        if user.id in [p["id"] for p in game["team_b"]]:
            return await message.reply("❌ You already joined Team B!")
        
        if len(game["team_a"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team A is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
        
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
        
        current_count = len(game["team_a"])
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A! ({current_count}/{TEAM_SIZE} players)", disable_web_page_preview=True)
        
        if current_count >= TEAM_SIZE:
            game["status"] = "team_creation_b"
            await client.send_message(
                chat_id,
                f"✅ Team A is complete! ({TEAM_SIZE}/{TEAM_SIZE} players)\n\n"
                f"🎉 Join Team B by sending /join_teamB 📣\n\n"
                f"👥 Need {TEAM_SIZE} players for Team B\n"
                f"⏰ You have 50 seconds to join Team B!"
            )
            asyncio.create_task(team_b_timer(client, chat_id))

    # ================= TEAM A TIMER =================
    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            
            team_a_count = len(game["team_a"])
            
            await client.send_message(
                chat_id,
                f"⏰ Time's up for Team A! ({team_a_count}/{TEAM_SIZE} players joined)\n\n"
                f"👥 Join Team B by sending /join_teamB 📣\n\n"
                f"👥 Need {TEAM_SIZE} players for Team B\n"
                f"⏰ You have 50 seconds to join Team B!"
            )
            asyncio.create_task(team_b_timer(client, chat_id))

    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        if not game or game["status"] != "team_creation_b":
            return await message.reply("❌ Team B is not open for joining right now!")
        
        if user.id in [p["id"] for p in game["team_b"]]:
            return await message.reply("❌ You already joined Team B!")
        
        if user.id in [p["id"] for p in game["team_a"]]:
            return await message.reply("❌ You already joined Team A!")
        
        if len(game["team_b"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team B is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
        
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
        
        current_count = len(game["team_b"])
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B! ({current_count}/{TEAM_SIZE} players)", disable_web_page_preview=True)

    # ================= TEAM B TIMER =================
    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            game["status"] = "captain_selection"
            
            team_a_count = len(game["team_a"])
            team_b_count = len(game["team_b"])
            
            await client.send_message(
                chat_id,
                f"👋 Hey, now members are joined the teams! 🎉\n\n"
                f"**Team A:** {team_a_count}/{TEAM_SIZE} players\n"
                f"**Team B:** {team_b_count}/{TEAM_SIZE} players\n\n"
                f"📝 Choose Team captains user /choose_cap 📝"
            )

    # ================= CHOOSE CAPTAIN COMMAND =================
    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "captain_selection":
            return await message.reply("❌ Captain selection is not open right now!")
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            return await message.reply("❌ Only the game host can select captains!")
        
        # Create team A player buttons
        team_a_buttons = []
        for player in game["team_a"]:
            team_a_buttons.append([InlineKeyboardButton(f"👤 {player['name']}", callback_data=f"cap_a_{player['id']}")])
        
        # Create team B player buttons
        team_b_buttons = []
        for player in game["team_b"]:
            team_b_buttons.append([InlineKeyboardButton(f"👤 {player['name']}", callback_data=f"cap_b_{player['id']}")])
        
        # Send captain selection message
        await client.send_message(
            chat_id,
            f"🏅 **Select Team A Captain**\n\n",
            reply_markup=InlineKeyboardMarkup(team_a_buttons)
        )
        await asyncio.sleep(1)
        await client.send_message(
            chat_id,
            f"🏅 **Select Team B Captain**\n\n",
            reply_markup=InlineKeyboardMarkup(team_b_buttons)
        )

    # ================= CAPTAIN SELECTION CALLBACK =================
    @app.on_callback_query(filters.regex("^cap_a_"))
    async def select_captain_a(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        player_id = int(callback.data.split("_")[2])
        
        game = team_games.get(chat_id)
        if not game:
            return await callback.answer("Game not found!", show_alert=True)
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            return await callback.answer("Only host can select captain!", show_alert=True)
        
        for player in game["team_a"]:
            if player["id"] == player_id:
                game["team_a_captain"] = player["username"] or player["name"]
                await callback.answer(f"✅ Team A Captain: {player['name']}")
                await callback.message.delete()
                break
        
        # Check if both captains selected
        if game["team_a_captain"] and game["team_b_captain"]:
            game["status"] = "ready"
            await client.send_message(
                chat_id,
                f"✅ **Captains Selected!**\n\n"
                f"🏅 Team A Captain: @{game['team_a_captain']}\n"
                f"🏅 Team B Captain: @{game['team_b_captain']}\n\n"
                f"🎯 Type /start_match to begin the match!"
            )

    @app.on_callback_query(filters.regex("^cap_b_"))
    async def select_captain_b(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        player_id = int(callback.data.split("_")[2])
        
        game = team_games.get(chat_id)
        if not game:
            return await callback.answer("Game not found!", show_alert=True)
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            return await callback.answer("Only host can select captain!", show_alert=True)
        
        for player in game["team_b"]:
            if player["id"] == player_id:
                game["team_b_captain"] = player["username"] or player["name"]
                await callback.answer(f"✅ Team B Captain: {player['name']}")
                await callback.message.delete()
                break
        
        if game["team_a_captain"] and game["team_b_captain"]:
            game["status"] = "ready"
            await client.send_message(
                chat_id,
                f"✅ **Captains Selected!**\n\n"
                f"🏅 Team A Captain: @{game['team_a_captain']}\n"
                f"🏅 Team B Captain: @{game['team_b_captain']}\n\n"
                f"🎯 Type /start_match to begin the match!"
            )

    # ================= MEMBER LIST COMMAND =================
    @app.on_message(filters.command("member_list") & filters.group)
    async def member_list_cmd(client, message: Message):
        chat_id = message.chat.id
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game:
            return await message.reply("❌ No active team game!")
        
        host_name = host.get("name", "Unknown") if host else "Unknown"
        
        team_a_players = []
        for p in game.get("team_a", []):
            team_a_players.append(f"{len(team_a_players)+1}. [{p['name']}](tg://user?id={p['id']})")
        
        team_b_players = []
        for p in game.get("team_b", []):
            team_b_players.append(f"{len(team_b_players)+1}. [{p['name']}](tg://user?id={p['id']})")
        
        team_a_captain = game.get("team_a_captain", "Not selected yet")
        team_b_captain = game.get("team_b_captain", "Not selected yet")
        
        text = f"👑 **Game Host:** [{host_name}](tg://user?id={host['id']})\n\n" if host else ""
        text += f"🎩 **Team A Captain:** {team_a_captain}\n"
        text += f"👒 **Team B Captain:** {team_b_captain}\n\n"
        
        text += f"🔵 **Team A Players ({len(team_a_players)}/{TEAM_SIZE}):**\n"
        text += "\n".join(team_a_players) if team_a_players else "(No players joined yet)"
        
        text += f"\n\n🔴 **Team B Players ({len(team_b_players)}/{TEAM_SIZE}):**\n"
        text += "\n".join(team_b_players) if team_b_players else "(No players joined yet)"
        
        await message.reply(text, disable_web_page_preview=True)

    # ================= START MATCH COMMAND =================
    @app.on_message(filters.command("start_match") & filters.group)
    async def start_match_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            return await message.reply("❌ Only the game host can start the match!")
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "ready":
            return await message.reply("❌ Teams are not ready yet! Complete captain selection first.")
        
        await message.reply("🚀 Match is starting...")

    # ================= CANCEL TEAM =================
    @app.on_message(filters.command("cancel_team") & filters.group)
    async def cancel_team_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            return await message.reply("❌ Only the host can cancel the game!")
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        await message.reply("❌ Team game cancelled!")
