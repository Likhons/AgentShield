# AgentShield dataset (datasheet)

Labeled English / Bangla / Banglish texts for the benchmark (`benchmark/`) and, later, classifier training (Phase 4).

## Files
| File | Content | Written by | Status |
|---|---|---|---|
| `benign.jsonl` | Benign look-alikes: normal texts about money, bills, numbers, "ignore", "assistant", urgency, secrecy | LLM (Claude), via `build_benign_seed.py` | 90 items, `reviewed=no` |
| `attacks.jsonl` | Prompt-injection attacks aimed at an AI agent | Team (hand-written seed + LLM variations) | TBD |

Validate and see the balance at any time:
```powershell
python -m benchmark.dataset
```

## Format (one JSON object per line)
```json
{"id": "bn-att-001", "text": "...", "language": "bn", "label": "attack",
 "attack_type": "indirect_email", "target_tool": "send_money",
 "source": "hand_written", "notes": "style=subtle; reviewed=yes"}
```
| Field | Values |
|---|---|
| `id` | unique; convention `<language>-<att|ben>-<number>` |
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
- LLM-generated items must be reviewed by a native speaker for natural Bangla/Banglish (`reviewed=yes`).
- All phone numbers use the `010` prefix (not used by Bangladeshi operators); all names, amounts and wallets are fake.
- Attack texts exist only to test defenses and target fake accounts.
