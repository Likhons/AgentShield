# Cached external data

`nvidia_agentic_ipi.jsonl`: rows from
[nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by NVIDIA.

Changed: only the injected tool-data string and a few metadata fields (id, domain, attack
category, target tool, injection vector) are kept from each row. Created by
`datasets/import_external.py`. Used for defensive benchmarking only.
