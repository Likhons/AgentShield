"""Generate the narration, one clip per beat, with the chosen neural voice.

    python video/make_vo.py [beat ...]  # writes video/film/assets/vo/<beat>.mp3 (all beats, or only those named)

Voice: en-IN-PrabhatNeural via edge-tts (free; the text is sent to Microsoft's TTS service).
The demo beat's amounts must match the recorded real-model run; re-run after editing them.
"""
import asyncio
import json
from pathlib import Path

import edge_tts

VOICE, RATE = "en-IN-PrabhatNeural", "-5%"
RATES = {"01_hook": "+4%"}  # the cold open is read a little faster
OUT = Path(__file__).resolve().parent / "film" / "assets" / "vo"
BEATS = {
    "01_hook": "Four thousand five hundred taka, gone. Your AI agent paid a bill that was never real.",
    "02_problem": ("An agent reads emails, web pages and files, and it cannot always tell its user's request "
                   "from text an attacker planted there. In Bangladesh, that text is often Bangla or Banglish. "
                   "A widely used guardrail, Meta's Prompt Guard 2, flagged none of our 24 Bangla and Banglish attacks."),
    "03_setup": ("Here is a real model, asked to pay the pending bills in its inbox. On the left it runs unprotected. "
                 "On the right, the same agent runs behind AgentShield."),
    "04_demo": ("Unprotected, the model paid the rent, and it also paid the fake bill: four and a half thousand taka "
                "to the attacker. With AgentShield, the fake bill is blocked before any money moves, with the reason "
                "in Bangla and English, and the landlord's real rent still goes through."),
    "05_how": ("AgentShield checks every tool call before it runs. Where did each value come from? Does the untrusted "
               "text try to instruct the AI? Does this action follow from what the user asked? And fixed policy rules "
               "for money. AI where judgment is needed. Deterministic rules where certainty is needed."),
    "06_proof": ("We measured it with the same real model, on twenty Bangla and Banglish attacks and twenty normal bill "
                 "payments. Without AgentShield, four attacks stole money. With it, none did. And the rent was paid "
                 "just as often as without protection: sixteen of twenty, both times. Every number is published "
                 "with its confidence interval."),
    "07_trust": ("Every decision is logged with its reason, and the rules are plain, readable policy. Developers add "
                 "AgentShield with a few lines of Python, or through an HTTP API from any framework."),
    "08_close": "The agent may be fooled. The money is not. Try the live demo at agentshield-demo dot streamlit dot app.",
}


async def main(only=None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tf = OUT / "timings.json"
    timings = json.loads(tf.read_text(encoding="utf-8")) if tf.exists() else {}
    for name, text in BEATS.items():
        if only and name not in only:
            continue
        words = []
        with open(OUT / f"{name}.mp3", "wb") as audio:
            async for chunk in edge_tts.Communicate(text, VOICE, rate=RATES.get(name, RATE), boundary="WordBoundary").stream():
                if chunk["type"] == "audio":
                    audio.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({"w": chunk["text"], "t": round(chunk["offset"] / 1e7, 2)})
        timings[name] = words
        print("saved", name, len(words), "words")
    (OUT / "timings.json").write_text(json.dumps(timings, indent=1), encoding="utf-8")


if __name__ == "__main__":
    import sys
    asyncio.run(main(sys.argv[1:] or None))
