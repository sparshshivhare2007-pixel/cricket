from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime

# Store reports
user_reports = {}

def register_report_user(app):

    @app.on_message(filters.command(["report_user"], prefixes=["/"]) & filters.group)
    async def report_user_cmd(client, message: Message):
        print("🔥 report_user command triggered")  # debug

        chat_id = message.chat.id
        user_id = message.from_user.id

        # Get reported user
        reported_user = None

        # Reply method
        if message.reply_to_message and message.reply_to_message.from_user:
            reported_user = message.reply_to_message.from_user

        # Username method
        elif message.command and len(message.command) > 1:
            username = message.command[1].replace("@", "")
            try:
                reported_user = await client.get_users(username)
            except Exception as e:
                print("User fetch error:", e)
                await message.reply(f"❌ User @{username} not found!")
                return

        if not reported_user:
            await message.reply("❌ Usage: /report_user @username or reply to a user's message")
            return

        # Prevent self-report
        if reported_user.id == user_id:
            await message.reply("❌ You cannot report yourself!")
            return

        # Get reason safely
        reason = "No reason provided"
        if message.command and len(message.command) > 2:
            reason = " ".join(message.command[2:])[:100]  # limit length

        # Init storage
        if chat_id not in user_reports:
            user_reports[chat_id] = {}

        if reported_user.id not in user_reports[chat_id]:
            user_reports[chat_id][reported_user.id] = []

        # 🚨 Anti-spam: prevent duplicate spam reports
        recent_reports = user_reports[chat_id][reported_user.id]
        if any(r["reporter_id"] == user_id for r in recent_reports[-3:]):
            await message.reply("⚠️ You have already reported this user recently!")
            return

        # Store report
        user_reports[chat_id][reported_user.id].append({
            "reporter_id": user_id,
            "reason": reason,
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        report_count = len(user_reports[chat_id][reported_user.id])

        await message.reply(
            f"✅ **Report Submitted!**\n\n"
            f"👤 Reported User: [{reported_user.first_name}](tg://user?id={reported_user.id})\n"
            f"📝 Reason: {reason}\n"
            f"📊 Total Reports: {report_count}\n\n"
            f"Thank you for helping keep the community clean!",
            disable_web_page_preview=True
        )
