import os
import subprocess 


# Helper function to run ffmpeg commands
def run_ffmpeg_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr.decode('utf-8')}")
    return result

# Change Audio Metadata function
def change_audio_metadata(input_path, output_path, comment, created_by, audio_title):
    temp_output = f"{os.path.splitext(output_path)[0]}_temp.flac"
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-metadata', f'comment={comment}',
        '-metadata', f'created_by={created_by}',
        '-metadata', f'title={audio_title}',
        '-c', 'copy',
        temp_output,
        '-y'
    ]
    
    run_ffmpeg_command(command)
    os.rename(temp_output, output_path)
