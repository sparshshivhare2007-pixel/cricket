from pyrogram import filters
from pyrogram.types import Message

def register_test(app):
    
    @app.on_message(filters.command("test") & filters.group)
    async def test_cmd(client, message: Message):
        await message.reply("✅ Test command is working! Extra commands are registered successfully.")