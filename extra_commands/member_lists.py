from pyrogram import filters
from pyrogram.types import Message

def register_member_lists(app):
    
    @app.on_message(filters.command("member_lists") & filters.group)
    async def member_lists_cmd(client, message: Message):
        chat_id = message.chat.id
        
        try:
            members = []
            async for member in client.get_chat_members(chat_id):
                members.append(member)
            
            admin_count = 0
            member_count = 0
            bot_count = 0
            
            admin_list = []
            member_list = []
            bot_list = []
            
            for m in members:
                if m.user.is_bot:
                    bot_count += 1
                    bot_list.append(f"🤖 @{m.user.username}" if m.user.username else f"🤖 {m.user.first_name}")
                elif m.status.value in ['administrator', 'creator']:
                    admin_count += 1
                    admin_list.append(f"👑 @{m.user.username}" if m.user.username else f"👑 {m.user.first_name}")
                else:
                    member_count += 1
                    member_list.append(f"👤 @{m.user.username}" if m.user.username else f"👤 {m.user.first_name}")
            
            list_text = f"📊 **Group Member List**\n\n"
            list_text += f"📈 **Total Members:** {len(members)}\n"
            list_text += f"👑 **Admins:** {admin_count}\n"
            list_text += f"👤 **Members:** {member_count}\n"
            list_text += f"🤖 **Bots:** {bot_count}\n\n"
            
            if admin_list:
                list_text += "**👑 Admins:**\n" + "\n".join(admin_list[:10]) + "\n\n"
            if member_list:
                list_text += "**👤 Members (First 10):**\n" + "\n".join(member_list[:10]) + "\n\n"
            if bot_list:
                list_text += "**🤖 Bots:**\n" + "\n".join(bot_list)
            
            await message.reply(list_text)
            
        except Exception as e:
            await message.reply(f"❌ Error fetching members: {e}")
