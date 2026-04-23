# bot.py - Final Version (Solo + Extra Commands)

from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from solo.handlers import register_handlers as register_solo_handlers
from database import init_db, close_db
import asyncio

print("🚀 Starting Cricket Game Bot...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")

async def main():
    # Initialize database
    await init_db()
    
    app = Client(
        "cricket-bot",
        api_id=int(API_ID),
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    print("📝 Registering Solo Mode Handlers...")
    register_solo_handlers(app)
    
    print("✅ Bot Started Successfully!")
    print("🏏 Cricket Game Bot is now running...")
    print("   - Solo Mode: /start → Solo → /joingame (min 4 players)")
    print("   - Team Mode: /start → Team → Become Host → /create_team")
    print("   - Extra Commands: /help for all commands")
    
    try:
        await app.run()
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
