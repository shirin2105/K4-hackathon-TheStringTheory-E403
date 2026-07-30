from typing import List, Tuple, Optional
from models.message import SourceMessage
from models.query import UserQuery
from models.result import RejectedSource
from core.source_ranker import ScoredSource


class ConflictDetector:
    """
    Detects conflicts between candidate announcements and resolves them
    by evaluating update chain, timestamps, status, and cohort scoping.
    """

    def detect_and_resolve(
        self,
        scored_sources: List[ScoredSource],
        query: UserQuery
    ) -> Tuple[Optional[ScoredSource], List[RejectedSource], bool]:
        """
        Returns:
            (selected_source, rejected_sources, has_conflict)
        """
        if not scored_sources:
            return None, [], False

        top_candidate = scored_sources[0]

        if len(scored_sources) == 1:
            if top_candidate.source.status in ["superseded", "expired"]:
                reason = "Thông báo đã hết hiệu lực hoặc bị thay thế"
                return None, [RejectedSource(source=top_candidate.source, reason=reason)], False
            return top_candidate, [], False

        rejected: List[RejectedSource] = []
        has_conflict = False

        for item in scored_sources[1:]:
            other = item.source

            # Skip historical background log entries when calculating official announcement conflicts
            if other.id.startswith("log_doc_"):
                continue

            # Only evaluate active competing candidates (score >= 60) or explicit superseding links
            if item.score < 60 and top_candidate.source.supersedes_source_id != other.id and other.status not in ["superseded", "expired"]:
                continue

            is_same_topic = (other.topic.lower() == top_candidate.source.topic.lower())

            if is_same_topic or top_candidate.source.supersedes_source_id == other.id:
                has_conflict = True

                if top_candidate.source.supersedes_source_id == other.id or other.status == "superseded":
                    rejected.append(RejectedSource(
                        source=other,
                        reason="Thông báo cũ đã được cập nhật"
                    ))
                elif query.cohort != "UNKNOWN" and other.cohort != "ALL" and other.cohort != query.cohort:
                    rejected.append(RejectedSource(
                        source=other,
                        reason=f"Thông báo cũ thuộc Cohort {other.cohort.replace('K', '')}"
                    ))
                elif other.status == "expired":
                    rejected.append(RejectedSource(
                        source=other,
                        reason="Thông báo đã hết hiệu lực"
                    ))
                else:
                    rejected.append(RejectedSource(
                        source=other,
                        reason="Thông báo cũ hơn hoặc có điểm tin cậy thấp hơn"
                    ))

        return top_candidate, rejected, has_conflict
