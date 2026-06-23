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
| [execution-tracks-overview.md](research/execution-tracks-overview.md) | Обзорная страница execution-треков: сравнение треков, открытые вопросы, навигация по подстраницам | 40 reports |
| &nbsp;&nbsp;↳ [execution-tracks-early-research.md](research/execution-tracks-early-research.md) | §1-3: Exit Policy, Outcome-Aligned, Triple Barrier | 4 reports (04-08) |
| &nbsp;&nbsp;↳ [execution-tracks-entry-path-v1.md](research/execution-tracks-entry-path-v1.md) | §4: Entry Path v1 + quantile research + cross-instrument + PF uplift | 14 reports (04-08 — 04-24) |
| &nbsp;&nbsp;↳ [execution-tracks-take-skip-v2.md](research/execution-tracks-take-skip-v2.md) | §5: Take/Skip v1 matrix + v2 handoff + trailing stop + execution policy + feature ablation | 10 reports (04-17 — 04-22) |
| &nbsp;&nbsp;↳ [execution-tracks-robustness-plus-portfolio.md](research/execution-tracks-robustness-plus-portfolio.md) | §6-7: Cross-Instrument Robustness + Portfolio Correlation | 2 reports (04-24) |
| &nbsp;&nbsp;↳ [execution-tracks-telemetry-plus-mql.md](research/execution-tracks-telemetry-plus-mql.md) | §8-9: Telemetry Demo + MQL Runtime Architecture + Contract Hardening | 2 reports (04-27 — 04-29) |
| &nbsp;&nbsp;↳ [execution-tracks-live-safe-audit.md](research/execution-tracks-live-safe-audit.md) | §10-13: Live-Safe ML Audit + Retrain + Quantile + Take/Skip Probe | 4 reports (05-05) |
| &nbsp;&nbsp;↳ [execution-tracks-reproducibility-plus-parity.md](research/execution-tracks-reproducibility-plus-parity.md) | §14-17: CPU/GPU Reproducibility + Live-Safe Reproducibility + MT4 Parity | 4 reports (05-07) |
| &nbsp;&nbsp;↳ [execution-tracks-reconciliation-plus-audit.md](research/execution-tracks-reconciliation-plus-audit.md) | §18-20: Online/Tester Reconciliation + Candidate-Source Audit + Direct Direction Improvement | 3 reports (05-12 — 05-15) |
| &nbsp;&nbsp;↳ [execution-tracks-direct-direction-audit.md](research/execution-tracks-direct-direction-audit.md) | §21: Direct Direction Audit + Rebuild + Transformer Encoder | 4 reports (05-15 — 05-21) |
| &nbsp;&nbsp;↳ [methodology-cycle-candidate-source-v2.md](research/methodology-cycle-candidate-source-v2.md) | Candidate-source v2 methodology cycle: live-safe protocol, Stage 09/10 invalidation | 1 report (05-25) |
| &nbsp;&nbsp;↳ [limit-order-feature-foundation.md](research/limit-order-feature-foundation.md) | Limit-order entry, feature ablation, direction-only signal, fractal channel ablation, RF GridSearch | 5 reports (05-29 — 06-05) |
| [fractal-stop-research.md](research/fractal-stop-research.md) | Fractal Stop Stage 1-5.0c: breach, fav, exit, walk-forward, Transformer, A7-аудит признаков, `asinh`, buy loader fix. Stage 5.0c завершил multi-seed replication test — FAIL, Transformer стабильно уступает XGBoost. Следующий шаг — Stage 5.0d (диагностический скрининг). | 19 report updates (06-10 — 06-23) |

## Concepts

Synthesized domain knowledge extracted from multiple reports.

| Page | Description |
|------|-------------|
| [signal-archetypes.md](concepts/signal-archetypes.md) | Bimodal signal structure: 64% failure / 36% flat drift. Key insight of the project. |
| [folded-mov-channels.md](concepts/folded-mov-channels.md) | Свёртка 10 up_X/dn_X → 5 mov_X: убирает 87-90% шумовых нулей, концепт и границы применимости |
