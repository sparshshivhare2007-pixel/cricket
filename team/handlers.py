# team/handlers.py - Team Mode with 11 Players per Team

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
import asyncio

team_games = {}
team_hosts = {}

TEAM_SIZE = 11  # 11 players per team

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

def register_team_handlers(app):

    # ================= TEAM MODE START =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
        ])
        
        caption = """**🏏 SOLO TREE COMMUNITY**

**🎯 TEAM MATCH**

**✨ New Game Alert! ✨**

Who will be the game host for this match? 🤔

Click below to become the host 👇"""
        
        await callback.message.delete()
        
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

    # ================= BECOME HOST =================
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
            "status": "waiting_host",
            "team_a": [],
            "team_b": [],
            "current_team": None,
            "join_started": False
        }
        
        caption = f"[{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏"
        
        await callback.message.edit_caption(
            caption=caption,
            disable_web_page_preview=True
        )
        await callback.answer()

    # ================= CREATE TEAM COMMAND =================
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
        if not game:
            return await message.reply("❌ No active game!")
        
        if game["status"] != "waiting_host":
            return await message.reply("❌ Teams already created!")
        
        game["status"] = "team_creation_a"
        game["join_started"] = True
        
        await message.reply(
            f"🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n"
            f"👥 Need {TEAM_SIZE} players for Team A\n"
            f"⏰ You have 2 minutes to join Team A!"
        )
        
        # Start timer for Team A (2 minutes = 120 seconds)
        asyncio.create_task(team_a_timer(client, chat_id))

    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
        if not game or game["status"] != "team_creation_a":
            return await message.reply("❌ Team A is not open for joining right now!")
        
        if len(game["team_a"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team A is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
        
        if user.id in [p["id"] for p in game["team_a"]] or user.id in [p["id"] for p in game["team_b"]]:
            return await message.reply("❌ You already joined a team!")
        
        game["team_a"].append({
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "score": 0,
            "balls": 0,
            "out": False,
            "history": []
        })
        
        current_count = len(game["team_a"])
        remaining = TEAM_SIZE - current_count
        
        await message.reply(f"🎉 {user.first_name} joined Team A! ({current_count}/{TEAM_SIZE} players)")
        
        # Check if Team A is complete
        if current_count >= TEAM_SIZE:
            game["status"] = "team_creation_b"
            await client.send_message(
                chat_id,
                f"✅ Team A is complete! ({TEAM_SIZE}/{TEAM_SIZE} players)\n\n"
                f"🎉 Join Team B by sending /join_teamB 📣\n\n"
                f"👥 Need {TEAM_SIZE} players for Team B\n"
                f"⏰ You have 2 minutes to join Team B!"
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
        
        if len(game["team_b"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team B is full! ({TEAM_SIZE}/{TEAM_SIZE} players)")
        
        if user.id in [p["id"] for p in game["team_a"]] or user.id in [p["id"] for p in game["team_b"]]:
            return await message.reply("❌ You already joined a team!")
        
        game["team_b"].append({
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "score": 0,
            "balls": 0,
            "out": False,
            "history": []
        })
        
        current_count = len(game["team_b"])
        remaining = TEAM_SIZE - current_count
        
        await message.reply(f"🎉 {user.first_name} joined Team B! ({current_count}/{TEAM_SIZE} players)")
        
        # Check if Team B is complete
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

    # ================= TEAM A TIMER =================
    async def team_a_timer(client, chat_id):
        await asyncio.sleep(120)  # 2 minutes
        
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            if len(game["team_a"]) >= TEAM_SIZE:
                # Already full, timer not needed
                return
            
            game["status"] = "team_creation_b"
            
            await client.send_message(
                chat_id,
                f"⏰ Time's up for Team A! ({len(game['team_a'])}/{TEAM_SIZE} players joined)\n\n"
                f"🎉 Join Team B by sending /join_teamB 📣\n\n"
                f"👥 Need {TEAM_SIZE} players for Team B\n"
                f"⏰ You have 2 minutes to join Team B!"
            )
            
            asyncio.create_task(team_b_timer(client, chat_id))

    # ================= TEAM B TIMER =================
    async def team_b_timer(client, chat_id):
        await asyncio.sleep(120)  # 2 minutes
        
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
        await start_team_match(client, chat_id)

    # ================= START TEAM MATCH =================
    async def start_team_match(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        game["status"] = "playing"
        game["current_innings"] = 1
        game["target"] = None
        game["team_a_total"] = 0
        game["team_b_total"] = 0
        
        team_a = game["team_a"]
        team_b = game["team_b"]
        
        team_a_names = "\n".join([f"• {p['name']}" for p in team_a])
        team_b_names = "\n".join([f"• {p['name']}" for p in team_b])
        
        await client.send_message(
            chat_id,
            f"**🏏 MATCH STARTED!** 🏏\n\n"
            f"**Team A ({len(team_a)} players):**\n{team_a_names}\n\n"
            f"**Team B ({len(team_b)} players):**\n{team_b_names}\n\n"
            f"⚾ **Team A will bat first!**"
        )
        
        await start_team_batting(client, chat_id, "A")

    # ================= START TEAM BATTING =================
    async def start_team_batting(client, chat_id, team):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{team.lower()}"
        team_players = game[team_key]
        
        if not team_players:
            await client.send_message(chat_id, f"❌ Team {team} has no players!")
            return
        
        for p in team_players:
            p["score"] = 0
            p["balls"] = 0
            p["out"] = False
            p["history"] = []
        
        game["current_batter_index"] = 0
        game["current_batter"] = team_players[0].copy()
        game["current_bowler_index"] = 1 if len(team_players) > 1 else 0
        game["current_bowler"] = team_players[game["current_bowler_index"]].copy()
        game["current_bowler_balls"] = 0
        game["bowling_number"] = None
        game["current_team"] = team
        game["team_total"] = 0
        
        await client.send_message(
            chat_id,
            f"**🏏 Team {team} Batting** 🏏\n\n"
            f"Batter: [{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})\n"
            f"Bowler: [{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})\n\n"
            f"⚾ Get ready!"
        )
        
        await send_team_bowling_video(client, chat_id, game["current_bowler"])

    # ================= SEND TEAM BOWLING VIDEO =================
    async def send_team_bowling_video(client, chat_id, bowler):
        game = team_games.get(chat_id)
        if not game or game["status"] != "playing":
            return
        
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
