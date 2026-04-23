from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
from solo.game import *
from solo.scoreboard import build_scoreboard
from solo.score import get_live_score
import asyncio
from datetime import datetime
import io
import random

active_votes = {}
bowling_tasks = {}

# ================= TEAM MODE VARIABLES =================
team_games = {}
team_hosts = {}
user_reports = {}

def get_run_video(runs):
    run_videos = {1: RUN_1_VIDEO, 2: RUN_2_VIDEO, 3: RUN_3_VIDEO, 4: RUN_4_VIDEO, 5: RUN_5_VIDEO, 6: RUN_6_VIDEO}
    return run_videos.get(runs, RUN_1_VIDEO)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ================= SOLO MODE SEND BOWLING VIDEO =================
async def send_bowling_video(client, chat_id, bowler):
    game = games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        return
    
    batter = game["current_batter"]
    bot_username = BOT_USERNAME
    dm_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Click to Bowl", url=dm_link)]
    ])
    
    bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
    
    await client.send_video(
        chat_id, 
        BOWLING_VIDEO,
        caption=f"{bowler_clickable} now you can send number on bot pm, You have 1 min.",
        reply_markup=keyboard
    )
    
    batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
    
    try:
        await client.send_message(
            bowler["id"],
            f"🎯 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
            disable_web_page_preview=True
        )
    except:
        pass
    
    if chat_id in bowling_tasks:
        try:
            bowling_tasks[chat_id].cancel()
        except:
            pass
    
    task = asyncio.create_task(bowling_timeout_with_warnings(client, chat_id, bowler["id"], bowler["name"], None))
    bowling_tasks[chat_id] = task

# ================= SOLO MODE TIMEOUT =================
async def bowling_timeout_with_warnings(client, chat_id, user_id, bowler_name, message_id):
    await asyncio.sleep(30)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 30 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(20)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 10 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(10)
    game = games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            
            for player in game["players"]:
                if player["id"] == user_id:
                    player["score"] -= 6
                    player["history"].append("-6")
                    break
            
            try:
                await client.send_video(
                    chat_id,
                    get_run_video(6),
                    caption=f"No message received from bowler, deducting 6 runs from {bowler_name}'s score."
                )
            except Exception as e:
                print(f"Error sending 6 run video: {e}")
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs from {bowler_name}'s score."
                )
            
            await client.send_message(chat_id, build_scoreboard(game["players"], is_final=False))
            
            game["bowling_number"] = None
            game["current_bowler_balls"] += 1
            game["total_balls_in_match"] += 1
            
            await send_bowling_video(client, chat_id, game["current_bowler"])
    
    if chat_id in bowling_tasks:
        del bowling_tasks[chat_id]

# ================= TEAM MODE SEND BOWLING VIDEO =================
async def send_bowling_video_team(client, chat_id, bowler):
    game = team_games.get(chat_id)
    if not game or game.get("status") != "playing" or game.get("game_over"):
        return
    
    batter = game["current_batter"]
    bot_username = BOT_USERNAME
    dm_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Click to Bowl", url=dm_link)]
    ])
    
    bowler_clickable = f"[{bowler['name']}](tg://user?id={bowler['id']})"
    
    await client.send_video(
        chat_id, 
        BOWLING_VIDEO,
        caption=f"{bowler_clickable} now you can send number on bot pm, You have 1 min.",
        reply_markup=keyboard
    )
    
    batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
    
    try:
        await client.send_message(
            bowler["id"],
            f"🎯 Current batter: {batter_clickable}\n\nSend Your number (1-6):",
            disable_web_page_preview=True
        )
    except:
        pass
    
    if chat_id in bowling_tasks:
        try:
            bowling_tasks[chat_id].cancel()
        except:
            pass
    
    task = asyncio.create_task(bowling_timeout_with_warnings_team(client, chat_id, bowler["id"], bowler["name"], None))
    bowling_tasks[chat_id] = task

# ================= TEAM MODE TIMEOUT =================
async def bowling_timeout_with_warnings_team(client, chat_id, user_id, bowler_name, message_id):
    await asyncio.sleep(30)
    game = team_games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 30 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(20)
    game = team_games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            try:
                await client.send_message(
                    chat_id,
                    f"⚠️ Warning: [{bowler_name}](tg://user?id={user_id}), you have 10 seconds left to send a number!"
                )
            except:
                pass
    
    await asyncio.sleep(10)
    game = team_games.get(chat_id)
    if game and game.get("status") == "playing":
        current_bowler = game.get("current_bowler", {})
        if current_bowler.get("id") == user_id and game.get("bowling_number") is None:
            
            team_key = f"team_{game['current_team'].lower()}"
            for player in game[team_key]:
                if player["id"] == user_id:
                    player["score"] -= 6
                    player["history"].append("-6")
                    break
            
            game["team_total"] = sum(p["score"] for p in game[team_key])
            
            try:
                await client.send_video(
                    chat_id,
                    get_run_video(6),
                    caption=f"No message received from bowler, deducting 6 runs from {game['current_team']} team."
                )
            except Exception as e:
                print(f"Error sending 6 run video: {e}")
                await client.send_message(
                    chat_id,
                    f"No message received from bowler, deducting 6 runs from {game['current_team']} team."
                )
            
            await client.send_message(chat_id, build_team_scoreboard(game))
            
            game["bowling_number"] = None
            game["current_bowler_balls"] += 1
            game["total_balls_in_inning"] += 1
            
            if game["current_bowler_balls"] >= 6:
                players = game[team_key]
                new_bowler_index = (game["current_bowler_index"] + 1) % len(players)
                game["current_bowler_index"] = new_bowler_index
                game["current_bowler"] = players[new_bowler_index].copy()
                game["current_bowler_balls"] = 0
            
            await send_bowling_video_team(client, chat_id, game["current_bowler"])
    
    if chat_id in bowling_tasks:
        del bowling_tasks[chat_id]

def build_team_scoreboard(game):
    team_key = f"team_{game['current_team'].lower()}"
    players = game[team_key]
    
    scoreboard = f"🏏 **{game['current_team']} Team Scoreboard** 🏏\n\n"
    scoreboard += f"**Total:** {game['team_total']}/{game['team_wickets']}\n"
    scoreboard += f"**Balls:** {game['total_balls_in_inning']}\n\n"
    scoreboard += "**Players:**\n"
    
    for p in players:
        status = "❌" if p.get("out", False) else "🏏"
        scoreboard += f"{status} {p['name']}: {p['score']} ({p['balls']} balls)"
        if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
            scoreboard += f" [4s:{p['fours']} 6s:{p['sixes']}]"
        scoreboard += "\n"
    
    return scoreboard

