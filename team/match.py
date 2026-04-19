# team/match.py

from pyrogram import filters
from pyrogram.types import Message
from .create_team import team_games, team_hosts

def register_match(app):

    @app.on_message(filters.command("member_list") & filters.group)
    async def member_list_cmd(client, message):
        chat_id = message.chat.id
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game:
            await message.reply("❌ No active team game!")
            return
        
        team_a_list = "\n".join([f"{i+1}. [{p['name']}](tg://user?id={p['id']})" for i, p in enumerate(game.get("team_a", []))]) or "No players"
        team_b_list = "\n".join([f"{i+1}. [{p['name']}](tg://user?id={p['id']})" for i, p in enumerate(game.get("team_b", []))]) or "No players"
        
        text = f"👑 **Host:** {host['name'] if host else 'Unknown'}\n\n"
        text += f"🔵 **Team A ({len(game['team_a'])}/11):**\n{team_a_list}\n\n"
        text += f"🔴 **Team B ({len(game['team_b'])}/11):**\n{team_b_list}\n"
        
        await message.reply(text)

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
            await message.reply("❌ Teams not ready! Need 11 players each.")
            return
        
        await message.reply("🚀 Match is starting...")

    @app.on_message(filters.command("cancel_team") & filters.group)
    async def cancel_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can cancel!")
            return
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        await message.reply("❌ Team game cancelled!")
