import streamlit as st
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import re
import requests
import json

st.set_page_config(page_title="YouTube AI Article Generator", page_icon="🎥", layout="centered")

st.markdown("""
<style>
.title { text-align:center; font-size:40px; font-weight:bold; color:#4CAF50; }
.subtitle { text-align:center; color:#BBBBBB; font-size:17px; margin-bottom:20px; }
.stButton>button {
    width:100%; background:linear-gradient(90deg,#4CAF50,#00C9A7);
    color:white; border:none; border-radius:10px;
    height:48px; font-size:17px; font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🎥 YouTube AI Article Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Convert any YouTube video into a professional AI-generated article & PDF</div>', unsafe_allow_html=True)
st.markdown("---")


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError("Invalid YouTube URL.")


def get_transcript(video_id: str) -> str:
    """Fetch transcript using YouTube innertube API."""
    
    # Step 1: Get the video page to extract caption URL
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    # Use innertube API
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101",
                "hl": "en",
                "gl": "US",
            }
        },
        "videoId": video_id,
    }

    r = session.post(
        "https://www.youtube.com/youtubei/v1/get_transcript",
        json=payload,
        params={"key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"}
    )

    if r.status_code == 200:
        data = r.json()
        # Extract text from transcript response
        try:
            transcript_parts = []
            actions = data.get("actions", [])
            for action in actions:
                segments = action.get("updateEngagementPanelAction", {}) \
                               .get("content", {}) \
                               .get("transcriptRenderer", {}) \
                               .get("body", {}) \
                               .get("transcriptBodyRenderer", {}) \
                               .get("cueGroups", [])
                for group in segments:
                    cues = group.get("transcriptCueGroupRenderer", {}).get("cues", [])
                    for cue in cues:
                        text = cue.get("transcriptCueRenderer", {}) \
                                  .get("cue", {}) \
                                  .get("simpleText", "")
                        if text:
                            transcript_parts.append(text)
            
            if transcript_parts:
                return " ".join(transcript_parts)
        except Exception:
            pass

    # Step 2: Fallback — scrape caption URL from video page
    page = session.get(f"https://www.youtube.com/watch?v={video_id}")
    html = page.text

    # Find caption tracks in page source
    match = re.search(r'"captionTracks":\[(.*?)\]', html)
    if not match:
        raise ValueError(
            "No captions found for this video.\n\n"
            "💡 Try a video that has subtitles/captions enabled."
        )

    captions_json = "[" + match.group(1) + "]"
    tracks = json.loads(captions_json)

    # Pick English track
    base_url = None
    for track in tracks:
        lang = track.get("languageCode", "")
        if lang.startswith("en"):
            base_url = track.get("baseUrl")
            break
    if not base_url:
        base_url = tracks[0].get("baseUrl")

    if not base_url:
        raise ValueError("Could not find caption URL.")

    # Fetch and parse captions
    cap_response = session.get(base_url + "&fmt=json3")
    cap_data = cap_response.json()
    
    texts = []
    for event in cap_data.get("events", []):
        for seg in event.get("segs", []):
            t = seg.get("utf8", "").strip()
            if t and t != "\n":
                texts.append(t)

    transcript = " ".join(texts)
    transcript = re.sub(r'\s+', ' ', transcript).strip()

    if not transcript:
        raise ValueError("Captions were empty for this video.")

    return transcript


def generate_article(transcript: str, gemini_key: str) -> str:
    client = genai.Client(api_key=gemini_key)
    prompt = f"""You are a professional content writer. Based on the transcript below, write a well-structured, 
engaging article with a title, introduction, multiple sections with headings, and a conclusion.
Make it informative, professional, and easy to read.

Transcript:
{transcript[:12000]}

Write the full article now:"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text


def create_pdf(article: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=A4,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, spaceAfter=16)
    body_style  = ParagraphStyle('Body',  parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=8)
    head_style  = ParagraphStyle('Head',  parent=styles['Heading2'], fontSize=13, spaceBefore=12, spaceAfter=6)

    story = []
    for line in article.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## ') or line.startswith('### '):
            story.append(Paragraph(re.sub(r'^#{2,3} ', '', line), head_style))
        else:
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(line, body_style))

    doc.build(story)
    return tmp.name


# ── UI ────────────────────────────────────────────────────────────────────────
youtube_url = st.text_input("🔗 Enter YouTube Video URL", placeholder="https://youtube.com/watch?v=...")

if st.button("🚀 Generate Article"):
    if not youtube_url:
        st.warning("⚠️ Please enter a YouTube URL.")
    else:
        try:
            gemini_key = st.secrets["GEMINI_API_KEY"]
        except KeyError as e:
            st.error(f"❌ Missing secret: {e}")
            st.stop()

        with st.spinner("📥 Fetching captions..."):
            try:
                video_id   = extract_video_id(youtube_url)
                transcript = get_transcript(video_id)
                st.success("✅ Captions fetched!")
            except Exception as e:
                st.error(f"❌ {e}")
                st.stop()

        with st.spinner("🤖 Generating article with Gemini..."):
            try:
                article = generate_article(transcript, gemini_key)
                st.success("✅ Article generated!")
            except Exception as e:
                st.error(f"❌ {e}")
                st.stop()

        col1, col2, col3 = st.columns(3)
        col1.metric("Words", len(article.split()))
        col2.metric("Characters", len(article))
        col3.metric("Pages (est.)", max(1, len(article) // 3000))

        st.markdown("## 📝 Generated Article")
        st.markdown(article)

        pdf_path = create_pdf(article)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF", f, file_name="AI_Article.pdf", mime="application/pdf")

        st.balloons()