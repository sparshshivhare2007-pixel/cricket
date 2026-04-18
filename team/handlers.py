# team/handlers.py - Final Complete Working Version

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
    
    try:
        await callback.message.delete()
        await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
    except:
        await client.send_message(chat_id, caption, reply_markup=keyboard)
    await callback.answer()

def register_team_handlers(app):
    print("🔴 REGISTERING TEAM HANDLERS...")

    # ================= STEP 1: TEAM MODE START =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback):
        await team_mode_start(client, callback)

    # ================= STEP 2: BECOME HOST =================
    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_hosts:
            await callback.answer("Host already selected!", show_alert=True)
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
            "team_b_captain": None
        }
        
        await callback.message.delete()
        await client.send_message(chat_id, f"👑 [{user.first_name}](tg://user?id={user.id}) is now the game host! Use /create_team to start!")
        await callback.answer()

    # ================= STEP 3: CREATE TEAM COMMAND =================
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
            await message.reply("❌ Teams already created or game in progress!")
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
            await message.reply("❌ Team A is not open for joining right now!")
            return
        
        if user.id in [p["id"] for p in game["team_a"]]:
            await message.reply("❌ You already joined Team A!")
            return
        
        if user.id in [p["id"] for p in game["team_b"]]:
            await message.reply("❌ You already joined Team B!")
            return
        
        if len(game["team_a"]) >= TEAM_SIZE:
            await message.reply(f"❌ Team A is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
            return
        
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
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A! ({current_count}/{TEAM_SIZE} players)")
        
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
            await client.send_message(
                chat_id,
                f"⏰ Time's up for Team A! ({len(game['team_a'])}/{TEAM_SIZE} players joined)\n\n"
                f"🎉 Join Team B by sending /join_teamB 📣\n\n"
                f"👥 Need {TEAM_SIZE} players for Team B\n"
                f"⏰ You have 50 seconds to join Team B!"
            )
            asyncio.create_task(team_b_timer(client, chat_id))

    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        print(f"🔴 JOIN TEAM B - User: {user.first_name}")
        
        if not game or game["status"] != "team_creation_b":
            await message.reply("❌ Team B is not open for joining right now!")
            return
        
        if user.id in [p["id"] for p in game["team_b"]]:
            await message.reply("❌ You already joined Team B!")
            return
        
        if user.id in [p["id"] for p in game["team_a"]]:
            await message.reply("❌ You already joined Team A!")
            return
        
        if len(game["team_b"]) >= TEAM_SIZE:
            await message.reply(f"❌ Team B is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
            return
        
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
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B! ({current_count}/{TEAM_SIZE} players)")
        
        if current_count >= TEAM_SIZE:
            game["status"] = "ready"
            await client.send_message(
                chat_id,
                f"✅ Team B is complete! ({TEAM_SIZE}/{TEAM_SIZE} players)\n\n"
                f"📊 **Final Teams:**\n"
                f"🏏 Team A: {len(game['team_a'])} players\n"
                f"🏏 Team B: {len(game['team_b'])} players\n\n"
                f"🎯 Type /start_match to begin the match!"
            )

    # ================= TEAM B TIMER =================
    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            team_a_count = len(game["team_a"])
            team_b_count = len(game["team_b"])
            
            if team_a_count < TEAM_SIZE or team_b_count < TEAM_SIZE:
                await client.send_message(
                    chat_id,
                    f"⚠️ Time's up!\n\n"
                    f"**Team A:** {team_a_count}/{TEAM_SIZE} players\n"
                    f"**Team B:** {team_b_count}/{TEAM_SIZE} players\n\n"
                    f"❌ Not enough players! Game cancelled."
                )
                if chat_id in team_games:
                    del team_games[chat_id]
                if chat_id in team_hosts:
                    del team_hosts[chat_id]
            else:
                game["status"] = "ready"
                await client.send_message(
                    chat_id,
                    f"✅ Teams are complete!\n\n"
                    f"**Team A:** {team_a_count}/{TEAM_SIZE} players\n"
                    f"**Team B:** {team_b_count}/{TEAM_SIZE} players\n\n"
                    f"🎯 Type /start_match to begin the match!"
                )

    # ================= MEMBER LIST COMMAND =================
    @app.on_message(filters.command("member_list") & filters.group)
    async def member_list_cmd(client, message):
        chat_id = message.chat.id
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game:
            await message.reply("❌ No active team game!")
            return
        
        host_name = host.get("name", "Unknown") if host else "Unknown"
        
        team_a_list = "\n".join([f"{i+1}. [{p['name']}](tg://user?id={p['id']})" for i, p in enumerate(game.get("team_a", []))]) or "No players"
        team_b_list = "\n".join([f"{i+1}. [{p['name']}](tg://user?id={p['id']})" for i, p in enumerate(game.get("team_b", []))]) or "No players"
        
        text = f"👑 **Game Host:** [{host_name}](tg://user?id={host['id']})\n\n"
        text += f"🔵 **Team A ({len(game['team_a'])}/{TEAM_SIZE}):**\n{team_a_list}\n\n"
        text += f"🔴 **Team B ({len(game['team_b'])}/{TEAM_SIZE}):**\n{team_b_list}\n"
        
        await message.reply(text)

    # ================= START MATCH COMMAND =================
    @app.on_message(filters.command("start_match") & filters.group)
    async def start_match_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only the game host can start the match!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "ready":
            await message.reply("❌ Teams are not ready yet! Make sure both teams have 11 players.")
            return
        
        await message.reply("🚀 Match is starting...")

    # ================= CANCEL TEAM =================
    @app.on_message(filters.command("cancel_team") & filters.group)
    async def cancel_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only the host can cancel the game!")
            return
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        await message.reply("❌ Team game cancelled!")

    print("🔴 TEAM HANDLERS REGISTERED SUCCESSFULLY!")
