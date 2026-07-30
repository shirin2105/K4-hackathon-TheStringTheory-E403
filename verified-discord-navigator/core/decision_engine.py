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
    Main orchestration engine powered by DeepSeek LLM + Guardrailed Scoring Pipeline.
    """

    def __init__(self, data_path: Optional[str] = None):
        self.classifier = IntentClassifier()
        self.extractor = EntityExtractor()
        self.retriever = SourceRetriever(data_path=data_path)
        self.ranker = SourceRanker()
        self.conflict_detector = ConflictDetector()
        self.llm = DeepSeekClient()

    def process_query(
        self,
        question: str,
        user_id: str = "user_demo",
        channel_id: str = "channel_demo",
        messages: Optional[List[SourceMessage]] = None
    ) -> DecisionResult:
        # Step 1: Receive Question & Step 2: Classify Intent & Step 3: Entity Extraction
        intent = self.classifier.classify(question)
        entities = self.extractor.extract(question)

        # Enhance with DeepSeek LLM if rule-based classification is uncertain
        if intent == "unknown" or entities["topic"] is None:
            llm_analysis = self.llm.analyze_query(question)
            if llm_analysis:
                if intent == "unknown" and llm_analysis.get("intent"):
                    intent = llm_analysis["intent"]
                if entities["topic"] is None and llm_analysis.get("topic"):
                    entities["topic"] = llm_analysis["topic"]
                if entities["cohort"] == "UNKNOWN" and llm_analysis.get("cohort"):
                    entities["cohort"] = llm_analysis["cohort"]

        # Build UserQuery
        query = UserQuery(
            user_id=user_id,
            channel_id=channel_id,
            question=question,
            intent=intent,
            cohort=entities["cohort"],
            topic=entities["topic"],
            date_reference=entities["date_reference"],
            resource_type=entities["resource_type"]
        )

        # Step 4: Retrieve Candidate Sources
        candidates = self.retriever.retrieve(query, messages=messages)

        if not candidates:
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                answer="Hiện chưa tìm thấy thông báo chính thức đủ tin cậy để trả lời câu hỏi này.",
                selected_source=None,
                rejected_sources=[],
                candidate_sources=[],
                confidence=0.0,
                confidence_level="insufficient",
                needs_mod=True,
                verification_details={"reason": "No candidates found matching query"}
            )

        # Step 5: Rank and Score Sources
        scored_sources = self.ranker.rank_sources(candidates, query)

        # Step 6: Detect Conflicts
        top_scored, rejected_sources, has_conflict = self.conflict_detector.detect_and_resolve(
            scored_sources, query
        )

        # Step 7: Decision Rules based on Score Thresholds
        if not top_scored or top_scored.score < 60:
            return DecisionResult(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                answer="Hiện chưa tìm thấy thông báo chính thức đủ tin cậy để trả lời câu hỏi này.",
                selected_source=None,
                rejected_sources=rejected_sources,
                candidate_sources=[s.source for s in scored_sources],
                confidence=float(top_scored.score / 100.0) if top_scored else 0.0,
                confidence_level="insufficient",
                needs_mod=True,
                verification_details={
                    "top_score": top_scored.score if top_scored else 0,
                    "reason": "Top candidate score below minimum confidence threshold (60)"
                }
            )

        # Determine confidence level
        score = top_scored.score
        if score >= 80:
            conf_level = "high"
            normalized_conf = min(0.98, score / 100.0)
        else:
            conf_level = "medium"
            normalized_conf = score / 100.0

        top_msg = top_scored.source
        
        # Use DeepSeek LLM to synthesize clean response from verified announcement text
        answer_text = self.llm.synthesize_answer(question, top_msg.content, top_msg.cohort)

        if has_conflict and rejected_sources:
            status = DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED
        else:
            status = DecisionStatus.VERIFIED

        return DecisionResult(
            status=status,
            answer=answer_text,
            selected_source=top_msg,
            rejected_sources=rejected_sources,
            candidate_sources=[s.source for s in scored_sources],
            confidence=normalized_conf,
            confidence_level=conf_level,
            needs_mod=False,
            verification_details={
                "score_breakdown": top_scored.score_breakdown,
                "total_score": top_scored.score,
                "query_params": query.model_dump(),
                "llm_engine": "DeepSeek-V3 (deepseek-chat)"
            }
        )
