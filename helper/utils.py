import os
import ffmepg
from pydub import AudioSegment
from helper.ffmepg import run_ffmpeg_command

# Apply Slow Reverb effect function
def apply_slowreverb(audio_path, output_path, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2, slowfactor=0.08):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav
    
    audio = AudioSegment.from_wav(audio_path)
    slowed_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * (1 - slowfactor))})
    slowed_audio = slowed_audio.set_frame_rate(audio.frame_rate)
    temp_file = "temp_reverb.wav"
    slowed_audio.export(temp_file, format="wav")
    
    reverb_command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', temp_file,
        '-af', f"aecho={wet_level}:{damping}:{room_size}:{dry_level}", output_path
    ]
    run_ffmpeg_command(reverb_command)
    
    os.remove(temp_file)
    if audio_path == "tmp.wav":
        os.remove(audio_path)

# Apply LOFI effect function
def apply_lofi_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav
    
    audio = AudioSegment.from_wav(audio_path)
    lofi_audio = audio.set_frame_rate(22050).low_pass_filter(1000)
    lofi_audio.export(output_path, format="wav")
    
    if audio_path == "tmp.wav":
        os.remove(audio_path)


def apply_8d_effect(audio_path, output_path):
    if not audio_path.lower().endswith('.wav'):
        tmp_wav = "tmp.wav"
        run_ffmpeg_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', audio_path, tmp_wav])
        audio_path = tmp_wav

    # Apply 8D effect using ffmpeg
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', audio_path,
        '-af', 'apulsator=hz=0.1',
        output_path
    ]
    run_ffmpeg_command(command)
    
    # Cleanup temporary file
    if audio_path == "tmp.wav":
        os.remove(audio_path)
