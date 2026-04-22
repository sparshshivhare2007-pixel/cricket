# config.py - Final Complete Version with Auction Assets

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

# ========== GAME IMAGES ==========
SELECT_GAME_IMAGE = os.path.join(IMAGES_PATH, "select_game.jpg")
VOTE_IMAGE = os.path.join(IMAGES_PATH, "vote.jpg")
SOLO_PLAY_IMAGE = os.path.join(IMAGES_PATH, "solo_play.jpg")
HOST_IMAGE_URL = os.path.join(IMAGES_PATH, "host_image.jpg")
SOLO_GAME_START_IMAGE = os.path.join(IMAGES_PATH, "game_start.jpg")
TEAM_PLAY_IMAGE = os.path.join(IMAGES_PATH, "team_match.jpg")

# ========== AUCTION MODE IMAGES ==========
AUCTION_PLAY_IMAGE = os.path.join(IMAGES_PATH, "auction_play.jpg")
AUCTION_HOST_IMAGE = os.path.join(IMAGES_PATH, "auction_host.jpg")

# ========== TOURNAMENT MODE IMAGES ==========
TOURNAMENT_PLAY_IMAGE = os.path.join(IMAGES_PATH, "tournament_play.jpg")
TOURNAMENT_HOST_IMAGE = os.path.join(IMAGES_PATH, "tournament_host.jpg")

# Fallback URLs for images
SELECT_GAME_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
# Team image after host selection
TEAM_CHAPU_IMG = "https://files.catbox.moe/9w291u.jpg"

# Toss video
TOSS_VIDEO = "https://files.catbox.moe/hhbun3.mp4"
VOTE_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
SOLO_PLAY_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
HOST_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
SOLO_GAME_START_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
TEAM_PLAY_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
AUCTION_PLAY_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
AUCTION_HOST_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
TOURNAMENT_PLAY_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"
TOURNAMENT_HOST_IMAGE_FALLBACK = "https://files.catbox.moe/0odkk1.jpg"

# ========== SOLO MODE VIDEOS ==========
BOWLING_VIDEO_PATH = os.path.join(VIDEOS_PATH, "bowling.mp4")
BATTING_VIDEO_PATH = os.path.join(VIDEOS_PATH, "batting.mp4")
OUT_VIDEO_PATH = os.path.join(VIDEOS_PATH, "out.mp4")
RUN_1_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run1.mp4")
RUN_2_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run2.mp4")
RUN_3_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run3.mp4")
RUN_4_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run4.mp4")
RUN_5_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run5.mp4")
RUN_6_VIDEO_PATH = os.path.join(VIDEOS_PATH, "run6.mp4")

# Fallback URLs for videos
BOWLING_VIDEO_URL = "https://files.catbox.moe/r75e19.mp4"
BATTING_VIDEO_URL = "https://files.catbox.moe/26qdaw.mp4"
OUT_VIDEO_URL = "https://files.catbox.moe/7ixfhp.mp4"
RUN_1_VIDEO_URL = "https://graph.org/file/88e77efecd24d39af3918-6684feebb8fe546a95.mp4"
RUN_2_VIDEO_URL = "https://graph.org/file/668a1fe8632c5a2a00d9d-61cbe9729b733341ff.mp4"
RUN_3_VIDEO_URL = "https://graph.org/file/d913fa6143c8a338055ff-7fd548d599f4389c5f.mp4"
FOUR_VIDEO_URL = "https://graph.org/file/f122a1d001bee672c3717-a8acfd94740ab619f9f.mp4"
RUN_5_VIDEO_URL = "https://graph.org/file/4bbb87b5d33ac6bed64e5-841214f4c3d85a6dd1.mp4"
SIX_VIDEO_URL = "https://graph.org/file/5652ee0d8c02e04118b9e-ec070692c1c407ce98.mp4"

# ========== HELPER FUNCTIONS ==========
def get_image_file(local_path, fallback_url):
    """Return local file path if exists, else return fallback URL"""
    if os.path.exists(local_path):
        return local_path
    print(f"⚠️ Local image not found: {local_path}, using URL fallback")
    return fallback_url

def get_video_file(video_path, video_url):
    """Return local file path if exists, else return fallback URL"""
    if os.path.exists(video_path):
        return video_path
    print(f"⚠️ Local video not found: {video_path}, using URL fallback")
    return video_url

# ========== PRE-DEFINE IMAGES ==========
SELECT_GAME_IMG = get_image_file(SELECT_GAME_IMAGE, SELECT_GAME_IMAGE_FALLBACK)
VOTE_IMG = get_image_file(VOTE_IMAGE, VOTE_IMAGE_FALLBACK)
SOLO_PLAY_IMG = get_image_file(SOLO_PLAY_IMAGE, SOLO_PLAY_IMAGE_FALLBACK)
HOST_IMAGE_URL = get_image_file(HOST_IMAGE_URL, HOST_IMAGE_FALLBACK)
SOLO_START_IMAGE = get_image_file(SOLO_GAME_START_IMAGE, SOLO_GAME_START_IMAGE_FALLBACK)
TEAM_PLAY_IMG = get_image_file(TEAM_PLAY_IMAGE, TEAM_PLAY_IMAGE_FALLBACK)

# ========== AUCTION IMAGES ==========
AUCTION_PLAY_IMG = get_image_file(AUCTION_PLAY_IMAGE, AUCTION_PLAY_IMAGE_FALLBACK)
AUCTION_HOST_IMG = get_image_file(AUCTION_HOST_IMAGE, AUCTION_HOST_IMAGE_FALLBACK)

# ========== TOURNAMENT IMAGES ==========
TOURNAMENT_PLAY_IMG = get_image_file(TOURNAMENT_PLAY_IMAGE, TOURNAMENT_PLAY_IMAGE_FALLBACK)
TOURNAMENT_HOST_IMG = get_image_file(TOURNAMENT_HOST_IMAGE, TOURNAMENT_HOST_IMAGE_FALLBACK)

# ========== PRE-DEFINE VIDEOS ==========
BOWLING_VIDEO = get_video_file(BOWLING_VIDEO_PATH, BOWLING_VIDEO_URL)
BATTING_VIDEO = get_video_file(BATTING_VIDEO_PATH, BATTING_VIDEO_URL)
OUT_VIDEO = get_video_file(OUT_VIDEO_PATH, OUT_VIDEO_URL)
RUN_1_VIDEO = get_video_file(RUN_1_VIDEO_PATH, RUN_1_VIDEO_URL)
RUN_2_VIDEO = get_video_file(RUN_2_VIDEO_PATH, RUN_2_VIDEO_URL)
RUN_3_VIDEO = get_video_file(RUN_3_VIDEO_PATH, RUN_3_VIDEO_URL)
RUN_4_VIDEO = get_video_file(RUN_4_VIDEO_PATH, FOUR_VIDEO_URL)
RUN_5_VIDEO = get_video_file(RUN_5_VIDEO_PATH, RUN_5_VIDEO_URL)
RUN_6_VIDEO = get_video_file(RUN_6_VIDEO_PATH, SIX_VIDEO_URL)

# ========== RUN VIDEOS DICTIONARY ==========
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

BOWLING_MESSAGE = """
🎯 {bowler}, send bowling number (1-6)
⏰ You have 60 seconds
"""

MATCH_END_MESSAGE = "🏁 Match Ended!"
