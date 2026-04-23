from pyrogram import filters
from pyrogram.types import Message
from solo.game import create_game

def register_startgame(app):
    
    @app.on_message(filters.command("startgame") & filters.group)
    async def startgame_cmd(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if user is admin
        from solo.handlers import is_admin
        if not await is_admin(client, chat_id, user_id):
            await message.reply("❌ Only admins can use /startgame!")
            return
        
        # Check if game already exists
        from solo.game import games
        if games.get(chat_id):
            await message.reply("❌ A game is already active in this group!")
            return
        
        # Create new game
        create_game(chat_id)
        
        # Call the solo mode start menu
        from solo.handlers import select_game_menu
        await select_game_menu(client, message)
