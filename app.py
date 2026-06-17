import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import re
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


def get_transcript(video_id: str, supadata_key: str) -> str:
    url = "https://api.supadata.ai/v1/youtube/transcript"
    headers = {"x-api-key": supadata_key}
    params = {"videoId": video_id, "text": "true"}

    r = requests.get(url, headers=headers, params=params)

    if r.status_code == 200:
        data = r.json()
        transcript = data.get("content", "")
        if isinstance(transcript, list):
            transcript = " ".join([t.get("text", "") for t in transcript])
        if transcript:
            return transcript.strip()
        raise ValueError("Transcript is empty for this video.")
    elif r.status_code == 404:
        raise ValueError("No transcript found. Try a video with captions enabled.")
    else:
        raise ValueError(f"Supadata API error: {r.status_code}")


def generate_article(transcript: str, groq_key: str) -> str:
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a professional content writer who writes well-structured, engaging articles."
            },
            {
                "role": "user",
                "content": f"""Based on the transcript below, write a well-structured engaging article with:
- A compelling title
- Introduction
- Multiple sections with headings
- A conclusion

Make it informative, professional, and easy to read.

Transcript:
{transcript[:4000]}

Write the full article now:"""
            }
        ],
        max_tokens=2000,
        temperature=0.7
    )
    return response.choices[0].message.content


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


# ── UI ───────────────────────────────────────────────────────────────────────
youtube_url = st.text_input("🔗 Enter YouTube Video URL", placeholder="https://youtube.com/watch?v=...")

if st.button("🚀 Generate Article"):
    if not youtube_url:
        st.warning("⚠️ Please enter a YouTube URL.")
    else:
        try:
            groq_key     = st.secrets["GROQ_API_KEY"]
            supadata_key = st.secrets["SUPADATA_API_KEY"]
        except KeyError as e:
            st.error(f"❌ Missing secret: {e}")
            st.stop()

        with st.spinner("📥 Fetching transcript..."):
            try:
                video_id   = extract_video_id(youtube_url)
                transcript = get_transcript(video_id, supadata_key)
                st.success("✅ Transcript fetched!")
            except Exception as e:
                st.error(f"❌ {e}")
                st.stop()

        with st.spinner("🤖 Generating article with Groq AI..."):
            try:
                article = generate_article(transcript, groq_key)
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