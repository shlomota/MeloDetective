import hashlib
import requests
import yt_dlp
import os

def fetch_metadata_and_download(query, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(query, download=True)
        entries = info_dict.get('entries', [info_dict])  # Handle both single video and playlist
        results = []

        for entry in entries:
            video_info = entry
            video_url = video_info['webpage_url']
            thumbnail_url = video_info['thumbnail']
            video_title = video_info['title']

            # Download the thumbnail image
            query_hash = hashlib.md5(video_url.encode()).hexdigest()
            thumbnail_filename = f"data/metadata/{query_hash}.jpg"
            if not os.path.exists("data/metadata"):
                os.makedirs("data/metadata")
            response = requests.get(thumbnail_url)
            with open(thumbnail_filename, 'wb') as f:
                f.write(response.content)

            result = {
                'title': video_title,
                'url': video_url,
                'thumbnail': thumbnail_filename
            }

            # Save metadata
            metadata_file = os.path.join(f"data/metadata/{query_hash}.txt")
            with open(metadata_file, 'w') as f:
                f.write(video_url)

            results.append(result)

        return results

def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'data/library/%(title)s.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch:{query}", download=False)
        return results['entries'][0] if 'entries' in results else None

