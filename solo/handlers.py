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

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Solo", callback_data="mode_solo"), InlineKeyboardButton("Team", callback_data="mode_team")],
            [InlineKeyboardButton("Start Auction", callback_data="mode_auction"), InlineKeyboardButton("Tournament Mode", callback_data="mode_tournament")],
            [InlineKeyboardButton("Cancel", callback_data="mode_cancel")]
        ])
        
        caption = """SOLO TREE COMMUNITY

SELECT GAME

Solo Mode
Team Match

Select game mode:"""
        
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
        
        caption = """SOLO TREE COMMUNITY

SOLO PLAY MATCH

Choose the Bowling mode:

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
            f"Game created! Join the game using /joingame (2 minutes to join)\n⏰"
        )
        
        asyncio.create_task(start_join_timer(client, chat_id))

    # ================= JOIN TIMER =================
    async def start_join_timer(client, chat_id):
        await asyncio.sleep(60)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            await client.send_message(chat_id, "1 minute left only, everyone /joingame fast!!")
        
        await asyncio.sleep(30)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            await client.send_message(chat_id, "30 seconds left only, everyone /joingame fast!!")
        
        await asyncio.sleep(20)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            await client.send_message(chat_id, "Last 10 seconds left only, /joingame !!")
        
        await asyncio.sleep(10)
        
        game = games.get(chat_id)
        if game and game["status"] == "waiting":
            players_count = len(game.get("players", []))
            
            if players_count < 4:
                await client.send_message(chat_id, "Minimum 4 players required to start the game! 😭💔")
                await asyncio.sleep(2)
                await client.send_message(chat_id, "⚠️ Failed to start the game.")
                if chat_id in games:
                    del games[chat_id]
            else:
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
            
            if players_count >= 4:
                await message.reply("Enough players! Starting game...")
                await start_game_match(client, chat_id)

    # ================= START GAME MATCH =================
    async def start_game_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        start_match(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        text = "Match Started!\n\nPlayers:\n" + "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(players)])
        await client.send_message(chat_id, text)
        
        await client.send_video(
            chat_id, BOWLING_VIDEO,
            caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bowling", callback_data="bowl")]])
        )

    # ================= BOWLING BUTTON =================
    @app.on_callback_query(filters.regex("^bowl$"))
    async def bowl_btn(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        game = games.get(chat_id)
        
        if not game or game["status"] != "playing":
            return await callback.answer("No game!", show_alert=True)
        if game["current_bowler"]["id"] != user.id:
            return await callback.answer("Not your turn!", show_alert=True)
        
        await callback.answer("Check DM!")
        try:
            await client.send_message(user.id, "Send bowling number (1-6)")
        except:
            await callback.answer("Open DM first!", show_alert=True)

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message):
        user_id = message.from_user.id
        for chat_id, game in games.items():
            if game.get("status") != "playing":
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            
            text = message.text.strip()
            if not text.isdigit() or int(text) not in range(1, 7):
                return await message.reply(INVALID_NUMBER)
            
            set_bowling(chat_id, int(text))
            await client.send_video(
                chat_id, BATTING_VIDEO,
                caption=f"Batter: {game['current_batter']['name']}\nSend number (1-6) in GROUP"
            )
            await message.reply("Bowling number sent!")
            break

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game or game.get("status") != "playing":
            return
        if game.get("bowling_number") is None:
            return await message.reply("Waiting for bowler!")
        
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
        
        if result["type"] == "out":
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            
            if game.get("game_over"):
                return await message.reply(f"Game Over! {game['winner']['name']} wins!")
            
            await message.reply(f"New batter: {game['current_batter']['name']}")
        else:
            try:
                await message.reply_video(get_run_video(result["runs"]), caption=RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            except:
                await message.reply(RUN_MESSAGE.format(
                    batter=batter["name"], runs=f"{result['runs']} run{'s' if result['runs'] > 1 else ''}",
                    bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
        
        await message.reply(build_scoreboard(game["players"]))
        
        if game.get("game_over"):
            return await message.reply(f"Game Over! {game['winner']['name']} wins!")
        
        await message.reply(NEXT_TURN_MESSAGE.format(
            batter=game["current_batter"]["name"], bowler=game["current_bowler"]["name"]))
        
        try:
            await message.reply_video(BOWLING_VIDEO, caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bowling", callback_data="bowl")]]))
        except:
            await message.reply(BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bowling", callback_data="bowl")]]))
