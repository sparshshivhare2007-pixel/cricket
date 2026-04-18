# Team scoreboard builder
from config import SOLO_ICONS

def build_team_scoreboard(team_a, team_b, team_a_score=0, team_b_score=0, team_a_wickets=0, team_b_wickets=0):
    text = "─────⊱ Tᴇᴀᴍ Sᴄᴏʀᴇʙᴏᴀʀᴅ ⊰────\n\n"
    
    text += "🏏 **TEAM A**\n"
    for i, p in enumerate(team_a, 1):
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        out_status = "❌" if p.get('out', False) else ""
        text += f"{i}. {p['name']} {out_status} = {runs}({balls})\n"
    
    text += f"\n📊 **Team A Total: {team_a_score}/{team_a_wickets}**\n\n"
    
    text += "🏏 **TEAM B**\n"
    for i, p in enumerate(team_b, 1):
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        out_status = "❌" if p.get('out', False) else ""
        text += f"{i}. {p['name']} {out_status} = {runs}({balls})\n"
    
    text += f"\n📊 **Team B Total: {team_b_score}/{team_b_wickets}**\n"
    
    return text
