import os, re
from pydub import AudioSegment
from helper.ffmpeg import run_ffmpeg_command
from yt_dlp import YoutubeDL
from config import *
import base64
import requests
import subprocess 

credentials = base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode('utf-8')).decode('utf-8')

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

async def download_songs(music, download_directory="."):
  query = f"{music}".replace("+", "")
  ydl_opts = {
      "format": "bestaudio/best",
      "default_search": "ytsearch",
      "noplaylist": True,
      "nocheckcertificate": True,
      "outtmpl": f"{music}.mp3",
      "quiet": True,
      "addmetadata": True,
      "prefer_ffmpeg": True,
      "geo_bypass": True,
      "nocheckcertificate": True,
  }

  with YoutubeDL(ydl_opts) as ydl:
      try:
          video = ydl.extract_info(f"ytsearch:{music}", download=False)["entries"][0]["id"]
          info = ydl.extract_info(video)
          filename = ydl.prepare_filename(info)
          if not filename:
              print(f"Track Not Found⚠️")
          else:
              path_link = filename
              return path_link, info 
      except Exception as e:
          raise Exception(f"Error downloading song: {e}") 
          

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

# Function to extract media information using mediainfo command
def get_mediainfo(file_path):
    process = subprocess.Popen(
        ["mediainfo", file_path, "--Output=HTML"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"Error getting media info: {stderr.decode().strip()}")
    return stdout.decode().strip()
