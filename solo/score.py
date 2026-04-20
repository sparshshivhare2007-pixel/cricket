# solo/score.py - Live Score Module (Solo + Team)

from solo.game import games
from solo.scoreboard import build_scoreboard
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LIVE_SCORE_LINK, SOLO_ICONS

def build_solo_scoreboard(players, is_final=False):
    """Build solo scoreboard text from players list"""
    if not players:
        return "📊 No players yet!"
    
    text = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"
    
    if is_final:
        sorted_players = sorted(players, key=lambda x: x.get('score', 0), reverse=True)
    else:
        sorted_players = players

    for i, p in enumerate(sorted_players, start=1):
        icon = SOLO_ICONS[i % len(SOLO_ICONS)]
        history = ", ".join(map(str, p["history"][-5:]))
        
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        fours = p.get('fours', 0)
        sixes = p.get('sixes', 0)
        out_status = "❌" if p.get('out', False) else ""
        
        text += f"{i}. {icon} {p['name']} {out_status}= {runs}({balls})\n"
        text += f"    ╰⊚ 4️⃣s: {fours:02}, 6️⃣s: {sixes:02} - ID: `{p['id']}`\n"
        
        if history and not is_final:
            text += f"      ╰⊚ ({history})\n"
        
        text += "\n"
    
    if is_final:
        winner = max(players, key=lambda x: x.get('score', 0))
        text += f"─────⊱ Rᴇsᴜʟᴛ ⊰─────\n"
        text += f"🏆 Wɪɴɴᴇʀ: {winner['name']}\n"
        text += f"📊 Sᴄᴏʀᴇ: {winner['score']} runs"
        if winner.get('balls', 0) > 0:
            text += f" ({winner['balls']} balls)"
        text += "\n"
    
    return text

def build_team_scoreboard(game):
    """Build team scoreboard text"""
    team_a = game.get("team_a", [])
    team_b = game.get("team_b", [])
    team_a_score = game.get("team_a_score", 0)
    team_b_score = game.get("team_b_score", 0)
    team_a_wickets = game.get("team_a_wickets", 0)
    team_b_wickets = game.get("team_b_wickets", 0)
    current_team = game.get("current_team", "A")
    target = game.get("target", None)
    
    text = "─────⊱ Tᴇᴀᴍ Sᴄᴏʀᴇʙᴏᴀʀᴅ ⊰────\n\n"
    
    # Team A
    text += f"🏏 **TEAM A** - {team_a_score}/{team_a_wickets}\n"
    for i, p in enumerate(team_a[:5], 1):
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        out_status = "❌" if p.get('out', False) else ""
        text += f"   {i}. {p['name']} {out_status} = {runs}({balls})\n"
    if len(team_a) > 5:
        text += f"   ... and {len(team_a)-5} more\n"
    
    text += f"\n🏏 **TEAM B** - {team_b_score}/{team_b_wickets}\n"
    for i, p in enumerate(team_b[:5], 1):
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        out_status = "❌" if p.get('out', False) else ""
        text += f"   {i}. {p['name']} {out_status} = {runs}({balls})\n"
    if len(team_b) > 5:
        text += f"   ... and {len(team_b)-5} more\n"
    
    if target:
        text += f"\n🎯 **Target:** {target} runs\n"
    
    text += f"\n🟢 **Batting:** Team {current_team}\n"
    
    return text

async def get_live_score(client, message):
    """Unified live score - works for both solo and team mode"""
    chat_id = message.chat.id
    
    # Create inline button for live score link
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏏 Live Cricket Score", url=LIVE_SCORE_LINK)]
    ])
    
    # Check for SOLO mode first
    solo_game = games.get(chat_id)
    if solo_game:
        if solo_game.get("status") == "waiting":
            players_count = len(solo_game.get("players", []))
            ball_mode = solo_game.get("ball_mode", "Not selected")
            text = f"⏳ **SOLO MODE - Waiting**\n\n👥 Players joined: {players_count}\n🎯 Ball Mode: {ball_mode} Ball{'s' if ball_mode != 1 else ''}\n\nSend `/joingame` to join!"
        elif solo_game.get("status") == "playing" and not solo_game.get("game_over"):
            text = build_solo_scoreboard(solo_game["players"], is_final=False)
        elif solo_game.get("game_over"):
            text = build_solo_scoreboard(solo_game["players"], is_final=True)
        else:
            text = "📊 No active game!"
        
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
        return
    
    # Check for TEAM mode
    team_game = team_games.get(chat_id)
    if team_game:
        if team_game.get("status") == "waiting_host":
            text = f"⏳ **TEAM MODE - Waiting for Host**\n\n👑 Host: {team_game.get('host_name', 'Unknown')}\n\nHost type `/create_team` to start!"
        elif team_game.get("status") in ["team_creation_a", "team_creation_b"]:
            team_a_count = len(team_game.get("team_a", []))
            team_b_count = len(team_game.get("team_b", []))
            text = f"🎯 **TEAM MODE - Team Creation**\n\n🏏 Team A: {team_a_count} players\n🏏 Team B: {team_b_count} players"
        elif team_game.get("status") == "ready":
            team_a_count = len(team_game.get("team_a", []))
            team_b_count = len(team_game.get("team_b", []))
            text = f"✅ **TEAM MODE - Teams Ready**\n\n🏏 Team A: {team_a_count} players\n🏏 Team B: {team_b_count} players\n\nType `/start_match` to begin!"
        elif team_game.get("status") == "playing" and not team_game.get("game_over"):
            text = build_team_scoreboard(team_game)
        elif team_game.get("game_over"):
            winner = team_game.get("winner", "Unknown")
            text = f"🏆 **GAME OVER** 🏆\n\n🏅 Winner: {winner}\n\nUse /start to play again!"
        else:
            text = "📊 No active game!"
        
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
        return
    
    # No active game
    await message.reply("❌ No active game in this chat!\n\nUse /start to create a game.", reply_markup=keyboard)
