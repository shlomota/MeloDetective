import os
import logging
import subprocess

try:
    from pytubefix import YouTube, Playlist, Search
except ImportError:
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytubefix", "-q"])
    from pytubefix import YouTube, Playlist, Search

from audio_processing import sanitize_filename


def _download_as_mp3(yt: YouTube, output_dir: str) -> dict | None:
    """Download a single YouTube video's audio as MP3, return metadata dict."""
    try:
        stream = yt.streams.get_audio_only()
        if not stream:
            logging.error(f"No audio stream found for {yt.title}")
            return None

        sanitized_title = sanitize_filename(yt.title)
        mp3_path = os.path.join(output_dir, f"{sanitized_title}.mp3")

        if not os.path.exists(mp3_path):
            tmp_file = stream.download(output_path=output_dir, filename="__tmp_audio.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_file, "-q:a", "0", "-map", "a", mp3_path],
                check=True, capture_output=True
            )
            os.remove(tmp_file)
            logging.info(f"Downloaded: {sanitized_title}")
        else:
            logging.info(f"Already exists, skipping: {sanitized_title}")

        return {
            "title": yt.title,
            "url": yt.watch_url,
            "thumbnail": yt.thumbnail_url,
        }
    except Exception as e:
        logging.error(f"Error downloading {yt.watch_url}: {e}")
        return None


def fetch_metadata_and_download(query, output_dir):
    """
    Download audio from a YouTube URL or playlist as MP3.
    Returns a list of dicts with 'title', 'url', and 'thumbnail' keys.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    try:
        if "list=" in query:
            pl = Playlist(query)
            for video in pl.videos:
                info = _download_as_mp3(video, output_dir)
                if info:
                    results.append(info)
        else:
            yt = YouTube(query)
            info = _download_as_mp3(yt, output_dir)
            if info:
                results.append(info)
    except Exception as e:
        logging.error(f"Error in fetch_metadata_and_download: {e}")
    return results


def search_youtube(query):
    """
    Search YouTube for a query and return the top result's info,
    or None if nothing found.
    """
    try:
        results = Search(query)
        if results.videos:
            top = results.videos[0]
            return {
                "webpage_url": top.watch_url,
                "thumbnail": top.thumbnail_url,
            }
    except Exception as e:
        logging.error(f"YouTube search error: {e}")
    return None
