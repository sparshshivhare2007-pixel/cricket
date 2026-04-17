# handlers.py - Complete updated version

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

votes = {}

# Run video mapping function
def get_run_video(runs):
    """Return video URL based on runs scored"""
    run_videos = {
        1: RUN_1_VIDEO_URL,
        2: RUN_2_VIDEO_URL,
        3: RUN_3_VIDEO_URL,
        4: FOUR_VIDEO_URL,
        5: RUN_5_VIDEO_URL,
        6: SIX_VIDEO_URL
    }
    return run_videos.get(runs, RUN_1_VIDEO_URL)

def register_handlers(app):

    # ================= START =================
    @app.on_message(filters.command("start") & filters.group)
    async def start(client, message: Message):
        chat_id = message.chat.id
        create_game(chat_id)
        votes[chat_id] = {"count": 0, "users": []}

        await message.reply(
            "🗳️ Voting in Progress:\n\nCurrent votes: 0/3",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Vote to Start", callback_data="vote_start")]]
            )
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
            f"🗳️ Voting in Progress:\n\n"
            f"Current votes: {data['count']}/3\n"
            f"Voters:\n{voters}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Vote to Start", callback_data="vote_start")]]
            )
        )

        if data["count"] >= 3:
            await callback.message.edit_text("✅ Voting successful! Game starting...")
            await asyncio.sleep(1)

            await client.send_photo(
                chat_id,
                SOLO_GAME_START_IMAGE,
                caption="🥎 Select Mode:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("1 Ball", callback_data="solo_1")],
                    [InlineKeyboardButton("3 Ball", callback_data="solo_3")]
                ])
            )

    # ================= MODE SELECT =================
    @app.on_callback_query(filters.regex("^solo_"))
    async def solo_mode(client, callback):
        chat_id = callback.message.chat.id

        game = games.get(chat_id)
        if game:
            game["mode"] = callback.data

        await callback.message.delete()

        await client.send_message(
            chat_id,
            "🎉 Game created!\n\nJoin using /joingame\n⏰ 2 minutes left"
        )

        asyncio.create_task(auto_start_game(client, chat_id))

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join(client, message: Message):
        chat_id = message.chat.id

        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            await message.reply(
                f"🎉 {message.from_user.first_name} joined! (Player {len(game['players'])})"
            )

    # ================= AUTO START =================
    async def auto_start_game(client, chat_id):
        await asyncio.sleep(JOINING_TIMER_SECONDS)

        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return

        players = game["players"]

        if len(players) < 1:
            await client.send_message(chat_id, "❌ Not enough players to start.")
            return

        text = "👑 Unknown Host\n\n👤 Solo Players\n\n"

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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Bowling", callback_data="start_bowling")]]
            )
        )

    # ================= BOWLING BUTTON =================
    @app.on_callback_query(filters.regex("^start_bowling$"))
    async def start_bowling(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user

        game = games.get(chat_id)
        if not game:
            return await callback.answer("Game not found ❌", show_alert=True)

        if game["current_bowler"]["id"] != user.id:
            return await callback.answer("❌ Not your turn", show_alert=True)

        await callback.answer("Check DM 📩", show_alert=True)

        try:
            await client.send_message(
                user.id,
                "🎯 Bowling Started!\nSend number (1-6)"
            )
        except:
            await callback.answer("Open bot in DM first ❌", show_alert=True)

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
                caption=(
                    f"🏏 Now Batter: {game['current_batter']['name']}\n"
                    "🔥 Send number (1-6) in GROUP"
                )
            )
            
            await message.reply("✅ Bowling number sent to game!")

    # ================= BATTING WITH RUN VIDEOS =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)

        if not game or game["status"] != "playing":
            return

        # Check if bowling number is set
        if game.get("bowling_number") is None:
            await message.reply("⏳ Waiting for bowler to bowl first!")
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

        # Clear bowling number after play
        game["bowling_number"] = None

        # ================= OUT =================
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
            
            # Check if game is over
            if game.get("game_over"):
                await message.reply(
                    f"🏆 Game Over! {game['winner']['name']} wins with {game['winner']['score']} runs!"
                )
                return

        # ================= RUN WITH VIDEO =================
        elif result["type"] == "run":
            runs = result['runs']
            runs_text = f"{runs} run{'s' if runs > 1 else ''}"
            
            # Get the appropriate run video
            run_video_url = get_run_video(runs)
            
            # Send run video
            await message.reply_video(
                run_video_url,
                caption=RUN_MESSAGE.format(
                    batter=batter["name"],
                    runs=runs_text,
                    bat=bat,
                    bowler=game["current_bowler"]["name"],
                    bowl=bow
                )
            )

        # Send scoreboard
        await message.reply(build_scoreboard(game["players"]))

        # Check again if game is over after updating score
        if game.get("game_over"):
            await message.reply(
                f"🏆 Game Over! {game['winner']['name']} wins with {game['winner']['score']} runs!"
            )
            return

        # ================= ROTATE PLAYERS =================
        players = game["players"]
        
        # Find current batter index
        cur_index = None
        for i, player in enumerate(players):
            if player["id"] == batter["id"]:
                cur_index = i
                break
        
        if cur_index is not None:
            # Find next batter who is not out
            next_index = cur_index
            for _ in range(len(players)):
                next_index = (next_index + 1) % len(players)
                if not players[next_index].get("out", False):
                    break
            
            # Update current batter and bowler
            game["current_batter"] = players[next_index].copy()
            
            # Set bowler to previous batter or next player
            bowler_index = (next_index + 1) % len(players)
            game["current_bowler"] = players[bowler_index].copy()

            await message.reply(
                NEXT_TURN_MESSAGE.format(
                    batter=game["current_batter"]["name"],
                    bowler=game["current_bowler"]["name"]
                )
            )

            # Ask next bowler to bowl
            await message.reply_video(
                BOWLING_VIDEO_URL,
                caption=BOWLING_MESSAGE.format(
                    bowler=game["current_bowler"]["name"]
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Bowling", callback_data="start_bowling")]]
                )
            )
