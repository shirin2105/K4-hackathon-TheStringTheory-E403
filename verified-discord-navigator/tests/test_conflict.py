from models.message import SourceMessage
from models.query import UserQuery
from core.source_ranker import SourceRanker
from core.conflict_detector import ConflictDetector


def test_conflict_detection_superseded():
    ranker = SourceRanker()
    detector = ConflictDetector()

    query = UserQuery(
        question="Khóa 4 nộp Gate 1 khi nào?",
        intent="deadline",
        cohort="K4",
        topic="Gate 1"
    )

    msg1 = SourceMessage(
        id="msg_001",
        channel_name="venture-arena",
        channel_id="123",
        message_url="http://mock/1",
        author_role="official",
        content="Deadline Gate 1 là 23:59 ngày 28/07/2026.",
        topic="Gate 1",
        intent="deadline",
        cohort="ALL",
        posted_at="2026-07-28T08:00:00+07:00",
        status="superseded"
    )

    msg2 = SourceMessage(
        id="msg_002",
        channel_name="venture-arena",
        channel_id="123",
        message_url="http://mock/2",
        author_role="official",
        content="CẬP NHẬT: Deadline Gate 1 cho Khóa 4 là 15:00 ngày 30/07/2026.",
        topic="Gate 1",
        intent="deadline",
        cohort="K4",
        posted_at="2026-07-30T08:10:00+07:00",
        status="active",
        supersedes_source_id="msg_001"
    )

    scored = ranker.rank_sources([msg1, msg2], query)
    top, rejected, has_conflict = detector.detect_and_resolve(scored, query)

    assert top is not None
    assert top.source.id == "msg_002"
    assert len(rejected) >= 1
    assert rejected[0].source.id == "msg_001"
    assert "cũ" in rejected[0].reason or "cập nhật" in rejected[0].reason
