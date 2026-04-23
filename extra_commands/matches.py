from pyrogram import filters
from pyrogram.types import Message
from solo.game import games
from solo.handlers import team_games
from datetime import datetime

def register_matches(app):

    @app.on_message(filters.command(["matches"], prefixes=["/"]) & filters.group)
    async def matches_cmd(client, message: Message):
        print("🔥 matches command triggered")  # debug

        chat_id = message.chat.id

        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)

        if not solo_game and not team_game:
            await message.reply("❌ No active matches in this group!")
            return

        matches_text = "🏏 **ACTIVE MATCHES** 🏏\n\n"

        # ================= SOLO =================
        if solo_game:
            status = solo_game.get("status", "unknown")
            players_count = len(solo_game.get("players", []))

            match_start_time = solo_game.get("start_time")
            if isinstance(match_start_time, (int, float)):
                match_start_time = datetime.fromtimestamp(match_start_time).strftime('%H:%M:%S')
            else:
                match_start_time = "N/A"

            matches_text += "**SOLO MODE**\n"
            matches_text += f"📊 Status: {status.upper()}\n"
            matches_text += f"👥 Players: {players_count}\n"
            matches_text += f"⏰ Started: {match_start_time}\n"
            matches_text += f"🎯 Ball Mode: {solo_game.get('ball_mode', 3)} balls\n\n"

        # ================= TEAM =================
        if team_game:
            status = team_game.get("status", "unknown")
            team_a_count = len(team_game.get("team_a", []))
            team_b_count = len(team_game.get("team_b", []))
            overs = team_game.get("overs", 0)

            matches_text += "**TEAM MODE**\n"
            matches_text += f"📊 Status: {status.upper()}\n"
            matches_text += f"🏏 Team A: {team_a_count} players\n"
            matches_text += f"🏏 Team B: {team_b_count} players\n"
            matches_text += f"🎯 Overs: {overs}\n"

        await message.reply(matches_text, disable_web_page_preview=True)
