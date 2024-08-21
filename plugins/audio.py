import motor.motor_asyncio
from pyrogram import Client, filters
import os
import subprocess
from pyrogram.types import Message





# Apply 8D effect function
def apply_8d_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav

    # Apply 8D effect using ffmpeg
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', audio_path,
        '-af', 'apulsator=hz=0.1',
        output_path
    ]
    run_ffmpeg_command(command)
    
    # Cleanup temporary file
    if audio_path == "tmp.wav":
        os.remove(audio_path)

# /8d command handler
@app.on_message(filters.command("8d") & filters.private)
async def eight_d_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /8d command.")
        return
    
    # Inform user about processing time
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    # Fetch metadata from the database
    metadata = await db.get_user_metadata(user_id)
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_8d.wav"
    
    # Apply the 8D effect
    apply_8d_effect(input_file, output_file)
    
    # Convert the output to FLAC with 24-bit depth and 48kHz sample rate
    final_output = f"{os.path.splitext(file_path)[0]}_8d_24bit_48kHz.flac"
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', output_file,
        '-sample_fmt', 's32',
        '-ar', '48000',
        final_output
    ]
    run_ffmpeg_command(command)
    
    # Add metadata to the final FLAC file
    change_audio_metadata(final_output, final_output,
                          metadata.get("comment", "Default comment"),
                          metadata.get("created_by", "Default creator"),
                          metadata.get("title", "Default title"))
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    # Cleanup intermediate files
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)


import motor.motor_asyncio
from pyrogram import Client, filters
import os
import subprocess
from pyrogram.types import Message
from pydub import AudioSegment

# Initialize your database connection
class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db["users"]

    async def get_user_metadata(self, user_id):
        user = await self.users_col.find_one({"user_id": user_id})
        return user.get("metadata", {}) if user else {}

db = Database("mongodb_uri", "database_name")

# Helper function to run ffmpeg commands
def run_ffmpeg_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr.decode('utf-8')}")
    return result

# Change Audio Metadata function
def change_audio_metadata(input_path, output_path, comment, created_by, audio_title):
    temp_output = f"{os.path.splitext(output_path)[0]}_temp.flac"
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-metadata', f'comment={comment}',
        '-metadata', f'created_by={created_by}',
        '-metadata', f'title={audio_title}',
        '-c', 'copy',
        temp_output,
        '-y'
    ]
    
    run_ffmpeg_command(command)
    os.rename(temp_output, output_path)

# Apply Slow Reverb effect function
def apply_slowreverb(audio_path, output_path, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2, slowfactor=0.08):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav
    
    audio = AudioSegment.from_wav(audio_path)
    slowed_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * (1 - slowfactor))})
    slowed_audio = slowed_audio.set_frame_rate(audio.frame_rate)
    temp_file = "temp_reverb.wav"
    slowed_audio.export(temp_file, format="wav")
    
    reverb_command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', temp_file,
        '-af', f"aecho={wet_level}:{damping}:{room_size}:{dry_level}", output_path
    ]
    run_ffmpeg_command(reverb_command)
    
    os.remove(temp_file)
    if audio_path == "tmp.wav":
        os.remove(audio_path)

# Apply LOFI effect function
def apply_lofi_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav
    
    audio = AudioSegment.from_wav(audio_path)
    lofi_audio = audio.set_frame_rate(22050).low_pass_filter(1000)
    lofi_audio.export(output_path, format="wav")
    
    if audio_path == "tmp.wav":
        os.remove(audio_path)

# /slowreverb command handler
@app.on_message(filters.command("slowreverb") & filters.private)
async def slow_reverb_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /slowreverb command.")
        return
    
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    metadata = await db.get_user_metadata(user_id)
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_slowreverb.wav"
    
    apply_slowreverb(input_file, output_file)
    
    final_output = f"{os.path.splitext(file_path)[0]}_slowreverb_24bit_48kHz.flac"
    run_ffmpeg_command([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', output_file,
        '-sample_fmt', 's32',
        '-ar', '48000',
        final_output
    ])
    
    change_audio_metadata(final_output, final_output,
                          metadata.get("comment", "Default comment"),
                          metadata.get("created_by", "Default creator"),
                          metadata.get("title", "Default title"))
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)

# /lofi command handler
@app.on_message(filters.command("lofi") & filters.private)
async def lofi_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /lofi command.")
        return
    
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    metadata = await db.get_user_metadata(user_id)
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_lofi.wav"
    
    apply_lofi_effect(input_file, output_file)
    
    final_output = f"{os.path.splitext(file_path)[0]}_lofi_24bit_48kHz.flac"
    run_ffmpeg_command([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', output_file,
        '-sample_fmt', 's32',
        '-ar', '48000',
        '-metadata', f'comment={metadata.get("comment", "Default comment")}',
        '-metadata', f'created_by={metadata.get("created_by", "Default creator")}',
        '-metadata', f'title={metadata.get("title", "Default title")}',
        final_output
    ])
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)

import motor.motor_asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Initialize your database connection
class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db["users"]

    async def get_user_metadata(self, user_id):
        user = await self.users_col.find_one({"user_id": user_id})
        return user.get("metadata", {}) if user else {}

    async def set_user_metadata(self, user_id, metadata):
        await self.users_col.update_one(
            {"user_id": user_id},
            {"$set": {"metadata": metadata}},
            upsert=True
        )

db = Database("mongodb_uri", "database_name")

@app.on_message(filters.command("setmetadata") & filters.private)
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
