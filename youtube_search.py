import hashlib
import requests
import yt_dlp
import os
from audio_processing import sanitize_filename
from consts import *
import logging

def replace_quotes(filename):
    # Replace standard quotes with special quotes
    return filename.replace('"', '＂').replace("'", '＇')

def fetch_metadata_and_download(query, output_dir):
    # Path to your cookies file
    cookies_path = 'ytcookies.txt'
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        # Add cookies and user-agent
        'cookiefile': cookies_path,
        'http_headers': {
            'User-Agent': user_agent
        }
    }


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(query, download=True)
        entries = info_dict.get('entries', [info_dict])  # Handle both single video and playlist
        results = []

        for entry in entries:
            video_info = entry
            video_url = video_info['webpage_url']
            thumbnail_url = video_info['thumbnail']
            video_title_orig = video_info['title']
            video_title = sanitize_filename(video_title_orig)

            original_filename = os.path.join(output_dir, f"{video_title_orig}.mp3")
            sanitized_filename = os.path.join(output_dir, f"{video_title}.mp3")

            logging.info("Original: %s" % (original_filename))
            logging.info("Sanitized: %s" % (sanitized_filename))
            replaced_filename = replace_quotes(original_filename)
            if os.path.exists(original_filename):
                logging.info("Renaming file %s to %s" % (original_filename, sanitized_filename))
                os.rename(original_filename, sanitized_filename)
            elif os.path.exists(replaced_filename):
                logging.info("Renaming replaced file %s to %s" % (replaced_filename, sanitized_filename))
                os.rename(replaced_filename, sanitized_filename)
            result = {
                'title': video_title,
                'url': video_url,
                'thumbnail': thumbnail_url
            }
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
        'outtmpl': '/home/ubuntu/MeloDetective/data/library/%(title)s.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch:{query}", download=False)
        return results['entries'][0] if 'entries' in results else None

