import streamlit as st
from googleapiclient.discovery import build
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import re
import xml.etree.ElementTree as ET
import requests

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


def get_transcript_via_api(video_id: str, yt_api_key: str) -> str:
    """Get caption track URL via YouTube Data API, then fetch content directly."""
    youtube = build("youtube", "v3", developerKey=yt_api_key)

    # List caption tracks
    response = youtube.captions().list(
        part="snippet",
        videoId=video_id
    ).execute()

    tracks = response.get("items", [])
    if not tracks:
        raise ValueError("No captions found for this video.")

    # Get video page to extract timedtext URL
    # Use YouTube's timedtext endpoint (public, no auth needed)
    lang = None
    for track in tracks:
        if track["snippet"]["language"].startswith("en"):
            lang = track["snippet"]["language"]
            break
    if not lang:
        lang = tracks[0]["snippet"]["language"]

    # Fetch captions via timedtext endpoint
    timedtext_url = f"https://www.youtube.com/api/timedtext?lang={lang}&v={video_id}&fmt=json3"
    r = requests.get(timedtext_url, headers={"User-Agent": "Mozilla/5.0"})

    if r.status_code != 200 or not r.text.strip():
        # Try without fmt parameter
        timedtext_url = f"https://www.youtube.com/api/timedtext?lang={lang}&v={video_id}"
        r = requests.get(timedtext_url, headers={"User-Agent": "Mozilla/5.0"})

    if not r.text.strip():
        raise ValueError("Could not fetch captions. This video may not have English subtitles.")

    # Parse XML response
    try:
        root = ET.fromstring(r.text)
        texts = [elem.text for elem in root.iter('text') if elem.text]
        transcript = " ".join(texts)
        transcript = re.sub(r'\s+', ' ', transcript).strip()
        return transcript
    except ET.ParseError:
        # Try as plain text
        text = re.sub(r'<[^>]+>', '', r.text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            return text
        raise ValueError("Could not parse captions for this video.")


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
            yt_key     = st.secrets["YOUTUBE_API_KEY"]
            gemini_key = st.secrets["GEMINI_API_KEY"]
        except KeyError as e:
            st.error(f"❌ Missing secret: {e}")
            st.stop()

        with st.spinner("📥 Fetching captions..."):
            try:
                video_id   = extract_video_id(youtube_url)
                transcript = get_transcript_via_api(video_id, yt_key)
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