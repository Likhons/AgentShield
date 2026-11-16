"""Dashboard API: everything the React frontend shows, from the same sources as the Streamlit dashboard.

    uvicorn webapi.app:build_app --factory --reload --port 8000      # docs at http://localhost:8000/docs

It mounts the existing AgentShield gateway (/v1/check, /v1/audit, /v1/stats, /health) unchanged and adds
read-only /api/* endpoints plus the demo scenario runner. Numbers come only from benchmark/results/,
the audit database and datasets/, exactly like dashboard/app.py.

This package lives outside agentshield/ on purpose: it imports demo_agent and benchmark, which the
library must not depend on.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import threading
import time
import tomllib
from collections import deque
from datetime import timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from agentshield.api.app import create_app
from agentshield.audit.log import AuditLog
from agentshield.checks.policy import DEFAULT_POLICY_PATH, PolicyRule
from agentshield.config import get_settings
from agentshield.core.models import AuditRecord, CheckName, DecisionThresholds
from agentshield.llm import LLMError
from benchmark.dataset import load_dataset, summarize
from benchmark.report import agent_rows, detection_rows, latest_where, outcome_rows
from demo_agent.recording import load_result, recording_path
from demo_agent.run import ScenarioResult, run_scenario
from demo_agent.scenarios import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT / "datasets"
DOCS = {"results": ROOT / "docs" / "results.md", "datasets-readme": DATASETS_DIR / "README.md"}
OUTCOME_ORDER = ["paid", "never tried", "blocked", "not attempted", "held for approval", "attacker paid"]
# Team-written attack texts: counts are shown, the texts only when SHOW_ATTACK_TEXTS is set.
# docs/ethics_impact.md: the attack set is shared with researchers on request, not published.
PRIVATE_TEXT_FILES = {"attacks.jsonl"}
HIDDEN_NOTE = "Attack texts are not published; they are shared with researchers on request (docs/ethics_impact.md)."


def attack_texts_public() -> bool:
    return os.getenv("SHOW_ATTACK_TEXTS", "").strip().lower() in {"1", "true", "yes"}


def texts_public(file_name: str) -> bool:
    return file_name not in PRIVATE_TEXT_FILES or attack_texts_public()
_RATE = re.compile(r"(\d+)% \((\d+)/(\d+), 95% CI (\d+)%-(\d+)%\)")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def rate_cell(text: str) -> dict[str, Any]:
    """'20% (4/20, 95% CI 8%-42%)' -> numbers the frontend can draw; keeps the original text."""
    m = _RATE.fullmatch(text.strip())
    if not m:
        return {"text": text, "hits": None, "total": None, "pct": None, "ci": None}
    pct, hits, total, low, high = (int(g) for g in m.groups())
    return {"text": text, "hits": hits, "total": total, "pct": pct, "ci": [low, high]}


def lang_label(code: str) -> str:
    return code.upper() if len(code) <= 2 else code.capitalize()


def taka(amount: int) -> str:
    return f"৳ {amount:,}"


def summary_banner(name: str, stolen_without: int, stolen_with: int) -> dict[str, str] | None:
    """Same wording as dashboard/ui.py summary_banner (kept in sync by tests)."""
    saved = stolen_without - stolen_with
    if saved > 0:
        return {"tone": "saved", "text": f"🛡️ AgentShield saved {taka(saved)} · AgentShield {taka(saved)} বাঁচিয়েছে"}
    if stolen_without == 0 and name.startswith("attack"):
        return {"tone": "neutral", "text": "ℹ️ The agent ignored this attack on its own this time, so AgentShield had "
                "nothing to stop · এবার AI নিজেই attack উপেক্ষা করেছে, তাই AgentShield-এর আটকানোর কিছু ছিল না"}
    if stolen_without == 0:
        return {"tone": "saved", "text": "✅ Normal task: AgentShield let it run · সাধারণ কাজ, AgentShield বাধা দেয়নি"}
    return None


def heuristic_run(data: dict) -> bool:
    return data.get("detector", "heuristic") == "heuristic"


def dataset_label(dataset: Any) -> str:
    if not isinstance(dataset, dict):
        return str(dataset)
    parts = []
    for lang, counts in sorted(dataset.items()):
        if isinstance(counts, dict):
            parts.append(f"{lang_label(lang)} {counts.get('attack', 0)} attack / {counts.get('benign', 0)} benign")
        else:
            parts.append(f"{lang_label(lang)} {counts}")
    return " · ".join(parts)


def serialize_result(result: ScenarioResult) -> dict[str, Any]:
    steps = []
    for step, verdict in zip(result.run.steps, result.step_verdicts):
        steps.append({
            "number": step.number,
            "tool": step.tool,
            "args": step.args,
            "result": step.result[:600] + ("…" if len(step.result) > 600 else ""),
            "stopped_by_shield": step.result.startswith("[AgentShield]"),
            "verdict": verdict.model_dump(mode="json") if verdict else None,
        })
    return {
        "task": result.run.task,
        "shielded": result.shielded,
        "start_balance": result.start_balance,
        "end_balance": result.end_balance,
        "stolen": result.outcome.stolen,
        "unauthorized": [{"to": t.to, "amount": t.amount} for t in result.outcome.unauthorized],
        "stopped": sum(1 for _, v in result.history if v.decision.value != "allow"),
        "steps": steps,
        "final_answer": result.run.final_answer,
    }


def audit_csv(records: list[AuditRecord]) -> bytes:
    """Same columns as the Streamlit export; UTF-8 with BOM so Excel keeps Bangla."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "timestamp_utc", "session_id", "request_id", "tool", "decision", "risk_score", "tainted",
                     "latency_ms", "arguments", "user_request", "reason_bn", "reason_en"])
    for r in records:
        writer.writerow([r.id, r.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), r.session_id,
                         r.request_id, r.tool_name, r.decision.value, round(r.risk_score, 4), r.tainted,
                         round(r.total_latency_ms, 2), json.dumps(r.arguments, ensure_ascii=False), r.user_request,
                         r.reason_bn, r.reason_en])
    return buf.getvalue().encode("utf-8-sig")


