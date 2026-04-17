# handlers.py - Fixed Admin Detection

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus  # ADD THIS IMPORT
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

active_votes = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    """Check if user is admin - FIXED with proper enum comparison"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        
        # Print for debugging
        print(f"🔍 User ID: {user_id}")
        print(f"🔍 Status: {member.status}")
        print(f"🔍 Status type: {type(member.status)}")
        
        # FIXED: Compare with ChatMemberStatus enum
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            print(f"✅ Is Admin: True")
            return True
        
        print(f"❌ Is Admin: False")
        return False
    except Exception as e:
        print(f"❌ Error checking admin: {e}")
        return False

def register_handlers(app):

    # ================= START =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        print(f"📱 /start command from user: {user_id}")
        print(f"📱 Chat ID: {chat_id}")
        
        admin_status = await is_admin(client, chat_id, user_id)
        
        if admin_status:
            print("✅ ADMIN - Showing SELECT GAME menu")
            await select_game_menu(client, message)
        else:
            print("❌ MEMBER - Showing VOTE system")
            await vote_system(client, message)

    # ================= SELECT GAME MENU (ADMIN) =================
    async def select_game_menu(client, message):
        print("🎮 Opening SELECT GAME menu")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Solo", callback_data="mode_solo"), InlineKeyboardButton("👥 Team", callback_data="mode_team")],
            [InlineKeyboardButton("💰 Start Auction", callback_data="mode_auction"), InlineKeyboardButton("🏆 Tournament Mode", callback_data="mode_tournament")],
            [InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel")]
        ])
        
        caption = """**# SOLO TREE COMMUNITY**

**# SELECT GAME**

**Solo mode**  
Each bowler bowls 3 balls, the batsman scores runs or gets out, and if out, the next player comes in until all batters are dismissed, with the total runs and wickets shown at the end.

**Team Match**  
Team A and Team B each play 6 balls, scoring runs or losing wickets, and the team with the higher total at the end win.

---

Select the game mode:"""
        
        try:
            await message.reply_photo(SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except Exception as e:
            print(f"Image error: {e}")
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
            await callback.answer(f"🚧 {action} mode coming soon!", show_alert=True)
            return
        
        if action == "solo":
            await callback.message.delete()
            create_game(callback.message.chat.id)
            await callback.message.reply(
                "🎉 Game created!\n\nJoin using /joingame\n⏰ 2 minutes left",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh")],
                    [InlineKeyboardButton("🚀 Force Start", callback_data="force_start")]
                ])
            )
            asyncio.create_task(auto_start(client, callback.message.chat.id))

    # ================= VOTE SYSTEM (MEMBER) =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        print(f"🗳️ Starting VOTE system for chat: {chat_id}")
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"🗳️ Voting already in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        caption = """**# VOTING REQUIRED!**

You are not an admin. At least 3 members must vote to start the game.

Click 'Vote to Start' to participate.

Current votes: 0/3"""
        
        try:
            msg = await message.reply_photo(
                VOTE_IMG, 
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ Vote to Start", callback_data="vote")]])
            )
        except:
            msg = await message.reply(
                caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ Vote to Start", callback_data="vote")]])
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
            return await callback.answer("You already voted!", show_alert=True)
        
        vote["users"].append(user.id)
        vote["count"] += 1
        
        # Get voter names
        voters = []
        for uid in vote["users"]:
            try:
                u = await client.get_users(uid)
                name = u.first_name if u.first_name else f"User_{uid}"
                voters.append(f"• {name}")
            except:
                voters.append(f"• User_{uid}")
        
        voters_text = "\n".join(voters)
        
        if vote["count"] >= 3:
            # Voting successful - Show SELECT GAME menu
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            vote["active"] = False
            await callback.answer("✅ Voting successful!")
        else:
            caption = f"""**# VOTING REQUIRED!**

You are not an admin. At least 3 members must vote to start the game.

Click 'Vote to Start' to participate.

