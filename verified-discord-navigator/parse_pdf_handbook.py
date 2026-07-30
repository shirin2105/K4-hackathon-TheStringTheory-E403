import os
import sys
import json
import re
from datetime import datetime
import pypdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

pdf_path = r"C:\Users\trand\Downloads\Others\20K-AI-Handbook_final.pdf"

if not os.path.exists(pdf_path):
    print("PDF file not found:", pdf_path)
    sys.exit(1)

print(f"Reading PDF handbook: {pdf_path} ({os.path.getsize(pdf_path)} bytes)...")

reader = pypdf.PdfReader(pdf_path)
print(f"Total pages in handbook: {len(reader.pages)}")

pdf_docs = []
pdf_counter = 2000

for page_num, page in enumerate(reader.pages, start=1):
    page_text = page.extract_text() or ""
    if not page_text.strip():
        continue

    # Split page text into paragraphs / sections
    paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) > 30]

    if not paragraphs:
        # Fallback to line chunks if double newlines are absent
        lines = page_text.split("\n")
        chunk = ""
        for line in lines:
            chunk += " " + line.strip()
            if len(chunk) > 200:
                paragraphs.append(chunk.strip())
                chunk = ""
        if chunk.strip():
            paragraphs.append(chunk.strip())

    for p_idx, text_chunk in enumerate(paragraphs, start=1):
        pdf_counter += 1
        doc_id = f"pdf_handbook_{page_num}_{p_idx}"

        text_lower = text_chunk.lower()

        # Intent classification
        if any(w in text_lower for w in ["deadline", "hạn", "nộp", "thời gian"]):
            intent = "deadline"
        elif any(w in text_lower for w in ["quy định", "nội quy", "yêu cầu", "đánh giá", "tiêu chí"]):
            intent = "regulation"
        elif any(w in text_lower for w in ["lịch", "workshop", "chương trình"]):
            intent = "schedule"
        else:
            intent = "document"

        # Topic classification
        if "gate 1" in text_lower:
            topic = "Gate 1"
        elif "gate 2" in text_lower:
            topic = "Gate 2"
        elif "gate 3" in text_lower:
            topic = "Gate 3"
        elif "checkpoint" in text_lower or "cp1" in text_lower or "cp2" in text_lower:
            topic = "Checkpoint"
        elif "workshop" in text_lower:
            topic = "Workshop"
        elif "hackathon" in text_lower:
            topic = "Hackathon"
        else:
            topic = f"Handbook Trang {page_num}"

        # Cohort classification
        if "k4" in text_lower or "khóa 4" in text_lower:
            cohort = "K4"
        elif "k3" in text_lower or "khóa 3" in text_lower:
            cohort = "K3"
        elif "k2" in text_lower or "khóa 2" in text_lower:
            cohort = "K2"
        else:
            cohort = "ALL"

        pdf_docs.append({
            "id": doc_id,
            "channel_name": "Sổ tay Cẩm nang 20K AI Handbook",
            "channel_id": "pdf_handbook",
            "message_url": "file:///C:/Users/trand/Downloads/Others/20K-AI-Handbook_final.pdf",
            "author_name": "Ban Tổ Chức AI20K",
            "author_role": "official",
            "content": f"[Handbook Trang {page_num}]: {text_chunk[:450]}",
            "topic": topic,
            "intent": intent,
            "cohort": cohort,
            "posted_at": datetime.now().isoformat(),
            "status": "active",
            "supersedes_source_id": None
        })

print(f"Extracted {len(pdf_docs)} knowledge sections from PDF handbook!")

# Load current database
data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mock_messages.json")
existing_docs = []
if os.path.exists(data_file):
    with open(data_file, "r", encoding="utf-8") as f:
        existing_docs = json.load(f)

# Deduplicate
existing_ids = {d["id"] for d in existing_docs}
new_added = 0
for d in pdf_docs:
    if d["id"] not in existing_ids:
        existing_docs.append(d)
        existing_ids.add(d["id"])
        new_added += 1

print(f"Added {new_added} PDF handbook sections into database. Total entries now: {len(existing_docs)}.")

with open(data_file, "w", encoding="utf-8") as f:
    json.dump(existing_docs, f, ensure_ascii=False, indent=2)

print("Database updated with PDF handbook content successfully!")
