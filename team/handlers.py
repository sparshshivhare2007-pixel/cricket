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

    caption = """🎉 **New Game Alert!** 🎉

Who will be the game host for this match? 🤔"""

    try:
        # Use TEAM_PLAY_IMG from config for the image
        await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
    except:
        # Fallback if image not found
        await client.send_message(chat_id, caption, reply_markup=keyboard)

    await callback.answer()


def register_team_handlers(app):

    # ================= START - MODE SELECTION =================
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback: CallbackQuery):
        await team_mode_start(client, callback)


    # ================= HOST SELECTION =================
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

        # Delete the previous message with button
        await callback.message.delete()

        # Send simple text message without any button
        await client.send_message(
            chat_id,
            f"👑 {user.first_name} is now the game host! Game host can create teams now by using /create_team. Let's get the match started! 🏏"
        )

        await callback.answer()


    # ================= CREATE TEAM COMMAND =================
    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_command(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        host = team_hosts.get(chat_id)
        game = team_games.get(chat_id)

        if not host or host["id"] != user_id:
            return await message.reply("❌ Only host can create teams!")

        if not game or game["status"] != "host_selected":
            return await message.reply("❌ Invalid game state! Use /create_team only after becoming host.")

        game["status"] = "team_a_join"

        await message.reply(
            f"🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n"
            f"👥 Need {TEAM_SIZE} players\n⏰ 50 seconds timeout"
        )

        asyncio.create_task(team_a_timer(client, chat_id))


    # ================= JOIN TEAM A =================
    @app.on_message(filters.command("join_teamA") & filters.group)
    async def join_team_a(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)

        if not game or game["status"] != "team_a_join":
            return await message.reply("❌ Team A joining is not active right now!")

        # Check if user already joined any team
        if user.id in [p["id"] for p in game["team_a"] + game["team_b"]]:
            return await message.reply("❌ You have already joined a team!")

        if len(game["team_a"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team A is full! ({TEAM_SIZE}/{TEAM_SIZE})")

        game["team_a"].append({"id": user.id, "name": user.first_name})

        count = len(game["team_a"])
        remaining = TEAM_SIZE - count
        await message.reply(f"✅ {user.first_name} joined Team A! ({count}/{TEAM_SIZE})\n\n{remaining} more players needed for Team A.")

        if count >= TEAM_SIZE:
            await start_team_b(client, chat_id)


    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_a_join":
            if len(game["team_a"]) < TEAM_SIZE:
                await client.send_message(
                    chat_id,
                    f"⏰ Time's up! Team A has {len(game['team_a'])}/{TEAM_SIZE} players.\nMoving to Team B creation..."
                )
            await start_team_b(client, chat_id)


    async def start_team_b(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return

        game["status"] = "team_b_join"

        await client.send_message(
            chat_id,
            f"📣 **Team A Complete!** Now join Team B using /join_teamB 📣\n\n"
            f"👥 Need {TEAM_SIZE} players\n⏰ 50 seconds timeout"
        )

        asyncio.create_task(team_b_timer(client, chat_id))


    # ================= JOIN TEAM B =================
    @app.on_message(filters.command("join_teamB") & filters.group)
    async def join_team_b(client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        game = team_games.get(chat_id)

        if not game or game["status"] != "team_b_join":
            return await message.reply("❌ Team B joining is not active right now!")

        # Check if user already joined any team
        if user.id in [p["id"] for p in game["team_a"] + game["team_b"]]:
            return await message.reply("❌ You have already joined a team!")

        if len(game["team_b"]) >= TEAM_SIZE:
            return await message.reply(f"❌ Team B is full! ({TEAM_SIZE}/{TEAM_SIZE})")

        game["team_b"].append({"id": user.id, "name": user.first_name})

        count = len(game["team_b"])
        remaining = TEAM_SIZE - count
        await message.reply(f"✅ {user.first_name} joined Team B! ({count}/{TEAM_SIZE})\n\n{remaining} more players needed for Team B.")

        if count >= TEAM_SIZE:
            await start_captain_selection(client, chat_id)


    async def team_b_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_b_join":
            if len(game["team_b"]) < TEAM_SIZE:
                await client.send_message(
                    chat_id,
                    f"⏰ Time's up! Team B has {len(game['team_b'])}/{TEAM_SIZE} players.\nMoving to captain selection with available players..."
                )
            await start_captain_selection(client, chat_id)


    # ================= CAPTAIN SELECTION =================
    async def start_captain_selection(client, chat_id):
        game = team_games.get(chat_id)
        if not game:
            return

        game["status"] = "captain"

        # Check if teams have players
        if not game["team_a"]:
            await client.send_message(chat_id, "❌ Team A has no players! Cannot proceed.")
            return
        
        if not game["team_b"]:
            await client.send_message(chat_id, "❌ Team B has no players! Cannot proceed.")
            return

        # Create captain selection buttons
        a_buttons = []
        for p in game["team_a"]:
            a_buttons.append([InlineKeyboardButton(p["name"], callback_data=f"capA_{p['id']}")])
        
        b_buttons = []
        for p in game["team_b"]:
            b_buttons.append([InlineKeyboardButton(p["name"], callback_data=f"capB_{p['id']}")])

        await client.send_message(chat_id, "🏅 **Select Team A Captain**", reply_markup=InlineKeyboardMarkup(a_buttons))
        await client.send_message(chat_id, "🏅 **Select Team B Captain**", reply_markup=InlineKeyboardMarkup(b_buttons))


    @app.on_callback_query(filters.regex("^capA_"))
    async def cap_a(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        game = team_games.get(chat_id)

        if not game:
            return await callback.answer("Game not found!")

        pid = int(callback.data.split("_")[1])
        selected_name = ""
        for p in game["team_a"]:
            if p["id"] == pid:
                game["team_a_captain"] = p["name"]
                selected_name = p["name"]

        await callback.message.delete()
        await callback.answer(f"✅ {selected_name} is now Team A Captain!")

        await check_ready(client, chat_id)


    @app.on_callback_query(filters.regex("^capB_"))
    async def cap_b(client, callback: CallbackQuery):
        chat_id = callback.message.chat.id
        game = team_games.get(chat_id)

        if not game:
            return await callback.answer("Game not found!")

        pid = int(callback.data.split("_")[1])
        selected_name = ""
        for p in game["team_b"]:
            if p["id"] == pid:
                game["team_b_captain"] = p["name"]
                selected_name = p["name"]

        await callback.message.delete()
        await callback.answer(f"✅ {selected_name} is now Team B Captain!")

        await check_ready(client, chat_id)


    async def check_ready(client, chat_id):
        game = team_games.get(chat_id)
        if game and game["team_a_captain"] and game["team_b_captain"]:
            game["status"] = "ready"

            # Show team summary
            team_a_names = ", ".join([p["name"] for p in game["team_a"]])
            team_b_names = ", ".join([p["name"] for p in game["team_b"]])

            await client.send_message(
                chat_id,
                f"✅ **Teams are Ready!**\n\n"
                f"🏏 **Team A** (Captain: {game['team_a_captain']})\n"
                f"Players: {team_a_names}\n\n"
                f"🏏 **Team B** (Captain: {game['team_b_captain']})\n"
                f"Players: {team_b_names}\n\n"
                f"Type /start_match to begin the match! 🚀"
            )


    # ================= START MATCH =================
    @app.on_message(filters.command("start_match") & filters.group)
    async def start_match(client, message: Message):
        chat_id = message.chat.id
        game = team_games.get(chat_id)

        if not game or game["status"] != "ready":
            return await message.reply("❌ Match is not ready yet! Make sure both captains are selected.")

        game["status"] = "match_started"
        
        # Show final match start message
        await message.reply(
            f"🚀 **MATCH STARTED!** 🚀\n\n"
            f"🏏 Team A (Captain: {game['team_a_captain']}) vs 🏏 Team B (Captain: {game['team_b_captain']})\n\n"
            f"Good luck to both teams! 🎉"
        )
