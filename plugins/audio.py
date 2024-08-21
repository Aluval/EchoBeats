import os, re
import numpy as np
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest
import subprocess 
import random
import shutil
import base64
import requests
import wget
from yt_dlp import YoutubeDL
from helper.ffmpeg import change_audio_metadata, run_ffmpeg_command
from helper.utils import apply_slowreverb, apply_lofi_effect, apply_8d_effect

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
