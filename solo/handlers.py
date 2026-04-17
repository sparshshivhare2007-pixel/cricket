from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard

votes = {}

# ================= AUTO START =================
async def auto_start_game(client, chat_id):
    await asyncio.sleep(JOINING_TIMER_SECONDS)

    game = games.get(chat_id)
    if not game or game["status"] != "waiting":
        return

    players = game["players"]

    if not players:
        return await client.send_message(chat_id, "❌ Not enough players")

    text = "👑 Unknown Host\n\n👤 Players\n\n"
    for i, p in enumerate(players, 1):
        name = f"@{p.get('username')}" if p.get("username") else p["name"]
        text += f"{i}. {name}\n"

    await client.send_message(chat_id, text)

    start_match(chat_id)
    game = games[chat_id]

    await client.send_message(chat_id, "🚀 Game starting...")

    await client.send_video(
        chat_id,
        BOWLING_VIDEO_URL,
        caption=BOWLING_MESSAGE.format(
            bowler=game["current_bowler"]["name"]
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bowling", callback_data="start_bowling")]
        ])
    )


def register_handlers(app):

    # ================= START (GROUP FIXED) =================
    @app.on_message(filters.command("start"))
    async def start(client, message: Message):

        chat = message.chat
        chat_id = chat.id

        # PRIVATE
        if chat.type == "private":
            return await message.reply(
                "👋 Add me in a group to play cricket 🏏"
            )

        # GROUP / SUPERGROUP
        if chat.type in ["group", "supergroup"]:

            create_game(chat_id)
            votes[chat_id] = {"count": 0, "users": []}

            await message.reply(
                "🗳️ Voting Started!\nNeed 3 votes to start game",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Vote 🏏", callback_data="vote_start")]
                ])
            )

    # ================= VOTE =================
    @app.on_callback_query(filters.regex("^vote_start$"))
    async def vote(client, callback):

        chat_id = callback.message.chat.id
        user = callback.from_user

        data = votes.get(chat_id)
        if not data:
            return await callback.answer()

        if user.id in data["users"]:
            return await callback.answer("Already voted ❌", show_alert=True)

        data["users"].append(user.id)
        data["count"] += 1

        voters = "\n".join(
            [f"• {u.first_name}" for u in await asyncio.gather(
                *[client.get_users(uid) for uid in data["users"]]
            )]
        )

        await callback.message.edit_text(
            f"🗳️ Voting\n\nVotes: {data['count']}/3\n\n{voters}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Vote 🏏", callback_data="vote_start")]
            ])
        )

        if data["count"] >= 3:
            await callback.message.edit_text("✅ Game starting...")

            await asyncio.sleep(1)

            await client.send_photo(
                chat_id,
                SOLO_GAME_START_IMAGE,
                caption="🥎 Select Mode",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("1 Ball", callback_data="solo_1")],
                    [InlineKeyboardButton("3 Ball", callback_data="solo_3")]
                ])
            )

    # ================= MODE =================
    @app.on_callback_query(filters.regex("^solo_"))
    async def solo_mode(client, callback):

        chat_id = callback.message.chat.id

        game = games.get(chat_id)
        if game:
            game["mode"] = callback.data

        await callback.message.delete()

        await client.send_message(chat_id, "🎉 Game Started\nUse /joingame")

        asyncio.create_task(auto_start_game(client, chat_id))

    # ================= JOIN =================
    @app.on_message(filters.command("joingame"))
    async def join(client, message: Message):

        chat_id = message.chat.id

        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            await message.reply(
                f"🎉 Joined ({len(game['players'])})"
            )

    # ================= BOWLING BUTTON =================
    @app.on_callback_query(filters.regex("^start_bowling$"))
    async def start_bowling(client, callback):

        chat_id = callback.message.chat.id
        user = callback.from_user

        game = games.get(chat_id)
        if not game:
            return await callback.answer("No game ❌", show_alert=True)

        if game["current_bowler"]["id"] != user.id:
            return await callback.answer("Not your turn ❌", show_alert=True)

        await callback.answer("Check DM 📩", show_alert=True)

        try:
            await client.send_message(
                user.id,
                "🎯 Send number (1-6)"
            )
        except:
            await callback.answer("Open DM first ❌", show_alert=True)

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message: Message):

        user_id = message.from_user.id

        for chat_id, game in games.items():

            if game["status"] != "playing":
                continue

            if game["current_bowler"]["id"] != user_id:
                continue

            text = (message.text or "").strip()

            if not text.isdigit():
                return await message.reply(INVALID_NUMBER)

            num = int(text)
            if num < 1 or num > 6:
                return await message.reply(INVALID_NUMBER)

            set_bowling(chat_id, num)

            await client.send_video(
                chat_id,
                BATTING_VIDEO_URL,
                caption=f"🏏 Batter: {game['current_batter']['name']}\nSend number (1-6)"
            )

    # ================= BATTING (FINAL FIXED) =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting(client, message: Message):

        chat_id = message.chat.id
        game = games.get(chat_id)

        if not game or game["status"] != "playing":
            return

        batter = game.get("current_batter")
        if not batter:
            return

        if message.from_user.id != batter["id"]:
            return

        text = (message.text or "").strip()

        if not text.isdigit():
            return await message.reply(INVALID_NUMBER)

        bat = int(text)

        if bat < 1 or bat > 6:
            return await message.reply(INVALID_NUMBER)

        result = play_ball(chat_id, bat)
        bow = game["bowling_number"]

        runs = result["runs"] if result["type"] != "out" else 0
        runs_text = f"{runs} run" if runs == 1 else f"{runs} runs"

        if result["type"] == "out":
            await message.reply_video(
                OUT_VIDEO_URL,
                caption=OUT_MESSAGE.format(
                    batter=batter["name"],
                    bat=bat,
                    bowler=game["current_bowler"]["name"],
                    bowl=bow
                )
            )
        else:
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

        # ROTATION SAFE
        players = game["players"]

        cur = next((i for i, p in enumerate(players) if p["id"] == batter["id"]), 0)
        nxt = (cur + 1) % len(players)

        game["current_batter"] = players[nxt]
        game["current_bowler"] = players[cur]
        game["bowling_number"] = None

        await message.reply_video(
            BOWLING_VIDEO_URL,
            caption=BOWLING_MESSAGE.format(
                bowler=game["current_bowler"]["name"]
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bowling", callback_data="start_bowling")]
            ])
        )
