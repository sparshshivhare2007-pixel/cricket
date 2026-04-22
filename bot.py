# bot.py - Final Version (Solo + Team Both in one file)

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

print("📝 Registering Handlers (Solo + Team)...")
register_handlers(app)

print("✅ Bot Started Successfully!")
print("🏏 Cricket Game Bot is now running...")
print("   - Solo Mode: /start → Solo → Choose 1 or 3 ball → /joingame")
print("   - Team Mode: /start → Team → Become Host → /create_team")

app.run()
