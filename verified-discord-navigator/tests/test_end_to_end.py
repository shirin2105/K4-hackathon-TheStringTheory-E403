import os
import pytest
from core.decision_engine import DecisionEngine
from models.result import DecisionStatus


@pytest.fixture
def engine():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "mock_messages.json")
    instance = DecisionEngine(data_path=data_path)
    instance.llm_client.synthesize_answer = (
        lambda question, source_content, cohort, current_time_str=None: source_content
    )
    return instance


def test_llm_outage_fails_closed(engine):
    engine.llm_client.synthesize_answer = (
        lambda question, source_content, cohort, current_time_str=None: ""
    )

    res = engine.process_query("Workshop tối nay lúc mấy giờ?")

    assert res.status == DecisionStatus.INSUFFICIENT_EVIDENCE
    assert res.selected_source is None
    assert res.needs_mod is True
    assert "tạm thời không phản hồi" in res.answer
    assert res.verification_details["synthesized_by"] == "safe outage fallback"


def test_scenario_1_conflict_resolution(engine):
    """
    Test 1:
    Input: 'Khóa 4 nộp Gate 1 khi nào?'
    Expected:
    - status = VERIFIED_WITH_CONFLICT_RESOLVED
    - selected_source.id = msg_002
    - reject msg_001 because superseded
    - reject msg_003 because wrong cohort or expired
    """
    res = engine.process_query("Khóa 4 nộp Gate 1 khi nào?")

    assert res.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED
    assert res.selected_source is not None
    assert res.selected_source.id == "msg_002"

    rejected_ids = [r.source.id for r in res.rejected_sources]
    assert "msg_001" in rejected_ids
    assert "msg_003" in rejected_ids


def test_scenario_2_single_verified(engine):
    """
    Test 2:
    Input: 'Workshop tối nay lúc mấy giờ?'
    Expected:
    - status = VERIFIED
    - selected_source.id = msg_004
    - answer contains 20:00
    """
    res = engine.process_query("Workshop tối nay lúc mấy giờ?")

    assert res.status == DecisionStatus.VERIFIED
    assert res.selected_source is not None
    assert res.selected_source.id == "msg_004"
    assert "20:00" in res.answer


def test_scenario_3_insufficient_evidence(engine):
    """
    Test 3:
    Input: 'Tuần sau có workshop đặc biệt không?'
    Expected:
    - status = INSUFFICIENT_EVIDENCE
    - needs_mod = true
    - no hallucinated date or time
    """
    res = engine.process_query("Tuần sau có workshop đặc biệt không?")

    assert res.status == DecisionStatus.INSUFFICIENT_EVIDENCE
    assert res.needs_mod is True
    assert res.selected_source is None


def test_scenario_4_missing_document(engine):
    """
    Test 4:
    Input: 'Cho tôi slide Workshop 99'
    Expected:
    - status = INSUFFICIENT_EVIDENCE
    - no fake link generated
    """
    res = engine.process_query("Cho tôi slide Workshop 99")

    assert res.status == DecisionStatus.INSUFFICIENT_EVIDENCE
    assert res.selected_source is None


def test_scenario_5_historical_cohort(engine):
    """
    Test 5:
    Input: 'Gate 1 Cohort 2 khi nào?'
    Expected:
    - status = INSUFFICIENT_EVIDENCE (due to expired status score penalty) or flags expired
    - msg_003 is detected
    """
    res = engine.process_query("Gate 1 Cohort 2 khi nào?")

    assert res.status == DecisionStatus.INSUFFICIENT_EVIDENCE
    assert res.needs_mod is True


def test_out_of_scope_question_does_not_search_or_call_llm(engine):
    engine.retriever.retrieve = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("retrieval should not run"))
    engine.llm_client.synthesize_answer = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM should not run"))

    res = engine.process_query("What is the weather today?")

    assert res.status == DecisionStatus.INSUFFICIENT_EVIDENCE
    assert res.needs_mod is False
    assert res.verification_details["reason"] == "unsupported_course_question"