def register_handlers(app):

    # ================= START GROUP =================
    @app.on_message(filters.command("start") & filters.group)
    async def start_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if await is_admin(client, chat_id, user_id):
            await select_game_menu(client, message)
        else:
            await vote_system(client, message)

    # ================= SCORE COMMAND =================
    @app.on_message(filters.command("score") & filters.group)
    async def score_cmd(client, message: Message):
        await get_live_score(client, message)

    # ================= HELP COMMAND =================
    @app.on_message(filters.command("help") & filters.group)
    async def help_cmd(client, message: Message):
        help_text = """🏏 **Cricket Game Bot Commands** 🏏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          🎮 GAME MODES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**SOLO MODE:**
/start - Start game (Admin) or Vote (Member)
/joingame - Join solo game (min 4 players)
/score - Check live score
/end_match - End current match (Admin)
/solo_leave - Leave solo game

**TEAM MODE:**
/create_team - Create teams (Host only)
/join_teamA - Join Team A
/join_teamB - Join Team B
/choose_cap - Choose team captains (Host)
/add_A @user - Add player to Team A
/add_B @user - Add player to Team B
/shift_Team - Shift player between teams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📊 EXTRA COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/user_info - Get your user information
/user_ranks - View player rankings
/member_lists - View group members list
/startgame - Start new game (Admin)
/matches - View active matches
/live_matches - View live match updates
/host_change @user - Change game host
/full_score - View complete scorecard
/report_user @user - Report a user
/report_stats - View report statistics (Admin)
/batting <pos> - Change batting order (Captain)
/bowling <pos> - Change bowling order (Captain)
/cap_change @user - Change team captain (Host)
/add_cap @user - Add a captain (Host)
/rm_cap @user - Remove a captain (Host)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ℹ️ INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Solo mode requires minimum 4 players
• 3 balls per bowler in solo mode
• 6 balls per over in team mode
• Bot must be admin in group

🏏 **Enjoy the game!** 🏏"""
        
        await message.reply(help_text)

    # ================= USER INFO COMMAND ================
    @app.on_message(filters.command("user_info") & filters.group)
    async def user_info_cmd(client, message: Message):
        user = message.from_user
        user_id = user.id
        name = user.first_name
        username = user.username
        
        # Get or create user from database
        from database import get_or_create_user
        
        # Ensure user exists in database
        user_data = await get_or_create_user(user_id, name, username)
        
        # Get stats from database
        highest_score = user_data.get("highest_score", 0)
        highest_score_balls = user_data.get("highest_score_balls", 0)
        best_game_host = user_data.get("best_game_host", 0)
        total_runs = user_data.get("total_runs", 0)
        total_balls = user_data.get("total_balls", 0)
        wickets = user_data.get("wickets", 0)
        sixes = user_data.get("sixes", 0)
        fours = user_data.get("fours", 0)
        centuries = user_data.get("centuries", 0)
        fifties = user_data.get("fifties", 0)
        ducks = user_data.get("ducks", 0)
        hat_tricks = user_data.get("hat_tricks", 0)
        man_of_match = user_data.get("man_of_match", 0)
        best_captain = user_data.get("best_captain", 0)
        matches_played = user_data.get("matches_played", 0)
        runs_conceded = user_data.get("runs_conceded", 0)
        overs_bowled = user_data.get("overs_bowled", 0)
        
        # Calculate strike rate
        strike_rate = round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0.0
        
        # Calculate economy rate
        economy_rate = round((runs_conceded / overs_bowled), 2) if overs_bowled > 0 else 0.0
        
        # Create clickable user mention
        if username:
            user_mention = f"<a href='tg://user?id={user_id}'>@{username}</a>"
        else:
            user_mention = f"<a href='tg://user?id={user_id}'>{name}</a>"
        
        # Prepare stats text with monospace font
        stats_text = f"""<code>
🏏 STATS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━

👤 User     : {user_mention}
🆔 User ID  : {user_id}
📅 Date     : {datetime.now().strftime('%Y-%m-%d')}

━━━━━━━━━━━━━━━━━━━━━━━━━
BATTING STATS
━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 Highest Score    : {highest_score} ({highest_score_balls} balls)
📊 Total Runs       : {total_runs}
🎯 Matches Played   : {matches_played}
⚡ Strike Rate      : {strike_rate}
💥 Sixes            : {sixes}
✨ Fours            : {fours}
🔥 Centuries        : {centuries}
⭐ Fifties          : {fifties}
🦆 Ducks            : {ducks}

━━━━━━━━━━━━━━━━━━━━━━━━━
BOWLING STATS
━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Wickets          : {wickets}
🎯 Economy Rate     : {economy_rate}
🎩 Hat-Tricks       : {hat_tricks}

━━━━━━━━━━━━━━━━━━━━━━━━━
ACHIEVEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━

🏅 Man of the Match : {man_of_match}
🧢 Best Captain     : {best_captain}
🎮 Best Game Host   : {best_game_host}

━━━━━━━━━━━━━━━━━━━━━━━━━
</code>"""
        
        # Send image with spoiler and caption
        try:
            if USER_STATS_IMAGE.startswith(('http://', 'https://')):
                await client.send_photo(
                    message.chat.id,
                    USER_STATS_IMAGE,
                    caption=stats_text,
                    has_spoiler=True,
                    parse_mode="HTML"
                )
            else:
                await client.send_photo(
                    message.chat.id,
                    USER_STATS_IMAGE,
                    caption=stats_text,
                    has_spoiler=True,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Error sending image: {e}")
            await message.reply(stats_text, parse_mode="HTML")

    # ================= USER RANKS COMMAND =================
    @app.on_message(filters.command("user_ranks") & filters.group)
    async def user_ranks_cmd(client, message: Message):
        chat_id = message.chat.id
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        rank_text = "🏆 **Player Ranks** 🏆\n\n"
        
        if solo_game and solo_game.get("players"):
            players = solo_game["players"]
            sorted_players = sorted(players, key=lambda x: x.get("score", 0), reverse=True)
            
            for i, p in enumerate(sorted_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
                rank_text += f"{medal} {i}. {name} - {p.get('score', 0)} runs\n"
        
        if team_game:
            rank_text += "\n**TEAM A:**\n"
            team_a_players = sorted(team_game.get("team_a", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_a_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
            
            rank_text += "\n**TEAM B:**\n"
            team_b_players = sorted(team_game.get("team_b", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_b_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
        
        await message.reply(rank_text)
        
    # ================= USER RANKS COMMAND =================
    @app.on_message(filters.command("user_ranks") & filters.group)
    async def user_ranks_cmd(client, message: Message):
        chat_id = message.chat.id
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        rank_text = "🏆 **Player Ranks** 🏆\n\n"
        
        if solo_game and solo_game.get("players"):
            players = solo_game["players"]
            sorted_players = sorted(players, key=lambda x: x.get("score", 0), reverse=True)
            
            for i, p in enumerate(sorted_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
                rank_text += f"{medal} {i}. {name} - {p.get('score', 0)} runs\n"
        
        if team_game:
            rank_text += "\n**TEAM A:**\n"
            team_a_players = sorted(team_game.get("team_a", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_a_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
            
            rank_text += "\n**TEAM B:**\n"
            team_b_players = sorted(team_game.get("team_b", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_b_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
        
        await message.reply(rank_text)

    # ================= MEMBER LISTS COMMAND =================
    @app.on_message(filters.command("member_lists") & filters.group)
    async def member_lists_cmd(client, message: Message):
        chat_id = message.chat.id
        
        try:
            total = 0
            admins = []
            members = []
            bots = []
            
            async for m in client.get_chat_members(chat_id):
                total += 1
                if m.user.is_bot:
                    bots.append(m.user.first_name)
                elif m.status.value in ['administrator', 'creator']:
                    admins.append(f"@{m.user.username}" if m.user.username else m.user.first_name)
                else:
                    members.append(f"@{m.user.username}" if m.user.username else m.user.first_name)
            
            text = f"📊 **Group Members**\n\n"
            text += f"👥 Total Members: {total}\n"
            text += f"👑 Admins: {len(admins)}\n"
            text += f"👤 Members: {len(members)}\n"
            text += f"🤖 Bots: {len(bots)}\n\n"
            
            if admins:
                text += "**👑 Admins:**\n" + "\n".join(admins[:10]) + "\n\n"
            if members:
                text += "**👤 Members (First 10):**\n" + "\n".join(members[:10]) + "\n\n"
            if bots:
                text += "**🤖 Bots:**\n" + "\n".join(bots)
            
            await message.reply(text)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ================= STARTGAME COMMAND =================
    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if not await is_admin(client, chat_id, user_id):
            await message.reply("❌ Only admins can use /startgame!")
            return
        
        if games.get(chat_id):
            await message.reply("❌ A game is already active in this group!")
            return
        
        create_game(chat_id)
        await select_game_menu(client, message)

    # ================= MATCHES COMMAND =================
    @app.on_message(filters.command("matches") & filters.group)
    async def matches_cmd(client, message: Message):
        chat_id = message.chat.id
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active matches in this group!")
            return
        
        matches_text = "🏏 **Active Matches** 🏏\n\n"
        
        if solo_game:
            status = solo_game.get("status", "unknown")
            players_count = len(solo_game.get("players", []))
            matches_text += f"**SOLO MODE**\n"
            matches_text += f"📊 Status: {status.upper()}\n"
            matches_text += f"👥 Players: {players_count}\n"
            matches_text += f"🎯 Ball Mode: {solo_game.get('ball_mode', 3)} balls\n\n"
        
        if team_game:
            status = team_game.get("status", "unknown")
            team_a_count = len(team_game.get("team_a", []))
            team_b_count = len(team_game.get("team_b", []))
            overs = team_game.get("overs", 0)
            matches_text += f"**TEAM MODE**\n"
            matches_text += f"📊 Status: {status.upper()}\n"
            matches_text += f"🏏 Team A: {team_a_count} players\n"
            matches_text += f"🏏 Team B: {team_b_count} players\n"
            matches_text += f"🎯 Overs: {overs}\n"
        
        await message.reply(matches_text)

    # ================= LIVE MATCHES COMMAND =================
    @app.on_message(filters.command("live_matches") & filters.group)
    async def live_matches_cmd(client, message: Message):
        chat_id = message.chat.id
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No live matches in this group!")
            return
        
        live_text = "🔥 **LIVE MATCHES** 🔥\n\n"
        
        if solo_game and solo_game.get("status") == "playing":
            batter = solo_game.get("current_batter", {})
            bowler = solo_game.get("current_bowler", {})
            players = solo_game.get("players", [])
            live_text += f"**SOLO MODE - LIVE**\n"
            live_text += f"🏏 Batter: {batter.get('name', 'N/A')}\n"
            live_text += f"⚾ Bowler: {bowler.get('name', 'N/A')}\n"
            live_text += f"📊 Balls: {solo_game.get('total_balls_in_match', 0)}\n"
            live_text += f"👥 Active: {len([p for p in players if not p.get('out', False)])}\n\n"
        
        if team_game and team_game.get("status") == "playing":
            current_team = team_game.get("current_team", "N/A")
            batter = team_game.get("current_batter", {})
            bowler = team_game.get("current_bowler", {})
            live_text += f"**TEAM MODE - LIVE**\n"
            live_text += f"🏏 Batting: Team {current_team}\n"
            live_text += f"🏏 Batter: {batter.get('name', 'N/A')}\n"
            live_text += f"⚾ Bowler: {bowler.get('name', 'N/A')}\n"
            live_text += f"📊 Team A: {team_game.get('team_a_score', 0)}/{team_game.get('team_a_wickets', 0)}\n"
            live_text += f"📊 Team B: {team_game.get('team_b_score', 0)}/{team_game.get('team_b_wickets', 0)}\n"
        
        await message.reply(live_text)

    # ================= HOST CHANGE COMMAND =================
    @app.on_message(filters.command("host_change") & filters.group)
    async def host_change_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        is_group_admin = await is_admin(client, chat_id, user_id)
        is_solo_host = solo_game and solo_game.get("host_id") == user_id
        is_team_host = team_game and team_hosts.get(chat_id, {}).get("id") == user_id
        
        if not (is_group_admin or is_solo_host or is_team_host):
            await message.reply("❌ Only game host or group admin can change host!")
            return
        
        new_host = None
        if message.reply_to_message:
            new_host = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_host = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not new_host:
            await message.reply("❌ Usage: /host_change @username or reply to a user's message")
            return
        
        if solo_game:
            solo_game["host_id"] = new_host.id
            solo_game["host_name"] = new_host.first_name
            await message.reply(f"👑 Host changed to [{new_host.first_name}](tg://user?id={new_host.id}) in SOLO mode!")
        
        if team_game:
            team_hosts[chat_id] = {"id": new_host.id, "name": new_host.first_name, "username": new_host.username}
            team_game["host_id"] = new_host.id
            team_game["host_name"] = new_host.first_name
            await message.reply(f"👑 Host changed to [{new_host.first_name}](tg://user?id={new_host.id}) in TEAM mode!")

    # ================= SOLO LEAVE COMMAND =================
    @app.on_message(filters.command("solo_leave") & filters.group)
    async def solo_leave_cmd(client, message: Message):
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
                await message.reply(f"✅ {message.from_user.first_name} left the solo game!\nRemaining players: {len(players)}")
                return
        
        await message.reply("❌ You are not in the solo game!")

    # ================= FULL SCORE COMMAND =================
    @app.on_message(filters.command("full_score") & filters.group)
    async def full_score_cmd(client, message: Message):
        chat_id = message.chat.id
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        if solo_game:
            players = solo_game.get("players", [])
            if players:
                await message.reply(build_scoreboard(players, is_final=False))
            else:
                await message.reply("❌ No players in solo game!")
        
        if team_game:
            score_text = "🏏 **COMPLETE SCOREBOARD** 🏏\n\n"
            score_text += "**TEAM A:**\n"
            for p in team_game.get("team_a", []):
                status = "❌" if p.get("out", False) else "🏏"
                name = f"@{p['username']}" if p.get('username') else p['name']
                score_text += f"{status} {name}: {p.get('score', 0)} ({p.get('balls', 0)} balls)"
                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    score_text += f" [4s:{p.get('fours', 0)} 6s:{p.get('sixes', 0)}]"
                score_text += "\n"
            score_text += f"\n**Team A Total:** {team_game.get('team_a_score', 0)}/{team_game.get('team_a_wickets', 0)}\n\n"
            
            score_text += "**TEAM B:**\n"
            for p in team_game.get("team_b", []):
                status = "❌" if p.get("out", False) else "🏏"
                name = f"@{p['username']}" if p.get('username') else p['name']
                score_text += f"{status} {name}: {p.get('score', 0)} ({p.get('balls', 0)} balls)"
                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    score_text += f" [4s:{p.get('fours', 0)} 6s:{p.get('sixes', 0)}]"
                score_text += "\n"
            score_text += f"\n**Team B Total:** {team_game.get('team_b_score', 0)}/{team_game.get('team_b_wickets', 0)}"
            
            await message.reply(score_text)

    # ================= REPORT USER COMMAND =================
    @app.on_message(filters.command("report_user") & filters.group)
    async def report_user_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        reported_user = None
        if message.reply_to_message:
            reported_user = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                reported_user = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not reported_user:
            await message.reply("❌ Usage: /report_user @username or reply to a user's message")
            return
        
        if reported_user.id == user_id:
            await message.reply("❌ You cannot report yourself!")
            return
        
        reason = "No reason provided"
        if len(message.command) > 2:
            reason = " ".join(message.command[2:])
        
        if chat_id not in user_reports:
            user_reports[chat_id] = {}
        if reported_user.id not in user_reports[chat_id]:
            user_reports[chat_id][reported_user.id] = []
        
        user_reports[chat_id][reported_user.id].append({
            "reporter_id": user_id,
            "reason": reason,
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        report_count = len(user_reports[chat_id][reported_user.id])
        
        await message.reply(f"✅ **Report Submitted!**\n\nReported: [{reported_user.first_name}](tg://user?id={reported_user.id})\nReason: {reason}\nTotal Reports: {report_count}")

    # ================= REPORT STATS COMMAND =================
    @app.on_message(filters.command("report_stats") & filters.group)
    async def report_stats_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if not await is_admin(client, chat_id, user_id):
            await message.reply("❌ Only group admins can view report statistics!")
            return
        
        if chat_id not in user_reports or not user_reports[chat_id]:
            await message.reply("📊 No reports have been submitted yet!")
            return
        
        stats_text = "📊 **Report Statistics** 📊\n\n"
        for uid, reports in user_reports[chat_id].items():
            try:
                user = await client.get_users(uid)
                name = f"@{user.username}" if user.username else user.first_name
            except:
                name = f"User_{uid}"
            stats_text += f"👤 {name}: {len(reports)} reports\n"
            for r in reports[-3:]:
                stats_text += f"   • Reason: {r['reason']}\n"
                stats_text += f"     Time: {r['time']}\n"
            stats_text += "\n"
        
        await message.reply(stats_text)

    # ================= BATTING COMMAND =================
    @app.on_message(filters.command("batting") & filters.group)
    async def batting_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        team_game = team_games.get(chat_id)
        
        if not team_game or team_game.get("status") != "playing":
            await message.reply("❌ No active team game found!")
            return
        
        is_captain_a = team_game.get("captain_a", {}).get("id") == user_id
        is_captain_b = team_game.get("captain_b", {}).get("id") == user_id
        
        if not (is_captain_a or is_captain_b):
            await message.reply("❌ Only team captains can change batting order!")
            return
        
        args = message.command
        if len(args) < 2:
            await message.reply("❌ Usage: /batting <position_number>\nExample: /batting 3")
            return
        
        try:
            position = int(args[1]) - 1
        except ValueError:
            await message.reply("❌ Please provide a valid number!")
            return
        
        current_team = team_game.get("current_team", "A")
        team_key = f"team_{current_team.lower()}"
        players = team_game[team_key]
        
        if position < 0 or position >= len(players):
            await message.reply(f"❌ Invalid position! Choose 1 to {len(players)}")
            return
        
        current_batter_index = team_game.get("current_batter_index", 0)
        players[current_batter_index], players[position] = players[position], players[current_batter_index]
        team_game["current_batter_index"] = position
        team_game["current_batter"] = players[position].copy()
        
        await message.reply(f"✅ Batting order updated!\nNew batter at position {args[1]}: {players[position]['name']}")

    # ================= BOWLING COMMAND =================
    @app.on_message(filters.command("bowling") & filters.group)
    async def bowling_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        team_game = team_games.get(chat_id)
        
        if not team_game or team_game.get("status") != "playing":
            await message.reply("❌ No active team game found!")
            return
        
        is_captain_a = team_game.get("captain_a", {}).get("id") == user_id
        is_captain_b = team_game.get("captain_b", {}).get("id") == user_id
        
        if not (is_captain_a or is_captain_b):
            await message.reply("❌ Only team captains can change bowling order!")
            return
        
        args = message.command
        if len(args) < 2:
            await message.reply("❌ Usage: /bowling <position_number>\nExample: /bowling 2")
            return
        
        try:
            position = int(args[1]) - 1
        except ValueError:
            await message.reply("❌ Please provide a valid number!")
            return
        
        current_team = team_game.get("current_team", "A")
        team_key = f"team_{current_team.lower()}"
        players = team_game[team_key]
        
        if position < 0 or position >= len(players):
            await message.reply(f"❌ Invalid position! Choose 1 to {len(players)}")
            return
        
        current_bowler_index = team_game.get("current_bowler_index", 0)
        players[current_bowler_index], players[position] = players[position], players[current_bowler_index]
        team_game["current_bowler_index"] = position
        team_game["current_bowler"] = players[position].copy()
        
        await message.reply(f"✅ Bowling order updated!\nNew bowler at position {args[1]}: {players[position]['name']}")

    # ================= CAP CHANGE COMMAND =================
    @app.on_message(filters.command("cap_change") & filters.group)
    async def cap_change_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        team_game = team_games.get(chat_id)
        
        if not team_game:
            await message.reply("❌ No active team game found!")
            return
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can change captains!")
            return
        
        new_captain = None
        if message.reply_to_message:
            new_captain = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_captain = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not new_captain:
            await message.reply("❌ Usage: /cap_change @username or reply to a user's message")
            return
        
        team = None
        for player in team_game["team_a"]:
            if player["id"] == new_captain.id:
                team = "A"
                break
        for player in team_game["team_b"]:
            if player["id"] == new_captain.id:
                team = "B"
                break
        
        if not team:
            await message.reply(f"❌ {new_captain.first_name} is not in any team!")
            return
        
        if team == "A":
            team_game["captain_a"] = {"id": new_captain.id, "name": new_captain.first_name, "username": new_captain.username}
        else:
            team_game["captain_b"] = {"id": new_captain.id, "name": new_captain.first_name, "username": new_captain.username}
        
        await message.reply(f"✅ Team {team} captain changed to [{new_captain.first_name}](tg://user?id={new_captain.id})!")

    # ================= ADD CAP COMMAND =================
    @app.on_message(filters.command("add_cap") & filters.group)
    async def add_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        team_game = team_games.get(chat_id)
        
        if not team_game:
            await message.reply("❌ No active team game found!")
            return
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can add captains!")
            return
        
        new_captain = None
        if message.reply_to_message:
            new_captain = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                new_captain = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not new_captain:
            await message.reply("❌ Usage: /add_cap @username or reply to a user's message")
            return
        
        team = None
        for player in team_game["team_a"]:
            if player["id"] == new_captain.id:
                team = "A"
                break
        for player in team_game["team_b"]:
            if player["id"] == new_captain.id:
                team = "B"
                break
        
        if not team:
            await message.reply(f"❌ {new_captain.first_name} is not in any team!")
            return
        
        if team == "A" and team_game.get("captain_a"):
            await message.reply("❌ Team A already has a captain! Use /cap_change to change.")
            return
        elif team == "B" and team_game.get("captain_b"):
            await message.reply("❌ Team B already has a captain! Use /cap_change to change.")
            return
        
        if team == "A":
            team_game["captain_a"] = {"id": new_captain.id, "name": new_captain.first_name, "username": new_captain.username}
        else:
            team_game["captain_b"] = {"id": new_captain.id, "name": new_captain.first_name, "username": new_captain.username}
        
        await message.reply(f"✅ {new_captain.first_name} is now Team {team} Captain!")

    # ================= RM CAP COMMAND =================
    @app.on_message(filters.command("rm_cap") & filters.group)
    async def rm_cap_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        team_game = team_games.get(chat_id)
        
        if not team_game:
            await message.reply("❌ No active team game found!")
            return
        
        host = team_hosts.get(chat_id)
        if not host or host.get("id") != user_id:
            await message.reply("❌ Only game host can remove captains!")
            return
        
        rm_captain = None
        if message.reply_to_message:
            rm_captain = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                rm_captain = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not rm_captain:
            await message.reply("❌ Usage: /rm_cap @username or reply to a user's message")
            return
        
        removed = False
        if team_game.get("captain_a", {}).get("id") == rm_captain.id:
            team_game["captain_a"] = None
            removed = True
            team = "A"
        elif team_game.get("captain_b", {}).get("id") == rm_captain.id:
            team_game["captain_b"] = None
            removed = True
            team = "B"
        
        if removed:
            await message.reply(f"✅ {rm_captain.first_name} is no longer Team {team} Captain!")
        else:
            await message.reply(f"❌ {rm_captain.first_name} is not a captain!")

    # ================= END MATCH COMMAND =================
    @app.on_message(filters.command("end_match") & filters.group)
    async def end_match_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        is_group_admin = await is_admin(client, chat_id, user_id)
        if not is_group_admin:
            await message.reply("❌ Only group admins can end the match!")
            return
        
        solo_game = games.get(chat_id)
        if solo_game and solo_game.get("status") == "playing" and not solo_game.get("game_over"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, End Match", callback_data=f"end_solo_confirm_{chat_id}"),
                 InlineKeyboardButton("❌ No, Cancel", callback_data="end_cancel")]
            ])
            await message.reply("⚠️ **Are you sure you want to end the match?**", reply_markup=keyboard)
            return
        
        team_game = team_games.get(chat_id)
        if team_game and team_game.get("status") == "playing" and not team_game.get("game_over"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, End Match", callback_data=f"end_team_confirm_{chat_id}"),
                 InlineKeyboardButton("❌ No, Cancel", callback_data="end_cancel")]
            ])
            await message.reply("⚠️ **Are you sure you want to end the match?**", reply_markup=keyboard)
            return
        
        await message.reply("❌ No active game found to end!")

    # ================= END SOLO MATCH CONFIRM =================
    @app.on_callback_query(filters.regex("^end_solo_confirm_"))
    async def end_solo_confirm_callback(client, callback):
        chat_id = int(callback.data.split("_")[3])
        user_id = callback.from_user.id
        
        if not await is_admin(client, chat_id, user_id):
            await callback.answer("❌ Only group admins can end the match!", show_alert=True)
            return
        
        game = games.get(chat_id)
        if not game or game.get("status") != "playing":
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        game["game_over"] = True
        players = game["players"]
        
        await callback.message.delete()
        await client.send_message(chat_id, "🏏 **Match Ended!** 🏏")
        await client.send_message(chat_id, build_scoreboard(players, is_final=True))
        
        if chat_id in games:
            del games[chat_id]
        
        await callback.answer("✅ Match ended successfully!")

    # ================= END TEAM MATCH CONFIRM =================
    @app.on_callback_query(filters.regex("^end_team_confirm_"))
    async def end_team_confirm_callback(client, callback):
        chat_id = int(callback.data.split("_")[3])
        user_id = callback.from_user.id
        
        if not await is_admin(client, chat_id, user_id):
            await callback.answer("❌ Only group admins can end the match!", show_alert=True)
            return
        
        game = team_games.get(chat_id)
        if not game or game.get("status") != "playing":
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        game["game_over"] = True
        
        await callback.message.delete()
        await client.send_message(chat_id, "🏏 **Match Ended!** 🏏")
        await client.send_message(chat_id, build_team_scoreboard(game))
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        await callback.answer("✅ Match ended successfully!")

    # ================= END MATCH CANCEL =================
    @app.on_callback_query(filters.regex("^end_cancel$"))
    async def end_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Match end cancelled!")

    # ================= START DM =================
    @app.on_message(filters.command("start") & filters.private)
    async def start_dm(client, message: Message):
        user_id = message.from_user.id
        
        for chat_id, game in games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply("🎯 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
                    return
        
        for chat_id, game in team_games.items():
            if game.get("status") == "playing" and not game.get("game_over"):
                bowler = game.get("current_bowler", {})
                if bowler.get("id") == user_id and game.get("bowling_number") is None:
                    await message.reply("🎯 **Send bowling number (1-6)**\n\nExample: `4`\n\n⏰ You have 60 seconds!")
                    return
        
        await message.reply("🏏 **Welcome to Cricket Game Bot!**\n\nUse me in a group to play cricket games.\nAdd me to a group and use /start there!\n\n**Commands:**\n/start - Start game (Admin) or Vote (Member)\n/joingame - Join a solo game\n/score - Check live score")

    # ================= SELECT GAME MENU =================
    async def select_game_menu(client, message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Solo", callback_data="mode_solo"), InlineKeyboardButton("👥 Team", callback_data="mode_team")],
            [InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel")]
        ])
        
        caption = "🏏 **Select Game Mode** 🏏\n\nChoose how you want to play:"
        
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
        
        if action == "team":
            await callback.message.delete()
            await callback.answer("Opening Team Mode...")
            await team_mode_start(client, callback)
            return
        
        if action == "solo":
            await ball_selection_menu(client, callback)

    # ================= SOLO MODE =================
    async def ball_selection_menu(client, callback):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Solo Play - 1 Ball", callback_data="ball_1")],
            [InlineKeyboardButton("🎯 Solo Play - 3 Ball", callback_data="ball_3")]
        ])
        
        caption = "🏏 **Choose Bowling Mode** 🏏\n\n• Solo Play - 1 Ball (Single ball per bowler)\n• Solo Play - 3 Ball (Three balls per bowler)"
        
        await callback.message.delete()
        
        try:
            await callback.message.reply_photo(SOLO_PLAY_IMG, caption=caption, reply_markup=keyboard)
        except:
            await callback.message.reply(caption, reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^ball_"))
    async def ball_handler(client, callback: CallbackQuery):
        ball_mode = int(callback.data.split("_")[1])
        chat_id = callback.message.chat.id
        
        create_game(chat_id)
        game = games[chat_id]
        game["ball_mode"] = ball_mode
        game["mode"] = f"solo_{ball_mode}"
        
        await callback.message.delete()
        await client.send_message(chat_id, "🎉 Solo game created! Join the game using /joingame (2 minutes to join)\n⏰")
        asyncio.create_task(start_join_timer(client, chat_id))

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
            
            if players_count < 4:
                await client.send_message(chat_id, f"❌ Minimum 4 players required to start the game! 👥\n\nCurrent players: {players_count}/4\n⚠️ Game cancelled due to insufficient players.")
                if chat_id in games:
                    del games[chat_id]
            else:
                await client.send_message(chat_id, f"✅ Time's up! {players_count} players joined. Starting game...")
                await start_game_match(client, chat_id)

    @app.on_message(filters.command("joingame") & filters.group)
    async def join_game_cmd(client, message: Message):
        chat_id = message.chat.id
        game = games.get(chat_id)
        
        if not game:
            return await message.reply("❌ No active solo game! Use /start and select Solo mode first.")
        
        if game.get("status") != "waiting":
            return await message.reply("❌ Game already started!")
        
        if join_game(chat_id, message.from_user):
            players_count = len(game["players"])
            await message.reply(f"🎉 {message.from_user.first_name}, you've joined the solo game! (Player {players_count}) 👍")

    async def start_game_match(client, chat_id):
        game = games.get(chat_id)
        if not game or game["status"] != "waiting":
            return
        
        players_count = len(game["players"])
        
        if players_count < 4:
            await client.send_message(chat_id, f"❌ Minimum 4 players required to start the game! 👥\n\nCurrent players: {players_count}/4\n⚠️ Game cancelled!")
            if chat_id in games:
                del games[chat_id]
            return
        
        start_match(chat_id)
        game = games[chat_id]
        players = game["players"]
        
        host_text = "🏏 **SOLO CRICKET** 🏏\n\n**Players List:**\n"
        for i, p in enumerate(players, 1):
            host_text += f"{i}. [{p['name']}](tg://user?id={p['id']})\n"
        
        try:
            await client.send_photo(chat_id, HOST_IMAGE_URL, caption=host_text)
        except:
            await client.send_message(chat_id, host_text)
        
        batter = game["current_batter"]
        bowler = game["current_bowler"]
        
        await client.send_message(chat_id, f"🎯 Hey [{batter['name']}](tg://user?id={batter['id']}), now you're batter!")
        await client.send_message(chat_id, f"🎯 Hey [{bowler['name']}](tg://user?id={bowler['id']}), now you're bowling!")
        
        await asyncio.sleep(1)
        await send_bowling_video(client, chat_id, bowler)

    # ================= TEAM MODE =================
    async def team_mode_start(client, callback):
        chat_id = callback.message.chat.id
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]])
        caption = "🎉 **New Game Alert!** 🎉 \n\nWho will be the game host for this match? 🤔"
        
        try:
            await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
        except:
            await client.send_message(chat_id, caption, reply_markup=keyboard)
        await callback.answer()

    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        existing_game = team_games.get(chat_id)
        if existing_game and existing_game.get("status") == "playing":
            await callback.answer("❌ A match is currently in progress! Cannot change host.", show_alert=True)
            return
        
        if chat_id in team_games:
            del team_games[chat_id]
        if chat_id in team_hosts:
            del team_hosts[chat_id]
        
        team_hosts[chat_id] = {"id": user.id, "name": user.first_name, "username": user.username}
        
        team_games[chat_id] = {
            "host_id": user.id, "host_name": user.first_name, "status": "waiting_host",
            "team_a": [], "team_b": [], "captain_a": None, "captain_b": None,
            "toss_winner": None, "toss_decision": None, "overs": 0,
            "team_a_score": 0, "team_b_score": 0, "team_a_wickets": 0, "team_b_wickets": 0,
            "current_team": None, "target": None, "game_over": False, "winner": None,
            "match_start_time": None, "match_end_time": None, "total_balls": 0,
            "team_a_name": "Team A", "team_b_name": "Team B"
        }
        
        await callback.message.delete()
        
        try:
            await client.send_photo(chat_id, TEAM_CHAPU_IMG, caption=f"[{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏")
        except:
            await client.send_message(chat_id, f"[{user.first_name}](tg://user?id={user.id}) is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏")
        
        await callback.answer()

    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host:
            await message.reply("❌ No game host found! Start team mode first.")
            return
        
        if host["id"] != user_id:
            await message.reply("❌ Only the game host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "waiting_host":
            await message.reply("❌ Teams already created!")
            return
        
        game["status"] = "team_creation_a"
        await message.reply("🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n")
        asyncio.create_task(team_a_timer(client, chat_id))

    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game or game["status"] != "team_creation_a":
            await message.reply("❌ Team A is not open for joining!")
            return
        
        if host and host["id"] == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        if any(p["id"] == user.id for p in game["team_a"]):
            await message.reply("❌ You already joined Team A!")
            return
        
        if any(p["id"] == user.id for p in game["team_b"]):
            await message.reply("❌ You already joined Team B!")
            return
        
        game["team_a"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team A!")

    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            await client.send_message(chat_id, f"⏰ Time's up for Team A! ({len(game['team_a'])} players joined)\n\n🎉 Join Team B by sending /join_teamB 📣")
            asyncio.create_task(team_b_timer(client, chat_id))

    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b_cmd(client, message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)
        host = team_hosts.get(chat_id)
        
        if not game or game["status"] != "team_creation_b":
            await message.reply("❌ Team B is not open for joining!")
            return
        
        if host and host["id"] == user.id:
            await message.reply("❌ You are the host! Host cannot join any team.")
            return
        
        if any(p["id"] == user.id for p in game["team_b"]):
            await message.reply("❌ You already joined Team B!")
            return
        
        if any(p["id"] == user.id for p in game["team_a"]):
            await message.reply("❌ You already joined Team A!")
            return
        
        game["team_b"].append({
            "id": user.id, "name": user.first_name, "username": user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        await message.reply(f"✈️ [{user.first_name}](tg://user?id={user.id}) joined Team B!")

    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_b":
            game["status"] = "captain_selection"
            await client.send_message(chat_id, "👋 Hey, now members are joined the teams! 🎉 Choose Team captains user /choose_cap 📝")

    @app.on_message(filters.command("choose_cap") & filters.group)
    async def choose_cap_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only game host can start captain selection!")
            return
        
        game = team_games.get(chat_id)
        if not game:
            await message.reply("❌ No active game found!")
            return
        
        if game.get("captain_a") and game.get("captain_b"):
            await message.reply("❌ Captains already selected!")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏆 Choose Team A Captain", callback_data="choose_cap_a")],
            [InlineKeyboardButton("🏆 Choose Team B Captain", callback_data="choose_cap_b")]
        ])
        
        await message.reply("**Game Host, please choose captains for Team A and Team B:**\n\n", reply_markup=keyboard)

    @app.on_callback_query(filters.regex("^choose_cap_a$"))
    async def choose_cap_a_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_a"):
            await callback.answer("❌ Team A captain already selected!", show_alert=True)
            return
        
        for player in game["team_a"]:
            if player["id"] == user_id:
                game["captain_a"] = player
                await callback.answer(f"✅ {player['name']} is now Team A Captain!")
                break
        else:
            await callback.answer("❌ You are not in Team A!", show_alert=True)
            return
        
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏏 Choose Team B Captain 🏏", callback_data="choose_cap_b")]])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n✅ Team A Captain: {game['captain_a']['name']}\n⚠️ Team B Captain: Not selected yet\n\nTeam B members click 'Team B Captain' button to become captain.",
                reply_markup=keyboard
            )

    @app.on_callback_query(filters.regex("^choose_cap_b$"))
    async def choose_cap_b_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        if game.get("captain_b"):
            await callback.answer("❌ Team B captain already selected!", show_alert=True)
            return
        
        for player in game["team_b"]:
            if player["id"] == user_id:
                game["captain_b"] = player
                await callback.answer(f"✅ {player['name']} is now Team B Captain!")
                break
        else:
            await callback.answer("❌ You are not in Team B!", show_alert=True)
            return
        
        if game.get("captain_a") and game.get("captain_b"):
            await callback.message.delete()
            await start_toss(client, chat_id)
        else:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏏 Choose Team A Captain 🏏", callback_data="choose_cap_a")]])
            await callback.message.edit_text(
                f"🏏 **Captain Selection!** 🏏\n\n⚠️ Team A Captain: Not selected yet\n✅ Team B Captain: {game['captain_b']['name']}\n\nTeam A members click 'Team A Captain' button to become captain.",
                reply_markup=keyboard
            )

    async def start_toss(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 HEADS", callback_data="toss_heads")],
            [InlineKeyboardButton("🪙 TAILS", callback_data="toss_tails")]
        ])
        
        await client.send_message(chat_id, "Team Captains, choose Heads or Tails:\n\n", reply_markup=keyboard)
        game["status"] = "toss"

    @app.on_callback_query(filters.regex("^toss_"))
    async def toss_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "toss":
            await callback.answer("❌ No toss in progress!", show_alert=True)
            return
        
        if game["captain_a"]["id"] != user_id:
            await callback.answer("❌ Only Team A captain can do the toss!", show_alert=True)
            return
        
        choice = callback.data.split("_")[1]
        toss_result = random.choice(["heads", "tails"])
        
        cap_a_id = game['captain_a']['id']
        cap_a_name = game['captain_a']['name']
        cap_a_username = game['captain_a'].get('username')
        cap_a_display = f"@{cap_a_username}" if cap_a_username else cap_a_name
        
        cap_b_id = game['captain_b']['id']
        cap_b_name = game['captain_b']['name']
        cap_b_username = game['captain_b'].get('username')
        cap_b_display = f"@{cap_b_username}" if cap_b_username else cap_b_name
        
        toss_video_url = TOSS_VIDEO
        await callback.message.delete()
        
        cap_a_clickable = f"[{cap_a_display}](tg://user?id={cap_a_id})"
        cap_b_clickable = f"[{cap_b_display}](tg://user?id={cap_b_id})"
        
        if choice == toss_result:
            winner_clickable = cap_a_clickable
            winner_team = "A"
        else:
            winner_clickable = cap_b_clickable
            winner_team = "B"
        
        caption_text = f"🪙 The coin shows: {toss_result.upper()}!\n\n🅰️ - {cap_a_clickable} chose {choice.upper()}\n🅱️ {cap_b_clickable} got {toss_result.upper()}\n\n🏆 {winner_clickable} from Team {winner_team} won the toss!\n\n🏆 {winner_clickable}, please choose to Bat or Bowl:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 BAT FIRST", callback_data="toss_bat")],
            [InlineKeyboardButton("⚾ BOWL FIRST", callback_data="toss_bowl")]
        ])
        
        await client.send_video(chat_id, toss_video_url, caption=caption_text, reply_markup=keyboard)
        game["toss_winner"] = winner_team

    @app.on_callback_query(filters.regex("^toss_bat$|^toss_bowl$"))
    async def toss_decision_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ No active game found!", show_alert=True)
            return
        
        decision = callback.data.split("_")[1]
        toss_winner = game.get("toss_winner")
        
        if toss_winner == "A" and game["captain_a"]["id"] != user_id:
            await callback.answer("❌ Only Team A captain can decide!", show_alert=True)
            return
        elif toss_winner == "B" and game["captain_b"]["id"] != user_id:
            await callback.answer("❌ Only Team B captain can decide!", show_alert=True)
            return
        
        game["toss_decision"] = decision
        batting_team = toss_winner if decision == "bat" else ("A" if toss_winner == "B" else "B")
        
        await callback.message.delete()
        await select_overs(client, chat_id, batting_team)

    async def select_overs(client, chat_id, batting_team):
        game = team_games.get(chat_id)
        if not game:
            return
        
        buttons = []
        row = []
        for i in range(1, 21):
            row.append(InlineKeyboardButton(f"{i}", callback_data=f"over_{i}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(buttons)
        await client.send_message(chat_id, "📊 **Select number of overs:**\n\nChoose overs (1 to 20 overs per side):", reply_markup=keyboard)
        
        game["status"] = "over_selection"
        game["batting_first"] = batting_team

    @app.on_callback_query(filters.regex("^over_"))
    async def over_selection_callback(client, callback):
        chat_id = callback.message.chat.id
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "over_selection":
            await callback.answer("❌ No over selection in progress!", show_alert=True)
            return
        
        overs = int(callback.data.split("_")[1])
        game["overs"] = overs
        game["total_balls_limit"] = overs * 6
        
        await callback.message.delete()
        
        batting_team = game["batting_first"]
        team_name = "Team A" if batting_team == "A" else "Team B"
        
        await client.send_message(chat_id, f"✅ Match set! {overs} overs per side.\n\n🚀 Match is starting...\n🏏 {team_name} will bat first!\n\nLet the game begin! 🎉")
        
        game["match_start_time"] = datetime.now()
        game["status"] = "playing"
        
        await start_team_batting(client, chat_id, batting_team)

    async def start_team_batting(client, chat_id, team):
        game = team_games.get(chat_id)
        if not game:
            return
        
        team_key = f"team_{team.lower()}"
        players = game[team_key]
        
        for p in players:
            p["score"] = 0
            p["balls"] = 0
            p["fours"] = 0
            p["sixes"] = 0
            p["out"] = False
            p["history"] = []
        
        game["current_team"] = team
        game["current_batter_index"] = 0
        game["current_batter"] = players[0].copy()
        
        if len(players) == 1:
            game["current_bowler_index"] = 0
            game["current_bowler"] = players[0].copy()
        else:
            game["current_bowler_index"] = 1 if len(players) > 1 else 0
            game["current_bowler"] = players[game["current_bowler_index"]].copy()
        
        game["current_bowler_balls"] = 0
        game["bowling_number"] = None
        game["team_total"] = 0
        game["team_wickets"] = 0
        game["total_balls_in_inning"] = 0
        
        batter_clickable = f"[{game['current_batter']['name']}](tg://user?id={game['current_batter']['id']})"
        bowler_clickable = f"[{game['current_bowler']['name']}](tg://user?id={game['current_bowler']['id']})"
        
        await client.send_message(chat_id, f"🏏 **Team {team} Batting**\n\nBatter: {batter_clickable}\nBowler: {bowler_clickable}")
        await send_bowling_video_team(client, chat_id, game["current_bowler"])

    # ================= ADD TO TEAM A/B =================
    @app.on_message(filters.command("add_A") & filters.group)
    async def add_to_team_a_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team A!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_a", "team_creation_b", "captain_selection"]:
            await message.reply("❌ Cannot add players now!")
            return
        
        added_user = None
        if message.reply_to_message:
            added_user = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                added_user = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not added_user:
            await message.reply("❌ Usage: /add_A @username or reply to a user's message")
            return
        
        if any(p["id"] == added_user.id for p in game["team_a"]):
            await message.reply(f"❌ {added_user.first_name} already in Team A!")
            return
        
        if any(p["id"] == added_user.id for p in game["team_b"]):
            await message.reply(f"❌ {added_user.first_name} already in Team B!")
            return
        
        game["team_a"].append({
            "id": added_user.id, "name": added_user.first_name, "username": added_user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current = len(game["team_a"])
        username_display = f"@{added_user.username}" if added_user.username else added_user.first_name
        await message.reply(f"added {username_display} to Team A! ({current} players)")

    @app.on_message(filters.command("add_B") & filters.group)
    async def add_to_team_b_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can add players to Team B!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_b", "captain_selection"]:
            await message.reply("❌ Cannot add players to Team B now!")
            return
        
        added_user = None
        if message.reply_to_message:
            added_user = message.reply_to_message.from_user
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                added_user = await client.get_users(username)
            except:
                await message.reply(f"❌ User @{username} not found!")
                return
        
        if not added_user:
            await message.reply("❌ Usage: /add_B @username or reply to a user's message")
            return
        
        if any(p["id"] == added_user.id for p in game["team_b"]):
            await message.reply(f"❌ {added_user.first_name} already in Team B!")
            return
        
        if any(p["id"] == added_user.id for p in game["team_a"]):
            await message.reply(f"❌ {added_user.first_name} already in Team A!")
            return
        
        game["team_b"].append({
            "id": added_user.id, "name": added_user.first_name, "username": added_user.username,
            "score": 0, "balls": 0, "fours": 0, "sixes": 0, "out": False, "history": []
        })
        
        current = len(game["team_b"])
        username_display = f"@{added_user.username}" if added_user.username else added_user.first_name
        await message.reply(f"added {username_display} to Team B! ({current} players)")

    @app.on_message(filters.command("shift_Team") & filters.group)
    async def shift_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await message.reply("❌ Only host can shift players between teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] not in ["team_creation_a", "team_creation_b", "captain_selection"]:
            await message.reply("❌ Cannot shift players now!")
            return
        
        if not message.reply_to_message:
            await message.reply("❌ Please reply to a user's message to shift them!")
            return
        
        user_to_shift = message.reply_to_message.from_user
        username_display = f"@{user_to_shift.username}" if user_to_shift.username else user_to_shift.first_name
        
        in_team_a = any(p["id"] == user_to_shift.id for p in game["team_a"])
        
        if not in_team_a:
            in_team_b = any(p["id"] == user_to_shift.id for p in game["team_b"])
            if not in_team_b:
                await message.reply(f"❌ {username_display} is not in any team!")
                return
            current_team = "B"
            target_team = "A"
        else:
            current_team = "A"
            target_team = "B"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Confirm shift to Team {target_team}", callback_data=f"shift_confirm_{user_to_shift.id}_{current_team}_{target_team}"),
             InlineKeyboardButton("Cancel", callback_data="shift_cancel")]
        ])
        
        await message.reply(f"🔄 {username_display} is currently in Team {current_team}.\nDo you want to shift them to Team {target_team}?", reply_markup=keyboard)

    @app.on_callback_query(filters.regex("^shift_confirm_"))
    async def shift_confirm_callback(client, callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        host = team_hosts.get(chat_id)
        if not host or host["id"] != user_id:
            await callback.answer("❌ Only host can confirm shift!", show_alert=True)
            return
        
        game = team_games.get(chat_id)
        if not game:
            await callback.answer("❌ Game not found!", show_alert=True)
            return
        
        data = callback.data.split("_")
        user_to_shift_id = int(data[2])
        current_team = data[3]
        target_team = data[4]
        
        player = None
        if current_team == "A":
            for i, p in enumerate(game["team_a"]):
                if p["id"] == user_to_shift_id:
                    player = game["team_a"].pop(i)
                    game["team_b"].append(player)
                    break
        else:
            for i, p in enumerate(game["team_b"]):
                if p["id"] == user_to_shift_id:
                    player = game["team_b"].pop(i)
                    game["team_a"].append(player)
                    break
        
        if not player:
            await callback.answer("❌ Player not found!", show_alert=True)
            return
        
        username_display = f"@{player['username']}" if player['username'] else player['name']
        
        await callback.message.delete()
        await callback.message.reply(f"🔄 {username_display} shifted from Team {current_team} to Team {target_team}!\n\n🏏 Team A: {len(game['team_a'])} players\n🏏 Team B: {len(game['team_b'])} players")
        await callback.answer("✅ Player shifted successfully!")

    @app.on_callback_query(filters.regex("^shift_cancel$"))
    async def shift_cancel_callback(client, callback):
        await callback.message.delete()
        await callback.answer("❌ Shift cancelled!")

    # ================= BOWLING DM =================
    @app.on_message(filters.private & filters.text)
    async def bowling_dm(client, message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        if text.startswith("/start"):
            return
        
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        num = int(text)
        
        # Solo mode
        for chat_id, game in games.items():
            if game.get("status") != "playing" or game.get("game_over"):
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            if game.get("bowling_number") is not None:
                await message.reply("❌ You already bowled! Wait for your next turn.")
                return
            
            if chat_id in bowling_tasks:
                bowling_tasks[chat_id].cancel()
                del bowling_tasks[chat_id]
            
            set_bowling(chat_id, num)
            await message.reply(f"✅ Bowling number {num} sent to game!")
            
            batter = game["current_batter"]
            batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
            await client.send_video(chat_id, BATTING_VIDEO, caption=f"Hey {batter_clickable}, now you're batting! Send number (1-6) in GROUP")
            return
        
        # Team mode
        for chat_id, game in team_games.items():
            if game.get("status") != "playing" or game.get("game_over"):
                continue
            if game.get("current_bowler", {}).get("id") != user_id:
                continue
            if game.get("bowling_number") is not None:
                await message.reply("❌ You already bowled! Wait for your next turn.")
                return
            
            if chat_id in bowling_tasks:
                bowling_tasks[chat_id].cancel()
                del bowling_tasks[chat_id]
            
            game["bowling_number"] = num
            await message.reply(f"✅ Bowling number {num} sent to game!")
            
            batter = game["current_batter"]
            batter_clickable = f"[{batter['name']}](tg://user?id={batter['id']})"
            await client.send_message(chat_id, f"🎯 Bowler bowled {num}! Now {batter_clickable}, send your batting number (1-6) in GROUP")
            return
        
        await message.reply("❌ No active game found where you are the bowler!")

    # ================= BATTING =================
    @app.on_message(filters.group & filters.text & ~filters.bot)
    async def batting_msg(client, message):
        chat_id = message.chat.id
        
        # Solo mode
        game = games.get(chat_id)
        if game:
            if game.get("status") != "playing" or game.get("game_over") or game.get("bowling_number") is None:
                return
            
            batter = game.get("current_batter")
            if not batter or message.from_user.id != batter.get("id"):
                return
            
            text = message.text.strip()
            if not text.isdigit() or int(text) not in range(1, 7):
                return await message.reply(INVALID_NUMBER)
            
            try:
                await message.reply("👍")
            except:
                pass
            
            bat = int(text)
            result = play_ball(chat_id, bat)
            bow = game.get("bowling_number", "?")
            game["bowling_number"] = None
            bowler = game["current_bowler"]
            
            if result["type"] == "out":
                try:
                    await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
                except:
                    await message.reply(OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
                
                if game.get("game_over"):
                    await message.reply(build_scoreboard(game["players"], is_final=True))
                    if chat_id in games:
                        del games[chat_id]
                    return
                
                await message.reply(build_scoreboard(game["players"], is_final=False))
                
                new_batter = game["current_batter"]
                new_bowler = game["current_bowler"]
                await client.send_message(chat_id, f"🎯 New batter: [{new_batter['name']}](tg://user?id={new_batter['id']})\n🎯 New bowler: [{new_bowler['name']}](tg://user?id={new_bowler['id']})")
                await send_bowling_video(client, chat_id, game["current_bowler"])
            else:
                try:
                    await message.reply_video(get_run_video(result["runs"]))
                except:
                    await message.reply_video(get_run_video(result["runs"]))
                
                if not game.get("game_over"):
                    await send_bowling_video(client, chat_id, bowler)
            return
        
        # Team mode
        team_game = team_games.get(chat_id)
        if not team_game:
            return
        
        if team_game.get("status") != "playing" or team_game.get("game_over") or team_game.get("bowling_number") is None:
            return
        
        batter = team_game.get("current_batter")
        if not batter or message.from_user.id != batter.get("id"):
            return
        
        text = message.text.strip()
        if not text.isdigit() or int(text) not in range(1, 7):
            return await message.reply(INVALID_NUMBER)
        
        try:
            await message.reply("👍")
        except:
            pass
        
        bat = int(text)
        bow = team_game.get("bowling_number", "?")
        team_game["bowling_number"] = None
        bowler = team_game["current_bowler"]
        team_key = f"team_{team_game['current_team'].lower()}"
        
        if bat == bow:
            batter["out"] = True
            team_game["team_wickets"] += 1
            
            try:
                await message.reply_video(OUT_VIDEO, caption=OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            except:
                await message.reply(OUT_MESSAGE.format(batter=batter["name"], bat=bat, bowler=bowler["name"], bowl=bow))
            
            active_batters = [p for p in team_game[team_key] if not p.get("out", False)]
            
            if not active_batters or team_game["team_wickets"] >= len(team_game[team_key]):
                team_game["status"] = "innings_break"
                
                if team_game["current_team"] == "A":
                    team_game["team_a_score"] = team_game["team_total"]
                    team_game["team_a_wickets"] = team_game["team_wickets"]
                    await client.send_message(chat_id, f"🏏 **Team A Innings Complete!**\n\nTotal: {team_game['team_a_score']}/{team_game['team_a_wickets']}\n\nTeam B needs {team_game['team_a_score'] + 1} runs to win!\n\nStarting Team B innings...")
                    await start_team_batting(client, chat_id, "B")
                else:
                    team_game["team_b_score"] = team_game["team_total"]
                    team_game["team_b_wickets"] = team_game["team_wickets"]
                    
                    if team_game["team_b_score"] > team_game["team_a_score"]:
                        winner = "Team B"
                    elif team_game["team_b_score"] < team_game["team_a_score"]:
                        winner = "Team A"
                    else:
                        winner = "Match Tied"
                    
                    team_game["game_over"] = True
                    team_game["winner"] = winner
                    await client.send_message(chat_id, build_team_scoreboard(team_game))
                    await client.send_message(chat_id, f"🏆 **Match Over!**\n\nWinner: {winner}\n\nTeam A: {team_game['team_a_score']}/{team_game['team_a_wickets']}\nTeam B: {team_game['team_b_score']}/{team_game['team_b_wickets']}")
                    
                    if chat_id in team_games:
                        del team_games[chat_id]
                    if chat_id in team_hosts:
                        del team_hosts[chat_id]
                return
            
            # Find next batter
            next_batter_index = team_game["current_batter_index"] + 1
            for i in range(next_batter_index, len(team_game[team_key])):
                if not team_game[team_key][i].get("out", False):
                    team_game["current_batter_index"] = i
                    team_game["current_batter"] = team_game[team_key][i].copy()
                    await client.send_message(chat_id, f"🎯 New batter: [{team_game['current_batter']['name']}](tg://user?id={team_game['current_batter']['id']})")
                    break
            
            await client.send_message(chat_id, build_team_scoreboard(team_game))
            team_game["current_bowler_balls"] += 1
            team_game["total_balls_in_inning"] += 1
            
            if team_game["current_bowler_balls"] >= 6:
                players = team_game[team_key]
                new_bowler_index = (team_game["current_bowler_index"] + 1) % len(players)
                team_game["current_bowler_index"] = new_bowler_index
                team_game["current_bowler"] = players[new_bowler_index].copy()
                team_game["current_bowler_balls"] = 0
                await client.send_message(chat_id, f"🔄 New bowler: [{team_game['current_bowler']['name']}](tg://user?id={team_game['current_bowler']['id']})")
            
            await send_bowling_video_team(client, chat_id, team_game["current_bowler"])
        else:
            runs = bat
            batter["score"] += runs
            batter["balls"] += 1
            if runs == 4:
                batter["fours"] += 1
            elif runs == 6:
                batter["sixes"] += 1
            batter["history"].append(f"{runs}")
            team_game["team_total"] += runs
            team_game["total_balls_in_inning"] += 1
            
            try:
                await message.reply_video(get_run_video(runs))
            except:
                await message.reply_video(get_run_video(runs))
            
            if team_game["current_team"] == "B" and team_game["team_total"] > team_game["team_a_score"]:
                team_game["team_b_score"] = team_game["team_total"]
                team_game["game_over"] = True
                team_game["winner"] = "Team B"
                await client.send_message(chat_id, build_team_scoreboard(team_game))
                await client.send_message(chat_id, f"🏆 **Team B Wins!**\n\nTarget: {team_game['team_a_score'] + 1}\nTeam B: {team_game['team_b_score']}\n\nTeam B wins!")
                
                if chat_id in team_games:
                    del team_games[chat_id]
                if chat_id in team_hosts:
                    del team_hosts[chat_id]
                return
            
            await client.send_message(chat_id, build_team_scoreboard(team_game))
            team_game["current_bowler_balls"] += 1
            
            if team_game["current_bowler_balls"] >= 6:
                players = team_game[team_key]
                new_bowler_index = (team_game["current_bowler_index"] + 1) % len(players)
                team_game["current_bowler_index"] = new_bowler_index
                team_game["current_bowler"] = players[new_bowler_index].copy()
                team_game["current_bowler_balls"] = 0
                await client.send_message(chat_id, f"🔄 New bowler: [{team_game['current_bowler']['name']}](tg://user?id={team_game['current_bowler']['id']})")
            
            await send_bowling_video_team(client, chat_id, team_game["current_bowler"])

    # ================= VOTE SYSTEM =================
    async def vote_system(client, message):
        chat_id = message.chat.id
        
        if chat_id in active_votes and active_votes[chat_id].get("active"):
            await message.reply(f"Voting in progress! Votes: {active_votes[chat_id]['count']}/3")
            return
        
        active_votes[chat_id] = {"active": True, "count": 0, "users": [], "msg_id": None}
        
        caption = "🗳️ **VOTING REQUIRED!** 🗳️\n\nYou are not an admin. 3 votes needed.\n\nCurrent votes: 0/3"
        
        try:
            msg = await message.reply_photo(VOTE_IMG, caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
        except:
            msg = await message.reply(caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
        
        active_votes[chat_id]["msg_id"] = msg.id
        asyncio.create_task(auto_cancel_vote(client, chat_id))

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
        
        if vote["count"] >= 3:
            await callback.message.delete()
            await select_game_menu(client, callback.message)
            vote["active"] = False
            await callback.answer("Voting successful!")
        else:
            voters = []
            for uid in vote["users"]:
                try:
                    u = await client.get_users(uid)
                    voters.append(f"• {u.first_name}")
                except:
                    voters.append(f"• User_{uid}")
            
            caption = f"🗳️ **VOTING REQUIRED!** 🗳️\n\nYou are not an admin. 3 votes needed.\n\nCurrent votes: {vote['count']}/3\n\n**Voters:**\n{chr(10).join(voters)}"
            
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
            except:
                await callback.message.edit_text(caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Vote to Start", callback_data="vote")]]))
            await callback.answer(f"Voted! ({vote['count']}/3)")

    async def auto_cancel_vote(client, chat_id):
        await asyncio.sleep(60)
        vote = active_votes.get(chat_id)
        if vote and vote.get("active") and vote["count"] < 3:
            try:
                await client.edit_message_caption(chat_id, vote["msg_id"], caption=f"❌ Voting expired! Got {vote['count']}/3 votes.\nUse /start again.")
            except:
                pass
            vote["active"] = False
