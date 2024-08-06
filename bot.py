
import os
import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest

# Initialize the bot with your credentials
api_id = '10811400'
api_hash = '191bf5ae7a6c39771e7b13cf4ffd1279'
bot_token = '7412278588:AAFKWhBga4p9sqXT9OcaYt41nQz14IVmQyA'


app = Client("8d_music_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def apply_8d_effect(audio_path, output_path, pan_speed=0.1, rotation_duration=10):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(2)  # Ensure the audio is stereo
    
    # Parameters
    frame_rate = audio.frame_rate
    duration_ms = len(audio)
    sample_rate = frame_rate / 1000.0
    frames = np.array(audio.get_array_of_samples())

    # Prepare for panning
    num_samples = len(frames)
    num_frames = int(sample_rate * rotation_duration)
    
    left_channel = np.zeros(num_samples)
    right_channel = np.zeros(num_samples)

    # Apply panning effect
    for i in range(num_samples):
        pan = np.sin(2 * np.pi * i / num_frames)  # Generate a panning wave
        left_channel[i] = frames[i] * (1 - pan)
        right_channel[i] = frames[i] * pan

    # Create new audio segments for left and right channels
    left_audio = AudioSegment(
        data=left_channel.astype(np.int16).tobytes(),
        sample_width=audio.sample_width,
        frame_rate=frame_rate,
        channels=1
    )

    right_audio = AudioSegment(
        data=right_channel.astype(np.int16).tobytes(),
        sample_width=audio.sample_width,
        frame_rate=frame_rate,
        channels=1
    )

    stereo_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)
    stereo_audio.export(output_path, format="flac")

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
