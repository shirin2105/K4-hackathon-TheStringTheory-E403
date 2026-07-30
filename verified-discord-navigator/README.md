# VERIFIED DISCORD NAVIGATOR (Checkpoint 2 Prototype)

> **Mini Hackathon AI — Batch 03 | Hướng B: Trợ lý Học viên (Discord)**

---

## 1. Product Overview & Pain Point

### Pain Point
Học viên trong Discord khóa học thường gặp tình trạng **loạn thông tin logistics**:
- Nguồn tin rải rác ở nhiều channel (`#thong-bao`, `#venture-arena`, `#cohort-2`...).
- Thông báo cũ bị thay thế bởi thông báo cập nhật muộn hơn nhưng học viên chỉ đọc tin nhắn cũ.
- Trả lời sai deadline hoặc sai mâu thuẫn thời gian gây hậu quả trực tiếp đến kết quả học tập của học viên.

### Giải pháp: Verified Discord Navigator
Bot không chỉ tìm kiếm theo từ khóa thông thường mà thực hiện quy trình xác minh 8 bước:
1. Phân loại Ý định (Intent Classification).
2. Trích xuất Thực thể (Cohort, Topic, Date reference, Resource type).
3. Truy xuất candidate announcements.
4. Chấm điểm nguồn theo 5 thành phần (Authority, Cohort match, Topic match, Freshness, Active status).
5. Phát hiện & giải quyết xung đột mâu thuẫn thời gian/cập nhật.
6. Ra quyết định (VERIFIED, VERIFIED_WITH_CONFLICT_RESOLVED, INSUFFICIENT_EVIDENCE).
7. Trả lời ngắn gọn kèm link nguồn chính thức & lý do loại các nguồn mâu thuẫn.
8. Tuyệt đối không suy đoán khi thiếu bằng chứng (`confidence < 60`).

---

## 2. User Flow & Core Pipeline

```
[User Slash Command / Mention]
          │
          ▼
   1. Receive Query (request_id, user_id, channel_id, question, timestamp)
          │
          ▼
   2. Intent Classification (deadline, schedule, workshop, document, etc.)
          │
          ▼
   3. Entity Extraction (Cohort: K3/K4/ALL, Topic: Gate 1/Workshop, etc.)
          │
          ▼
   4. Candidate Source Retrieval (from mock_messages.json)
          │
          ▼
   5. Source Ranking & Scoring (Authority + Cohort + Topic + Freshness + Status)
          │
          ▼
   6. Conflict Detection & Update Chain Resolution (supersedes_source_id)
          │
          ▼
   7. Decision Engine (VERIFIED / CONFLICT_RESOLVED / INSUFFICIENT_EVIDENCE)
          │
          ▼
   8. Discord Response Formatting (Rich Embeds & Interactive Buttons)
```

---

## 3. Architecture & Code Structure

```
verified-discord-navigator/
│
├── bot/
│   ├── main.py              # Discord Bot Client & Mention Listener
│   ├── commands.py          # Slash commands (/ask, /demo, /sources, /health)
│   ├── views.py             # Interactive Discord UI Buttons (Mở nguồn, Xem cách xác minh, Chuyển Mod...)
│   └── embeds.py            # Discord Embed formatting
│
├── core/
│   ├── intent_classifier.py  # Rule-based intent classifier
│   ├── entity_extractor.py  # Regex & Keyword entity extractor
│   ├── retriever.py         # Candidate source retriever
│   ├── source_ranker.py     # 5-factor scoring engine
│   ├── conflict_detector.py # Temporal & update chain conflict resolver
│   ├── decision_engine.py   # Decision orchestrator & threshold validator
│   └── response_builder.py  # Response payload formatting
│
├── data/
│   └── mock_messages.json   # Mock database of announcements
│
├── models/
│   ├── message.py           # SourceMessage Pydantic model
│   ├── query.py             # UserQuery Pydantic model
│   └── result.py            # DecisionResult & Status Enums
│
├── tests/
│   ├── test_classifier.py   # Intent & entity unit tests
│   ├── test_ranker.py       # Source scoring unit tests
│   ├── test_conflict.py     # Conflict resolution unit tests
│   └── test_end_to_end.py   # 5 mandatory hackathon scenarios test suite
│
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
└── run.py                   # CLI & Demo runner entry point
```

