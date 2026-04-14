# REPO Integrity Map — SoSimple
> Auto-generated 2026-04-14 20:15 UTC · git `0998c56`
> Refresh: `python wiki/wiki.py generate`  ·  Verify: `python wiki/wiki.py verify`

## Agent Access Protocol

1. Read this file first to get a project map (what exists, where, integrity hash).
2. Run `python wiki/wiki.py verify` to detect files changed since last index.
3. Navigate via paths in the tables; use `wiki/research/` and `wiki/concepts/` for synthesized knowledge.
4. After modifying significant files, run `generate` and commit `REPO_integrity.md`.

**Tracked**: 645 files  ·  **Commit**: `0998c56`  ·  **Generated**: 2026-04-14 20:15 UTC

## Root Docs

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [AGENTS.md](AGENTS.md) |  | 2026-04-14 | 10KB | `c0235e5f` |
| [CHANGELOG.md](CHANGELOG.md) |  | 2026-04-14 | 106KB | `82eb034c` |
| [CLAUDE.md](CLAUDE.md) |  | 2026-04-14 | 3KB | `7eaa5505` |
| [CONTEXT_HANDOFF.md](CONTEXT_HANDOFF.md) |  | 2026-04-14 | 13KB | `ff3ca80e` |
| [MODULE_INDEX.md](MODULE_INDEX.md) |  | 2026-04-14 | 14KB | `7351ca61` |
| [README.md](README.md) |  | 2026-04-14 | 969B | `4fc82a41` |

