from core.intent_classifier import IntentClassifier
from core.entity_extractor import EntityExtractor


def test_intent_classification():
    classifier = IntentClassifier()

    assert classifier.classify("Gate 1 khi nào hết hạn?") == "deadline"
    assert classifier.classify("Cho tôi slide workshop 2") == "document"
    assert classifier.classify("Tối nay có gì?") == "schedule"
    assert classifier.classify("Nộp bài ở đâu?") == "submission"
    assert classifier.classify("Một câu không liên quan") == "unknown"


def test_entity_extraction():
    extractor = EntityExtractor()

    res1 = extractor.extract("Deadline Gate 1 Khóa 4 là khi nào?")
    assert res1["cohort"] == "K4"
    assert res1["topic"] == "Gate 1"

    res2 = extractor.extract("Workshop tối nay lúc mấy giờ?")
    assert res2["topic"] == "Workshop"
    assert res2["date_reference"] == "tối nay"

    res3 = extractor.extract("Gate 1 Cohort 2 khi nào?")
    assert res3["cohort"] == "K2"
    assert res3["topic"] == "Gate 1"
