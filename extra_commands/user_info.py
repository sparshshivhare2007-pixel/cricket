from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime

def register_user_info(app):
    
    @app.on_message(filters.command("user_info") & filters.group)
    async def user_info_cmd(client, message: Message):
        user = message.from_user
        
        user_info_text = f"""👤 **User Information**

🆔 **User ID:** `{user.id}`
📛 **First Name:** {user.first_name}
🏷️ **Last Name:** {user.last_name if user.last_name else 'N/A'}
📝 **Username:** @{user.username if user.username else 'N/A'}
👑 **Is Admin:** {'Yes' if user.is_self else 'No'}
📅 **Account Created:** {datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date') else 'N/A'}

📊 **Stats:**
• Total Messages: {user.message_count if hasattr(user, 'message_count') else 'N/A'}
• Total Commands: {user.command_count if hasattr(user, 'command_count') else 'N/A'}
"""
        
        await message.reply(user_info_text)
