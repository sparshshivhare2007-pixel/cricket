# solo/scoreboard.py - Final Exact Output

def build_scoreboard(players, is_final=False):
    """Build scoreboard text from players list - Exact format as shown"""
    if not players:
        return "📊 No players yet!"
    
    text = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"
    
    # Sort players by score for final result
    if is_final:
        sorted_players = sorted(players, key=lambda x: x.get('score', 0), reverse=True)
    else:
        sorted_players = players

    # Player icons
    icons = ["⭕", "⚪", "🟣", "🟣", "⚪", "🔴", "🔵", "🟢", "🟡", "🟠"]
    
    for i, p in enumerate(sorted_players, start=1):
        # Get icon
        icon = icons[(i - 1) % len(icons)]
        
        # Get player details
        name = p.get('name', 'Unknown')
        runs = p.get('score', 0)
        balls = p.get('balls', 0)
        fours = p.get('fours', 0)
        sixes = p.get('sixes', 0)
        player_id = p.get('id', 0)
        history = p.get('history', [])
        is_out = p.get('out', False)
        
        # Format fours and sixes with leading zero
        fours_str = f"{fours:02d}"
        sixes_str = f"{sixes:02d}"
        
        # Out status
        out_mark = " ❌" if is_out else ""
        
        # Main line
        text += f"{i}. {icon} {name}{out_mark} = {runs}({balls})\n"
        
        # Stats line
        text += f"    ╰⊚ 4️⃣s: {fours_str}, 6️⃣s: {sixes_str} - ID: {player_id}\n"
        
        # History line
        if history:
            # Format history: replace -6 with - (as shown in example)
            formatted_history = []
            for h in history[-5:]:  # Last 5 balls
                if h == -6 or h == "-6":
                    formatted_history.append("-")
                elif h == "W":
                    formatted_history.append("W")
                else:
                    formatted_history.append(str(h))
            history_str = ", ".join(formatted_history)
            text += f"      ╰⊚ ({history_str})\n"
        else:
            text += f"      ╰⊚ (No balls)\n"
        
        text += "\n"
    
    # Add result section for final scoreboard
    if is_final:
        # Find winner (player with highest score)
        winner = max(players, key=lambda x: x.get('score', 0))
        winner_score = winner.get('score', 0)
        winner_balls = winner.get('balls', 0)
        
        text += f"─────⊱ Rᴇsᴜʟᴛ ⊰─────\n"
        text += f"🏆 Wɪɴɴᴇʀ: {winner['name']}\n"
        text += f"📊 Sᴄᴏʀᴇ: {winner_score} runs"
        if winner_balls > 0:
            text += f" ({winner_balls} balls)"
        text += "\n"
    
    return text


# Alias for backward compatibility
def build_solo_scoreboard(players, is_final=False):
    return build_scoreboard(players, is_final)
