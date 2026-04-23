from pyrogram import filters
from pyrogram.types import Message
from solo.game import games
from team.handlers import team_games

def register_user_ranks(app):
    
    @app.on_message(filters.command("user_ranks") & filters.group)
    async def user_ranks_cmd(client, message: Message):
        chat_id = message.chat.id
        
        # Check solo mode players
        solo_game = games.get(chat_id)
        team_game = team_games.get(chat_id)
        
        if not solo_game and not team_game:
            await message.reply("❌ No active game found!")
            return
        
        rank_text = "🏆 **Player Ranks** 🏆\n\n"
        
        if solo_game and solo_game.get("players"):
            players = solo_game["players"]
            sorted_players = sorted(players, key=lambda x: x.get("score", 0), reverse=True)
            
            rank_text += "**SOLO MODE RANKS:**\n"
            for i, p in enumerate(sorted_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
                rank_text += f"{medal} {i}. {name} - {p.get('score', 0)} runs\n"
        
        if team_game:
            rank_text += "\n**TEAM MODE RANKS:**\n"
            
            # Team A players
            rank_text += "\n🏏 **Team A:**\n"
            team_a_players = sorted(team_game.get("team_a", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_a_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
            
            # Team B players
            rank_text += "\n🏏 **Team B:**\n"
            team_b_players = sorted(team_game.get("team_b", []), key=lambda x: x.get("score", 0), reverse=True)
            for i, p in enumerate(team_b_players, 1):
                name = f"@{p['username']}" if p.get('username') else p['name']
                rank_text += f"   {i}. {name} - {p.get('score', 0)} runs\n"
        
        await message.reply(rank_text)
