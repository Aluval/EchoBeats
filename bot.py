import os
import numpy as np
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest

# Initialize the bot with your credentials
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAFKWhBga4p9sqXT9OcaYt41nQz14IVmQyA'

app = Client("8d_music_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def apply_8d_effect(audio_path, output_path, pan_speed=0.1, rotation_duration=10):
    audio = AudioSegment.from_file(audio_path)
    mono_audio = audio.set_channels(1)
    frame_count = int(mono_audio.frame_rate * rotation_duration)
    result = AudioSegment.empty()

    for i in range(0, len(mono_audio), frame_count):
        chunk = mono_audio[i:i + frame_count]
        panning = np.sin(np.linspace(0, 2 * np.pi, frame_count)) * pan_speed
        for j in range(frame_count):
            chunk = chunk.set_frame(j, chunk.get_frame(j).pan(panning[j]))
        result += chunk

    result.export(output_path, format="flac")

@app.on_message(filters.command("8dconvert") & filters.private)
async def convert_to_8d(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Please reply to an audio file with the /8dconvert command.")
        return

    audio = message.reply_to_message.audio
    file_path = await client.download_media(audio)

    input_file = file_path
    output_file = f"{os.path.splitext(file_path)[0]}_8d.flac"

    apply_8d_effect(input_file, output_file)

    try:
        await message.reply_audio(audio=output_file)
    except BadRequest as e:
        await message.reply_text(f"Failed to send audio: {e}")

    os.remove(file_path)
    os.remove(output_file)

if __name__ == "__main__":
    app.run()
