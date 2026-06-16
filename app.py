import streamlit as st
from modules.transcript import get_transcript
from modules.summarizer import generate_summary
from modules.pdf_generator import generate_pdf

st.set_page_config(
    page_title="YouTube AI Article Generator",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
.main { background-color: #0E1117; }
.title { text-align:center; font-size:42px; font-weight:bold; color:#4CAF50; }
.subtitle { text-align:center; color:#BBBBBB; font-size:18px; margin-bottom:30px; }
.stButton>button {
    width:100%; background: linear-gradient(90deg,#4CAF50,#00C9A7);
    color:white; border:none; border-radius:10px;
    height:50px; font-size:18px; font-weight:bold;
}
.result-box { background:#1E1E1E; padding:20px; border-radius:15px; border:1px solid #333; }
.proxy-badge-on  { background:#1a3a1a; border:1px solid #4CAF50; color:#4CAF50;
                   padding:6px 14px; border-radius:8px; font-size:13px; display:inline-block; }
.proxy-badge-off { background:#3a1a1a; border:1px solid #e05252; color:#e05252;
                   padding:6px 14px; border-radius:8px; font-size:13px; display:inline-block; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🎥 YouTube AI Article Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Convert any YouTube Video into a Professional AI Generated Article & PDF</div>',
    unsafe_allow_html=True
)

# --- Proxy status indicator ---
proxy_user = st.secrets.get("PROXY_USER", "")
proxy_pass = st.secrets.get("PROXY_PASS", "")

if proxy_user and proxy_pass:
    st.markdown(
        '<div class="proxy-badge-on">🔒 Proxy: Active (WebShare)</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="proxy-badge-off">⚠️ Proxy: Not configured — transcript fetching may fail on cloud deployments. '
        'Add PROXY_USER & PROXY_PASS to Streamlit secrets.</div>',
        unsafe_allow_html=True
    )

st.markdown("---")

youtube_url = st.text_input(
    "🔗 Enter YouTube Video URL",
    placeholder="https://youtube.com/watch?v=..."
)

if st.button("🚀 Generate Article"):
    if youtube_url:
        with st.spinner("📥 Fetching Transcript..."):
            try:
                transcript = get_transcript(youtube_url)
            except ValueError as e:
                st.error(f"❌ {e}")
                if not (proxy_user and proxy_pass):
                    st.info(
                        "💡 **Fix:** Add a WebShare proxy to your Streamlit secrets.\n\n"
                        "1. Sign up free at https://webshare.io\n"
                        "2. Go to **Streamlit Cloud → App Settings → Secrets**\n"
                        "3. Add:\n```\nPROXY_USER = \"your_username\"\nPROXY_PASS = \"your_password\"\n```"
                    )
                st.stop()

        st.success("✅ Transcript Retrieved Successfully")

        with st.spinner("🤖 Generating AI Article... (may retry if server is busy)"):
            try:
                article = generate_summary(transcript)
            except Exception as e:
                st.error("❌ Failed to generate article after multiple attempts. Please try again in a moment.")
                st.stop()

        st.success("✅ Article Generated Successfully")

        pdf_file = generate_pdf(article)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", len(article.split()))
        with col2:
            st.metric("Characters", len(article))
        with col3:
            st.metric("Pages", max(1, len(article) // 3000))

        st.markdown("## 📝 Generated Article")
        st.markdown(f'<div class="result-box">{article}</div>', unsafe_allow_html=True)

        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📄 Download PDF",
                data=f,
                file_name="AI_Article.pdf",
                mime="application/pdf"
            )

        st.balloons()
    else:
        st.warning("⚠️ Please Enter a YouTube URL")