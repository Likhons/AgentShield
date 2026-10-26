"""Google Gemini provider (REST API, free tier)."""

import httpx

from agentshield.llm.base import LLMError, LLMProvider, Message, message_text, require_key

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider(LLMProvider):
    """Calls the Gemini generateContent endpoint."""

    name = "gemini"

    def __init__(self, model: str, api_key: str, client: httpx.Client | None = None) -> None:
        super().__init__(model)
        self.api_key = require_key(api_key, "GEMINI_API_KEY")
        self.client = client or httpx.Client(timeout=30.0)

    def generate(self, messages: list[Message]) -> str:
        response = self.client.post(
            GEMINI_URL.format(model=self.model),
            headers={"x-goog-api-key": self.api_key},
            json=build_gemini_body(messages),
        )
        if response.status_code != 200:
            raise LLMError(f"Gemini error {response.status_code}: {response.text[:300]}")
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Gemini response: {response.text[:300]}") from exc


def build_gemini_body(messages: list[Message]) -> dict:
    """Convert our messages into Gemini's request format.

    Gemini has only "user" and "model" roles, and system text goes in a
    separate field. Consecutive messages with the same role are merged.
    """
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    contents: list[dict] = []
    for m in messages:
        if m.role == "system":
            continue
        role = "model" if m.role == "assistant" else "user"
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"][0]["text"] += "\n\n" + message_text(m)
        else:
            contents.append({"role": role, "parts": [{"text": message_text(m)}]})

    body: dict = {"contents": contents, "generationConfig": {"temperature": 0}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    return body
