# config.py
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

# ========== ASSETS FOLDER ==========
ASSETS_PATH = "assets"
VIDEOS_PATH = os.path.join(ASSETS_PATH, "videos")
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")

# ========== GAME IMAGES (Local) ==========
GAME_MENU_IMAGE = os.path.join(IMAGES_PATH, "game_menu.jpg")
SOLO_GAME_START_IMAGE = os.path.join(IMAGES_PATH, "game_start.jpg")
IMAGE_URL = os.path.join(IMAGES_PATH, "default.jpg")
HOST_IMAGE_URL = os.path.join(IMAGES_PATH, "host.jpg")
GAME_INSTRUCTIONS_IMAGE_URL = os.path.join(IMAGES_PATH, "instructions.jpg")
RESULT_IMAGE_URL = os.path.join(IMAGES_PATH, "result.jpg")

# Fallback URLs for images (if local files don't exist)
IMAGE_URL_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
HOST_IMAGE_URL_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
GAME_INSTRUCTIONS_IMAGE_URL_FALLBACK = "https://files.catbox.moe/iq4758.jpg"
RESULT_IMAGE_URL_FALLBACK = "https://graph.org/file/17971526dfefa9e20863b-44207fd3a022c59c53.jpg"
SOLO_GAME_START_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"

# ========== SOLO MODE VIDEOS (Local) ==========
BOWLING_VIDEO_PATH = os.path.join(VIDEOS_PATH, "bowling.mp4")
BATTING_VIDEO_PATH = os.path.join(VIDEOS_PATH, "batting.mp4")
OUT_VIDEO_PATH = os.path.join(VIDEOS_PATH, "out.mp4")
RUN_1_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run1.mp4")
RUN_2_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run2.mp4")
RUN_3_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run3.mp4")
RUN_4_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run4.mp4")
RUN_5_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run5.mp4")
RUN_6_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run6.mp4")

# Fallback URLs for videos (if local files don't exist)
BOWLING_VIDEO_URL = "https://files.catbox.moe/r75e19.mp4"
BATTING_VIDEO_URL = "https://files.catbox.moe/26qdaw.mp4"
OUT_VIDEO_URL = "https://files.catbox.moe/7ixfhp.mp4"
RUN_1_VIDEO_URL = "https://graph.org/file/88e77efecd24d39af3918-6684feebb8fe546a95.mp4"
RUN_2_VIDEO_URL = "https://graph.org/file/668a1fe8632c5a2a00d9d-61cbe9729b733341ff.mp4"
RUN_3_VIDEO_URL = "https://graph.org/file/d913fa6143c8a338055ff-7fd548d599f4389c5f.mp4"
FOUR_VIDEO_URL = "https://graph.org/file/f122a1d001bee672c3717-a8acfd94740ab619f9f.mp4"
RUN_5_VIDEO_URL = "https://graph.org/file/4bbb87b5d33ac6bed64e5-841214f4c3d85a6dd1.mp4"
SIX_VIDEO_URL = "https://graph.org/file/5652ee0d8c02e04118b9e-ec070692c1c407ce98.mp4"

# Function to get image file (local or URL)
def get_image_file(local_path, fallback_url):
    """Return local file path if exists, else return fallback URL"""
    if os.path.exists(local_path):
        return local_path
    print(f"⚠️ Local image not found: {local_path}, using URL fallback")
    return fallback_url

# Function to get video file (local or URL)
def get_video_file(video_path, video_url):
    """Return local file path if exists, else return URL"""
    if os.path.exists(video_path):
        return video_path
    print(f"⚠️ Local video not found: {video_path}, using URL fallback")
    return video_url

# Pre-define images with fallback
GAME_MENU = get_image_file(GAME_MENU_IMAGE, IMAGE_URL_FALLBACK)
SOLO_START_IMAGE = get_image_file(SOLO_GAME_START_IMAGE, SOLO_GAME_START_IMAGE_FALLBACK)

# Pre-define videos with fallback
BOWLING_VIDEO = get_video_file(BOWLING_VIDEO_PATH, BOWLING_VIDEO_URL)
BATTING_VIDEO = get_video_file(BATTING_VIDEO_PATH, BATTING_VIDEO_URL)
OUT_VIDEO = get_video_file(OUT_VIDEO_PATH, OUT_VIDEO_URL)
RUN_1_VIDEO = get_video_file(RUN_1_VIDEO_PATH, RUN_1_VIDEO_URL)
RUN_2_VIDEO = get_video_file(RUN_2_VIDEO_PATH, RUN_2_VIDEO_URL)
RUN_3_VIDEO = get_video_file(RUN_3_VIDEO_PATH, RUN_3_VIDEO_URL)
RUN_4_VIDEO = get_video_file(RUN_4_VIDEO_PATH, FOUR_VIDEO_URL)
RUN_5_VIDEO = get_video_file(RUN_5_VIDEO_PATH, RUN_5_VIDEO_URL)
RUN_6_VIDEO = get_video_file(RUN_6_VIDEO_PATH, SIX_VIDEO_URL)

# Dictionary for easy access
RUN_VIDEOS = {
    1: RUN_1_VIDEO,
    2: RUN_2_VIDEO,
    3: RUN_3_VIDEO,
    4: RUN_4_VIDEO,
    5: RUN_5_VIDEO,
    6: RUN_6_VIDEO
}

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
