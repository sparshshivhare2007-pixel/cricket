from pyrogram import filters
from pyrogram.types import Message

def register_user_info(app):

    @app.on_message(filters.command(["user_info"], prefixes=["/"]) & filters.group)
    async def user_info_cmd(client, message: Message):
        print("🔥 user_info command triggered")  # debug

        user = message.from_user
        chat_id = message.chat.id

        # Check admin properly
        from solo.handlers import is_admin
        is_admin_user = await is_admin(client, chat_id, user.id)

        user_info_text = f"""👤 **User Information**

🆔 **User ID:** `{user.id}`
📛 **First Name:** {user.first_name}
🏷️ **Last Name:** {user.last_name if user.last_name else 'N/A'}
📝 **Username:** @{user.username if user.username else 'N/A'}
👑 **Is Admin:** {'Yes' if is_admin_user else 'No'}

📊 **Info:**
• Is Bot: {'Yes' if user.is_bot else 'No'}
"""

        await message.reply(user_info_text, disable_web_page_preview=True)
