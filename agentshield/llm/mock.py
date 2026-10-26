"""Deterministic mock LLM: works offline, needs no API key.

As an agent it imitates a *naive* tool-using model:
  1. It plans tool calls from simple keywords in the user's task.
  2. It OBEYS any money-transfer instruction it finds inside tool output.

Point 2 is the vulnerability we want to demonstrate. Real LLMs are often
tricked the same way, but not every time; the mock gives a repeatable
worst case for demos and tests. Results on real LLMs are measured separately.

As an intent judge (prompt contains "PROPOSED TOOL CALL:") it answers with a
simple keyword rule, so AgentShield's intent check also works offline.
"""

import json
import re
import unicodedata
from dataclasses import dataclass

from agentshield.llm.base import LLMProvider, Message

BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def normalize(text: str) -> str:
    """Unicode-normalize text and turn Bangla digits into ASCII digits."""
    return unicodedata.normalize("NFC", text).translate(BANGLA_DIGITS)


PHONE_RE = re.compile(r"\b0\d{10}\b")
AMOUNT_RE = re.compile(r"(\d[\d,]*)\s*(?:taka|tk|bdt|টাকা)", re.IGNORECASE)
SEND_VERB_RE = re.compile(
    normalize(
        r"\b(?:send|pay|transfer|pathao|pathan|pathiye dao|pathiye din|pathiye diben)\b"
        r"|পাঠাও|পাঠান|পাঠিয়ে দাও|পাঠিয়ে দিন|পাঠিয়ে দিবেন|ট্রান্সফার কর"
    ),
    re.IGNORECASE,
)

INBOX_WORDS = ("inbox", "email", "mail", "ইমেইল", "ইনবক্স")
BALANCE_WORDS = ("balance", "ব্যালেন্স")
SEARCH_WORDS = ("search", "web", "খুঁজ")
FILE_WORDS = ("file", "ফাইল")


@dataclass
class MoneyOrder:
    """A 'send X taka to number Y' instruction found in some text."""

    to: str
    amount: int


def find_money_order(text: str) -> MoneyOrder | None:
    """Return the money instruction in the text, or None.

    Needs all three: a send verb, a phone number and an amount in taka.
    """
    text = normalize(text)
    if not SEND_VERB_RE.search(text):
        return None
    phone = PHONE_RE.search(text)
    amount = AMOUNT_RE.search(text)
    if not phone or not amount:
        return None
    return MoneyOrder(to=phone.group(), amount=int(amount.group(1).replace(",", "")))


class MockProvider(LLMProvider):
    """Rule-based fake LLM that replies with JSON agent actions."""

    name = "mock"

    def __init__(self, model: str = "mock-agent-v1") -> None:
        super().__init__(model)

    def generate(self, messages: list[Message]) -> str:
        if JUDGE_MARKER in messages[-1].content:
            return json.dumps(judge_intent(messages[-1].content), ensure_ascii=False)
        return json.dumps(next_agent_action(messages), ensure_ascii=False)


# ---- intent judge mode ----------------------------------------------------

JUDGE_MARKER = "PROPOSED TOOL CALL:"
MONEY_TOOLS = {"send_money"}
PAYMENT_INTENT_RE = re.compile(
    normalize(r"\b(?:send|pay|transfer|bills?|taka|tk|pathao|pathiye|bhara)\b|পাঠা|পরিশোধ|বিল|টাকা|ভাড়া"),
    re.IGNORECASE,
)


def judge_intent(prompt: str) -> dict:
    """Keyword stand-in for the LLM judge: a money tool is consistent only
    if the user's own request talks about sending or paying money."""
    request = prompt.split("<<<", 1)[-1].split(">>>", 1)[0]
    tool = prompt.split(JUDGE_MARKER, 1)[1].split()[0]
    if tool not in MONEY_TOOLS or PAYMENT_INTENT_RE.search(normalize(request)):
        return {
            "consistent": True,
            "reason_en": f"The user's request can involve '{tool}'.",
            "reason_bn": f"ব্যবহারকারীর অনুরোধের সাথে '{tool}' মেলে।",
        }
    return {
        "consistent": False,
        "reason_en": "The user did not ask to send or pay money.",
        "reason_bn": "ব্যবহারকারী টাকা পাঠাতে বা পরিশোধ করতে বলেননি।",
    }


