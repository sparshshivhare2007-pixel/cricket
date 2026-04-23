from pyrogram import filters
from pyrogram.types import Message
from solo.game import games

def register_solo_leave(app):

    @app.on_message(filters.command(["solo_leave"], prefixes=["/"]) & filters.group)
    async def solo_leave_cmd(client, message: Message):
        print("🔥 solo_leave command triggered")  # debug

        chat_id = message.chat.id
        user_id = message.from_user.id

        solo_game = games.get(chat_id)
        if not solo_game or solo_game.get("status") != "waiting":
            await message.reply("❌ No active solo game in waiting mode!")
            return

        players = solo_game.get("players", [])

        for i, p in enumerate(players):
            if p["id"] == user_id:
                players.pop(i)

                await message.reply(
                    f"✅ [{message.from_user.first_name}](tg://user?id={user_id}) left the solo game!\n\n"
                    f"👥 Remaining players: {len(players)}",
                    disable_web_page_preview=True
                )
                return

        await message.reply("❌ You are not in the solo game!")
