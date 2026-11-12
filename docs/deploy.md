# Putting the dashboard online (free)

> Status (12 Nov 2026): not deployed yet. The preliminary submission form asks for a live demo URL, so deploy before submitting. Publishing makes the demo reachable by anyone with the link: decide first what may be public (see "Before you publish").

## Before you publish
- **Secrets never go into the repo.** API keys (`GROQ_API_KEY`) go into the platform's secret settings. Without a key the dashboard still works in `mock` and `recorded (groq)` mode.
- **Default to offline modes.** For a public link, use `LLM_PROVIDER=mock` and the recorded real runs; a live `groq` button would spend the free-tier quota for every visitor.
- **What becomes visible:** the demo emails in `demo_agent/data/` (including the fake attack emails), the recordings and the benchmark tables. The team-written attack dataset (`datasets/attacks.jsonl`) is not shown by the dashboard, but it is in the repo: if the platform needs a public repo, decide whether to remove it from that copy (see `docs/ethics_impact.md`, misuse section).
- Record the stage demo first (`python -m demo_agent.run --all --compare --provider groq --record`) and commit `demo_agent/recordings/`.

## Option 1: Streamlit Community Cloud
1. Sign in at https://share.streamlit.io with the GitHub account that owns the repo.
2. *Create app* → choose the repo, branch `main`, main file `dashboard/app.py`.
3. *Advanced settings*: Python 3.12 or newer; secrets, if any, in TOML form, for example `LLM_PROVIDER = "mock"`.
4. Deploy. The app installs `requirements.txt` automatically.
5. Check on the platform's current docs whether private repositories are allowed on your plan before relying on it.

## Option 2: Hugging Face Spaces
1. Create a new Space at https://huggingface.co/new-space (free CPU hardware). Pick the Streamlit option if offered; otherwise the Docker option with a Streamlit template.
2. Push this repo's code to the Space (or connect it), with `dashboard/app.py` as the app file.
3. Add secrets under *Settings → Variables and secrets* (`LLM_PROVIDER=mock`; add `GROQ_API_KEY` only if live mode is wanted).
4. A Space can be private; a public Space is visible to everyone.

## After deploying
- Open the link in a private browser window and run `attack_bill_bn` in Offline and Recorded mode.
- Open every sidebar page (Benchmarks, Audit Log, Policies, Datasets).
- Live (Groq) needs `GROQ_API_KEY` in the secrets; without it the dashboard shows a clear "LLM error" and Offline keeps working.
- Never paste the key into a public file or issue; rotate it at https://console.groq.com/keys if it ever leaks.
