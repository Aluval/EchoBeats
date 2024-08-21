#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
import asyncio, time
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import UserNotParticipant, UserBannedInChannel
from config import *
from helper.database import db
from pymongo.errors import PyMongoError



START_TEXT = """
Hᴇʟʟᴏ Mᴀᴡа❤️! I ᴀᴍ ᴛʜᴇ Aᴅᴠᴀɴᴄᴇᴅ 𝟸𝟺 Bᴏᴛ ⚡

Mᴀᴅᴇ ʙʏ <b><a href=https://t.me/Sunrises24botupdates>SUNRISES ™💥</a></b> ᴀɴᴅ <b><a href=https://t.me/Sunrises_24>Sᴜɴʀɪꜱᴇꜱ Hᴀʀꜱʜᴀ 𝟸𝟺❤️</a></b>.

#SUNRISES24BOTS 
"""

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24


joined_channel_1 = {}
joined_channel_2 = {}

@Client.on_message(filters.command("start"))
async def start(bot, msg: Message):
    user_id = msg.chat.id
    username = msg.from_user.username or "N/A"

    # Check if user is banned
    if await db.is_user_banned(user_id):
        await msg.reply_text("Sorry, you are banned 🚫. Contact admin for more information ℹ️.")
        return

    # Fetch user from the database or add a new user
    user_data = await db.get_user(user_id)
    if user_data is None:
        await db.add_user(user_id, username)
        user_data = await db.get_user(user_id)

    # Check for channel 1 (updates channel) membership
    if FSUB_UPDATES:
        try:
            user = await bot.get_chat_member(FSUB_UPDATES, user_id)
            if user.status == "kicked":
                await msg.reply_text("Sorry, you are banned 🚫. Contact admin for more information ℹ️.")
                return
        except UserNotParticipant:
            await msg.reply_text(
                text="**Please join my first updates channel before using me.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="Join Updates Channel", url=f"https://t.me/{FSUB_UPDATES}")]
                ])
            )
            joined_channel_1[user_id] = False
            return
        else:
            joined_channel_1[user_id] = True

    # Check for channel 2 (group) membership
    if FSUB_GROUP:
        try:
            user = await bot.get_chat_member(FSUB_GROUP, user_id)
            if user.status == "kicked":
                await msg.reply_text("Sorry, you are banned 🚫. Contact admin for more information ℹ️.")
                return
        except UserNotParticipant:
            await msg.reply_text(
                text="**Please join my Group before using me.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="JOIN GROUP", url=f"https://t.me/{FSUB_GROUP}")]
                ])
            )
            joined_channel_2[user_id] = False
            return
        else:
            joined_channel_2[user_id] = True

    # Update user's membership status in the database
    await db.update_user_membership(
        user_id,
        joined_channel_1.get(user_id, False),
        joined_channel_2.get(user_id, False)
    )

    # If the user has joined both required channels, send the start message with photo
    if joined_channel_1.get(user_id, False) and joined_channel_2.get(user_id, False):
        start_text = START_TEXT.format(msg.from_user.first_name) if hasattr(msg, "message_id") else START_TEXT
        await bot.send_photo(
            chat_id=user_id,
            photo=SUNRISES_PIC,
            caption=start_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Developer ❤️", url="https://t.me/Sunrises_24"),
                 InlineKeyboardButton("Updates 📢", url="https://t.me/Sunrises24botupdates")],
                [InlineKeyboardButton("Help 🌟", callback_data="help"),
                 InlineKeyboardButton("About 🧑🏻‍💻", callback_data="about")],
                [InlineKeyboardButton("Support ❤️‍🔥", url="https://t.me/Sunrises24botSupport")]
            ]),
            reply_to_message_id=getattr(msg, "message_id", None)
        )
    else:
        await msg.reply_text(
            "You need to join both the updates channel and the group to use the bot."
        )

    # Notify log channel
    log_message = (
        f"💬 **Bot Started**\n"
        f"🆔 **ID**: {user_id}\n"
        f"👤 **Username**: {username}"
    )
    try:
        await bot.send_message(LOG_CHANNEL_ID, log_message)
    except Exception as e:
        print(f"An error occurred while sending log message: {e}")

async def check_membership(bot, msg: Message, fsub, joined_channel_dict, prompt_text, join_url):
    user_id = msg.chat.id
    if user_id in joined_channel_dict and not joined_channel_dict[user_id]:
        await msg.reply_text(
            text=prompt_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="Join Now", url=join_url)]
            ])
        )
        return False
    return True

@Client.on_message(filters.private & ~filters.command("start"))
async def handle_private_message(bot, msg: Message):
    user_id = msg.chat.id

    # Check if user is banned
    if await db.is_user_banned(user_id):
        await msg.reply_text("Sorry, you are banned 🚫. Contact admin for more information ℹ️.")
        return
    
    # Check membership for updates channel
    if FSUB_UPDATES and not await check_membership(bot, msg, FSUB_UPDATES, joined_channel_1, "Please join my first updates channel before using me.", f"https://t.me/{FSUB_UPDATES}"):
        return
    
    # Check membership for group channel
    if FSUB_GROUP and not await check_membership(bot, msg, FSUB_GROUP, joined_channel_2, "Please join my Group before using me.", f"https://t.me/{FSUB_GROUP}"):
        return
        

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
#FUNCTION CALLBACK HELP
@Client.on_callback_query(filters.regex("help"))
async def help(bot, msg):
    txt =  "Fᴏʀ ᴀssɪsᴛᴀɴᴄᴇ, ᴄʟɪᴄᴋ ᴛʜᴇ 'Hᴇʟᴘ' ʙᴜᴛᴛᴏɴ ᴏʀ ᴛʏᴘᴇ ᴛʜᴇ `/help` ᴄᴏᴍᴍᴀɴᴅ ғᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ɪɴsᴛʀᴜᴄᴛɪᴏɴs ᴀɴᴅ sᴜᴘᴘᴏʀᴛ.\n\n"
    txt += "Jᴏɪɴ : @Sunrises24BotUpdates"
    button= [[        
        InlineKeyboardButton("Cʟᴏꜱᴇ ❌", callback_data="del")   
    ]] 
    await msg.message.edit(text=txt, reply_markup=InlineKeyboardMarkup(button), disable_web_page_preview = True)
 
