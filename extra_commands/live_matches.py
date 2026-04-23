from pyrogram import filters
from pyrogram.types import Message
from solo.game import games
from solo.handlers import team_games

def register_live_matches(app):

    @app.on_message(filters.command(["live_matches"], prefixes=["/"]) & filters.group)
    async def live_matches_cmd(client, message: Message):
        print("🔥 live_matches command triggered")  # debug

        chat_id = message.chat.id

        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)

        if not solo_game and not team_game:
            await message.reply("❌ No live matches in this group!")
            return

        live_text = "🔥 **LIVE MATCHES** 🔥\n\n"
        has_live = False  # important flag

        # ================= SOLO =================
        if solo_game and solo_game.get("status") == "playing":
            has_live = True

            batter = solo_game.get("current_batter", {})
            bowler = solo_game.get("current_bowler", {})
            players = solo_game.get("players", [])

            active_players = len([p for p in players if not p.get("out", False)])

            live_text += "**SOLO MODE - LIVE**\n"
            live_text += f"🏏 Current Batter: {batter.get('name', 'N/A')}\n"
            live_text += f"⚾ Current Bowler: {bowler.get('name', 'N/A')}\n"
            live_text += f"📊 Total Balls: {solo_game.get('total_balls_in_match', 0)}\n"
            live_text += f"👥 Active Players: {active_players}\n\n"

        # ================= TEAM =================
        if team_game and team_game.get("status") == "playing":
            has_live = True

            current_team = team_game.get("current_team", "N/A")
            batter = team_game.get("current_batter", {})
            bowler = team_game.get("current_bowler", {})

            live_text += "**TEAM MODE - LIVE**\n"
            live_text += f"🏏 Batting Team: Team {current_team}\n"
            live_text += f"🏏 Current Batter: {batter.get('name', 'N/A')}\n"
            live_text += f"⚾ Current Bowler: {bowler.get('name', 'N/A')}\n"
            live_text += f"📊 Team A: {team_game.get('team_a_score', 0)}/{team_game.get('team_a_wickets', 0)}\n"
            live_text += f"📊 Team B: {team_game.get('team_b_score', 0)}/{team_game.get('team_b_wickets', 0)}\n"

        # ❗ FIX: agar game exist hai but playing nahi hai
        if not has_live:
            await message.reply("❌ No match is currently live!")
            return

        await message.reply(live_text, disable_web_page_preview=True)
