"""Common message type and the interface every LLM provider implements."""

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel

Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    """One message in a conversation with an LLM."""

    role: Role
    content: str
    name: str | None = None  # tool name, only used when role == "tool"


class LLMError(RuntimeError):
    """Raised when a provider is misconfigured or the API call fails."""


class LLMProvider(ABC):
    """Interface: give it a list of messages, get back the model's text reply."""

    name: str = "base"

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def generate(self, messages: list[Message]) -> str:
        """Return the model's reply to the conversation."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Same as generate(), but takes plain dicts like {"role": "user", "content": "..."}."""
        return self.generate([Message(**m) for m in messages])


def message_text(message: Message) -> str:
    """Render a message as plain text.

    Tool results are sent to real APIs as normal user-side text, because we
    use a simple JSON protocol instead of each vendor's own tool-calling format.
    """
    if message.role == "tool":
        return f"[Tool result from {message.name}]\n{message.content}"
    return message.content


def require_key(key: str, env_name: str) -> str:
    """Fail with a helpful message if an API key is missing or still a placeholder."""
    if not key or key.startswith("your-"):
        raise LLMError(f"{env_name} is missing. Put your key in the .env file.")
    return key
