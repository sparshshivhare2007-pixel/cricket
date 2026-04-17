# solo/scoreboard.py - Final Fixed Version

from config import SOLO_ICONS

def build_scoreboard(players):
    text = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"

    for i, p in enumerate(players, start=1):
        icon = SOLO_ICONS[i % len(SOLO_ICONS)]
        history = ", ".join(map(str, p["history"][-5:]))

        # Changed from 'runs' to 'score'
        text += f"{i}. {icon} {p['name']} = {p['score']}({p['balls']})\n"
        text += f"    ╰⊚ 4️⃣s: {p['fours']:02}, 6️⃣s: {p['sixes']:02} - ID: `{p['id']}`\n"
        
        if history:
            text += f"      ╰⊚ ({history})\n\n"

    # Add total runs and outs
    total_runs = sum(p.get('score', 0) for p in players)
    total_outs = len([p for p in players if p.get('out', False)])
    active_players = len(players) - total_outs
    
    text += f"\n─────⊱ Sᴛᴀᴛs ⊰─────\n"
    text += f"📊 Total: {total_runs}/{total_outs}\n"
    text += f"👥 Active: {active_players}\n"

    return text
