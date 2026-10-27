"""Save and load scenario runs, so a real-LLM demo can be replayed instantly on stage
(no internet, no rate limits). A replay is clearly labeled as a recording in the dashboard.

    python -m demo_agent.run --all --compare --provider groq --record    # record once
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agentshield.core.models import ToolCall, Verdict
from demo_agent.agent import AgentRun, Step
from demo_agent.scenarios import Outcome
from demo_agent.tools import Transaction

RECORDINGS_DIR = Path(__file__).resolve().parent / "recordings"


def recording_path(name: str, shielded: bool, provider: str, folder: Path = RECORDINGS_DIR) -> Path:
    return folder / provider / f"{name}_{'with' if shielded else 'without'}.json"


def save_result(result, provider: str, folder: Path = RECORDINGS_DIR) -> Path:
    """Write one ScenarioResult as JSON and return the file path."""
    data = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "name": result.name,
        "shielded": result.shielded,
        "task": result.run.task,
        "final_answer": result.run.final_answer,
        "steps": [{"number": s.number, "tool": s.tool, "args": s.args, "result": s.result} for s in result.run.steps],
        "step_verdicts": [v.model_dump(mode="json") if v else None for v in result.step_verdicts],
        "history": [[c.model_dump(mode="json"), v.model_dump(mode="json")] for c, v in result.history],
        "unauthorized": [{"txn_id": t.txn_id, "to": t.to, "amount": t.amount} for t in result.outcome.unauthorized],
        "start_balance": result.start_balance,
        "end_balance": result.end_balance,
    }
    path = recording_path(result.name, result.shielded, provider, folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def load_result(name: str, shielded: bool, provider: str, folder: Path = RECORDINGS_DIR):
    """Rebuild a ScenarioResult from a recording, plus the time it was recorded. None if missing."""
    from demo_agent.run import ScenarioResult  # local import: run.py imports this module

    path = recording_path(name, shielded, provider, folder)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    run = AgentRun(task=data["task"], final_answer=data["final_answer"],
                   steps=[Step(**s) for s in data["steps"]])
    result = ScenarioResult(
        name=data["name"],
        run=run,
        outcome=Outcome(unauthorized=[Transaction(**t) for t in data["unauthorized"]]),
        start_balance=data["start_balance"],
        end_balance=data["end_balance"],
        shielded=data["shielded"],
        history=[(ToolCall.model_validate(c), Verdict.model_validate(v)) for c, v in data["history"]],
        step_verdicts=[Verdict.model_validate(v) if v else None for v in data["step_verdicts"]],
    )
    return result, data["recorded_utc"]


def available(provider: str, folder: Path = RECORDINGS_DIR) -> set[str]:
    """Scenario names that have both a 'without' and a 'with' recording."""
    base = folder / provider
    if not base.exists():
        return set()
    names = {p.stem.rsplit("_", 1)[0] for p in base.glob("*.json")}
    return {n for n in names if recording_path(n, False, provider, folder).exists()
            and recording_path(n, True, provider, folder).exists()}
