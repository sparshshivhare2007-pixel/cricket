from pyrogram import filters
from pyrogram.types import Message
from solo.handlers import team_games

def register_batting(app):

    @app.on_message(filters.command(["batting"], prefixes=["/"]) & filters.group)
    async def batting_cmd(client, message: Message):
        print("🔥 batting command triggered")  # debug

        chat_id = message.chat.id
        user_id = message.from_user.id

        team_game = team_games.get(chat_id)
        if not team_game or team_game.get("status") != "playing":
            await message.reply("❌ No active team game found!")
            return

        # Check if user is captain
        is_captain_a = team_game.get("captain_a", {}).get("id") == user_id
        is_captain_b = team_game.get("captain_b", {}).get("id") == user_id

        if not (is_captain_a or is_captain_b):
            await message.reply("❌ Only team captains can change batting order!")
            return

        # Get args safely
        args = message.command
        if not args or len(args) < 2:
            await message.reply("❌ Usage: /batting <position_number>\nExample: /batting 3")
            return

        # Convert position
        try:
            position = int(args[1]) - 1
        except Exception:
            await message.reply("❌ Please provide a valid number!")
            return

        # Get current team
        current_team = team_game.get("current_team", "A")
        team_key = f"team_{current_team.lower()}"
        players = team_game.get(team_key, [])

        if not players:
            await message.reply("❌ No players found in current team!")
            return

        if position < 0 or position >= len(players):
            await message.reply(f"❌ Invalid position! Choose 1 to {len(players)}")
            return

        # Get current batter index
        current_batter_index = team_game.get("current_batter_index", 0)

        if current_batter_index >= len(players):
            current_batter_index = 0

        # Swap positions
        players[current_batter_index], players[position] = players[position], players[current_batter_index]

        # Update batter
        team_game["current_batter_index"] = position
        team_game["current_batter"] = players[position].copy()

        await message.reply(
            f"✅ Batting order updated!\n\n"
            f"🏏 New batter at position {position + 1}: {players[position]['name']}"
        )
