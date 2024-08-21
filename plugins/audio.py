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
from helper.utils import apply_slowreverb, apply_lofi_effect, apply_8d_effect, get_access_token, download_songs
from helper.database import db

# /slowreverb command handler
@Client.on_message(filters.command("slowreverb") & filters.private)
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
@Client.on_message(filters.command("lofi") & filters.private)
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
@Client.on_message(filters.command("8d") & filters.private)
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


async def fetch_track_info(song_name_or_url, access_token):
    if re.match(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)', song_name_or_url):
        song_id = re.match(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)', song_name_or_url).group(1)
    else:
        search_url = f'https://api.spotify.com/v1/search?q={song_name_or_url}&type=track'
        search_headers = {"Authorization": f"Bearer {access_token}"}
        try:
            search_response = requests.get(search_url, headers=search_headers)
            search_response.raise_for_status()
            search_data = search_response.json()
            song_id = search_data["tracks"]["items"][0]["id"]
        except requests.RequestException as e:
            raise Exception(f"Failed to search for track: {e}")

    track_url = f'https://api.spotify.com/v1/tracks/{song_id}'
    try:
        track_response = requests.get(track_url, headers={"Authorization": f"Bearer {access_token}"})
        track_response.raise_for_status()
        return track_response.json()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch track info: {e}")


