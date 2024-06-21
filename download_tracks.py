import os
#from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL



# YouTube playlist URL
playlist_url = "https://www.youtube.com/watch?v=9bsgVmaS2gY&list=PLnuftEmfAbZz80nWrmK-ORwGVQGYKNFtF"

# Directory to store the downloaded MP3 files
output_directory = "downloaded_tracks"

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Configure youtube-dl options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
}

# Create a youtube-dl object
with YoutubeDL(ydl_opts) as ydl:
    # Download the playlist
    ydl.download([playlist_url])

print("Playlist downloaded successfully!")