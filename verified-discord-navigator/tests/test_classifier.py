import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from core.intent_classifier import IntentClassifier
from core.entity_extractor import EntityExtractor
from core.response_builder import ResponseBuilder
from core.retriever import SourceRetriever
from models.message import SourceMessage
from models.result import DecisionResult, DecisionStatus


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


def test_embed_description_is_bounded():
    result = DecisionResult(
        status=DecisionStatus.VERIFIED,
        confidence=0.9,
        answer="x" * 5000,
        selected_source=None,
        candidate_sources=[],
        rejected_sources=[],
        needs_mod=False,
    )

    embed = ResponseBuilder.build_embed_dict(result)

    assert len(embed["description"]) == ResponseBuilder.MAX_DESCRIPTION_LENGTH
    assert embed["description"].endswith("…")


def test_verified_embed_includes_discord_source_link():
    source = SourceMessage(
        id="discord_99",
        channel_name="thong-bao",
        channel_id="123456789",
        message_url="https://discord.com/channels/1/123456789/99",
        content="Mentor Duty diễn ra lúc 20:00.",
        topic="Announce",
        intent="schedule",
        posted_at="2026-07-31T20:00:00",
    )
    result = DecisionResult(
        status=DecisionStatus.VERIFIED,
        confidence=0.9,
        answer="Mentor Duty bắt đầu lúc 20:00.",
        selected_source=source,
        candidate_sources=[source],
        rejected_sources=[],
        needs_mod=False,
        should_show_source_link=True,
    )

    embed = ResponseBuilder.build_embed_dict(result)

    assert "Xem thông báo gốc" in embed["description"]
    assert source.message_url in embed["description"]


def test_verified_embed_hides_link_when_disclosure_is_disabled():
    source = SourceMessage(
        id="discord_100",
        channel_name="thong-bao",
        channel_id="123456789",
        message_url="https://discord.com/channels/1/123456789/100",
        content="Course concept information.",
        topic="XP",
        intent="unknown",
        posted_at="2026-07-31T20:00:00",
    )
    result = DecisionResult(
        status=DecisionStatus.VERIFIED,
        confidence=0.9,
        answer="Course concept answer.",
        selected_source=source,
        candidate_sources=[source],
        rejected_sources=[],
        needs_mod=False,
        should_show_source_link=False,
    )

    embed = ResponseBuilder.build_embed_dict(result)

    assert "Xem thông báo gốc" not in embed["description"]
    assert source.message_url not in embed["description"]


def test_live_message_ingestion_builds_complete_source(monkeypatch):
    channel_id = "123456789"
    monkeypatch.setenv("ANNOUNCEMENT_CHANNEL_ID", channel_id)
    content = "THÔNG BÁO LỊCH HOẠT ĐỘNG: Thứ 4 | 20:00 Mentor Duty"
    message = SimpleNamespace(
        id=99,
        author=SimpleNamespace(bot=False, display_name="BTC", name="BTC"),
        content=content,
        created_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
        jump_url=f"https://discord.com/channels/1/{channel_id}/99",
    )

    class AsyncHistory:
        def __aiter__(self):
            self._messages = iter([message])
            return self

        async def __anext__(self):
            try:
                return next(self._messages)
            except StopIteration:
                raise StopAsyncIteration

    channel = SimpleNamespace(
        id=int(channel_id),
        name="thong-bao",
        history=lambda limit: AsyncHistory(),
    )
    bot = SimpleNamespace(get_channel=lambda requested_id: channel)

    sources = asyncio.run(SourceRetriever().fetch_live_messages_async(bot, channel_id))

    assert len(sources) == 1
    assert sources[0].channel_id == channel_id
    assert sources[0].channel_name == "thong-bao"
    assert sources[0].message_url.endswith("/99")
    assert sources[0].intent == "schedule"
    assert sources[0].content == content


def test_course_scope_requires_a_course_anchor():
    classifier = IntentClassifier()

    assert classifier.is_course_question("Lich mentor duty") is True
    assert classifier.is_course_question("What is the deadline for my taxes?") is False
    assert classifier.is_course_question("Give me a link to OpenAI docs") is False
