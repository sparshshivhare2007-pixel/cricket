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

# RUN VIDEOS
RUN_1_VIDEO_URL = "https://graph.org/file/88e77efecd24d39af3918-6684feebb8fe546a95.mp4"
RUN_2_VIDEO_URL = "https://graph.org/file/668a1fe8632c5a2a00d9d-61cbe9729b733341ff.mp4"
RUN_3_VIDEO_URL = "https://graph.org/file/d913fa6143c8a338055ff-7fd548d599f4389c5f.mp4"
FOUR_VIDEO_URL = "https://graph.org/file/f122a1d001bee672c3717-a8acfd94740ab619f9f.mp4"
RUN_5_VIDEO_URL = "https://graph.org/file/4bbb87b5d33ac6bed64e5-841214f4c3d85a6dd1.mp4"
SIX_VIDEO_URL = "https://graph.org/file/5652ee0d8c02e04118b9e-ec070692c1c407ce98.mp4"

# ========== TIMERS ==========
BOWLING_TIMER_SECONDS = 60
JOINING_TIMER_SECONDS = 120

# ========== SOLO ICONS ==========
SOLO_ICONS = ["⚪", "🟠", "🟢", "🟣", "🔵", "🟡", "⚫", "🔴"]

# ========== MESSAGES ==========

START_VOTE_MESSAGE = """
🗳️ Voting Required!
At least 3 members must vote.
"""

GAME_CREATED_MESSAGE = """
🎉 Game created!
Use /joingame to join.
"""

FINAL_PLAYER_LIST = """
👑 Unknown Host

👤 Solo Players

{players}
"""

GAME_STARTING_MESSAGE = """
🚀 Game starting...
"""

CURRENT_BATTER_MESSAGE = """
🏏 Current batter: {batter}
Send number (1-6)
"""

BOWLING_MESSAGE = """
🎯 {bowler}, send bowling number (1-6)
⏰ You have 60 seconds
"""

BOWLING_WARNING_30 = """
⚠️ {bowler}, 30 seconds left!
"""

INVALID_NUMBER = "❌ Send number between 1-6"
NOT_YOUR_TURN = "❌ Not your turn"

# ================= FIXED RUN MESSAGE =================
RUN_MESSAGE = """
🏏 {batter} scored {runs}!

Bat: {bat}
Bowler: {bowler} | Bowl: {bowl}
"""

OUT_MESSAGE = """
❌ OUT!

Bat: {bat}
Bowler: {bowler} | Bowl: {bowl}
"""

NEXT_TURN_MESSAGE = """
🎮 Next Turn:

🏏 Batter: {batter}
🎯 Bowler: {bowler}
"""

MATCH_END_MESSAGE = "🏁 Match Ended!"
