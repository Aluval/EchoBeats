from pyrogram.types import Message
from pyrogram import Client, filters
from helper.database import db
from html_telegraph_poster import TelegraphPoster
from helper.utils import get_mediainfo

# Initialize Telegraph
telegraph = TelegraphPoster(use_api=True)
telegraph.create_api_token("MediaInfoBot")

@Client.on_message(filters.command("mediainfo") & filters.private)
async def mediainfo_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file to get MediaInfo.")
        return

    reply = message.reply_to_message
    audio = reply.audio

    # Send an acknowledgment message immediately
    processing_message = await message.reply_text("Getting MediaInfo...")

    try:
        # Download the audio file to a local location
        if audio:
            file_path = await client.download_media(audio)
        else:
            raise ValueError("No valid audio file found in the replied message.")

        # Get media info
        media_info_html = get_mediainfo(file_path)

        # Customize the media info output
        media_info_html = (
            f"<strong>SUNRISES 24 BOT UPDATES</strong><br>"
            f"<strong>MediaInfo X</strong><br>"
            f"{media_info_html}"
            f"<p>Rights Designed By Sᴜɴʀɪsᴇs Hᴀʀsʜᴀ 𝟸𝟺 🇮🇳 ᵀᴱᴸ</p>"
        )

        # Save the media info to an HTML file
        html_file_path = f"media_info_{audio.file_id}.html"
        with open(html_file_path, "w") as file:
            file.write(media_info_html)

        # Store media info in MongoDB
        media_info_data = {
            'media_info': media_info_html,
            'media_id': audio.file_id
        }
        media_info_id = await db.store_media_info_in_db(media_info_data)

        # Upload the media info to Telegraph
        response = telegraph.post(
            title="MediaInfo",
            author="SUNRISES 24 BOT UPDATES",
            author_url="https://t.me/Sunrises24BotUpdates",
            text=media_info_html
        )
        link = f"https://graph.org/{response['path']}"

        # Prepare the final message with the Telegraph link
        message_text = (
            f"SUNRISES 24 BOT UPDATES\n"
            f"MediaInfo X\n\n"
            f"[View Info on Telegraph]({link})\n"
            f"Rights Designed By Sᴜɴʀɪsᴇs Hᴀʀsʜᴀ 𝟸𝟺 🇮🇳 ᵀᴱᴸ"
        )

        # Send HTML file and Telegraph link
        await message.reply_document(document=html_file_path, caption=message_text)

    except Exception as e:
        await message.reply_text(f"Error: {e}")
    finally:
        # Clean up the acknowledgment message
        await processing_message.delete()

        # Clean up downloaded files and HTML file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'html_file_path' in locals() and os.path.exists(html_file_path):
            os.remove(html_file_path)

