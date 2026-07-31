INTENT_KEYWORDS = {
    "document": [
        "slide", "tài liệu", "link", "repo", "form", "thread", "bài giảng", "file"
    ],
    "deadline": [
        "deadline", "hạn", "nộp khi nào", "hết hạn", "chốt lúc nào",
        "hạn nộp", "nộp bài hạn", "khi nào hết hạn", "bao giờ nộp", "nộp gate"
    ],
    "submission": [
        "nộp ở đâu", "submit", "cách nộp", "nộp bài ở đâu", "địa chỉ nộp"
    ],
    "schedule": [
        "hôm nay", "tối nay", "lịch", "mấy giờ", "khi nào", "lịch học", "mấy h"
    ],
    "workshop": [
        "workshop", "lớp workshop", "ws", "buổi chia sẻ"
    ],
    "regulation": [
        "quy định", "nội quy", "điều khoản", "quy tắc", "thể lệ"
    ]
}

INTENT_PRIORITY = ["document", "deadline", "submission", "schedule", "workshop", "regulation"]

COURSE_SCOPE_TERMS = {
    "ai20k", "build phase", "khóa", "khoá", "cohort", "mentor", "duty",
    "office hours", "workshop", "weekly", "daily", "gate", "checkpoint",
    "cp", "xp", "rank", "discord", "thông báo", "thong bao",
}


class IntentClassifier:
    """
    Rule-based intent classifier with priority handling for CP2 hackathon prototype.
    """
    def __init__(self):
        self.keywords = INTENT_KEYWORDS

    def classify(self, text: str) -> str:
        text_lower = text.lower()

        matched_intents = set()
        for intent, kw_list in self.keywords.items():
            if any(kw in text_lower for kw in kw_list):
                matched_intents.add(intent)

        if not matched_intents:
            return "unknown"

        # Select highest priority intent matched
        for intent in INTENT_PRIORITY:
            if intent in matched_intents:
                return intent

        return list(matched_intents)[0]

    def is_course_question(self, text: str, intent: str | None = None) -> bool:
        """Return whether a question is within the course announcement/knowledge scope."""
        normalized_text = text.lower()
        return any(term in normalized_text for term in COURSE_SCOPE_TERMS)
