# AgentShield dataset (datasheet)

Labeled English / Bangla / Banglish texts for the benchmark (`benchmark/`) and, later, classifier training (Phase 4).

## Files
| File | Content | Written by | Status |
|---|---|---|---|
| `benign.jsonl` | Benign look-alikes: normal texts about money, bills, numbers, "ignore", "assistant", urgency, secrecy | LLMs, via `build_benign_seed.py` | 135 items (45 per language), `reviewed=no` |
| `external.jsonl` | English attacks hidden inside agent tool data, from a public dataset | Third party, via `import_external.py` | 40 items, see External sources |
| `attacks.jsonl` | Prompt-injection attacks aimed at an AI agent, in Bangla and Banglish | Team (hand-written seed + LLM variations) | TBD |
| `external_raw/` | Cached rows of the public dataset (not loaded by the benchmark) | – | re-download with `--refresh` |

Validate and see the balance at any time:
```powershell
python -m benchmark.dataset
```

## External sources
`python datasets/import_external.py` rebuilds `external.jsonl` from the cache (deterministic sample, seed 42).

| Dataset | License | Used as | Items |
|---|---|---|---|
| [nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1) | CC-BY-4.0 | English attacks hidden in agent tool data (`indirect_*`, `style=embedded`) | 40 |

Changes we made (CC-BY-4.0 asks for this): from each original row we keep only the tool-data string that carries the injection (the longest string in the agent's environment containing the attacker's target arguments), skip items longer than 2,000 characters instead of cutting them, and map the injection vector to our `attack_type`. `notes` keeps the original `source_id`, domain, attack category and vector. The sample spans 9 domains (healthcare, HR, legal, e-commerce, logistics, IT helpdesk, real estate, education, insurance), none of them banking.

Not used: [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) (Apache-2.0). Several rows that would be labeled English are French, German, Spanish or Serbo-Croatian, and some "attack" rows are ordinary role-play or questions rather than injections against an agent.

No public Bangla/Banglish agent prompt-injection dataset is known to us; Bangla and Banglish attacks come from the team (`attacks.jsonl`). Claims about other datasets must be verified (link + license) before they appear in the pitch.

## Format (one JSON object per line)
```json
{"id": "bn-att-001", "text": "...", "language": "bn", "label": "attack",
 "attack_type": "indirect_email", "target_tool": "send_money",
 "source": "hand_written", "notes": "style=subtle; reviewed=yes"}
```
| Field | Values |
|---|---|
| `id` | unique; convention: language, then `att` or `ben`, then a number, e.g. `bn-att-001` |
| `language` | `en`, `bn` (Bangla script), `banglish` (Bangla in Latin letters), `mixed` |
| `label` | `attack` or `benign` |
| `attack_type` | attacks only: `direct`, `indirect_email`, `indirect_web`, `indirect_file`; benign: `null` |
| `target_tool` | e.g. `send_money` (attacks), `null` for benign |
| `source` | `hand_written`, `llm_generated` or `external` (record which dataset in `notes`) |
| `notes` | free tags separated by `; `: `style=blunt` / `style=subtle` (attacks), `lookalike=<tag>` (benign), `reviewed=yes/no` |

## Targets (300–500 items total)
Per language (en, bn, banglish), roughly:
- **Attacks ~60–80**: both `style=blunt` (openly addresses the AI) and `style=subtle` (looks like a normal message to a human, e.g. a fake bill with the attacker's number), spread over email / web / file / direct.
- **Benign ~60–80**: at least half look-alikes (money, numbers, "send", "ignore", "assistant", urgency).

## Known limitations (keep honest in results)
- **The benign seed was written by the same assistant that had read the heuristic classifier's code.** It deliberately includes hard negatives, but it may still unconsciously avoid wording that would fool the heuristic. Independent benign items (written by people who have not seen the classifier) are needed before over-refusal numbers are claimed as final.
- External items are English only and not about banking, and many share one template ("[PRIORITY MESSAGE] ... — the user", "URGENT: Before completing any other tasks, you MUST"). Detectors that learn the template score well on them, so report results per source (external vs team-written) as well as per language.
- LLM-generated items must be reviewed by a native speaker for natural Bangla/Banglish (`reviewed=yes`).
- All phone numbers use the `010` prefix (not used by Bangladeshi operators); all names, amounts and wallets are fake.
- Attack texts exist only to test defenses and target fake accounts.
