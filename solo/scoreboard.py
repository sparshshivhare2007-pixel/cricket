from config import SOLO_ICONS

def build_scoreboard(players):
    text = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"

    for i, p in enumerate(players, start=1):
        icon = SOLO_ICONS[i % len(SOLO_ICONS)]
        history = ", ".join(map(str, p["history"][-5:]))

        text += f"{i}. {icon} {p['name']} = {p['runs']}({p['balls']})\n"
        text += f"    ╰⊚ 4️⃣s: {p['fours']:02}, 6️⃣s: {p['sixes']:02} - ID: `{p['id']}`\n"
        
        if history:
            text += f"      ╰⊚ ({history})\n\n"

    return text
