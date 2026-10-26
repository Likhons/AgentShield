"""Import a public English agent-injection dataset into datasets/external.jsonl.

Source: nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1 (CC-BY-4.0)
        https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1
        Injections hidden inside the tool data (notes, messages, descriptions) of agents,
        which matches AgentShield's threat model.

(deepset/prompt-injections was tried and left out: several rows labeled English are
French, German, Spanish or Serbo-Croatian, and some "attack" rows are ordinary
role-play or questions, not injections against an agent.)

Rows come from the Hugging Face datasets-server API (no login) and are cached in
datasets/external_raw/, so the sample stays the same even if the source changes.
Sampling is deterministic (seed 42).

    python datasets/import_external.py            # uses the cache when present
    python datasets/import_external.py --refresh  # download again
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "external_raw"  # subfolder: benchmark.dataset only reads datasets/*.jsonl
OUT = HERE / "external.jsonl"
API = "https://datasets-server.huggingface.co/rows"
SEED = 42
MAX_CHARS = 2000  # longer items are skipped, never cut: cutting could remove the injection

NVIDIA = "nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1"
NVIDIA_TOTAL = 1272
PER_PAGE = 5


def fetch(dataset: str, split: str, offset: int, length: int) -> list[dict]:
    query = urllib.parse.urlencode(
        {"dataset": dataset, "config": "default", "split": split, "offset": offset, "length": length}
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"{API}?{query}", timeout=60) as resp:
                return [r["row"] for r in json.load(resp)["rows"]]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    return []


def strings(obj, out: list[str]) -> list[str]:
    """All string values inside nested dicts/lists."""
    if isinstance(obj, dict):
        for v in obj.values():
            strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            strings(v, out)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def injected_text(row: dict) -> str | None:
    """The tool-data field carrying the injection: the longest string in the agent's
    environment that contains one of the attacker's target argument values."""
    env = json.loads(row["environment"]) if isinstance(row["environment"], str) else row["environment"]
    inj = json.loads(row["injection"]) if isinstance(row["injection"], str) else row["injection"]
    needles = [str(v) for v in (inj.get("target_args") or {}).values() if len(str(v)) >= 6]
    candidates = [s for s in strings(env, []) if len(s) > 40 and any(n in s for n in needles)]
    return max(candidates, key=len) if candidates else None


def load_nvidia(refresh: bool, count: int) -> list[dict]:
    """Small pages spread over the whole dataset (all domains); cached as raw rows we kept."""
    path = RAW_DIR / "nvidia_agentic_ipi.jsonl"
    if path.exists() and not refresh:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    pages = count // PER_PAGE * 2 + 2  # fetch about twice what we need; some rows are skipped
    rows = []
    for i in range(pages):
        offset = int(i * (NVIDIA_TOTAL - PER_PAGE) / max(1, pages - 1))
        for r in fetch(NVIDIA, "train", offset, PER_PAGE):
            text = injected_text(r)
            if text:
                rows.append({
                    "id": r["id"], "domain": r["domain"], "attack_category": r["attack_category"],
                    "target_tool": r["target_tool"], "injection_vector": r["injection_vector"], "text": text,
                })
    RAW_DIR.mkdir(exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return rows


def attack_type(vector: str) -> str:
    v = vector.lower()
    if any(k in v for k in ("message", "email", "mail", "body")):
        return "indirect_email"
    if any(k in v for k in ("description", "review", "listing", "page", "post")):
        return "indirect_web"
    return "indirect_file"  # notes, comments, records, documents


def convert(count: int, refresh: bool) -> list[dict]:
    usable = [r for r in load_nvidia(refresh, count) if len(r["text"]) <= MAX_CHARS]
    sample = random.Random(SEED).sample(usable, min(count, len(usable)))
    return [
        {
            "id": f"en-att-nv{n:03d}",
            "text": r["text"],
            "language": "en",
            "label": "attack",
            "attack_type": attack_type(r["injection_vector"]),
            "target_tool": r["target_tool"],
            "source": "external",
            "notes": (
                f"external={NVIDIA}; license=cc-by-4.0; source_id={r['id']}; domain={r['domain']}; "
                f"category={r['attack_category']}; vector={r['injection_vector']}; style=embedded"
            ),
        }
        for n, r in enumerate(sample, start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--refresh", action="store_true", help="download again instead of using the cache")
    args = parser.parse_args()

    rows = convert(args.count, args.refresh)
    with open(OUT, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