def load_dataset_files() -> list[dict[str, Any]]:
    files = []
    for path in sorted(DATASETS_DIR.glob("*.jsonl")):
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        reviewed = sum("reviewed=yes" in (r.get("notes") or "") for r in lines)
        files.append({
            "file": path.name,
            "items": len(lines),
            "reviewed": reviewed,
            "sources": sorted({str(r.get("source", "?")) for r in lines}),
            "size_bytes": path.stat().st_size,
            "texts_public": texts_public(path.name),
        })
    return files


# ---------------------------------------------------------------------------
# request bodies
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    mode: Literal["mock", "groq", "recorded"] = "mock"
    approve: bool = False


# ---------------------------------------------------------------------------
# app
# ---------------------------------------------------------------------------
def build_app(audit: AuditLog | None = None) -> FastAPI:
    settings = get_settings()
    if audit is None:
        audit = AuditLog(settings.audit_db_path)
    app = create_app(audit=audit)  # the gateway: /v1/check, /v1/audit, /v1/stats, /health
    app.title = "AgentShield dashboard API"

    origins = [o.strip() for o in os.getenv("WEB_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

    # Live (Groq) runs spend the account's free-tier quota and hit per-minute limits, so a public server
    # allows one live run at a time and at most LIVE_RUNS_PER_HOUR per rolling hour (0 = live off).
    live_available = bool(settings.groq_api_key and settings.llm_model)
    live_per_hour = int(os.getenv("LIVE_RUNS_PER_HOUR", "20"))
    live_started: deque[float] = deque()
    live_count_lock = threading.Lock()
    live_run_lock = threading.Lock()

    def claim_live_slot() -> None:
        now = time.monotonic()
        with live_count_lock:
            while live_started and now - live_started[0] > 3600:
                live_started.popleft()
            if len(live_started) >= live_per_hour:
                raise HTTPException(429, f"The live demo is limited to {live_per_hour} runs per hour to protect the free "
                                         "Groq quota. Try again later, or use Recorded Run (a saved real Groq run).")
            live_started.append(now)

    @lru_cache(maxsize=1)
    def version() -> str:
        try:
            return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        except (OSError, KeyError, tomllib.TOMLDecodeError):
            return "dev"

    def policy_rules() -> list[dict]:
        return yaml.safe_load(Path(DEFAULT_POLICY_PATH).read_text(encoding="utf-8")).get("rules", [])

    # -- overview ------------------------------------------------------------
    @app.get("/api/overview", tags=["dashboard"])
    def overview() -> dict[str, Any]:
        summary = summarize(load_dataset())
        attacks = {lang: c.get("attack", 0) for lang, c in summary.items()}
        real = None
        found = latest_where("agent", lambda d: d["provider"] == "groq" and heuristic_run(d))
        if found:
            name, data = found
            row = next((r for r in agent_rows(data) if r["language"] == "all"), None)
            if row:
                real = {"source": name,
                        "with": rate_cell(row["attack success WITH AgentShield"]),
                        "without": rate_cell(row["attack success WITHOUT AgentShield"])}
        return {
            "version": version(),
            "agent_llm": settings.llm_provider,
            "detector": settings.detector,
            "checks": [c.value for c in CheckName],
            "policy_rules": len(policy_rules()),
            "decisions_logged": audit.stats()["total"],
            "attack_samples": {"total": sum(attacks.values()), "by_language": attacks},
            "real_llm": real,
            "live_mode_available": live_available and live_per_hour > 0,
        }

    # -- playground ------------------------------------------------------------
    @app.get("/api/scenarios", tags=["playground"])
    def scenarios() -> list[dict[str, Any]]:
        items = load_scenarios()
        names = sorted(items, key=lambda n: (not n.startswith("attack"), n))
        return [{
            "name": n,
            "kind": "attack" if n.startswith("attack") else "benign",
            "description": items[n]["description"],
            "user_task": items[n]["user_task"],
            "has_recording": recording_path(n, True, "groq").exists() and recording_path(n, False, "groq").exists(),
        } for n in names]

    @app.post("/api/scenarios/{name}/run", tags=["playground"])
    def run(name: str, body: RunRequest) -> dict[str, Any]:
        if name not in load_scenarios():
            raise HTTPException(404, f"unknown scenario: {name}")
        recorded_utc = None
        if body.mode == "recorded":
            without, with_shield = load_result(name, False, "groq"), load_result(name, True, "groq")
            if without is None or with_shield is None:
                raise HTTPException(404, "no recording for this scenario yet")
            (without, recorded_utc), (with_shield, _) = without, with_shield
        else:
            live = body.mode == "groq"
            if live and (not live_available or live_per_hour <= 0):
                raise HTTPException(400, "Live mode is off on this server (no Groq key). Use mock or recorded.")
            if live and not live_run_lock.acquire(blocking=False):
                raise HTTPException(429, "Another live run is in progress. Try again in a minute, or use Recorded Run.")
            try:
                if live:
                    claim_live_slot()
                without = run_scenario(name, provider=body.mode, shield=False)
                with_shield = run_scenario(name, provider=body.mode, shield=True, audit=audit, approve=body.approve)
            except LLMError as exc:
                raise HTTPException(502, f"LLM error: {exc}") from exc
            finally:
                if live:
                    live_run_lock.release()
        return {
            "scenario": name,
            "mode": body.mode,
            "recorded_utc": recorded_utc,
            "banner": summary_banner(name, without.outcome.stolen, with_shield.outcome.stolen),
            "without": serialize_result(without),
            "with": serialize_result(with_shield),
        }

    # -- audit ------------------------------------------------------------------
    @app.get("/api/audit", tags=["audit"])
    def audit_query(
        decision: Literal["allow", "ask_human", "block"] | None = None,
        search: str | None = None,
        tool: str | None = None,
        tainted: bool | None = None,
        min_risk: float | None = Query(None, ge=0.0, le=1.0),
        since: str | None = Query(None, description="ISO timestamp, e.g. 2026-11-16T00:00:00+00:00"),
        limit: int = Query(8, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        records, total, counts = audit.query(decision=decision, search=search, tool_name=tool, tainted=tainted,
                                             min_risk=min_risk, since_iso=since, limit=limit, offset=offset)
        newest = audit.recent(limit=1)
        return {
            "records": [r.model_dump(mode="json") for r in records],
            "total": total,
            "counts": counts,
            "stats": audit.stats(),
            "tools": audit.distinct_tools(),
            "thresholds": DecisionThresholds().model_dump(),
            # date ranges count back from the newest event (as in Streamlit), so older demo data stays reachable
            "newest": newest[0].timestamp.isoformat() if newest else None,
        }

    @app.get("/api/audit.csv", tags=["audit"])
    def audit_export(
        decision: Literal["allow", "ask_human", "block"] | None = None,
        search: str | None = None,
        tool: str | None = None,
        tainted: bool | None = None,
        min_risk: float | None = Query(None, ge=0.0, le=1.0),
        since: str | None = None,
    ) -> Response:
        records, _, _ = audit.query(decision=decision, search=search, tool_name=tool, tainted=tainted,
                                    min_risk=min_risk, since_iso=since, limit=None)
        return Response(audit_csv(records), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="agentshield_audit.csv"'})

    @app.get("/api/audit/{record_id}", tags=["audit"])
    def audit_record(record_id: str) -> dict[str, Any]:
        record = audit.get_by_id(record_id)
        if record is None:
            raise HTTPException(404, "record not found")
        return record.model_dump(mode="json")

    # -- benchmarks ---------------------------------------------------------------
    @app.get("/api/benchmarks", tags=["benchmarks"])
    def benchmarks() -> dict[str, Any]:
        def agent_section(title: str, found) -> dict | None:
            if found is None:
                return None
            name, data = found
            totals: dict[str, int] = {}
            for r in data.get("rows", []):
                if r.get("shield") and "outcome" in r:
                    totals[str(r["outcome"])] = totals.get(str(r["outcome"]), 0) + 1
            order = [k for k in OUTCOME_ORDER if k in totals] + sorted(k for k in totals if k not in OUTCOME_ORDER)
            return {
                "kind": "agent", "title": title, "source": name,
                "provider": data.get("provider"), "note": data.get("note", ""),
                "detector": data.get("detector", "heuristic"), "runs": data.get("runs", 1),
                "rows": [{"language": r["language"], "label": lang_label(r["language"]),
                          **{k: rate_cell(v) for k, v in r.items() if k != "language"}} for r in agent_rows(data)],
                "outcomes": outcome_rows(data),
                "outcome_totals": [{"outcome": k, "count": totals[k]} for k in order],
            }

        def detection_section(title: str, note: str, found) -> dict | None:
            if found is None:
                return None
            name, data = found
            return {
                "kind": "detection", "title": title, "source": name, "note": note,
                "dataset": dataset_label(data.get("dataset", "")),
                "rows": [{"detector": r["detector"], "language": r["language"], "label": lang_label(r["language"]),
                          "attacks_flagged": rate_cell(r["attacks flagged"]),
                          "benign_flagged": rate_cell(r["benign flagged"])} for r in detection_rows(data)],
            }

        sections = [
            agent_section("Agent level, real LLM (Groq): is the money safe?",
                          latest_where("agent", lambda d: d["provider"] == "groq" and heuristic_run(d))),
            agent_section("Agent level, simulated agent",
                          latest_where("agent", lambda d: d["provider"] == "mock" and heuristic_run(d))),
            detection_section("Text level: do existing guardrails catch Bangla/Banglish attacks?",
                              "Meta Prompt Guard 2 vs AgentShield's heuristic.",
                              latest_where("detection", lambda d: not d.get("split")
                                           and any("promptguard" in k for k in d["metrics"]))),
            detection_section("Trained model (XLM-R), held-out test split",
                              "Text level only: at agent level this model still holds real bills "
                              "(docs/results.md 3e), so the heuristic stays the runtime default.",
                              latest_where("detection", lambda d: d.get("split") == "test")),
        ]
        return {"sections": [s for s in sections if s]}

    # -- policies -----------------------------------------------------------------
    @app.get("/api/policies", tags=["policies"])
    def policies() -> dict[str, Any]:
        rules = policy_rules()
        return {"file": Path(DEFAULT_POLICY_PATH).name, "rules": rules,
                "yaml": {r["id"]: yaml.safe_dump([r], allow_unicode=True, sort_keys=False) for r in rules},
                "thresholds": DecisionThresholds().model_dump()}

    @app.post("/api/policies/validate", tags=["policies"])
    def validate_policy(rule: dict[str, Any]) -> dict[str, Any]:
        """Check a rule against PolicyRule and return it as YAML. Nothing is written: default.yaml stays
        read-only at runtime (same as the Streamlit 'Add Policy' form)."""
        try:
            validated = PolicyRule.model_validate(rule)
        except ValidationError as exc:
            return {"valid": False, "error": "; ".join(f"{'.'.join(map(str, e['loc'])) or 'rule'}: {e['msg']}"
                                                         for e in exc.errors())}
        return {"valid": True, "yaml": yaml.safe_dump([validated.model_dump(mode="json", exclude_none=True)],
                                                      allow_unicode=True, sort_keys=False)}

    # -- documents shown in the UI --------------------------------------------------
    @app.get("/api/docs/{name}", tags=["docs"])
    def document(name: Literal["results", "datasets-readme"]) -> dict[str, str]:
        path = DOCS[name]
        if not path.is_file():
            raise HTTPException(404, f"{path.name} not found")
        return {"name": name, "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "markdown": path.read_text(encoding="utf-8")}

    # -- datasets -----------------------------------------------------------------
    def dataset_path(file_name: str) -> Path:
        # only plain .jsonl names inside datasets/ (no paths)
        if not re.fullmatch(r"[\w.-]+\.jsonl", file_name):
            raise HTTPException(400, "bad file name")
        path = DATASETS_DIR / file_name
        if not path.is_file():
            raise HTTPException(404, "file not found")
        return path

    @app.get("/api/datasets", tags=["datasets"])
    def datasets() -> dict[str, Any]:
        summary = summarize(load_dataset())
        return {
            "languages": [{"language": lang, "label": lang_label(lang), "attack": c.get("attack", 0),
                           "benign": c.get("benign", 0)} for lang, c in sorted(summary.items())],
            "files": load_dataset_files(),
        }

    @app.get("/api/datasets/{file_name}", tags=["datasets"])
    def dataset_preview(file_name: str, limit: int = Query(15, ge=1, le=200)) -> dict[str, Any]:
        lines = [json.loads(x) for x in dataset_path(file_name).read_text(encoding="utf-8").splitlines() if x.strip()]
        by_language: dict[str, dict[str, int]] = {}
        for r in lines:
            row = by_language.setdefault(str(r.get("language", "?")), {"attack": 0, "benign": 0, "reviewed": 0})
            label = str(r.get("label", "?"))
            row[label] = row.get(label, 0) + 1
            row["reviewed"] += "reviewed=yes" in (r.get("notes") or "")
        public = texts_public(file_name)
        records = lines[:limit] if public else [{**r, "text": None} for r in lines[:limit]]
        return {"file": file_name, "total": len(lines), "records": records,
                "texts_public": public, "note": None if public else HIDDEN_NOTE,
                "by_language": [{"language": k, "label": lang_label(k), **v} for k, v in sorted(by_language.items())]}

    @app.get("/api/datasets/{file_name}/download", tags=["datasets"])
    def dataset_download(file_name: str) -> Response:
        path = dataset_path(file_name)
        if not texts_public(path.name):
            raise HTTPException(403, HIDDEN_NOTE)
        return Response(path.read_bytes(), media_type="application/jsonl",
                        headers={"Content-Disposition": f'attachment; filename="{path.name}"'})

    return app
