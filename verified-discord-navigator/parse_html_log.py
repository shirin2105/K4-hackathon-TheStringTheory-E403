import os
import sys
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

file_path = r"C:\Users\trand\Downloads\Learning - AI\Vin\Lab\Day5\K4-hackathon-TheStringTheory-E403\AI20K Build Phase — Cohort 3 & 4 - Bot & Tiện ích - 🤖-gõ-commands [1527920243350179960].html"

if not os.path.exists(file_path):
    print("File not found:", file_path)
    sys.exit(1)

def parse_iso(val: str) -> str:
    date_formats = [
        "%A, %B %d, %Y %I:%M %p",
        "%B %d, %Y %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(val.strip(), fmt).isoformat()
        except ValueError:
            continue
    return datetime.now().isoformat()

print(f"Loading {file_path} ({os.path.getsize(file_path)} bytes)...")

with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

msg_groups = soup.find_all("div", class_="chatlog__message-group")
print(f"Found {len(msg_groups)} message groups.")

extracted_docs = []
doc_counter = 100

for group in msg_groups:
    author_elem = group.find("span", class_="chatlog__author-name")
    author_name = author_elem.get_text().strip() if author_elem else "Học viên / BTC"

    time_elem = group.find("span", class_="chatlog__timestamp")
    posted_at = datetime.now().isoformat()
    if time_elem:
        raw_time = time_elem.get_text().strip()
        if time_elem.has_attr("title"):
            posted_at = parse_iso(time_elem["title"])
        else:
            posted_at = parse_iso(raw_time)

    messages = group.find_all("div", class_="chatlog__message")
    for msg in messages:
        content_elem = msg.find("div", class_="chatlog__content")
        text_content = ""
        if content_elem:
            text_content = content_elem.get_text().strip()

        embeds = msg.find_all("div", class_="chatlog__embed")
        embed_text_list = []
        for emb in embeds:
            title = emb.find("div", class_="chatlog__embed-title")
            desc = emb.find("div", class_="chatlog__embed-description")
            if title:
                embed_text_list.append(title.get_text().strip())
            if desc:
                embed_text_list.append(desc.get_text().strip())

        if embed_text_list:
            text_content = (text_content + " " + " ".join(embed_text_list)).strip()

        if not text_content or len(text_content) < 15:
            continue

        keywords = [
            "deadline", "hạn", "nộp", "link", "github", "drive", "form", "slide",
            "bot", "command", "hướng dẫn", "quy định", "bài tập", "checkpoint",
            "cp1", "cp2", "cp3", "gate", "workshop", "lịch", "thời gian"
        ]

        text_lower = text_content.lower()
        if any(kw in text_lower for kw in keywords):
            doc_counter += 1
            doc_id = f"log_doc_{doc_counter}"

            if "deadline" in text_lower or "hạn" in text_lower or "nộp" in text_lower:
                intent = "deadline"
            elif "slide" in text_lower or "link" in text_lower or "drive" in text_lower or "github" in text_lower:
                intent = "document"
            elif "lịch" in text_lower or "workshop" in text_lower or "thời gian" in text_lower:
                intent = "schedule"
            elif "quy định" in text_lower or "nội quy" in text_lower:
                intent = "regulation"
            else:
                intent = "document"

            if "k4" in text_lower or "khóa 4" in text_lower:
                cohort = "K4"
            elif "k3" in text_lower or "khóa 3" in text_lower:
                cohort = "K3"
            elif "k2" in text_lower or "khóa 2" in text_lower:
                cohort = "K2"
            else:
                cohort = "ALL"

            if "gate 1" in text_lower:
                topic = "Gate 1"
            elif "gate 2" in text_lower:
                topic = "Gate 2"
            elif "cp1" in text_lower or "checkpoint 1" in text_lower:
                topic = "CP1"
            elif "cp2" in text_lower or "checkpoint 2" in text_lower:
                topic = "CP2"
            elif "cp3" in text_lower or "checkpoint 3" in text_lower:
                topic = "CP3"
            elif "workshop" in text_lower:
                topic = "Workshop"
            else:
                topic = "Tri thức Khóa học"

            urls = re.findall(r"https?://[^\s<]+", text_content)
            message_url = urls[0] if urls else "https://discord.com/channels/ai20k/commands"

            # Assign mentor role (score 20) for parsed history log items so official announcements (score 40) outrank them
            role = "official" if ("ban tổ chức" in author_name.lower() or "ban giáo trình" in author_name.lower()) else "mentor"

            extracted_docs.append({
                "id": doc_id,
                "channel_name": "Nhật ký Lịch sử Khóa học",
                "channel_id": "history_log",
                "message_url": message_url,
                "author_name": author_name,
                "author_role": role,
                "content": text_content[:300],
                "topic": topic,
                "intent": intent,
                "cohort": cohort,
                "posted_at": posted_at,
                "status": "active",
                "supersedes_source_id": None
            })

print(f"Extracted {len(extracted_docs)} knowledge entries from HTML log!")

base_docs = [
  {
    "id": "msg_001",
    "channel_name": "Thông báo Khóa học",
    "channel_id": "123456",
    "message_url": "https://discord.com/channels/mock/venture-arena/msg_001",
    "author_name": "Ban Tổ Chức",
    "author_role": "official",
    "content": "Deadline Gate 1 là 23:59 ngày 28/07/2026.",
    "topic": "Gate 1",
    "intent": "deadline",
    "cohort": "ALL",
    "posted_at": "2026-07-28T08:00:00+07:00",
    "status": "superseded",
    "supersedes_source_id": None
  },
  {
    "id": "msg_002",
    "channel_name": "Thông báo Khóa học",
    "channel_id": "123456",
    "message_url": "https://discord.com/channels/mock/venture-arena/msg_002",
    "author_name": "Ban Tổ Chức",
    "author_role": "official",
    "content": "CẬP NHẬT: Deadline Gate 1 dành cho Khóa 4 là 15:00 ngày 30/07/2026.",
    "topic": "Gate 1",
    "intent": "deadline",
    "cohort": "K4",
    "posted_at": "2026-07-30T08:10:00+07:00",
    "status": "active",
    "supersedes_source_id": "msg_001"
  },
  {
    "id": "msg_003",
    "channel_name": "Thông báo Khóa học",
    "channel_id": "789000",
    "message_url": "https://discord.com/channels/mock/cohort-2/msg_003",
    "author_name": "Ban Tổ Chức",
    "author_role": "official",
    "content": "Deadline Gate 1 Cohort 2 là 23:59 ngày 07/06/2026.",
    "topic": "Gate 1",
    "intent": "deadline",
    "cohort": "K2",
    "posted_at": "2026-06-07T08:00:00+07:00",
    "status": "expired",
    "supersedes_source_id": None
  },
  {
    "id": "msg_004",
    "channel_name": "Thông báo Khóa học",
    "channel_id": "333333",
    "message_url": "https://discord.com/channels/mock/thong-bao/msg_004",
    "author_name": "Ban Tổ Chức",
    "author_role": "official",
    "content": "Workshop tối nay bắt đầu lúc 20:00, áp dụng cho Khóa 3 và Khóa 4.",
    "topic": "Workshop",
    "intent": "workshop",
    "cohort": "ALL",
    "posted_at": "2026-07-30T09:00:00+07:00",
    "status": "active",
    "supersedes_source_id": None
  }
]

existing_contents = {d["content"][:50] for d in base_docs}
final_docs = list(base_docs)
new_added = 0

for d in extracted_docs:
    if d["content"][:50] not in existing_contents:
        final_docs.append(d)
        existing_contents.add(d["content"][:50])
        new_added += 1

data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mock_messages.json")
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(final_docs, f, ensure_ascii=False, indent=2)

print(f"Successfully updated {data_file} with {new_added} parsed knowledge entries. Total entries: {len(final_docs)}.")
