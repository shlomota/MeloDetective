"""
Simplified version of youtube_search.py without yt_dlp dependency.
This version provides stub functions that return empty results.
"""

import logging

def fetch_metadata_and_download(query, output_dir):
    """
    Stub function that returns an empty list.
    In the original implementation, this would fetch metadata and download audio from YouTube.
    """
    logging.warning("YouTube functionality is disabled. yt_dlp is not installed.")
    return []

def search_youtube(query):
    """
    Stub function that returns None.
    In the original implementation, this would search YouTube for a query.
    """
    logging.warning("YouTube search functionality is disabled. yt_dlp is not installed.")
    return None