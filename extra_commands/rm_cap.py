from pyrogram import filters
from pyrogram.types import Message
from solo.handlers import team_games, team_hosts

def register_rm_cap(app):
    
    @app.on_message(filters.command("rm_cap") & filters.group)
    async def rm_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        team_game = team_games.get(chat_id)
        if not team_game:
            await message.reply("❌ No active team game found!")
            return
        
        # Check if user is host
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can remove captains!")
            return
        
        # Get captain to remove
        rm_captain = None
        if message.reply_to_message:
            rm_captain = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                rm_captain = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not rm_captain:
            await message.reply("❌ Usage: /rm_cap @username or reply to a user's message")
            return
        
        # Remove captain
        removed = False
        if team_game.get("captain_a", {}).get("id") == rm_captain.id:
            team_game["captain_a"] = None
            removed = True
            team = "A"
        elif team_game.get("captain_b", {}).get("id") == rm_captain.id:
            team_game["captain_b"] = None
            removed = True
            team = "B"
        
        if removed:
            await message.reply(f"✅ {rm_captain.first_name} is no longer Team {team} Captain!")
        else:
            await message.reply(f"❌ {rm_captain.first_name} is not a captain!")