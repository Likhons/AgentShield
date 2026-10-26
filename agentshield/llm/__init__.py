"""LLM provider abstraction: mock (offline), gemini and groq.

Usage:
    from agentshield.llm import get_provider
    llm = get_provider()          # reads LLM_PROVIDER / LLM_MODEL from .env
    reply = llm.generate(messages)
"""

from agentshield.config import get_settings
from agentshield.llm.base import LLMError, LLMProvider, Message
from agentshield.llm.gemini import GeminiProvider
from agentshield.llm.groq import GroqProvider
from agentshield.llm.mock import MockProvider

__all__ = ["LLMError", "LLMProvider", "Message", "get_provider"]


def get_provider(provider: str | None = None, model: str | None = None) -> LLMProvider:
    """Create the LLM provider named in the arguments or in .env."""
    settings = get_settings()
    provider = (provider or settings.llm_provider).lower()
    model = model or settings.llm_model

    if provider == "mock":
        return MockProvider()
    if not model or model.startswith("your-"):
        raise LLMError("Set LLM_MODEL in your .env file (see .env.example for where to find names).")
    if provider == "gemini":
        return GeminiProvider(model, settings.gemini_api_key)
    if provider == "groq":
        return GroqProvider(model, settings.groq_api_key)
    raise LLMError(f"Unknown LLM_PROVIDER '{provider}'. Use mock, gemini or groq.")
