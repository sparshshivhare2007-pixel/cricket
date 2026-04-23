from pyrogram import filters
from pyrogram.types import Message
from solo.game import games
from solo.handlers import team_games, team_hosts

def register_host_change(app):

    @app.on_message(filters.command(["host_change"], prefixes=["/"]) & filters.group)
    async def host_change_cmd(client, message: Message):
        print("🔥 host_change command triggered")  # debug

        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check game modes
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)

        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return

        # Check permissions
        from solo.handlers import is_admin
        is_group_admin = await is_admin(client, chat_id, user_id)

        is_solo_host = False
        is_team_host = False

        if solo_game:
            is_solo_host = user_id == solo_game.get("host_id")

        if team_game:
            host = team_hosts.get(chat_id)
            is_team_host = host and host.get("id") == user_id

        if not (is_group_admin or is_solo_host or is_team_host):
            await message.reply("❌ Only game host or group admin can change host!")
            return

        # Get new host
        new_host = None

        # Reply method
        if message.reply_to_message and message.reply_to_message.from_user:
            new_host = message.reply_to_message.from_user

        # Username method
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_host = await client.get_users(username)
            except Exception as e:
                print("Error fetching user:", e)
                await message.reply(f"❌ User @{username} not found!")
                return

        if not new_host:
            await message.reply("❌ Usage: /host_change @username or reply to a user's message")
            return

        # Apply changes
        responses = []

        if solo_game:
            solo_game["host_id"] = new_host.id
            solo_game["host_name"] = new_host.first_name
            responses.append(
                f"👑 SOLO Host → [{new_host.first_name}](tg://user?id={new_host.id})"
            )

        if team_game:
            team_hosts[chat_id] = {
                "id": new_host.id,
                "name": new_host.first_name,
                "username": new_host.username
            }
            team_game["host_id"] = new_host.id
            team_game["host_name"] = new_host.first_name

            responses.append(
                f"👑 TEAM Host → [{new_host.first_name}](tg://user?id={new_host.id})"
            )

        # Final reply (single message instead of 2 spam)
        await message.reply(
            "✅ Host Updated Successfully!\n\n" + "\n".join(responses),
            disable_web_page_preview=True
        )
