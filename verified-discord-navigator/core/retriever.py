import json
import os
import time
import re
from typing import List, Optional
from models.message import SourceMessage
from models.query import UserQuery
from core.entity_extractor import EntityExtractor
from core.intent_classifier import IntentClassifier


class SourceRetriever:
    """
    Retriever for official announcement messages EXCLUSIVELY from:
    1. Official Announcement Channel (`ANNOUNCEMENT_CHANNEL_ID: 1532306560871567390`)
    2. Official Course Documents & Handbook DB (`data/mock_messages.json`)
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "mock_messages.json")
        self.data_path = data_path
        self.extractor = EntityExtractor()
        self.classifier = IntentClassifier()

        self._live_cache: List[SourceMessage] = []
        self._last_fetch_time: float = 0
        self._cache_ttl_seconds: float = 60.0

    def load_all_messages(self) -> List[SourceMessage]:
        if not os.path.exists(self.data_path):
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [SourceMessage(**item) for item in raw_data]

    async def fetch_live_messages_async(self, bot, channel_id: str, limit: int = 50) -> List[SourceMessage]:
        """
        Fetches live messages EXCLUSIVELY from official announcement channel ID 1532306560871567390.
        Uses 60-second in-memory cache to prevent Discord API rate-limiting.
        """
        target_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID", "1532306560871567390").strip()

        if not channel_id or str(channel_id).strip() != target_channel_id:
            return []

        now = time.time()
        if self._live_cache and (now - self._last_fetch_time < self._cache_ttl_seconds):
            return self._live_cache

        try:
            channel = bot.get_channel(int(target_channel_id))
            if channel is None:
                channel = await bot.fetch_channel(int(target_channel_id))

            if channel is None:
                return self._live_cache

            live_msgs = []
            async for msg in channel.history(limit=limit):
                full_content = msg.content or ""
                if msg.embeds:
                    embed_texts = [f"{e.title or ''} {e.description or ''}".strip() for e in msg.embeds]
                    full_content = (full_content + " " + " ".join(embed_texts)).strip()

                if not full_content:
                    continue

                extracted = self.extractor.extract(full_content)
                intent = self.classifier.classify(full_content)

                topic = extracted["topic"] or "Thông báo"
                cohort = extracted["cohort"] if extracted["cohort"] != "UNKNOWN" else "ALL"

                author_role = "official"
                status = "updated" if "cập nhật" in full_content.lower() else "active"

                source_msg = SourceMessage(
                    id=f"discord_{msg.id}",
                    channel_name=getattr(channel, "name", "thông-báo"),
                    channel_id=str(channel.id),
                    message_url=msg.jump_url,
                    author_name=msg.author.display_name,
                    author_role=author_role,
                    content=full_content,
                    topic=topic,
                    intent=intent,
                    cohort=cohort,
                    posted_at=msg.created_at.isoformat(),
                    status=status,
                    supersedes_source_id=None
                )
                live_msgs.append(source_msg)

            self._live_cache = live_msgs
            self._last_fetch_time = now
            return live_msgs
        except Exception as e:
            print(f"[Live Fetch Warning]: {e}")
            return self._live_cache

    def retrieve(self, query: UserQuery, messages: Optional[List[SourceMessage]] = None) -> List[SourceMessage]:
        if messages is None:
            messages = self.load_all_messages()

        official_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID", "1532306560871567390").strip()

        candidates = []
        clean_q_text = re.sub(r"[^\w\s]", " ", query.question.lower())
        q_topic = query.topic.lower() if query.topic else None

        # Check if query asks for announcements, schedule, or daily tasks
        schedule_announcement_terms = [
            "thông báo", "mới nhất", "tin mới", "có gì mới", "hôm nay", "tối nay",
            "ngày mai", "lịch", "lịch học", "làm gì", "phải làm", "nhiệm vụ", "bài tập"
        ]
        is_general_announcement_query = any(term in clean_q_text for term in schedule_announcement_terms)

        stop_words = {
            "là", "gì", "ở", "đâu", "nào", "có", "không", "cho", "tôi", "xin",
            "hỏi", "mấy", "giờ", "bao", "nhiêu", "thì", "được", "với", "như", "hay",
            "cần", "tự", "của", "và", "học", "viên", "bạn", "mình", "anh", "em",
            "các", "về", "trong", "trên", "từ", "khoá", "khóa", "sử", "dụng", "áp",
            "dụng", "này", "đó", "đã", "đang", "theo", "sau", "trước", "bằng"
        }
        query_keywords = [w for w in clean_q_text.split() if w not in stop_words and len(w) > 1]

        for msg in messages:
            if msg.id.startswith("discord_") and msg.channel_id != official_channel_id:
                continue

            msg_topic = msg.topic.lower()
            msg_content = msg.content.lower()

            overlap = sum(1 for kw in query_keywords if kw in msg_content or kw in msg_topic)

            # Strict gateway for live channel messages
            if msg.channel_id == official_channel_id:
                if not is_general_announcement_query and overlap == 0 and not (q_topic and q_topic in msg_topic):
                    continue

            match_score = 0

            # Topic match
            if q_topic:
                if q_topic == msg_topic:
                    match_score += 5
                elif q_topic in msg_content:
                    match_score += 3

            # Intent match
            if query.intent.lower() != "unknown" and query.intent.lower() == msg.intent.lower():
                match_score += 1

            # Keyword overlap score
            match_score += (overlap * 2)

            # Live announcement relevance boost ONLY if relevant
            if msg.channel_id == official_channel_id and (is_general_announcement_query or overlap > 0):
                match_score += 5

            if match_score > 0:
                candidates.append(msg)

        return candidates
