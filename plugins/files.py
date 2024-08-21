import psutil
import asyncio
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMIN
from pymongo.errors import PyMongoError
from pyrogram.errors import FloodWait
from helper.database import db
from datetime import timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery

# Global variables
START_TIME = datetime.datetime.now()

@Client.on_message(filters.command("ban") & filters.user(ADMIN))
async def ban_user(bot, msg: Message):
    try:
        user_id = int(msg.text.split()[1])
        # Ban user in the database
        await db.ban_user(user_id)
        # Ban user from the chat
        await bot.ban_chat_member(chat_id=msg.chat.id, user_id=user_id)
        await msg.reply_text(f"User {user_id} has been banned.")
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred: {e}")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await msg.reply_text(f"Flood wait error: Please try again later.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("unban") & filters.user(ADMIN))
async def unban_user(bot, msg: Message):
    try:
        user_id = int(msg.text.split()[1])
        # Unban user in the database
        await db.unban_user(user_id)
        # Unban user from the chat
        await bot.unban_chat_member(chat_id=msg.chat.id, user_id=user_id)
        await msg.reply_text(f"User {user_id} has been unbanned.")
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred: {e}")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await msg.reply_text(f"Flood wait error: Please try again later.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("users") & filters.user(ADMIN))
async def count_users(bot, msg):
    try:
        total_users = await db.count_users()
        banned_users = await db.count_banned_users()

        response = (
            f"**User Statistics:**\n"
            f"Total Active Users: {total_users}\n"
            f"Banned Users: {banned_users}"
        )
        await msg.reply_text(response)
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred while counting users: {e}")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("stats") & filters.chat(GROUP))        
async def stats_command(_, msg):
    uptime = datetime.datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    total_space = psutil.disk_usage('/').total / (1024 ** 3)
    used_space = psutil.disk_usage('/').used / (1024 ** 3)
    free_space = psutil.disk_usage('/').free / (1024 ** 3)

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    stats_message = (
        f"📊 **Server Stats** 📊\n\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"💾 **Total Space:** `{total_space:.2f} GB`\n"
        f"📂 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)\n"
        f"📁 **Free Space:** `{free_space:.2f} GB`\n"
        f"⚙️ **CPU Usage:** `{cpu_usage:.1f}%`\n"
        f"💻 **RAM Usage:** `{ram_usage:.1f}%`\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")]
        ]
    )

    await msg.reply_text(stats_message, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^refresh_stats$"))
async def refresh_stats_callback(_, callback_query):
    # Refresh stats
    uptime = datetime.datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    total_space = psutil.disk_usage('/').total / (1024 ** 3)
    used_space = psutil.disk_usage('/').used / (1024 ** 3)
    free_space = psutil.disk_usage('/').free / (1024 ** 3)

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    stats_message = (
        f"📊 **Server Stats** 📊\n\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"💾 **Total Space:** `{total_space:.2f} GB`\n"
        f"📂 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)\n"
        f"📁 **Free Space:** `{free_space:.2f} GB`\n"
        f"⚙️ **CPU Usage:** `{cpu_usage:.1f}%`\n"
        f"💻 **RAM Usage:** `{ram_usage:.1f}%`\n"
    )

    await callback_query.message.edit_text(stats_message, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")]
        ]
    ))


@Client.on_message(filters.command("clear") & filters.user(ADMIN))
async def clear_database_handler(client: Client, msg: Message):
    try:
        await db.clear_database()
        await msg.reply_text("Database has been cleared✅.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast(bot, msg: Message):
    if not msg.reply_to_message:
        await msg.reply_text("Please reply to a message to broadcast it.")
        return

    broadcast_message = msg.reply_to_message

    # Fetch all user IDs
    user_ids = await db.get_all_user_ids()

    sent_count = 0
    failed_count = 0
    log_entries = []

    for user_id in user_ids:
        try:
            await broadcast_message.copy(chat_id=user_id)
            sent_count += 1
            log_entries.append(f"Sent to {user_id}")
        except Exception as e:
            failed_count += 1
            log_entries.append(f"Failed to send to {user_id}: {e}")

        await asyncio.sleep(0.5)  # To avoid hitting rate limits

    # Write log entries to a text file
    log_content = "\n".join(log_entries)
    with open("broadcast_log.txt", "w") as log_file:
        log_file.write(log_content)

    # Send summary to admin
    await msg.reply_text(f"Broadcast completed: {sent_count} sent, {failed_count} failed.")
    await msg.reply_document('broadcast_log.txt')
  
