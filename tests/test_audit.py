from datetime import datetime, timedelta, timezone

import pytest

from agentshield.audit.log import AuditLog
from agentshield.checks.policy import PolicyEngine
from agentshield.checks.taint import TaintChecker
from agentshield.core.engine import Engine
from agentshield.core.models import (
    AuditRecord,
    CheckName,
    CheckResult,
    ContextItem,
    Decision,
    GuardRequest,
    SourceType,
    ToolCall,
)

BASE_TIME = datetime(2026, 10, 29, 10, 15, tzinfo=timezone.utc)


def make_record(**overrides) -> AuditRecord:
    data = dict(
        session_id="s1",
        request_id="r1",
        user_request="আমার inbox-এর সারাংশ দাও",
        tool_name="send_money",
        arguments={"to": "01000000666", "amount": 5000, "meta": {"note": "ভাড়া"}},
        tainted=True,
        decision=Decision.BLOCK,
        risk_score=0.95,
        reason_en="Blocked. The transfer was triggered by untrusted content.",
        reason_bn="আটকানো হয়েছে। টাকা পাঠানোর নির্দেশ অবিশ্বস্ত কনটেন্ট থেকে এসেছে।",
        checks=[
            CheckResult(check=CheckName.TAINT, risk_score=0.9, flagged=True, details={"arguments": {"to": {"status": "tool_data"}}}),
            CheckResult(check=CheckName.INTENT, risk_score=0.0, skipped=True),
        ],
        total_latency_ms=12.5,
        timestamp=BASE_TIME,
    )
    data.update(overrides)
    return AuditRecord(**data)


@pytest.fixture
def log():
    with AuditLog() as audit:
        yield audit


def test_write_then_recent_roundtrip(log):
    record = make_record()
    log.write(record)
    [back] = log.recent()
    assert back.id == record.id
    assert back.arguments == record.arguments
    assert back.checks == record.checks
    assert back.decision == Decision.BLOCK
    assert back.tainted is True
    assert back.timestamp == record.timestamp


def test_bangla_reason_survives(log):
    log.write(make_record())
    assert log.recent()[0].reason_bn == "আটকানো হয়েছে। টাকা পাঠানোর নির্দেশ অবিশ্বস্ত কনটেন্ট থেকে এসেছে।"


def test_newest_first_and_limit(log):
    for minutes in (0, 2, 1):
        log.write(make_record(request_id=f"r{minutes}", timestamp=BASE_TIME + timedelta(minutes=minutes)))
    assert [r.request_id for r in log.recent()] == ["r2", "r1", "r0"]
    assert [r.request_id for r in log.recent(limit=2)] == ["r2", "r1"]


def test_same_timestamp_keeps_insert_order(log):
    for i in range(3):
        log.write(make_record(request_id=f"r{i}"))
    assert [r.request_id for r in log.recent()] == ["r2", "r1", "r0"]


def test_filter_by_session(log):
    log.write(make_record(session_id="alice"))
    log.write(make_record(session_id="bob"))
    log.write(make_record(session_id="alice"))
    records = log.recent(session_id="alice")
    assert len(records) == 2
    assert all(r.session_id == "alice" for r in records)


def test_sql_injection_is_stored_as_text(log):
    evil = "'); DROP TABLE audit; --"
    log.write(make_record(user_request=evil, session_id=evil))
    log.write(make_record())
    assert log.recent(session_id=evil)[0].user_request == evil
    assert len(log.recent()) == 2  # table still exists


def test_file_db_persists(tmp_path):
    path = tmp_path / "data" / "audit.db"
    with AuditLog(path) as first:
        first.write(make_record())
    with AuditLog(path) as second:
        assert len(second.recent()) == 1


def test_engine_writes_one_record():
    audit = AuditLog()
    engine = Engine(policy=PolicyEngine.from_yaml(), taint=TaintChecker(), audit=audit)
    request = GuardRequest(
        user_request="01711111111 নম্বরে 500 টাকা পাঠাও",
        tool_call=ToolCall(tool_name="send_money", arguments={"to": "01711111111", "amount": 500}),
        context=[ContextItem(content="01711111111 নম্বরে 500 টাকা পাঠাও", source=SourceType.USER)],
    )
    verdict = engine.check(request)
    [record] = audit.recent()
    assert record.request_id == request.id
    assert record.decision == verdict.decision
    audit.close()


def test_stats(log):
    llm_check = CheckResult(check=CheckName.INTENT, risk_score=0.05)
    log.write(make_record(decision=Decision.ALLOW, total_latency_ms=10, checks=[llm_check]))
    log.write(make_record(decision=Decision.ALLOW, total_latency_ms=20))
    log.write(make_record(decision=Decision.ASK_HUMAN, total_latency_ms=30, checks=[llm_check]))
    log.write(make_record(decision=Decision.BLOCK, total_latency_ms=40))
    stats = log.stats()
    assert stats["total"] == 4
    assert (stats["allow"], stats["ask_human"], stats["block"]) == (2, 1, 1)
    assert stats["llm_calls"] == 2
    assert stats["median_latency_ms"] == 25


def test_stats_empty(log):
    assert log.stats() == {"total": 0, "allow": 0, "ask_human": 0, "block": 0, "llm_calls": 0, "median_latency_ms": None}
