from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from config import *
import asyncio

team_games = {}
team_hosts = {}

TEAM_SIZE = 11


# ================= ADMIN CHECK =================
async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False


# ================= TEAM MODE START =================
async def team_mode_start(client, callback):
    chat_id = callback.message.chat.id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
    ])

    caption = """🏏 **TEAM MATCH MODE**

Click below to become host and create teams!
"""

    try:
        await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
    except:
        await client.send_message(chat_id, caption, reply_markup=keyboard)

    await callback.answer()


def register_team_handlers(app):

    # ================= START =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback: CallbackQuery):
        await team_mode_start(client, callback)


    # ================= HOST =================
    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user = callback.from_user

        if chat_id in team_hosts:
            return await callback.answer("Host already selected!", show_alert=True)

        team_hosts[chat_id] = {
            "id": user.id,
            "name": user.first_name
        }

        team_games[chat_id] = {
            "status": "host_selected",
            "team_a": [],
            "team_b": [],
            "team_a_captain": None,
            "team_b_captain": None
        }

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Create Team", callback_data="create_team_now")]
        ])

        await callback.message.delete()

        await client.send_message(
            chat_id,
            f"👑 {user.first_name} is now the host!\n\nClick below to create teams 👇",
            reply_markup=keyboard
        )

        await callback.answer()


    # ================= CREATE TEAM BUTTON =================
    @app.on_callback_query(filters.regex("^create_team_now$"))
    async def create_team_button(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id

        host = team_hosts.get(chat_id)
        game = team_games.get(chat_id)

        if not host or host["id"] != user_id:
            return await callback.answer("Only host can create team!", True)

        if not game or game["status"] != "host_selected":
            return await callback.answer("Invalid game state!", True)

        game["status"] = "team_a_join"

        await callback.message.edit_text(
            f"📣 **Join Team A** using /join_teamA\n\n"
            f"👥 Need {TEAM_SIZE} players\n⏰ 50 sec"
        )

        asyncio.create_task(team_a_timer(client, chat_id))
        await callback.answer()


    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)

        if not game or game["status"] != "team_a_join":
            return

        if user.id in [p["id"] for p in game["team_a"] + game["team_b"]]:
            return await message.reply("❌ Already joined!")

        if len(game["team_a"]) >= TEAM_SIZE:
            return await message.reply("❌ Team A full!")

        game["team_a"].append({"id": user.id, "name": user.first_name})

        count = len(game["team_a"])
        await message.reply(f"✅ {user.first_name} joined Team A ({count}/{TEAM_SIZE})")

        if count >= TEAM_SIZE:
            await start_team_b(client, chat_id)


    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_a_join":
            await start_team_b(client, chat_id)


    async def start_team_b(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return

        game["status"] = "team_b_join"

        await client.send_message(
            chat_id,
            f"📣 **Join Team B** using /join_teamB\n\n"
            f"👥 Need {TEAM_SIZE} players\n⏰ 50 sec"
        )

        asyncio.create_task(team_b_timer(client, chat_id))


    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)

        if not game or game["status"] != "team_b_join":
            return

        if user.id in [p["id"] for p in game["team_a"] + game["team_b"]]:
            return await message.reply("❌ Already joined!")

        if len(game["team_b"]) >= TEAM_SIZE:
            return await message.reply("❌ Team B full!")

        game["team_b"].append({"id": user.id, "name": user.first_name})

        count = len(game["team_b"])
        await message.reply(f"✅ {user.first_name} joined Team B ({count}/{TEAM_SIZE})")

        if count >= TEAM_SIZE:
            await start_captain_selection(client, chat_id)


    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_b_join":
            await start_captain_selection(client, chat_id)


    # ================= CAPTAIN =================
    async def start_captain_selection(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return

        game["status"] = "captain"

        a_buttons = [[InlineKeyboardButton(p["name"], callback_data=f"capA_{p['id']}")] for p in game["team_a"]]
        b_buttons = [[InlineKeyboardButton(p["name"], callback_data=f"capB_{p['id']}")] for p in game["team_b"]]

        await client.send_message(chat_id, "🏅 Select Team A Captain", reply_markup=InlineKeyboardMarkup(a_buttons))
        await client.send_message(chat_id, "🏅 Select Team B Captain", reply_markup=InlineKeyboardMarkup(b_buttons))


    @app.on_callback_query(filters.regex("^capA_"))
    async def cap_a(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        game = team_games.get(chat_id)

        pid = int(callback.data.split("_")[1])
        for p in game["team_a"]:
            if p["id"] == pid:
                game["team_a_captain"] = p["name"]

        await callback.message.delete()
        await callback.answer("Captain A selected")

        await check_ready(client, chat_id)


    @app.on_callback_query(filters.regex("^capB_"))
    async def cap_b(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        game = team_games.get(chat_id)

        pid = int(callback.data.split("_")[1])
        for p in game["team_b"]:
            if p["id"] == pid:
                game["team_b_captain"] = p["name"]

        await callback.message.delete()
        await callback.answer("Captain B selected")

        await check_ready(client, chat_id)


    async def check_ready(client, chat_id):
        game = team_games.get(chat_id)
        if game["team_a_captain"] and game["team_b_captain"]:
            game["status"] = "ready"

            await client.send_message(
                chat_id,
                f"✅ Captains Ready!\n\n"
                f"Team A: {game['team_a_captain']}\n"
                f"Team B: {game['team_b_captain']}\n\n"
                f"Type /start_match"
            )


    # ================= START MATCH =================
    @app.on_message(filters.command("start_match") & filters.group)
    async def start_match(client, message: Message):
        chat_id = message.chat.id
        game = team_games.get(chat_id)

        if not game or game["status"] != "ready":
            return await message.reply("❌ Not ready!")

        await message.reply("🚀 Match Started!")