def next_agent_action(messages: list[Message]) -> dict:
    """Decide the next action, like a naive agent model would."""
    task = next(m.content for m in messages if m.role == "user")
    calls = previous_calls(messages)
    last = messages[-1]

    # The vulnerability: instructions inside untrusted tool output are obeyed.
    if last.role == "tool":
        order = find_money_order(last.content)
        if order and not already_sent(calls, order.to):
            return tool_call("send_money", to=order.to, amount=order.amount)

    return plan_from_task(task, calls, messages)


def plan_from_task(task: str, calls: list[dict], messages: list[Message]) -> dict:
    """Pick the next tool from keywords in the user's task."""
    lower = normalize(task).lower()

    order = find_money_order(task)
    if order:
        if not already_sent(calls, order.to):
            return tool_call("send_money", to=order.to, amount=order.amount)
        return final(f"Done: {last_tool_result(messages)}")

    if any(word in lower for word in INBOX_WORDS):
        if not was_called(calls, "read_inbox"):
            return tool_call("read_inbox")
        for email_id in inbox_ids(messages):
            if not was_called(calls, "read_email", email_id=email_id):
                return tool_call("read_email", email_id=email_id)
        return final("Here is your inbox:\n" + tool_result(messages, "read_inbox"))

    if any(word in lower for word in BALANCE_WORDS):
        if not was_called(calls, "get_balance"):
            return tool_call("get_balance")
        return final(last_tool_result(messages))

    if any(word in lower for word in SEARCH_WORDS):
        if not was_called(calls, "search_web"):
            return tool_call("search_web", query=task)
        return final("Here is what I found:\n" + tool_result(messages, "search_web")[:300])

    if any(word in lower for word in FILE_WORDS):
        filename = re.search(r"[\w-]+\.\w+", task)
        if filename and not was_called(calls, "read_file"):
            return tool_call("read_file", filename=filename.group())
        return final("The file says:\n" + tool_result(messages, "read_file")[:300])

    return final("Sorry, I can only help with balance, money transfers, email, web search and files.")


# ---- small helpers -------------------------------------------------------


def tool_call(tool: str, **args) -> dict:
    return {"action": "tool", "tool": tool, "args": args}


def final(answer: str) -> dict:
    return {"action": "final", "answer": answer}


def previous_calls(messages: list[Message]) -> list[dict]:
    """Tool calls the agent already made (parsed from its JSON replies)."""
    calls = []
    for m in messages:
        if m.role != "assistant":
            continue
        try:
            action = json.loads(m.content)
        except json.JSONDecodeError:
            continue
        if isinstance(action, dict) and action.get("action") == "tool":
            calls.append(action)
    return calls


def was_called(calls: list[dict], tool: str, **args) -> bool:
    return any(
        c["tool"] == tool and all(c.get("args", {}).get(k) == v for k, v in args.items())
        for c in calls
    )


def already_sent(calls: list[dict], to: str) -> bool:
    return was_called(calls, "send_money", to=to)


def tool_result(messages: list[Message], tool: str) -> str:
    """Latest output of the given tool, or an empty string."""
    for m in reversed(messages):
        if m.role == "tool" and m.name == tool:
            return m.content
    return ""


def last_tool_result(messages: list[Message]) -> str:
    for m in reversed(messages):
        if m.role == "tool":
            return m.content
    return ""


def inbox_ids(messages: list[Message]) -> list[str]:
    """Email IDs listed by read_inbox (lines look like 'e1 | From: ...')."""
    return re.findall(r"^(e\d+) \|", tool_result(messages, "read_inbox"), re.MULTILINE)
