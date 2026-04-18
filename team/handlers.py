# team/handlers.py - Final Complete Version

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

# ================= TEAM MODE START FUNCTION (called from solo) =================
async def team_mode_start(client, callback):
    """Team mode start function - called from solo mode"""
    chat_id = callback.message.chat.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
    ])
    
    caption = """**🏏 SOLO TREE COMMUNITY**

**🎯 TEAM MATCH**

**✨ New Game Alert! ✨**

Who will be the game host for this match? 🤔

Click below to become the host 👇"""
    
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

    # ================= STEP 1: TEAM MODE START (direct) =================
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
        
        # Delete old message and send new one
        await callback.message.delete()
        
        caption = f"[{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏"
        
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
        
        await message.reply(f"🎉 {user.first_name} joined Team A! ({current_count}/{TEAM_SIZE} players)")
        
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
                f"🎉 Join Team B by sending /join_teamB 📣\n\n"
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
        
        await message.reply(f"🎉 {user.first_name} joined Team B! ({current_count}/{TEAM_SIZE} players)")
        
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
            game["status"] = "ready"
            
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
                await client.send_message(
                    chat_id,
                    f"✅ Teams are complete!\n\n"
                    f"**Team A:** {team_a_count}/{TEAM_SIZE} players\n"
                    f"**Team B:** {team_b_count}/{TEAM_SIZE} players\n\n"
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
        
        batting_team = game.get("current_team", "None")
        innings = game.get("innings", "None")
        
        # Team A players with @username
        team_a_players = []
        for p in game.get("team_a", []):
            if p.get("username"):
                team_a_players.append(f"{len(team_a_players)+1}. @{p['username']}")
            else:
                team_a_players.append(f"{len(team_a_players)+1}. {p['name']}")
        
        # Team B players with @username
        team_b_players = []
        for p in game.get("team_b", []):
            if p.get("username"):
                team_b_players.append(f"{len(team_b_players)+1}. @{p['username']}")
            else:
                team_b_players.append(f"{len(team_b_players)+1}. {p['name']}")
        
        # Captains
        team_a_captain = game.get("team_a_captain", "Not selected yet")
        team_b_captain = game.get("team_b_captain", "Not selected yet")
        
        if team_a_captain and team_a_captain != "Not selected yet":
            team_a_captain_name = f"@{team_a_captain}" if not team_a_captain.startswith("@") else team_a_captain
        else:
            team_a_captain_name = "Not selected yet"
        
        if team_b_captain and team_b_captain != "Not selected yet":
            team_b_captain_name = f"@{team_b_captain}" if not team_b_captain.startswith("@") else team_b_captain
        else:
            team_b_captain_name = "Not selected yet"
        
        # Build output
        text = f"👽 **Game Host:** {host_name}\n\n"
        text += f"🏏 **Batting:** Team {batting_team} (Innings {innings})\n"
        
        if batting_team == "A":
            text += f"🎯 **Bowling:** Team B\n\n"
        elif batting_team == "B":
            text += f"🎯 **Bowling:** Team A\n\n"
        else:
            text += f"🎯 **Bowling:** Team None\n\n"
        
        text += f"🎩 **Team A Captain:** {team_a_captain_name}\n"
        text += f"👒 **Team B Captain:** {team_b_captain_name}\n\n"
        
        text += f"🔵 **Team A Players ({len(team_a_players)}/{TEAM_SIZE}):**\n"
        if team_a_players:
            text += "\n".join(team_a_players) + "\n"
        else:
            text += "(No players joined yet)\n"
        
        text += f"\n🔴 **Team B Players ({len(team_b_players)}/{TEAM_SIZE}):**\n"
        if team_b_players:
            text += "\n".join(team_b_players) + "\n"
        else:
            text += "(No players joined yet)\n"
        
        await message.reply(text)

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
            return await message.reply("❌ Teams are not ready yet! Wait for both teams to complete.")
        
        if len(game["team_a"]) < TEAM_SIZE:
            return await message.reply(f"❌ Team A needs {TEAM_SIZE - len(game['team_a'])} more players!")
        
        if len(game["team_b"]) < TEAM_SIZE:
            return await message.reply(f"❌ Team B needs {TEAM_SIZE - len(game['team_b'])} more players!")
        
        await message.reply("🚀 Match is starting...")
        # Here you can add the match start logic (similar to solo mode but for teams)

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
