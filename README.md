# 🎥 YouTube AI Article Generator

Convert any YouTube video into a **professional AI-generated article** and downloadable **PDF** — powered by Google Gemini AI.

---

## 🚀 Features

- 🔗 Paste any YouTube URL and get a full article instantly
- 🤖 AI-powered article generation using Gemini 2.5 Flash
- 📄 Download the article as a professional PDF
- 📊 Word count, character count and page metrics
- 🔁 Auto-retry if Gemini server is busy
- 🎨 Clean and modern UI built with Streamlit

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Streamlit | Web UI |
| Google Gemini AI | Article generation |
| YouTube Transcript API | Fetching video transcript |
| ReportLab | PDF generation |
| python-dotenv | Managing API keys |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
git clone https://github.com/aravindsai2202/youtube-article-generator.git

cd youtube-article-generator

### 2. Install dependencies
pip install -r requirements.txt

### 3. Create a `.env` file
GEMINI_API_KEY=your_gemini_api_key_here

> Get your free Gemini API key at: https://aistudio.google.com/app/apikey

### 4. Run the app
streamlit run app.py

---

## 📸 How It Works

1. Paste a YouTube video URL
2. Click **Generate Article**
3. AI fetches the transcript and generates a full article
4. Download the article as a PDF

---

## 📁 Project Structure
youtube-article-generator/

├── app.py                  # Main Streamlit app

├── requirements.txt        # Dependencies

├── .env                    # API keys (not uploaded to GitHub)

├── .gitignore              # Files to ignore

├── README.md               # Project documentation

└── modules/

├── transcript.py       # Fetch YouTube transcript

├── summarizer.py       # Generate article using Gemini

└── pdf_generator.py    # Generate PDF from article

---
---

## 👨‍💻 Author

**Venkata AravindSai Thanneru**  
GitHub: [@aravindsai2202](https://github.com/aravindsai2202)

---


