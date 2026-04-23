from pyrogram import filters
from pyrogram.types import Message

def register_member_lists(app):

    @app.on_message(filters.command(["member_lists"], prefixes=["/"]) & filters.group)
    async def member_lists_cmd(client, message: Message):
        print("🔥 member_lists command triggered")  # debug

        chat_id = message.chat.id

        try:
            members = []

            # ⚠️ LIMIT to avoid lag in big groups
            async for member in client.get_chat_members(chat_id, limit=200):
                members.append(member)

            admin_count = 0
            member_count = 0
            bot_count = 0

            admin_list = []
            member_list = []
            bot_list = []

            for m in members:
                user = m.user

                if user.is_bot:
                    bot_count += 1
                    name = f"@{user.username}" if user.username else user.first_name
                    bot_list.append(f"🤖 {name}")

                elif m.status.value in ["administrator", "creator"]:
                    admin_count += 1
                    name = f"@{user.username}" if user.username else user.first_name
                    admin_list.append(f"👑 {name}")

                else:
                    member_count += 1
                    name = f"@{user.username}" if user.username else user.first_name
                    member_list.append(f"👤 {name}")

            list_text = f"📊 **GROUP MEMBER LIST**\n\n"
            list_text += f"📈 **Total (sampled):** {len(members)}\n"
            list_text += f"👑 **Admins:** {admin_count}\n"
            list_text += f"👤 **Members:** {member_count}\n"
            list_text += f"🤖 **Bots:** {bot_count}\n\n"

            if admin_list:
                list_text += "**👑 Admins:**\n" + "\n".join(admin_list[:10]) + "\n\n"

            if member_list:
                list_text += "**👤 Members (First 10):**\n" + "\n".join(member_list[:10]) + "\n\n"

            if bot_list:
                list_text += "**🤖 Bots:**\n" + "\n".join(bot_list[:10])

            await message.reply(list_text, disable_web_page_preview=True)

        except Exception as e:
            print("Member list error:", e)
            await message.reply("❌ Error fetching members!")
