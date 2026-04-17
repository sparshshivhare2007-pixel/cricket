from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

votes = {}

def register_handlers(app):

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)

        if not game or game["status"] != "playing":
            return

        batter = game.get("current_batter")
        if not batter or message.from_user.id != batter["id"]:
            return

        text = (message.text or "").strip()

        if not text.isdigit():
            return await message.reply(INVALID_NUMBER)

        bat = int(text)
        if bat < 1 or bat > 6:
            return await message.reply(INVALID_NUMBER)

        result = play_ball(chat_id, bat)
        bow = game["bowling_number"]

        # ================= OUT =================
        if result["type"] == "out":
            await message.reply_video(
                OUT_VIDEO_URL,
                caption=OUT_MESSAGE.format(
                    bat=bat,
                    bowler=game["current_bowler"]["name"],
                    bowl=bow
                )
            )

        # ================= RUN =================
        else:
            runs = result["runs"]

            runs_text = f"{runs} run" if runs == 1 else f"{runs} runs"

            await message.reply(
                RUN_MESSAGE.format(
                    batter=batter["name"],
                    runs=runs_text,
                    bat=bat,
                    bowler=game["current_bowler"]["name"],
                    bowl=bow
                )
            )

        await message.reply(build_scoreboard(game["players"]))

        # ================= ROTATION =================
        players = game["players"]

        cur = next((i for i, p in enumerate(players) if p["id"] == batter["id"]), 0)
        nxt = (cur + 1) % len(players)

        game["current_batter"] = players[nxt]
        game["current_bowler"] = players[cur]
        game["bowling_number"] = None

        await message.reply(
            NEXT_TURN_MESSAGE.format(
                batter=game["current_batter"]["name"],
                bowler=game["current_bowler"]["name"]
            )
        )

        await message.reply_video(
            BOWLING_VIDEO_URL,
            caption=BOWLING_MESSAGE.format(
                bowler=game["current_bowler"]["name"]
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Bowling", callback_data="start_bowling")]]
            )
        )
