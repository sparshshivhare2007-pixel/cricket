from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

votes = {}

def register_handlers(app):

    # ================= START =================
    @app.on_message(filters.command("start") & filters.group)
    async def start(client, message: Message):
        chat_id = message.chat.id

        create_game(chat_id)

        votes[chat_id] = {
            "count": 0,
            "users": []
        }

        await message.reply(
            """🗳️ Voting in Progress:

Current votes: 0/3

Click 'Vote to Start' to participate!
""",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Vote to Start", callback_data="vote_start")]]
            )
        )

    # ================= VOTE =================
    @app.on_callback_query(filters.regex("vote_start"))
    async def vote(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user

        data = votes.get(chat_id)

        if user.id in data["users"]:
            return await callback.answer("Already voted ❌", show_alert=True)

        data["users"].append(user.id)
        data["count"] += 1

        voters = ""
        for uid in data["users"]:
            u = await client.get_users(uid)
            voters += f"\n{u.first_name}"

        text = f"""🗳️ Voting in Progress:

Current votes: {data['count']}/3
Voters:{voters}

Click 'Vote to Start' to participate!
"""

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Vote to Start", callback_data="vote_start")]]
            )
        )

        # ===== VOTE COMPLETE =====
        if data["count"] >= 3:
            await callback.answer("Voting completed ✅")

            await callback.message.edit_text(
                "✅ Voting successful! The game will start shortly."
            )

            await asyncio.sleep(0.5)

            await client.send_photo(
                chat_id,
                SOLO_GAME_START_IMAGE,
                caption="🥎 Select number of balls:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("1 Ball", callback_data="solo_1")],
                    [InlineKeyboardButton("3 Ball", callback_data="solo_3")]
                ])
            )

    # ================= MODE SELECT =================
    @app.on_callback_query(filters.regex("solo_"))
    async def solo_mode(client, callback):
        chat_id = callback.message.chat.id

        game = games.get(chat_id)
        if game:
            game["mode"] = "1 Ball" if callback.data == "solo_1" else "3 Ball"

        await callback.message.delete()

        await client.send_message(
            chat_id,
            """🎉 Game created!

Join the game using /joingame
(2 minutes to join) ⏰"""
        )

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join(client, message: Message):
        chat_id = message.chat.id

        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            player_no = len(game["players"])

            await message.reply(
                f"🎉 {message.from_user.first_name}, you've joined the game! (Player {player_no}) 👍"
            )

    # ================= START GAME =================
    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame(client, message: Message):
        chat_id = message.chat.id
        start_match(chat_id)

        game = games[chat_id]

        await message.reply(GAME_STARTING_MESSAGE)

        await message.reply(f"Hey {game['current_batter']['name']}, now you're batter!")
        await message.reply(f"Hey {game['current_bowler']['name']}, now you're bowling!")

        await message.reply_video(
            BOWLING_VIDEO_URL,
            caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Bowling", url=f"https://t.me/{client.me.username}")]]
            )
        )

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message: Message):
        user_id = message.from_user.id

        for chat_id, game in games.items():
            if game["status"] != "playing":
                continue

            if game["current_bowler"]["id"] == user_id:
                if not message.text.isdigit():
                    return await message.reply(INVALID_NUMBER)

                num = int(message.text)
                if num < 1 or num > 6:
                    return await message.reply(INVALID_NUMBER)

                set_bowling(chat_id, num)

                await client.send_message(
                    chat_id,
                    CURRENT_BATTER_MESSAGE.format(
                        batter=game["current_batter"]["name"]
                    )
                )

                await client.send_video(chat_id, BATTING_VIDEO_URL)

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text)
    async def batting(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)

        if not game or game["status"] != "playing":
            return

        if message.from_user.id != game["current_batter"]["id"]:
            return

        if not message.text.isdigit():
            return await message.reply(INVALID_NUMBER)

        bat = int(message.text)
        if bat < 1 or bat > 6:
            return await message.reply(INVALID_NUMBER)

        result = play_ball(chat_id, bat)

        bow = game["bowling_number"]
        batter = game["current_batter"]["name"]
        bowler = game["current_bowler"]["name"]

        if result["type"] == "out":
            await message.reply_video(
                OUT_VIDEO_URL,
                caption=OUT_MESSAGE.format(
                    batter=batter,
                    bat=bat,
                    bowler=bowler,
                    bowl=bow
                )
            )
        else:
            runs = result["runs"]

            video = None
            if runs == 6 and SIX_VIDEO_URL:
                video = SIX_VIDEO_URL
            elif runs == 4 and FOUR_VIDEO_URL:
                video = FOUR_VIDEO_URL
            elif runs == 3 and RUN_3_VIDEO_URL:
                video = RUN_3_VIDEO_URL
            elif runs == 2 and RUN_2_VIDEO_URL:
                video = RUN_2_VIDEO_URL
            elif runs == 1 and RUN_1_VIDEO_URL:
                video = RUN_1_VIDEO_URL

            caption = RUN_MESSAGE.format(
                batter=batter,
                runs=runs,
                bat=bat,
                bowler=bowler,
                bowl=bow
            )

            if video:
                await message.reply_video(video, caption=caption)
            else:
                await message.reply(caption)

        scoreboard = build_scoreboard(game["players"])
        await message.reply(scoreboard)

        players = game["players"]
        current_index = players.index(game["current_batter"])
        next_index = (current_index + 1) % len(players)

        game["current_batter"] = players[next_index]
        game["current_bowler"] = players[current_index]
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
                [[InlineKeyboardButton("Bowling", url=f"https://t.me/{client.me.username}")]]
            )
        )
