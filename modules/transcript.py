import re
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig


def extract_video_id(url: str) -> str:
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


def get_transcript(url: str) -> str:
    video_id = extract_video_id(url)

    proxy_user = st.secrets.get("PROXY_USER", "")
    proxy_pass = st.secrets.get("PROXY_PASS", "")
    proxy_host = st.secrets.get("PROXY_HOST", "38.154.203.95")
    proxy_port = st.secrets.get("PROXY_PORT", "5863")

    try:
        if proxy_user and proxy_pass:
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}/"
            proxy_config = GenericProxyConfig(
                http_url=proxy_url,
                https_url=proxy_url,
            )
            api = YouTubeTranscriptApi(proxy_config=proxy_config)
        else:
            api = YouTubeTranscriptApi()

        transcript_list = api.fetch(video_id)
        text = " ".join([entry.text for entry in transcript_list])
        return text
    except Exception as e:
        error_msg = str(e)
        if "Could not retrieve a transcript" in error_msg:
            raise ValueError(
                "Could not fetch transcript. This video may have no captions, "
                "or YouTube is blocking requests from this server."
            )
        raise ValueError(f"Could not fetch transcript: {error_msg}")