from modules.transcript import get_transcript
from modules.summarizer import generate_summary  # FIX: was generate_article (doesn't exist); correct name is generate_summary
from modules.pdf_generator import generate_pdf   # FIX: was create_pdf (doesn't exist); correct name is generate_pdf
# FIX: removed duplicate `from modules.transcript import get_transcript`


url = input("Enter YouTube URL: ")

print("Getting transcript...")
transcript = get_transcript(url)

print("Generating AI Article...")
article = generate_summary(transcript)  # FIX: was generate_article

print(article)

pdf_file = generate_pdf(article)  # FIX: was create_pdf

print(f"\nPDF Saved Successfully: {pdf_file}")
print("Import OK")
