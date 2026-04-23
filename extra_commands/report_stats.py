from pyrogram import filters
from pyrogram.types import Message
from .report_user import user_reports

def register_report_stats(app):

    @app.on_message(filters.command(["report_stats"], prefixes=["/"]) & filters.group)
    async def report_stats_cmd(client, message: Message):
        print("🔥 report_stats command triggered")  # debug

        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check admin
        from solo.handlers import is_admin
        if not await is_admin(client, chat_id, user_id):
            await message.reply("❌ Only group admins can view report statistics!")
            return

        if chat_id not in user_reports or not user_reports[chat_id]:
            await message.reply("📊 No reports have been submitted yet!")
            return

        stats_text = "📊 **REPORT STATISTICS** 📊\n\n"

        # ⚠️ Limit users to avoid long message
        for uid, reports in list(user_reports[chat_id].items())[:15]:

            # Safe user fetch
            try:
                user = await client.get_users(uid)
                name = f"@{user.username}" if user.username else user.first_name
            except:
                name = f"User_{uid}"

            stats_text += f"👤 {name}: {len(reports)} reports\n"

            # Show last 3 reports only
            for r in reports[-3:]:
                reporter_id = r.get("reporter_id", "N/A")
                reason = r.get("reason", "No reason")
                time = r.get("time", "Unknown")

                stats_text += f"   • Reporter: User_{reporter_id}\n"
                stats_text += f"     Reason: {reason}\n"
                stats_text += f"     Time: {time}\n"

            stats_text += "\n"

        await message.reply(stats_text, disable_web_page_preview=True)
