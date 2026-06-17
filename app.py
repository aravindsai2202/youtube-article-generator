import streamlit as st
from googleapiclient.discovery import build
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import re

# ── Page config ──────────────────────────────────────────────────────────────
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

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    raise ValueError("Invalid YouTube URL — could not extract video ID.")


def get_captions(video_id: str, yt_api_key: str) -> str:
    """Fetch auto-generated or manual captions via YouTube Data API v3."""
    youtube = build("youtube", "v3", developerKey=yt_api_key)

    # Get caption tracks
    captions_response = youtube.captions().list(
        part="snippet",
        videoId=video_id
    ).execute()

    tracks = captions_response.get("items", [])
    if not tracks:
        raise ValueError("No captions found for this video. Try a video with subtitles enabled.")

    # Prefer English
    track_id = None
    for track in tracks:
        lang = track["snippet"]["language"]
        if lang.startswith("en"):
            track_id = track["id"]
            break
    if not track_id:
        track_id = tracks[0]["id"]

    # Download caption content
    caption_content = youtube.captions().download(
        id=track_id,
        tfmt="srt"
    ).execute()

    # Clean SRT formatting
    text = caption_content.decode("utf-8") if isinstance(caption_content, bytes) else caption_content
    text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n+', ' ', text).strip()
    return text


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
    lines = article.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], head_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], head_style))
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
            st.error(f"❌ Missing secret: {e}. Add it in Streamlit Cloud → Settings → Secrets.")
            st.stop()

        with st.spinner("📥 Fetching captions via YouTube API..."):
            try:
                video_id   = extract_video_id(youtube_url)
                transcript = get_captions(video_id, yt_key)
                st.success("✅ Captions fetched successfully!")
            except Exception as e:
                st.error(f"❌ {e}")
                st.stop()

        with st.spinner("🤖 Generating AI article with Gemini..."):
            try:
                article = generate_article(transcript, gemini_key)
                st.success("✅ Article generated!")
            except Exception as e:
                st.error(f"❌ Gemini error: {e}")
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