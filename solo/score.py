# solo/score.py - Live Score Module

from solo.game import games
from solo.scoreboard import build_scoreboard

async def get_live_score(client, message):
    """Send live score of current game"""
    chat_id = message.chat.id
    game = games.get(chat_id)
    
    if not game:
        await message.reply("No game is going on in this chat!")
        return
    
    if game.get("status") == "waiting":
        players_count = len(game.get("players", []))
        await message.reply(
            f"⏳ **Game Status: Waiting**\n\n"
            f"👥 Players joined: {players_count}\n"
            f"🎯 Ball Mode: {game.get('ball_mode', 'Not selected')} Ball{'s' if game.get('ball_mode', 0) > 1 else ''}\n\n"
            f"Send `/joingame` to join!"
        )
        return
    
    if game.get("status") == "playing" and not game.get("game_over"):
        players = game["players"]
        current_batter = game.get("current_batter", {})
        current_bowler = game.get("current_bowler", {})
        ball_mode = game.get("ball_mode", 3)
        bowler_balls = game.get("current_bowler_balls", 0)
        total_balls = game.get("total_balls_in_match", 0)
        
        total_runs = sum(p.get('score', 0) for p in players)
        total_outs = len([p for p in players if p.get('out', False)])
        
        score_text = f"📊 **LIVE SCORE** 📊\n\n"
        score_text += f"🏏 **Total: {total_runs}/{total_outs}**\n"
        score_text += f"⚾ **Balls Bowled: {total_balls}**\n"
        score_text += f"🎯 **Mode: {ball_mode} Ball{'s' if ball_mode > 1 else ''}**\n\n"
        
        score_text += f"🟢 **Current Batter:**\n"
        score_text += f"   👤 {current_batter.get('name', 'None')}\n"
        score_text += f"   📈 Score: {current_batter.get('score', 0)} runs"
        score_text += f" ({current_batter.get('balls', 0)} balls)\n\n"
        
        score_text += f"🔴 **Current Bowler:**\n"
        score_text += f"   👤 {current_bowler.get('name', 'None')}\n"
        score_text += f"   🎯 Balls bowled: {bowler_balls}/{ball_mode}\n\n"
        
        players_list = "\n".join([f"{i+1}. {p['name']} - {p.get('score', 0)} runs" for i, p in enumerate(players[:5])])
        if len(players) > 5:
            players_list += f"\n... and {len(players)-5} more"
        
        score_text += f"👥 **Players:**\n{players_list}\n"
        
        await message.reply(score_text)
        return
    
    if game.get("game_over"):
        winner = game.get("winner", {})
        total_runs = sum(p.get('score', 0) for p in game["players"])
        total_outs = len([p for p in game["players"] if p.get('out', False)])
        
        await message.reply(
            f"🏆 **GAME OVER** 🏆\n\n"
            f"🏅 **Winner:** {winner.get('name', 'Unknown')}\n"
            f"📊 **Final Score:** {total_runs}/{total_outs}\n\n"
            f"Use /start to play again!"
        )
        return
