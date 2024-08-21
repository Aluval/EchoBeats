from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import db

@Client.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_command(client: Client, msg: Message):
    user_id = msg.from_user.id
    
    # Extract metadata from the command message
    if len(msg.command) < 2:
        await msg.reply_text("Invalid command format. Use: /setmetadata comment | created_by | title")
        return
    
    parts = msg.text.split(" ", 1)[1].split(" | ")
    if len(parts) != 3:
        await msg.reply_text("Invalid number of metadata parts. Use: /setmetadata comment | created_by | title")
        return
    
    metadata = {
        "comment": parts[0].strip(),
        "created_by": parts[1].strip(),
        "title": parts[2].strip()
    }
    
    # Store the metadata in the database
    await db.set_user_metadata(user_id, metadata)
    
    await msg.reply_text("Metadata set successfully ✅.")
  
