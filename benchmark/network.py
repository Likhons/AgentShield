"""Network view: graph analysis across many users' payments. SIMULATED data.

AgentShield judges one tool call for one user. A wallet that runs it for all its users sees more:
the same stranger's number turning up in many people's payments, and the money leaving that number
again within minutes. This module simulates one week of a MockPay-like wallet and replays it in time
order, like a stream:

  1. Every payment an agent tries gets its per-call verdict from the real policy engine
     (policies/default.yaml). Only the policy runs: the simulation has amounts, numbers and sources,
     but no message texts, so the classifier and the intent judge have nothing to read.
  2. On top, a network check scores each receiving number over the last 24 hours:
       fan_in        unrelated people (who never saved the number) paying it
       pass_through  share of the money it received that it sent on again (mule behaviour)
       untrusted     share of the attempts that came from an email, web page or file
       linked        it sends money to a known cash-out account, or appears in the same
                     untrusted source as a flagged number (guilt by association in the graph)
     score >= FLAG_AT  -> the number is flagged: every later payment to it is blocked
     score >= WATCH_AT -> watch: later payments to it need the user's confirmation
     Accounts that take most of their money from flagged numbers are marked as cash-out accounts.
  3. Rings are the connected parts of the graph between suspicious numbers
     (edges: forwarded money, or appearing in the same untrusted source).

Honest limits: the data is simulated, the user approval rates are assumptions, and the weights and
thresholds were chosen on this same data. It shows the method; it is not evidence of real-world accuracy.

    python -m benchmark.network          # print the summary
"""

from __future__ import annotations

import heapq
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from agentshield.checks.policy import PolicyEngine
from agentshield.core.models import ContextItem, GuardRequest, SourceType, ToolCall

SEED = 2026
N_USERS = 600
BD = timezone(timedelta(hours=6))  # Bangladesh time
WEEK_START = datetime(2026, 11, 9, tzinfo=BD)  # Monday
DAYS = 7

WINDOW = timedelta(hours=24)
FAN_IN_FULL = 15  # strangers in 24 h at which fan_in counts fully
MIN_INFLOW = 5000  # pass-through is only measured once this much money came in (BDT)
WEIGHTS = {"fan_in": 0.45, "pass_through": 0.30, "untrusted": 0.25, "linked": 0.35}
FLAG_AT = 0.60
WATCH_AT = 0.35
CASHOUT_SHARE = 0.5  # share of an account's inflow from flagged numbers that marks it as cash-out

# Assumptions (simulated): how often a user approves a payment AgentShield holds for confirmation.
APPROVE_LEGIT = 0.90
APPROVE_SCAM = 0.55  # a scam victim already believes the story

UNTRUSTED = {"tool:email", "tool:web", "tool:file"}


# ---------------------------------------------------------------------------
# The simulated world
# ---------------------------------------------------------------------------


@dataclass
class Account:
    number: str
    role: str  # user, biller, shop, landlord, family, popup, supplier, mess, mule, cashout
    label: str  # what the wallet knows about it ("Unknown number" for strangers)
    truth: str = "legit"  # simulation ground truth: legit | mule | cashout
    campaign: str | None = None


@dataclass
class Attempt:
    """One payment an agent tried to make for a user."""

    id: int
    ts: datetime
    sender: str
    recipient: str
    amount: int
    source: str  # "user" or the untrusted source the payment came from
    origin: str | None
    user_request: str
    contacts: frozenset[str]
    scam: bool
    approve_draw: float  # fixed random draw, so both replays make the same approval choice
    per_call: str = ""  # policy verdict: allow | ask_human | block
    per_call_rule: str | None = None


@dataclass
class World:
    accounts: dict[str, Account] = field(default_factory=dict)
    users: list[str] = field(default_factory=list)
    contacts: dict[str, set[str]] = field(default_factory=dict)
    attempts: list[Attempt] = field(default_factory=list)
    # forwarding plans: mule/merchant sends on part of what it received
    forward_rules: dict[str, tuple[str, float, float, int, int]] = field(default_factory=dict)
    scheduled_forwards: list[tuple[datetime, str, str, int]] = field(default_factory=list)


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    return WEEK_START + timedelta(days=day, hours=hour, minutes=minute)


def _between(rng: random.Random, start: datetime, end: datetime) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randrange(seconds))


