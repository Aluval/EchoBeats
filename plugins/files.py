import psutil
import asyncio
import datetime, time
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

@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(_, msg):
    uptime = datetime.datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    total_space = psutil.disk_usage('/').total / (1024 ** 3)
    used_space = psutil.disk_usage('/').used / (1024 ** 3)
    free_space = psutil.disk_usage('/').free / (1024 ** 3)

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    stats_message = (
        "╔═════════════════════╗\n"
        "║  🖥️ **Server Dashboard**  ║\n"
        "╚═════════════════════╝\n\n"
        "╔═════════════════════╗\n"
        f"║  ⏳ **Uptime:** `{uptime_str}`  ║\n"
        "╠═════════════════════╣\n"
        f"║  💽 **Total Space:** `{total_space:.2f} GB`  ║\n"
        f"║  📉 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)  ║\n"
        f"║  🗃️ **Free Space:** `{free_space:.2f} GB`  ║\n"
        "╠═════════════════════╣\n"
        f"║  🧠 **CPU Usage:** `{cpu_usage:.1f}%`  ║\n"
        f"║  🧩 **RAM Usage:** `{ram_usage:.1f}%`  ║\n"
        "╚═════════════════════╝"
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
        "╔═════════════════════╗\n"
        "║  🖥️ **Server Dashboard**  ║\n"
        "╚═════════════════════╝\n\n"
        "╔═════════════════════╗\n"
        f"║  ⏳ **Uptime:** `{uptime_str}`  ║\n"
        "╠═════════════════════╣\n"
        f"║  💽 **Total Space:** `{total_space:.2f} GB`  ║\n"
        f"║  📉 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)  ║\n"
        f"║  🗃️ **Free Space:** `{free_space:.2f} GB`  ║\n"
        "╠═════════════════════╣\n"
        f"║  🧠 **CPU Usage:** `{cpu_usage:.1f}%`  ║\n"
        f"║  🧩 **RAM Usage:** `{ram_usage:.1f}%`  ║\n"
        "╚═════════════════════╝"
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
  

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
@Client.on_callback_query(filters.regex("del"))
async def closed(bot, msg):
    try:
        await msg.message.delete()
    except:
        return
#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
#FUNCTION ABOUT HANDLER
@Client.on_message(filters.command("about"))
async def about_command(bot, msg):
    about_text = """
<b>✯ Mʏ Nᴀᴍᴇ : <a href=https://t.me/MetaMorpher24Bot>𝐄𝐜𝐡𝐨𝐁𝐞𝐚𝐭𝐬𝟐𝟒𝐁𝐨𝐭 🎧</a></b>
<b>✯ Dᴇᴠᴇʟᴏᴘᴇʀ 🧑🏻‍💻 : <a href=https://t.me/Sunrises_24>𝐒𝐔𝐍𝐑𝐈𝐒𝐄𝐒™ ⚡</a></b>
<b>✯ Uᴘᴅᴀᴛᴇs 📢 : <a href=https://t.me/Sunrises24BotUpdates>𝐔𝐏𝐃𝐀𝐓𝐄𝐒 📢</a></b>
<b>✯ Sᴜᴘᴘᴏʀᴛ ✨ : <a href=https://t.me/Sunrises24BotUpdates>𝐒𝐔𝐏𝐏𝐎𝐑𝐓 ✨</a></b>
<b>✯ Bᴜɪʟᴅ Sᴛᴀᴛᴜs 📊 : ᴠ2.5 [Sᴛᴀʙʟᴇ]</b>
    """
    await msg.reply_text(about_text)

# Function to handle /help command
@Client.on_message(filters.command("help"))
async def help_command(bot, msg):
    help_text = """
    <b>Hᴇʟʟᴏ Mᴀᴡᴀ ❤️
Hᴇʀᴇ Is Tʜᴇ Hᴇʟᴘ Fᴏʀ Mʏ Cᴏᴍᴍᴀɴᴅs.

◉ Spotify - 𝑆ℎ𝑎𝑟𝑒 𝑇ℎ𝑒 𝑆𝑝𝑜𝑡𝑖𝑓𝑦 𝑇𝑟𝑎𝑐𝑘 𝑙𝑖𝑛𝑘 𝑡𝑜 𝑑𝑜𝑤𝑛𝑙𝑜𝑎𝑑🎼

🦋 ʜᴏᴡ ᴛᴏ ᴜꜱᴇ
◉ Reply To Any Video/File 🖼️

/start - 𝐵𝑜𝑡 𝑎𝑙𝑖𝑣𝑒 𝑜𝑟 𝑁𝑜𝑡 🚶🏻
/setmetadata - 𝑆𝑒𝑡 𝑀𝑒𝑡𝑎𝑑𝑎𝑡𝑎 𝐼𝑛𝑑𝑖𝑣𝑖𝑑𝑢𝑎𝑙 𝑇𝑖𝑡𝑙𝑒𝑠
/slowreverb - 𝐷𝑖𝑣𝑒 𝑖𝑛𝑡𝑜 𝑎 𝑑𝑟𝑒𝑎𝑚𝑦, 𝑠𝑙𝑜𝑤𝑒𝑑-𝑑𝑜𝑤𝑛 𝑤𝑜𝑟𝑙𝑑 𝑤𝑖𝑡ℎ 𝑟𝑒𝑣𝑒𝑟𝑏-𝑒𝑛ℎ𝑎𝑛𝑐𝑒𝑑 𝑡𝑟𝑎𝑐𝑘𝑠.
/lofi - 𝐶ℎ𝑖𝑙𝑙 𝑜𝑢𝑡 𝑤𝑖𝑡ℎ 𝑠𝑜𝑚𝑒 𝑚𝑒𝑙𝑙𝑜𝑤, 𝑙𝑜𝑓𝑖 𝑏𝑒𝑎𝑡𝑠 𝑡𝑎𝑖𝑙𝑜𝑟𝑒𝑑 𝑗𝑢𝑠𝑡 𝑓𝑜𝑟 𝑦𝑜𝑢.
/8d - 𝐺𝑒𝑡 𝑙𝑜𝑠𝑡 𝑖𝑛 𝑡ℎ𝑒 𝑖𝑚𝑚𝑒𝑟𝑠𝑖𝑣𝑒 8𝐷 𝑎𝑢𝑑𝑖𝑜 𝑡ℎ𝑎𝑡 𝑠𝑢𝑟𝑟𝑜𝑢𝑛𝑑𝑠 𝑦𝑜𝑢 𝑓𝑟𝑜𝑚 𝑎𝑙𝑙 𝑑𝑖𝑟𝑒𝑐𝑡𝑖𝑜𝑛𝑠.
/mediainfo - 𝑈𝑛𝑐𝑜𝑣𝑒𝑟 𝑒𝑣𝑒𝑟𝑦 𝑑𝑒𝑡𝑎𝑖𝑙 𝑜𝑓 𝑦𝑜𝑢𝑟 𝑀𝑒𝑑𝑖𝑎 𝐴𝑢𝑑𝑖𝑜 𝐹𝑖𝑙𝑒 𝑤𝑖𝑡ℎ 𝑎𝑛 𝑖𝑛-𝑑𝑒𝑝𝑡ℎ 𝑖𝑛𝑓𝑜.
/clear - 𝑐𝑙𝑒𝑎𝑟 𝑡ℎ𝑒 𝑑𝑎𝑡𝑎𝑏𝑎𝑠𝑒
/stats - 𝑠𝑡𝑎𝑡𝑠 𝑜𝑓 𝑡ℎ𝑒 𝑏𝑜𝑡 📊
/users - 𝐴𝑐𝑡𝑖𝑣𝑒 𝑢𝑠𝑒𝑟𝑠 𝑜𝑓 𝑏𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/ban - 𝐵𝑎𝑛 𝑡ℎ𝑒 𝑢𝑠𝑒𝑟 𝑓𝑟𝑜𝑚  𝐵𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/unban - 𝑈𝑛𝑏𝑎𝑛 𝑡ℎ𝑒 𝑢𝑠𝑒𝑟 𝑓𝑟𝑜𝑚  𝐵𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/broadcast  -  𝑀𝑒𝑠𝑠𝑎𝑔𝑒𝑠 𝑡𝑜 𝐸𝑣𝑒𝑟𝑦 𝑈𝑠𝑒𝑟𝑠 𝑖𝑛 𝑏𝑜𝑡 [𝐴𝑑𝑚𝑖𝑛]
/help - 𝐺𝑒𝑡 𝑑𝑒𝑡𝑎𝑖𝑙𝑒𝑑 𝑜𝑓 𝑏𝑜𝑡 𝑐𝑜𝑚𝑚𝑎𝑛𝑑𝑠 📝
/about - 𝐿𝑒𝑎𝑟𝑛 𝑚𝑜𝑟𝑒 𝑎𝑏𝑜𝑢𝑡 𝑡ℎ𝑖𝑠 𝑏𝑜𝑡 🧑🏻‍💻
/ping - 𝑇𝑜 𝐶ℎ𝑒𝑐𝑘 𝑇ℎ𝑒 𝑃𝑖𝑛𝑔 𝑂𝑓 𝑇ℎ𝑒 𝐵𝑜𝑡 📍

 • **🎧 𝑇ℎ𝑖𝑠 𝐵𝑜𝑡 𝑆𝑝𝑒𝑐𝑖𝑎𝑙𝑖𝑧𝑒𝑠 𝑖𝑛 𝑀𝑢𝑠𝑖𝑐 𝑀𝑎𝑔𝑖𝑐:**

• 𝐿𝑜𝑓𝑖 𝑉𝑖𝑏𝑒𝑠: 𝐶ℎ𝑖𝑙𝑙 𝑜𝑢𝑡 𝑤𝑖𝑡ℎ 𝑐𝑢𝑠𝑡𝑜𝑚 𝑙𝑜𝑓𝑖 𝑏𝑒𝑎𝑡𝑠.
• 𝐸𝑐ℎ𝑜𝑒𝑑 𝐵𝑒𝑎𝑡𝑠: 𝐸𝑥𝑝𝑒𝑟𝑖𝑒𝑛𝑐𝑒 𝑠𝑙𝑜𝑤 𝑟𝑒𝑣𝑒𝑟𝑏-𝑒𝑛ℎ𝑎𝑛𝑐𝑒𝑑 𝑡𝑟𝑎𝑐𝑘𝑠.
• 𝐼𝑚𝑚𝑒𝑟𝑠𝑖𝑣𝑒 𝑆𝑜𝑢𝑛𝑑: 𝐷𝑖𝑣𝑒 𝑖𝑛𝑡𝑜 𝑡ℎ𝑒 𝑤𝑜𝑟𝑙𝑑 𝑜𝑓 8𝐷 𝑎𝑢𝑑𝑖𝑜.

🔱 𝐌𝐚𝐢𝐧𝐭𝐚𝐢𝐧𝐞𝐝 𝐁𝐲 : <a href='https://t.me/Sunrises_24'>𝐒𝐔𝐍𝐑𝐈𝐒𝐄𝐒™</a></b>
    
   """
    await msg.reply_text(help_text)
    

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
#Ping
@Client.on_message(filters.command("ping"))
async def ping(bot, msg):
    start_t = time.time()
    rm = await msg.reply_text("Checking")
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rm.edit(f"Pong!📍\n{time_taken_s:.3f} ms")

