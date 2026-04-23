from pyrogram import filters
from pyrogram.types import Message

def register_help(app):
    
    @app.on_message(filters.command("help") & filters.group)
    async def help_cmd(client, message: Message):
        help_text = """🏏 **Cricket Game Bot Help** 🏏

**🎮 GAME COMMANDS:**
/start - Start game (Admin) or Vote (Member)
/joingame - Join a solo game
/score - Check live score
/end_match - End current match (Admin only)

**👥 TEAM MODE COMMANDS:**
/create_team - Create teams (Host only)
/join_teamA - Join Team A
/join_teamB - Join Team B
/choose_cap - Choose team captains (Host only)
/add_A @user - Add player to Team A (Host only)
/add_B @user - Add player to Team B (Host only)
/shift_Team - Shift player between teams (Host only)

**📊 EXTRA COMMANDS:**
/user_info - Get user information
/user_ranks - View player ranks
/member_lists - View group members
/startgame - Start a new game (Admin only)
/matches - View active matches
/live_matches - View live match updates
/batting <number> - Set batting position (Team mode)
/bowling <number> - Set bowling position (Team mode)
/host_change @user - Change game host
/solo_leave - Leave solo game
/full_score - View complete scorecard
/report_user @user - Report a user
/report_stats - View report statistics
/cap_change @user - Change team captain (Host only)
/add_cap @user - Add a captain (Host only)
/rm_cap @user - Remove a captain (Host only)

**ℹ️ INFO:**
• Solo mode requires minimum 4 players
• Each bowler bowls 3 balls in solo mode
• Team mode has 6 balls per over
• Use /start in group to begin!

**📞 Support:** @YourSupportUsername
"""
        await message.reply(help_text)
