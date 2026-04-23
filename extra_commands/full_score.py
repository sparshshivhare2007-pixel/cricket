from pyrogram import filters
from pyrogram.types import Message
from solo.game import games, build_scoreboard
from solo.handlers import team_games

def register_full_score(app):

    @app.on_message(filters.command(["full_score"], prefixes=["/"]) & filters.group)
    async def full_score_cmd(client, message: Message):
        print("🔥 full_score command triggered")  # debug

        chat_id = message.chat.id

        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)

        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return

        # ================= SOLO GAME =================
        if solo_game:
            players = solo_game.get("players", [])
            if players:
                score_text = build_scoreboard(players, is_final=False)
                await message.reply(score_text)
            else:
                await message.reply("❌ No players in solo game!")

        # ================= TEAM GAME =================
        if team_game:
            score_text = "🏏 **COMPLETE SCOREBOARD** 🏏\n\n"

            # -------- TEAM A --------
            score_text += "**TEAM A:**\n"
            for p in team_game.get("team_a", []):
                status = "❌" if p.get("out", False) else "🏏"
                name = f"@{p.get('username')}" if p.get('username') else p.get('name', 'Unknown')

                score_text += f"{status} {name}: {p.get('score', 0)} ({p.get('balls', 0)} balls)"

                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    score_text += f" [4s:{p.get('fours', 0)} 6s:{p.get('sixes', 0)}]"

                score_text += "\n"

            score_text += (
                f"\n**Team A Total:** {team_game.get('team_a_score', 0)}/"
                f"{team_game.get('team_a_wickets', 0)}\n\n"
            )

            # -------- TEAM B --------
            score_text += "**TEAM B:**\n"
            for p in team_game.get("team_b", []):
                status = "❌" if p.get("out", False) else "🏏"
                name = f"@{p.get('username')}" if p.get('username') else p.get('name', 'Unknown')

                score_text += f"{status} {name}: {p.get('score', 0)} ({p.get('balls', 0)} balls)"

                if p.get('fours', 0) > 0 or p.get('sixes', 0) > 0:
                    score_text += f" [4s:{p.get('fours', 0)} 6s:{p.get('sixes', 0)}]"

                score_text += "\n"

            score_text += (
                f"\n**Team B Total:** {team_game.get('team_b_score', 0)}/"
                f"{team_game.get('team_b_wickets', 0)}"
            )

            await message.reply(score_text, disable_web_page_preview=True)