## Documentation

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам | 2026-04-14 | 22KB | `e5956740` |
| [docs/ML/baseline_experiments.py.md](docs/ML/baseline_experiments.py.md) |  | 2026-04-14 | 2KB | `8dc50028` |
| [docs/ML/conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы | 2026-04-14 | 5KB | `dca1ea47` |
| [docs/ML/neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики | 2026-04-14 | 23KB | `a6510741` |
| [docs/MT/lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC | 2026-04-14 | 6KB | `0ba8e976` |
| [docs/MT/ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) | 2026-04-14 | 8KB | `815919c2` |
| [docs/MT/trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() | 2026-04-14 | 12KB | `9b0f7b34` |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document | 2026-04-14 | 4KB | `5df7ce35` |
| [docs/dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv | 2026-04-14 | 10KB | `7d9009ee` |
| [docs/processing/label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора | 2026-04-14 | 2KB | `fa1b6aa7` |
| [docs/processing/label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict | 2026-04-14 | 1KB | `55dc11a9` |
| [docs/processing/normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков | 2026-04-14 | 3KB | `06e43e08` |
| [docs/statistics/EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу | 2026-04-14 | 17KB | `914b3a5e` |
| [docs/statistics/signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF | 2026-04-14 | 7KB | `052eb4f7` |
| [docs/statistics/statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике | 2026-04-14 | 6KB | `9835a477` |
| [docs/superpowers/plans/2026-03-22-triple-barrier.md](docs/superpowers/plans/2026-03-22-triple-barrier.md) |  | 2026-04-14 | 28KB | `fe31fa4e` |
| [docs/superpowers/plans/2026-03-25-updn-denormalization.md](docs/superpowers/plans/2026-03-25-updn-denormalization.md) |  | 2026-04-14 | 19KB | `01d8efee` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md) |  | 2026-04-14 | 22KB | `ba50388e` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md) |  | 2026-04-14 | 9KB | `7ed11b5f` |
| [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](docs/superpowers/plans/2026-04-01-signal-research-variant-2.md) |  | 2026-04-14 | 29KB | `09aa7ec8` |
| [docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md](docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md) |  | 2026-04-14 | 20KB | `43d44dc5` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-04-14 | 19KB | `b25009ee` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3.md) |  | 2026-04-14 | 3KB | `3b40fae8` |
| [docs/superpowers/plans/2026-04-03-signal-path-atlas.md](docs/superpowers/plans/2026-04-03-signal-path-atlas.md) |  | 2026-04-14 | 39KB | `b0fea2ba` |
| [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](docs/superpowers/plans/2026-04-03-signal-quality-filter.md) |  | 2026-04-14 | 39KB | `6518f11b` |
| [docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md](docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md) |  | 2026-04-14 | 7KB | `636d1a67` |
| [docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md](docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md) |  | 2026-04-14 | 7KB | `af4ec829` |
| [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md) |  | 2026-04-14 | 11KB | `44d803a8` |
| [docs/superpowers/plans/2026-04-07-validation-first-research.md](docs/superpowers/plans/2026-04-07-validation-first-research.md) |  | 2026-04-14 | 10KB | `c0b29ff8` |
| [docs/superpowers/plans/2026-04-08-entry-path-v1.md](docs/superpowers/plans/2026-04-08-entry-path-v1.md) |  | 2026-04-14 | 28KB | `86fb358e` |
| [docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md](docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-04-14 | 15KB | `e9cb346d` |
| [docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md](docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md) |  | 2026-04-14 | 22KB | `0a35f491` |
| [docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md](docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md) |  | 2026-04-14 | 29KB | `1ab66152` |
| [docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md](docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md) |  | 2026-04-14 | 26KB | `9b5a8151` |
| [docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md](docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md) |  | 2026-04-14 | 31KB | `155a7325` |
| [docs/superpowers/plans/2026-04-10-entry-path-cqr.md](docs/superpowers/plans/2026-04-10-entry-path-cqr.md) |  | 2026-04-14 | 24KB | `0f832c74` |
| [docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md](docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md) |  | 2026-04-14 | 15KB | `fe2b2167` |
| [docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md](docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md) |  | 2026-04-14 | 14KB | `5b49271e` |
| [docs/superpowers/plans/2026-04-13-early-timeout-bar12.md](docs/superpowers/plans/2026-04-13-early-timeout-bar12.md) |  | 2026-04-14 | 37KB | `908866bf` |
| [docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md](docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-04-14 | 20KB | `80750ee6` |
| [docs/superpowers/plans/2026-04-13-label-convention-audit.md](docs/superpowers/plans/2026-04-13-label-convention-audit.md) |  | 2026-04-14 | 31KB | `ea55d54a` |
| [docs/superpowers/plans/2026-04-13-ny-session-filter.md](docs/superpowers/plans/2026-04-13-ny-session-filter.md) |  | 2026-04-14 | 2KB | `325f4e90` |
| [docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md](docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md) |  | 2026-04-14 | 29KB | `74578dba` |
| [docs/superpowers/plans/2026-04-13-pred-adv-cap.md](docs/superpowers/plans/2026-04-13-pred-adv-cap.md) |  | 2026-04-14 | 2KB | `51f3e15c` |
| [docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md](docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md) |  | 2026-04-14 | 15KB | `50a68d1f` |
| [docs/superpowers/plans/2026-04-13-quantile-fav-composition.md](docs/superpowers/plans/2026-04-13-quantile-fav-composition.md) |  | 2026-04-14 | 25KB | `20186b5d` |
| [docs/superpowers/plans/2026-04-13-quantile-forward-validation.md](docs/superpowers/plans/2026-04-13-quantile-forward-validation.md) |  | 2026-04-14 | 13KB | `e4d63c4c` |
| [docs/superpowers/plans/ME13_Diagnostics_Plan.md](docs/superpowers/plans/ME13_Diagnostics_Plan.md) |  | 2026-04-14 | 5KB | `10a0c4ea` |
| [docs/superpowers/roadmap.md](docs/superpowers/roadmap.md) |  | 2026-04-14 | 6KB | `9aa88e34` |
| [docs/superpowers/specs/2026-03-22-triple-barrier-design.md](docs/superpowers/specs/2026-03-22-triple-barrier-design.md) |  | 2026-04-14 | 12KB | `82b0860f` |
| [docs/superpowers/specs/2026-03-27-pf-improvement-design.md](docs/superpowers/specs/2026-03-27-pf-improvement-design.md) |  | 2026-04-14 | 18KB | `85d548d9` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md) |  | 2026-04-14 | 13KB | `477a2843` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md) |  | 2026-04-14 | 10KB | `db9fb094` |
| [docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md](docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md) |  | 2026-04-14 | 21KB | `dcb5dcd3` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md) |  | 2026-04-14 | 3KB | `15368fbf` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md) |  | 2026-04-14 | 10KB | `88d9ca83` |
| [docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md](docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md) |  | 2026-04-14 | 10KB | `81b0a31f` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md) |  | 2026-04-14 | 8KB | `60e115b4` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md) |  | 2026-04-14 | 7KB | `119b59e0` |
| [docs/superpowers/specs/2026-04-08-entry-path-v1-design.md](docs/superpowers/specs/2026-04-08-entry-path-v1-design.md) |  | 2026-04-14 | 17KB | `deafd06e` |
| [docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md) |  | 2026-04-14 | 12KB | `e771d628` |
| [docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md) |  | 2026-04-14 | 12KB | `402001b6` |
| [docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md](docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md) |  | 2026-04-14 | 12KB | `1a877fcd` |
| [docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md](docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md) |  | 2026-04-14 | 13KB | `2ef88bef` |
| [docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md](docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md) |  | 2026-04-14 | 8KB | `8272fe58` |
| [docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md](docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md) |  | 2026-04-14 | 7KB | `7fede3fc` |
| [docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md](docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md) |  | 2026-04-14 | 6KB | `f1f6cae8` |
| [docs/tests/tests.md](docs/tests/tests.md) |  | 2026-04-14 | 4KB | `551fd6e9` |

## Reports

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md) |  | 2026-04-14 | 5KB | `37b9ec88` |
| [docs/reports/2026-04-02-signal-research-variant-3-prep.md](docs/reports/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-04-14 | 12KB | `d26a9270` |
| [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md) |  | 2026-04-14 | 15KB | `98244916` |
| [docs/reports/2026-04-03-signal-path-atlas.md](docs/reports/2026-04-03-signal-path-atlas.md) |  | 2026-04-14 | 8KB | `c68aa3b8` |
| [docs/reports/2026-04-04-archetype-filter-bridge.md](docs/reports/2026-04-04-archetype-filter-bridge.md) |  | 2026-04-14 | 14KB | `28e2bd45` |
| [docs/reports/2026-04-04-signal-path-atlas-readout.md](docs/reports/2026-04-04-signal-path-atlas-readout.md) |  | 2026-04-14 | 25KB | `fbfedb40` |
| [docs/reports/2026-04-04-signal-quality-filter.md](docs/reports/2026-04-04-signal-quality-filter.md) |  | 2026-04-14 | 12KB | `e2e74751` |
| [docs/reports/2026-04-08-entry-path-v1-baseline.md](docs/reports/2026-04-08-entry-path-v1-baseline.md) |  | 2026-04-14 | 10KB | `ff56ac36` |
| [docs/reports/2026-04-08-ml-exit-validation-first.md](docs/reports/2026-04-08-ml-exit-validation-first.md) |  | 2026-04-14 | 8KB | `f61986e3` |
| [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md) |  | 2026-04-14 | 8KB | `1783da26` |
| [docs/reports/2026-04-08-triple-barrier-hardening.md](docs/reports/2026-04-08-triple-barrier-hardening.md) |  | 2026-04-14 | 8KB | `ec8f88b7` |
| [docs/reports/2026-04-08-triple-barrier-runtime-verdict.md](docs/reports/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-04-14 | 9KB | `33e1602a` |
| [docs/reports/2026-04-09-entry-path-trade-filter.md](docs/reports/2026-04-09-entry-path-trade-filter.md) |  | 2026-04-14 | 10KB | `8553f63e` |
| [docs/reports/2026-04-09-entry-path-v1-loss-weighting.md](docs/reports/2026-04-09-entry-path-v1-loss-weighting.md) |  | 2026-04-14 | 7KB | `79f4b733` |
| [docs/reports/2026-04-09-mt4-parity-check-winner.md](docs/reports/2026-04-09-mt4-parity-check-winner.md) |  | 2026-04-14 | 8KB | `a8467fad` |
| [docs/reports/2026-04-10-entry-path-v1-quantile.md](docs/reports/2026-04-10-entry-path-v1-quantile.md) |  | 2026-04-14 | 6KB | `d4fef0e4` |
| [docs/reports/2026-04-12-quantile-status-decision.md](docs/reports/2026-04-12-quantile-status-decision.md) |  | 2026-04-14 | 10KB | `5375913e` |
| [docs/reports/2026-04-12-tb-verdict.md](docs/reports/2026-04-12-tb-verdict.md) |  | 2026-04-14 | 7KB | `089642df` |
| [docs/reports/2026-04-13-fav-3-vs-12-standalone.md](docs/reports/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-04-14 | 5KB | `8a929a77` |
| [docs/reports/2026-04-13-label-convention-audit.md](docs/reports/2026-04-13-label-convention-audit.md) |  | 2026-04-14 | 6KB | `3ddc2a23` |
| [docs/reports/2026-04-13-pf-uplift-discovery.md](docs/reports/2026-04-13-pf-uplift-discovery.md) |  | 2026-04-14 | 14KB | `f93b85c0` |
| [docs/reports/2026-04-13-quantile-fav-composition.md](docs/reports/2026-04-13-quantile-fav-composition.md) |  | 2026-04-14 | 8KB | `8dd53bda` |
| [docs/reports/2026-04-13-quantile-forward-validation.md](docs/reports/2026-04-13-quantile-forward-validation.md) |  | 2026-04-14 | 4KB | `1364686a` |
| [docs/reports/2026-04-14-quantile-early-timeout.md](docs/reports/2026-04-14-quantile-early-timeout.md) |  | 2026-04-14 | 7KB | `9409b8ca` |
| [docs/reports/README.md](docs/reports/README.md) |  | 2026-04-14 | 2KB | `ed0769cc` |

## ML

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [ML/README.md](ML/README.md) |  |  | 2026-04-14 | 4KB | `97586272` |
| [ML/ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | 🏁 | 2026-04-14 | 4KB | `390f9209` |
| [ML/baseline/baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | 🏁 | 2026-04-14 | 40KB | `d214b051` |
| [ML/baseline/reports/baseline_report.md](ML/baseline/reports/baseline_report.md) |  |  | 2026-04-14 | 4KB | `66cbf52f` |
| [ML/benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | 🏁 | 2026-04-14 | 6KB | `1bc86818` |
| [ML/benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | ✅ | 2026-04-14 | 13KB | `40bbefc1` |
| [ML/benchmark_entry_path_v1_quantile_n_boost.py](ML/benchmark_entry_path_v1_quantile_n_boost.py) |  |  | 2026-04-14 | 13KB | `6538fa97` |
| [ML/benchmark_fav_3_vs_12_standalone.py](ML/benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-04-14 | 16KB | `8e4214fd` |
| [ML/benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | 🏁 | 2026-04-14 | 14KB | `16753618` |
| [ML/benchmark_quantile_early_timeout.py](ML/benchmark_quantile_early_timeout.py) |  |  | 2026-04-14 | 17KB | `7a8acedc` |
| [ML/benchmark_quantile_fav_composition.py](ML/benchmark_quantile_fav_composition.py) |  |  | 2026-04-14 | 15KB | `97a02b70` |
| [ML/benchmark_quantile_forward_validation.py](ML/benchmark_quantile_forward_validation.py) |  |  | 2026-04-14 | 5KB | `a3386bcc` |
| [ML/benchmark_triple_barrier_mt4_execution.py](ML/benchmark_triple_barrier_mt4_execution.py) |  |  | 2026-04-14 | 4KB | `3ef3e057` |
| [ML/compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | 🏁 | 2026-04-14 | 13KB | `103ded09` |
| [ML/conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | 🏁 | 2026-04-14 | 14KB | `d34cb990` |
| [ML/conformal/conformal_quantiles.json](ML/conformal/conformal_quantiles.json) |  |  | 2026-04-14 | 399B | `6d9e2e03` |
| [ML/data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ | 2026-04-14 | 42KB | `2d5baa5e` |
| [ML/entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | ✅ | 2026-04-14 | 12KB | `618cac0e` |
| [ML/entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | ✅ | 2026-04-14 | 14KB | `54d61050` |
| [ML/entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | ✅ | 2026-04-14 | 8KB | `6e03b05a` |
| [ML/evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | ✅ | 2026-04-14 | 29KB | `cb7ba908` |
| [ML/experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | 🏁 | 2026-04-14 | 20KB | `390bd6fb` |
| [ML/export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export train/validation/test predictions for entry_path_v1_quantile | ✅ | 2026-04-14 | 6KB | `9a532051` |
| [ML/export_entry_path_v1_quantile_rule.py](ML/export_entry_path_v1_quantile_rule.py) |  |  | 2026-04-14 | 7KB | `aa96afd9` |
| [ML/export_updn_active_predictions.py](ML/export_updn_active_predictions.py) |  |  | 2026-04-14 | 4KB | `515bde2e` |
| [ML/losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ | 2026-04-14 | 9KB | `f7313c67` |
| [ML/models/__init__.py](ML/models/__init__.py) |  |  | 2026-04-14 | 1KB | `f8ff5fa3` |
| [ML/models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | 🏁 | 2026-04-14 | 4KB | `f1b6faea` |
| [ML/models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | 🏁 | 2026-04-14 | 4KB | `61595f42` |
| [ML/models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | ✅ | 2026-04-14 | 3KB | `4d6b2e51` |
| [ML/models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | ✅ | 2026-04-14 | 4KB | `a25b4776` |
| [ML/models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 | 2026-04-14 | 5KB | `069a6018` |
| [ML/models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | ✅ | 2026-04-14 | 7KB | `27645ebe` |
| [ML/optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | 🏁 | 2026-04-14 | 19KB | `f6c18a03` |
| [ML/reports/architecture_comparison_classification.md](ML/reports/architecture_comparison_classification.md) |  |  | 2026-04-14 | 3KB | `c0fe9f2d` |
| [ML/reports/architecture_comparison_regression.md](ML/reports/architecture_comparison_regression.md) |  |  | 2026-04-14 | 1KB | `3fe65254` |
| [ML/reports/architecture_comparison_regression_updn.md](ML/reports/architecture_comparison_regression_updn.md) |  |  | 2026-04-14 | 1KB | `bc5e1dc4` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 536B | `2dbd3e0a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `2f9e801c` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 536B | `7b9539cf` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 2KB | `062a50ec` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 544B | `7d0c8863` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `756079bf` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 541B | `201a0e3e` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `a077c548` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 528B | `a9a86071` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `ece7ee12` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 521B | `d4d1887c` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `e186a9fd` |
| [ML/reports/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_report.md) |  |  | 2026-04-14 | 495B | `e8a9e03d` |
| [ML/reports/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `ead9e11c` |
| [ML/reports/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_filter_report.md) |  |  | 2026-04-14 | 706B | `0d99ebcd` |
| [ML/reports/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-04-14 | 1KB | `f665ab0d` |
| [ML/reports/entry_path_v1_quantile_selected_rule.json](ML/reports/entry_path_v1_quantile_selected_rule.json) |  |  | 2026-04-14 | 2KB | `a2fce0f7` |
| [ML/reports/evaluate_test_H12.md](ML/reports/evaluate_test_H12.md) |  |  | 2026-04-14 | 513B | `8b8eb347` |
| [ML/reports/evaluate_test_entry_path_v1.md](ML/reports/evaluate_test_entry_path_v1.md) |  |  | 2026-04-14 | 1KB | `36f18e23` |
| [ML/reports/evaluate_test_entry_path_v1_quantile.md](ML/reports/evaluate_test_entry_path_v1_quantile.md) |  |  | 2026-04-14 | 523B | `03c3cfb6` |
| [ML/reports/evaluate_test_tb.md](ML/reports/evaluate_test_tb.md) |  |  | 2026-04-14 | 1KB | `295448ff` |
| [ML/reports/evaluate_validation_entry_path_v1.md](ML/reports/evaluate_validation_entry_path_v1.md) |  |  | 2026-04-14 | 1KB | `6eb89813` |
| [ML/reports/fav_3_vs_12_standalone/run_metadata.json](ML/reports/fav_3_vs_12_standalone/run_metadata.json) |  |  | 2026-04-14 | 1KB | `749e6a5b` |
| [ML/reports/fav_3_vs_12_standalone/selected_threshold.json](ML/reports/fav_3_vs_12_standalone/selected_threshold.json) |  |  | 2026-04-14 | 532B | `d941fc13` |
| [ML/reports/fav_3_vs_12_standalone/verdict.json](ML/reports/fav_3_vs_12_standalone/verdict.json) |  |  | 2026-04-14 | 893B | `1fc84a37` |
| [ML/reports/frozen_exit_policy.json](ML/reports/frozen_exit_policy.json) |  |  | 2026-04-14 | 537B | `4da12318` |
| [ML/reports/label_convention_audit.md](ML/reports/label_convention_audit.md) |  |  | 2026-04-14 | 3KB | `72706b95` |
| [ML/reports/n_boost_result.json](ML/reports/n_boost_result.json) |  |  | 2026-04-14 | 1KB | `9248dae1` |
| [ML/reports/optuna_best_params_bilstm_regression.json](ML/reports/optuna_best_params_bilstm_regression.json) |  |  | 2026-04-14 | 496B | `b1a36a79` |
| [ML/reports/optuna_best_params_cnn1d_classification.json](ML/reports/optuna_best_params_cnn1d_classification.json) |  |  | 2026-04-14 | 461B | `25ae2754` |
| [ML/reports/optuna_best_params_transformer_regression_updn.json](ML/reports/optuna_best_params_transformer_regression_updn.json) |  |  | 2026-04-14 | 539B | `5a6d031a` |
| [ML/reports/optuna_study_bilstm_regression_20260311_223415.json](ML/reports/optuna_study_bilstm_regression_20260311_223415.json) |  |  | 2026-04-14 | 1KB | `f908cbce` |
| [ML/reports/optuna_study_bilstm_regression_20260312_003636.json](ML/reports/optuna_study_bilstm_regression_20260312_003636.json) |  |  | 2026-04-14 | 31KB | `8318dd5a` |
| [ML/reports/optuna_study_bilstm_regression_20260312_105613.json](ML/reports/optuna_study_bilstm_regression_20260312_105613.json) |  |  | 2026-04-14 | 18KB | `9860a4c5` |
| [ML/reports/optuna_study_bilstm_regression_20260312_112811.json](ML/reports/optuna_study_bilstm_regression_20260312_112811.json) |  |  | 2026-04-14 | 18KB | `535d2951` |
| [ML/reports/optuna_study_bilstm_regression_20260316_102024.json](ML/reports/optuna_study_bilstm_regression_20260316_102024.json) |  |  | 2026-04-14 | 31KB | `ef829e93` |
| [ML/reports/optuna_study_cnn1d_classification_20260226_134119.json](ML/reports/optuna_study_cnn1d_classification_20260226_134119.json) |  |  | 2026-04-14 | 29KB | `a53f62cd` |
| [ML/reports/optuna_study_cnn1d_classification_20260227_231828.json](ML/reports/optuna_study_cnn1d_classification_20260227_231828.json) |  |  | 2026-04-14 | 28KB | `f8e66057` |
| [ML/reports/optuna_study_cnn1d_classification_20260228_100415.json](ML/reports/optuna_study_cnn1d_classification_20260228_100415.json) |  |  | 2026-04-14 | 29KB | `c38b7403` |
| [ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json](ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json) |  |  | 2026-04-14 | 33KB | `2c98a9f9` |
| [ML/reports/outcome_target_validation_benchmark.md](ML/reports/outcome_target_validation_benchmark.md) |  |  | 2026-04-14 | 763B | `9104e652` |
| [ML/reports/pf_uplift_discovery/baseline_numbers.json](ML/reports/pf_uplift_discovery/baseline_numbers.json) |  |  | 2026-04-14 | 2KB | `4519e3fe` |
| [ML/reports/pf_uplift_discovery/hypotheses_longlist.md](ML/reports/pf_uplift_discovery/hypotheses_longlist.md) |  |  | 2026-04-14 | 8KB | `61fcd585` |
| [ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json](ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json) |  |  | 2026-04-14 | 602B | `d5ab62dc` |
| [ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json](ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json) |  |  | 2026-04-14 | 536B | `afb475b6` |
| [ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json) |  |  | 2026-04-14 | 655B | `1db83311` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json) |  |  | 2026-04-14 | 665B | `8da7e815` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json) |  |  | 2026-04-14 | 623B | `866da98b` |
| [ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json](ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json) |  |  | 2026-04-14 | 614B | `2146acd5` |
| [ML/reports/pf_uplift_discovery/run_metadata.json](ML/reports/pf_uplift_discovery/run_metadata.json) |  |  | 2026-04-14 | 552B | `2ffaa2db` |
| [ML/reports/quantile_early_timeout/run_metadata.json](ML/reports/quantile_early_timeout/run_metadata.json) |  |  | 2026-04-14 | 3KB | `a1af3c28` |
| [ML/reports/quantile_early_timeout/test_summary.json](ML/reports/quantile_early_timeout/test_summary.json) |  |  | 2026-04-14 | 618B | `550a17e5` |
| [ML/reports/quantile_early_timeout/validation_summary.json](ML/reports/quantile_early_timeout/validation_summary.json) |  |  | 2026-04-14 | 1KB | `4d766207` |
| [ML/reports/quantile_fav_composition/intersection_diagnostic.json](ML/reports/quantile_fav_composition/intersection_diagnostic.json) |  |  | 2026-04-14 | 270B | `8877d751` |
| [ML/reports/quantile_fav_composition/n_boost_composition.json](ML/reports/quantile_fav_composition/n_boost_composition.json) |  |  | 2026-04-14 | 155B | `164387a5` |
| [ML/reports/quantile_fav_composition/run_metadata.json](ML/reports/quantile_fav_composition/run_metadata.json) |  |  | 2026-04-14 | 4KB | `6aa02ee6` |
| [ML/reports/quantile_fav_composition/test_metrics.json](ML/reports/quantile_fav_composition/test_metrics.json) |  |  | 2026-04-14 | 1KB | `86714f9b` |
| [ML/reports/quantile_fav_composition/updn_active_source/metadata.json](ML/reports/quantile_fav_composition/updn_active_source/metadata.json) |  |  | 2026-04-14 | 619B | `d44841e2` |
| [ML/reports/quantile_fav_composition/validation_metrics.json](ML/reports/quantile_fav_composition/validation_metrics.json) |  |  | 2026-04-14 | 1KB | `7583bfeb` |
| [ML/reports/quantile_forward_validation/run_metadata.json](ML/reports/quantile_forward_validation/run_metadata.json) |  |  | 2026-04-14 | 554B | `eeb46771` |
| [ML/reports/quantile_forward_validation/summary.json](ML/reports/quantile_forward_validation/summary.json) |  |  | 2026-04-14 | 440B | `f208a93b` |
| [ML/reports/reproducibility_report_12H.md](ML/reports/reproducibility_report_12H.md) |  |  | 2026-04-14 | 1KB | `c9af48ba` |
| [ML/reports/tb_mt4_verdict/test_summary.json](ML/reports/tb_mt4_verdict/test_summary.json) |  |  | 2026-04-14 | 172B | `6ea3e9d3` |
| [ML/reports/tb_mt4_verdict/validation_summary.json](ML/reports/tb_mt4_verdict/validation_summary.json) |  |  | 2026-04-14 | 167B | `cc2e7d34` |
| [ML/reports/tb_selected_rule.json](ML/reports/tb_selected_rule.json) |  |  | 2026-04-14 | 279B | `3329dfb8` |
| [ML/reports/threshold_analysis_12H.md](ML/reports/threshold_analysis_12H.md) |  |  | 2026-04-14 | 2KB | `2eba7e9d` |
| [ML/reports/threshold_analysis_24H.md](ML/reports/threshold_analysis_24H.md) |  |  | 2026-04-14 | 2KB | `b6b5b9d3` |
| [ML/reports/threshold_analysis_48H.md](ML/reports/threshold_analysis_48H.md) |  |  | 2026-04-14 | 2KB | `9f692fd3` |
| [ML/reports/threshold_analysis_tb.md](ML/reports/threshold_analysis_tb.md) |  |  | 2026-04-14 | 975B | `d501c624` |
| [ML/reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | 🏁 | 2026-04-14 | 7KB | `756dd1c8` |
| [ML/tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | 🏁 | 2026-04-14 | 2KB | `502427cf` |
| [ML/tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | ✅ | 2026-04-14 | 4KB | `f07ea73a` |
| [ML/threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | ✅ | 2026-04-14 | 47KB | `b03bf490` |
| [ML/train.py](ML/train.py) | Обучение (--task regression_updn / triple_barrier) | ✅ | 2026-04-14 | 93KB | `f3d5366f` |
| [ML/triple_barrier_mt4_execution.py](ML/triple_barrier_mt4_execution.py) |  |  | 2026-04-14 | 6KB | `e2520e9d` |
| [ML/utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ | 2026-04-14 | 11KB | `5458dccf` |

## Processing

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [processing/README.md](processing/README.md) |  |  | 2026-04-14 | 1KB | `0013c357` |
| [processing/label_main.py](processing/label_main.py) | CLI оркестратор pipeline | 🏁 | 2026-04-14 | 17KB | `396488f9` |
| [processing/label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | 🏁 | 2026-04-14 | 36KB | `4352233a` |
| [processing/normalize.py](processing/normalize.py) | Построчная нормализация признаков | 🏁 | 2026-04-14 | 25KB | `62ee241c` |

## API

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [API/README.md](API/README.md) |  |  | 2026-04-14 | 2KB | `6e0d3067` |
| [API/api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, отдача ML-сигналов | 🏁 | 2026-04-14 | 6KB | `6c418d6e` |
| [API/exit_policy_research.py](API/exit_policy_research.py) | Offline research: сравнение ML-политик выхода и position management | 🏁 | 2026-04-14 | 14KB | `1d29b812` |
| [API/export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) |  |  | 2026-04-14 | 8KB | `a5a84e1a` |
| [API/generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | ✅ | 2026-04-14 | 25KB | `8804d3d0` |
| [API/signal_path_atlas.py](API/signal_path_atlas.py) | Research CLI: ATR-normalized Signal Path Atlas, path archetypes, holdout validation | 🏁 | 2026-04-14 | 37KB | `e2c123fe` |
| [API/signal_quality_research.py](API/signal_quality_research.py) | Signal Quality Filter Research (Variant 4): multi-horizon prediction features как фильтры | 🏁 | 2026-04-14 | 29KB | `ad2482f8` |
| [API/signal_research.py](API/signal_research.py) | Research CLI: качество ML-сигналов по реальным OHLC (Variant 2/3) | 🏁 | 2026-04-14 | 72KB | `c723fb6f` |
| [API/test_api_client.py](API/test_api_client.py) | Интеграционный тест REST API-сервера (MT4) | 🏁 | 2026-04-14 | 1KB | `83309207` |

## Statistics

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [statistics/EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | 🏁 | 2026-04-14 | 188KB | `4c750fc3` |
| [statistics/README.md](statistics/README.md) |  |  | 2026-04-14 | 2KB | `8a02dc7e` |
| [statistics/analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | 🏁 | 2026-04-14 | 8KB | `f3ed1639` |
| [statistics/class_statistics.json](statistics/class_statistics.json) |  |  | 2026-04-14 | 6KB | `c107590a` |
| [statistics/feature_catalog.json](statistics/feature_catalog.json) |  |  | 2026-04-14 | 70KB | `bb41c2d1` |
| [statistics/nero_features_metadata.json](statistics/nero_features_metadata.json) |  |  | 2026-04-14 | 6KB | `fc79c23a` |
| [statistics/reports/EDA_executed.ipynb](statistics/reports/EDA_executed.ipynb) |  |  | 2026-04-14 | 3MB | `--------` |
| [statistics/reports/EDA_report.md](statistics/reports/EDA_report.md) |  |  | 2026-04-14 | 59KB | `01e9ac82` |
| [statistics/signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | ✅ | 2026-04-14 | 49KB | `da86a8c1` |
| [statistics/statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | 🏁 | 2026-04-14 | 21KB | `c725dd71` |
| [statistics/statistics_summary.json](statistics/statistics_summary.json) |  |  | 2026-04-14 | 5KB | `1e7882c0` |

## Tests

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [tests/README.md](tests/README.md) |  |  | 2026-04-14 | 1KB | `c1093573` |
| [tests/test_benchmark_fav_3_vs_12_standalone.py](tests/test_benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-04-14 | 11KB | `dcdcc7a1` |
| [tests/test_benchmark_outcome_targets.py](tests/test_benchmark_outcome_targets.py) | `ML/benchmark_outcome_targets.py` | ✅ | 2026-04-14 | 4KB | `e9159813` |
| [tests/test_benchmark_quantile_early_timeout.py](tests/test_benchmark_quantile_early_timeout.py) |  |  | 2026-04-14 | 13KB | `6a8d5a38` |
| [tests/test_benchmark_quantile_fav_composition.py](tests/test_benchmark_quantile_fav_composition.py) |  |  | 2026-04-14 | 6KB | `e7f68596` |
| [tests/test_benchmark_quantile_forward_validation.py](tests/test_benchmark_quantile_forward_validation.py) |  |  | 2026-04-14 | 6KB | `3dc6e7a3` |
| [tests/test_entry_path_labels.py](tests/test_entry_path_labels.py) | `processing/label_signals.py` — entry_path_v1 helpers | ✅ | 2026-04-14 | 3KB | `abe2c2b4` |
| [tests/test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | ✅ | 2026-04-14 | 1KB | `e0f000fe` |
| [tests/test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | ✅ | 2026-04-14 | 7KB | `7894f43c` |
| [tests/test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | ✅ | 2026-04-14 | 3KB | `bb7e4326` |
| [tests/test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | ✅ | 2026-04-14 | 12KB | `8390258c` |
| [tests/test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | ✅ | 2026-04-14 | 7KB | `00d9071b` |
| [tests/test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | ✅ | 2026-04-14 | 4KB | `142bfe32` |
| [tests/test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | ✅ | 2026-04-14 | 1KB | `b9a1044c` |
| [tests/test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | ✅ | 2026-04-14 | 8KB | `30925a1f` |
| [tests/test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | ✅ | 2026-04-14 | 2KB | `294562f5` |
| [tests/test_entry_path_v1_quantile_training.py](tests/test_entry_path_v1_quantile_training.py) |  |  | 2026-04-14 | 9KB | `9a3a0f3e` |
| [tests/test_exit_policy_research.py](tests/test_exit_policy_research.py) | `API/exit_policy_research.py` | ✅ | 2026-04-14 | 4KB | `4c75d18c` |
| [tests/test_export_entry_path_v1_quantile_rule.py](tests/test_export_entry_path_v1_quantile_rule.py) |  |  | 2026-04-14 | 2KB | `8a808fd4` |
| [tests/test_export_entry_path_v1_quantile_signals.py](tests/test_export_entry_path_v1_quantile_signals.py) |  |  | 2026-04-14 | 7KB | `237d172f` |
| [tests/test_generate_signals_research.py](tests/test_generate_signals_research.py) | TB signal selection в `API/generate_signals.py` | ✅ | 2026-04-14 | 831B | `44529dd9` |
| [tests/test_inverse_piecewise.py](tests/test_inverse_piecewise.py) | `processing/normalize.py` + `statistics/signal_tracer.py` — round-trip piecewise | ✅ | 2026-04-14 | 5KB | `30c6b7c6` |
| [tests/test_label_updn.py](tests/test_label_updn.py) | `processing/label_signals.py` — parse_fractal, label_updn | ✅ | 2026-04-14 | 4KB | `be2af292` |
| [tests/test_outcome_tasks.py](tests/test_outcome_tasks.py) | outcome tasks в `ML/data_loader.py` | ✅ | 2026-04-14 | 1KB | `8be56a6e` |
| [tests/test_signal_path_atlas.py](tests/test_signal_path_atlas.py) | `API/signal_path_atlas.py` — calendar split, path tensor, archetypes, CLI | ✅ | 2026-04-14 | 38KB | `94234b75` |
| [tests/test_signal_quality_research.py](tests/test_signal_quality_research.py) | `API/signal_quality_research.py` — filter features, variance check, tree, holdout | ✅ | 2026-04-14 | 12KB | `60b730b0` |
| [tests/test_signal_research.py](tests/test_signal_research.py) | `API/signal_research.py` — ATR14, excursions, barriers, split | ✅ | 2026-04-14 | 41KB | `2eeb81b2` |
| [tests/test_signal_tracer_tb.py](tests/test_signal_tracer_tb.py) | TB-specific parsing в `statistics/signal_tracer.py` | ✅ | 2026-04-14 | 2KB | `cfe94d2f` |
| [tests/test_tb_label_invariants.py](tests/test_tb_label_invariants.py) |  |  | 2026-04-14 | 1KB | `46510bd4` |
| [tests/test_trade_target_labels.py](tests/test_trade_target_labels.py) | `processing/label_signals.py` — trade target labels | ✅ | 2026-04-14 | 2KB | `6f50053b` |
| [tests/test_triple_barrier_calibration.py](tests/test_triple_barrier_calibration.py) | EV/calibration helper для Triple Barrier | ✅ | 2026-04-14 | 745B | `591d7e79` |
| [tests/test_triple_barrier_first_touch.py](tests/test_triple_barrier_first_touch.py) | first-touch helper для Triple Barrier разметки | ✅ | 2026-04-14 | 1KB | `0aef6c1d` |
| [tests/test_triple_barrier_mt4_execution.py](tests/test_triple_barrier_mt4_execution.py) |  |  | 2026-04-14 | 4KB | `a5e04561` |
| [tests/test_triple_barrier_training.py](tests/test_triple_barrier_training.py) | transfer-learning kwargs для TB обучения | ✅ | 2026-04-14 | 1KB | `3c7dd827` |

## MQL

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [MT/.vscode/settings.json](MT/.vscode/settings.json) |  |  | 2026-04-14 | 928B | `d6834b74` |
| [MT/MQL4/.vscode/settings.json](MT/MQL4/.vscode/settings.json) |  |  | 2026-04-14 | 927B | `c3c0af89` |
| [MT/MQL4/Experts/$o$imple.mq4](MT/MQL4/Experts/$o$imple.mq4) |  |  | 2026-04-14 | 12KB | `3539d741` |
| [MT/MQL4/Include/COUNT.mqh](MT/MQL4/Include/COUNT.mqh) |  |  | 2026-04-14 | 8KB | `687fc943` |
| [MT/MQL4/Include/ERRORs.mqh](MT/MQL4/Include/ERRORs.mqh) |  |  | 2026-04-14 | 20KB | `09c555ab` |
| [MT/MQL4/Include/FUNCTIONS.mqh](MT/MQL4/Include/FUNCTIONS.mqh) |  |  | 2026-04-14 | 15KB | `d2671854` |
| [MT/MQL4/Include/INPUT.mqh](MT/MQL4/Include/INPUT.mqh) |  |  | 2026-04-14 | 22KB | `27ad874f` |
| [MT/MQL4/Include/MAIN.mqh](MT/MQL4/Include/MAIN.mqh) |  |  | 2026-04-14 | 9KB | `2daa8904` |
| [MT/MQL4/Include/MM.mqh](MT/MQL4/Include/MM.mqh) |  |  | 2026-04-14 | 10KB | `c7d3005a` |
| [MT/MQL4/Include/ORDERS.mqh](MT/MQL4/Include/ORDERS.mqh) |  |  | 2026-04-14 | 40KB | `fbab4671` |
| [MT/MQL4/Include/OUTPUT.mqh](MT/MQL4/Include/OUTPUT.mqh) |  |  | 2026-04-14 | 19KB | `7ff1d32e` |
| [MT/MQL4/Include/SERVICE.mqh](MT/MQL4/Include/SERVICE.mqh) |  |  | 2026-04-14 | 80KB | `cb127d0e` |
| [MT/MQL4/Include/StdLibErr.mqh](MT/MQL4/Include/StdLibErr.mqh) |  |  | 2026-04-14 | 673B | `8a094f85` |
| [MT/MQL4/Include/WinUser32.mqh](MT/MQL4/Include/WinUser32.mqh) |  |  | 2026-04-14 | 17KB | `05085603` |
| [MT/MQL4/Include/head_PIC.mqh](MT/MQL4/Include/head_PIC.mqh) |  |  | 2026-04-14 | 9KB | `b5a78736` |
| [MT/MQL4/Include/iGRAPH.mqh](MT/MQL4/Include/iGRAPH.mqh) |  |  | 2026-04-14 | 38KB | `73d71482` |
| [MT/MQL4/Include/lib_ATR.mqh](MT/MQL4/Include/lib_ATR.mqh) |  |  | 2026-04-14 | 2KB | `77c582a3` |
| [MT/MQL4/Include/lib_Flat.mqh](MT/MQL4/Include/lib_Flat.mqh) |  |  | 2026-04-14 | 13KB | `bc1a865b` |
| [MT/MQL4/Include/lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, торговля | ✅ | 2026-04-14 | 13KB | `7c84529b` |
| [MT/MQL4/Include/lib_ML_Signal_TB.mqh](MT/MQL4/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-04-14 | 8KB | `86f9658b` |
| [MT/MQL4/Include/lib_ML_Signal_back.mqh](MT/MQL4/Include/lib_ML_Signal_back.mqh) |  |  | 2026-04-14 | 14KB | `996e3367` |
| [MT/MQL4/Include/lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | ⚠️ | 2026-04-14 | 56KB | `ac479661` |
| [MT/MQL4/Include/stderror.mqh](MT/MQL4/Include/stderror.mqh) |  |  | 2026-04-14 | 9KB | `1678c440` |
| [MT/MQL4/Include/stdlib.mqh](MT/MQL4/Include/stdlib.mqh) |  |  | 2026-04-14 | 648B | `fa321ad4` |
| [MT/MQL4/Indicators/ATR.mq4](MT/MQL4/Indicators/ATR.mq4) |  |  | 2026-04-14 | 3KB | `dc211832` |
| [MT/MQL4/Indicators/ATR_original.mq4](MT/MQL4/Indicators/ATR_original.mq4) |  |  | 2026-04-14 | 3KB | `efe79c20` |
| [MT/MQL4/Indicators/iATR.mq4](MT/MQL4/Indicators/iATR.mq4) |  |  | 2026-04-14 | 3KB | `2053ea50` |
| [MT/MQL4/Indicators/iATRcycle.mq4](MT/MQL4/Indicators/iATRcycle.mq4) |  |  | 2026-04-14 | 2KB | `3a5033e7` |
| [MT/MQL4/Indicators/iPIC.mq4](MT/MQL4/Indicators/iPIC.mq4) |  |  | 2026-04-14 | 13KB | `2b8088f6` |
| [MT/MQL4/Indicators/iPOC.mq4](MT/MQL4/Indicators/iPOC.mq4) |  |  | 2026-04-14 | 7KB | `4b4df898` |
| [MT/MQL4/Indicators/iVolumeCluster.mq4](MT/MQL4/Indicators/iVolumeCluster.mq4) |  |  | 2026-04-14 | 44KB | `db9c3442` |
| [MT/MQL4/Libraries/StdLibErr.mqh](MT/MQL4/Libraries/StdLibErr.mqh) |  |  | 2026-04-14 | 673B | `01044c60` |
| [MT/MQL4/Libraries/WinUser32.mqh](MT/MQL4/Libraries/WinUser32.mqh) |  |  | 2026-04-14 | 17KB | `84f99057` |
| [MT/MQL4/Libraries/stderror.mqh](MT/MQL4/Libraries/stderror.mqh) |  |  | 2026-04-14 | 9KB | `47505e6c` |
| [MT/MQL4/Libraries/stdlib.mq4](MT/MQL4/Libraries/stdlib.mq4) |  |  | 2026-04-14 | 19KB | `cdb0a440` |
| [MT/MQL4/Libraries/stdlib.mqh](MT/MQL4/Libraries/stdlib.mqh) |  |  | 2026-04-14 | 648B | `5695494a` |
| [MT/MQL4/README.md](MT/MQL4/README.md) |  |  | 2026-04-14 | 146B | `4e32d804` |
| [MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4](MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4) |  |  | 2026-04-14 | 2KB | `7d447b15` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4) |  |  | 2026-04-14 | 3KB | `d0dbff33` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4) |  |  | 2026-04-14 | 4KB | `c0c67ebe` |
| [MT/MQL4/Scripts/ExportOHLC.mq4](MT/MQL4/Scripts/ExportOHLC.mq4) |  |  | 2026-04-14 | 1KB | `3358f6b5` |
| [MT/MQL4/Scripts/HistoryConvertor1002.mq4](MT/MQL4/Scripts/HistoryConvertor1002.mq4) |  |  | 2026-04-14 | 4KB | `2a904122` |
| [MT/MQL4/Scripts/MATLABLOG.mq4](MT/MQL4/Scripts/MATLABLOG.mq4) |  |  | 2026-04-14 | 10KB | `01bef2dd` |
| [MT/MQL4/Scripts/PeriodConverter.mq4](MT/MQL4/Scripts/PeriodConverter.mq4) |  |  | 2026-04-14 | 6KB | `b5a97900` |
| [MT/MQL4/Scripts/trade.mq4](MT/MQL4/Scripts/trade.mq4) |  |  | 2026-04-14 | 1KB | `7c2e252f` |
| [MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh](MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh) |  |  | 2026-04-14 | 3KB | `98d2d8a4` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh) |  |  | 2026-04-14 | 2KB | `ec173678` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh) |  |  | 2026-04-14 | 9KB | `3d047cfe` |
| [MT/MQL4/Trash/iSIG_TURTLE.mqh](MT/MQL4/Trash/iSIG_TURTLE.mqh) |  |  | 2026-04-14 | 3KB | `1b311295` |
| [MT/MQL4/Trash/lib_PIC_old.mqh](MT/MQL4/Trash/lib_PIC_old.mqh) |  |  | 2026-04-14 | 43KB | `59b6536b` |
| [MT/MQL4/Trash/lib_POC.mqh](MT/MQL4/Trash/lib_POC.mqh) |  |  | 2026-04-14 | 7KB | `130bc358` |
| [MT/MQL4/Trash/lib_REZENKO.mqh](MT/MQL4/Trash/lib_REZENKO.mqh) |  |  | 2026-04-14 | 8KB | `8128da38` |
| [MT/MQL4/Trash/lib_TRG.mqh](MT/MQL4/Trash/lib_TRG.mqh) |  |  | 2026-04-14 | 3KB | `e676d2c4` |
| [MT/MQL4/Trash/lib_Triangle.mqh](MT/MQL4/Trash/lib_Triangle.mqh) |  |  | 2026-04-14 | 9KB | `12350503` |
| [MT/MQL4/Trash/lib_ssss.mqh](MT/MQL4/Trash/lib_ssss.mqh) |  |  | 2026-04-14 | 3KB | `6c2e9b73` |
| [MT/MQL5/Include/Arrays/Array.mqh](MT/MQL5/Include/Arrays/Array.mqh) |  |  | 2026-04-14 | 6KB | `dcaa074e` |
| [MT/MQL5/Include/Arrays/ArrayChar.mqh](MT/MQL5/Include/Arrays/ArrayChar.mqh) |  |  | 2026-04-14 | 24KB | `54edbdc1` |
| [MT/MQL5/Include/Arrays/ArrayColor.mqh](MT/MQL5/Include/Arrays/ArrayColor.mqh) |  |  | 2026-04-14 | 24KB | `5de5acca` |
| [MT/MQL5/Include/Arrays/ArrayDatetime.mqh](MT/MQL5/Include/Arrays/ArrayDatetime.mqh) |  |  | 2026-04-14 | 24KB | `28aca33a` |
| [MT/MQL5/Include/Arrays/ArrayDouble.mqh](MT/MQL5/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-04-14 | 24KB | `b442d2c3` |
| [MT/MQL5/Include/Arrays/ArrayFloat.mqh](MT/MQL5/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-04-14 | 24KB | `58db64bf` |
| [MT/MQL5/Include/Arrays/ArrayInt.mqh](MT/MQL5/Include/Arrays/ArrayInt.mqh) |  |  | 2026-04-14 | 24KB | `60c3a599` |
| [MT/MQL5/Include/Arrays/ArrayLong.mqh](MT/MQL5/Include/Arrays/ArrayLong.mqh) |  |  | 2026-04-14 | 24KB | `93c0a2e1` |
| [MT/MQL5/Include/Arrays/ArrayObj.mqh](MT/MQL5/Include/Arrays/ArrayObj.mqh) |  |  | 2026-04-14 | 24KB | `1b604f04` |
| [MT/MQL5/Include/Arrays/ArrayShort.mqh](MT/MQL5/Include/Arrays/ArrayShort.mqh) |  |  | 2026-04-14 | 24KB | `588fba4c` |
| [MT/MQL5/Include/Arrays/ArrayString.mqh](MT/MQL5/Include/Arrays/ArrayString.mqh) |  |  | 2026-04-14 | 24KB | `d7e92876` |
| [MT/MQL5/Include/Arrays/ArrayUChar.mqh](MT/MQL5/Include/Arrays/ArrayUChar.mqh) |  |  | 2026-04-14 | 24KB | `b7d6f43f` |
| [MT/MQL5/Include/Arrays/ArrayUInt.mqh](MT/MQL5/Include/Arrays/ArrayUInt.mqh) |  |  | 2026-04-14 | 24KB | `e6097a29` |
| [MT/MQL5/Include/Arrays/ArrayULong.mqh](MT/MQL5/Include/Arrays/ArrayULong.mqh) |  |  | 2026-04-14 | 24KB | `6c18b082` |
| [MT/MQL5/Include/Arrays/ArrayUShort.mqh](MT/MQL5/Include/Arrays/ArrayUShort.mqh) |  |  | 2026-04-14 | 24KB | `92db202e` |
| [MT/MQL5/Include/Arrays/List.mqh](MT/MQL5/Include/Arrays/List.mqh) |  |  | 2026-04-14 | 20KB | `a173f72b` |
| [MT/MQL5/Include/Arrays/Tree.mqh](MT/MQL5/Include/Arrays/Tree.mqh) |  |  | 2026-04-14 | 13KB | `8824d2cf` |
| [MT/MQL5/Include/Arrays/TreeNode.mqh](MT/MQL5/Include/Arrays/TreeNode.mqh) |  |  | 2026-04-14 | 6KB | `efde8191` |
| [MT/MQL5/Include/COUNT.mqh](MT/MQL5/Include/COUNT.mqh) |  |  | 2026-04-14 | 8KB | `93b61a0a` |
| [MT/MQL5/Include/Canvas/Canvas.mqh](MT/MQL5/Include/Canvas/Canvas.mqh) |  |  | 2026-04-14 | 152KB | `4abe8ef4` |
| [MT/MQL5/Include/Canvas/Canvas3D.mqh](MT/MQL5/Include/Canvas/Canvas3D.mqh) |  |  | 2026-04-14 | 33KB | `f75c5970` |
| [MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh](MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh) |  |  | 2026-04-14 | 35KB | `018e7b5b` |
| [MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh](MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh) |  |  | 2026-04-14 | 11KB | `89f96b38` |
| [MT/MQL5/Include/Canvas/Charts/LineChart.mqh](MT/MQL5/Include/Canvas/Charts/LineChart.mqh) |  |  | 2026-04-14 | 12KB | `ac171461` |
| [MT/MQL5/Include/Canvas/Charts/PieChart.mqh](MT/MQL5/Include/Canvas/Charts/PieChart.mqh) |  |  | 2026-04-14 | 13KB | `81e44597` |
| [MT/MQL5/Include/Canvas/DX/DXBox.mqh](MT/MQL5/Include/Canvas/DX/DXBox.mqh) |  |  | 2026-04-14 | 3KB | `e9cbd560` |
| [MT/MQL5/Include/Canvas/DX/DXBuffers.mqh](MT/MQL5/Include/Canvas/DX/DXBuffers.mqh) |  |  | 2026-04-14 | 4KB | `da4319c8` |
| [MT/MQL5/Include/Canvas/DX/DXData.mqh](MT/MQL5/Include/Canvas/DX/DXData.mqh) |  |  | 2026-04-14 | 3KB | `4a5f2988` |
| [MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh](MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh) |  |  | 2026-04-14 | 12KB | `ce240376` |
| [MT/MQL5/Include/Canvas/DX/DXHandle.mqh](MT/MQL5/Include/Canvas/DX/DXHandle.mqh) |  |  | 2026-04-14 | 8KB | `7a799c15` |
| [MT/MQL5/Include/Canvas/DX/DXInput.mqh](MT/MQL5/Include/Canvas/DX/DXInput.mqh) |  |  | 2026-04-14 | 4KB | `2c890e23` |
| [MT/MQL5/Include/Canvas/DX/DXMath.mqh](MT/MQL5/Include/Canvas/DX/DXMath.mqh) |  |  | 2026-04-14 | 151KB | `cbff51f5` |
| [MT/MQL5/Include/Canvas/DX/DXMesh.mqh](MT/MQL5/Include/Canvas/DX/DXMesh.mqh) |  |  | 2026-04-14 | 15KB | `5bb993cf` |
| [MT/MQL5/Include/Canvas/DX/DXObject.mqh](MT/MQL5/Include/Canvas/DX/DXObject.mqh) |  |  | 2026-04-14 | 1KB | `605a2574` |
| [MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh](MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh) |  |  | 2026-04-14 | 2KB | `262b9064` |
| [MT/MQL5/Include/Canvas/DX/DXShader.mqh](MT/MQL5/Include/Canvas/DX/DXShader.mqh) |  |  | 2026-04-14 | 16KB | `fbeceb80` |
| [MT/MQL5/Include/Canvas/DX/DXSurface.mqh](MT/MQL5/Include/Canvas/DX/DXSurface.mqh) |  |  | 2026-04-14 | 6KB | `75cfc660` |
| [MT/MQL5/Include/Canvas/DX/DXTexture.mqh](MT/MQL5/Include/Canvas/DX/DXTexture.mqh) |  |  | 2026-04-14 | 6KB | `1a3377f2` |
| [MT/MQL5/Include/Canvas/DX/DXUtils.mqh](MT/MQL5/Include/Canvas/DX/DXUtils.mqh) |  |  | 2026-04-14 | 35KB | `81b0d9c9` |
| [MT/MQL5/Include/Canvas/FlameCanvas.mqh](MT/MQL5/Include/Canvas/FlameCanvas.mqh) |  |  | 2026-04-14 | 26KB | `8a0d3427` |
| [MT/MQL5/Include/ChartObjects/ChartObject.mqh](MT/MQL5/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-04-14 | 40KB | `f13eb438` |
| [MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-04-14 | 8KB | `7479429b` |
| [MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh](MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh) |  |  | 2026-04-14 | 16KB | `0d77ef95` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-04-14 | 23KB | `9c0cbe08` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-04-14 | 20KB | `26885f86` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-04-14 | 11KB | `11590972` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh) |  |  | 2026-04-14 | 9KB | `c0255f7d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-04-14 | 17KB | `6ae0eb18` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-04-14 | 16KB | `f4d66975` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-04-14 | 15KB | `7888e00d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-04-14 | 7KB | `d6d59613` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-04-14 | 37KB | `64387446` |
| [MT/MQL5/Include/Charts/Chart.mqh](MT/MQL5/Include/Charts/Chart.mqh) |  |  | 2026-04-14 | 62KB | `c5d96344` |
| [MT/MQL5/Include/Controls/BmpButton.mqh](MT/MQL5/Include/Controls/BmpButton.mqh) |  |  | 2026-04-14 | 11KB | `91c016b1` |
| [MT/MQL5/Include/Controls/Button.mqh](MT/MQL5/Include/Controls/Button.mqh) |  |  | 2026-04-14 | 6KB | `39ba2260` |
| [MT/MQL5/Include/Controls/CheckBox.mqh](MT/MQL5/Include/Controls/CheckBox.mqh) |  |  | 2026-04-14 | 7KB | `cd5744e7` |
| [MT/MQL5/Include/Controls/CheckGroup.mqh](MT/MQL5/Include/Controls/CheckGroup.mqh) |  |  | 2026-04-14 | 13KB | `3f03b33e` |
| [MT/MQL5/Include/Controls/ComboBox.mqh](MT/MQL5/Include/Controls/ComboBox.mqh) |  |  | 2026-04-14 | 13KB | `df4bb90f` |
| [MT/MQL5/Include/Controls/DateDropList.mqh](MT/MQL5/Include/Controls/DateDropList.mqh) |  |  | 2026-04-14 | 14KB | `85818981` |
| [MT/MQL5/Include/Controls/DatePicker.mqh](MT/MQL5/Include/Controls/DatePicker.mqh) |  |  | 2026-04-14 | 10KB | `2e2ce745` |
| [MT/MQL5/Include/Controls/Defines.mqh](MT/MQL5/Include/Controls/Defines.mqh) |  |  | 2026-04-14 | 12KB | `066dbc7d` |
| [MT/MQL5/Include/Controls/Dialog.mqh](MT/MQL5/Include/Controls/Dialog.mqh) |  |  | 2026-04-14 | 37KB | `d1e15482` |
| [MT/MQL5/Include/Controls/Edit.mqh](MT/MQL5/Include/Controls/Edit.mqh) |  |  | 2026-04-14 | 8KB | `aed92dbf` |
| [MT/MQL5/Include/Controls/Label.mqh](MT/MQL5/Include/Controls/Label.mqh) |  |  | 2026-04-14 | 4KB | `1d73f6a0` |
| [MT/MQL5/Include/Controls/ListView.mqh](MT/MQL5/Include/Controls/ListView.mqh) |  |  | 2026-04-14 | 19KB | `3ca374e7` |
| [MT/MQL5/Include/Controls/Panel.mqh](MT/MQL5/Include/Controls/Panel.mqh) |  |  | 2026-04-14 | 5KB | `836869ed` |
| [MT/MQL5/Include/Controls/Picture.mqh](MT/MQL5/Include/Controls/Picture.mqh) |  |  | 2026-04-14 | 5KB | `5e62233e` |
| [MT/MQL5/Include/Controls/RadioButton.mqh](MT/MQL5/Include/Controls/RadioButton.mqh) |  |  | 2026-04-14 | 6KB | `5537db3e` |
| [MT/MQL5/Include/Controls/RadioGroup.mqh](MT/MQL5/Include/Controls/RadioGroup.mqh) |  |  | 2026-04-14 | 13KB | `13d3d9bc` |
| [MT/MQL5/Include/Controls/Rect.mqh](MT/MQL5/Include/Controls/Rect.mqh) |  |  | 2026-04-14 | 10KB | `c0b73dc8` |
| [MT/MQL5/Include/Controls/Scrolls.mqh](MT/MQL5/Include/Controls/Scrolls.mqh) |  |  | 2026-04-14 | 26KB | `18fb49e5` |
| [MT/MQL5/Include/Controls/SpinEdit.mqh](MT/MQL5/Include/Controls/SpinEdit.mqh) |  |  | 2026-04-14 | 10KB | `1e7dded7` |
| [MT/MQL5/Include/Controls/Wnd.mqh](MT/MQL5/Include/Controls/Wnd.mqh) |  |  | 2026-04-14 | 29KB | `0c5fa8a9` |
| [MT/MQL5/Include/Controls/WndClient.mqh](MT/MQL5/Include/Controls/WndClient.mqh) |  |  | 2026-04-14 | 11KB | `25e7cdee` |
| [MT/MQL5/Include/Controls/WndContainer.mqh](MT/MQL5/Include/Controls/WndContainer.mqh) |  |  | 2026-04-14 | 15KB | `e5d88b28` |
| [MT/MQL5/Include/Controls/WndObj.mqh](MT/MQL5/Include/Controls/WndObj.mqh) |  |  | 2026-04-14 | 10KB | `79eb339d` |
| [MT/MQL5/Include/ERRORS.mqh](MT/MQL5/Include/ERRORS.mqh) |  |  | 2026-04-14 | 22B | `f437293a` |
| [MT/MQL5/Include/ERRORs.mqh](MT/MQL5/Include/ERRORs.mqh) |  |  | 2026-04-14 | 20KB | `3a30c213` |
| [MT/MQL5/Include/Expert/Expert.mqh](MT/MQL5/Include/Expert/Expert.mqh) |  |  | 2026-04-14 | 119KB | `667e739c` |
| [MT/MQL5/Include/Expert/ExpertBase.mqh](MT/MQL5/Include/Expert/ExpertBase.mqh) |  |  | 2026-04-14 | 26KB | `15d5fae3` |
| [MT/MQL5/Include/Expert/ExpertMoney.mqh](MT/MQL5/Include/Expert/ExpertMoney.mqh) |  |  | 2026-04-14 | 4KB | `9e6d6c11` |
| [MT/MQL5/Include/Expert/ExpertSignal.mqh](MT/MQL5/Include/Expert/ExpertSignal.mqh) |  |  | 2026-04-14 | 19KB | `b7a7ad81` |
| [MT/MQL5/Include/Expert/ExpertTrade.mqh](MT/MQL5/Include/Expert/ExpertTrade.mqh) |  |  | 2026-04-14 | 6KB | `b2b0f317` |
| [MT/MQL5/Include/Expert/ExpertTrailing.mqh](MT/MQL5/Include/Expert/ExpertTrailing.mqh) |  |  | 2026-04-14 | 1KB | `66a3a25d` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh) |  |  | 2026-04-14 | 3KB | `62d53ce2` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh) |  |  | 2026-04-14 | 3KB | `f8a1fe72` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh) |  |  | 2026-04-14 | 4KB | `38b6869e` |
| [MT/MQL5/Include/Expert/Money/MoneyNone.mqh](MT/MQL5/Include/Expert/Money/MoneyNone.mqh) |  |  | 2026-04-14 | 3KB | `b866ac59` |
| [MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh](MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh) |  |  | 2026-04-14 | 6KB | `22c850e8` |
| [MT/MQL5/Include/Expert/Signal/SignalAC.mqh](MT/MQL5/Include/Expert/Signal/SignalAC.mqh) |  |  | 2026-04-14 | 7KB | `c3fe7a79` |
| [MT/MQL5/Include/Expert/Signal/SignalAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalAMA.mqh) |  |  | 2026-04-14 | 12KB | `a5bbc59b` |
| [MT/MQL5/Include/Expert/Signal/SignalAO.mqh](MT/MQL5/Include/Expert/Signal/SignalAO.mqh) |  |  | 2026-04-14 | 13KB | `cadb934f` |
| [MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh) |  |  | 2026-04-14 | 11KB | `0a9fdc1f` |
| [MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh) |  |  | 2026-04-14 | 11KB | `9b6f9b73` |
| [MT/MQL5/Include/Expert/Signal/SignalCCI.mqh](MT/MQL5/Include/Expert/Signal/SignalCCI.mqh) |  |  | 2026-04-14 | 17KB | `8b02f15b` |
| [MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh) |  |  | 2026-04-14 | 11KB | `27a1b1b3` |
| [MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh](MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh) |  |  | 2026-04-14 | 16KB | `28378510` |
| [MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh](MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh) |  |  | 2026-04-14 | 9KB | `07c314dc` |
| [MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh) |  |  | 2026-04-14 | 11KB | `cc3ea8eb` |
| [MT/MQL5/Include/Expert/Signal/SignalITF.mqh](MT/MQL5/Include/Expert/Signal/SignalITF.mqh) |  |  | 2026-04-14 | 4KB | `0991d92b` |
| [MT/MQL5/Include/Expert/Signal/SignalMA.mqh](MT/MQL5/Include/Expert/Signal/SignalMA.mqh) |  |  | 2026-04-14 | 11KB | `51878396` |
| [MT/MQL5/Include/Expert/Signal/SignalMACD.mqh](MT/MQL5/Include/Expert/Signal/SignalMACD.mqh) |  |  | 2026-04-14 | 19KB | `6794035e` |
| [MT/MQL5/Include/Expert/Signal/SignalRSI.mqh](MT/MQL5/Include/Expert/Signal/SignalRSI.mqh) |  |  | 2026-04-14 | 18KB | `536ef112` |
| [MT/MQL5/Include/Expert/Signal/SignalRVI.mqh](MT/MQL5/Include/Expert/Signal/SignalRVI.mqh) |  |  | 2026-04-14 | 7KB | `89af5171` |
| [MT/MQL5/Include/Expert/Signal/SignalSAR.mqh](MT/MQL5/Include/Expert/Signal/SignalSAR.mqh) |  |  | 2026-04-14 | 7KB | `b84730ef` |
| [MT/MQL5/Include/Expert/Signal/SignalStoch.mqh](MT/MQL5/Include/Expert/Signal/SignalStoch.mqh) |  |  | 2026-04-14 | 19KB | `6cff6dd9` |
| [MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh) |  |  | 2026-04-14 | 11KB | `e8258b51` |
| [MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh](MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh) |  |  | 2026-04-14 | 17KB | `39e3f752` |
| [MT/MQL5/Include/Expert/Signal/SignalWPR.mqh](MT/MQL5/Include/Expert/Signal/SignalWPR.mqh) |  |  | 2026-04-14 | 16KB | `78fc2800` |
| [MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh](MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh) |  |  | 2026-04-14 | 5KB | `39c49839` |
| [MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh](MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh) |  |  | 2026-04-14 | 6KB | `a11d5980` |
| [MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh](MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh) |  |  | 2026-04-14 | 2KB | `bbdc0191` |
| [MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh](MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh) |  |  | 2026-04-14 | 5KB | `b73d3930` |
| [MT/MQL5/Include/FUNCTIONS.mqh](MT/MQL5/Include/FUNCTIONS.mqh) |  |  | 2026-04-14 | 15KB | `b3fce0c5` |
| [MT/MQL5/Include/Files/File.mqh](MT/MQL5/Include/Files/File.mqh) |  |  | 2026-04-14 | 11KB | `9b8c6449` |
| [MT/MQL5/Include/Files/FileBMP.mqh](MT/MQL5/Include/Files/FileBMP.mqh) |  |  | 2026-04-14 | 6KB | `5827c2f4` |
| [MT/MQL5/Include/Files/FileBin.mqh](MT/MQL5/Include/Files/FileBin.mqh) |  |  | 2026-04-14 | 20KB | `916879d9` |
| [MT/MQL5/Include/Files/FilePipe.mqh](MT/MQL5/Include/Files/FilePipe.mqh) |  |  | 2026-04-14 | 12KB | `197bd514` |
| [MT/MQL5/Include/Files/FileTxt.mqh](MT/MQL5/Include/Files/FileTxt.mqh) |  |  | 2026-04-14 | 2KB | `14f5dff2` |
| [MT/MQL5/Include/Generic/ArrayList.mqh](MT/MQL5/Include/Generic/ArrayList.mqh) |  |  | 2026-04-14 | 49KB | `b840b4bc` |
| [MT/MQL5/Include/Generic/HashMap.mqh](MT/MQL5/Include/Generic/HashMap.mqh) |  |  | 2026-04-14 | 25KB | `e22edcd0` |
| [MT/MQL5/Include/Generic/HashSet.mqh](MT/MQL5/Include/Generic/HashSet.mqh) |  |  | 2026-04-14 | 36KB | `d38ceded` |
| [MT/MQL5/Include/Generic/Interfaces/ICollection.mqh](MT/MQL5/Include/Generic/Interfaces/ICollection.mqh) |  |  | 2026-04-14 | 1KB | `402ea83c` |
| [MT/MQL5/Include/Generic/Interfaces/IComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IComparable.mqh) |  |  | 2026-04-14 | 1KB | `aa814da7` |
| [MT/MQL5/Include/Generic/Interfaces/IComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IComparer.mqh) |  |  | 2026-04-14 | 998B | `0cf6f120` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh) |  |  | 2026-04-14 | 1012B | `4979c4c7` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh) |  |  | 2026-04-14 | 1KB | `7e8c86a3` |
| [MT/MQL5/Include/Generic/Interfaces/IList.mqh](MT/MQL5/Include/Generic/Interfaces/IList.mqh) |  |  | 2026-04-14 | 1KB | `e5e9586d` |
| [MT/MQL5/Include/Generic/Interfaces/IMap.mqh](MT/MQL5/Include/Generic/Interfaces/IMap.mqh) |  |  | 2026-04-14 | 1KB | `303da59f` |
| [MT/MQL5/Include/Generic/Interfaces/ISet.mqh](MT/MQL5/Include/Generic/Interfaces/ISet.mqh) |  |  | 2026-04-14 | 1KB | `15eaf0e1` |
| [MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh](MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh) |  |  | 2026-04-14 | 4KB | `4d708d05` |
| [MT/MQL5/Include/Generic/Internal/CompareFunction.mqh](MT/MQL5/Include/Generic/Internal/CompareFunction.mqh) |  |  | 2026-04-14 | 7KB | `b5a08f39` |
| [MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh) |  |  | 2026-04-14 | 1KB | `2f430ea9` |
| [MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh) |  |  | 2026-04-14 | 1KB | `ea37b258` |
| [MT/MQL5/Include/Generic/Internal/EqualFunction.mqh](MT/MQL5/Include/Generic/Internal/EqualFunction.mqh) |  |  | 2026-04-14 | 1KB | `47e2bc02` |
| [MT/MQL5/Include/Generic/Internal/HashFunction.mqh](MT/MQL5/Include/Generic/Internal/HashFunction.mqh) |  |  | 2026-04-14 | 7KB | `87c69022` |
| [MT/MQL5/Include/Generic/Internal/Introsort.mqh](MT/MQL5/Include/Generic/Internal/Introsort.mqh) |  |  | 2026-04-14 | 8KB | `2bd4b00f` |
| [MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh](MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh) |  |  | 2026-04-14 | 3KB | `6d9e6603` |
| [MT/MQL5/Include/Generic/LinkedList.mqh](MT/MQL5/Include/Generic/LinkedList.mqh) |  |  | 2026-04-14 | 20KB | `1cdd7bab` |
| [MT/MQL5/Include/Generic/Queue.mqh](MT/MQL5/Include/Generic/Queue.mqh) |  |  | 2026-04-14 | 29KB | `1313ea7c` |
| [MT/MQL5/Include/Generic/RedBlackTree.mqh](MT/MQL5/Include/Generic/RedBlackTree.mqh) |  |  | 2026-04-14 | 73KB | `3b568c0d` |
| [MT/MQL5/Include/Generic/SortedMap.mqh](MT/MQL5/Include/Generic/SortedMap.mqh) |  |  | 2026-04-14 | 14KB | `5745fcdf` |
| [MT/MQL5/Include/Generic/SortedSet.mqh](MT/MQL5/Include/Generic/SortedSet.mqh) |  |  | 2026-04-14 | 24KB | `0efbc013` |
| [MT/MQL5/Include/Generic/Stack.mqh](MT/MQL5/Include/Generic/Stack.mqh) |  |  | 2026-04-14 | 8KB | `39c47e97` |
| [MT/MQL5/Include/Graphics/Axis.mqh](MT/MQL5/Include/Graphics/Axis.mqh) |  |  | 2026-04-14 | 12KB | `30e582f4` |
| [MT/MQL5/Include/Graphics/ColorGenerator.mqh](MT/MQL5/Include/Graphics/ColorGenerator.mqh) |  |  | 2026-04-14 | 3KB | `204f3a70` |
| [MT/MQL5/Include/Graphics/Curve.mqh](MT/MQL5/Include/Graphics/Curve.mqh) |  |  | 2026-04-14 | 22KB | `5b3764a4` |
| [MT/MQL5/Include/Graphics/Graphic.mqh](MT/MQL5/Include/Graphics/Graphic.mqh) |  |  | 2026-04-14 | 169KB | `0cca00f7` |
| [MT/MQL5/Include/INPUT.mqh](MT/MQL5/Include/INPUT.mqh) |  |  | 2026-04-14 | 22KB | `477b69ca` |
| [MT/MQL5/Include/Indicators/BillWilliams.mqh](MT/MQL5/Include/Indicators/BillWilliams.mqh) |  |  | 2026-04-14 | 32KB | `f57a6107` |
| [MT/MQL5/Include/Indicators/Custom.mqh](MT/MQL5/Include/Indicators/Custom.mqh) |  |  | 2026-04-14 | 7KB | `5e9fbee8` |
| [MT/MQL5/Include/Indicators/Indicator.mqh](MT/MQL5/Include/Indicators/Indicator.mqh) |  |  | 2026-04-14 | 19KB | `1e663d5c` |
| [MT/MQL5/Include/Indicators/Indicators.mqh](MT/MQL5/Include/Indicators/Indicators.mqh) |  |  | 2026-04-14 | 11KB | `e8cd4f31` |
| [MT/MQL5/Include/Indicators/Oscilators.mqh](MT/MQL5/Include/Indicators/Oscilators.mqh) |  |  | 2026-04-14 | 72KB | `18221239` |
| [MT/MQL5/Include/Indicators/Series.mqh](MT/MQL5/Include/Indicators/Series.mqh) |  |  | 2026-04-14 | 12KB | `e0040d48` |
| [MT/MQL5/Include/Indicators/TimeSeries.mqh](MT/MQL5/Include/Indicators/TimeSeries.mqh) |  |  | 2026-04-14 | 61KB | `9aa20382` |
| [MT/MQL5/Include/Indicators/Trend.mqh](MT/MQL5/Include/Indicators/Trend.mqh) |  |  | 2026-04-14 | 72KB | `eb97c7df` |
| [MT/MQL5/Include/Indicators/Volumes.mqh](MT/MQL5/Include/Indicators/Volumes.mqh) |  |  | 2026-04-14 | 17KB | `81921db6` |
| [MT/MQL5/Include/MAIN.mqh](MT/MQL5/Include/MAIN.mqh) |  |  | 2026-04-14 | 10KB | `53cf2ce0` |
| [MT/MQL5/Include/MM.mqh](MT/MQL5/Include/MM.mqh) |  |  | 2026-04-14 | 10KB | `8b02452d` |
| [MT/MQL5/Include/MQL4Compat.mqh](MT/MQL5/Include/MQL4Compat.mqh) |  |  | 2026-04-14 | 28KB | `b26d5ab4` |
| [MT/MQL5/Include/Math/Alglib/alglib.mqh](MT/MQL5/Include/Math/Alglib/alglib.mqh) |  |  | 2026-04-14 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/alglibinternal.mqh](MT/MQL5/Include/Math/Alglib/alglibinternal.mqh) |  |  | 2026-04-14 | 579KB | `175c1183` |
| [MT/MQL5/Include/Math/Alglib/alglibmisc.mqh](MT/MQL5/Include/Math/Alglib/alglibmisc.mqh) |  |  | 2026-04-14 | 119KB | `7466a12d` |
| [MT/MQL5/Include/Math/Alglib/ap.mqh](MT/MQL5/Include/Math/Alglib/ap.mqh) |  |  | 2026-04-14 | 89KB | `a7e4677f` |
| [MT/MQL5/Include/Math/Alglib/arrayresize.mqh](MT/MQL5/Include/Math/Alglib/arrayresize.mqh) |  |  | 2026-04-14 | 3KB | `e64b72cb` |
| [MT/MQL5/Include/Math/Alglib/bitconvert.mqh](MT/MQL5/Include/Math/Alglib/bitconvert.mqh) |  |  | 2026-04-14 | 13KB | `c9dffd4e` |
| [MT/MQL5/Include/Math/Alglib/dataanalysis.mqh](MT/MQL5/Include/Math/Alglib/dataanalysis.mqh) |  |  | 2026-04-14 | 1MB | `596bc4ac` |
| [MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh](MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh) |  |  | 2026-04-14 | 21KB | `ebc422fa` |
| [MT/MQL5/Include/Math/Alglib/diffequations.mqh](MT/MQL5/Include/Math/Alglib/diffequations.mqh) |  |  | 2026-04-14 | 32KB | `e612f10b` |
| [MT/MQL5/Include/Math/Alglib/fasttransforms.mqh](MT/MQL5/Include/Math/Alglib/fasttransforms.mqh) |  |  | 2026-04-14 | 92KB | `f6bbf7c2` |
| [MT/MQL5/Include/Math/Alglib/integration.mqh](MT/MQL5/Include/Math/Alglib/integration.mqh) |  |  | 2026-04-14 | 116KB | `f8600aaa` |
| [MT/MQL5/Include/Math/Alglib/interpolation.mqh](MT/MQL5/Include/Math/Alglib/interpolation.mqh) |  |  | 2026-04-14 | 1MB | `43be4546` |
| [MT/MQL5/Include/Math/Alglib/linalg.mqh](MT/MQL5/Include/Math/Alglib/linalg.mqh) |  |  | 2026-04-14 | 1MB | `73b32040` |
| [MT/MQL5/Include/Math/Alglib/matrix.mqh](MT/MQL5/Include/Math/Alglib/matrix.mqh) |  |  | 2026-04-14 | 45KB | `52f0963f` |
| [MT/MQL5/Include/Math/Alglib/optimization.mqh](MT/MQL5/Include/Math/Alglib/optimization.mqh) |  |  | 2026-04-14 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/solvers.mqh](MT/MQL5/Include/Math/Alglib/solvers.mqh) |  |  | 2026-04-14 | 295KB | `cfe0276c` |
| [MT/MQL5/Include/Math/Alglib/specialfunctions.mqh](MT/MQL5/Include/Math/Alglib/specialfunctions.mqh) |  |  | 2026-04-14 | 235KB | `a4f6fa85` |
| [MT/MQL5/Include/Math/Alglib/statistics.mqh](MT/MQL5/Include/Math/Alglib/statistics.mqh) |  |  | 2026-04-14 | 407KB | `3156c1e5` |
| [MT/MQL5/Include/Math/Fuzzy/dictionary.mqh](MT/MQL5/Include/Math/Fuzzy/dictionary.mqh) |  |  | 2026-04-14 | 8KB | `5fc3e371` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh) |  |  | 2026-04-14 | 17KB | `2b675722` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh) |  |  | 2026-04-14 | 3KB | `b5744882` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh) |  |  | 2026-04-14 | 5KB | `c70f7f31` |
| [MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh) |  |  | 2026-04-14 | 11KB | `0c24ddb8` |
| [MT/MQL5/Include/Math/Fuzzy/helper.mqh](MT/MQL5/Include/Math/Fuzzy/helper.mqh) |  |  | 2026-04-14 | 7KB | `26906afe` |
| [MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh](MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh) |  |  | 2026-04-14 | 7KB | `981fa315` |
| [MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh) |  |  | 2026-04-14 | 22KB | `a4ff1a81` |
| [MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh](MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh) |  |  | 2026-04-14 | 43KB | `db1e7a2e` |
| [MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh](MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh) |  |  | 2026-04-14 | 36KB | `a32fa745` |
| [MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh) |  |  | 2026-04-14 | 13KB | `5502caaf` |
| [MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh](MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh) |  |  | 2026-04-14 | 10KB | `89b49ae6` |
| [MT/MQL5/Include/Math/Stat/Beta.mqh](MT/MQL5/Include/Math/Stat/Beta.mqh) |  |  | 2026-04-14 | 32KB | `9aef6db1` |
| [MT/MQL5/Include/Math/Stat/Binomial.mqh](MT/MQL5/Include/Math/Stat/Binomial.mqh) |  |  | 2026-04-14 | 34KB | `eb1604d4` |
| [MT/MQL5/Include/Math/Stat/Cauchy.mqh](MT/MQL5/Include/Math/Stat/Cauchy.mqh) |  |  | 2026-04-14 | 24KB | `2a5b994b` |
| [MT/MQL5/Include/Math/Stat/ChiSquare.mqh](MT/MQL5/Include/Math/Stat/ChiSquare.mqh) |  |  | 2026-04-14 | 24KB | `31d24602` |
| [MT/MQL5/Include/Math/Stat/Exponential.mqh](MT/MQL5/Include/Math/Stat/Exponential.mqh) |  |  | 2026-04-14 | 24KB | `f1846a90` |
| [MT/MQL5/Include/Math/Stat/F.mqh](MT/MQL5/Include/Math/Stat/F.mqh) |  |  | 2026-04-14 | 26KB | `9e90f69b` |
| [MT/MQL5/Include/Math/Stat/Gamma.mqh](MT/MQL5/Include/Math/Stat/Gamma.mqh) |  |  | 2026-04-14 | 31KB | `358ed8cd` |
| [MT/MQL5/Include/Math/Stat/Geometric.mqh](MT/MQL5/Include/Math/Stat/Geometric.mqh) |  |  | 2026-04-14 | 24KB | `031a2627` |
| [MT/MQL5/Include/Math/Stat/Hypergeometric.mqh](MT/MQL5/Include/Math/Stat/Hypergeometric.mqh) |  |  | 2026-04-14 | 34KB | `2208c6d3` |
| [MT/MQL5/Include/Math/Stat/Logistic.mqh](MT/MQL5/Include/Math/Stat/Logistic.mqh) |  |  | 2026-04-14 | 27KB | `6a74c8a4` |
| [MT/MQL5/Include/Math/Stat/Lognormal.mqh](MT/MQL5/Include/Math/Stat/Lognormal.mqh) |  |  | 2026-04-14 | 28KB | `ca8a59c4` |
| [MT/MQL5/Include/Math/Stat/Math.mqh](MT/MQL5/Include/Math/Stat/Math.mqh) |  |  | 2026-04-14 | 424KB | `65212111` |
| [MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh](MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh) |  |  | 2026-04-14 | 28KB | `27a3e21c` |
| [MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh](MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh) |  |  | 2026-04-14 | 40KB | `ce6d8685` |
| [MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh](MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh) |  |  | 2026-04-14 | 36KB | `96a70f8c` |
| [MT/MQL5/Include/Math/Stat/NoncentralF.mqh](MT/MQL5/Include/Math/Stat/NoncentralF.mqh) |  |  | 2026-04-14 | 34KB | `9990ce6c` |
| [MT/MQL5/Include/Math/Stat/NoncentralT.mqh](MT/MQL5/Include/Math/Stat/NoncentralT.mqh) |  |  | 2026-04-14 | 46KB | `9e154d87` |
| [MT/MQL5/Include/Math/Stat/Normal.mqh](MT/MQL5/Include/Math/Stat/Normal.mqh) |  |  | 2026-04-14 | 39KB | `21ffb41d` |
| [MT/MQL5/Include/Math/Stat/Poisson.mqh](MT/MQL5/Include/Math/Stat/Poisson.mqh) |  |  | 2026-04-14 | 31KB | `df71df52` |
| [MT/MQL5/Include/Math/Stat/Stat.mqh](MT/MQL5/Include/Math/Stat/Stat.mqh) |  |  | 2026-04-14 | 1KB | `c8af779d` |
| [MT/MQL5/Include/Math/Stat/T.mqh](MT/MQL5/Include/Math/Stat/T.mqh) |  |  | 2026-04-14 | 27KB | `d3dbb617` |
| [MT/MQL5/Include/Math/Stat/Uniform.mqh](MT/MQL5/Include/Math/Stat/Uniform.mqh) |  |  | 2026-04-14 | 25KB | `8de48345` |
| [MT/MQL5/Include/Math/Stat/Weibull.mqh](MT/MQL5/Include/Math/Stat/Weibull.mqh) |  |  | 2026-04-14 | 26KB | `ff94f29f` |
| [MT/MQL5/Include/ORDERS.mqh](MT/MQL5/Include/ORDERS.mqh) |  |  | 2026-04-14 | 40KB | `6655a760` |
| [MT/MQL5/Include/OUTPUT.mqh](MT/MQL5/Include/OUTPUT.mqh) |  |  | 2026-04-14 | 18KB | `5a14ae04` |
| [MT/MQL5/Include/OpenCL/OpenCL.mqh](MT/MQL5/Include/OpenCL/OpenCL.mqh) |  |  | 2026-04-14 | 27KB | `a82fa081` |
| [MT/MQL5/Include/SERVICE.mqh](MT/MQL5/Include/SERVICE.mqh) |  |  | 2026-04-14 | 80KB | `aced0492` |
| [MT/MQL5/Include/Strings/String.mqh](MT/MQL5/Include/Strings/String.mqh) |  |  | 2026-04-14 | 13KB | `adbde208` |
| [MT/MQL5/Include/Tools/DateTime.mqh](MT/MQL5/Include/Tools/DateTime.mqh) |  |  | 2026-04-14 | 17KB | `e06f30f0` |
| [MT/MQL5/Include/Trade/AccountInfo.mqh](MT/MQL5/Include/Trade/AccountInfo.mqh) |  |  | 2026-04-14 | 17KB | `336acd5d` |
| [MT/MQL5/Include/Trade/DealInfo.mqh](MT/MQL5/Include/Trade/DealInfo.mqh) |  |  | 2026-04-14 | 15KB | `5f444466` |
| [MT/MQL5/Include/Trade/HistoryOrderInfo.mqh](MT/MQL5/Include/Trade/HistoryOrderInfo.mqh) |  |  | 2026-04-14 | 19KB | `3c45a5f3` |
| [MT/MQL5/Include/Trade/OrderInfo.mqh](MT/MQL5/Include/Trade/OrderInfo.mqh) |  |  | 2026-04-14 | 21KB | `c7977cef` |
| [MT/MQL5/Include/Trade/PositionInfo.mqh](MT/MQL5/Include/Trade/PositionInfo.mqh) |  |  | 2026-04-14 | 15KB | `8f85983c` |
| [MT/MQL5/Include/Trade/SymbolInfo.mqh](MT/MQL5/Include/Trade/SymbolInfo.mqh) |  |  | 2026-04-14 | 35KB | `bb2f2760` |
| [MT/MQL5/Include/Trade/TerminalInfo.mqh](MT/MQL5/Include/Trade/TerminalInfo.mqh) |  |  | 2026-04-14 | 10KB | `db1d371d` |
| [MT/MQL5/Include/Trade/Trade.mqh](MT/MQL5/Include/Trade/Trade.mqh) |  |  | 2026-04-14 | 67KB | `ebefad3b` |
| [MT/MQL5/Include/WinAPI/errhandlingapi.mqh](MT/MQL5/Include/WinAPI/errhandlingapi.mqh) |  |  | 2026-04-14 | 1KB | `9c6abbb5` |
| [MT/MQL5/Include/WinAPI/fileapi.mqh](MT/MQL5/Include/WinAPI/fileapi.mqh) |  |  | 2026-04-14 | 9KB | `ce8862f9` |
| [MT/MQL5/Include/WinAPI/handleapi.mqh](MT/MQL5/Include/WinAPI/handleapi.mqh) |  |  | 2026-04-14 | 1KB | `72389e0e` |
| [MT/MQL5/Include/WinAPI/libloaderapi.mqh](MT/MQL5/Include/WinAPI/libloaderapi.mqh) |  |  | 2026-04-14 | 2KB | `fbe9c927` |
| [MT/MQL5/Include/WinAPI/memoryapi.mqh](MT/MQL5/Include/WinAPI/memoryapi.mqh) |  |  | 2026-04-14 | 5KB | `115d0c9e` |
| [MT/MQL5/Include/WinAPI/processenv.mqh](MT/MQL5/Include/WinAPI/processenv.mqh) |  |  | 2026-04-14 | 1KB | `7788d30f` |
| [MT/MQL5/Include/WinAPI/processthreadsapi.mqh](MT/MQL5/Include/WinAPI/processthreadsapi.mqh) |  |  | 2026-04-14 | 10KB | `5d2c97c4` |
| [MT/MQL5/Include/WinAPI/securitybaseapi.mqh](MT/MQL5/Include/WinAPI/securitybaseapi.mqh) |  |  | 2026-04-14 | 16KB | `a8296031` |
| [MT/MQL5/Include/WinAPI/sysinfoapi.mqh](MT/MQL5/Include/WinAPI/sysinfoapi.mqh) |  |  | 2026-04-14 | 4KB | `f1e35723` |
| [MT/MQL5/Include/WinAPI/winapi.mqh](MT/MQL5/Include/WinAPI/winapi.mqh) |  |  | 2026-04-14 | 827B | `18ecf395` |
| [MT/MQL5/Include/WinAPI/winbase.mqh](MT/MQL5/Include/WinAPI/winbase.mqh) |  |  | 2026-04-14 | 43KB | `80b349f7` |
| [MT/MQL5/Include/WinAPI/windef.mqh](MT/MQL5/Include/WinAPI/windef.mqh) |  |  | 2026-04-14 | 8KB | `b3d4d5b1` |
| [MT/MQL5/Include/WinAPI/wingdi.mqh](MT/MQL5/Include/WinAPI/wingdi.mqh) |  |  | 2026-04-14 | 63KB | `000f20a9` |
| [MT/MQL5/Include/WinAPI/winnt.mqh](MT/MQL5/Include/WinAPI/winnt.mqh) |  |  | 2026-04-14 | 95KB | `0e776dbe` |
| [MT/MQL5/Include/WinAPI/winreg.mqh](MT/MQL5/Include/WinAPI/winreg.mqh) |  |  | 2026-04-14 | 5KB | `3681c95b` |
| [MT/MQL5/Include/WinAPI/winuser.mqh](MT/MQL5/Include/WinAPI/winuser.mqh) |  |  | 2026-04-14 | 81KB | `0a662398` |
| [MT/MQL5/Include/head_PIC.mqh](MT/MQL5/Include/head_PIC.mqh) |  |  | 2026-04-14 | 9KB | `356c8df3` |
| [MT/MQL5/Include/iGRAPH.mqh](MT/MQL5/Include/iGRAPH.mqh) |  |  | 2026-04-14 | 39KB | `f5abe888` |
| [MT/MQL5/Include/lib_ATR.mqh](MT/MQL5/Include/lib_ATR.mqh) |  |  | 2026-04-14 | 2KB | `dcc5b590` |
| [MT/MQL5/Include/lib_Flat.mqh](MT/MQL5/Include/lib_Flat.mqh) |  |  | 2026-04-14 | 13KB | `4536cf5c` |
| [MT/MQL5/Include/lib_ML_Signal.mqh](MT/MQL5/Include/lib_ML_Signal.mqh) |  |  | 2026-04-14 | 14KB | `996e3367` |
| [MT/MQL5/Include/lib_ML_Signal_TB.mqh](MT/MQL5/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-04-14 | 8KB | `86f9658b` |
| [MT/MQL5/Include/lib_PIC.mqh](MT/MQL5/Include/lib_PIC.mqh) |  |  | 2026-04-14 | 56KB | `cc8e0ac9` |
| [MT/MQL5/Include/stderror.mqh](MT/MQL5/Include/stderror.mqh) |  |  | 2026-04-14 | 9KB | `e8590cbe` |
| [MT/MQL5/Include/stdlib.mqh](MT/MQL5/Include/stdlib.mqh) |  |  | 2026-04-14 | 712B | `b86b17a9` |

## Wiki

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [wiki/LLM Wiki_method.md](wiki/LLM Wiki_method.md) |  | 2026-04-14 | 11KB | `68a888b4` |
| [wiki/concepts/signal-archetypes.md](wiki/concepts/signal-archetypes.md) |  | 2026-04-14 | 3KB | `01af7dbd` |
| [wiki/index.md](wiki/index.md) |  | 2026-04-14 | 1KB | `694809a1` |
| [wiki/log.md](wiki/log.md) |  | 2026-04-14 | 7KB | `bba40be0` |
| [wiki/research/execution-tracks.md](wiki/research/execution-tracks.md) |  | 2026-04-14 | 27KB | `be26953a` |
| [wiki/research/signal-quality-research.md](wiki/research/signal-quality-research.md) |  | 2026-04-14 | 8KB | `a5355801` |
| [wiki/wiki.py](wiki/wiki.py) |  | 2026-04-14 | 18KB | `4bcfb243` |

## Agent Config

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.claude/memory/MEMORY.md](.claude/memory/MEMORY.md) |  | 2026-04-14 | 694B | `ca8a831e` |
| [.claude/memory/feedback_cyclic_encoding.md](.claude/memory/feedback_cyclic_encoding.md) |  | 2026-04-14 | 1KB | `7e05fc7c` |
| [.claude/memory/feedback_ml_approach.md](.claude/memory/feedback_ml_approach.md) |  | 2026-04-14 | 2KB | `1480e999` |
| [.claude/memory/feedback_no_auto_commit.md](.claude/memory/feedback_no_auto_commit.md) |  | 2026-04-14 | 752B | `e07d0571` |
| [.claude/memory/feedback_russian_reports.md](.claude/memory/feedback_russian_reports.md) |  | 2026-04-14 | 1KB | `e4464dc5` |
| [.claude/memory/project_ml_status.md](.claude/memory/project_ml_status.md) |  | 2026-04-14 | 2KB | `07fbf165` |
| [.claude/memory/user_profile.md](.claude/memory/user_profile.md) |  | 2026-04-14 | 890B | `8ca314d1` |
| [.claude/settings.json](.claude/settings.json) |  | 2026-04-14 | 526B | `2e76b9b8` |
| [.claude/skills/brainstorming/SKILL.md](.claude/skills/brainstorming/SKILL.md) |  | 2026-04-14 | 10KB | `3f82fad8` |
| [.claude/skills/brainstorming/spec-document-reviewer-prompt.md](.claude/skills/brainstorming/spec-document-reviewer-prompt.md) |  | 2026-04-14 | 1KB | `06b0277a` |
| [.claude/skills/brainstorming/visual-companion.md](.claude/skills/brainstorming/visual-companion.md) |  | 2026-04-14 | 11KB | `37305635` |
| [.claude/skills/dispatching-parallel-agents/SKILL.md](.claude/skills/dispatching-parallel-agents/SKILL.md) |  | 2026-04-14 | 6KB | `645864ea` |
| [.claude/skills/executing-plans/SKILL.md](.claude/skills/executing-plans/SKILL.md) |  | 2026-04-14 | 2KB | `1eedec6a` |
| [.claude/skills/finishing-a-development-branch/SKILL.md](.claude/skills/finishing-a-development-branch/SKILL.md) |  | 2026-04-14 | 4KB | `5068e5c2` |
| [.claude/skills/receiving-code-review/SKILL.md](.claude/skills/receiving-code-review/SKILL.md) |  | 2026-04-14 | 6KB | `7bdb2c2c` |
| [.claude/skills/requesting-code-review/SKILL.md](.claude/skills/requesting-code-review/SKILL.md) |  | 2026-04-14 | 2KB | `03ae853d` |
| [.claude/skills/requesting-code-review/code-reviewer.md](.claude/skills/requesting-code-review/code-reviewer.md) |  | 2026-04-14 | 3KB | `a17ab05f` |
| [.claude/skills/subagent-driven-development/SKILL.md](.claude/skills/subagent-driven-development/SKILL.md) |  | 2026-04-14 | 11KB | `0a35f71a` |
| [.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md](.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md) |  | 2026-04-14 | 1KB | `923a1c03` |
| [.claude/skills/subagent-driven-development/implementer-prompt.md](.claude/skills/subagent-driven-development/implementer-prompt.md) |  | 2026-04-14 | 4KB | `4c6c977c` |
| [.claude/skills/subagent-driven-development/spec-reviewer-prompt.md](.claude/skills/subagent-driven-development/spec-reviewer-prompt.md) |  | 2026-04-14 | 1KB | `70330453` |
| [.claude/skills/systematic-debugging/CREATION-LOG.md](.claude/skills/systematic-debugging/CREATION-LOG.md) |  | 2026-04-14 | 4KB | `c0a1bd0d` |
| [.claude/skills/systematic-debugging/SKILL.md](.claude/skills/systematic-debugging/SKILL.md) |  | 2026-04-14 | 9KB | `05a9d191` |
| [.claude/skills/systematic-debugging/condition-based-waiting.md](.claude/skills/systematic-debugging/condition-based-waiting.md) |  | 2026-04-14 | 3KB | `84c01c63` |
| [.claude/skills/systematic-debugging/defense-in-depth.md](.claude/skills/systematic-debugging/defense-in-depth.md) |  | 2026-04-14 | 3KB | `f1213004` |
| [.claude/skills/systematic-debugging/root-cause-tracing.md](.claude/skills/systematic-debugging/root-cause-tracing.md) |  | 2026-04-14 | 5KB | `aa760aed` |
| [.claude/skills/systematic-debugging/test-academic.md](.claude/skills/systematic-debugging/test-academic.md) |  | 2026-04-14 | 653B | `f93a550e` |
| [.claude/skills/systematic-debugging/test-pressure-1.md](.claude/skills/systematic-debugging/test-pressure-1.md) |  | 2026-04-14 | 1KB | `3fbf9df1` |
| [.claude/skills/systematic-debugging/test-pressure-2.md](.claude/skills/systematic-debugging/test-pressure-2.md) |  | 2026-04-14 | 2KB | `dc10de1a` |
| [.claude/skills/systematic-debugging/test-pressure-3.md](.claude/skills/systematic-debugging/test-pressure-3.md) |  | 2026-04-14 | 2KB | `4c1b5df1` |
| [.claude/skills/test-driven-development/SKILL.md](.claude/skills/test-driven-development/SKILL.md) |  | 2026-04-14 | 9KB | `847d3947` |
| [.claude/skills/test-driven-development/testing-anti-patterns.md](.claude/skills/test-driven-development/testing-anti-patterns.md) |  | 2026-04-14 | 8KB | `70d9ec22` |
| [.claude/skills/using-git-worktrees/SKILL.md](.claude/skills/using-git-worktrees/SKILL.md) |  | 2026-04-14 | 5KB | `fb693c90` |
| [.claude/skills/using-superpowers/SKILL.md](.claude/skills/using-superpowers/SKILL.md) |  | 2026-04-14 | 5KB | `ecc31260` |
| [.claude/skills/using-superpowers/references/codex-tools.md](.claude/skills/using-superpowers/references/codex-tools.md) |  | 2026-04-14 | 960B | `70fe0aeb` |
| [.claude/skills/using-superpowers/references/gemini-tools.md](.claude/skills/using-superpowers/references/gemini-tools.md) |  | 2026-04-14 | 1KB | `5f43b981` |
| [.claude/skills/verification-before-completion/SKILL.md](.claude/skills/verification-before-completion/SKILL.md) |  | 2026-04-14 | 4KB | `830cfbe3` |
| [.claude/skills/writing-plans/SKILL.md](.claude/skills/writing-plans/SKILL.md) |  | 2026-04-14 | 5KB | `26d892e5` |
| [.claude/skills/writing-plans/plan-document-reviewer-prompt.md](.claude/skills/writing-plans/plan-document-reviewer-prompt.md) |  | 2026-04-14 | 1KB | `412ec6bb` |
| [.claude/skills/writing-skills/SKILL.md](.claude/skills/writing-skills/SKILL.md) |  | 2026-04-14 | 21KB | `5cfc05f1` |
| [.claude/skills/writing-skills/anthropic-best-practices.md](.claude/skills/writing-skills/anthropic-best-practices.md) |  | 2026-04-14 | 44KB | `95ea2856` |
| [.claude/skills/writing-skills/examples/CLAUDE_MD_TESTING.md](.claude/skills/writing-skills/examples/CLAUDE_MD_TESTING.md) |  | 2026-04-14 | 5KB | `9d292f89` |
| [.claude/skills/writing-skills/persuasion-principles.md](.claude/skills/writing-skills/persuasion-principles.md) |  | 2026-04-14 | 5KB | `672d4b80` |
| [.claude/skills/writing-skills/testing-skills-with-subagents.md](.claude/skills/writing-skills/testing-skills-with-subagents.md) |  | 2026-04-14 | 12KB | `24475f71` |
| [.codex/skills/csv-processing/SKILL.md](.codex/skills/csv-processing/SKILL.md) |  | 2026-04-14 | 2KB | `8081acc8` |
| [.codex/skills/jupyter-processing/SKILL.md](.codex/skills/jupyter-processing/SKILL.md) |  | 2026-04-14 | 3KB | `36c3f0e0` |
| [.codex/skills/rebuild-module-index/SKILL.md](.codex/skills/rebuild-module-index/SKILL.md) |  | 2026-04-14 | 2KB | `c47376c5` |
| [.codex/skills/stage-reporting/SKILL.md](.codex/skills/stage-reporting/SKILL.md) |  | 2026-04-14 | 4KB | `94d35eef` |
| [.codex/skills/update-docs-on-code-change/SKILL.md](.codex/skills/update-docs-on-code-change/SKILL.md) |  | 2026-04-14 | 3KB | `6960bb8e` |
| [.codex/skills/wiki/SKILL.md](.codex/skills/wiki/SKILL.md) |  | 2026-04-14 | 8KB | `7145a33d` |
| [.kilocode/mcp.json](.kilocode/mcp.json) |  | 2026-04-14 | 481B | `14bc1e7d` |
| [.kilocode/rules-architect/user_rules.md](.kilocode/rules-architect/user_rules.md) |  | 2026-04-14 | 1KB | `351b6484` |
| [.kilocode/rules-ask/user_rules.md](.kilocode/rules-ask/user_rules.md) |  | 2026-04-14 | 1KB | `351b6484` |
| [.kilocode/skills/csv-processing/SKILL.md](.kilocode/skills/csv-processing/SKILL.md) |  | 2026-04-14 | 2KB | `8081acc8` |
| [.kilocode/skills/jupyter-processing/SKILL.md](.kilocode/skills/jupyter-processing/SKILL.md) |  | 2026-04-14 | 3KB | `36c3f0e0` |
| [.kilocode/skills/rebuild-module-index/SKILL.md](.kilocode/skills/rebuild-module-index/SKILL.md) |  | 2026-04-14 | 2KB | `c47376c5` |
| [.kilocode/skills/update-docs-on-code-change/SKILL.md](.kilocode/skills/update-docs-on-code-change/SKILL.md) |  | 2026-04-14 | 3KB | `802a1668` |
| [.kilocode/skills/update-docs-on-code-change/references/file-mappings.md](.kilocode/skills/update-docs-on-code-change/references/file-mappings.md) |  | 2026-04-14 | 2KB | `ab7602fe` |
| [.kilocode/skills/update-docs-on-code-change/templates/file-headers.md](.kilocode/skills/update-docs-on-code-change/templates/file-headers.md) |  | 2026-04-14 | 4KB | `a7010b41` |

## Other

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.mcp.json](.mcp.json) |  | 2026-04-14 | 91B | `2ecc4de2` |

