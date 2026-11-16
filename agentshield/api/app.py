"""HTTP gateway: the same AgentShield checks as a web service, for agents written in any
language or framework.

    uvicorn agentshield.api.app:create_app --factory --port 8000
    # then open http://localhost:8000/docs for the interactive API page

Endpoints:
    POST /v1/check   GuardRequest -> Verdict   (ask before every tool call)
    GET  /v1/audit   recent decisions          (?limit=50&session_id=...)
    GET  /v1/stats   decision counts, LLM calls, median latency
    GET  /health     liveness

If AGENTSHIELD_API_KEY is set in .env, every /v1 request must send it in the
X-API-Key header. Set it whenever the gateway is reachable from other machines.
"""

from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from agentshield.audit.log import AuditLog
from agentshield.config import get_settings
from agentshield.core.engine import Engine, build_default_engine
from agentshield.core.models import AuditRecord, GuardRequest, Verdict


def create_app(engine: Engine | None = None, audit: AuditLog | None = None, api_key: str | None = None) -> FastAPI:
    """Build the gateway. Defaults: engine from .env, audit log at AUDIT_DB_PATH."""
    if audit is None:
        audit = AuditLog(get_settings().audit_db_path)
    if engine is None:
        engine = build_default_engine(audit=audit)
    if api_key is None:
        api_key = os.getenv("AGENTSHIELD_API_KEY", "")

    def require_key(x_api_key: str = Header(default="")) -> None:
        # compare_digest: no timing hints about how much of the key was right
        if api_key and not hmac.compare_digest(x_api_key, api_key):
            raise HTTPException(status_code=401, detail="missing or wrong X-API-Key")

    app = FastAPI(
        title="AgentShield gateway",
        description="Checks an AI agent's tool call before it runs: ALLOW / ASK_HUMAN / BLOCK with a reason in English and Bangla.",
        version="0.1.0",
    )
    guarded = [Depends(require_key)]

    # HEAD too: uptime monitors (e.g. UptimeRobot) check with HEAD and report 405 otherwise
    @app.api_route("/health", methods=["GET", "HEAD"])
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/v1/check", response_model=Verdict, dependencies=guarded)
    def check(request: GuardRequest) -> Verdict:
        """Judge one tool call. Send it BEFORE the tool runs, with everything the agent has read so far."""
        return engine.check(request)

    @app.get("/v1/audit", response_model=list[AuditRecord], dependencies=guarded)
    def recent(limit: int = Query(50, ge=1, le=500), session_id: str | None = None) -> list[AuditRecord]:
        return audit.recent(limit=limit, session_id=session_id)

    @app.get("/v1/stats", dependencies=guarded)
    def stats(session_id: str | None = None) -> dict:
        return audit.stats(session_id=session_id)

    return app
