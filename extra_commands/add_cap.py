from pyrogram import filters
from pyrogram.types import Message
from team.handlers import team_games, team_hosts

def register_add_cap(app):
    
    @app.on_message(filters.command("add_cap") & filters.group)
    async def add_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        team_game = team_games.get(chat_id)
        if not team_game:
            await message.reply("❌ No active team game found!")
            return
        
        # Check if user is host
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can add captains!")
            return
        
        # Get captain to add
        new_captain = None
        if message.reply_to_message:
            new_captain = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_captain = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not new_captain:
            await message.reply("❌ Usage: /add_cap @username or reply to a user's message")
            return
        
        # Determine which team the user is in
        team = None
        for player in team_game["team_a"]:
            if player["id"] == new_captain.id:
                team = "A"
                break
        for player in team_game["team_b"]:
            if player["id"] == new
