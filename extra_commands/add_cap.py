from pyrogram import filters
from pyrogram.types import Message
from solo.handlers import team_games, team_hosts

def register_add_cap(app):

    @app.on_message(filters.command(["add_cap"], prefixes=["/"]) & filters.group)
    async def add_cap_cmd(client, message: Message):
        print("🔥 add_cap command triggered")  # debug

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

        # Reply method
        if message.reply_to_message and message.reply_to_message.from_user:
            new_captain = message.reply_to_message.from_user

        # Username method
        elif len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_captain = await client.get_users(username)
            except Exception as e:
                print("Error fetching user:", e)
                await message.reply(f"❌ User @{username} not found!")
                return

        if not new_captain:
            await message.reply("❌ Usage: /add_cap @username or reply to a user's message")
            return

        # Determine which team the user is in
        team = None

        for player in team_game.get("team_a", []):
            if player["id"] == new_captain.id:
                team = "A"
                break

        if not team:
            for player in team_game.get("team_b", []):
                if player["id"] == new_captain.id:
                    team = "B"
                    break

        if not team:
            await message.reply(f"❌ {new_captain.first_name} is not in any team!")
            return

        # Check if captain already exists
        if team == "A" and team_game.get("captain_a"):
            await message.reply("❌ Team A already has a captain! Use /cap_change to change.")
            return

        if team == "B" and team_game.get("captain_b"):
            await message.reply("❌ Team B already has a captain! Use /cap_change to change.")
            return

        # Add captain
        captain_data = {
            "id": new_captain.id,
            "name": new_captain.first_name,
            "username": new_captain.username
        }

        if team == "A":
            team_game["captain_a"] = captain_data
        else:
            team_game["captain_b"] = captain_data

        await message.reply(f"✅ {new_captain.first_name} is now Team {team} Captain!")
