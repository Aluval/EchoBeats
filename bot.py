import os
import subprocess as sp
from pyrogram import Client, filters
from pyrogram.types import Message
from pydub import AudioSegment

# Initialize the metadata dictionary
metadata = {
    "comment": "Default comment",
    "created_by": "Default creator",
    "title": "Default title"
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
        f'-af "aecho={wet_level}:{damping}:{room_size}:{dry_level}" "{output_path}"'
    )
    sp.call(reverb_command, shell=True)

    # Cleanup temporary files
    os.remove(temp_file)
    if audio_path == "tmp.wav":
        os.remove(audio_path)

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

    # Update the metadata dictionary
    metadata["comment"] = comment
    metadata["created_by"] = created_by
    metadata["title"] = title

    await message.reply_text(
        f"Metadata updated:\n"
        f"Comment: {comment}\n"
        f"Created by: {created_by}\n"
        f"Title: {title}"
    )

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

    # Cleanup intermediate files
    os.remove(file_path)
    os.remove(output_file)
    
    try:
        await message.reply_audio(audio=final_output)
    except Exception as e:
        await message.reply_text(f"Failed to send audio: {e}")
    
    os.remove(final_output)



    
if __name__ == "__main__":
    app.run()
