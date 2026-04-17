from pyrogram import Client
from config import BOT_TOKEN
from solo.handlers import register_handlers

app = Client(
    "cricket-bot",
    bot_token=BOT_TOKEN
)

register_handlers(app)

app.run()
