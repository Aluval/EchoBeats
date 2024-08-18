

import os
import numpy as np
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest
import subprocess 

import re
import random
import shutil
import base64
import requests
import wget

# Configurations (Ideally loaded from environment variables or config file)
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAHmk19iP3uK79OglBISjicbl70TD6i9wEc'
SPOTIFY_CLIENT_ID = '8a9eab1a1a2948fbaa582389e1ae565b'
SPOTIFY_CLIENT_SECRET = 'e20f2cc4202146c3aa62ccf7ed83f80d'

credentials = base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode('utf-8')).decode('utf-8')


app = Client("slowreverb_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# Initialize the metadata dictionary
metadata = {
    "comment": "Default comment",
    "created_by": "Default creator",
    "title": "Default title"
}



@app.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_command(client, msg):
    # Extract metadata from the command message
    if len(msg.command) < 2:
        await msg.reply_text("Invalid command format. Use: /setmetadata comment | created_by | title")
        return
    
    parts = msg.text.split(" ", 1)[1].split(" | ")
    if len(parts) != 3:
        await msg.reply_text("Invalid number of metadata parts. Use: /setmetadata comment | created_by | title")
        return
    
    # Store the metadata locally
    metadata["comment"] = parts[0].strip()
    metadata["created_by"] = parts[1].strip()
    metadata["title"] = parts[2].strip()
    
    await msg.reply_text("Metadata set successfully ✅.")

def change_audio_metadata(input_path, output_path, comment, created_by, audio_title):
    temp_output = f"{os.path.splitext(output_path)[0]}_temp.flac"
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-metadata', f'comment={comment}',
        '-metadata', f'artist={created_by}',
        '-metadata', f'title={audio_title}',
        '-c', 'copy',
        temp_output,
        '-y'
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr.decode('utf-8')}")
    
    os.rename(temp_output, output_path)

def apply_slowreverb(audio_path, output_path, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2, slowfactor=0.08):
    # Convert to WAV if needed
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav
    
    # Load the audio file
    audio = AudioSegment.from_wav(audio_path)
    audio = audio.set_channels(2)  # Ensure the audio is stereo

    # Slow down the audio
    slowed_audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * (1 - slowfactor))
    })
    slowed_audio = slowed_audio.set_frame_rate(audio.frame_rate)

    # Export to temporary file
    temp_file = "temp_reverb.wav"
    slowed_audio.export(temp_file, format="wav")

    # Apply reverb using ffmpeg
    reverb_command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', temp_file,
        '-af', f"aecho={wet_level}:{damping}:{room_size}:{dry_level}", output_path
    ]
    subprocess.run(reverb_command)

    # Cleanup temporary files
    os.remove(temp_file)
    if audio_path == "tmp.wav":
        os.remove(audio_path)

@app.on_message(filters.command("slowreverb") & filters.private)
async def slow_reverb_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /slowreverb command.")
        return

    # Inform user about processing time
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")

    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_slowreverb.wav"

    # Apply the slow reverb effect
    apply_slowreverb(input_file, output_file)

    # Convert the output to FLAC with 24-bit depth and 48kHz sample rate
    final_output = f"{os.path.splitext(file_path)[0]}_slowreverb_24bit_48kHz.flac"
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', output_file, '-sample_fmt', 's32', '-ar', '48000', final_output])

    # Add metadata to the final FLAC file
    change_audio_metadata(final_output, final_output, metadata["comment"], metadata["created_by"], metadata["title"])

    # Cleanup intermediate files
    os.remove(file_path)
    os.remove(output_file)
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(final_output)





def apply_lofi_effect(audio_path, output_path):
    # Convert to WAV if needed
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
        audio_path = tmp_wav

    # Load the audio file
    audio = AudioSegment.from_wav(audio_path)
    
    # Apply lofi effect by lowering the sample rate and adding a lowpass filter
    lofi_audio = audio.set_frame_rate(22050).low_pass_filter(1000)
    
    # Export to output file
    lofi_audio.export(output_path, format="wav")
    
    # Cleanup temporary file
    if audio_path == "tmp.wav":
        os.remove(audio_path)

@app.on_message(filters.command("lofi") & filters.private)
async def lofi_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /lofi command.")
        return
    
    # Inform user about processing time
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_lofi.wav"
    
    # Apply the lofi effect
    apply_lofi_effect(input_file, output_file)
    
    # Convert the output to FLAC with 24-bit depth and 48kHz sample rate, and add metadata
    final_output = f"{os.path.splitext(file_path)[0]}_lofi_24bit_48kHz.flac"
    subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{output_file}" -sample_fmt s32 -ar 48000 -metadata comment="{metadata["comment"]}" -metadata created_by="{metadata["created_by"]}" -metadata title="{metadata["title"]}" "{final_output}"', shell=True)
    
    try:
        await message.reply_audio(audio=final_output)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    # Cleanup intermediate files
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)

def apply_8d_effect(audio_path, output_path):
    # Convert to WAV if needed
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
        audio_path = tmp_wav

    # Apply 8D effect using ffmpeg's aeval filter for a binaural panning effect
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', audio_path,
        '-af', 'apulsator=hz=0.1',
        output_path
    ]
    subprocess.call(command)
    
    # Cleanup temporary file
    if audio_path == "tmp.wav":
        os.remove(audio_path)

@app.on_message(filters.command("8d") & filters.private)
async def eight_d_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /8d command.")
        return
    
    # Inform user about processing time
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_8d.wav"
    
    # Apply the 8D effect
    apply_8d_effect(input_file, output_file)
    
    # Convert the output to FLAC with 24-bit depth and 48kHz sample rate, and add metadata
    final_output = f"{os.path.splitext(file_path)[0]}_8d_24bit_48kHz.flac"
    subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{output_file}" -sample_fmt s32 -ar 48000 -metadata comment="{metadata["comment"]}" -metadata created_by="{metadata["created_by"]}" -metadata title="{metadata["title"]}" "{final_output}"', shell=True)
    
    try:
        await message.reply_audio(audio=final_output)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    # Cleanup intermediate files
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)



def get_access_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.RequestException as e:
        raise Exception(f"Failed to get access token: {e}")

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

@app.on_message(filters.regex(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)'))
async def spotify(client, message):
    try:
        access_token = get_access_token()
        track_info = await fetch_track_info(message.text, access_token)
        
        thumbnail_url = track_info["album"]["images"][0]["url"]
        artist = track_info["artists"][0]["name"]
        name = track_info["name"]
        album = track_info["album"]["name"]
        release_date = track_info["album"]["release_date"]

        music = f"{name} {album}"
        thumbnail = wget.download(thumbnail_url)

        randomdir = f"/tmp/{random.randint(1, 100000000)}"
        os.makedirs(randomdir)
        path, info = await download_songs(music, randomdir)
        
        await message.reply_photo(photo=thumbnail_url, caption=f"🎧 Title: <code>{name}</code>\n🎼 Artist: <code>{artist}</code>\n🎤 Album: <code>{album}</code>\n🗓️ Release Date: <code>{release_date}</code>\n")
        
        await message.reply_audio(
            path,
            thumb=thumbnail
        )
        
        shutil.rmtree(randomdir)
        os.remove(thumbnail)
    
    except Exception as e:
        await message.reply_text(f"Error: {e}")
    
if __name__ == "__main__":
    app.run()

