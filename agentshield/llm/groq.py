"""Groq provider (OpenAI-compatible REST API, free tier)."""

import re
import time
from collections.abc import Callable

import httpx

from agentshield.llm.base import LLMError, LLMProvider, Message, message_text, require_key

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_RETRIES = 5


class GroqProvider(LLMProvider):
    """Calls Groq's chat completions endpoint.

    The free tier has small per-minute limits. On HTTP 429 (rate limit) we
    wait as long as Groq asks and try again; network timeouts are retried
    too. At most MAX_RETRIES attempts.
    """

    name = "groq"

    def __init__(
        self,
        model: str,
        api_key: str,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(model)
        self.api_key = require_key(api_key, "GROQ_API_KEY")
        self.client = client or httpx.Client(timeout=30.0)
        self.sleep = sleep  # replaceable in tests, so they don't really wait

    def generate(self, messages: list[Message]) -> str:
        response = None
        for _ in range(MAX_RETRIES):
            try:
                response = self.client.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=build_groq_body(self.model, messages),
                )
            except httpx.TransportError:  # timeout or network hiccup
                self.sleep(2.0)
                continue
            if response.status_code != 429:
                break
            self.sleep(retry_delay(response))
        if response is None:
            raise LLMError("Groq did not respond (network error or timeout). Check your internet.")
        if response.status_code != 200:
            raise LLMError(f"Groq error {response.status_code}: {response.text[:300]}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Groq response: {response.text[:300]}") from exc


def retry_delay(response: httpx.Response) -> float:
    """Seconds to wait after a 429: from the retry-after header or the
    'try again in 2.52s' text in the error message, plus a small margin."""
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header) + 0.5
        except ValueError:
            pass
    match = re.search(r"try again in ([\d.]+)s", response.text)
    return float(match.group(1)) + 0.5 if match else 5.0


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
