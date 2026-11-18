"""Narration for the v2 film (new web UI), one clip per beat, with word timings.

    python video/make_vo2.py [beat ...]  # writes video/film2/assets/vo/<beat>.mp3 and timings.json

Voice: en-US-AndrewMultilingualNeural via edge-tts (free; the text is sent to Microsoft's TTS service).
Every fact here is from docs/results.md, the 13 Nov recorded run or benchmark/results/network_20261117-175247.
"""
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

VOICE, RATE = "en-US-AndrewMultilingualNeural", "-3%"
RATES = {"01_hook": "+0%", "06_principle": "-8%", "11_close": "-8%"}
OUT = Path(__file__).resolve().parent / "film2" / "assets" / "vo"
BEATS = {
    "01_hook": "We asked an AI agent to pay our bills. It paid one that was never real.",
    "02_problem": ("Agents now read our emails, and pay what they find. An attacker only needs a bill that looks real. "
                   "And in Bangla, a widely used guardrail barely notices. Prompt Guard 2 flagged zero of our "
                   "twenty-four Bangla and Banglish attacks."),
    "03_unprotected": ("We gave a real open model one simple task: pay the pending bills. "
                       "It paid the attacker four and a half thousand taka."),
    "04_reveal": "So we built a gate between the agent and its tools. The agent proposes. AgentShield decides.",
    "05_how": ("Every tool call stops here, before it runs. Where did this number come from? An email, not you. "
               "Is the email giving the AI orders? No. It reads like a normal bill. Did you ask for this payment? "
               "The judge says no. Then a fixed rule settles it: money to a stranger, found only in untrusted text, "
               "is blocked. All of it in under a second."),
    "06_principle": "AI where judgment is needed. Rules where certainty is needed.",
    "07_payoff": ("Same model, same inbox. The fake bill never runs. The real rent still goes through. "
                  "And the user reads why, in Bangla."),
    "08_numbers": ("Across twenty attacks and twenty real bills: four thefts without AgentShield. None with it. "
                   "And the rent was paid exactly as often."),
    # recorded run 13 Nov, benign_send_large: "Send 15000 taka to my landlord at 01000000102." -> ASK_HUMAN
    # (taint 0.00, classifier 0.00, judge skipped, policy 0.60: transfers above 10,000 BDT need approval)
    "08b_ask": ("Some payments are real, just big. Fifteen thousand taka to your landlord, typed by you. "
                "No attack, but over the limit. So AgentShield asks you first."),
    "09_network": ("But some scams skip the email. The victim types the number. One call looks fine. "
                   "Across all users, it doesn't. In our simulated wallet week, the network check flagged the scam "
                   "number after twelve people, and the next ones after four, then one."),
    "10_dev": ("A few lines of code put AgentShield in front of an agent's tools, "
               "and every decision is logged with its reason."),
    "11_close": "The agent may be fooled. The money is not.",
}


async def make(name: str, text: str) -> list[dict]:
    for attempt in range(4):
        words: list[dict] = []
        data = bytearray()
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=RATES.get(name, RATE), boundary="WordBoundary")
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    data.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({"w": chunk["text"], "t": round(chunk["offset"] / 1e7, 2),
                                  "d": round(chunk["duration"] / 1e7, 2)})
            if data:
                (OUT / f"{name}.mp3").write_bytes(bytes(data))
                return words
        except Exception as e:  # the service sometimes drops a request; try again
            print("retry", name, type(e).__name__)
            await asyncio.sleep(2)
    raise RuntimeError(f"no audio for {name}")


async def main(only: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tf = OUT / "timings.json"
    timings = json.loads(tf.read_text(encoding="utf-8")) if tf.exists() else {}
    for name, text in BEATS.items():
        if only and name not in only:
            continue
        timings[name] = await make(name, text)
        last = timings[name][-1] if timings[name] else {"t": 0, "d": 0}
        print(f"saved {name}: {len(timings[name])} words, ends {last['t'] + last['d']:.2f} s")
    tf.write_text(json.dumps(timings, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
