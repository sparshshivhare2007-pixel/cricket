# team/handlers.py - Simplified Working Version

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import asyncio

team_games = {}
team_hosts = {}
TEAM_SIZE = 11

print("🔴 TEAM HANDLERS LOADED!")

# ================= TEAM MODE START =================
async def team_mode_start(client, callback):
    chat_id = callback.message.chat.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
    ])
    
    caption = """**🏏 TEAM MATCH**

**⭐ New Game Alert! ⭐**

Who will be the game host?

Click below to become the host 🏆"""
    
    await callback.message.delete()
    await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
    await callback.answer()

def register_team_handlers(app):
    print("🔴 REGISTERING TEAM HANDLERS...")

    # ================= TEAM MODE START =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback):
        await team_mode_start(client, callback)

    # ================= BECOME HOST =================
    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_hosts:
            await callback.answer("Host already selected!", show_alert=True)
            return
        
        team_hosts[chat_id] = {"id": user.id, "name": user.first_name, "username": user.username}
        team_games[chat_id] = {
            "host_id": user.id, "host_name": user.first_name, "status": "waiting_host",
            "team_a": [], "team_b": [], "team_a_captain": None, "team_b_captain": None
        }
        
        await callback.message.delete()
        await client.send_message(chat_id, f"👑 {user.first_name} is now the game host! Use /create_team to start!")
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
            f"👥 Need {TEAM_SIZE} players for Team A\n"
            f"⏰ You have 50 seconds to join Team A!"
        )
        
        asyncio.create_task(team_a_timer(client, chat_id))

    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        print(f"🔴 JOIN TEAM A - User: {user.first_name}")
        
        if not game or game["status"] != "team_creation_a":
            await message.reply("❌ Team A is not open for joining!")
            return
        
        if len(game["team_a"]) >= TEAM_SIZE:
            await message.reply(f"❌ Team A is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
            return
        
        game["team_a"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current_count = len(game["team_a"])
        await message.reply(f"✈️ {user.first_name} joined Team A! ({current_count}/{TEAM_SIZE} players)")
        
        if current_count >= TEAM_SIZE:
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, f"✅ Team A complete! Join Team B by sending /join_teamB 📣")

    # ================= TEAM A TIMER =================
    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, f"⏰ Time's up! Join Team B by sending /join_teamB 📣")

    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        print(f"🔴 JOIN TEAM B - User: {user.first_name}")
        
        if not game or game["status"] != "team_creation_b":
            await message.reply("❌ Team B is not open for joining!")
            return
        
        if len(game["team_b"]) >= TEAM_SIZE:
            await message.reply(f"❌ Team B is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
            return
        
        game["team_b"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current_count = len(game["team_b"])
        await message.reply(f"✈️ {user.first_name} joined Team B! ({current_count}/{TEAM_SIZE} players)")
        
        if current_count >= TEAM_SIZE:
            game["status"] = "ready"
            await client.send_message(chat_id, f"✅ Teams complete! Type /start_match to begin!")

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
        
        await message.reply("🚀 Match is starting...")

    # ================= CANCEL =================
    @app.on_message(filters.command("cancel_team") & filters.group)
    async def cancel_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can cancel!")
            return
        
        if chat_id in team_games: del team_games[chat_id]
        if chat_id in team_hosts: del team_hosts[chat_id]
        await message.reply("❌ Team game cancelled!")

    print("🔴 TEAM HANDLERS REGISTERED SUCCESSFULLY!")
