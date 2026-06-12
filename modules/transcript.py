from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import re


def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def get_transcript(url):
    video_id = extract_video_id(url)

    if not video_id:
        raise ValueError("Invalid YouTube URL. Please check and try again.")

    ytt_api = YouTubeTranscriptApi()

    try:
        transcript_list = ytt_api.list(video_id)
        transcript = transcript_list.find_generated_transcript(
            [t.language_code for t in transcript_list]
        ).fetch()

    except TranscriptsDisabled:
        raise ValueError("This video has transcripts disabled. Please try another video.")

    except NoTranscriptFound:
        raise ValueError("No transcript found for this video. Please try a video with captions enabled.")

    except Exception as e:
        raise ValueError(f"Could not fetch transcript: {str(e)}")

    text = " ".join([snippet.text for snippet in transcript])
    return text