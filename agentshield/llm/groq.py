"""Groq provider (OpenAI-compatible REST API, free tier)."""

import httpx

from agentshield.llm.base import LLMError, LLMProvider, Message, message_text, require_key

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """Calls Groq's chat completions endpoint."""

    name = "groq"

    def __init__(self, model: str, api_key: str, client: httpx.Client | None = None) -> None:
        super().__init__(model)
        self.api_key = require_key(api_key, "GROQ_API_KEY")
        self.client = client or httpx.Client(timeout=30.0)

    def generate(self, messages: list[Message]) -> str:
        response = self.client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=build_groq_body(self.model, messages),
        )
        if response.status_code != 200:
            raise LLMError(f"Groq error {response.status_code}: {response.text[:300]}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Groq response: {response.text[:300]}") from exc


def build_groq_body(model: str, messages: list[Message]) -> dict:
    """Convert our messages into the OpenAI chat format.

    Tool results become "user" messages, because the "tool" role in this
    API requires native tool-calling IDs that we do not use.
    """
    chat = [
        {"role": "user" if m.role == "tool" else m.role, "content": message_text(m)}
        for m in messages
    ]
    return {"model": model, "messages": chat, "temperature": 0}
