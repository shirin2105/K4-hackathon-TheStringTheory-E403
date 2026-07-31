import re
from datetime import datetime
from typing import List, Tuple, Dict, Any
from models.message import SourceMessage
from models.query import UserQuery


class ScoredSource:
    def __init__(self, source: SourceMessage, score: float, score_breakdown: Dict[str, float]):
        self.source = source
        self.score = score
        self.score_breakdown = score_breakdown

    def __repr__(self):
        return f"<ScoredSource {self.source.id} score={self.score}>"


class SourceRanker:
    """
    Ranks and scores candidate sources based on authority, cohort alignment,
    topic match, date reference match, resource type match, freshness, status,
    and semantic query relevance.
    """

    AUTHORITY_WEIGHTS = {
        "official": 40,
        "mod": 30,
        "mentor": 20,
        "student": 5
    }

    STATUS_WEIGHTS = {
        "updated": 25,
        "active": 20,
        "superseded": -40,
        "expired": -70
    }

    STOP_WORDS = {
        "là", "gì", "ở", "đâu", "nào", "có", "không", "cho", "tôi", "xin",
        "hỏi", "mấy", "giờ", "bao", "nhiêu", "thì", "được", "với", "như", "hay",
        "cần", "tự", "của", "và", "học", "viên", "bạn", "mình", "anh", "em",
        "các", "về", "trong", "trên", "từ", "khoá", "khóa", "sử", "dụng", "áp",
        "dụng", "này", "đó", "đang", "theo", "sau", "trước", "bằng",
        "mang", "tính", "nhà", "rất", "nhiều", "cần", "được", "hoặc", "trường"
    }

    GENERIC_TOPICS = {
        "thông báo", "thông báo khóa học", "tri thức khóa học", "n/a", "none", "unknown", ""
    }

    SCHEDULE_ANNOUNCEMENT_TERMS = [
        "thông báo", "mới nhất", "tin mới", "có gì mới", "hôm nay", "tối nay",
        "ngày mai", "lịch", "lịch học", "làm gì", "phải làm", "nhiệm vụ", "bài tập"
    ]

    TODAY_TERMS = ["hôm nay", "tối nay", "sáng nay", "chiều nay"]

    def score_source(
        self,
        source: SourceMessage,
        query: UserQuery,
        is_newest: bool = False
    ) -> ScoredSource:
        breakdown = {}

        # 1. Authority Score
        auth_score = self.AUTHORITY_WEIGHTS.get(source.author_role, 5)
        breakdown["authority_score"] = float(auth_score)

        # 2. Cohort Match Score
        q_cohort = query.cohort.upper()
        msg_cohort = source.cohort.upper()

        if q_cohort != "UNKNOWN":
            if msg_cohort == q_cohort:
                cohort_score = 25
            elif msg_cohort == "ALL":
                cohort_score = 15
            else:
                cohort_score = -100
        else:
            cohort_score = 15 if msg_cohort == "ALL" else 10
        breakdown["cohort_match_score"] = float(cohort_score)

        # 3. Topic & Specific Entity Match Score
        q_topic = (query.topic or "").lower().strip()
        msg_topic = source.topic.lower().strip()
        msg_content = source.content.lower()
        clean_q_text = re.sub(r"[^\w\s]", " ", query.question.lower())

        # Check for specific numbered entity request (e.g. "Workshop 99", "Gate 99") or specific modifiers ("đặc biệt")
        numbers_in_query = re.findall(r'\b\d+\b', clean_q_text)
        has_unmatched_number = any(num not in msg_content and num not in msg_topic for num in numbers_in_query)
        has_unmatched_modifier = ("đặc biệt" in clean_q_text and "đặc biệt" not in msg_content)

        if has_unmatched_number or has_unmatched_modifier:
            topic_score = -100
        elif q_topic and q_topic not in self.GENERIC_TOPICS:
            if q_topic == msg_topic:
                topic_score = 20
            elif q_topic in msg_content:
                topic_score = 10
            else:
                topic_score = -60
        else:
            topic_score = 0
        breakdown["topic_match_score"] = float(topic_score)

        # 4. Date Reference Match Score
        q_date = query.date_reference
        if not q_date:
            if any(term in clean_q_text for term in self.TODAY_TERMS):
                q_date = "hôm nay"

        now_dt = datetime.now()
        today_date_str = now_dt.strftime("%Y-%m-%d")
        today_dm_str = now_dt.strftime("%d/%m")
        today_dm_short = now_dt.strftime("%d/%m").lstrip("0").replace("/0", "/")

        if q_date:
            q_date_lower = q_date.lower()
            if q_date_lower in self.TODAY_TERMS:
                msg_posted_date = source.posted_at[:10] if source.posted_at else ""
                if source.status in ["active", "updated"] or msg_posted_date == today_date_str or today_dm_str in msg_content or today_dm_short in msg_content:
                    date_score = 15
                else:
                    date_score = -100
            elif q_date_lower in msg_content:
                date_score = 15
            else:
                date_score = -100
        else:
            date_score = 0
        breakdown["date_match_score"] = float(date_score)

        # 5. Resource Type Match Score
        q_res = query.resource_type
        if q_res:
            q_res_lower = q_res.lower()
            msg_res_type = getattr(source, "resource_type", "") or ""
            if q_res_lower in msg_content or msg_res_type.lower() == q_res_lower:
                res_score = 15
            else:
                res_score = -100
        else:
            res_score = 0
        breakdown["resource_match_score"] = float(res_score)

        # 6. Freshness Score
        freshness_score = 15 if is_newest else 0
        breakdown["freshness_score"] = float(freshness_score)

        # 7. Active Status Score
        status_score = self.STATUS_WEIGHTS.get(source.status, 0)
        breakdown["status_score"] = float(status_score)

        # 8. Query Keyword Overlap Score
        q_tokens = set([w for w in clean_q_text.split() if w not in self.STOP_WORDS and len(w) > 1])

        # XP/EXP/Rank handling
        if any(term in clean_q_text for term in ["xp", "exp", "rank"]):
            q_tokens.add("xp")
            q_tokens.add("rank")

        msg_tokens = set(re.findall(r'\w+', msg_content))
        overlap_count = len(q_tokens.intersection(msg_tokens))
        semantic_score = min(25, overlap_count * 5)
        breakdown["semantic_score"] = float(semantic_score)

        total_score = auth_score + cohort_score + topic_score + date_score + res_score + freshness_score + status_score + semantic_score

        return ScoredSource(
            source=source,
            score=max(0.0, float(total_score)),
            score_breakdown=breakdown
        )

    def rank_sources(self, sources: List[SourceMessage], query: UserQuery) -> List[ScoredSource]:
        if not sources:
            return []

        sorted_sources = sorted(sources, key=lambda x: x.posted_at, reverse=True)
        newest_id = sorted_sources[0].id if sorted_sources else None

        scored_sources = []
        for src in sources:
            is_newest = (src.id == newest_id)
            scored = self.score_source(src, query, is_newest=is_newest)
            scored_sources.append(scored)

        scored_sources.sort(key=lambda x: x.score, reverse=True)
        return scored_sources
