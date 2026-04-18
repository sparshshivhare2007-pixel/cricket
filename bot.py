# bot.py - Final Complete Version

from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from solo.handlers import register_handlers as register_solo_handlers
from team.handlers import register_team_handlers

print("🚀 Starting Cricket Game Bot...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")

app = Client(
    "cricket-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

print("📝 Registering Solo Mode Handlers...")
register_solo_handlers(app)

print("📝 Registering Team Mode Handlers...")
register_team_handlers(app)

print("✅ Bot Started Successfully!")

app.run()
