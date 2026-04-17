from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from solo.game import *
from solo.scoreboard import build_scoreboard
from config import BOWLING_VIDEO_URL, BATTING_VIDEO_URL, OUT_VIDEO_URL

def register_handlers(app):

    @app.on_message(filters.command("start") & filters.group)
    async def start(client, message: Message):
        create_game(message.chat.id)

        await message.reply(
            "🗳️ Voting Required!\n\nClick to start",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Vote to Start", callback_data="vote_start")]]
            )
        )

    @app.on_callback_query(filters.regex("vote_start"))
    async def vote(client, callback):
        await callback.message.edit("✅ Voting successful!\n\nChoose mode")

    @app.on_message(filters.command("joingame") & filters.group)
    async def join(client, message: Message):
        if join_game(message.chat.id, message.from_user):
            await message.reply(f"🎉 {message.from_user.first_name} joined!")

    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame(client, message: Message):
        start_match(message.chat.id)
        game = games[message.chat.id]

        await message.reply(f"Hey {game['current_batter']['name']}, now you're batter!")
        await message.reply(f"Hey {game['current_bowler']['name']}, now you're bowling!")

        await message.reply_video(
            BOWLING_VIDEO_URL,
            caption=f"{game['current_bowler']['name']} send number in DM",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Bowling", url=f"https://t.me/{client.me.username}")]]
            )
        )

    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message: Message):
        user_id = message.from_user.id

        for chat_id, game in games.items():
            if game["current_bowler"]["id"] == user_id:
                num = int(message.text)
                set_bowling(chat_id, num)

                await client.send_message(
                    chat_id,
                    f"Current batter: {game['current_batter']['name']}\n\nSend Your number:"
                )

    @app.on_message(filters.group & filters.text)
    async def batting(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)

        if not game or game["status"] != "playing":
            return

        if message.from_user.id != game["current_batter"]["id"]:
            return

        bat = int(message.text)
        result = play_ball(chat_id, bat)

        if result["type"] == "out":
            await message.reply_video(OUT_VIDEO_URL, caption="❌ OUT!")
        else:
            await message.reply(f"🏏 {result['runs']} runs!")

        text = build_scoreboard(game["players"])
        await message.reply(text)
