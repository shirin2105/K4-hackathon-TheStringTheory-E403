import re
from typing import Dict, Any, Optional


class EntityExtractor:
    """
    Rule & Regex entity extractor for CP2 hackathon prototype.
    Extracts cohort, topic, date_reference, and resource_type.
    """

    COHORT_PATTERNS = [
        (re.compile(r"\b(khóa|khoá)\s*4\b|\bk4\b", re.IGNORECASE), "K4"),
        (re.compile(r"\b(khóa|khoá)\s*3\b|\bk3\b", re.IGNORECASE), "K3"),
        (re.compile(r"\b(khóa|khoá)\s*2\b|\bk2\b", re.IGNORECASE), "K2"),
        (re.compile(r"\b(khóa|khoá)\s*1\b|\bk1\b", re.IGNORECASE), "K1"),
        (re.compile(r"\bcohort\s*2\b", re.IGNORECASE), "K2"),
        (re.compile(r"\bcohort\s*3\b", re.IGNORECASE), "K3"),
        (re.compile(r"\bcohort\s*4\b", re.IGNORECASE), "K4"),
    ]

    DYNAMIC_TOPIC_PATTERNS = [
        re.compile(r"\bworkshop\s*\d+\b", re.IGNORECASE),
        re.compile(r"\bgate\s*\d+\b", re.IGNORECASE),
        re.compile(r"\bcheckpoint\s*\d+\b|\bcp\s*\d+\b", re.IGNORECASE),
    ]

    STATIC_TOPIC_PATTERNS = [
        (re.compile(r"\bworkshop\b", re.IGNORECASE), "Workshop"),
        (re.compile(r"\bgate\b", re.IGNORECASE), "Gate"),
        (re.compile(r"\bventure\s*arena\b", re.IGNORECASE), "Venture Arena"),
    ]

    DATE_REF_PATTERNS = [
        "tối nay", "hôm nay", "chiều nay", "sáng nay",
        "tuần sau", "ngày mai", "tuần này", "cuối tuần"
    ]

    RESOURCE_PATTERNS = [
        "slide", "link", "repo", "form", "thread", "tài liệu", "đáp án", "code"
    ]

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        text_lower = text.lower()

        # Cohort extraction
        cohort = "UNKNOWN"
        for pattern, val in self.COHORT_PATTERNS:
            if pattern.search(text):
                cohort = val
                break

        # Dynamic Topic extraction (e.g. Workshop 99, Gate 1, CP2)
        topic = None
        for pattern in self.DYNAMIC_TOPIC_PATTERNS:
            match = pattern.search(text)
            if match:
                topic = match.group(0).title()
                break

        # Static Topic fallback if dynamic match not found
        if not topic:
            for pattern, val in self.STATIC_TOPIC_PATTERNS:
                if pattern.search(text):
                    topic = val
                    break

        # Date reference extraction
        date_ref = None
        for ref in self.DATE_REF_PATTERNS:
            if ref in text_lower:
                date_ref = ref
                break

        # Resource type extraction
        res_type = None
        for res in self.RESOURCE_PATTERNS:
            if res in text_lower:
                res_type = res
                break

        return {
            "cohort": cohort,
            "topic": topic,
            "date_reference": date_ref,
            "resource_type": res_type
        }