#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
#FUNCTION CALL BACK ABOUT
@Client.on_callback_query(filters.regex("about"))
async def about(bot, msg):
    me=await bot.get_me()
    Dᴇᴠᴇʟᴏᴘᴇʀ ="<a href=https://t.me/Sunrises_24>SUNRISES™🧑🏻‍💻</a>"     
    txt="<b>Uᴘᴅᴀᴛᴇs 📢: <a href=https://t.me/Sunrises24botupdates>SUNRISES™</a></b>"
    txt="<b>Sᴜᴘᴘᴏʀᴛ ✨: <a href=https://t.me/Sunrises24botSupport>SUNRISES⚡™</a></b>"
    txt="<b>✯ Bᴜɪʟᴅ Sᴛᴀᴛᴜs 📊 : ᴠ2.4 [Sᴛᴀʙʟᴇ]</b>" 
    button= [[        
        InlineKeyboardButton("Cʟᴏꜱᴇ ❌", callback_data="del")       
    ]]  
    await msg.message.edit(text=txt, reply_markup=InlineKeyboardMarkup(button), disable_web_page_preview = True, parse_mode=enums.ParseMode.HTML)

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
<b>✯ Mʏ Nᴀᴍᴇ : <a href=https://t.me/MetaMorpher24Bot>𝐌𝐞𝐭𝐚𝐌𝐨𝐫𝐩𝐡𝐞𝐫 🌟</a></b>
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

🦋 ʜᴏᴡ ᴛᴏ ᴜꜱᴇ
◉ Reply To Any Video/File 🖼️

/start - 𝐵𝑜𝑡 𝑎𝑙𝑖𝑣𝑒 𝑜𝑟 𝑁𝑜𝑡 🚶🏻
/clear - 𝑐𝑙𝑒𝑎𝑟 𝑡ℎ𝑒 𝑑𝑎𝑡𝑎𝑏𝑎𝑠𝑒
/stats - 𝑠𝑡𝑎𝑡𝑠 𝑜𝑓 𝑡ℎ𝑒 𝑏𝑜𝑡 📊
/users - 𝐴𝑐𝑡𝑖𝑣𝑒 𝑢𝑠𝑒𝑟𝑠 𝑜𝑓 𝑏𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/ban - 𝐵𝑎𝑛 𝑡ℎ𝑒 𝑢𝑠𝑒𝑟 𝑓𝑟𝑜𝑚  𝐵𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/unban - 𝑈𝑛𝑏𝑎𝑛 𝑡ℎ𝑒 𝑢𝑠𝑒𝑟 𝑓𝑟𝑜𝑚  𝐵𝑜𝑡[𝐴𝑑𝑚𝑖𝑛]
/broadcast  -  𝑀𝑒𝑠𝑠𝑎𝑔𝑒𝑠 𝑡𝑜 𝐸𝑣𝑒𝑟𝑦 𝑈𝑠𝑒𝑟𝑠 𝑖𝑛 𝑏𝑜𝑡 [𝐴𝑑𝑚𝑖𝑛]
/help - 𝐺𝑒𝑡 𝑑𝑒𝑡𝑎𝑖𝑙𝑒𝑑 𝑜𝑓 𝑏𝑜𝑡 𝑐𝑜𝑚𝑚𝑎𝑛𝑑𝑠 📝
/about - 𝐿𝑒𝑎𝑟𝑛 𝑚𝑜𝑟𝑒 𝑎𝑏𝑜𝑢𝑡 𝑡ℎ𝑖𝑠 𝑏𝑜𝑡 🧑🏻‍💻
/ping - 𝑇𝑜 𝐶ℎ𝑒𝑐𝑘 𝑇ℎ𝑒 𝑃𝑖𝑛𝑔 𝑂𝑓 𝑇ℎ𝑒 𝐵𝑜𝑡 📍

 💭• Tʜɪs Bᴏᴛ Is Fᴏʟʟᴏᴡs ᴛʜᴇ 𝟸GB Bᴇʟᴏᴡ Fɪʟᴇs Tᴏ Tᴇʟᴇɢʀᴀᴍ.\n• 𝟸GB Aʙᴏᴠᴇ Fɪʟᴇs Tᴏ Gᴏᴏɢʟᴇ Dʀɪᴠᴇ.
 
🔱 𝐌𝐚𝐢𝐧𝐭𝐚𝐢𝐧𝐞𝐝 𝐁𝐲 : <a href='https://t.me/Sunrises_24'>𝐒𝐔𝐍𝐑𝐈𝐒𝐄𝐒™</a></b>
    
   """
    await msg.reply_text(help_text)
    

  
