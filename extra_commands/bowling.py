from pyrogram import filters
from pyrogram.types import Message
from solo.handlers import team_games

def register_bowling(app):
    
    @app.on_message(filters.command("bowling") & filters.group)
    async def bowling_cmd(client, message: Message):
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
            await message.reply("❌ Only team captains can change bowling order!")
            return
        
        args = message.command
        if len(args) < 2:
            await message.reply("❌ Usage: /bowling <position_number>\nExample: /bowling 2")
            return
        
        try:
            position = int(args[1]) - 1  # Convert to 0-based index
        except ValueError:
            await message.reply("❌ Please provide a valid number!")
            return
        
        current_team = team_game.get("current_team", "A")
        team_key = f"team_{current_team.lower()}"
        players = team_game[team_key]
        
        if position < 0 or position >= len(players):
            await message.reply(f"❌ Invalid position! Choose 1 to {len(players)}")
            return
        
        # Get current bowler index
        current_bowler_index = team_game.get("current_bowler_index", 0)
        
        # Swap bowling positions
        players[current_bowler_index], players[position] = players[position], players[current_bowler_index]
        
        # Update current bowler
        team_game["current_bowler_index"] = position
        team_game["current_bowler"] = players[position].copy()
        
        await message.reply(f"✅ Bowling order updated!\n\nNew bowler at position {args[1]}: {players[position]['name']}")