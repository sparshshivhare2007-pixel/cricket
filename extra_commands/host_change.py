from pyrogram import filters
from pyrogram.types import Message
from solo.game import games
from solo.handlers import team_games, team_hosts

def register_host_change(app):
    
    @app.on_message(filters.command("host_change") & filters.group)
    async def host_change_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check solo mode
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        # Check if user is current host/admin
        from solo.handlers import is_admin
        is_group_admin = await is_admin(client, chat_id, user_id)
        
        is_solo_host = False
        is_team_host = False
        
        if solo_game:
            is_solo_host = user_id == solo_game.get("host_id") if solo_game.get("host_id") else False
        
        if team_game:
            host = team_hosts.get(chat_id)
            is_team_host = host and host.get("id") == user_id
        
        if not (is_group_admin or is_solo_host or is_team_host):
            await message.reply("❌ Only game host or group admin can change host!")
            return
        
        # Get new host
        new_host = None
        if message.reply_to_message:
            new_host = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_host = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not new_host:
            await message.reply("❌ Usage: /host_change @username or reply to a user's message")
            return
        
        # Change host
        if solo_game:
            solo_game["host_id"] = new_host.id
            solo_game["host_name"] = new_host.first_name
            await message.reply(f"👑 Host changed to [{new_host.first_name}](tg://user?id={new_host.id}) in SOLO mode!")
        
        if team_game:
            team_hosts[chat_id] = {
                "id": new_host.id,
                "name": new_host.first_name,
                "username": new_host.username
            }
            team_game["host_id"] = new_host.id
            team_game["host_name"] = new_host.first_name
            await message.reply(f"👑 Host changed to [{new_host.first_name}](tg://user?id={new_host.id}) in TEAM mode!")