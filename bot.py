
"""
import os
import numpy as np
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest
import subprocess 

# Initialize the bot with your credentials
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAFKWhBga4p9sqXT9OcaYt41nQz14IVmQyA'

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
    
if __name__ == "__main__":
    app.run()

"""

import os
import subprocess
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest

# Initialize the bot with your credentials
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAHmk19iP3uK79OglBISjicbl70TD6i9wEc'

app = Client("music_converter_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Initialize the metadata dictionary
metadata = {
    "comment": "Default comment",
    "created_by": "Default creator",
    "title": "Default title"
}

def best_settings_buttons():
    keyboard = [
        [InlineKeyboardButton("High Quality Bitrate (320 kbps)", callback_data="bitrate_320")],
        [InlineKeyboardButton("Standard Quality Bitrate (192 kbps)", callback_data="bitrate_192")],
        [InlineKeyboardButton("Increase Volume (+3 dB)", callback_data="volume_increase")],
        [InlineKeyboardButton("Moderate Noise Reduction (0.5)", callback_data="noise_reduction_0.5")],
        [InlineKeyboardButton("Low Compression (0.2)", callback_data="compression_0.2")],
        [InlineKeyboardButton("Apply Settings", callback_data="apply_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

@app.on_message(filters.command("settings") & filters.private)
async def show_settings(client, message):
    await message.reply_text(
        "Select the best settings for your audio processing:",
        reply_markup=best_settings_buttons()
    )

@app.on_callback_query()
async def handle_callback_query(client, query):
    data = query.data
    settings = {}
    if data.startswith("bitrate"):
        settings['bitrate'] = int(data.split("_")[1])
        await query.message.edit_text(f"Selected Bitrate: {settings['bitrate']} kbps")
    elif data.startswith("volume"):
        settings['volume'] = float(data.split("_")[1])
        await query.message.edit_text(f"Selected Volume: {settings['volume']} dB")
    elif data.startswith("noise_reduction"):
        settings['noise_reduction'] = float(data.split("_")[1])
        await query.message.edit_text(f"Selected Noise Reduction: {settings['noise_reduction']}")
    elif data.startswith("compression"):
        settings['compression'] = float(data.split("_")[1])
        await query.message.edit_text(f"Selected Compression: {settings['compression']}")
    elif data == "apply_settings":
        await query.message.edit_text("Settings applied. You can now process your audio.")
        # Apply settings to the audio processing functions as needed
        # For demonstration, settings are printed. Implement actual application of settings here.
        print(settings)
    else:
        await query.message.edit_text("Invalid selection.")

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
async def slow_reverb_handler(client, message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /slowreverb command.")
        return

    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")

    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_slowreverb.wav"

    apply_slowreverb(input_file, output_file)

    final_output = f"{os.path.splitext(file_path)[0]}_slowreverb_24bit_48kHz.flac"
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', output_file, '-sample_fmt', 's32', '-ar', '48000', final_output])

    change_audio_metadata(final_output, final_output, metadata["comment"], metadata["created_by"], metadata["title"])

    os.remove(file_path)
    os.remove(output_file)
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(final_output)

def apply_lofi_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
        audio_path = tmp_wav

    audio = AudioSegment.from_wav(audio_path)
    lofi_audio = audio.set_frame_rate(22050).low_pass_filter(1000)
    lofi_audio.export(output_path, format="wav")
    
    if audio_path == "tmp.wav":
        os.remove(audio_path)

@app.on_message(filters.command("lofi") & filters.private)
async def lofi_handler(client, message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /lofi command.")
        return
    
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_lofi.wav"
    
    apply_lofi_effect(input_file, output_file)
    
    final_output = f"{os.path.splitext(file_path)[0]}_lofi_24bit_48kHz.flac"
    subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{output_file}" -sample_fmt s32 -ar 48000 -metadata comment="{metadata["comment"]}" -metadata created_by="{metadata["created_by"]}" -metadata title="{metadata["title"]}" "{final_output}"', shell=True)
    
    try:
        await message.reply_audio(audio=final_output)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)

def apply_8d_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
        audio_path = tmp_wav

    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', audio_path,
        '-af', 'apulsator=hz=0.1',
        output_path
    ]
    subprocess.call(command)
    
    if audio_path == "tmp.wav":
        os.remove(audio_path)
        
@app.on_message(filters.command("8d") & filters.private)
async def eight_d_handler(client, message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /8d command.")
        return
    
    await message.reply_text("Processing your request. Please wait for 2 to 4 minutes.")
    
    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)
    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_8d.wav"
    
    apply_8d_effect(input_file, output_file)
    
    final_output = f"{os.path.splitext(file_path)[0]}_8d_24bit_48kHz.flac"
    subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{output_file}" -sample_fmt s32 -ar 48000 -metadata comment="{metadata["comment"]}" -metadata created_by="{metadata["created_by"]}" -metadata title="{metadata["title"]}" "{final_output}"', shell=True)
    
    try:
        await message.reply_audio(audio=final_output)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(file_path)
    os.remove(output_file)
    os.remove(final_output)

if __name__ == "__main__":
    app.run()
