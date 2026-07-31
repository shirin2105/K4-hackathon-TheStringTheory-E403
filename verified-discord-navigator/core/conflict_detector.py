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

        q_cohort = query.cohort.upper() if query.cohort else "UNKNOWN"
        rejected: List[RejectedSource] = []
        has_conflict = False

        # 1. Check if official announcement for this query topic/cohort is expired/superseded with no active replacement
        official_expired = [
            s for s in scored_sources
            if s.source.status in ["superseded", "expired"]
            and not s.source.id.startswith("log_doc_")
            and (q_cohort == "UNKNOWN" or s.source.cohort.upper() in [q_cohort, "ALL"])
            and (not query.topic or s.source.topic.lower() == query.topic.lower())
        ]
        official_active = [
            s for s in scored_sources
            if s.source.status in ["active", "updated"]
            and not s.source.id.startswith("log_doc_")
            and (q_cohort == "UNKNOWN" or s.source.cohort.upper() in [q_cohort, "ALL"])
            and (not query.topic or s.source.topic.lower() == query.topic.lower())
        ]

        if official_expired and not official_active:
            for item in official_expired:
                rejected.append(RejectedSource(
                    source=item.source,
                    reason="Thông báo đã hết hiệu lực hoặc bị thay thế"
                ))
            return None, rejected, True

        # 2. Select top candidate
        if q_cohort != "UNKNOWN":
            cohort_candidates = [s for s in scored_sources if s.source.cohort.upper() in [q_cohort, "ALL"]]
            top_candidate = cohort_candidates[0] if cohort_candidates else scored_sources[0]
        else:
            top_candidate = scored_sources[0]

        if top_candidate.source.status in ["superseded", "expired"]:
            has_conflict = True
            rejected.append(RejectedSource(
                source=top_candidate.source,
                reason="Thông báo đã hết hiệu lực hoặc bị thay thế"
            ))
            valid_sources = [
                s for s in scored_sources
                if s.source.status not in ["superseded", "expired"]
                and (q_cohort == "UNKNOWN" or s.source.cohort.upper() in [q_cohort, "ALL"])
                and s.source.topic.lower() == top_candidate.source.topic.lower()
            ]
            if valid_sources:
                return valid_sources[0], rejected, True
            return None, rejected, True

        for item in scored_sources:
            if item.source.id == top_candidate.source.id:
                continue

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
                elif q_cohort != "UNKNOWN" and other.cohort != "ALL" and other.cohort != q_cohort:
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
