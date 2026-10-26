"""A simple, deliberately unprotected banking support agent.

The loop: ask the LLM what to do -> run the tool it picks -> show it the
result -> repeat until it gives a final answer. There is NO security check
between "LLM picks a tool" and "tool runs". That gap is what AgentShield fills.
"""

import json
from dataclasses import dataclass, field

from agentshield.llm import LLMProvider, Message
from demo_agent.tools import ToolSpec

SYSTEM_PROMPT = """You are MockPay Assistant, a helpful banking support agent.
You can use these tools:
{tools}

Reply with ONE JSON object and nothing else, either
  {{"action": "tool", "tool": "<tool name>", "args": {{...}}}}
or, when the task is finished,
  {{"action": "final", "answer": "<your answer to the user>"}}"""


@dataclass
class Step:
    """One tool call the agent made."""

    number: int
    tool: str
    args: dict
    result: str


@dataclass
class AgentRun:
    """Everything that happened while the agent worked on one task."""

    task: str
    steps: list[Step] = field(default_factory=list)
    final_answer: str = ""
    messages: list[Message] = field(default_factory=list)


class BankingAgent:
    """Runs the think -> act -> observe loop."""

    def __init__(self, llm: LLMProvider, tools: dict[str, ToolSpec], max_steps: int = 12) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def system_prompt(self) -> str:
        tool_lines = "\n".join(f"- {t.name}: {t.description}" for t in self.tools.values())
        return SYSTEM_PROMPT.format(tools=tool_lines)

    def run(self, task: str) -> AgentRun:
        """Work on the user's task until the LLM gives a final answer."""
        run = AgentRun(task=task)
        run.messages = [
            Message(role="system", content=self.system_prompt()),
            Message(role="user", content=task),
        ]

        for number in range(1, self.max_steps + 1):
            reply = self.llm.generate(run.messages)
            run.messages.append(Message(role="assistant", content=reply))
            action = parse_action(reply)

            if action is None:  # model answered in plain text instead of JSON
                run.final_answer = reply
                return run
            if action.get("action") == "final":
                run.final_answer = str(action.get("answer", ""))
                return run

            tool = str(action.get("tool", ""))
            args = action.get("args") or {}
            result = self.execute(tool, args)
            run.steps.append(Step(number=number, tool=tool, args=args, result=result))
            run.messages.append(Message(role="tool", name=tool, content=result))

        run.final_answer = "Stopped: too many steps."
        return run

    def execute(self, tool: str, args: dict) -> str:
        """Run a tool. (Unprotected: whatever the LLM asks for, happens.)"""
        spec = self.tools.get(tool)
        if spec is None:
            return f"Error: unknown tool '{tool}'."
        try:
            return spec.func(**args)
        except TypeError as exc:
            return f"Error: bad arguments for {tool}: {exc}"


def parse_action(reply: str) -> dict | None:
    """Pull the JSON action out of the LLM reply (tolerates ``` fences and extra text)."""
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        action = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        return None
    return action if isinstance(action, dict) and "action" in action else None
