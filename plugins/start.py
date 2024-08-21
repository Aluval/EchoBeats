#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
import asyncio, time
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import UserNotParticipant, UserBannedInChannel
from config import *
from helper.database import db
from pymongo.errors import PyMongoError



START_TEXT = """
Hᴇʟʟᴏ Mᴀᴡᴀ❤️! I ᴀᴍ ᴛʜᴇ EᴄʜᴏBᴇᴀᴛs𝟸𝟺Bᴏᴛ ⚡

• Lᴏғɪ Vɪʙᴇs: Cʜɪʟʟ ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ʟᴏғɪ ʙᴇᴀᴛs.
• Eᴄʜᴏᴇᴅ Bᴇᴀᴛs: Exᴘᴇʀɪᴇɴᴄᴇ sʟᴏᴡ ʀᴇᴠᴇʀʙ-ᴇɴʜᴀɴᴄᴇᴅ ᴛʀᴀᴄᴋs.
• Iᴍᴍᴇʀsɪᴠᴇ Sᴏᴜɴᴅ: Dɪᴠᴇ ɪɴᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ ᴏғ 𝟾D ᴀᴜᴅɪᴏ.

#SUNRISES24BOTS
#EchoBeats24Bot
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
    