---

## 4. Setup & Environment Instructions

### Requirements
- Python 3.11+
- Virtual environment (`venv`)

### Installation

```bash
# 1. Clone or navigate to directory
cd verified-discord-navigator

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Environment Variables setup (`.env`)

Copy `.env.example` to `.env`:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
MOD_CHANNEL_ID=your_mod_channel_id_here
```

---

## 5. Execution Commands

### A. Run Demo Script (End-to-End Hackathon Scenarios)
No Discord Token required. Runs pre-packaged demonstration of the 3 required cases:

```bash
python run.py --demo
```

### B. Run Interactive Terminal CLI
Test custom questions directly in your terminal:

```bash
python run.py --cli
```

### C. Run Automated Test Suite
Executes unit tests and end-to-end tests for all 5 mandatory hackathon test cases:

```bash
pytest tests/ -v
```

### D. Launch Live Discord Bot
Runs the live Discord bot with slash commands:

```bash
python run.py
# Or:
python bot/main.py
```

---

## 6. Discord Commands & Interactivity

| Command | Usage | Description |
|---|---|---|
| `/ask` | `/ask question:<text>` | Hỏi câu hỏi để nhận thông tin đã xác minh |
| `@VerifiedBot` | `@VerifiedBot <câu hỏi>` | Mention bot trực tiếp trong channel |
| `/demo` | `/demo case:<verified\|conflict\|insufficient>` | Chạy nhanh 3 case demo |
| `/sources` | `/sources question:<text>` | Rà soát toàn bộ candidate sources & điểm số |
| `/health` | `/health` | Kiểm tra trạng thái hoạt động |

---

## 7. Mock vs. Real Components Matrix

| Component | Status CP2 (Current) | Roadmap CP3 (Future) |
|---|---|---|
| Data Store | Mock JSON (`data/mock_messages.json`) | Live Discord Message Ingestion & Vector DB (Qdrant / Chroma) |
| Intent / Entity Extraction | Keyword rules & Regex patterns | LLM Extraction (Gemini 1.5 / GPT-4o-mini) |
| Retrieval | Keyword matching & Topic overlap | Dense Embedding Retrieval + Hybrid BM25 |
| Source Ranking | 5-Factor Rule Engine | Reranking (Cohere Rerank / Cross-Encoder) |
| Temporal Conflict Resolution | Supersedes ID & Timestamp rules | LLM Temporal Reasoning & Citation Verification |
| Discord Bot | Live discord.py slash commands & buttons | Production deployment (Docker, Koyeb / Fly.io) |

---

## 8. Known Limitations in CP2

1. **Rule-based NLP:** Syntactic variations outside predefined keyword lists may fallback to `unknown` intent or `INSUFFICIENT_EVIDENCE`.
2. **Static Mock Dataset:** Real-time Discord message listeners are mocked via JSON for CP2 stability.
3. **Mod Escalation:** Mod forwarding button creates an ephemeral ticket tracking code in CP2 rather than posting to a live Zendesk/Discord ticket system.

---

## 9. CP3 Roadmap

1. **Ingestion Engine:** Discord Bot event listener for auto-indexing `#thong-bao`, `#announcements`, `#mod-support`.
2. **Embedding Pipeline:** Indexing texts into Vector DB with metadata filtering by `cohort`, `channel`, `posted_at`.
3. **LLM Citation Verifier:** Double-checking model answers against raw retrieved text chunks to ensure 0 hallucination.
4. **Golden Set & Evaluation:** Testing against golden set of 20+ realistic student questions with automated evaluation report.
