# handlers.py - Final Complete Working Version

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

active_votes = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def bowling_timeout(client, chat_id, user_id):
    await asyncio.sleep(60)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            await client.send_message(user_id, "⏰ Time's up! You took too long to bowl.")

def register_handlers(app):

    # ================= START =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if await is_admin(client, chat_id, user_id):
            await select_game_menu(client, message)
        else:
            await vote_system(client, message)

    # ================= START DM =================
    @app.on_message(filters.command("start") & filters.private)
    async def start_dm(client, message: Message):
        user_id = message.from_user.id
        
        # Check if user is a bowler in any active game
        for chat_id, game in games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply(
                        "🎯 **Send bowling number (1-6)**\n\n"
                        "Example: `4`\n\n"
                        "⏰ You have 60 seconds!"
                    )
                    asyncio.create_task(bowling_timeout(client, chat_id, user_id))
                    return
        
        # Normal welcome message
        await message.reply(
            "🏏 **Welcome to Cricket Game Bot!**\n\n"
            "Use me in a group to play cricket games.\n"
            "Add me to a group and use /start there!\n\n"
            "**Commands:**\n"
            "/start - Start game (Admin) or Vote (Member)\n"
            "/joingame - Join an existing game"
        )

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤Solo", callback_data="mode_solo"), InlineKeyboardButton("👥Team", callback_data="mode_team")],
            [InlineKeyboardButton("⭐️Start Auction", callback_data="mode_auction"), InlineKeyboardButton("🏆Tournament Mode", callback_data="mode_tournament")],
            [InlineKeyboardButton("Cancel", callback_data="mode_cancel")]
        ])
        
        caption = """Select game mode:"""
        
        try:
            await message.reply_photo(SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except:
            await message.reply(caption, reply_markup=keyboard)

    # ================= MODE HANDLER =================
    @app.on_callback_query(filters.regex("^mode_"))
    async def mode_handler(client, callback: CallbackQuery):
        action = callback.data.split("_")[1]
        
        if action == "cancel":
            await callback.message.delete()
            await callback.answer("Cancelled")
            return
        
        if action in ["team", "auction", "tournament"]:
            await callback.answer(f"{action} mode coming soon!", show_alert=True)
            return
        
        if action == "solo":
            await ball_selection_menu(client, callback)

    # ================= BALL SELECTION MENU =================
    async def ball_selection_menu(client, callback):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = """🥎 Choose the Bowling mode:

Solo Play - 1 Ball
Solo Play - 3 Ball"""
        
        await callback.message.delete()
        
        try:
            await callback.message.reply_photo(
                SOLO_PLAY_IMG,
                caption=caption,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending solo play image: {e}")
            await callback.message.reply(
                caption,
                reply_markup=keyboard
            )
        await callback.answer()

    # ================= BALL SELECTION HANDLER =================
    @app.on_callback_query(filters.regex("^ball_"))
    async def ball_handler(client, callback: CallbackQuery):
        action = callback.data.split("_")[1]
        
        ball_mode = int(action)
        chat_id = callback.message.chat.id
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        
        await callback.message.delete()
        
        await client.send_message(
            chat_id,
            f"🎉Game created! Join the game using /joingame (2 minutes to join)\n⏰"
        )
        
        asyncio.create_task(start_join_timer(client, chat_id))

    # ================= JOIN TIMER =================
    async def start_join_timer(client, chat_id):
        await asyncio.sleep(60)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"1 minute left! {players_count} players joined. Send /joingame to join!")
        
        await asyncio.sleep(30)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"30 seconds left! {players_count} players joined. /joingame fast!!")
        
        await asyncio.sleep(20)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            await client.send_message(chat_id, f"Last 10 seconds! {players_count} players joined. /joingame !!")
        
        await asyncio.sleep(10)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            
            if players_count < 1:
                await client.send_message(chat_id, "No players joined! Game cancelled.")
                if chat_id in games:
                    del games[chat_id]
            else:
                await client.send_message(chat_id, f"Time's up! Starting game with {players_count} players...")
                await start_game_match(client, chat_id)

    # ================= VOTE SYSTEM =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"Voting in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        caption = """VOTING REQUIRED!

You are not an admin. 3 votes needed.

Current votes: 0/3"""
        
        try:
            msg = await message.reply_photo(
                VOTE_IMG, 
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
            )
        except:
            msg = await message.reply(
                caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
            )
        
        active_votes[chat_id]["msg_id"] = msg.id
        asyncio.create_task(auto_cancel_vote(client, chat_id))

    # ================= VOTE BUTTON =================
    @app.on_callback_query(filters.regex("^vote$"))
    async def vote_handler(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        vote = active_votes.get(chat_id)
        if not vote or not vote.get("active"):
            return await callback.answer("No active voting!", show_alert=True)
        
        if user.id in vote["users"]:
            return await callback.answer("Already voted!", show_alert=True)
        
        vote["users"].append(user.id)
        vote["count"] += 1
        
        voters = []
        for uid in vote["users"]:
            try:
                u = await client.get_users(uid)
                name = u.first_name if u.first_name else f"User_{uid}"
                voters.append(f"• {name}")
            except:
                voters.append(f"• User_{uid}")
        
        if vote["count"] >= 3:
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            vote["active"] = False
            await callback.answer("Voting successful!")
        else:
            caption = f"""VOTING REQUIRED!

