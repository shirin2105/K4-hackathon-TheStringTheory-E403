import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.message import SourceMessage
from models.query import UserQuery
from models.result import DecisionResult, DecisionStatus
from core.intent_classifier import IntentClassifier
from core.entity_extractor import EntityExtractor
from core.retriever import SourceRetriever
from core.source_ranker import SourceRanker, ScoredSource
from core.conflict_detector import ConflictDetector
from core.llm_client import DeepSeekClient

logger = logging.getLogger("DecisionEngine")


class DecisionEngine:
    """
    Central Decision Engine implementing the 8-Step Verification Pipeline:
    1. Intent Classification & Entity Extraction
    2. Candidate Retrieval (Retrieve First from Official Channel & 1,050 KB Entries)
    3. 8-Factor Source Scoring (Authority, Cohort, Topic, Date, Resource, Freshness, Status, Semantic)
    4. Confidence Threshold Gate (≥ 60.0 Score)
    5. Conflict Resolution & Supersedes Detection
    6. Time-Aware LLM Synthesis (DeepSeek V3) with Strict Time Comparison Guardrails
    """

    MIN_CONFIDENCE_SCORE = 60.0
    LINK_REQUEST_TERMS = ("link", "nguồn", "source", "thông báo", "xem chi tiết")
    ACTIONABLE_ANNOUNCEMENT_INTENTS = {"deadline", "schedule", "workshop"}
    DOCUMENT_ACTION_INTENTS = {"document", "submission"}

    def __init__(self, data_path: Optional[str] = None, api_key: Optional[str] = None):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.retriever = SourceRetriever(data_path=data_path)
        self.ranker = SourceRanker()
        self.conflict_detector = ConflictDetector()
        self.llm_client = DeepSeekClient(api_key=api_key)

    def process_query(
        self,
        question: str,
        request_id: str = "req_demo",
        user_id: str = "user_demo",
        channel_id: str = "channel_demo",
        messages: Optional[List[SourceMessage]] = None
    ) -> DecisionResult:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Intent Classification & Entity Extraction
        intent = self.intent_classifier.classify(question)
        if not self.intent_classifier.is_course_question(question, intent):
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                answer="Bot chỉ hỗ trợ hỏi đáp thông báo và thông tin thuộc khóa học từ nguồn dữ liệu đã xác minh.",
                selected_source=None,
                candidate_sources=[],
                rejected_sources=[],
                needs_mod=False,
                verification_details={"reason": "unsupported_course_question"},
            )
        entities = self.entity_extractor.extract(question)

        query = UserQuery(
            request_id=request_id,
            user_id=user_id,
            channel_id=channel_id,
            question=question,
            intent=intent,
            cohort=entities["cohort"],
            topic=entities["topic"],
            date_reference=entities["date_reference"],
            resource_type=entities["resource_type"]
        )

        # 2. RETRIEVE FIRST: Search official channel & 1,050 knowledge base entries
        all_candidates = self.retriever.retrieve(query, messages=messages)

        if not all_candidates:
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                answer="Hiện chưa tìm thấy thông báo hoặc tài liệu chính thức đủ tin cậy để trả lời câu hỏi này.",
                selected_source=None,
                candidate_sources=[],
                rejected_sources=[],
                needs_mod=True,
                verification_details={"reason": "No candidate sources retrieved from official channels"}
            )

        # 3. Rank & Score Sources
        scored_sources = self.ranker.rank_sources(all_candidates, query)
        top_scored = scored_sources[0]

        # 4. Confidence Threshold Gate (60.0 for official relevance)
        if top_scored.score < self.MIN_CONFIDENCE_SCORE:
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                confidence=float(max(0.05, top_scored.score / 100.0)),
                answer="Hiện chưa tìm thấy thông báo chính thức đủ tin cậy để trả lời câu hỏi này.",
                selected_source=None,
                candidate_sources=[s.source for s in scored_sources],
                rejected_sources=[],
                needs_mod=True,
                verification_details={
                    "top_score": top_scored.score,
                    "reason": f"Top candidate score below minimum confidence threshold ({self.MIN_CONFIDENCE_SCORE})"
                }
            )

        # 5. Detect Conflicts & Superseded Messages
        selected_scored, rejected_sources, has_conflict = self.conflict_detector.detect_and_resolve(scored_sources, query)
        final_source = selected_scored.source if selected_scored else None

        if final_source is None:
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.20,
                answer="Thông báo liên quan đã hết hiệu lực hoặc bị hủy bỏ. Không có dữ liệu chính thức mới hơn.",
                selected_source=None,
                candidate_sources=[s.source for s in scored_sources],
                rejected_sources=rejected_sources,
                needs_mod=True,
                verification_details={"reason": "Selected source expired or superseded without active replacement"}
            )

        # 6. Build Top 5 Timestamped Context Blocks for LLM Time-Aware Synthesis
        high_scoring_sources = [s for s in scored_sources if s.score >= 30.0]
        top_5_scored = high_scoring_sources[:5] if high_scoring_sources else scored_sources[:5]

        combined_content_blocks = []
        for idx, item in enumerate(top_5_scored, 1):
            src = item.source
            ch_name = f"#{src.channel_name}" if src.id.startswith("discord_") else src.channel_name
            posted_str = src.posted_at[:19].replace("T", " ")
            combined_content_blocks.append(
                f"--- Nguồn {idx} (Kênh: {ch_name} | Đăng bởi: {src.author_name} [{src.author_role}] | Thời điểm đăng: {posted_str} UTC | Topic: {src.topic} | Score: {item.score:.1f}): ---\n{src.content}"
            )

        context_content = "\n\n".join(combined_content_blocks)

        # 7. LLM Time-Aware Answer Synthesis with Time Guardrails
        llm_answer = self.llm_client.synthesize_answer(
            question=question,
            source_content=context_content,
            cohort=query.cohort,
            current_time_str=current_time_str
        )
        used_fallback = not bool(llm_answer)
        if used_fallback:
            llm_answer = (
                "Hệ thống AI đang tạm thời không phản hồi nên chưa thể xác minh cách diễn giải thông báo. "
                "Vui lòng thử lại sau hoặc chuyển Mod để kiểm tra nguồn chính thức."
            )

        refusal_phrases = [
            "xin lỗi, tôi là trợ lý khóa học", "không tìm thấy thông tin",
            "không có thông tin", "hoàn toàn không liên quan", "chưa tìm thấy thông tin"
        ]
        is_refusal = any(phrase in llm_answer.lower() for phrase in refusal_phrases)

        if used_fallback or is_refusal:
            status = DecisionStatus.INSUFFICIENT_EVIDENCE
            confidence = 0.20
            needs_mod = True
            selected_source = None
        else:
            status = DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED if has_conflict else DecisionStatus.VERIFIED
            confidence = float(min(0.99, max(0.65, top_scored.score / 100.0)))
            needs_mod = False
            selected_source = final_source

        # Determine Confidence Level String
        if confidence >= 0.85:
            conf_level = "high"
        elif confidence >= 0.60:
            conf_level = "medium"
        else:
            conf_level = "low"

        return DecisionResult(
            status=status,
            confidence=confidence,
            confidence_level=conf_level,
            answer=llm_answer,
            selected_source=selected_source,
            candidate_sources=[s.source for s in scored_sources],
            rejected_sources=rejected_sources,
            needs_mod=needs_mod,
            should_show_source_link=self._should_show_source_link(
                question=question,
                intent=intent,
                status=status,
                source=selected_source,
                has_conflict=has_conflict,
            ),
            verification_details={
                "total_score": top_scored.score,
                "score_breakdown": top_scored.score_breakdown,
                "has_conflict": has_conflict,
                "synthesized_by": "safe outage fallback" if used_fallback else "DeepSeek-V3 (deepseek-chat)"
            }
        )

    def _should_show_source_link(
        self,
        question: str,
        intent: str,
        status: DecisionStatus,
        source: Optional[SourceMessage],
        has_conflict: bool,
    ) -> bool:
        """Make a final, deterministic disclosure decision after answer verification."""
        if status not in {DecisionStatus.VERIFIED, DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED}:
            return False
        if not source or not source.message_url.startswith(("https://", "http://")):
            return False

        normalized_question = question.lower()
        user_requested_source = any(term in normalized_question for term in self.LINK_REQUEST_TERMS)
        is_live_actionable_announcement = (
            source.id.startswith("discord_") and intent in self.ACTIONABLE_ANNOUNCEMENT_INTENTS
        )
        return user_requested_source or has_conflict or is_live_actionable_announcement or intent in self.DOCUMENT_ACTION_INTENTS
