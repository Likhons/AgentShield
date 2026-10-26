"""Audit log: every Verdict, stored in SQLite for the dashboard and the benchmark.

Usage:
    audit = AuditLog(get_settings().audit_db_path)   # or AuditLog() for an in-memory DB
    engine = Engine(..., audit=audit)

Security: values are always passed with "?" placeholders, never formatted into
SQL. user_request and arguments can contain attacker text.
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import threading
from datetime import timezone
from pathlib import Path
from typing import Any

from agentshield.core.models import AuditRecord, CheckName, Decision

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id               TEXT PRIMARY KEY,
    timestamp        TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    request_id       TEXT NOT NULL,
    user_request     TEXT NOT NULL,
    tool_name        TEXT NOT NULL,
    arguments        TEXT NOT NULL,   -- JSON
    tainted          INTEGER NOT NULL,
    decision         TEXT NOT NULL,
    risk_score       REAL NOT NULL,
    reason_en        TEXT NOT NULL,
    reason_bn        TEXT NOT NULL,
    checks           TEXT NOT NULL,   -- JSON
    total_latency_ms REAL NOT NULL,
    llm_called       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_session ON audit (session_id);
"""

_COLUMNS = (
    "id", "timestamp", "session_id", "request_id", "user_request", "tool_name", "arguments",
    "tainted", "decision", "risk_score", "reason_en", "reason_bn", "checks", "total_latency_ms",
    "llm_called",
)
_INSERT = f"INSERT INTO audit ({', '.join(_COLUMNS)}) VALUES ({', '.join('?' for _ in _COLUMNS)})"


def _llm_called(record: AuditRecord) -> bool:
    return any(c.check == CheckName.INTENT and not c.skipped for c in record.checks)


class AuditLog:
    """SQLite-backed store of AuditRecords."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        path = str(path)
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: the Streamlit dashboard reads from another thread.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    # -- writing -----------------------------------------------------------

    def write(self, record: AuditRecord) -> None:
        data = record.model_dump(mode="json")
        # Fixed-width UTC ISO text, so sorting the text also sorts by time.
        timestamp = record.timestamp.astimezone(timezone.utc).isoformat(timespec="microseconds")
        values = (
            data["id"],
            timestamp,
            data["session_id"],
            data["request_id"],
            data["user_request"],
            data["tool_name"],
            json.dumps(data["arguments"], ensure_ascii=False),
            int(data["tainted"]),
            data["decision"],
            data["risk_score"],
            data["reason_en"],
            data["reason_bn"],
            json.dumps(data["checks"], ensure_ascii=False),
            data["total_latency_ms"],
            int(_llm_called(record)),
        )
        with self._lock:
            self._conn.execute(_INSERT, values)
            self._conn.commit()

    # -- reading -----------------------------------------------------------

    def recent(self, limit: int = 50, session_id: str | None = None) -> list[AuditRecord]:
        """Newest records first."""
        sql = "SELECT * FROM audit"
        params: list[Any] = []
        if session_id is not None:
            sql += " WHERE session_id = ?"
            params.append(session_id)
        sql += " ORDER BY timestamp DESC, rowid DESC LIMIT ?"
        params.append(int(limit))
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._to_record(row) for row in rows]

    def stats(self, session_id: str | None = None) -> dict[str, Any]:
        """KPIs for the dashboard: decision counts, LLM calls, median latency."""
        sql = "SELECT decision, llm_called, total_latency_ms FROM audit"
        params: list[Any] = []
        if session_id is not None:
            sql += " WHERE session_id = ?"
            params.append(session_id)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()

        counts = {d.value: 0 for d in Decision}
        for row in rows:
            counts[row["decision"]] = counts.get(row["decision"], 0) + 1
        latencies = [row["total_latency_ms"] for row in rows]
        return {
            "total": len(rows),
            **counts,
            "llm_calls": sum(row["llm_called"] for row in rows),
            "median_latency_ms": statistics.median(latencies) if latencies else None,
        }

    @staticmethod
    def _to_record(row: sqlite3.Row) -> AuditRecord:
        data = {key: row[key] for key in row.keys() if key != "llm_called"}
        data["arguments"] = json.loads(data["arguments"])
        data["checks"] = json.loads(data["checks"])
        data["tainted"] = bool(data["tainted"])
        return AuditRecord.model_validate(data)

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> AuditLog:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
