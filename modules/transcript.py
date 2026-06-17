import re
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_youtube_api(use_proxy: bool = True) -> YouTubeTranscriptApi:
    """
    Returns a YouTubeTranscriptApi instance.
    Uses direct proxy URL with specific IP and port from Streamlit secrets.
    Falls back to direct connection if no proxy configured.
    """
    if use_proxy:
        try:
            proxy_user = st.secrets.get("PROXY_USER", "")
            proxy_pass = st.secrets.get("PROXY_PASS", "")
            proxy_host = st.secrets.get("PROXY_HOST", "38.154.203.95")
            proxy_port = st.secrets.get("PROXY_PORT", "5863")

            if proxy_user and proxy_pass:
                proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}/"
                return YouTubeTranscriptApi(proxies={"http": proxy_url, "https": proxy_url})
        except Exception:
            pass

    return YouTubeTranscriptApi()


def get_transcript(url: str) -> str:
    """
    Fetch transcript for a YouTube video URL.
    Tries with proxy first, falls back to direct if proxy fails.
    Returns transcript as a single string.
    """
    video_id = extract_video_id(url)

    for use_proxy in [True, False]:
        try:
            api = get_youtube_api(use_proxy=use_proxy)
            transcript_list = api.fetch(video_id)
            text = " ".join([entry.text for entry in transcript_list])
            return text
        except Exception as e:
            error_msg = str(e)

            if use_proxy:
                continue

            if "Could not retrieve a transcript" in error_msg:
                raise ValueError(
                    "Could not fetch transcript. This video may have no captions, "
                    "or YouTube is blocking requests from this server."
                )
            else:
                raise ValueError(f"Could not fetch transcript: {error_msg}")