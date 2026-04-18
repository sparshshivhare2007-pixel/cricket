# solo/scoreboard.py - Final Exact Output (No Stats)

from config import SOLO_ICONS

def build_scoreboard(players, is_final=False):
    """Build scoreboard text from players list - No stats section"""
    if not players:
        return "📊 No players yet!"
    
    text = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"
    
    # Sort players by score for final result
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
        
        if history:
            text += f"      ╰⊚ ({history})\n"
        
        text += "\n"
    
    # Only add winner in final result (no stats)
    if is_final:
        winner = max(players, key=lambda x: x.get('score', 0))
        text += f"─────⊱ Rᴇsᴜʟᴛ ⊰─────\n"
        text += f"🏆 Wɪɴɴᴇʀ: {winner['name']}\n"
        text += f"📊 Sᴄᴏʀᴇ: {winner['score']} runs"
        if winner.get('balls', 0) > 0:
            text += f" ({winner['balls']} balls)"
        text += "\n"
    
    return text
