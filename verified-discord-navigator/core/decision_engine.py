import os
from datetime import datetime
from typing import List, Optional
from models.query import UserQuery
from models.message import SourceMessage
from models.result import DecisionResult, DecisionStatus, RejectedSource
from core.intent_classifier import IntentClassifier
from core.entity_extractor import EntityExtractor
from core.retriever import SourceRetriever
from core.source_ranker import SourceRanker, ScoredSource
from core.conflict_detector import ConflictDetector
from core.llm_client import DeepSeekClient


class DecisionEngine:
    """
    Main orchestrator for Verified Discord Navigator.
    Integrates NLP classification, retrieval, multi-factor ranking,
    conflict detection, Top 5 timestamp synthesis, and DeepSeek LLM.
    Enforces Retrieve First, Decide Second Strategy.
    """

    MIN_CONFIDENCE_SCORE = 60.0

    def __init__(self, data_path: Optional[str] = None):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.retriever = SourceRetriever(data_path=data_path)
        self.ranker = SourceRanker()
        self.conflict_detector = ConflictDetector()
        self.llm_client = DeepSeekClient()

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
        final_source = selected_scored.source if selected_scored else top_scored.source

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

        # 7. LLM Time-Aware Answer Synthesis (Retrieve First, Decide Second)
        llm_answer = self.llm_client.synthesize_answer(
            question=question,
            source_content=context_content,
            cohort=query.cohort,
            current_time_str=current_time_str
        )

        refusal_terms = [
            "chỉ hỗ trợ giải đáp các thắc mắc", "chưa có thông tin", "không tìm thấy thông tin",
            "không có thông tin", "không đề cập", "không có đề cập", "chưa đề cập", "không thấy"
        ]
        if any(term in llm_answer.lower() for term in refusal_terms):
            status = DecisionStatus.INSUFFICIENT_EVIDENCE
            confidence = 0.20
            needs_mod = True
            selected_source = None
        else:
            status = DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED if has_conflict else DecisionStatus.VERIFIED
            confidence = float(min(0.99, max(0.65, top_scored.score / 100.0)))
            needs_mod = False
            selected_source = final_source

        query_dict = query.model_dump() if hasattr(query, "model_dump") else query.dict()

        return DecisionResult(
            status=status,
            confidence=confidence,
            answer=llm_answer,
            selected_source=selected_source,
            candidate_sources=[s.source for s in scored_sources],
            rejected_sources=rejected_sources,
            needs_mod=needs_mod,
            verification_details={
                "score_breakdown": top_scored.score_breakdown,
                "total_score": top_scored.score,
                "query_params": query_dict,
                "current_system_time": current_time_str,
                "top_5_sources_used": len(top_5_scored),
                "llm_engine": "DeepSeek-V3 (deepseek-chat)"
            }
        )
