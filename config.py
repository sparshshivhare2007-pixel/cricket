import os
from dotenv import load_dotenv

load_dotenv()

# ========== BOT ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# ========== DATABASE ==========
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "cricket_bot"

# ========== ADMIN ==========
ADMIN_IDS = [6572893382]

# ========== LINKS ==========
OWNER_LINK = "https://t.me/oye_sparsh"
UPDATES_LINK = "https://t.me/your_updates_channel"
SUPPORT_LINK = "https://t.me/your_support_group"
PLAYZONE_LINK = "https://t.me/your_playzone_group"
LIVE_SCORE_LINK = "https://t.me/your_live_score_channel"

# ========== GAME IMAGES ==========
IMAGE_URL = "https://files.catbox.moe/0odkk1.jpg"
HOST_IMAGE_URL = "https://files.catbox.moe/0odkk1.jpg"
GAME_INSTRUCTIONS_IMAGE_URL = "https://files.catbox.moe/iq4758.jpg"
RESULT_IMAGE_URL = "https://graph.org/file/17971526dfefa9e20863b-44207fd3a022c59c53.jpg"
SOLO_GAME_START_IMAGE = "https://files.catbox.moe/0odkk1.jpg"

# ========== SOLO MODE MEDIA ==========
BOWLING_VIDEO_URL = "https://files.catbox.moe/r75e19.mp4"
BATTING_VIDEO_URL = "https://files.catbox.moe/26qdaw.mp4"
OUT_VIDEO_URL = "https://files.catbox.moe/7ixfhp.mp4"

# RUN VIDEOS (ADD YOUR LINKS)
RUN_1_VIDEO_URL = ""
RUN_2_VIDEO_URL = ""
RUN_3_VIDEO_URL = ""
FOUR_VIDEO_URL = ""
SIX_VIDEO_URL = ""

# ========== TIMERS ==========
BOWLING_TIMER_SECONDS = 60
JOINING_TIMER_SECONDS = 120

# ========== SOLO ICONS ==========
SOLO_ICONS = ["⚪", "🟠", "🟢", "🟣", "🔵", "🟡", "⚫", "🔴"]

# ========== GAME MESSAGES ==========

# START VOTING
START_VOTE_MESSAGE = """
🗳️ Voting Required!

At least 3 members must vote to start the game.

Click below 👇
"""

# GAME CREATED
GAME_CREATED_MESSAGE = """
🎉 Game created!

Join the game using /joingame  
(2 minutes to join) ⏰
"""

# FINAL PLAYER LIST
FINAL_PLAYER_LIST = """
👑 Unknown Host

👤 Solo Players

{players}
"""

# GAME START
GAME_STARTING_MESSAGE = """
🚀 Game starting...

Get ready players!
"""

# CURRENT BATTER
CURRENT_BATTER_MESSAGE = """
Current batter: {batter}

Send Your number:
"""

# BOWLING MESSAGE
BOWLING_MESSAGE = """
{bowler} now you can send number on bot pm, You have 1 min.
"""

# WARNING
BOWLING_WARNING_30 = """
⚠️ Warning: {bowler}, you have 30 seconds left to send a number!
"""

# INVALID INPUT
INVALID_NUMBER = "Send number between 1-6 ❌"
NOT_YOUR_TURN = "Not your turn ❌"

# RESULT MESSAGES
RUN_MESSAGE = """
🏏 {batter} scored {runs} run{'s' if runs > 1 else ''}!

{batter}: {bat}
{bowler}: {bowl}
"""

OUT_MESSAGE = """
❌ OUT!

{batter}: {bat}
{bowler}: {bowl}
"""

# NEXT TURN
NEXT_TURN_MESSAGE = """
🎮 Next Turn:

🏏 Batter: {batter}
🎯 Bowler: {bowler}
"""

# MATCH END
MATCH_END_MESSAGE = """
🏁 Match Ended!
"""

# ========== SOLO SCOREBOARD FORMAT ==========

SCOREBOARD_HEADER = "─────⊱ Sᴏʟᴏ Pʟᴀʏᴇʀ ⊰────\n\n"

PLAYER_LINE = "{index}. {icon} {name} = {runs}({balls})\n"
PLAYER_STATS = "    ╰⊚ 4️⃣s: {fours:02}, 6️⃣s: {sixes:02} - ID: `{user_id}`\n"
PLAYER_HISTORY = "      ╰⊚ ({history})\n\n"