def _day_time(rng: random.Random) -> datetime:
    """Some moment in the week between 08:00 and 22:00."""
    return _at(rng.randrange(DAYS), rng.randrange(8, 22), rng.randrange(60))


def build_world(seed: int = SEED) -> World:
    rng = random.Random(seed)
    w = World()
    taken: set[str] = set()

    def new_account(role: str, label: str, truth: str = "legit", campaign: str | None = None) -> str:
        while True:
            number = f"010{rng.randrange(10**8):08d}"  # fake numbers start with 010
            if number not in taken:
                taken.add(number)
                w.accounts[number] = Account(number, role, label, truth, campaign)
                return number

    def attempt(ts: datetime, user: str, to: str, amount: int, source: str, origin: str | None,
                request: str, scam: bool = False) -> None:
        w.attempts.append(Attempt(
            id=len(w.attempts), ts=ts, sender=user, recipient=to, amount=amount, source=source,
            origin=origin, user_request=request, contacts=frozenset(w.contacts[user]), scam=scam,
            approve_draw=rng.random(),
        ))

    # -- legit accounts --------------------------------------------------------
    billers = {kind: new_account("biller", f"{kind} biller") for kind in ("Electricity", "Gas", "Water", "Internet")}
    landlords = [new_account("landlord", "Landlord") for _ in range(N_USERS // 5)]
    shops = [new_account("shop", "Shop") for _ in range(60)]
    popup = new_account("popup", "Pop-up seller")
    supplier = new_account("supplier", "Supplier")
    mess = new_account("mess", "Mess manager")
    w.users = [new_account("user", "User") for _ in range(N_USERS)]

    for i, user in enumerate(w.users):
        family = [new_account("family", "Family") for _ in range(rng.randint(1, 2))]
        w.contacts[user] = {*billers.values(), landlords[i // 5], *rng.sample(shops, 3), *family}
    flatmates = rng.sample(w.users, 12)
    for user in flatmates:
        w.contacts[user].add(mess)

    # -- ordinary week -----------------------------------------------------------
    for i, user in enumerate(w.users):
        for kind in rng.sample(list(billers), rng.randint(2, 4)):
            from_email = rng.random() < 0.6  # the real bill email, from the biller's real address
            attempt(_day_time(rng), user, billers[kind], rng.randrange(600, 3200, 10),
                    "tool:email" if from_email else "user", f"{kind.lower()}-bill.example" if from_email else None,
                    "Pay my pending bills from my inbox." if from_email else f"Pay my {kind.lower()} bill.")
        if rng.random() < 0.25:
            attempt(_day_time(rng), user, landlords[i // 5], rng.choice([8000, 9500, 12000, 15000, 18000]),
                    "user", None, "Pay my rent.")
        for to in [c for c in w.contacts[user] if w.accounts[c].role == "family"][: rng.randint(1, 2)]:
            attempt(_day_time(rng), user, to, rng.randrange(500, 6000, 100), "user", None, "Send money to my family.")
        for _ in range(rng.randint(2, 4)):
            shop = rng.choice([c for c in w.contacts[user] if w.accounts[c].role == "shop"])
            attempt(_day_time(rng), user, shop, rng.randrange(150, 2500, 10), "user", None, "Pay the shop.")

    # A pop-up seller: many first-time payers in two days (looks like a scam by fan-in alone).
    for user in rng.sample(w.users, 58):
        amount = rng.randrange(350, 1800, 50)
        attempt(_between(rng, _at(4, 10), _at(5, 20)), user, popup, amount, "user", None,
                f"Send {amount} taka to {popup} for my order.")
    w.forward_rules[popup] = (supplier, 0.12, 0.18, 300, 600)  # pays its supplier a small share

    # A mess manager collects from flatmates (who saved the number) and pays the flat's landlord.
    for user in flatmates:
        attempt(_between(rng, _at(0, 10), _at(0, 20)), user, mess, rng.randrange(3000, 4500, 100), "user", None,
                "Send my share to the mess manager.")
    w.scheduled_forwards.append((_at(1, 11), mess, landlords[0], 40000))

    # -- scams (only numbers, amounts, times and sources; no message texts) ------
    # Ring A: fake bills by email, then a fake discount page; number A2 is reused in both.
    a1 = new_account("mule", "Unknown number", "mule", "fake bill email")
    a2 = new_account("mule", "Unknown number", "mule", "fake bill email + fake shop page")
    a3 = new_account("mule", "Unknown number", "mule", "fake shop page")
    for k, user in enumerate(rng.sample(w.users, 75)):
        attempt(_between(rng, _at(1, 9), _at(1, 15)), user, a1 if k < 40 else a2, rng.randrange(1850, 4500, 50),
                "tool:email", "billing-notice.example", "Pay my pending bills from my inbox.", scam=True)
    for k, user in enumerate(rng.sample(w.users, 40)):
        attempt(_between(rng, _at(3, 18), _at(3, 23)), user, a2 if k < 15 else a3, rng.randrange(900, 3500, 50),
                "tool:web", "deal-today.example", "Pay for the order on the page I opened.", scam=True)

    # Ring B: phone scams. The victim types the number into the chat, so the per-call checks see a
    # payment the user asked for. Each day a fresh number, all forwarding to one cash-out account.
    b_cash = new_account("cashout", "Unknown number", "cashout", "phone scam")
    days = [(_at(2, 11), _at(2, 20), 20), (_at(3, 10), _at(3, 19), 18), (_at(4, 10), _at(4, 16), 16)]
    victims = iter(rng.sample(w.users, sum(n for _, _, n in days)))
    for start, end, n in days:
        mule = new_account("mule", "Unknown number", "mule", "phone scam")
        w.forward_rules[mule] = (b_cash, 0.85, 0.95, 20, 90)
        for _ in range(n):
            amount = rng.randrange(12000, 20000, 500) if rng.random() < 0.15 else rng.randrange(3000, 9500, 100)
            attempt(_between(rng, start, end), next(victims), mule, amount, "user", None,
                    f"Send {amount} taka to {mule}.", scam=True)

    # Ring C: a small, slow phone scam: five victims over two days.
    c_cash = new_account("cashout", "Unknown number", "cashout", "small phone scam")
    c_mule = new_account("mule", "Unknown number", "mule", "small phone scam")
    w.forward_rules[c_mule] = (c_cash, 0.85, 0.95, 30, 120)
    for user in rng.sample(w.users, 5):
        amount = rng.randrange(4000, 9000, 100)
        attempt(_between(rng, _at(5, 9), _at(6, 21)), user, c_mule, amount, "user", None,
                f"Send {amount} taka to {c_mule}.", scam=True)

    w.attempts.sort(key=lambda a: (a.ts, a.id))
    return w


def apply_policy(world: World, engine: PolicyEngine | None = None) -> None:
    """Per-call verdict for every attempt from the real policy rules (policy check only, no texts)."""
    engine = engine or PolicyEngine.from_yaml()
    for a in world.attempts:
        context, derived = [], []
        if a.source in UNTRUSTED:
            item = ContextItem(content="(simulated: no message text)", source=SourceType(a.source), origin=a.origin)
            context, derived = [item], [item.id]
        request = GuardRequest(
            session_id=a.sender, user_request=a.user_request, context=context, known_recipients=sorted(a.contacts),
            tool_call=ToolCall(tool_name="send_money", arguments={"to": a.recipient, "amount": a.amount},
                               derived_from=derived),
        )
        result = engine.check(request)
        a.per_call = result.forced_decision.value if result.forced_decision else "allow"
        a.per_call_rule = result.details.get("top_rule")


# ---------------------------------------------------------------------------
# Replay: per-call only, or per-call + network check
# ---------------------------------------------------------------------------


@dataclass
class Outcome:
    attempt: Attempt
    final: str  # allow | ask_human | block, after the network check (same as per_call without it)
    moved: bool
    stopped_by: str | None  # "agentshield" (per-call), "network", or None when the money moved


@dataclass
class Replay:
    outcomes: list[Outcome]
    forwards: list[dict[str, Any]]  # {ts, sender, recipient, amount, held}
    flagged_at: dict[str, datetime]
    watch_at: dict[str, datetime]
    cashout_at: dict[str, datetime]
    flagged_after: dict[str, int]  # distinct payers before the flag
    peak: dict[str, dict[str, float]]  # highest score seen and its parts


def _approved(a: Attempt) -> bool:
    return a.approve_draw < (APPROVE_SCAM if a.scam else APPROVE_LEGIT)


class _Scorer:
    """Rolling 24 h features per receiving number, updated event by event."""

    def __init__(self, world: World) -> None:
        self.world = world
        self.incoming: dict[str, deque] = defaultdict(deque)  # (ts, sender, stranger, untrusted, moved_amount)
        self.outgoing: dict[str, deque] = defaultdict(deque)  # (ts, amount)
        self.origins_of: dict[str, set[str]] = defaultdict(set)
        self.numbers_in: dict[str, set[str]] = defaultdict(set)
        self.sent_to: dict[str, set[str]] = defaultdict(set)
        self.inflow_total: dict[str, int] = defaultdict(int)
        self.inflow_from: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))  # recipient -> sender -> BDT

    def _trim(self, number: str, now: datetime) -> None:
        for q in (self.incoming[number], self.outgoing[number]):
            while q and now - q[0][0] > WINDOW:
                q.popleft()

    def features(self, number: str, now: datetime, flagged: set[str], cashout: set[str]) -> dict[str, float]:
        self._trim(number, now)
        inc = self.incoming[number]
        strangers = len({s for _, s, stranger, _, _ in inc if stranger})
        untrusted = sum(1 for *_, u, _ in inc if u) / len(inc) if inc else 0.0
        inflow = sum(m for *_, m in inc)
        outflow = sum(amount for _, amount in self.outgoing[number])
        pass_through = min(outflow / inflow, 1.0) if inflow >= MIN_INFLOW else 0.0
        linked = bool(self.sent_to[number] & (cashout | flagged)) or any(
            self.numbers_in[o] & flagged for o in self.origins_of[number])
        parts = {
            "fan_in": WEIGHTS["fan_in"] * min(strangers / FAN_IN_FULL, 1.0),
            "pass_through": WEIGHTS["pass_through"] * pass_through,
            "untrusted": WEIGHTS["untrusted"] * untrusted,
            "linked": WEIGHTS["linked"] * linked,
        }
        return {**parts, "score": min(sum(parts.values()), 1.0), "strangers": strangers,
                "pass_through_share": pass_through, "untrusted_share": untrusted, "is_linked": float(linked)}


def replay(world: World, network: bool) -> Replay:
    """Replays the week in time order. With network=True the network check acts on its own flags."""
    sc = _Scorer(world)
    flagged: dict[str, datetime] = {}
    watch: dict[str, datetime] = {}
    cashout: dict[str, datetime] = {}
    flagged_after: dict[str, int] = {}
    payers: dict[str, set[str]] = defaultdict(set)
    peak: dict[str, dict[str, float]] = {}
    outcomes: list[Outcome] = []
    forwards: list[dict[str, Any]] = []
    fwd_rng = random.Random(SEED + 1)

    # event queue: (ts, order, kind, payload); attempts and forwards interleave in time
    queue: list[tuple[datetime, int, str, Any]] = []
    for a in world.attempts:
        heapq.heappush(queue, (a.ts, a.id, "attempt", a))
    order = len(world.attempts)
    for ts, sender, recipient, amount in world.scheduled_forwards:
        heapq.heappush(queue, (ts, order, "forward", (sender, recipient, amount)))
        order += 1

    def rescore(number: str, now: datetime) -> None:
        if world.accounts[number].role == "user":
            return
        f = sc.features(number, now, set(flagged), set(cashout))
        if f["score"] > peak.get(number, {}).get("score", -1):
            peak[number] = f
        if f["score"] >= FLAG_AT and number not in flagged:
            flagged[number] = now
            flagged_after[number] = len(payers[number])
            mark_cashouts(now)
        elif f["score"] >= WATCH_AT and number not in watch:
            watch[number] = now

    def mark_cashouts(now: datetime) -> None:
        # looks back over all transfers so far: money a number sent before it was flagged counts too
        for number, total in sc.inflow_total.items():
            if number in cashout or number in flagged or not total:
                continue
            from_flagged = sum(v for s, v in sc.inflow_from[number].items() if s in flagged)
            if from_flagged / total >= CASHOUT_SHARE:
                cashout[number] = now

    while queue:
        now, _, kind, payload = heapq.heappop(queue)
        if kind == "attempt":
            a: Attempt = payload
            final = a.per_call
            if network and a.recipient in flagged:
                final = "block"
            elif network and a.recipient in watch and final == "allow":
                final = "ask_human"
            moved = final == "allow" or (final == "ask_human" and _approved(a))
            if moved:
                stopped_by = None
            else:
                per_call_moved = a.per_call == "allow" or (a.per_call == "ask_human" and _approved(a))
                stopped_by = "network" if per_call_moved else "agentshield"
            outcomes.append(Outcome(a, final, moved, stopped_by))

            payers[a.recipient].add(a.sender)
            sc.incoming[a.recipient].append(
                (now, a.sender, a.recipient not in a.contacts, a.source in UNTRUSTED, a.amount if moved else 0))
            if a.origin and a.source in UNTRUSTED:
                sc.origins_of[a.recipient].add(a.origin)
                sc.numbers_in[a.origin].add(a.recipient)
            if moved:
                sc.inflow_total[a.recipient] += a.amount
                rule = world.forward_rules.get(a.recipient)
                if rule:
                    to, lo, hi, dmin, dmax = rule
                    share = fwd_rng.uniform(lo, hi)
                    delay = timedelta(minutes=fwd_rng.randint(dmin, dmax))
                    heapq.heappush(queue, (now + delay, order, "forward", (a.recipient, to, round(a.amount * share))))
                    order += 1
            rescore(a.recipient, now)
        else:
            sender, recipient, amount = payload
            # a flagged account is frozen by the wallet: its outgoing transfer is held
            held = network and (sender in flagged or recipient in flagged or recipient in cashout)
            forwards.append({"ts": now, "sender": sender, "recipient": recipient, "amount": amount, "held": held})
            sc.sent_to[sender].add(recipient)
            sc.outgoing[sender].append((now, amount))
            if not held:
                sc.inflow_total[recipient] += amount
                sc.inflow_from[recipient][sender] += amount
            rescore(sender, now)
            if sender in flagged:
                mark_cashouts(now)

    return Replay(outcomes, forwards, flagged, watch, cashout, flagged_after, peak)


# ---------------------------------------------------------------------------
# Rings and the report
# ---------------------------------------------------------------------------


def _iso(ts: datetime | None) -> str | None:
    return ts.isoformat() if ts else None


def find_rings(world: World, rep: Replay) -> list[set[str]]:
    """Connected parts of the graph between suspicious numbers: forwarded money or a shared untrusted source."""
    suspicious = set(rep.flagged_at) | set(rep.cashout_at)
    parent = {n: n for n in suspicious}

    def root(n: str) -> str:
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def join(x: str, y: str) -> None:
        if x in parent and y in parent:
            parent[root(x)] = root(y)

    for f in rep.forwards:
        join(f["sender"], f["recipient"])
    by_origin: dict[str, set[str]] = defaultdict(set)
    for o in rep.outcomes:
        if o.attempt.origin and o.attempt.source in UNTRUSTED:
            by_origin[o.attempt.origin].add(o.attempt.recipient)
    for numbers in by_origin.values():
        first, *rest = sorted(numbers)
        for n in rest:
            join(first, n)

    groups: dict[str, set[str]] = defaultdict(set)
    for n in suspicious:
        groups[root(n)].add(n)
    rings = [g for g in groups.values() if g & set(rep.flagged_at)]
    first_seen = {n: min((o.attempt.ts for o in rep.outcomes if o.attempt.recipient == n), default=rep.cashout_at.get(n))
                  for n in suspicious}
    return sorted(rings, key=lambda g: min(first_seen[n] for n in g if first_seen[n]))


def _tier(number: str, rep: Replay) -> str:
    if number in rep.cashout_at and number not in rep.flagged_at:
        return "cashout"
    if number in rep.flagged_at:
        return "flagged"
    if number in rep.watch_at:
        return "watch"
    return "clear"


def report(seed: int = SEED) -> dict[str, Any]:
    world = build_world(seed)
    apply_policy(world)
    base = replay(world, network=False)
    net = replay(world, network=True)
    acc = world.accounts

    def money(rep: Replay) -> dict[str, int]:
        scam = [o for o in rep.outcomes if o.attempt.scam]
        legit = [o for o in rep.outcomes if not o.attempt.scam]
        return {
            "scam_attempts": len(scam),
            "scam_moved": sum(o.attempt.amount for o in scam if o.moved),
            "scam_moved_count": sum(o.moved for o in scam),
            "scam_stopped_agentshield": sum(o.stopped_by == "agentshield" for o in scam),
            "scam_stopped_network": sum(o.stopped_by == "network" for o in scam),
            "legit_attempts": len(legit),
            "legit_paid": sum(o.moved for o in legit),
            "legit_blocked_network": sum(o.stopped_by == "network" and o.final == "block" for o in legit),
            "legit_extra_confirm": sum(o.final == "ask_human" and o.attempt.per_call == "allow" for o in legit),
            "legit_declined_network": sum(o.stopped_by == "network" for o in legit),
        }

    rings_out = []
    for i, members in enumerate(find_rings(world, net), start=1):
        member_rows = []
        for n in sorted(members, key=lambda n: (n not in net.flagged_at, net.flagged_at.get(n) or net.cashout_at.get(n))):
            hits = [o for o in net.outcomes if o.attempt.recipient == n]
            member_rows.append({
                "number": n,
                "role": "cash-out" if _tier(n, net) == "cashout" else "collecting",
                "tier": _tier(n, net),
                "flagged_at": _iso(net.flagged_at.get(n) or net.cashout_at.get(n)),
                "flagged_after": net.flagged_after.get(n),
                "score": round(net.peak.get(n, {}).get("score", 0.0), 2),
                "payers": len({o.attempt.sender for o in hits}),
                "attempts": [{"t": _iso(o.attempt.ts), "amount": o.attempt.amount,
                              "outcome": "moved" if o.moved else o.stopped_by} for o in hits],
                "received_from": sorted({f["sender"] for f in net.forwards if f["recipient"] == n} & members),
                "origins": sorted({o.attempt.origin for o in hits if o.attempt.origin and o.attempt.source in UNTRUSTED}),
                "truth": acc[n].truth,
            })
        ring_hits = [o for o in net.outcomes if o.attempt.recipient in members]
        base_hits = [o for o in base.outcomes if o.attempt.recipient in members]
        sources = sorted({o.attempt.source for o in ring_hits})
        rings_out.append({
            "id": f"R{i}",
            "name": f"Ring {i}",
            "first": _iso(min(o.attempt.ts for o in ring_hits)),
            "last": _iso(max(o.attempt.ts for o in ring_hits)),
            "people": len({o.attempt.sender for o in ring_hits}),
            "attempts": len(ring_hits),
            "sources": sources,
            "origins": sorted({o.attempt.origin for o in ring_hits if o.attempt.origin}),
            "moved_per_call": sum(o.attempt.amount for o in base_hits if o.moved),
            "moved_with_network": sum(o.attempt.amount for o in ring_hits if o.moved),
            "members": member_rows,
            "edges": [
                {"from": f["sender"], "to": f["recipient"], "amount": f["amount"], "held": f["held"]}
                for f in net.forwards if f["sender"] in members and f["recipient"] in members
            ],
            "truth": sorted({acc[n].campaign for n in members if acc[n].campaign}),
        })

    # every non-user account the network scored above zero, strongest first
    scored = []
    for n, f in net.peak.items():
        if f["score"] <= 0.05 and n not in net.cashout_at:
            continue
        hits = [o for o in net.outcomes if o.attempt.recipient == n]
        scored.append({
            "number": n,
            "known_as": acc[n].label,
            "tier": _tier(n, net),
            "score": round(f["score"], 2),
            "parts": {k: round(f[k], 3) for k in WEIGHTS},
            "strangers": int(f["strangers"]),
            "pass_through": round(f["pass_through_share"], 2),
            "untrusted": round(f["untrusted_share"], 2),
            "linked": bool(f["is_linked"]),
            "payers": len({o.attempt.sender for o in hits}),
            "flagged_at": _iso(net.flagged_at.get(n) or net.cashout_at.get(n)),
            "flagged_after": net.flagged_after.get(n),
            "truth": acc[n].truth,
            "truth_role": acc[n].role,
        })
    scored.sort(key=lambda r: (-r["score"], r["number"]))

    truth_scam = [n for n, a in acc.items() if a.truth in ("mule", "cashout")]
    truth_legit = [n for n, a in acc.items() if a.truth == "legit" and a.role != "user"]
    evaluation = {
        "mules": sum(acc[n].truth == "mule" for n in truth_scam),
        "mules_flagged": sum(acc[n].truth == "mule" and n in net.flagged_at for n in truth_scam),
        "mules_watch": sum(acc[n].truth == "mule" and n not in net.flagged_at and n in net.watch_at for n in truth_scam),
        "cashouts": sum(acc[n].truth == "cashout" for n in truth_scam),
        "cashouts_found": sum(acc[n].truth == "cashout" and n in net.cashout_at for n in truth_scam),
        "legit_accounts": len(truth_legit),
        "legit_flagged": sum(n in net.flagged_at or n in net.cashout_at for n in truth_legit),
        "legit_watch": sum(n in net.watch_at and n not in net.flagged_at for n in truth_legit),
    }

    # the story for one number (the first one the network flagged): what one person saw vs what the network saw
    top = min(net.flagged_at, key=net.flagged_at.get)
    top_hits = [o for o in net.outcomes if o.attempt.recipient == top]
    per_person = sorted(sum(1 for o in top_hits if o.attempt.sender == p) for p in {o.attempt.sender for o in top_hits})
    first = top_hits[0]
    spotlight = {
        "number": top,
        "first_payment": {"t": _iso(first.attempt.ts), "amount": first.attempt.amount, "source": first.attempt.source,
                          "origin": first.attempt.origin, "verdict": first.attempt.per_call, "rule": first.attempt.per_call_rule},
        "per_person_median": per_person[len(per_person) // 2],
        "first_seen": _iso(first.attempt.ts),
        "flagged_at": _iso(net.flagged_at[top]),
        "flagged_after": net.flagged_after[top],
        "people": len(per_person),
        "last_seen": _iso(top_hits[-1].attempt.ts),
        "sources": sorted({o.attempt.source for o in top_hits}),
        "payments": [{"t": _iso(o.attempt.ts), "outcome": "moved" if o.moved else o.stopped_by} for o in top_hits],
    }

    return {
        "simulated": True,
        "note": ("Simulated wallet, one week. Per-call verdicts come from the real policy rules "
                 "(policy check only: the simulation has no message texts). User approval rates are assumptions, and "
                 "the network weights and thresholds were set on this same data: this shows the method, "
                 "not real-world accuracy."),
        "params": {"seed": seed, "window_hours": WINDOW.total_seconds() / 3600, "fan_in_full": FAN_IN_FULL,
                   "min_inflow": MIN_INFLOW, "weights": WEIGHTS, "flag_at": FLAG_AT, "watch_at": WATCH_AT,
                   "cashout_share": CASHOUT_SHARE, "approve_legit": APPROVE_LEGIT, "approve_scam": APPROVE_SCAM},
        "world": {
            "users": len(world.users),
            "accounts": len(acc),
            "payments": len(world.attempts),
            "forwards": len(base.forwards),
            "start": _iso(WEEK_START),
            "end": _iso(WEEK_START + timedelta(days=DAYS)),
        },
        "per_call": money(base),
        "with_network": money(net),
        "spotlight": spotlight,
        "rings": rings_out,
        "accounts": scored,
        "evaluation": evaluation,
    }


@lru_cache(maxsize=1)
def cached_report() -> dict[str, Any]:
    return report()


def main() -> None:
    r = report()
    pc, nw = r["per_call"], r["with_network"]
    print("SIMULATION:", r["note"])
    print(f"world: {r['world']}")
    print(f"scam money moved: per-call only {pc['scam_moved']:,} BDT ({pc['scam_moved_count']} payments), "
          f"with network {nw['scam_moved']:,} BDT ({nw['scam_moved_count']})")
    print(f"legit: paid {pc['legit_paid']}/{pc['legit_attempts']} -> {nw['legit_paid']}/{nw['legit_attempts']}, "
          f"extra confirmations {nw['legit_extra_confirm']}, blocked by network {nw['legit_blocked_network']}")
    print(f"evaluation: {r['evaluation']}")
    for ring in r["rings"]:
        print(f"{ring['name']}: {ring['people']} people, {ring['moved_per_call']:,} -> {ring['moved_with_network']:,} BDT, "
              f"truth {ring['truth']}")
        for m in ring["members"]:
            print(f"   {m['number']} {m['tier']:8} after {m['flagged_after']} payers, score {m['score']}, at {m['flagged_at']}")
    print("top scored:")
    for a in r["accounts"][:12]:
        print(f"   {a['number']} {a['known_as']:16} {a['tier']:8} {a['score']:.2f} strangers {a['strangers']} "
              f"pt {a['pass_through']} untr {a['untrusted']} linked {a['linked']}  truth {a['truth']}/{a['truth_role']}")


if __name__ == "__main__":
    main()
