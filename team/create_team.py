# team/create_team.py

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import asyncio

team_games = {}
team_hosts = {}
TEAM_SIZE = 11

async def team_mode_start(client, callback):
    chat_id = callback.message.chat.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm the Host", callback_data="team_become_host")]
    ])
    
    caption = """**🏏 TEAM MATCH**

**⭐ New Game Alert! ⭐**

Who will be the game host?

Click below to become the host 🏆"""
    
    await callback.message.delete()
    
    try:
        await client.send_photo(chat_id, TEAM_PLAY_IMG, caption=caption, reply_markup=keyboard)
    except:
        await client.send_message(chat_id, caption, reply_markup=keyboard)
    await callback.answer()

def register_create_team(app):
    
    @app.on_callback_query(filters.regex("^mode_team$"))
    async def team_mode_start_direct(client, callback):
        await team_mode_start(client, callback)

    @app.on_callback_query(filters.regex("^team_become_host$"))
    async def team_become_host(client, callback):
        chat_id = callback.message.chat.id
        user = callback.from_user
        
        if chat_id in team_hosts:
            await callback.answer("Host already selected!", show_alert=True)
            return
        
        team_hosts[chat_id] = {
            "id": user.id,
            "name": user.first_name,
            "username": user.username
        }
        
        team_games[chat_id] = {
            "host_id": user.id,
            "host_name": user.first_name,
            "status": "waiting_host",
            "team_a": [],
            "team_b": []
        }
        
        await callback.message.delete()
        await client.send_message(chat_id, f"👑 [{user.first_name}](tg://user?id={user.id}) is now the game host! Use /create_team to start!")
        await callback.answer()

    @app.on_message(filters.command("create_team") & filters.group)
    async def create_team_cmd(client, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        print(f"🔴 CREATE TEAM - Chat: {chat_id}, User: {user_id}")
        
        host = team_hosts.get(chat_id)
        if not host:
            await message.reply("❌ No game host found! Start team mode first.")
            return
        
        if host["id"] != user_id:
            await message.reply("❌ Only the game host can create teams!")
            return
        
        game = team_games.get(chat_id)
        if not game or game["status"] != "waiting_host":
            await message.reply("❌ Teams already created!")
            return
        
        game["status"] = "team_creation_a"
        
        await message.reply(
            f"🎉 Team creation is underway! Join Team A by sending /join_teamA 📣\n\n"
            f"👥 Need {TEAM_SIZE} players for Team A\n"
            f"⏰ You have 50 seconds to join Team A!"
        )
        
        asyncio.create_task(team_a_timer(client, chat_id))

    async def team_a_timer(client, chat_id):
        await asyncio.sleep(50)
        game = team_games.get(chat_id)
        if game and game["status"] == "team_creation_a":
            game["status"] = "team_creation_b"
            await client.send_message(
                chat_id,
                f"⏰ Time's up for Team A!\n\n"
                f"🎉 Join Team B by sending /join_teamB 📣"
            )
