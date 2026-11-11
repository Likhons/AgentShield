"""Settings loaded from the .env file (or real environment variables)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """All configuration values AgentShield reads from the environment."""

    llm_provider: str
    llm_model: str
    judge_model: str  # model for AgentShield's intent judge; empty = same as llm_model
    gemini_api_key: str
    groq_api_key: str
    audit_db_path: str
    detector: str  # injection classifier: "heuristic" (default) or "model" (Phase 4 XLM-R in models/)


def get_settings() -> Settings:
    """Read .env (if present) and return the current settings.

    Defaults are safe: with no .env at all, everything runs on the mock LLM.
    """
    load_dotenv()
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        llm_model=os.getenv("LLM_MODEL", ""),
        judge_model=os.getenv("JUDGE_MODEL", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        audit_db_path=os.getenv("AUDIT_DB_PATH", "agentshield_audit.db"),
        detector=os.getenv("AGENTSHIELD_DETECTOR", "heuristic"),
    )
