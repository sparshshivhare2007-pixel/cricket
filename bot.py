# bot.py - Final Complete Version

from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_TOKEN, API_ID, API_HASH, SELECT_GAME_IMG
import asyncio

print("🚀 Starting Cricket Game Bot...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")

app = Client(
    "cricket-bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= GAME MODES =================
@app.on_message()
async def start_command(client, message: Message):
    if message.text == "/start":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Solo Play", callback_data="mode_solo")],
            [InlineKeyboardButton("👥 Team Match", callback_data="mode_team")]
        ])
        
        caption = "🎉 **Welcome to Cricket Game Bot!** 🏏\n\nChoose your game mode:"
        
        try:
            await client.send_photo(message.chat.id, SELECT_GAME_IMG, caption=caption, reply_markup=keyboard)
        except:
            await client.send_message(message.chat.id, caption, reply_markup=keyboard)


# ================= IMPORT HANDLERS =================
try:
    from solo.handlers import register_handlers as register_solo_handlers
    print("✅ Solo mode handlers imported successfully")
    register_solo_handlers(app)
except Exception as e:
    print(f"⚠️ Solo mode import error: {e}")

try:
    from team.handlers import register_team_handlers
    print("✅ Team mode handlers imported successfully")
    register_team_handlers(app)
except Exception as e:
    print(f"⚠️ Team mode import error: {e}")


# ================= ERROR HANDLER =================
@app.on_callback_query()
async def handle_unknown_callback(client, callback: CallbackQuery):
    await callback.answer("⚠️ This option is no longer available!", show_alert=True)


@app.on_message()
async def handle_unknown_message(client, message: Message):
    if message.text and not message.text.startswith("/"):
        await message.reply("❌ Unknown command! Use /start to see available options.")


# ================= RUN BOT =================
if __name__ == "__main__":
    print("✅ Bot Started Successfully!")
    print("🏏 Cricket Game Bot is now running...")
    app.run()
