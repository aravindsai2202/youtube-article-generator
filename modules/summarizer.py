from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def generate_summary(transcript, retries=4, backoff=5):
    prompt = f"""
Convert the following YouTube transcript into a professional article.

Requirements:
- Attractive Title
- Introduction
- Main Content with Headings
- Key Takeaways
- Conclusion

Transcript:
{transcript[:15000]}
"""

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text

        except genai_errors.ServerError as e:
            if attempt == retries:
                raise
            wait = backoff * attempt
            print(f"[Attempt {attempt}/{retries}] Gemini server busy (503). Retrying in {wait}s...")
            time.sleep(wait)