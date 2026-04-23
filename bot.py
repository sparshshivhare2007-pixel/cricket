# bot.py - Final Version (Solo + Extra Commands)

from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from solo.handlers import register_handlers as register_solo_handlers
from extra_commands import register_extra_commands

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

print("📝 Registering Extra Commands...")
register_extra_commands(app)

print("✅ Bot Started Successfully!")
print("🏏 Cricket Game Bot is now running...")
print("   - Solo Mode: /start → Solo → Choose 1 or 3 ball → /joingame")
print("   - Team Mode: /start → Team → Become Host → /create_team")
print("   - Extra Commands: /help for all commands")

app.run()
