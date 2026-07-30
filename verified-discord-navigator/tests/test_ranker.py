from models.message import SourceMessage
from models.query import UserQuery
from core.source_ranker import SourceRanker


def test_source_ranking_weights():
    ranker = SourceRanker()
    query = UserQuery(
        question="Khóa 4 nộp Gate 1 khi nào?",
        intent="deadline",
        cohort="K4",
        topic="Gate 1"
    )

    msg_k4 = SourceMessage(
        id="msg_002",
        channel_name="venture-arena",
        channel_id="123",
        message_url="http://mock/2",
        author_role="official",
        content="Deadline Gate 1 Khóa 4 là 15:00 ngày 30/07/2026.",
        topic="Gate 1",
        intent="deadline",
        cohort="K4",
        posted_at="2026-07-30T08:10:00+07:00",
        status="active"
    )

    msg_k2 = SourceMessage(
        id="msg_003",
        channel_name="cohort-2",
        channel_id="789",
        message_url="http://mock/3",
        author_role="official",
        content="Deadline Gate 1 Cohort 2 là 23:59 ngày 07/06/2026.",
        topic="Gate 1",
        intent="deadline",
        cohort="K2",
        posted_at="2026-06-07T08:00:00+07:00",
        status="expired"
    )

    scored = ranker.rank_sources([msg_k4, msg_k2], query)

    assert len(scored) == 2
    assert scored[0].source.id == "msg_002"
    assert scored[0].score > scored[1].score
