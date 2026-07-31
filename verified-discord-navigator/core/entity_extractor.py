import re
from typing import Dict, Optional


class EntityExtractor:
    """
    Extracts structured entities (cohort, topic, date_reference, resource_type) from user queries.
    """

    COHORT_PATTERNS = [
        (r'\b(khóa|khoá|cohort)\s*2\b|\bk2\b', "K2"),
        (r'\b(khóa|khoá|cohort)\s*3\b|\bk3\b', "K3"),
        (r'\b(khóa|khoá|cohort)\s*4\b|\bk4\b', "K4"),
    ]

    TOPIC_PATTERNS = [
        (r'\bgate\s*1\b', "Gate 1"),
        (r'\bgate\s*2\b', "Gate 2"),
        (r'\bgate\s*3\b', "Gate 3"),
        (r'\bcp2\b|\bcheckpoint\s*2\b', "CP2"),
        (r'\bcp1\b|\bcheckpoint\s*1\b', "CP1"),
        (r'\bcp3\b|\bcheckpoint\s*3\b', "CP3"),
        (r'\bcp4\b|\bcheckpoint\s*4\b', "CP4"),
        (r'\bcp5\b|\bcheckpoint\s*5\b', "CP5"),
        (r'\bxp\b|\bexp\b|\brank\b|\bđiểm\b', "XP"),
        (r'\bworkshop\b', "Workshop"),
        (r'\blab\b', "Lab"),
    ]

    DATE_PATTERNS = [
        (r'\btối\s*nay\b', "tối nay"),
        (r'\bhôm\s*nay\b|\bsáng\s*nay\b|\bchiều\s*nay\b', "hôm nay"),
        (r'\bngày\s*mai\b|\bmai\b', "ngày mai"),
        (r'\btuần\s*sau\b|\btuần\s*tới\b', "tuần sau"),
        (r'\btuần\s*này\b', "tuần này"),
        (r'\b\d{1,2}/\d{1,2}\b', "date_spec"),
    ]

    RESOURCE_PATTERNS = [
        (r'\bslide\b|\bbài\s*giảng\b', "slide"),
        (r'\blink\b|\bđường\s*dẫn\b|\burl\b', "link"),
        (r'\brepo\b|\bgithub\b|\bcode\b', "repo"),
        (r'\bdoc\b|\btài\s*liệu\b|\bfile\b|\bpdf\b', "document"),
    ]

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        text_lower = text.lower()

        # Cohort Extraction
        cohort = "UNKNOWN"
        for pattern, val in self.COHORT_PATTERNS:
            if re.search(pattern, text_lower):
                cohort = val
                break

        # Topic Extraction
        topic = None
        for pattern, val in self.TOPIC_PATTERNS:
            if re.search(pattern, text_lower):
                topic = val
                break

        # Date Reference Extraction
        date_reference = None
        for pattern, val in self.DATE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                date_reference = match.group(0) if val == "date_spec" else val
                break

        # Resource Type Extraction
        resource_type = None
        for pattern, val in self.RESOURCE_PATTERNS:
            if re.search(pattern, text_lower):
                resource_type = val
                break

        return {
            "cohort": cohort,
            "topic": topic,
            "date_reference": date_reference,
            "resource_type": resource_type
        }
