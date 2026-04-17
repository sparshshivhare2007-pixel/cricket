from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from solo.handlers import register_handlers

# Debug (remove later)
print("API_ID:", API_ID)
print("API_HASH:", API_HASH)

app = Client(
    "cricket-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

register_handlers(app)

print("🚀 Bot Started Successfully!")

app.run()
