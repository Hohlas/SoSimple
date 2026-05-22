# Wiki Index — SoSimple
> LLM-maintained catalog of synthesized wiki pages.
> Auto-generated integrity map of the whole repo: [REPO_integrity.md](REPO_integrity.md).
> Module registry (canonical, do not duplicate here): [MODULE_INDEX.md](../MODULE_INDEX.md).

## How to use (agents)
- This file is the entry point for synthesized knowledge. Read it before answering questions.
- For modules and code: use [MODULE_INDEX.md](../MODULE_INDEX.md), not wiki pages.
- For pipeline/architecture: use [docs/DATA_FLOW.md](../docs/DATA_FLOW.md) and [AGENTS.md](../AGENTS.md).
- For current operational state: use [CONTEXT_HANDOFF.md](../CONTEXT_HANDOFF.md).
- For docs/ artifacts: use [docs/README.md](../docs/README.md).
- Wiki pages below represent synthesis that has no canonical home in the project files.

---

## Research

Cross-report synthesis of experiment results and evolution of approaches.

| Page | Covers | Reports |
|------|--------|---------|
| [signal-quality-research.md](research/signal-quality-research.md) | V2 -> V3 -> Path Atlas -> Quality Filter -> Archetype Bridge: main research arc | 7 reports (04-01 — 04-04) |
| [execution-tracks.md](research/execution-tracks.md) | Exit Policy, Outcome-Aligned, Triple Barrier, Entry Path v1, trailing-stop family, take/skip v2, frequency follow-up, rule consumer, MT4 trailing execution, execution policy v2, lib_PIC external selection, lib_PIC feature training, original-contour ablation, signal-export parity, cross-instrument robustness, entry-path transfer robustness, portfolio correlation check, telemetry demo launch, MQL runtime architecture snapshot, online inference contract hardening, live-safe ML audit, CPU/GPU reproducibility, entry_path_v1 live-safe CPU baseline, quantile over CPU baseline, MT4 parity for entry_path_v1 live-safe, online/tester execution reconciliation, entry_path candidate-source audit, causal surrogate, direct bar model, direct-direction audit follow-up: parallel execution tracks | 42 reports (04-08 — 05-19) |

## Concepts

Synthesized domain knowledge extracted from multiple reports.

| Page | Description |
|------|-------------|
| [signal-archetypes.md](concepts/signal-archetypes.md) | Bimodal signal structure: 64% failure / 36% flat drift. Key insight of the project. |
