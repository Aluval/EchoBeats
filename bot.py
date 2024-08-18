
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
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import BadRequest

api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAFKWhBga4p9sqXT9OcaYt41nQz14IVmQyA'

app = Client("audio_settings_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store user preferences
user_preferences = {}

@app.on_message(filters.command("settings") & filters.private)
async def settings_handler(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Audio Quality", callback_data="audio_quality")],
        [InlineKeyboardButton("Audio Speed", callback_data="audio_speed")],
        [InlineKeyboardButton("Audio Compress", callback_data="audio_compress")],
        [InlineKeyboardButton("Bass Booster", callback_data="bass_booster")],
        [InlineKeyboardButton("Treble Booster", callback_data="treble_booster")],
        [InlineKeyboardButton("Audio Volume", callback_data="audio_volume")],
        [InlineKeyboardButton("Audio Reverb", callback_data="audio_reverb")],
        [InlineKeyboardButton("8D Settings", callback_data="8d_settings")],
        [InlineKeyboardButton("← Back", callback_data="back")]
    ])
    await message.reply_text("Select the setting you want to adjust:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("back"))
async def back_handler(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("Back to main menu", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Settings", callback_data="settings")]
    ]))

@app.on_callback_query(filters.regex("audio_quality"))
async def audio_quality_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("8 kbps", callback_data="quality_8"),
         InlineKeyboardButton("16 kbps", callback_data="quality_16"),
         InlineKeyboardButton("24 kbps", callback_data="quality_24")],
        [InlineKeyboardButton("32 kbps", callback_data="quality_32"),
         InlineKeyboardButton("40 kbps", callback_data="quality_40"),
         InlineKeyboardButton("64 kbps", callback_data="quality_64")],
        [InlineKeyboardButton("80 kbps", callback_data="quality_80"),
         InlineKeyboardButton("96 kbps", callback_data="quality_96"),
         InlineKeyboardButton("112 kbps", callback_data="quality_112")],
        [InlineKeyboardButton("128 kbps", callback_data="quality_128"),
         InlineKeyboardButton("160 kbps", callback_data="quality_160"),
         InlineKeyboardButton("192 kbps", callback_data="quality_192")],
        [InlineKeyboardButton("224 kbps", callback_data="quality_224"),
         InlineKeyboardButton("256 kbps", callback_data="quality_256"),
         InlineKeyboardButton("320 kbps", callback_data="quality_320")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select audio quality in kbps:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("audio_speed"))
async def audio_speed_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("50%", callback_data="speed_50"),
         InlineKeyboardButton("60%", callback_data="speed_60"),
         InlineKeyboardButton("70%", callback_data="speed_70")],
        [InlineKeyboardButton("80%", callback_data="speed_80"),
         InlineKeyboardButton("90%", callback_data="speed_90"),
         InlineKeyboardButton("100%", callback_data="speed_100")],
        [InlineKeyboardButton("110%", callback_data="speed_110"),
         InlineKeyboardButton("120%", callback_data="speed_120"),
         InlineKeyboardButton("130%", callback_data="speed_130")],
        [InlineKeyboardButton("140%", callback_data="speed_140"),
         InlineKeyboardButton("150%", callback_data="speed_150"),
         InlineKeyboardButton("160%", callback_data="speed_160")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select audio speed percentage:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("audio_compress"))
async def audio_compress_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("0", callback_data="compress_0"),
         InlineKeyboardButton("1", callback_data="compress_1"),
         InlineKeyboardButton("2", callback_data="compress_2")],
        [InlineKeyboardButton("3", callback_data="compress_3"),
         InlineKeyboardButton("4", callback_data="compress_4"),
         InlineKeyboardButton("5", callback_data="compress_5")],
        [InlineKeyboardButton("6", callback_data="compress_6"),
         InlineKeyboardButton("7", callback_data="compress_7"),
         InlineKeyboardButton("8", callback_data="compress_8")],
        [InlineKeyboardButton("9", callback_data="compress_9")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select audio compression level:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("bass_booster"))
