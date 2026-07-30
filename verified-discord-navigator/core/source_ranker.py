import re
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
        "expired": -50
    }

    STOP_WORDS = {
        "là", "gì", "ở", "đâu", "nào", "có", "không", "cho", "tôi", "xin",
        "hỏi", "mấy", "giờ", "bao", "nhiêu", "thì", "được", "với", "như", "hay",
        "cần", "tự", "của", "và", "học", "viên", "bạn", "mình", "anh", "em",
        "các", "về", "trong", "trên", "từ", "khoá", "khóa", "sử", "dụng", "áp",
        "dụng", "này", "đó", "đã", "đang", "theo", "sau", "trước", "bằng",
        "mang", "tính", "nhà", "rất", "nhiều", "cần", "được", "hoặc", "trường"
    }

    GENERIC_TOPICS = {
        "thông báo", "thông báo khóa học", "tri thức khóa học", "n/a", "none", "unknown", ""
    }

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
                cohort_score = -50
        else:
            cohort_score = 15 if msg_cohort == "ALL" else 10
        breakdown["cohort_match_score"] = float(cohort_score)

        # 3. Topic Match Score (Exclude generic fallback topics)
        q_topic = (query.topic or "").lower().strip()
        msg_topic = source.topic.lower().strip()
        msg_content = source.content.lower()

        if q_topic and q_topic not in self.GENERIC_TOPICS:
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
        if q_date:
            q_date_lower = q_date.lower()
            if q_date_lower in msg_content:
                date_score = 15
            else:
                date_score = -60
        else:
            date_score = 0
        breakdown["date_match_score"] = float(date_score)

        # 5. Resource Type Match Score
        q_res = query.resource_type
        if q_res:
            q_res_lower = q_res.lower()
            if q_res_lower in msg_content or "http" in msg_content or "drive" in msg_content or ".pdf" in msg_content:
                res_score = 15
            else:
                res_score = -60
        else:
            res_score = 0
        breakdown["resource_match_score"] = float(res_score)

        # 6. Freshness Score
        freshness_score = 15 if is_newest else 0
        breakdown["freshness_score"] = float(freshness_score)

        # 7. Active Status Score
        status_score = self.STATUS_WEIGHTS.get(source.status, 0)
        breakdown["active_status_score"] = float(status_score)

        # 8. Query Relevance Guardrail (Clean exact word token matching)
        clean_q_text = re.sub(r"[^\w\s]", " ", query.question.lower())
        query_words = [w for w in clean_q_text.split() if w not in self.STOP_WORDS and len(w) > 1]
        is_general_announcement_query = any(term in clean_q_text for term in ["thông báo", "mới nhất", "tin mới", "có gì mới"])

        if query_words and not is_general_announcement_query:
            content_tokens = set(re.sub(r"[^\w\s]", " ", msg_content).split())
            matched_words = [w for w in query_words if w in content_tokens]

            has_keyword_match = (
                len(matched_words) >= 2 or
                any(w in ["laptop", "codelabs", "github", "drive"] for w in matched_words) or
                (q_topic and q_topic not in self.GENERIC_TOPICS and q_topic in msg_topic)
            )

            if not has_keyword_match:
                breakdown["relevance_penalty"] = -80.0

        # Total score calculation
        total_score = float(sum(breakdown.values()))

        # Cap history chat log entries (log_doc_) for schedule/deadline queries below 60 threshold
        if source.id.startswith("log_doc_") and query.intent in ["schedule", "deadline", "workshop"]:
            total_score = min(total_score, 55.0)

        return ScoredSource(source=source, score=total_score, score_breakdown=breakdown)

    def rank_sources(self, candidates: List[SourceMessage], query: UserQuery) -> List[ScoredSource]:
        if not candidates:
            return []

        sorted_by_time = sorted(
            candidates,
            key=lambda m: m.parse_posted_at(),
            reverse=True
        )
        newest_id = sorted_by_time[0].id if sorted_by_time else None

        scored_list = []
        for msg in candidates:
            is_newest = (msg.id == newest_id)
            scored = self.score_source(msg, query, is_newest=is_newest)
            scored_list.append(scored)

        scored_list.sort(key=lambda s: s.score, reverse=True)
        return scored_list
