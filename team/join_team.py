# team/join_team.py

from pyrogram import filters
from pyrogram.types import Message
from .create_team import team_games, team_hosts, TEAM_SIZE

def register_join_team(app):

    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
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
        
        current = len(game["team_a"])
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A! ({current}/{TEAM_SIZE} players)")
        
        if current >= TEAM_SIZE:
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, f"✅ Team A complete! Join Team B by sending /join_teamB 📣")

    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        
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
        
        current = len(game["team_b"])
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B! ({current}/{TEAM_SIZE} players)")
        
        if current >= TEAM_SIZE:
            game["status"] = "ready"
            await client.send_message(chat_id, f"✅ Teams complete! Type /start_match to begin!")
