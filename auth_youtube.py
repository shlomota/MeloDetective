#!/usr/bin/env python3
"""
Run this once on the server to authenticate with YouTube OAuth.
It will print a URL + code — open the URL, enter the code, sign in.
The token is cached and reused automatically by the app.

Usage: python auth_youtube.py
"""

from pytubefix import YouTube

TEST_URL = "https://www.youtube.com/watch?v=ym8TxNDUF8U"

print("Authenticating with YouTube OAuth...")
print("You will be prompted with a URL and a code. Open the URL and enter the code.\n")

yt = YouTube(TEST_URL, use_oauth=True, allow_oauth_cache=True)
print(f"\nAuth successful! Video title: {yt.title}")
print("Token cached. The app will use it automatically from now on.")
