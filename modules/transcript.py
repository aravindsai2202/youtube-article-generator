import re
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig


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
    If proxy credentials are available in Streamlit secrets, uses WebShare proxy.
    Falls back to direct connection if no proxy configured.
    """
    if use_proxy:
        try:
            proxy_user = st.secrets.get("PROXY_USER", "")
            proxy_pass = st.secrets.get("PROXY_PASS", "")

            if proxy_user and proxy_pass:
                proxy_config = WebshareProxyConfig(
                    proxy_username=proxy_user,
                    proxy_password=proxy_pass,
                )
                return YouTubeTranscriptApi(proxies=proxy_config)
        except Exception:
            pass  # Secrets not configured or proxy init failed

    return YouTubeTranscriptApi()


def get_transcript(url: str) -> str:
    """
    Fetch transcript for a YouTube video URL.
    Tries with proxy first (if configured), falls back to direct if proxy fails.
    Returns transcript as a single string.
    """
    video_id = extract_video_id(url)

    # Try with proxy first
    for use_proxy in [True, False]:
        try:
            api = get_youtube_api(use_proxy=use_proxy)
            transcript_list = api.fetch(video_id)
            text = " ".join([entry.text for entry in transcript_list])
            return text
        except Exception as e:
            error_msg = str(e)

            # If proxy attempt failed, try without proxy
            if use_proxy:
                continue

            # Final failure — raise a clean error
            if "Could not retrieve a transcript" in error_msg:
                raise ValueError(
                    "Could not fetch transcript. This video may have no captions, "
                    "or YouTube is blocking requests from this server. "
                    "Try adding a WebShare proxy in Streamlit secrets (PROXY_USER / PROXY_PASS)."
                )
            else:
                raise ValueError(f"Could not fetch transcript: {error_msg}")