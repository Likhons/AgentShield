"""The fake MockPay world and the tools the banking agent can call.

Every tool returns a string, because that string is what the LLM reads.
Each ToolSpec also records the *source label* of its output (e.g.
"tool:email"). AgentShield's taint tracking uses these labels in Phase 2.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

PHONE_RE = re.compile(r"^0\d{10}$")


@dataclass
class ToolSpec:
    """A tool the agent may call."""

    name: str
    description: str
    func: Callable[..., str]
    source: str  # where the tool's output comes from: "tool:email", "tool:web", ...


@dataclass
class Transaction:
    """One completed money transfer."""

    txn_id: str
    to: str
    amount: int


@dataclass
class MockPayWorld:
    """In-memory fake world: one MockPay wallet, an inbox, web pages and files."""

    owner: str
    account: str
    balance: int
    emails: list[dict] = field(default_factory=list)
    web_pages: list[dict] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)

    # ---- tools -----------------------------------------------------------

    def read_inbox(self) -> str:
        """List all emails: id, sender and subject."""
        if not self.emails:
            return "Inbox is empty."
        return "\n".join(f"{e['id']} | From: {e['from']} | Subject: {e['subject']}" for e in self.emails)

    def read_email(self, email_id: str) -> str:
        """Return the full text of one email."""
        for e in self.emails:
            if e["id"] == email_id:
                return f"From: {e['from']}\nSubject: {e['subject']}\n\n{e['body']}"
        return f"Error: no email with id '{email_id}'."

    def get_balance(self) -> str:
        """Return the wallet balance."""
        return f"MockPay balance for {self.owner} ({self.account}): {self.balance} BDT"

    def send_money(self, to: str, amount: int) -> str:
        """Transfer money from the user's wallet to another MockPay number."""
        to = str(to).strip()
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return f"Error: invalid amount '{amount}'."
        if not PHONE_RE.match(to):
            return f"Error: '{to}' is not a valid 11-digit MockPay number."
        if amount <= 0:
            return "Error: amount must be positive."
        if amount > self.balance:
            return f"Error: insufficient balance ({self.balance} BDT)."

        self.balance -= amount
        txn = Transaction(txn_id=f"TXN-{len(self.transactions) + 1:04d}", to=to, amount=amount)
        self.transactions.append(txn)
        return f"Sent {amount} BDT to {to}. Transaction {txn.txn_id}. New balance: {self.balance} BDT"

    def search_web(self, query: str) -> str:
        """Return the fake web page that best matches the query."""
        words = set(re.findall(r"\w+", query.lower()))

        def score(page: dict) -> int:
            return len(words & set(re.findall(r"\w+", page["title"].lower())))

        best = max(self.web_pages, key=score, default=None)
        if best is None or score(best) == 0:
            return "No results found."
        return f"{best['title']}\n{best['url']}\n\n{best['content']}"

    def read_file(self, filename: str) -> str:
        """Return the content of one of the user's files."""
        if filename not in self.files:
            return f"Error: file '{filename}' not found."
        return self.files[filename]

    # ---- registry --------------------------------------------------------

    def tool_specs(self) -> dict[str, ToolSpec]:
        """All tools, keyed by name."""
        specs = [
            ToolSpec("read_inbox", "List emails in the inbox. Args: none.", self.read_inbox, "tool:email"),
            ToolSpec("read_email", "Read one email. Args: email_id (str).", self.read_email, "tool:email"),
            ToolSpec("get_balance", "Get the wallet balance. Args: none.", self.get_balance, "tool:bank"),
            ToolSpec(
                "send_money",
                "Send money. Args: to (11-digit MockPay number, str), amount (BDT, int).",
                self.send_money,
                "tool:bank",
            ),
            ToolSpec("search_web", "Search the web. Args: query (str).", self.search_web, "tool:web"),
            ToolSpec("read_file", "Read a user file. Args: filename (str).", self.read_file, "tool:file"),
        ]
        return {spec.name: spec for spec in specs}
