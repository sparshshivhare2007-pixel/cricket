# handlers.py - Final Complete Version

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
import asyncio

active_votes = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_group_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def register_handlers(app):

    # ================= START =================
    @app.on_message(filters.command("start") & filters.group)
    async def start(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if await is_group_admin(client, chat_id, user_id):
            # ADMIN - Direct SELECT GAME menu
            await select_game_menu(client, message)
        else:
            # MEMBER - Voting system with VOTE image
            await member_vote_system(client, message)

    # ================= SELECT GAME MENU (Admin) =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Solo", callback_data="select_solo"), InlineKeyboardButton("👥 Team", callback_data="select_team")],
            [InlineKeyboardButton("💰 Start Auction", callback_data="select_auction"), InlineKeyboardButton("🏆 Tournament Mode", callback_data="select_tournament")],
            [InlineKeyboardButton("❌ Cancel", callback_data="select_cancel")]
        ])
        
        caption = """**🏏 SOLO TREE COMMUNITY**

**SELECT GAME**

**🎯 Solo Mode**
Each bowler bowls 3 balls, the batsman scores runs or gets out

**👥 Team Match**
Team A and Team B each play 6 balls

---
*Select the game mode below* 👇"""
        
        try:
            await message.reply_photo(SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except:
            await message.reply(caption, reply_markup=keyboard)

    # ================= SELECT GAME BUTTONS =================
    @app.on_callback_query(filters.regex("^select_"))
    async def select_game_handler(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        action = callback.data.split("_")[1]
        
        if action == "cancel":
            await callback.message.delete()
            await callback.answer("Cancelled ❌")
            return
        
        if action in ["auction", "tournament", "team"]:
            await callback.answer(f"🚧 {action.title()} mode coming soon!", show_alert=True)
            return
        
        if action == "solo":
            await callback.message.delete()
            create_game(chat_id)
            
            await client.send_message(
                chat_id,
                "🎉 **Solo Mode Activated!**\n\n"
                "📝 Send `/joingame` to join\n"
                f"⏰ Auto-start in {JOINING_TIMER_SECONDS//60} minutes",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_solo")],
                    [InlineKeyboardButton("🚀 Force Start", callback_data="force_solo_start")]
                ])
            )
            asyncio.create_task(auto_start_game(client, chat_id))

    # ================= MEMBER VOTE SYSTEM =================
    async def member_vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active", False):
            await message.reply(f"🗳️ Voting already in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "start_time": asyncio.get_event_loop().time()}
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="member_vote")]])
        
        caption = """**🏏 SOLO TREE COMMUNITY**

🗳️ **VOTING REQUIRED!**

You are not an admin. At least 3 members must vote to start the game.

Click 'Vote to Start' to participate.

Current votes: 0/3"""
        
        try:
            vote_msg = await message.reply_photo(VOTE_IMG, caption=caption, reply_markup=keyboard)
        except:
            vote_msg = await message.reply(caption, reply_markup=keyboard)
        
        active_votes[chat_id]["message_id"] = vote_msg.id
        asyncio.create_task(auto_cancel_vote(client, chat_id))

    # ================= MEMBER VOTE =================
    @app.on_callback_query(filters.regex("^member_vote$"))
    async def member_vote(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        vote_data = active_votes.get(chat_id)
        if not vote_data or not vote_data.get("active", False):
            await callback.answer("❌ No active voting session!", show_alert=True)
            return
        
        if user.id in vote_data["users"]:
            await callback.answer("❌ You already voted!", show_alert=True)
            return
        
        vote_data["users"].append(user.id)
        vote_data["count"] += 1
        
        voters = []
        for uid in vote_data["users"]:
            try:
                u = await client.get_users(uid)
                voters.append(f"• {u.first_name}")
            except:
                voters.append(f"• User {uid}")
        
        voters_text = "\n".join(voters)
        
        if vote_data["count"] >= 3:
            # Voting successful - Show SELECT GAME menu
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            active_votes[chat_id]["active"] = False
            await callback.answer("✅ Voting successful! Game menu opened!")
        else:
            caption = f"""**🏏 SOLO TREE COMMUNITY**

🗳️ **VOTING IN PROGRESS!**

Current votes: {vote_data['count']}/3

**Voters:**
{voters_text}

Need {3 - vote_data['count']} more vote(s)! 👇"""
            
            await callback.message.edit_caption(
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="member_vote")]])
            )
            await callback.answer(f"Voted! ({vote_data['count']}/3)")

    # ================= AUTO CANCEL VOTE =================
    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote_data = active_votes.get(chat_id)
        if vote_data and vote_data.get("active", False) and vote_data["count"] < 3:
            try:
                caption = f"""**🏏 SOLO TREE COMMUNITY**

⚠️ **Voting session expired!**

Got only {vote_data['count']}/3 votes.
Use /start to start new voting session."""
                await client.edit_message_caption(chat_id, vote_data["message_id"], caption=caption)
            except:
                pass
            active_votes[chat_id]["active"] = False

    # ================= REFRESH SOLO =================
    @app.on_callback_query(filters.regex("^refresh_solo$"))
    async def refresh_solo(client, callback):
        chat_id = callback.message.chat.id
        game = games.get(chat_id)
        if not game:
            return await callback.answer("No active game!", show_alert=True)
        
        players = game.get("players", [])
        players_list = "\n".join([f"• {p['name']}" for p in players]) or "• No players yet"
        
        await callback.message.edit_text(
            f"🎉 **Solo Mode Active!**\n\n📝 **Players ({len(players)}):**\n{players_list}\n\nSend `/joingame` to join!\n⏰ Auto-start in {JOINING_TIMER_SECONDS//60} minutes",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_solo")],
                [InlineKeyboardButton("🚀 Force Start", callback_data="force_solo_start")]
            ])
        )
        await callback.answer()

    # ================= FORCE SOLO START =================
    @app.on_callback_query(filters.regex("^force_solo_start$"))
    async def force_solo_start(client, callback):
        chat_id = callback.message.chat.id
        game = games.get(chat_id)
        if not game:
            return await callback.answer("No active game!", show_alert=True)
        if len(game.get("players", [])) < 1:
            return await callback.answer("Need at least 1 player!", show_alert=True)
        await callback.message.edit_text("🚀 Force starting game...")
        await start_match_flow(client, chat_id)

    # ================= JOIN =================
    @app.on_message(filters.command("joingame") & filters.group)
    async def join(client, message: Message):
        chat_id = message.chat.id
        if join_game(chat_id, message.from_user):
            game = games[chat_id]
            await message.reply(f"🎉 {message.from_user.first_name} joined! (Player {len(game['players'])})")

    # ================= AUTO START =================
    async def auto_start_game(client, chat_id):
        await asyncio.sleep(JOINING_TIMER_SECONDS)
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        if len(game["players"]) < 1:
            await client.send_message(chat_id, "❌ Not enough players to start.")
            return
        await start_match_flow(client, chat_id)

    # ================= START MATCH FLOW =================
    async def start_match_flow(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        players = game["players"]
        text = "👑 **Match Started!**\n\n👤 **Players:**\n"
        for i, p in enumerate(players, 1):
            name = f"@{p.get('username')}" if p.get("username") else p["name"]
            text += f"{i}. {name}\n"
        await client.send_message(chat_id, text)
        
        start_match(chat_id)
        game = games[chat_id]
        await client.send_message(chat_id, "🚀 Game starting...")
        
        try:
            await client.send_video(chat_id, BOWLING_VIDEO, caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="start_bowling")]]))
        except:
            await client.send_message(chat_id, BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="start_bowling")]]))

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
            await client.send_message(user.id, "🎯 Bowling Started!\nSend number (1-6)")
        except:
            await callback.answer("Open bot in DM first ❌", show_alert=True)

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message: Message):
        user_id = message.from_user.id
        for chat_id, game in games.items():
            if game.get("status") != "playing":
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            text = (message.text or "").strip()
            if not text.isdigit():
                return await message.reply(INVALID_NUMBER)
            num = int(text)
            if num < 1 or num > 6:
                return await message.reply(INVALID_NUMBER)
            set_bowling(chat_id, num)
            try:
                await client.send_video(chat_id, BATTING_VIDEO, caption=f"🏏 Now Batter: {game['current_batter']['name']}\n🔥 Send number (1-6) in GROUP")
            except:
                await client.send_message(chat_id, f"🏏 Now Batter: {game['current_batter']['name']}\n🔥 Send number (1-6) in GROUP")
            await message.reply("✅ Bowling number sent to game!")
            break

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        if not game or game.get("status") != "playing":
            return
        if game.get("bowling_number") is None:
            await message.reply("⏳ Waiting for bowler to bowl first!")
            return
        batter = game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        text = (message.text or "").strip()
        if not text.isdigit():
            return await message.reply(INVALID_NUMBER)
        bat = int(text)
        if bat < 1 or bat > 6:
            return await message.reply(INVALID_NUMBER)
        result = play_ball(chat_id, bat)
        bow = game.get("bowling_number", "?")
        game["bowling_number"] = None
        
        if result["type"] == "out":
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            if game.get("game_over"):
                await message.reply(f"🏆 Game Over! {game['winner']['name']} wins!")
                return
        elif result["type"] == "run":
            runs = result['runs']
            runs_text = f"{runs} run{'s' if runs > 1 else ''}"
            run_video = get_run_video(runs)
            try:
                await message.reply_video(run_video, caption=RUN_MESSAGE.format(batter=batter["name"], runs=runs_text, bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
            except:
                await message.reply(RUN_MESSAGE.format(batter=batter["name"], runs=runs_text, bat=bat, bowler=game["current_bowler"]["name"], bowl=bow))
        
        await message.reply(build_scoreboard(game["players"]))
        if game.get("game_over"):
            await message.reply(f"🏆 Game Over! {game['winner']['name']} wins!")
            return
        
        players = game["players"]
        cur_index = next((i for i, p in enumerate(players) if p["id"] == batter["id"]), 0)
        next_index = cur_index
        for _ in range(len(players)):
            next_index = (next_index + 1) % len(players)
            if not players[next_index].get("out", False):
                break
        game["current_batter"] = players[next_index].copy()
        bowler_index = (next_index + 1) % len(players)
        game["current_bowler"] = players[bowler_index].copy()
        await message.reply(NEXT_TURN_MESSAGE.format(batter=game["current_batter"]["name"], bowler=game["current_bowler"]["name"]))
        try:
            await message.reply_video(BOWLING_VIDEO, caption=BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="start_bowling")]]))
        except:
            await message.reply(BOWLING_MESSAGE.format(bowler=game["current_bowler"]["name"]), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Bowling", callback_data="start_bowling")]]))