async def bass_booster_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("-20 dB", callback_data="bass_-20"),
         InlineKeyboardButton("-10 dB", callback_data="bass_-10"),
         InlineKeyboardButton("0 dB", callback_data="bass_0")],
        [InlineKeyboardButton("10 dB", callback_data="bass_10"),
         InlineKeyboardButton("20 dB", callback_data="bass_20")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select bass booster level (dB):", reply_markup=keyboard)

@app.on_callback_query(filters.regex("treble_booster"))
async def treble_booster_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("-20 dB", callback_data="treble_-20"),
         InlineKeyboardButton("-10 dB", callback_data="treble_-10"),
         InlineKeyboardButton("0 dB", callback_data="treble_0")],
        [InlineKeyboardButton("10 dB", callback_data="treble_10"),
         InlineKeyboardButton("20 dB", callback_data="treble_20")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select treble booster level (dB):", reply_markup=keyboard)

@app.on_callback_query(filters.regex("audio_volume"))
async def audio_volume_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("10%", callback_data="volume_10"),
         InlineKeyboardButton("20%", callback_data="volume_20"),
         InlineKeyboardButton("30%", callback_data="volume_30")],
        [InlineKeyboardButton("40%", callback_data="volume_40"),
         InlineKeyboardButton("50%", callback_data="volume_50"),
         InlineKeyboardButton("60%", callback_data="volume_60")],
        [InlineKeyboardButton("70%", callback_data="volume_70"),
         InlineKeyboardButton("80%", callback_data="volume_80"),
         InlineKeyboardButton("90%", callback_data="volume_90")],
        [InlineKeyboardButton("100%", callback_data="volume_100")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select audio volume percentage:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("audio_reverb"))
async def audio_reverb_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("0%", callback_data="reverb_0"),
         InlineKeyboardButton("10%", callback_data="reverb_10"),
         InlineKeyboardButton("20%", callback_data="reverb_20")],
        [InlineKeyboardButton("30%", callback_data="reverb_30"),
         InlineKeyboardButton("40%", callback_data="reverb_40"),
         InlineKeyboardButton("50%", callback_data="reverb_50")],
        [InlineKeyboardButton("60%", callback_data="reverb_60"),
         InlineKeyboardButton("70%", callback_data="reverb_70"),
         InlineKeyboardButton("80%", callback_data="reverb_80")],
        [InlineKeyboardButton("90%", callback_data="reverb_90"),
         InlineKeyboardButton("100%", callback_data="reverb_100")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Select reverb percentage:", reply_markup=keyboard)



@app.on_callback_query(filters.regex("8d_settings"))
async def eight_d_settings_handler(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Sine", callback_data="8d_sine"),
         InlineKeyboardButton("Triangle", callback_data="8d_triangle")],
        [InlineKeyboardButton("Square", callback_data="8d_square"),
         InlineKeyboardButton("Sawup", callback_data="8d_sawup")],
        [InlineKeyboardButton("Sawdown", callback_data="8d_sawdown")],
        [InlineKeyboardButton("← Back", callback_data="settings")]
    ])
    await callback_query.message.edit_text("Choose 8D Sound Type according to your choice:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("8d_sine|8d_triangle|8d_square|8d_sawup|8d_sawdown"))
async def eight_d_sound_type_handler(client, callback_query: CallbackQuery):
    # Store user choice for 8D sound type
    user_preferences[callback_query.from_user.id] = {"8d_sound_type": callback_query.data.split("_")[1]}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("2 sec", callback_data="8d_loop_2"),
         InlineKeyboardButton("5 sec", callback_data="8d_loop_5"),
         InlineKeyboardButton("8 sec", callback_data="8d_loop_8")],
        [InlineKeyboardButton("10 sec", callback_data="8d_loop_10"),
         InlineKeyboardButton("20 sec", callback_data="8d_loop_20"),
         InlineKeyboardButton("40 sec", callback_data="8d_loop_40")],
        [InlineKeyboardButton("50 sec", callback_data="8d_loop_50"),
         InlineKeyboardButton("80 sec", callback_data="8d_loop_80")],
        [InlineKeyboardButton("← Back", callback_data="8d_settings")]
    ])
    await callback_query.message.edit_text("Choose 8D Sound Loop Duration in seconds:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("8d_loop_"))
async def eight_d_loop_duration_handler(client, callback_query: CallbackQuery):
    loop_duration = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id
    
    # Store loop duration in user preferences
    user_preferences[user_id]["8d_loop_duration"] = loop_duration
    
    await callback_query.message.edit_text(
        f"8D Sound settings applied:\nSound Type: {user_preferences[user_id]['8d_sound_type']}\n"
        f"Loop Duration: {loop_duration} seconds"
    )





if __name__ == "__main__":
    app.run()
        
