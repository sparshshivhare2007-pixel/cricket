# bot.py - Final Version (Solo + Team Both)

from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from solo.handlers import register_handlers

print("🚀 Starting Cricket Game Bot...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")

app = Client(
    "cricket-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

print("📝 Registering Handlers...")
register_handlers(app)

print("✅ Bot Started Successfully!")
print("🏏 Cricket Game Bot is now running...")

app.run()