You are not an admin. 3 votes needed.

Current votes: {vote['count']}/3

Voters:
{chr(10).join(voters)}"""
            
            try:
                await callback.message.edit_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
                )
            except:
                await callback.message.edit_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Vote to Start", callback_data="vote")]])
                )
            await callback.answer(f"Voted! ({vote['count']}/3)")

    # ================= AUTO CANCEL VOTE =================
    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote = active_votes.get(chat_id)
        if vote and vote.get("active") and vote["count"] < 3:
            try:
                await client.edit_message_caption(
                    chat_id, vote["msg_id"],
                    caption=f"Voting expired! Got {vote['count']}/3 votes.\nUse /start again."
                )
            except:
                pass
            vote["active"] = False

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return await message.reply("No active game! Use /start")
        
        if game.get("status") != "waiting":
            return await message.reply("Game already started!")
        
        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            players_count = len(game["players"])
            await message.reply(f"{message.from_user.first_name}, you've joined the game! (Player {players_count})")

    # ================= START GAME MATCH =================
    async def start_game_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        players_count = len(game["players"])
        if players_count < 1:
            await client.send_message(chat_id, "No players to start the game!")
            return
        
        start_match(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        host_text = "SOLO TREE COMMUNITY\n\nUnknown Host\n\nSolo Players\n\n"
        for i, p in enumerate(players, 1):
            name = f"@{p['username']}" if p.get("username") else p["name"]
            host_text += f"{i}. {name}\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text)
        except:
            await client.send_message(chat_id, host_text)
        
        batter = game["current_batter"]
        await client.send_message(chat_id, f"Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batter!")
        
        bowler = game["current_bowler"]
        await client.send_message(chat_id, f"Hey [{bowler['name']}](tg://user?id={bowler['id']}), now you're bowling!")
        
        await asyncio.sleep(1)
        await send_bowling_video(client, chat_id, bowler)

    # ================= SEND BOWLING VIDEO =================
    async def send_bowling_video(client, chat_id, bowler):
        game = games.get(chat_id)
        if not game or game.get("status") != "playing" or game.get("game_over"):
            return
        
        bot_username = BOT_USERNAME
        dm_link = f"https://t.me/{bot_username}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Click to Bowl", url=dm_link)]
        ])
        
        await client.send_video(
            chat_id, 
            BOWLING_VIDEO,
            caption=f"[{bowler['name']}](tg://user?id={bowler['id']}) now you can send number on bot pm, You have 1 min.",
            reply_markup=keyboard
        )

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        # Ignore /start command
        if text.startswith("/start"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        num = int(text)
        
        for chat_id, game in games.items():
            if game.get("status") != "playing" or game.get("game_over"):
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            if game.get("bowling_number") is not None:
                await message.reply("❌ You already bowled! Wait for your next turn.")
                return
            
            set_bowling(chat_id, num)
            await message.reply(f"✅ Bowling number {num} sent to game!")
            
            batter = game["current_batter"]
            await client.send_video(
                chat_id, 
                BATTING_VIDEO,
                caption=f"Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batting! Send number (1-6) in GROUP"
            )
            return
        
        await message.reply("❌ No active game found where you are the bowler!")

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return
        if game.get("status") != "playing":
            return
        if game.get("game_over"):
            return
        if game.get("bowling_number") is None:
            return
        
        batter = game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        
        text = message.text.strip()
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        bat = int(text)
        result = play_ball(chat_id, bat)
        bow = game.get("bowling_number", "?")
        game["bowling_number"] = None
        
        bowler = game["current_bowler"]
        ball_mode = game.get("ball_mode", 3)
        
        if result["type"] == "out":
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            
            if game.get("game_over"):
                final_text = build_scoreboard(game["players"], is_final=True)
                await message.reply(final_text)
                if chat_id in games:
                    del games[chat_id]
                return
            
            await message.reply(build_scoreboard(game["players"], is_final=False))
            
            new_batter = game["current_batter"]
            await client.send_message(chat_id, f"Hey [{new_batter['name']}](tg://user?id={new_batter['id']}), now you're batter!")
            
            if not game.get("game_over"):
                new_bowler = game["current_bowler"]
                await send_bowling_video(client, chat_id, new_bowler)
            
        else:
            try:
                await message.reply_video(get_run_video(result["runs"]), caption=RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=bowler["name"], bowl=bow))
            
            if not game.get("game_over"):
                if game["current_bowler_balls"] >= ball_mode:
                    await message.reply(build_scoreboard(game["players"], is_final=False))
                    new_bowler = game["current_bowler"]
                    await client.send_message(chat_id, f"Bowler changed! Now bowling: [{new_bowler['name']}](tg://user?id={new_bowler['id']})")
                    await send_bowling_video(client, chat_id, new_bowler)
                else:
                    await send_bowling_video(client, chat_id, bowler)