Current votes: {vote['count']}/3

**Voters:**
{voters_text}"""
            
            try:
                await callback.message.edit_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ Vote to Start", callback_data="vote")]])
                )
            except:
                await callback.message.edit_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ Vote to Start", callback_data="vote")]])
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
                    caption=f"⚠️ Voting expired! Got only {vote['count']}/3 votes.\nUse /start again."
                )
            except:
                pass
            vote["active"] = False

    # ================= REFRESH =================
    @app.on_callback_query(filters.regex("^refresh$"))
    async def refresh_handler(client, callback):
        chat_id = callback.message.chat.id
        game = games.get(chat_id)
        if not game:
            return await callback.answer("No game!", show_alert=True)
        
        players = game.get("players", [])
        text = f"🎉 Solo Mode Active!\n\nPlayers ({len(players)}):\n" + "\n".join([f"• {p['name']}" for p in players]) or "• No players"
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh")],
                [InlineKeyboardButton("🚀 Force Start", callback_data="force_start")]
            ])
        )

    # ================= FORCE START =================
    @app.on_callback_query(filters.regex("^force_start$"))
    async def force_start_handler(client, callback):
        chat_id = callback.message.chat.id
        game = games.get(chat_id)
        if not game or len(game.get("players", [])) < 1:
            return await callback.answer("Need at least 1 player!", show_alert=True)
        await callback.message.edit_text("🚀 Starting game...")
        await start_match(client, chat_id)

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return await message.reply("❌ No active game! Ask admin to start with /start")
        
        if game.get("status") != "waiting":
            return await message.reply("❌ Game already started!")
        
        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            await message.reply(f"🎉 {message.from_user.first_name} joined! (Player {len(game['players'])})")

    # ================= AUTO START =================
    async def auto_start(client, chat_id):
        await asyncio.sleep(JOINING_TIMER_SECONDS)
        game = games.get(chat_id)
        if game and game["status"] == "waiting" and len(game["players"]) >= 1:
            await start_match(client, chat_id)
        elif game and len(game["players"]) < 1:
            await client.send_message(chat_id, "❌ Not enough players to start.")

    # ================= START MATCH =================
    async def start_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        start_match_game(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        text = "👑 **Match Started!**\n\n👤 **Players:**\n" + "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(players)])
        await client.send_message(chat_id, text)
        
        await client.send_video(
            chat_id, BOWLING_VIDEO,
            caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="bowl")]])
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
            await client.send_message(user.id, "🎯 Send bowling number (1-6)")
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
                caption=f"🏏 Now Batter: {game['current_batter']['name']}\n🔥 Send number (1-6) in GROUP"
            )
            await message.reply("✅ Bowling number sent!")
            break

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game or game.get("status") != "playing":
            return
        if game.get("bowling_number") is None:
            return await message.reply("⏳ Waiting for bowler!")
        
        batter = game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        
        text = message.text.strip()
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        bat = int(text)
        result = play_ball(chat_id, bat)
        bow = game["bowling_number"]
        game["bowling_number"] = None
        
        if result["type"] == "out":
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(
                    batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
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
            return await message.reply(f"🏆 Game Over! {game['winner']['name']} wins!")
        
        # Rotate players
        players = game["players"]
        idx = next((i for i, p in enumerate(players) if p["id"] == batter["id"]), 0)
        nxt = idx
        for _ in range(len(players)):
            nxt = (nxt + 1) % len(players)
            if not players[nxt].get("out"):
                break
        
        game["current_batter"] = players[nxt].copy()
        game["current_bowler"] = players[(nxt + 1) % len(players)].copy()
        
        await message.reply(NEXT_TURN_MESSAGE.format(
            batter=game["current_batter"]["name"], bowler=game["current_bowler"]["name"]))
        
        try:
            await message.reply_video(BOWLING_VIDEO, caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="bowl")]]))
        except:
            await message.reply(BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="bowl")]]))
