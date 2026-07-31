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
                if msg.author.bot:
                    continue

                clean_content = msg.content.strip()
                if not clean_content:
                    continue

                posted_at_iso = msg.created_at.strftime("%Y-%m-%dT%H:%M:%S")

                entities = self.extractor.extract(clean_content)

                source_msg = SourceMessage(
                    id=f"discord_{msg.id}",
                    channel_name=getattr(channel, "name", "thông-báo"),
                    channel_id=str(channel.id),
                    message_url=msg.jump_url,
                    author_name=msg.author.display_name or msg.author.name,
                    author_role="official",
                    posted_at=posted_at_iso,
                    content=clean_content,
                    cohort=entities["cohort"] if entities["cohort"] != "UNKNOWN" else "ALL",
                    topic=entities["topic"] or "Announce",
                    intent=self.classifier.classify(clean_content),
                    status="active"
                )
                live_msgs.append(source_msg)

            self._live_cache = live_msgs
            self._last_fetch_time = now
            return self._live_cache

        except Exception as e:
            print(f"[Live Fetch Error]: {e}")
            return self._live_cache

    def retrieve(self, query: UserQuery, messages: Optional[List[SourceMessage]] = None) -> List[SourceMessage]:
        if messages is None:
            messages = self.load_all_messages()
        return self.retrieve_candidates(query, messages)

    def retrieve_candidates(self, query: UserQuery, messages: List[SourceMessage], top_k: Optional[int] = None) -> List[SourceMessage]:
        if not messages:
            return []

        scored_candidates = []
        raw_q = getattr(query, 'raw_question', getattr(query, 'question', ''))
        q_lower = raw_q.lower()
        q_tokens = set(re.findall(r'\w+', q_lower))

        for msg in messages:
            content_lower = msg.content.lower()
            topic_lower = (msg.topic or "").lower()

            base_score = 0.0

            if msg.cohort == query.cohort:
                base_score += 15.0
            elif msg.cohort == "ALL":
                base_score += 10.0

            if query.topic and (query.topic.lower() in content_lower or query.topic.lower() in topic_lower):
                base_score += 25.0

            msg_tokens = set(re.findall(r'\w+', content_lower))
            overlap = len(q_tokens.intersection(msg_tokens))
            base_score += overlap * 4.0

            normalized_channel = msg.channel_name.lstrip("#").lower()
            if normalized_channel in ["thông báo khóa học", "venture-arena", "thong-bao", "thông-báo"]:
                base_score += 15.0

            if base_score > 0 or len(q_tokens) == 0:
                scored_candidates.append((base_score, msg))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        results = [candidate for score, candidate in scored_candidates]
        if top_k is not None:
            return results[:top_k]
        return results
