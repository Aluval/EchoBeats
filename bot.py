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

    apply_slowreverb(input_file, output_file)

    try:
        await message.reply_audio(audio=output_file)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")

    os.remove(file_path)
    os.remove(output_file)

if __name__ == "__main__":
    app.run()
