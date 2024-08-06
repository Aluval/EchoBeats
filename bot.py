import os
import numpy as np
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest
import subprocess as sp

# Initialize the bot with your credentials
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAFKWhBga4p9sqXT9OcaYt41nQz14IVmQyA'

app = Client("slowreverb_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

metadata = {
    "comment": "Created by Slow + Reverb Bot",
    "created_by": "Slow + Reverb Bot",
    "title": "Audio with Slow Reverb"
}


def apply_slowreverb(audio_path, output_path, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2, slowfactor=0.08):
    # Convert to WAV if needed
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        sp.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
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
    reverb_command = (
        f'ffmpeg -hide_banner -loglevel error -y -i "{temp_file}" '
        f'-af "aecho=0.8:0.88:60:0.4" "{output_path}"'
    )
    sp.call(reverb_command, shell=True)

    # Add metadata to the final file
    if metadata:
        metadata_command = (
            f'ffmpeg -hide_banner -loglevel error -y -i "{output_path}" '
            f'-metadata comment="{metadata["comment"]}" '
            f'-metadata created_by="{metadata["created_by"]}" '
            f'-metadata title="{metadata["title"]}" '
            f'"{output_path}"'
        )
        sp.call(metadata_command, shell=True)

    # Cleanup temporary files
    os.remove(temp_file)
    if audio_path == "tmp.wav":
        os.remove(audio_path)

@app.on_message(filters.command("slowreverb") & filters.private)
async def slow_reverb_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /slowreverb command.")
        return

    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)

    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_slowreverb.wav"

    try:
        apply_slowreverb(input_file, output_file)

        try:
            await message.reply_audio(audio=output_file)
        except BadRequest as e:
            await message.reply_text(f"Failed to send audio: {e}")

    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

    os.remove(file_path)
    os.remove(output_file)

def apply_lofi_effect(audio_path, output_path, sample_rate=22050, bit_depth=16):
    # Convert to WAV if needed
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        sp.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path}" "{tmp_wav}"', shell=True)
        audio_path = tmp_wav

    # Load the audio file
    audio = AudioSegment.from_wav(audio_path)
    audio = audio.set_channels(2)  # Ensure the audio is stereo

    # Apply high-pass filter to remove low frequencies
    filtered_audio = audio.low_pass_filter(3000)  # Adjust cutoff frequency if needed

    # Export to temporary file
    temp_file = "temp_lofi.wav"
    filtered_audio.export(temp_file, format="wav")

    # Apply bitcrusher effect and downsample
    lofi_command = (
        f'ffmpeg -hide_banner -loglevel error -y -i "{temp_file}" '
        f'-ar {sample_rate} -sample_fmt s{bit_depth} "{output_path}"'
    )
    sp.call(lofi_command, shell=True)

    # Cleanup temporary files
    os.remove(temp_file)
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

    try:
        # Apply the lofi effect
        apply_lofi_effect(input_file, output_file)

        # Convert the output to FLAC with 24-bit depth and 48kHz sample rate
        final_output = f"{os.path.splitext(file_path)[0]}_lofi_24bit_48kHz.flac"
        sp.call(f'ffmpeg -hide_banner -loglevel error -y -i "{output_file}" -sample_fmt s32 -ar 48000 "{final_output}"', shell=True)
        
        # Add metadata to the final FLAC file
        metadata_command = (
            f'ffmpeg -hide_banner -loglevel error -y -i "{final_output}" '
            f'-metadata comment="{metadata["comment"]}" '
            f'-metadata created_by="{metadata["created_by"]}" '
            f'-metadata title="{metadata["title"]}" '
            f'"{final_output}"'
        )
        sp.call(metadata_command, shell=True)

        # Send the final output
        try:
            await message.reply_audio(audio=final_output)
        except BadRequest as e:
            await message.reply_text(f"Failed to send audio: {e}")

        # Cleanup intermediate files
        os.remove(file_path)
        os.remove(output_file)
        os.remove(final_output)
        
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@app.on_message(filters.command("setmetadata") & filters.private)
async def set_metadata_handler(client: Client, message: Message):
    global metadata
    # Extract metadata from the command
    parts = message.text.split('|')
    
    if len(parts) < 3:
        await message.reply_text("Usage: /setmetadata <comment> | <created_by> | <title>")
        return

    comment = parts[0].strip()
    created_by = parts[1].strip()
    title = parts[2].strip()

    metadata["comment"] = comment
    metadata["created_by"] = created_by
    metadata["title"] = title

    await message.reply_text(
        f"Metadata updated:\n"
        f"Comment: {comment}\n"
        f"Created by: {created_by}\n"
        f"Title: {title}"
    )

    
if __name__ == "__main__":
    app.run()
