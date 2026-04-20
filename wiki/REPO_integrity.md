# REPO Integrity Map — SoSimple
> Auto-generated 2026-04-20 08:45 UTC · git `47fba69`
> Refresh: `python wiki/wiki.py generate`  ·  Verify: `python wiki/wiki.py verify`

## Agent Access Protocol

1. Read this file first to get a project map (what exists, where, integrity hash).
2. Run `python wiki/wiki.py verify` to detect files changed since last index.
3. Navigate via paths in the tables; use `wiki/research/` and `wiki/concepts/` for synthesized knowledge.
4. After modifying significant files, run `generate` and commit `REPO_integrity.md`.

**Tracked**: 831 files  ·  **Commit**: `47fba69`  ·  **Generated**: 2026-04-20 08:45 UTC

## Root Docs

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [AGENTS.md](AGENTS.md) |  | 2026-04-19 | 10KB | `58a59f0e` |
| [CHANGELOG.md](CHANGELOG.md) |  | 2026-04-20 | 119KB | `295d7ebf` |
| [CLAUDE.md](CLAUDE.md) |  | 2026-04-18 | 5KB | `f0c0cdff` |
| [CONTEXT_HANDOFF.md](CONTEXT_HANDOFF.md) |  | 2026-04-20 | 20KB | `0a57348c` |
| [MODULE_INDEX.md](MODULE_INDEX.md) |  | 2026-04-20 | 24KB | `e98b6ecf` |
| [README.md](README.md) |  | 2026-04-09 | 969B | `4fc82a41` |

## Documentation

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам | 2026-04-20 | 24KB | `47f6ffc5` |
| [docs/ML/baseline_experiments.py.md](docs/ML/baseline_experiments.py.md) |  | 2026-04-01 | 2KB | `8dc50028` |
| [docs/ML/benchmark_execution_policy_v2.py.md](docs/ML/benchmark_execution_policy_v2.py.md) | Benchmark вариантов выхода для готовых ML-сигналов | 2026-04-19 | 3KB | `0aaec907` |
| [docs/ML/benchmark_take_skip_lib_pic_selection.py.md](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | Внешний отбор `take_skip_v2` по признакам `lib_PIC` | 2026-04-20 | 2KB | `085cc039` |
| [docs/ML/conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы | 2026-04-01 | 5KB | `dca1ea47` |
| [docs/ML/feature_bank_comparison_diagnostics.py.md](docs/ML/feature_bank_comparison_diagnostics.py.md) | Сравнение baseline/geometry/path feature-bank вариантов | 2026-04-20 | 2KB | `5bfce017` |
| [docs/ML/feature_importance_diagnostics.py.md](docs/ML/feature_importance_diagnostics.py.md) | Диагностика важности групп текущих fractal-признаков | 2026-04-20 | 2KB | `fd76dcaf` |
| [docs/ML/lib_pic_feature_profiles.py.md](docs/ML/lib_pic_feature_profiles.py.md) | Единая сборка профилей признаков `lib_PIC` | 2026-04-20 | 2KB | `988ba17b` |
| [docs/ML/lib_pic_geometry_feature_bank.py.md](docs/ML/lib_pic_geometry_feature_bank.py.md) | Производные признаки геометрии уровней `lib_PIC` | 2026-04-20 | 3KB | `1da45c79` |
| [docs/ML/lib_pic_path_reaction_feature_bank.py.md](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | Производные признаки исторической реакции цены `Up/Dn` после уровней | 2026-04-20 | 2KB | `9d18b5e1` |
| [docs/ML/neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики | 2026-04-20 | 24KB | `b00080ac` |
| [docs/ML/run_take_skip_lib_pic_feature_matrix.py.md](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | Training matrix для `take_skip_v2` с признаками `lib_PIC` внутри модели | 2026-04-20 | 3KB | `46e7fd49` |
| [docs/MT/lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC | 2026-04-20 | 8KB | `e40ecf3c` |
| [docs/MT/ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) | 2026-04-19 | 11KB | `40b6a8bb` |
| [docs/MT/trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() | 2026-04-19 | 14KB | `84bb5246` |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document | 2026-04-12 | 4KB | `5df7ce35` |
| [docs/dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv | 2026-04-01 | 10KB | `7d9009ee` |
| [docs/processing/label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора | 2026-04-20 | 2KB | `3f1ffcb9` |
| [docs/processing/label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict | 2026-04-20 | 1KB | `3fd26730` |
| [docs/processing/normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков | 2026-03-26 | 3KB | `06e43e08` |
| [docs/statistics/EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу | 2026-04-01 | 17KB | `914b3a5e` |
| [docs/statistics/signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF | 2026-04-12 | 7KB | `052eb4f7` |
| [docs/statistics/statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике | 2026-03-26 | 6KB | `9835a477` |
| [docs/superpowers/plans/2026-03-22-triple-barrier.md](docs/superpowers/plans/2026-03-22-triple-barrier.md) |  | 2026-04-07 | 28KB | `fe31fa4e` |
| [docs/superpowers/plans/2026-03-25-updn-denormalization.md](docs/superpowers/plans/2026-03-25-updn-denormalization.md) |  | 2026-03-25 | 19KB | `01d8efee` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md) |  | 2026-03-27 | 22KB | `ba50388e` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md) |  | 2026-03-27 | 9KB | `7ed11b5f` |
| [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](docs/superpowers/plans/2026-04-01-signal-research-variant-2.md) |  | 2026-04-01 | 29KB | `09aa7ec8` |
| [docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md](docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md) |  | 2026-04-02 | 20KB | `43d44dc5` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-04-02 | 19KB | `b25009ee` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3.md) |  | 2026-04-02 | 3KB | `3b40fae8` |
| [docs/superpowers/plans/2026-04-03-signal-path-atlas.md](docs/superpowers/plans/2026-04-03-signal-path-atlas.md) |  | 2026-04-03 | 39KB | `b0fea2ba` |
| [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](docs/superpowers/plans/2026-04-03-signal-quality-filter.md) |  | 2026-04-03 | 39KB | `6518f11b` |
| [docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md](docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md) |  | 2026-04-07 | 7KB | `636d1a67` |
| [docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md](docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md) |  | 2026-04-07 | 7KB | `af4ec829` |
| [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md) |  | 2026-04-07 | 11KB | `44d803a8` |
| [docs/superpowers/plans/2026-04-07-validation-first-research.md](docs/superpowers/plans/2026-04-07-validation-first-research.md) |  | 2026-04-07 | 10KB | `c0b29ff8` |
| [docs/superpowers/plans/2026-04-08-entry-path-v1.md](docs/superpowers/plans/2026-04-08-entry-path-v1.md) |  | 2026-04-08 | 28KB | `86fb358e` |
| [docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md](docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-04-08 | 15KB | `e9cb346d` |
| [docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md](docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md) |  | 2026-04-09 | 22KB | `0a35f491` |
| [docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md](docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md) |  | 2026-04-09 | 29KB | `1ab66152` |
| [docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md](docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md) |  | 2026-04-09 | 26KB | `9b5a8151` |
| [docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md](docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md) |  | 2026-04-10 | 31KB | `155a7325` |
| [docs/superpowers/plans/2026-04-10-entry-path-cqr.md](docs/superpowers/plans/2026-04-10-entry-path-cqr.md) |  | 2026-04-10 | 24KB | `0f832c74` |
| [docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md](docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md) |  | 2026-04-10 | 15KB | `fe2b2167` |
| [docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md](docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md) |  | 2026-04-12 | 14KB | `5b49271e` |
| [docs/superpowers/plans/2026-04-13-early-timeout-bar12.md](docs/superpowers/plans/2026-04-13-early-timeout-bar12.md) |  | 2026-04-15 | 37KB | `908866bf` |
| [docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md](docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-04-13 | 20KB | `80750ee6` |
| [docs/superpowers/plans/2026-04-13-label-convention-audit.md](docs/superpowers/plans/2026-04-13-label-convention-audit.md) |  | 2026-04-13 | 31KB | `ea55d54a` |
| [docs/superpowers/plans/2026-04-13-ny-session-filter.md](docs/superpowers/plans/2026-04-13-ny-session-filter.md) |  | 2026-04-13 | 2KB | `325f4e90` |
| [docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md](docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md) |  | 2026-04-13 | 29KB | `74578dba` |
| [docs/superpowers/plans/2026-04-13-pred-adv-cap.md](docs/superpowers/plans/2026-04-13-pred-adv-cap.md) |  | 2026-04-13 | 2KB | `51f3e15c` |
| [docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md](docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md) |  | 2026-04-13 | 15KB | `50a68d1f` |
| [docs/superpowers/plans/2026-04-13-quantile-fav-composition.md](docs/superpowers/plans/2026-04-13-quantile-fav-composition.md) |  | 2026-04-13 | 25KB | `20186b5d` |
| [docs/superpowers/plans/2026-04-13-quantile-forward-validation.md](docs/superpowers/plans/2026-04-13-quantile-forward-validation.md) |  | 2026-04-13 | 13KB | `e4d63c4c` |
| [docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md](docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md) |  | 2026-04-15 | 11KB | `cfa70650` |
| [docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md](docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md) |  | 2026-04-15 | 18KB | `2d48d389` |
| [docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md](docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md) |  | 2026-04-15 | 21KB | `7c99ab9c` |
| [docs/superpowers/plans/2026-04-15-track-a-max-out.md](docs/superpowers/plans/2026-04-15-track-a-max-out.md) |  | 2026-04-17 | 27KB | `4a83f18e` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md) |  | 2026-04-17 | 31KB | `a6f904f0` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md) |  | 2026-04-17 | 21KB | `2085188e` |
| [docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md](docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-04-19 | 2KB | `0617b8a6` |
| [docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md](docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md) |  | 2026-04-18 | 9KB | `a6b6e6e9` |
| [docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md](docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-04-20 | 2KB | `d3f1a358` |
| [docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md](docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-04-20 | 2KB | `23a84682` |
| [docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md](docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-04-20 | 6KB | `35ba356d` |
| [docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-04-20 | 2KB | `53f8ce75` |
| [docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-04-20 | 2KB | `e0278dfc` |
| [docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md](docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md) |  | 2026-04-20 | 5KB | `c19d12dc` |
| [docs/superpowers/plans/ME13_Diagnostics_Plan.md](docs/superpowers/plans/ME13_Diagnostics_Plan.md) |  | 2026-04-07 | 5KB | `10a0c4ea` |
| [docs/superpowers/roadmap.md](docs/superpowers/roadmap.md) |  | 2026-04-20 | 8KB | `579eceb3` |
| [docs/superpowers/specs/2026-03-22-triple-barrier-design.md](docs/superpowers/specs/2026-03-22-triple-barrier-design.md) |  | 2026-03-23 | 12KB | `82b0860f` |
| [docs/superpowers/specs/2026-03-27-pf-improvement-design.md](docs/superpowers/specs/2026-03-27-pf-improvement-design.md) |  | 2026-03-27 | 18KB | `85d548d9` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md) |  | 2026-04-01 | 13KB | `477a2843` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md) |  | 2026-04-01 | 10KB | `db9fb094` |
| [docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md](docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md) |  | 2026-04-02 | 21KB | `dcb5dcd3` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md) |  | 2026-04-02 | 3KB | `15368fbf` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md) |  | 2026-04-02 | 10KB | `88d9ca83` |
| [docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md](docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md) |  | 2026-04-03 | 10KB | `81b0a31f` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md) |  | 2026-04-03 | 8KB | `60e115b4` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md) |  | 2026-04-03 | 7KB | `119b59e0` |
| [docs/superpowers/specs/2026-04-08-entry-path-v1-design.md](docs/superpowers/specs/2026-04-08-entry-path-v1-design.md) |  | 2026-04-08 | 17KB | `deafd06e` |
| [docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md) |  | 2026-04-09 | 12KB | `e771d628` |
| [docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md) |  | 2026-04-09 | 12KB | `402001b6` |
| [docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md](docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md) |  | 2026-04-10 | 12KB | `1a877fcd` |
| [docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md](docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md) |  | 2026-04-12 | 13KB | `2ef88bef` |
| [docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md](docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md) |  | 2026-04-13 | 8KB | `8272fe58` |
| [docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md](docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md) |  | 2026-04-13 | 7KB | `7fede3fc` |
| [docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md](docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md) |  | 2026-04-13 | 6KB | `f1f6cae8` |
| [docs/superpowers/specs/2026-04-15-quantile-next-research-design.md](docs/superpowers/specs/2026-04-15-quantile-next-research-design.md) |  | 2026-04-15 | 20KB | `8ac77369` |
| [docs/superpowers/specs/2026-04-15-track-a-max-out-design.md](docs/superpowers/specs/2026-04-15-track-a-max-out-design.md) |  | 2026-04-17 | 12KB | `2b4ee2f7` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md) |  | 2026-04-17 | 13KB | `299a938f` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md) |  | 2026-04-17 | 10KB | `48c918e2` |
| [docs/tests/tests.md](docs/tests/tests.md) |  | 2026-04-05 | 4KB | `551fd6e9` |

## Reports

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md) |  | 2026-04-05 | 5KB | `37b9ec88` |
| [docs/reports/2026-04-02-signal-research-variant-3-prep.md](docs/reports/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-04-05 | 12KB | `d26a9270` |
| [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md) |  | 2026-04-05 | 15KB | `98244916` |
| [docs/reports/2026-04-03-signal-path-atlas.md](docs/reports/2026-04-03-signal-path-atlas.md) |  | 2026-04-03 | 8KB | `c68aa3b8` |
| [docs/reports/2026-04-04-archetype-filter-bridge.md](docs/reports/2026-04-04-archetype-filter-bridge.md) |  | 2026-04-04 | 14KB | `28e2bd45` |
| [docs/reports/2026-04-04-signal-path-atlas-readout.md](docs/reports/2026-04-04-signal-path-atlas-readout.md) |  | 2026-04-04 | 25KB | `fbfedb40` |
| [docs/reports/2026-04-04-signal-quality-filter.md](docs/reports/2026-04-04-signal-quality-filter.md) |  | 2026-04-05 | 12KB | `e2e74751` |
| [docs/reports/2026-04-08-entry-path-v1-baseline.md](docs/reports/2026-04-08-entry-path-v1-baseline.md) |  | 2026-04-08 | 10KB | `ff56ac36` |
| [docs/reports/2026-04-08-ml-exit-validation-first.md](docs/reports/2026-04-08-ml-exit-validation-first.md) |  | 2026-04-08 | 8KB | `f61986e3` |
| [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md) |  | 2026-04-08 | 8KB | `1783da26` |
| [docs/reports/2026-04-08-triple-barrier-hardening.md](docs/reports/2026-04-08-triple-barrier-hardening.md) |  | 2026-04-08 | 8KB | `ec8f88b7` |
| [docs/reports/2026-04-08-triple-barrier-runtime-verdict.md](docs/reports/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-04-08 | 9KB | `33e1602a` |
| [docs/reports/2026-04-09-entry-path-trade-filter.md](docs/reports/2026-04-09-entry-path-trade-filter.md) |  | 2026-04-09 | 10KB | `8553f63e` |
| [docs/reports/2026-04-09-entry-path-v1-loss-weighting.md](docs/reports/2026-04-09-entry-path-v1-loss-weighting.md) |  | 2026-04-09 | 7KB | `79f4b733` |
| [docs/reports/2026-04-09-mt4-parity-check-winner.md](docs/reports/2026-04-09-mt4-parity-check-winner.md) |  | 2026-04-09 | 8KB | `a8467fad` |
| [docs/reports/2026-04-10-entry-path-v1-quantile.md](docs/reports/2026-04-10-entry-path-v1-quantile.md) |  | 2026-04-10 | 6KB | `d4fef0e4` |
| [docs/reports/2026-04-12-quantile-status-decision.md](docs/reports/2026-04-12-quantile-status-decision.md) |  | 2026-04-12 | 10KB | `5375913e` |
| [docs/reports/2026-04-12-tb-verdict.md](docs/reports/2026-04-12-tb-verdict.md) |  | 2026-04-12 | 7KB | `089642df` |
| [docs/reports/2026-04-13-fav-3-vs-12-standalone.md](docs/reports/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-04-13 | 5KB | `8a929a77` |
| [docs/reports/2026-04-13-label-convention-audit.md](docs/reports/2026-04-13-label-convention-audit.md) |  | 2026-04-13 | 6KB | `3ddc2a23` |
| [docs/reports/2026-04-13-pf-uplift-discovery.md](docs/reports/2026-04-13-pf-uplift-discovery.md) |  | 2026-04-13 | 14KB | `f93b85c0` |
| [docs/reports/2026-04-13-quantile-fav-composition.md](docs/reports/2026-04-13-quantile-fav-composition.md) |  | 2026-04-13 | 8KB | `8dd53bda` |
| [docs/reports/2026-04-13-quantile-forward-validation.md](docs/reports/2026-04-13-quantile-forward-validation.md) |  | 2026-04-13 | 4KB | `1364686a` |
| [docs/reports/2026-04-15-entry-path-v1-frequency.md](docs/reports/2026-04-15-entry-path-v1-frequency.md) |  | 2026-04-17 | 6KB | `9f5043d0` |
| [docs/reports/2026-04-15-track-a-max-out.md](docs/reports/2026-04-15-track-a-max-out.md) |  | 2026-04-17 | 9KB | `ca11c38f` |
| [docs/reports/2026-04-16-trailing-stop-target-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-first-wave.md) |  | 2026-04-17 | 6KB | `5b0b7b8b` |
| [docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md) |  | 2026-04-17 | 6KB | `e812d460` |
| [docs/reports/2026-04-18-mt4-trailing-stop-execution.md](docs/reports/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-04-19 | 5KB | `db5e5c66` |
| [docs/reports/2026-04-18-take-skip-frequency-followup.md](docs/reports/2026-04-18-take-skip-frequency-followup.md) |  | 2026-04-19 | 9KB | `edb6385b` |
| [docs/reports/2026-04-18-take-skip-rule-consumer.md](docs/reports/2026-04-18-take-skip-rule-consumer.md) |  | 2026-04-19 | 5KB | `bf29f837` |
| [docs/reports/2026-04-19-current-feature-importance-diagnostics.md](docs/reports/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-04-20 | 4KB | `e9beb824` |
| [docs/reports/2026-04-19-execution-policy-v2.md](docs/reports/2026-04-19-execution-policy-v2.md) |  | 2026-04-19 | 8KB | `f124b341` |
| [docs/reports/2026-04-19-feature-bank-clean-comparison.md](docs/reports/2026-04-19-feature-bank-clean-comparison.md) |  | 2026-04-20 | 3KB | `6c105216` |
| [docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md](docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-04-20 | 3KB | `8505936d` |
| [docs/reports/2026-04-19-lib-pic-feature-source-audit.md](docs/reports/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-04-20 | 8KB | `0b903977` |
| [docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md](docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-04-20 | 4KB | `c80ac4eb` |
| [docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-04-20 | 2KB | `64b8dea4` |
| [docs/reports/2026-04-20-take-skip-lib-pic-selection.md](docs/reports/2026-04-20-take-skip-lib-pic-selection.md) |  | 2026-04-20 | 4KB | `51a438b8` |
| [docs/reports/README.md](docs/reports/README.md) |  | 2026-04-05 | 2KB | `ed0769cc` |

## ML

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [ML/README.md](ML/README.md) |  |  | 2026-04-20 | 6KB | `011f18bf` |
| [ML/ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | 🏁 | 2026-03-12 | 4KB | `390f9209` |
| [ML/baseline/baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | 🏁 | 2026-02-25 | 40KB | `d214b051` |
| [ML/baseline/reports/baseline_report.md](ML/baseline/reports/baseline_report.md) |  |  | 2026-04-01 | 4KB | `66cbf52f` |
| [ML/benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | 🏁 | 2026-04-09 | 6KB | `1bc86818` |
| [ML/benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | 🏁 | 2026-04-17 | 7KB | `e469b58a` |
| [ML/benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | ✅ | 2026-04-13 | 13KB | `40bbefc1` |
| [ML/benchmark_entry_path_v1_quantile_n_boost.py](ML/benchmark_entry_path_v1_quantile_n_boost.py) |  |  | 2026-04-12 | 13KB | `6538fa97` |
| [ML/benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | ✅ | 2026-04-17 | 12KB | `34916e02` |
| [ML/benchmark_execution_policy_v2.py](ML/benchmark_execution_policy_v2.py) | Сравнение вариантов выхода для готовых ML-сигналов | ✅ | 2026-04-19 | 15KB | `4c633833` |
| [ML/benchmark_fav_3_vs_12_standalone.py](ML/benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-04-13 | 16KB | `8e4214fd` |
| [ML/benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | 🏁 | 2026-04-08 | 14KB | `16753618` |
| [ML/benchmark_quantile_early_timeout.py](ML/benchmark_quantile_early_timeout.py) |  |  | 2026-04-15 | 5KB | `dca2ba4f` |
| [ML/benchmark_quantile_fav_composition.py](ML/benchmark_quantile_fav_composition.py) |  |  | 2026-04-13 | 15KB | `97a02b70` |
| [ML/benchmark_quantile_forward_validation.py](ML/benchmark_quantile_forward_validation.py) |  |  | 2026-04-13 | 5KB | `a3386bcc` |
| [ML/benchmark_quantile_relaxed_composition.py](ML/benchmark_quantile_relaxed_composition.py) |  |  | 2026-04-15 | 8KB | `67b8d711` |
| [ML/benchmark_take_skip_lib_pic_selection.py](ML/benchmark_take_skip_lib_pic_selection.py) | Внешний слой отбора `take_skip_v2` по признакам `lib_PIC` без нового обучения | ✅ | 2026-04-20 | 18KB | `103dc4a1` |
| [ML/benchmark_take_skip_mt4_trailing_sequential.py](ML/benchmark_take_skip_mt4_trailing_sequential.py) | Read-only comparison of independent vs single-position trailing-stop execution for take/skip signals | ✅ | 2026-04-19 | 7KB | `1debf0f4` |
| [ML/benchmark_take_skip_trailing_stop.py](ML/benchmark_take_skip_trailing_stop.py) |  |  | 2026-04-19 | 7KB | `fd3fe635` |
| [ML/benchmark_take_skip_trailing_stop_v2.py](ML/benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-04-18 | 5KB | `f1ef638b` |
| [ML/benchmark_take_skip_trailing_stop_v2_followup.py](ML/benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-04-19 | 10KB | `106613ee` |
| [ML/benchmark_trailing_stop_target.py](ML/benchmark_trailing_stop_target.py) | Validation-first benchmark для trailing-stop target exports | ✅ | 2026-04-17 | 1KB | `7c96419a` |
| [ML/benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | ✅ | 2026-04-17 | 8KB | `d8cf04ba` |
| [ML/benchmark_triple_barrier_mt4_execution.py](ML/benchmark_triple_barrier_mt4_execution.py) |  |  | 2026-04-13 | 4KB | `3ef3e057` |
| [ML/compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | 🏁 | 2026-03-23 | 13KB | `103ded09` |
| [ML/conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | 🏁 | 2026-03-20 | 14KB | `d34cb990` |
| [ML/conformal/conformal_quantiles.json](ML/conformal/conformal_quantiles.json) |  |  | 2026-03-20 | 399B | `6d9e2e03` |
| [ML/data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ | 2026-04-20 | 55KB | `52e42b36` |
| [ML/entry_path_feature_bank.py](ML/entry_path_feature_bank.py) | Entry path feature bank: оконные сводки строки и row-wise context features | ✅ | 2026-04-17 | 3KB | `0c7004b2` |
| [ML/entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | ✅ | 2026-04-20 | 17KB | `cb38faa5` |
| [ML/entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | ✅ | 2026-04-09 | 14KB | `54d61050` |
| [ML/entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | ✅ | 2026-04-10 | 8KB | `6e03b05a` |
| [ML/evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | ✅ | 2026-04-20 | 37KB | `a215c472` |
| [ML/experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | 🏁 | 2026-03-23 | 20KB | `390bd6fb` |
| [ML/export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export train/validation/test predictions for entry_path_v1_quantile | ✅ | 2026-04-17 | 6KB | `38bc75e8` |
| [ML/export_entry_path_v1_quantile_rule.py](ML/export_entry_path_v1_quantile_rule.py) |  |  | 2026-04-12 | 7KB | `aa96afd9` |
| [ML/export_updn_active_predictions.py](ML/export_updn_active_predictions.py) |  |  | 2026-04-13 | 4KB | `515bde2e` |
| [ML/feature_bank_comparison_diagnostics.py](ML/feature_bank_comparison_diagnostics.py) | Сравнение baseline/geometry/path feature-bank вариантов | ✅ | 2026-04-20 | 9KB | `3599f7fa` |
| [ML/feature_importance_diagnostics.py](ML/feature_importance_diagnostics.py) | Диагностика важности групп текущих fractal-признаков | ✅ | 2026-04-20 | 16KB | `a68fad5b` |
| [ML/feature_screen_entry_path.py](ML/feature_screen_entry_path.py) | Диагностический feature screening для entry_path_v1 | ✅ | 2026-04-17 | 782B | `473127c5` |
| [ML/lib_pic_feature_profiles.py](ML/lib_pic_feature_profiles.py) | Единая сборка профилей признаков `lib_PIC` для диагностики и `entry_path_v1` | ✅ | 2026-04-20 | 4KB | `6da69e68` |
| [ML/lib_pic_geometry_feature_bank.py](ML/lib_pic_geometry_feature_bank.py) | Производные признаки геометрии уровней `lib_PIC` | ✅ | 2026-04-20 | 7KB | `24dd7aaa` |
| [ML/lib_pic_path_reaction_feature_bank.py](ML/lib_pic_path_reaction_feature_bank.py) | Производные признаки исторической реакции цены `Up/Dn` после уровней | ✅ | 2026-04-20 | 8KB | `a47b0ff1` |
| [ML/losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ | 2026-03-31 | 9KB | `f7313c67` |
| [ML/models/__init__.py](ML/models/__init__.py) |  |  | 2026-02-18 | 1KB | `f8ff5fa3` |
| [ML/models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | 🏁 | 2026-03-12 | 4KB | `f1b6faea` |
| [ML/models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | 🏁 | 2026-03-12 | 4KB | `61595f42` |
| [ML/models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | ✅ | 2026-04-17 | 4KB | `597779ed` |
| [ML/models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | ✅ | 2026-04-17 | 4KB | `41ffb003` |
| [ML/models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | ✅ | 2026-04-10 | 4KB | `a25b4776` |
| [ML/models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 | 2026-03-12 | 5KB | `069a6018` |
| [ML/models/take_skip_dual_stream_transformer.py](ML/models/take_skip_dual_stream_transformer.py) | Dual-stream Transformer для `take_skip_v2`: sequence branch + `lib_PIC` feature branch | ✅ | 2026-04-20 | 3KB | `d645930f` |
| [ML/models/trailing_stop_target_quantile_transformer.py](ML/models/trailing_stop_target_quantile_transformer.py) | TrailingStopTargetQuantileTransformer — q10/q50/q90 heads для `trail_48_pnl_atr_x3` | ✅ | 2026-04-17 | 2KB | `61f57808` |
| [ML/models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | ✅ | 2026-03-12 | 7KB | `27645ebe` |
| [ML/multi_scale_fractal_features.py](ML/multi_scale_fractal_features.py) |  |  | 2026-04-18 | 1KB | `c73c28c3` |
| [ML/optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | 🏁 | 2026-03-23 | 19KB | `f6c18a03` |
| [ML/reports/architecture_comparison_classification.md](ML/reports/architecture_comparison_classification.md) |  |  | 2026-02-24 | 3KB | `c0fe9f2d` |
| [ML/reports/architecture_comparison_regression.md](ML/reports/architecture_comparison_regression.md) |  |  | 2026-03-11 | 1KB | `3fe65254` |
| [ML/reports/architecture_comparison_regression_updn.md](ML/reports/architecture_comparison_regression_updn.md) |  |  | 2026-03-19 | 1KB | `bc5e1dc4` |
| [ML/reports/current_feature_importance/report.md](ML/reports/current_feature_importance/report.md) |  |  | 2026-04-20 | 2KB | `c58147a6` |
| [ML/reports/current_feature_importance/summary.json](ML/reports/current_feature_importance/summary.json) |  |  | 2026-04-20 | 498B | `a286b27a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 536B | `2dbd3e0a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `2f9e801c` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 536B | `7b9539cf` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 2KB | `062a50ec` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 544B | `7d0c8863` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `756079bf` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 541B | `201a0e3e` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `a077c548` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 528B | `a9a86071` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `ece7ee12` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 521B | `d4d1887c` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `e186a9fd` |
| [ML/reports/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_report.md) |  |  | 2026-04-09 | 495B | `e8a9e03d` |
| [ML/reports/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_selected_rule.json) |  |  | 2026-04-09 | 1KB | `ead9e11c` |
| [ML/reports/entry_path_v1_frequency/final_verdict.json](ML/reports/entry_path_v1_frequency/final_verdict.json) |  |  | 2026-04-17 | 637B | `c96361ff` |
| [ML/reports/entry_path_v1_frequency/run_metadata.json](ML/reports/entry_path_v1_frequency/run_metadata.json) |  |  | 2026-04-17 | 218B | `4c8fa299` |
| [ML/reports/entry_path_v1_frequency/selected_candidate.json](ML/reports/entry_path_v1_frequency/selected_candidate.json) |  |  | 2026-04-17 | 251B | `f2b86a6f` |
| [ML/reports/entry_path_v1_frequency_v2/final_verdict.json](ML/reports/entry_path_v1_frequency_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `3fa39482` |
| [ML/reports/entry_path_v1_frequency_v2/run_metadata.json](ML/reports/entry_path_v1_frequency_v2/run_metadata.json) |  |  | 2026-04-17 | 243B | `6316d165` |
| [ML/reports/entry_path_v1_frequency_v2/selected_candidate.json](ML/reports/entry_path_v1_frequency_v2/selected_candidate.json) |  |  | 2026-04-17 | 513B | `b69272ad` |
| [ML/reports/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_filter_report.md) |  |  | 2026-04-10 | 706B | `0d99ebcd` |
| [ML/reports/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-04-10 | 1KB | `f665ab0d` |
| [ML/reports/entry_path_v1_quantile_selected_rule.json](ML/reports/entry_path_v1_quantile_selected_rule.json) |  |  | 2026-04-12 | 2KB | `a2fce0f7` |
| [ML/reports/evaluate_test_H12.md](ML/reports/evaluate_test_H12.md) |  |  | 2026-03-19 | 513B | `8b8eb347` |
| [ML/reports/evaluate_test_entry_path_v1.md](ML/reports/evaluate_test_entry_path_v1.md) |  |  | 2026-04-19 | 1KB | `a6f68803` |
| [ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md](ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md) |  |  | 2026-04-20 | 1KB | `46ed4ec9` |
| [ML/reports/evaluate_test_entry_path_v1_quantile.md](ML/reports/evaluate_test_entry_path_v1_quantile.md) |  |  | 2026-04-10 | 523B | `03c3cfb6` |
| [ML/reports/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-04-18 | 277B | `1c95661a` |
| [ML/reports/evaluate_test_tb.md](ML/reports/evaluate_test_tb.md) |  |  | 2026-04-08 | 1KB | `295448ff` |
| [ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-04-17 | 385B | `e972ae90` |
| [ML/reports/evaluate_test_trailing_stop_target_v1.md](ML/reports/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-04-17 | 304B | `087f3217` |
| [ML/reports/evaluate_validation_entry_path_v1.md](ML/reports/evaluate_validation_entry_path_v1.md) |  |  | 2026-04-09 | 1KB | `6eb89813` |
| [ML/reports/execution_policy_v2/frequency_trail_scan/summary.json](ML/reports/execution_policy_v2/frequency_trail_scan/summary.json) |  |  | 2026-04-19 | 3KB | `8a130d60` |
| [ML/reports/execution_policy_v2/summary.json](ML/reports/execution_policy_v2/summary.json) |  |  | 2026-04-19 | 26KB | `63d0a3c5` |
| [ML/reports/fav_3_vs_12_standalone/run_metadata.json](ML/reports/fav_3_vs_12_standalone/run_metadata.json) |  |  | 2026-04-13 | 1KB | `749e6a5b` |
| [ML/reports/fav_3_vs_12_standalone/selected_threshold.json](ML/reports/fav_3_vs_12_standalone/selected_threshold.json) |  |  | 2026-04-13 | 532B | `d941fc13` |
| [ML/reports/fav_3_vs_12_standalone/verdict.json](ML/reports/fav_3_vs_12_standalone/verdict.json) |  |  | 2026-04-13 | 893B | `1fc84a37` |
| [ML/reports/feature_bank_clean_comparison/report.md](ML/reports/feature_bank_clean_comparison/report.md) |  |  | 2026-04-20 | 1KB | `ea8f6f93` |
| [ML/reports/feature_bank_clean_comparison/summary.json](ML/reports/feature_bank_clean_comparison/summary.json) |  |  | 2026-04-20 | 1KB | `84b8ec2f` |
| [ML/reports/feature_bank_comparison/report.md](ML/reports/feature_bank_comparison/report.md) |  |  | 2026-04-20 | 1KB | `f4f494ed` |
| [ML/reports/feature_bank_comparison/summary.json](ML/reports/feature_bank_comparison/summary.json) |  |  | 2026-04-20 | 1KB | `97d30738` |
| [ML/reports/frozen_exit_policy.json](ML/reports/frozen_exit_policy.json) |  |  | 2026-04-08 | 537B | `4da12318` |
| [ML/reports/label_convention_audit.md](ML/reports/label_convention_audit.md) |  |  | 2026-04-13 | 3KB | `72706b95` |
| [ML/reports/n_boost_result.json](ML/reports/n_boost_result.json) |  |  | 2026-04-12 | 1KB | `9248dae1` |
| [ML/reports/optuna_best_params_bilstm_regression.json](ML/reports/optuna_best_params_bilstm_regression.json) |  |  | 2026-03-16 | 496B | `b1a36a79` |
| [ML/reports/optuna_best_params_cnn1d_classification.json](ML/reports/optuna_best_params_cnn1d_classification.json) |  |  | 2026-02-28 | 461B | `25ae2754` |
| [ML/reports/optuna_best_params_transformer_regression_updn.json](ML/reports/optuna_best_params_transformer_regression_updn.json) |  |  | 2026-03-19 | 539B | `5a6d031a` |
| [ML/reports/optuna_study_bilstm_regression_20260311_223415.json](ML/reports/optuna_study_bilstm_regression_20260311_223415.json) |  |  | 2026-03-11 | 1KB | `f908cbce` |
| [ML/reports/optuna_study_bilstm_regression_20260312_003636.json](ML/reports/optuna_study_bilstm_regression_20260312_003636.json) |  |  | 2026-03-11 | 31KB | `8318dd5a` |
| [ML/reports/optuna_study_bilstm_regression_20260312_105613.json](ML/reports/optuna_study_bilstm_regression_20260312_105613.json) |  |  | 2026-03-12 | 18KB | `9860a4c5` |
| [ML/reports/optuna_study_bilstm_regression_20260312_112811.json](ML/reports/optuna_study_bilstm_regression_20260312_112811.json) |  |  | 2026-03-12 | 18KB | `535d2951` |
| [ML/reports/optuna_study_bilstm_regression_20260316_102024.json](ML/reports/optuna_study_bilstm_regression_20260316_102024.json) |  |  | 2026-03-16 | 31KB | `ef829e93` |
| [ML/reports/optuna_study_cnn1d_classification_20260226_134119.json](ML/reports/optuna_study_cnn1d_classification_20260226_134119.json) |  |  | 2026-02-26 | 29KB | `a53f62cd` |
| [ML/reports/optuna_study_cnn1d_classification_20260227_231828.json](ML/reports/optuna_study_cnn1d_classification_20260227_231828.json) |  |  | 2026-02-27 | 28KB | `f8e66057` |
| [ML/reports/optuna_study_cnn1d_classification_20260228_100415.json](ML/reports/optuna_study_cnn1d_classification_20260228_100415.json) |  |  | 2026-02-28 | 29KB | `c38b7403` |
| [ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json](ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json) |  |  | 2026-03-19 | 33KB | `2c98a9f9` |
| [ML/reports/outcome_target_validation_benchmark.md](ML/reports/outcome_target_validation_benchmark.md) |  |  | 2026-04-08 | 763B | `9104e652` |
| [ML/reports/pf_uplift_discovery/baseline_numbers.json](ML/reports/pf_uplift_discovery/baseline_numbers.json) |  |  | 2026-04-13 | 2KB | `4519e3fe` |
| [ML/reports/pf_uplift_discovery/hypotheses_longlist.md](ML/reports/pf_uplift_discovery/hypotheses_longlist.md) |  |  | 2026-04-13 | 8KB | `61fcd585` |
| [ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json](ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json) |  |  | 2026-04-13 | 602B | `d5ab62dc` |
| [ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json](ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json) |  |  | 2026-04-13 | 536B | `afb475b6` |
| [ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json) |  |  | 2026-04-13 | 655B | `1db83311` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json) |  |  | 2026-04-13 | 665B | `8da7e815` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json) |  |  | 2026-04-13 | 623B | `866da98b` |
| [ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json](ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json) |  |  | 2026-04-13 | 614B | `2146acd5` |
| [ML/reports/pf_uplift_discovery/run_metadata.json](ML/reports/pf_uplift_discovery/run_metadata.json) |  |  | 2026-04-13 | 552B | `2ffaa2db` |
| [ML/reports/quantile_fav_composition/intersection_diagnostic.json](ML/reports/quantile_fav_composition/intersection_diagnostic.json) |  |  | 2026-04-13 | 270B | `8877d751` |
| [ML/reports/quantile_fav_composition/n_boost_composition.json](ML/reports/quantile_fav_composition/n_boost_composition.json) |  |  | 2026-04-13 | 155B | `164387a5` |
| [ML/reports/quantile_fav_composition/run_metadata.json](ML/reports/quantile_fav_composition/run_metadata.json) |  |  | 2026-04-13 | 4KB | `6aa02ee6` |
| [ML/reports/quantile_fav_composition/test_metrics.json](ML/reports/quantile_fav_composition/test_metrics.json) |  |  | 2026-04-13 | 1KB | `86714f9b` |
| [ML/reports/quantile_fav_composition/updn_active_source/metadata.json](ML/reports/quantile_fav_composition/updn_active_source/metadata.json) |  |  | 2026-04-13 | 619B | `d44841e2` |
| [ML/reports/quantile_fav_composition/validation_metrics.json](ML/reports/quantile_fav_composition/validation_metrics.json) |  |  | 2026-04-13 | 1KB | `7583bfeb` |
| [ML/reports/quantile_forward_validation/run_metadata.json](ML/reports/quantile_forward_validation/run_metadata.json) |  |  | 2026-04-13 | 554B | `eeb46771` |
| [ML/reports/quantile_forward_validation/summary.json](ML/reports/quantile_forward_validation/summary.json) |  |  | 2026-04-13 | 440B | `f208a93b` |
| [ML/reports/quantile_relaxed_composition/selected_baseline.json](ML/reports/quantile_relaxed_composition/selected_baseline.json) |  |  | 2026-04-15 | 118B | `3c6efae0` |
| [ML/reports/reproducibility_report_12H.md](ML/reports/reproducibility_report_12H.md) |  |  | 2026-03-11 | 1KB | `c9af48ba` |
| [ML/reports/take_skip_lib_pic_selection/final_verdict.json](ML/reports/take_skip_lib_pic_selection/final_verdict.json) |  |  | 2026-04-20 | 5KB | `d5323101` |
| [ML/reports/take_skip_mt4_trailing_sequential/summary.json](ML/reports/take_skip_mt4_trailing_sequential/summary.json) |  |  | 2026-04-19 | 6KB | `80ed09d0` |
| [ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json](ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json) |  |  | 2026-04-19 | 3KB | `c5aa0bfc` |
| [ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json) |  |  | 2026-04-19 | 723B | `071ea894` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json](ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json) |  |  | 2026-04-18 | 16KB | `5a4d337a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json) |  |  | 2026-04-18 | 964B | `04c514f5` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-04-18 | 277B | `20c0004a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json) |  |  | 2026-04-18 | 4KB | `14a5e536` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-04-18 | 963B | `1aafa9e6` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-04-18 | 277B | `4af22546` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json) |  |  | 2026-04-18 | 4KB | `6bd39710` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json) |  |  | 2026-04-18 | 962B | `f4370930` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-04-18 | 277B | `ab926937` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json) |  |  | 2026-04-18 | 4KB | `416def03` |
| [ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json) |  |  | 2026-04-19 | 903B | `3d56d55f` |
| [ML/reports/tb_mt4_verdict/test_summary.json](ML/reports/tb_mt4_verdict/test_summary.json) |  |  | 2026-04-12 | 172B | `6ea3e9d3` |
| [ML/reports/tb_mt4_verdict/validation_summary.json](ML/reports/tb_mt4_verdict/validation_summary.json) |  |  | 2026-04-12 | 167B | `cc2e7d34` |
| [ML/reports/tb_selected_rule.json](ML/reports/tb_selected_rule.json) |  |  | 2026-04-08 | 279B | `3329dfb8` |
| [ML/reports/threshold_analysis_12H.md](ML/reports/threshold_analysis_12H.md) |  |  | 2026-03-19 | 2KB | `2eba7e9d` |
| [ML/reports/threshold_analysis_24H.md](ML/reports/threshold_analysis_24H.md) |  |  | 2026-03-19 | 2KB | `b6b5b9d3` |
| [ML/reports/threshold_analysis_48H.md](ML/reports/threshold_analysis_48H.md) |  |  | 2026-03-19 | 2KB | `9f692fd3` |
| [ML/reports/threshold_analysis_tb.md](ML/reports/threshold_analysis_tb.md) |  |  | 2026-04-08 | 975B | `d501c624` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `4210c896` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 349B | `36a6a110` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 498B | `47947c94` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `92fbb96a` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json) |  |  | 2026-04-17 | 9KB | `c0697157` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `aae66f9e` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 347B | `c94aaebb` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 476B | `f8499cc8` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `6afa1767` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json) |  |  | 2026-04-17 | 9KB | `cb8bd8b7` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `23ded61c` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 347B | `e511119f` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 493B | `f3e78f8d` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `93b3aaca` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json) |  |  | 2026-04-17 | 9KB | `9611273d` |
| [ML/reports/track_a_max_out_matrix/manifest.json](ML/reports/track_a_max_out_matrix/manifest.json) |  |  | 2026-04-17 | 63KB | `d565f9d8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `49b4b8cc` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 327B | `0effabc3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 514B | `88f69647` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `24810803` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json) |  |  | 2026-04-17 | 9KB | `6c2cbc3e` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `200c62ad` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 325B | `5795728a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 492B | `eb63ea67` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `ea93c21a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json) |  |  | 2026-04-17 | 9KB | `1aeaccaa` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `84235cc8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 325B | `2eee4697` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 490B | `6af015f3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `249b3cf5` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json) |  |  | 2026-04-17 | 9KB | `39c00532` |
| [ML/reports/track_a_max_out_matrix_deep/manifest.json](ML/reports/track_a_max_out_matrix_deep/manifest.json) |  |  | 2026-04-17 | 25KB | `f1b2534a` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `52d97d3c` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 335B | `035d3a21` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 495B | `f4b312bb` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `d87b2158` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json) |  |  | 2026-04-17 | 11KB | `67c6488f` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-04-17 | 1KB | `c8010aa4` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-04-17 | 335B | `5ca74235` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-04-17 | 487B | `0a640325` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-04-17 | 1KB | `a6f68803` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json) |  |  | 2026-04-17 | 11KB | `c4f044c8` |
| [ML/reports/trailing_stop_target_matrix/manifest.json](ML/reports/trailing_stop_target_matrix/manifest.json) |  |  | 2026-04-17 | 13KB | `eca77374` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-04-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-04-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-04-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-04-17 | 304B | `087f3217` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json) |  |  | 2026-04-17 | 3KB | `27fe5256` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-04-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-04-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-04-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-04-17 | 304B | `82e3e008` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json) |  |  | 2026-04-17 | 3KB | `15b1b065` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-04-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-04-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-04-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-04-17 | 304B | `311c6d96` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json) |  |  | 2026-04-17 | 3KB | `e7960f2b` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json) |  |  | 2026-04-17 | 1KB | `a654ac5f` |
| [ML/reports/trailing_stop_target_quantile/manifest.json](ML/reports/trailing_stop_target_quantile/manifest.json) |  |  | 2026-04-17 | 3KB | `2e163aa4` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json) |  |  | 2026-04-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-04-17 | 385B | `e972ae90` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json) |  |  | 2026-04-17 | 2KB | `255c26ad` |
| [ML/reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | 🏁 | 2026-03-11 | 7KB | `756dd1c8` |
| [ML/run_take_skip_lib_pic_feature_matrix.py](ML/run_take_skip_lib_pic_feature_matrix.py) | Training matrix для `take_skip_v2` с профилями признаков `lib_PIC` внутри модели | 🚧 | 2026-04-20 | 18KB | `9a955b99` |
| [ML/run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | ✅ | 2026-04-17 | 6KB | `0d1d781d` |
| [ML/run_trailing_stop_target_matrix.py](ML/run_trailing_stop_target_matrix.py) | Оркестратор bounded matrix для `trailing_stop_target_v1` | ✅ | 2026-04-18 | 9KB | `b18488e5` |
| [ML/run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | ✅ | 2026-04-17 | 6KB | `ac5afba9` |
| [ML/take_skip_trailing_stop_v2_task.py](ML/take_skip_trailing_stop_v2_task.py) |  |  | 2026-04-19 | 4KB | `aec11083` |
| [ML/tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | 🏁 | 2026-04-08 | 2KB | `502427cf` |
| [ML/tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | ✅ | 2026-04-13 | 4KB | `f07ea73a` |
| [ML/threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | ✅ | 2026-04-13 | 47KB | `b03bf490` |
| [ML/trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | ✅ | 2026-04-17 | 4KB | `9e87baba` |
| [ML/trailing_stop_target_task.py](ML/trailing_stop_target_task.py) | Trailing-stop target task: target contract, export helpers и metrics | ✅ | 2026-04-18 | 765B | `9e1ad543` |
| [ML/train.py](ML/train.py) | Обучение (--task regression_updn / triple_barrier) | ✅ | 2026-04-20 | 106KB | `ab7e2643` |
| [ML/triple_barrier_mt4_execution.py](ML/triple_barrier_mt4_execution.py) |  |  | 2026-04-12 | 6KB | `e2520e9d` |
| [ML/utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ | 2026-04-08 | 11KB | `5458dccf` |

## Processing

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [processing/README.md](processing/README.md) |  |  | 2026-03-26 | 1KB | `0013c357` |
| [processing/label_main.py](processing/label_main.py) | CLI оркестратор pipeline | 🏁 | 2026-04-17 | 17KB | `bcafa9e8` |
| [processing/label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | 🏁 | 2026-04-19 | 43KB | `ca81b6dd` |
| [processing/normalize.py](processing/normalize.py) | Построчная нормализация признаков | 🏁 | 2026-04-01 | 25KB | `62ee241c` |

## API

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [API/README.md](API/README.md) |  |  | 2026-04-19 | 2KB | `6703d214` |
| [API/api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, отдача ML-сигналов | 🏁 | 2026-03-19 | 6KB | `6c418d6e` |
| [API/exit_policy_research.py](API/exit_policy_research.py) | Offline research: сравнение ML-политик выхода и position management | 🏁 | 2026-04-08 | 14KB | `1d29b812` |
| [API/export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) |  |  | 2026-04-12 | 8KB | `a5a84e1a` |
| [API/export_take_skip_trailing_stop_v2_signals.py](API/export_take_skip_trailing_stop_v2_signals.py) | Применение frozen take/skip v2 rule к prediction CSV и экспорт `time;signal` | ✅ | 2026-04-19 | 6KB | `ea6aacaa` |
| [API/generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | ✅ | 2026-04-18 | 30KB | `48bc264c` |
| [API/signal_path_atlas.py](API/signal_path_atlas.py) | Research CLI: ATR-normalized Signal Path Atlas, path archetypes, holdout validation | 🏁 | 2026-04-08 | 37KB | `e2c123fe` |
| [API/signal_quality_research.py](API/signal_quality_research.py) | Signal Quality Filter Research (Variant 4): multi-horizon prediction features как фильтры | 🏁 | 2026-04-08 | 29KB | `ad2482f8` |
| [API/signal_research.py](API/signal_research.py) | Research CLI: качество ML-сигналов по реальным OHLC (Variant 2/3) | 🏁 | 2026-04-08 | 72KB | `c723fb6f` |
| [API/test_api_client.py](API/test_api_client.py) | Интеграционный тест REST API-сервера (MT4) | 🏁 | 2026-03-19 | 1KB | `83309207` |

## Statistics

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [statistics/EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | 🏁 | 2026-03-26 | 188KB | `4c750fc3` |
| [statistics/README.md](statistics/README.md) |  |  | 2026-04-12 | 2KB | `8a02dc7e` |
| [statistics/analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | 🏁 | 2026-03-27 | 8KB | `f3ed1639` |
| [statistics/class_statistics.json](statistics/class_statistics.json) |  |  | 2026-03-19 | 6KB | `c107590a` |
| [statistics/feature_catalog.json](statistics/feature_catalog.json) |  |  | 2026-02-18 | 70KB | `bb41c2d1` |
| [statistics/nero_features_metadata.json](statistics/nero_features_metadata.json) |  |  | 2026-02-18 | 6KB | `fc79c23a` |
| [statistics/reports/EDA_executed.ipynb](statistics/reports/EDA_executed.ipynb) |  |  | 2026-03-26 | 3MB | `--------` |
| [statistics/reports/EDA_report.md](statistics/reports/EDA_report.md) |  |  | 2026-04-01 | 59KB | `01e9ac82` |
| [statistics/signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | ✅ | 2026-04-12 | 49KB | `da86a8c1` |
| [statistics/statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | 🏁 | 2026-03-19 | 21KB | `c725dd71` |
| [statistics/statistics_summary.json](statistics/statistics_summary.json) |  |  | 2026-03-19 | 5KB | `1e7882c0` |

## Tests

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [tests/README.md](tests/README.md) |  |  | 2026-04-08 | 1KB | `c1093573` |
| [tests/test_benchmark_entry_path_v1_frequency.py](tests/test_benchmark_entry_path_v1_frequency.py) | `ML/benchmark_entry_path_v1_frequency.py` | ✅ | 2026-04-17 | 739B | `40f6843e` |
| [tests/test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | ✅ | 2026-04-17 | 2KB | `78d542d3` |
| [tests/test_benchmark_execution_policy_v2.py](tests/test_benchmark_execution_policy_v2.py) | `ML/benchmark_execution_policy_v2.py` | ✅ | 2026-04-19 | 2KB | `35ce24ab` |
| [tests/test_benchmark_fav_3_vs_12_standalone.py](tests/test_benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-04-13 | 11KB | `dcdcc7a1` |
| [tests/test_benchmark_outcome_targets.py](tests/test_benchmark_outcome_targets.py) | `ML/benchmark_outcome_targets.py` | ✅ | 2026-04-08 | 4KB | `e9159813` |
| [tests/test_benchmark_quantile_early_timeout.py](tests/test_benchmark_quantile_early_timeout.py) |  |  | 2026-04-15 | 1KB | `b4775c4c` |
| [tests/test_benchmark_quantile_fav_composition.py](tests/test_benchmark_quantile_fav_composition.py) |  |  | 2026-04-13 | 6KB | `e7f68596` |
| [tests/test_benchmark_quantile_forward_validation.py](tests/test_benchmark_quantile_forward_validation.py) |  |  | 2026-04-13 | 6KB | `3dc6e7a3` |
| [tests/test_benchmark_quantile_relaxed_composition.py](tests/test_benchmark_quantile_relaxed_composition.py) |  |  | 2026-04-15 | 5KB | `c7115be5` |
| [tests/test_benchmark_take_skip_lib_pic_selection.py](tests/test_benchmark_take_skip_lib_pic_selection.py) | `ML/benchmark_take_skip_lib_pic_selection.py` | ✅ | 2026-04-20 | 5KB | `345de225` |
| [tests/test_benchmark_take_skip_trailing_stop_v2.py](tests/test_benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-04-18 | 4KB | `d9fdae18` |
| [tests/test_benchmark_take_skip_trailing_stop_v2_followup.py](tests/test_benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-04-19 | 8KB | `0195683d` |
| [tests/test_benchmark_trailing_stop_target.py](tests/test_benchmark_trailing_stop_target.py) | `ML/benchmark_trailing_stop_target.py` | ✅ | 2026-04-17 | 2KB | `fb9d2a36` |
| [tests/test_benchmark_trailing_stop_target_quantile.py](tests/test_benchmark_trailing_stop_target_quantile.py) | `ML/benchmark_trailing_stop_target_quantile.py` | ✅ | 2026-04-17 | 8KB | `05ca8680` |
| [tests/test_entry_path_dual_stream_transformer.py](tests/test_entry_path_dual_stream_transformer.py) | `ML/models/entry_path_dual_stream_transformer.py` | ✅ | 2026-04-17 | 1KB | `e9c80f90` |
| [tests/test_entry_path_feature_bank.py](tests/test_entry_path_feature_bank.py) | `ML/entry_path_feature_bank.py` | ✅ | 2026-04-17 | 3KB | `295c827b` |
| [tests/test_entry_path_labels.py](tests/test_entry_path_labels.py) | `processing/label_signals.py` — entry_path_v1 helpers | ✅ | 2026-04-17 | 3KB | `d562f24d` |
| [tests/test_entry_path_loader_seq_len.py](tests/test_entry_path_loader_seq_len.py) | `ML/data_loader.py` — `entry_path_v1` sequence length contract | ✅ | 2026-04-20 | 4KB | `e5f1a2ce` |
| [tests/test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | ✅ | 2026-04-17 | 3KB | `2975dc23` |
| [tests/test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | ✅ | 2026-04-17 | 7KB | `8c945ae2` |
| [tests/test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | ✅ | 2026-04-20 | 7KB | `9d299d99` |
| [tests/test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | ✅ | 2026-04-09 | 12KB | `8390258c` |
| [tests/test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | ✅ | 2026-04-20 | 8KB | `7be46178` |
| [tests/test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | ✅ | 2026-04-12 | 4KB | `142bfe32` |
| [tests/test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | ✅ | 2026-04-10 | 1KB | `b9a1044c` |
| [tests/test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | ✅ | 2026-04-20 | 12KB | `229fb086` |
| [tests/test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | ✅ | 2026-04-10 | 2KB | `294562f5` |
| [tests/test_entry_path_v1_quantile_training.py](tests/test_entry_path_v1_quantile_training.py) |  |  | 2026-04-17 | 9KB | `3de68254` |
| [tests/test_exit_policy_research.py](tests/test_exit_policy_research.py) | `API/exit_policy_research.py` | ✅ | 2026-04-08 | 4KB | `4c75d18c` |
| [tests/test_export_entry_path_v1_quantile_rule.py](tests/test_export_entry_path_v1_quantile_rule.py) |  |  | 2026-04-12 | 2KB | `8a808fd4` |
| [tests/test_export_entry_path_v1_quantile_signals.py](tests/test_export_entry_path_v1_quantile_signals.py) |  |  | 2026-04-12 | 7KB | `237d172f` |
| [tests/test_export_take_skip_trailing_stop_v2_signals.py](tests/test_export_take_skip_trailing_stop_v2_signals.py) |  |  | 2026-04-19 | 4KB | `7bf99876` |
| [tests/test_feature_bank_comparison_diagnostics.py](tests/test_feature_bank_comparison_diagnostics.py) | `ML/feature_bank_comparison_diagnostics.py` | ✅ | 2026-04-20 | 3KB | `9423cafb` |
| [tests/test_feature_importance_diagnostics.py](tests/test_feature_importance_diagnostics.py) | `ML/feature_importance_diagnostics.py` | ✅ | 2026-04-20 | 2KB | `a821e722` |
| [tests/test_feature_screen_entry_path.py](tests/test_feature_screen_entry_path.py) | `ML/feature_screen_entry_path.py` | ✅ | 2026-04-17 | 567B | `b99a62db` |
| [tests/test_generate_signals_research.py](tests/test_generate_signals_research.py) | TB signal selection в `API/generate_signals.py` | ✅ | 2026-04-08 | 831B | `44529dd9` |
| [tests/test_inverse_piecewise.py](tests/test_inverse_piecewise.py) | `processing/normalize.py` + `statistics/signal_tracer.py` — round-trip piecewise | ✅ | 2026-04-05 | 5KB | `30c6b7c6` |
| [tests/test_label_updn.py](tests/test_label_updn.py) | `processing/label_signals.py` — parse_fractal, label_updn | ✅ | 2026-04-05 | 4KB | `be2af292` |
| [tests/test_lib_pic_feature_profiles.py](tests/test_lib_pic_feature_profiles.py) | `ML/lib_pic_feature_profiles.py` | ✅ | 2026-04-20 | 3KB | `24e7d32d` |
| [tests/test_lib_pic_geometry_feature_bank.py](tests/test_lib_pic_geometry_feature_bank.py) | `ML/lib_pic_geometry_feature_bank.py` | ✅ | 2026-04-20 | 2KB | `9c204a8c` |
| [tests/test_lib_pic_path_reaction_feature_bank.py](tests/test_lib_pic_path_reaction_feature_bank.py) | `ML/lib_pic_path_reaction_feature_bank.py` | ✅ | 2026-04-20 | 3KB | `1ab56954` |
| [tests/test_multi_scale_fractal_features.py](tests/test_multi_scale_fractal_features.py) |  |  | 2026-04-18 | 1KB | `de0eeac6` |
| [tests/test_outcome_tasks.py](tests/test_outcome_tasks.py) | outcome tasks в `ML/data_loader.py` | ✅ | 2026-04-08 | 1KB | `8be56a6e` |
| [tests/test_run_trailing_stop_target_matrix.py](tests/test_run_trailing_stop_target_matrix.py) | `ML/run_trailing_stop_target_matrix.py` | ✅ | 2026-04-18 | 7KB | `348a3ac4` |
| [tests/test_run_trailing_stop_target_quantile.py](tests/test_run_trailing_stop_target_quantile.py) | `ML/run_trailing_stop_target_quantile.py` | ✅ | 2026-04-17 | 4KB | `9f4fc6e6` |
| [tests/test_signal_path_atlas.py](tests/test_signal_path_atlas.py) | `API/signal_path_atlas.py` — calendar split, path tensor, archetypes, CLI | ✅ | 2026-04-08 | 38KB | `94234b75` |
| [tests/test_signal_quality_research.py](tests/test_signal_quality_research.py) | `API/signal_quality_research.py` — filter features, variance check, tree, holdout | ✅ | 2026-04-08 | 12KB | `60b730b0` |
| [tests/test_signal_research.py](tests/test_signal_research.py) | `API/signal_research.py` — ATR14, excursions, barriers, split | ✅ | 2026-04-08 | 41KB | `2eeb81b2` |
| [tests/test_signal_tracer_tb.py](tests/test_signal_tracer_tb.py) | TB-specific parsing в `statistics/signal_tracer.py` | ✅ | 2026-04-08 | 2KB | `cfe94d2f` |
| [tests/test_take_skip_lib_pic_feature_matrix.py](tests/test_take_skip_lib_pic_feature_matrix.py) | `ML/run_take_skip_lib_pic_feature_matrix.py` и `ML/models/take_skip_dual_stream_transformer.py` | ✅ | 2026-04-20 | 4KB | `d94925b1` |
| [tests/test_take_skip_trailing_stop_v2_task.py](tests/test_take_skip_trailing_stop_v2_task.py) |  |  | 2026-04-19 | 3KB | `df306b0d` |
| [tests/test_tb_label_invariants.py](tests/test_tb_label_invariants.py) |  |  | 2026-04-13 | 1KB | `46510bd4` |
| [tests/test_track_a_max_out_matrix.py](tests/test_track_a_max_out_matrix.py) | `ML/run_track_a_max_out_matrix.py` | ✅ | 2026-04-17 | 706B | `da3502cc` |
| [tests/test_trade_target_labels.py](tests/test_trade_target_labels.py) | `processing/label_signals.py` — trade target labels | ✅ | 2026-04-08 | 2KB | `6f50053b` |
| [tests/test_trailing_stop_target_labels.py](tests/test_trailing_stop_target_labels.py) | `processing/label_signals.py` — trailing-stop target labels | ✅ | 2026-04-19 | 5KB | `1a95f11e` |
| [tests/test_trailing_stop_target_quantile_model.py](tests/test_trailing_stop_target_quantile_model.py) | `ML/models/trailing_stop_target_quantile_transformer.py` | ✅ | 2026-04-17 | 542B | `692f8730` |
| [tests/test_trailing_stop_target_quantile_task.py](tests/test_trailing_stop_target_quantile_task.py) | `ML/trailing_stop_target_quantile_task.py` и train/evaluate/export wiring | ✅ | 2026-04-17 | 17KB | `329c7acb` |
| [tests/test_trailing_stop_target_task.py](tests/test_trailing_stop_target_task.py) | `ML/trailing_stop_target_task.py` и trailing-stop export/evaluate wiring | ✅ | 2026-04-18 | 11KB | `e7d215dd` |
| [tests/test_triple_barrier_calibration.py](tests/test_triple_barrier_calibration.py) | EV/calibration helper для Triple Barrier | ✅ | 2026-04-08 | 745B | `591d7e79` |
| [tests/test_triple_barrier_first_touch.py](tests/test_triple_barrier_first_touch.py) | first-touch helper для Triple Barrier разметки | ✅ | 2026-04-08 | 1KB | `0aef6c1d` |
| [tests/test_triple_barrier_mt4_execution.py](tests/test_triple_barrier_mt4_execution.py) |  |  | 2026-04-12 | 4KB | `a5e04561` |
| [tests/test_triple_barrier_training.py](tests/test_triple_barrier_training.py) | transfer-learning kwargs для TB обучения | ✅ | 2026-04-08 | 1KB | `3c7dd827` |

## MQL

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [MT/.vscode/settings.json](MT/.vscode/settings.json) |  |  | 2026-02-09 | 928B | `d6834b74` |
| [MT/MQL4/.vscode/settings.json](MT/MQL4/.vscode/settings.json) |  |  | 2026-02-17 | 927B | `c3c0af89` |
| [MT/MQL4/Experts/$o$imple.mq4](MT/MQL4/Experts/$o$imple.mq4) |  |  | 2026-04-19 | 12KB | `0c6b80b3` |
| [MT/MQL4/Include/COUNT.mqh](MT/MQL4/Include/COUNT.mqh) |  |  | 2026-04-08 | 8KB | `687fc943` |
| [MT/MQL4/Include/ERRORs.mqh](MT/MQL4/Include/ERRORs.mqh) |  |  | 2026-03-22 | 20KB | `09c555ab` |
| [MT/MQL4/Include/FUNCTIONS.mqh](MT/MQL4/Include/FUNCTIONS.mqh) |  |  | 2026-03-23 | 15KB | `d2671854` |
| [MT/MQL4/Include/INPUT.mqh](MT/MQL4/Include/INPUT.mqh) |  |  | 2026-03-24 | 22KB | `27ad874f` |
| [MT/MQL4/Include/MAIN.mqh](MT/MQL4/Include/MAIN.mqh) |  |  | 2026-04-19 | 9KB | `8a50dc03` |
| [MT/MQL4/Include/MM.mqh](MT/MQL4/Include/MM.mqh) |  |  | 2026-03-22 | 10KB | `c7d3005a` |
| [MT/MQL4/Include/ORDERS.mqh](MT/MQL4/Include/ORDERS.mqh) |  |  | 2026-03-22 | 40KB | `fbab4671` |
| [MT/MQL4/Include/OUTPUT.mqh](MT/MQL4/Include/OUTPUT.mqh) |  |  | 2026-04-08 | 19KB | `7ff1d32e` |
| [MT/MQL4/Include/SERVICE.mqh](MT/MQL4/Include/SERVICE.mqh) |  |  | 2026-03-23 | 80KB | `cb127d0e` |
| [MT/MQL4/Include/StdLibErr.mqh](MT/MQL4/Include/StdLibErr.mqh) |  |  | 2026-03-22 | 673B | `8a094f85` |
| [MT/MQL4/Include/WinUser32.mqh](MT/MQL4/Include/WinUser32.mqh) |  |  | 2026-03-22 | 17KB | `05085603` |
| [MT/MQL4/Include/head_PIC.mqh](MT/MQL4/Include/head_PIC.mqh) |  |  | 2026-03-31 | 9KB | `b5a78736` |
| [MT/MQL4/Include/iGRAPH.mqh](MT/MQL4/Include/iGRAPH.mqh) |  |  | 2026-03-22 | 38KB | `73d71482` |
| [MT/MQL4/Include/lib_ATR.mqh](MT/MQL4/Include/lib_ATR.mqh) |  |  | 2026-03-22 | 2KB | `77c582a3` |
| [MT/MQL4/Include/lib_Flat.mqh](MT/MQL4/Include/lib_Flat.mqh) |  |  | 2026-03-22 | 13KB | `bc1a865b` |
| [MT/MQL4/Include/lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, торговля | ✅ | 2026-04-19 | 26KB | `2d1d4e92` |
| [MT/MQL4/Include/lib_ML_Signal_TB.mqh](MT/MQL4/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-03-23 | 8KB | `86f9658b` |
| [MT/MQL4/Include/lib_ML_Signal_back.mqh](MT/MQL4/Include/lib_ML_Signal_back.mqh) |  |  | 2026-04-01 | 14KB | `996e3367` |
| [MT/MQL4/Include/lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | ⚠️ | 2026-04-20 | 56KB | `562aa97e` |
| [MT/MQL4/Include/stderror.mqh](MT/MQL4/Include/stderror.mqh) |  |  | 2026-03-22 | 9KB | `1678c440` |
| [MT/MQL4/Include/stdlib.mqh](MT/MQL4/Include/stdlib.mqh) |  |  | 2026-03-22 | 648B | `fa321ad4` |
| [MT/MQL4/Indicators/ATR.mq4](MT/MQL4/Indicators/ATR.mq4) |  |  | 2026-03-22 | 3KB | `dc211832` |
| [MT/MQL4/Indicators/ATR_original.mq4](MT/MQL4/Indicators/ATR_original.mq4) |  |  | 2026-03-22 | 3KB | `efe79c20` |
| [MT/MQL4/Indicators/iATR.mq4](MT/MQL4/Indicators/iATR.mq4) |  |  | 2026-03-22 | 3KB | `2053ea50` |
| [MT/MQL4/Indicators/iATRcycle.mq4](MT/MQL4/Indicators/iATRcycle.mq4) |  |  | 2026-03-22 | 2KB | `3a5033e7` |
| [MT/MQL4/Indicators/iPIC.mq4](MT/MQL4/Indicators/iPIC.mq4) |  |  | 2026-03-31 | 13KB | `2b8088f6` |
| [MT/MQL4/Indicators/iPOC.mq4](MT/MQL4/Indicators/iPOC.mq4) |  |  | 2026-03-22 | 7KB | `4b4df898` |
| [MT/MQL4/Indicators/iVolumeCluster.mq4](MT/MQL4/Indicators/iVolumeCluster.mq4) |  |  | 2026-03-22 | 44KB | `db9c3442` |
| [MT/MQL4/Libraries/StdLibErr.mqh](MT/MQL4/Libraries/StdLibErr.mqh) |  |  | 2026-02-17 | 673B | `01044c60` |
| [MT/MQL4/Libraries/WinUser32.mqh](MT/MQL4/Libraries/WinUser32.mqh) |  |  | 2026-02-17 | 17KB | `84f99057` |
| [MT/MQL4/Libraries/stderror.mqh](MT/MQL4/Libraries/stderror.mqh) |  |  | 2026-02-17 | 9KB | `47505e6c` |
| [MT/MQL4/Libraries/stdlib.mq4](MT/MQL4/Libraries/stdlib.mq4) |  |  | 2026-03-19 | 19KB | `cdb0a440` |
| [MT/MQL4/Libraries/stdlib.mqh](MT/MQL4/Libraries/stdlib.mqh) |  |  | 2026-02-17 | 648B | `5695494a` |
| [MT/MQL4/README.md](MT/MQL4/README.md) |  |  | 2026-02-17 | 146B | `4e32d804` |
| [MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4](MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4) |  |  | 2026-03-19 | 2KB | `7d447b15` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4) |  |  | 2026-03-19 | 3KB | `d0dbff33` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4) |  |  | 2026-03-19 | 4KB | `c0c67ebe` |
| [MT/MQL4/Scripts/ExportOHLC.mq4](MT/MQL4/Scripts/ExportOHLC.mq4) |  |  | 2026-04-02 | 1KB | `3358f6b5` |
| [MT/MQL4/Scripts/HistoryConvertor1002.mq4](MT/MQL4/Scripts/HistoryConvertor1002.mq4) |  |  | 2026-02-17 | 4KB | `2a904122` |
| [MT/MQL4/Scripts/MATLABLOG.mq4](MT/MQL4/Scripts/MATLABLOG.mq4) |  |  | 2026-02-17 | 10KB | `01bef2dd` |
| [MT/MQL4/Scripts/PeriodConverter.mq4](MT/MQL4/Scripts/PeriodConverter.mq4) |  |  | 2026-03-19 | 6KB | `b5a97900` |
| [MT/MQL4/Scripts/trade.mq4](MT/MQL4/Scripts/trade.mq4) |  |  | 2026-02-17 | 1KB | `7c2e252f` |
| [MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh](MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh) |  |  | 2026-03-22 | 3KB | `98d2d8a4` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh) |  |  | 2026-03-24 | 2KB | `ec173678` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh) |  |  | 2026-03-22 | 9KB | `3d047cfe` |
| [MT/MQL4/Trash/iSIG_TURTLE.mqh](MT/MQL4/Trash/iSIG_TURTLE.mqh) |  |  | 2026-03-22 | 3KB | `1b311295` |
| [MT/MQL4/Trash/lib_PIC_old.mqh](MT/MQL4/Trash/lib_PIC_old.mqh) |  |  | 2026-03-22 | 43KB | `59b6536b` |
| [MT/MQL4/Trash/lib_POC.mqh](MT/MQL4/Trash/lib_POC.mqh) |  |  | 2026-03-22 | 7KB | `130bc358` |
| [MT/MQL4/Trash/lib_REZENKO.mqh](MT/MQL4/Trash/lib_REZENKO.mqh) |  |  | 2026-03-22 | 8KB | `8128da38` |
| [MT/MQL4/Trash/lib_TRG.mqh](MT/MQL4/Trash/lib_TRG.mqh) |  |  | 2026-03-22 | 3KB | `e676d2c4` |
| [MT/MQL4/Trash/lib_Triangle.mqh](MT/MQL4/Trash/lib_Triangle.mqh) |  |  | 2026-03-22 | 9KB | `12350503` |
| [MT/MQL4/Trash/lib_ssss.mqh](MT/MQL4/Trash/lib_ssss.mqh) |  |  | 2026-03-22 | 3KB | `6c2e9b73` |
| [MT/MQL5/Include/Arrays/Array.mqh](MT/MQL5/Include/Arrays/Array.mqh) |  |  | 2026-02-04 | 6KB | `dcaa074e` |
| [MT/MQL5/Include/Arrays/ArrayChar.mqh](MT/MQL5/Include/Arrays/ArrayChar.mqh) |  |  | 2026-02-04 | 24KB | `54edbdc1` |
| [MT/MQL5/Include/Arrays/ArrayColor.mqh](MT/MQL5/Include/Arrays/ArrayColor.mqh) |  |  | 2026-02-04 | 24KB | `5de5acca` |
| [MT/MQL5/Include/Arrays/ArrayDatetime.mqh](MT/MQL5/Include/Arrays/ArrayDatetime.mqh) |  |  | 2026-02-04 | 24KB | `28aca33a` |
| [MT/MQL5/Include/Arrays/ArrayDouble.mqh](MT/MQL5/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-02-04 | 24KB | `b442d2c3` |
| [MT/MQL5/Include/Arrays/ArrayFloat.mqh](MT/MQL5/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-02-04 | 24KB | `58db64bf` |
| [MT/MQL5/Include/Arrays/ArrayInt.mqh](MT/MQL5/Include/Arrays/ArrayInt.mqh) |  |  | 2026-02-04 | 24KB | `60c3a599` |
| [MT/MQL5/Include/Arrays/ArrayLong.mqh](MT/MQL5/Include/Arrays/ArrayLong.mqh) |  |  | 2026-02-04 | 24KB | `93c0a2e1` |
| [MT/MQL5/Include/Arrays/ArrayObj.mqh](MT/MQL5/Include/Arrays/ArrayObj.mqh) |  |  | 2026-02-04 | 24KB | `1b604f04` |
| [MT/MQL5/Include/Arrays/ArrayShort.mqh](MT/MQL5/Include/Arrays/ArrayShort.mqh) |  |  | 2026-02-04 | 24KB | `588fba4c` |
| [MT/MQL5/Include/Arrays/ArrayString.mqh](MT/MQL5/Include/Arrays/ArrayString.mqh) |  |  | 2026-02-04 | 24KB | `d7e92876` |
| [MT/MQL5/Include/Arrays/ArrayUChar.mqh](MT/MQL5/Include/Arrays/ArrayUChar.mqh) |  |  | 2026-02-04 | 24KB | `b7d6f43f` |
| [MT/MQL5/Include/Arrays/ArrayUInt.mqh](MT/MQL5/Include/Arrays/ArrayUInt.mqh) |  |  | 2026-02-04 | 24KB | `e6097a29` |
| [MT/MQL5/Include/Arrays/ArrayULong.mqh](MT/MQL5/Include/Arrays/ArrayULong.mqh) |  |  | 2026-02-04 | 24KB | `6c18b082` |
| [MT/MQL5/Include/Arrays/ArrayUShort.mqh](MT/MQL5/Include/Arrays/ArrayUShort.mqh) |  |  | 2026-02-04 | 24KB | `92db202e` |
| [MT/MQL5/Include/Arrays/List.mqh](MT/MQL5/Include/Arrays/List.mqh) |  |  | 2026-02-04 | 20KB | `a173f72b` |
| [MT/MQL5/Include/Arrays/Tree.mqh](MT/MQL5/Include/Arrays/Tree.mqh) |  |  | 2026-02-04 | 13KB | `8824d2cf` |
| [MT/MQL5/Include/Arrays/TreeNode.mqh](MT/MQL5/Include/Arrays/TreeNode.mqh) |  |  | 2026-02-04 | 6KB | `efde8191` |
| [MT/MQL5/Include/COUNT.mqh](MT/MQL5/Include/COUNT.mqh) |  |  | 2026-04-07 | 8KB | `93b61a0a` |
| [MT/MQL5/Include/Canvas/Canvas.mqh](MT/MQL5/Include/Canvas/Canvas.mqh) |  |  | 2026-02-04 | 152KB | `4abe8ef4` |
| [MT/MQL5/Include/Canvas/Canvas3D.mqh](MT/MQL5/Include/Canvas/Canvas3D.mqh) |  |  | 2026-02-04 | 33KB | `f75c5970` |
| [MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh](MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh) |  |  | 2026-02-04 | 35KB | `018e7b5b` |
| [MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh](MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh) |  |  | 2026-02-04 | 11KB | `89f96b38` |
| [MT/MQL5/Include/Canvas/Charts/LineChart.mqh](MT/MQL5/Include/Canvas/Charts/LineChart.mqh) |  |  | 2026-02-04 | 12KB | `ac171461` |
| [MT/MQL5/Include/Canvas/Charts/PieChart.mqh](MT/MQL5/Include/Canvas/Charts/PieChart.mqh) |  |  | 2026-02-04 | 13KB | `81e44597` |
| [MT/MQL5/Include/Canvas/DX/DXBox.mqh](MT/MQL5/Include/Canvas/DX/DXBox.mqh) |  |  | 2026-02-04 | 3KB | `e9cbd560` |
| [MT/MQL5/Include/Canvas/DX/DXBuffers.mqh](MT/MQL5/Include/Canvas/DX/DXBuffers.mqh) |  |  | 2026-02-04 | 4KB | `da4319c8` |
| [MT/MQL5/Include/Canvas/DX/DXData.mqh](MT/MQL5/Include/Canvas/DX/DXData.mqh) |  |  | 2026-02-04 | 3KB | `4a5f2988` |
| [MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh](MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh) |  |  | 2026-02-04 | 12KB | `ce240376` |
| [MT/MQL5/Include/Canvas/DX/DXHandle.mqh](MT/MQL5/Include/Canvas/DX/DXHandle.mqh) |  |  | 2026-02-04 | 8KB | `7a799c15` |
| [MT/MQL5/Include/Canvas/DX/DXInput.mqh](MT/MQL5/Include/Canvas/DX/DXInput.mqh) |  |  | 2026-02-04 | 4KB | `2c890e23` |
| [MT/MQL5/Include/Canvas/DX/DXMath.mqh](MT/MQL5/Include/Canvas/DX/DXMath.mqh) |  |  | 2026-02-04 | 151KB | `cbff51f5` |
| [MT/MQL5/Include/Canvas/DX/DXMesh.mqh](MT/MQL5/Include/Canvas/DX/DXMesh.mqh) |  |  | 2026-02-04 | 15KB | `5bb993cf` |
| [MT/MQL5/Include/Canvas/DX/DXObject.mqh](MT/MQL5/Include/Canvas/DX/DXObject.mqh) |  |  | 2026-02-04 | 1KB | `605a2574` |
| [MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh](MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh) |  |  | 2026-02-04 | 2KB | `262b9064` |
| [MT/MQL5/Include/Canvas/DX/DXShader.mqh](MT/MQL5/Include/Canvas/DX/DXShader.mqh) |  |  | 2026-02-04 | 16KB | `fbeceb80` |
| [MT/MQL5/Include/Canvas/DX/DXSurface.mqh](MT/MQL5/Include/Canvas/DX/DXSurface.mqh) |  |  | 2026-02-04 | 6KB | `75cfc660` |
| [MT/MQL5/Include/Canvas/DX/DXTexture.mqh](MT/MQL5/Include/Canvas/DX/DXTexture.mqh) |  |  | 2026-02-04 | 6KB | `1a3377f2` |
| [MT/MQL5/Include/Canvas/DX/DXUtils.mqh](MT/MQL5/Include/Canvas/DX/DXUtils.mqh) |  |  | 2026-02-04 | 35KB | `81b0d9c9` |
| [MT/MQL5/Include/Canvas/FlameCanvas.mqh](MT/MQL5/Include/Canvas/FlameCanvas.mqh) |  |  | 2026-02-04 | 26KB | `8a0d3427` |
| [MT/MQL5/Include/ChartObjects/ChartObject.mqh](MT/MQL5/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-02-04 | 40KB | `f13eb438` |
| [MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-02-04 | 8KB | `7479429b` |
| [MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh](MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh) |  |  | 2026-02-04 | 16KB | `0d77ef95` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-02-04 | 23KB | `9c0cbe08` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-02-04 | 20KB | `26885f86` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-02-04 | 11KB | `11590972` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh) |  |  | 2026-02-04 | 9KB | `c0255f7d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-02-04 | 17KB | `6ae0eb18` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-02-04 | 16KB | `f4d66975` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-02-04 | 15KB | `7888e00d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-02-04 | 7KB | `d6d59613` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-02-04 | 37KB | `64387446` |
| [MT/MQL5/Include/Charts/Chart.mqh](MT/MQL5/Include/Charts/Chart.mqh) |  |  | 2026-02-04 | 62KB | `c5d96344` |
| [MT/MQL5/Include/Controls/BmpButton.mqh](MT/MQL5/Include/Controls/BmpButton.mqh) |  |  | 2026-02-04 | 11KB | `91c016b1` |
| [MT/MQL5/Include/Controls/Button.mqh](MT/MQL5/Include/Controls/Button.mqh) |  |  | 2026-02-04 | 6KB | `39ba2260` |
| [MT/MQL5/Include/Controls/CheckBox.mqh](MT/MQL5/Include/Controls/CheckBox.mqh) |  |  | 2026-02-04 | 7KB | `cd5744e7` |
| [MT/MQL5/Include/Controls/CheckGroup.mqh](MT/MQL5/Include/Controls/CheckGroup.mqh) |  |  | 2026-02-04 | 13KB | `3f03b33e` |
| [MT/MQL5/Include/Controls/ComboBox.mqh](MT/MQL5/Include/Controls/ComboBox.mqh) |  |  | 2026-02-04 | 13KB | `df4bb90f` |
| [MT/MQL5/Include/Controls/DateDropList.mqh](MT/MQL5/Include/Controls/DateDropList.mqh) |  |  | 2026-02-04 | 14KB | `85818981` |
| [MT/MQL5/Include/Controls/DatePicker.mqh](MT/MQL5/Include/Controls/DatePicker.mqh) |  |  | 2026-02-04 | 10KB | `2e2ce745` |
| [MT/MQL5/Include/Controls/Defines.mqh](MT/MQL5/Include/Controls/Defines.mqh) |  |  | 2026-02-04 | 12KB | `066dbc7d` |
| [MT/MQL5/Include/Controls/Dialog.mqh](MT/MQL5/Include/Controls/Dialog.mqh) |  |  | 2026-02-04 | 37KB | `d1e15482` |
| [MT/MQL5/Include/Controls/Edit.mqh](MT/MQL5/Include/Controls/Edit.mqh) |  |  | 2026-02-04 | 8KB | `aed92dbf` |
| [MT/MQL5/Include/Controls/Label.mqh](MT/MQL5/Include/Controls/Label.mqh) |  |  | 2026-02-04 | 4KB | `1d73f6a0` |
| [MT/MQL5/Include/Controls/ListView.mqh](MT/MQL5/Include/Controls/ListView.mqh) |  |  | 2026-02-04 | 19KB | `3ca374e7` |
| [MT/MQL5/Include/Controls/Panel.mqh](MT/MQL5/Include/Controls/Panel.mqh) |  |  | 2026-02-04 | 5KB | `836869ed` |
| [MT/MQL5/Include/Controls/Picture.mqh](MT/MQL5/Include/Controls/Picture.mqh) |  |  | 2026-02-04 | 5KB | `5e62233e` |
| [MT/MQL5/Include/Controls/RadioButton.mqh](MT/MQL5/Include/Controls/RadioButton.mqh) |  |  | 2026-02-04 | 6KB | `5537db3e` |
| [MT/MQL5/Include/Controls/RadioGroup.mqh](MT/MQL5/Include/Controls/RadioGroup.mqh) |  |  | 2026-02-04 | 13KB | `13d3d9bc` |
| [MT/MQL5/Include/Controls/Rect.mqh](MT/MQL5/Include/Controls/Rect.mqh) |  |  | 2026-02-04 | 10KB | `c0b73dc8` |
| [MT/MQL5/Include/Controls/Scrolls.mqh](MT/MQL5/Include/Controls/Scrolls.mqh) |  |  | 2026-02-04 | 26KB | `18fb49e5` |
| [MT/MQL5/Include/Controls/SpinEdit.mqh](MT/MQL5/Include/Controls/SpinEdit.mqh) |  |  | 2026-02-04 | 10KB | `1e7dded7` |
| [MT/MQL5/Include/Controls/Wnd.mqh](MT/MQL5/Include/Controls/Wnd.mqh) |  |  | 2026-02-04 | 29KB | `0c5fa8a9` |
| [MT/MQL5/Include/Controls/WndClient.mqh](MT/MQL5/Include/Controls/WndClient.mqh) |  |  | 2026-02-04 | 11KB | `25e7cdee` |
| [MT/MQL5/Include/Controls/WndContainer.mqh](MT/MQL5/Include/Controls/WndContainer.mqh) |  |  | 2026-02-04 | 15KB | `e5d88b28` |
| [MT/MQL5/Include/Controls/WndObj.mqh](MT/MQL5/Include/Controls/WndObj.mqh) |  |  | 2026-02-04 | 10KB | `79eb339d` |
| [MT/MQL5/Include/ERRORS.mqh](MT/MQL5/Include/ERRORS.mqh) |  |  | 2026-04-07 | 22B | `f437293a` |
| [MT/MQL5/Include/ERRORs.mqh](MT/MQL5/Include/ERRORs.mqh) |  |  | 2026-04-07 | 20KB | `3a30c213` |
| [MT/MQL5/Include/Expert/Expert.mqh](MT/MQL5/Include/Expert/Expert.mqh) |  |  | 2026-02-04 | 119KB | `667e739c` |
| [MT/MQL5/Include/Expert/ExpertBase.mqh](MT/MQL5/Include/Expert/ExpertBase.mqh) |  |  | 2026-02-04 | 26KB | `15d5fae3` |
| [MT/MQL5/Include/Expert/ExpertMoney.mqh](MT/MQL5/Include/Expert/ExpertMoney.mqh) |  |  | 2026-02-04 | 4KB | `9e6d6c11` |
| [MT/MQL5/Include/Expert/ExpertSignal.mqh](MT/MQL5/Include/Expert/ExpertSignal.mqh) |  |  | 2026-02-04 | 19KB | `b7a7ad81` |
| [MT/MQL5/Include/Expert/ExpertTrade.mqh](MT/MQL5/Include/Expert/ExpertTrade.mqh) |  |  | 2026-02-04 | 6KB | `b2b0f317` |
| [MT/MQL5/Include/Expert/ExpertTrailing.mqh](MT/MQL5/Include/Expert/ExpertTrailing.mqh) |  |  | 2026-02-04 | 1KB | `66a3a25d` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh) |  |  | 2026-02-04 | 3KB | `62d53ce2` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh) |  |  | 2026-02-04 | 3KB | `f8a1fe72` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh) |  |  | 2026-02-04 | 4KB | `38b6869e` |
| [MT/MQL5/Include/Expert/Money/MoneyNone.mqh](MT/MQL5/Include/Expert/Money/MoneyNone.mqh) |  |  | 2026-02-04 | 3KB | `b866ac59` |
| [MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh](MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh) |  |  | 2026-02-04 | 6KB | `22c850e8` |
| [MT/MQL5/Include/Expert/Signal/SignalAC.mqh](MT/MQL5/Include/Expert/Signal/SignalAC.mqh) |  |  | 2026-02-04 | 7KB | `c3fe7a79` |
| [MT/MQL5/Include/Expert/Signal/SignalAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalAMA.mqh) |  |  | 2026-02-04 | 12KB | `a5bbc59b` |
| [MT/MQL5/Include/Expert/Signal/SignalAO.mqh](MT/MQL5/Include/Expert/Signal/SignalAO.mqh) |  |  | 2026-02-04 | 13KB | `cadb934f` |
| [MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh) |  |  | 2026-02-04 | 11KB | `0a9fdc1f` |
| [MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh) |  |  | 2026-02-04 | 11KB | `9b6f9b73` |
| [MT/MQL5/Include/Expert/Signal/SignalCCI.mqh](MT/MQL5/Include/Expert/Signal/SignalCCI.mqh) |  |  | 2026-02-04 | 17KB | `8b02f15b` |
| [MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh) |  |  | 2026-02-04 | 11KB | `27a1b1b3` |
| [MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh](MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh) |  |  | 2026-02-04 | 16KB | `28378510` |
| [MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh](MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh) |  |  | 2026-02-04 | 9KB | `07c314dc` |
| [MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh) |  |  | 2026-02-04 | 11KB | `cc3ea8eb` |
| [MT/MQL5/Include/Expert/Signal/SignalITF.mqh](MT/MQL5/Include/Expert/Signal/SignalITF.mqh) |  |  | 2026-02-04 | 4KB | `0991d92b` |
| [MT/MQL5/Include/Expert/Signal/SignalMA.mqh](MT/MQL5/Include/Expert/Signal/SignalMA.mqh) |  |  | 2026-02-04 | 11KB | `51878396` |
| [MT/MQL5/Include/Expert/Signal/SignalMACD.mqh](MT/MQL5/Include/Expert/Signal/SignalMACD.mqh) |  |  | 2026-02-04 | 19KB | `6794035e` |
| [MT/MQL5/Include/Expert/Signal/SignalRSI.mqh](MT/MQL5/Include/Expert/Signal/SignalRSI.mqh) |  |  | 2026-02-04 | 18KB | `536ef112` |
| [MT/MQL5/Include/Expert/Signal/SignalRVI.mqh](MT/MQL5/Include/Expert/Signal/SignalRVI.mqh) |  |  | 2026-02-04 | 7KB | `89af5171` |
| [MT/MQL5/Include/Expert/Signal/SignalSAR.mqh](MT/MQL5/Include/Expert/Signal/SignalSAR.mqh) |  |  | 2026-02-04 | 7KB | `b84730ef` |
| [MT/MQL5/Include/Expert/Signal/SignalStoch.mqh](MT/MQL5/Include/Expert/Signal/SignalStoch.mqh) |  |  | 2026-02-04 | 19KB | `6cff6dd9` |
| [MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh) |  |  | 2026-02-04 | 11KB | `e8258b51` |
| [MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh](MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh) |  |  | 2026-02-04 | 17KB | `39e3f752` |
| [MT/MQL5/Include/Expert/Signal/SignalWPR.mqh](MT/MQL5/Include/Expert/Signal/SignalWPR.mqh) |  |  | 2026-02-04 | 16KB | `78fc2800` |
| [MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh](MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh) |  |  | 2026-02-04 | 5KB | `39c49839` |
| [MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh](MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh) |  |  | 2026-02-04 | 6KB | `a11d5980` |
| [MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh](MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh) |  |  | 2026-02-04 | 2KB | `bbdc0191` |
| [MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh](MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh) |  |  | 2026-02-04 | 5KB | `b73d3930` |
| [MT/MQL5/Include/FUNCTIONS.mqh](MT/MQL5/Include/FUNCTIONS.mqh) |  |  | 2026-04-07 | 15KB | `b3fce0c5` |
| [MT/MQL5/Include/Files/File.mqh](MT/MQL5/Include/Files/File.mqh) |  |  | 2026-02-04 | 11KB | `9b8c6449` |
| [MT/MQL5/Include/Files/FileBMP.mqh](MT/MQL5/Include/Files/FileBMP.mqh) |  |  | 2026-02-04 | 6KB | `5827c2f4` |
| [MT/MQL5/Include/Files/FileBin.mqh](MT/MQL5/Include/Files/FileBin.mqh) |  |  | 2026-02-04 | 20KB | `916879d9` |
| [MT/MQL5/Include/Files/FilePipe.mqh](MT/MQL5/Include/Files/FilePipe.mqh) |  |  | 2026-02-04 | 12KB | `197bd514` |
| [MT/MQL5/Include/Files/FileTxt.mqh](MT/MQL5/Include/Files/FileTxt.mqh) |  |  | 2026-02-04 | 2KB | `14f5dff2` |
| [MT/MQL5/Include/Generic/ArrayList.mqh](MT/MQL5/Include/Generic/ArrayList.mqh) |  |  | 2026-02-04 | 49KB | `b840b4bc` |
| [MT/MQL5/Include/Generic/HashMap.mqh](MT/MQL5/Include/Generic/HashMap.mqh) |  |  | 2026-02-04 | 25KB | `e22edcd0` |
| [MT/MQL5/Include/Generic/HashSet.mqh](MT/MQL5/Include/Generic/HashSet.mqh) |  |  | 2026-02-04 | 36KB | `d38ceded` |
| [MT/MQL5/Include/Generic/Interfaces/ICollection.mqh](MT/MQL5/Include/Generic/Interfaces/ICollection.mqh) |  |  | 2026-02-04 | 1KB | `402ea83c` |
| [MT/MQL5/Include/Generic/Interfaces/IComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IComparable.mqh) |  |  | 2026-02-04 | 1KB | `aa814da7` |
| [MT/MQL5/Include/Generic/Interfaces/IComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IComparer.mqh) |  |  | 2026-02-04 | 998B | `0cf6f120` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh) |  |  | 2026-02-04 | 1012B | `4979c4c7` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh) |  |  | 2026-02-04 | 1KB | `7e8c86a3` |
| [MT/MQL5/Include/Generic/Interfaces/IList.mqh](MT/MQL5/Include/Generic/Interfaces/IList.mqh) |  |  | 2026-02-04 | 1KB | `e5e9586d` |
| [MT/MQL5/Include/Generic/Interfaces/IMap.mqh](MT/MQL5/Include/Generic/Interfaces/IMap.mqh) |  |  | 2026-02-04 | 1KB | `303da59f` |
| [MT/MQL5/Include/Generic/Interfaces/ISet.mqh](MT/MQL5/Include/Generic/Interfaces/ISet.mqh) |  |  | 2026-02-04 | 1KB | `15eaf0e1` |
| [MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh](MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh) |  |  | 2026-02-04 | 4KB | `4d708d05` |
| [MT/MQL5/Include/Generic/Internal/CompareFunction.mqh](MT/MQL5/Include/Generic/Internal/CompareFunction.mqh) |  |  | 2026-02-04 | 7KB | `b5a08f39` |
| [MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh) |  |  | 2026-02-04 | 1KB | `2f430ea9` |
| [MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh) |  |  | 2026-02-04 | 1KB | `ea37b258` |
| [MT/MQL5/Include/Generic/Internal/EqualFunction.mqh](MT/MQL5/Include/Generic/Internal/EqualFunction.mqh) |  |  | 2026-02-04 | 1KB | `47e2bc02` |
| [MT/MQL5/Include/Generic/Internal/HashFunction.mqh](MT/MQL5/Include/Generic/Internal/HashFunction.mqh) |  |  | 2026-02-04 | 7KB | `87c69022` |
| [MT/MQL5/Include/Generic/Internal/Introsort.mqh](MT/MQL5/Include/Generic/Internal/Introsort.mqh) |  |  | 2026-02-04 | 8KB | `2bd4b00f` |
| [MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh](MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh) |  |  | 2026-02-04 | 3KB | `6d9e6603` |
| [MT/MQL5/Include/Generic/LinkedList.mqh](MT/MQL5/Include/Generic/LinkedList.mqh) |  |  | 2026-02-04 | 20KB | `1cdd7bab` |
| [MT/MQL5/Include/Generic/Queue.mqh](MT/MQL5/Include/Generic/Queue.mqh) |  |  | 2026-02-04 | 29KB | `1313ea7c` |
| [MT/MQL5/Include/Generic/RedBlackTree.mqh](MT/MQL5/Include/Generic/RedBlackTree.mqh) |  |  | 2026-02-04 | 73KB | `3b568c0d` |
| [MT/MQL5/Include/Generic/SortedMap.mqh](MT/MQL5/Include/Generic/SortedMap.mqh) |  |  | 2026-02-04 | 14KB | `5745fcdf` |
| [MT/MQL5/Include/Generic/SortedSet.mqh](MT/MQL5/Include/Generic/SortedSet.mqh) |  |  | 2026-02-04 | 24KB | `0efbc013` |
| [MT/MQL5/Include/Generic/Stack.mqh](MT/MQL5/Include/Generic/Stack.mqh) |  |  | 2026-02-04 | 8KB | `39c47e97` |
| [MT/MQL5/Include/Graphics/Axis.mqh](MT/MQL5/Include/Graphics/Axis.mqh) |  |  | 2026-02-04 | 12KB | `30e582f4` |
| [MT/MQL5/Include/Graphics/ColorGenerator.mqh](MT/MQL5/Include/Graphics/ColorGenerator.mqh) |  |  | 2026-02-04 | 3KB | `204f3a70` |
| [MT/MQL5/Include/Graphics/Curve.mqh](MT/MQL5/Include/Graphics/Curve.mqh) |  |  | 2026-02-04 | 22KB | `5b3764a4` |
| [MT/MQL5/Include/Graphics/Graphic.mqh](MT/MQL5/Include/Graphics/Graphic.mqh) |  |  | 2026-02-04 | 169KB | `0cca00f7` |
| [MT/MQL5/Include/INPUT.mqh](MT/MQL5/Include/INPUT.mqh) |  |  | 2026-04-07 | 22KB | `477b69ca` |
| [MT/MQL5/Include/Indicators/BillWilliams.mqh](MT/MQL5/Include/Indicators/BillWilliams.mqh) |  |  | 2026-02-04 | 32KB | `f57a6107` |
| [MT/MQL5/Include/Indicators/Custom.mqh](MT/MQL5/Include/Indicators/Custom.mqh) |  |  | 2026-02-04 | 7KB | `5e9fbee8` |
| [MT/MQL5/Include/Indicators/Indicator.mqh](MT/MQL5/Include/Indicators/Indicator.mqh) |  |  | 2026-02-04 | 19KB | `1e663d5c` |
| [MT/MQL5/Include/Indicators/Indicators.mqh](MT/MQL5/Include/Indicators/Indicators.mqh) |  |  | 2026-02-04 | 11KB | `e8cd4f31` |
| [MT/MQL5/Include/Indicators/Oscilators.mqh](MT/MQL5/Include/Indicators/Oscilators.mqh) |  |  | 2026-02-04 | 72KB | `18221239` |
| [MT/MQL5/Include/Indicators/Series.mqh](MT/MQL5/Include/Indicators/Series.mqh) |  |  | 2026-02-04 | 12KB | `e0040d48` |
| [MT/MQL5/Include/Indicators/TimeSeries.mqh](MT/MQL5/Include/Indicators/TimeSeries.mqh) |  |  | 2026-02-04 | 61KB | `9aa20382` |
| [MT/MQL5/Include/Indicators/Trend.mqh](MT/MQL5/Include/Indicators/Trend.mqh) |  |  | 2026-02-04 | 72KB | `eb97c7df` |
| [MT/MQL5/Include/Indicators/Volumes.mqh](MT/MQL5/Include/Indicators/Volumes.mqh) |  |  | 2026-02-04 | 17KB | `81921db6` |
| [MT/MQL5/Include/MAIN.mqh](MT/MQL5/Include/MAIN.mqh) |  |  | 2026-04-07 | 10KB | `53cf2ce0` |
| [MT/MQL5/Include/MM.mqh](MT/MQL5/Include/MM.mqh) |  |  | 2026-04-07 | 10KB | `8b02452d` |
| [MT/MQL5/Include/MQL4Compat.mqh](MT/MQL5/Include/MQL4Compat.mqh) |  |  | 2026-04-07 | 28KB | `b26d5ab4` |
| [MT/MQL5/Include/Math/Alglib/alglib.mqh](MT/MQL5/Include/Math/Alglib/alglib.mqh) |  |  | 2026-02-04 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/alglibinternal.mqh](MT/MQL5/Include/Math/Alglib/alglibinternal.mqh) |  |  | 2026-02-04 | 579KB | `175c1183` |
| [MT/MQL5/Include/Math/Alglib/alglibmisc.mqh](MT/MQL5/Include/Math/Alglib/alglibmisc.mqh) |  |  | 2026-02-04 | 119KB | `7466a12d` |
| [MT/MQL5/Include/Math/Alglib/ap.mqh](MT/MQL5/Include/Math/Alglib/ap.mqh) |  |  | 2026-02-04 | 89KB | `a7e4677f` |
| [MT/MQL5/Include/Math/Alglib/arrayresize.mqh](MT/MQL5/Include/Math/Alglib/arrayresize.mqh) |  |  | 2026-02-04 | 3KB | `e64b72cb` |
| [MT/MQL5/Include/Math/Alglib/bitconvert.mqh](MT/MQL5/Include/Math/Alglib/bitconvert.mqh) |  |  | 2026-02-04 | 13KB | `c9dffd4e` |
| [MT/MQL5/Include/Math/Alglib/dataanalysis.mqh](MT/MQL5/Include/Math/Alglib/dataanalysis.mqh) |  |  | 2026-02-04 | 1MB | `596bc4ac` |
| [MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh](MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh) |  |  | 2026-02-04 | 21KB | `ebc422fa` |
| [MT/MQL5/Include/Math/Alglib/diffequations.mqh](MT/MQL5/Include/Math/Alglib/diffequations.mqh) |  |  | 2026-02-04 | 32KB | `e612f10b` |
| [MT/MQL5/Include/Math/Alglib/fasttransforms.mqh](MT/MQL5/Include/Math/Alglib/fasttransforms.mqh) |  |  | 2026-02-04 | 92KB | `f6bbf7c2` |
| [MT/MQL5/Include/Math/Alglib/integration.mqh](MT/MQL5/Include/Math/Alglib/integration.mqh) |  |  | 2026-02-04 | 116KB | `f8600aaa` |
| [MT/MQL5/Include/Math/Alglib/interpolation.mqh](MT/MQL5/Include/Math/Alglib/interpolation.mqh) |  |  | 2026-02-04 | 1MB | `43be4546` |
| [MT/MQL5/Include/Math/Alglib/linalg.mqh](MT/MQL5/Include/Math/Alglib/linalg.mqh) |  |  | 2026-02-04 | 1MB | `73b32040` |
| [MT/MQL5/Include/Math/Alglib/matrix.mqh](MT/MQL5/Include/Math/Alglib/matrix.mqh) |  |  | 2026-02-04 | 45KB | `52f0963f` |
| [MT/MQL5/Include/Math/Alglib/optimization.mqh](MT/MQL5/Include/Math/Alglib/optimization.mqh) |  |  | 2026-02-04 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/solvers.mqh](MT/MQL5/Include/Math/Alglib/solvers.mqh) |  |  | 2026-02-04 | 295KB | `cfe0276c` |
| [MT/MQL5/Include/Math/Alglib/specialfunctions.mqh](MT/MQL5/Include/Math/Alglib/specialfunctions.mqh) |  |  | 2026-02-04 | 235KB | `a4f6fa85` |
| [MT/MQL5/Include/Math/Alglib/statistics.mqh](MT/MQL5/Include/Math/Alglib/statistics.mqh) |  |  | 2026-02-04 | 407KB | `3156c1e5` |
| [MT/MQL5/Include/Math/Fuzzy/dictionary.mqh](MT/MQL5/Include/Math/Fuzzy/dictionary.mqh) |  |  | 2026-02-04 | 8KB | `5fc3e371` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh) |  |  | 2026-02-04 | 17KB | `2b675722` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh) |  |  | 2026-02-04 | 3KB | `b5744882` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh) |  |  | 2026-02-04 | 5KB | `c70f7f31` |
| [MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh) |  |  | 2026-02-04 | 11KB | `0c24ddb8` |
| [MT/MQL5/Include/Math/Fuzzy/helper.mqh](MT/MQL5/Include/Math/Fuzzy/helper.mqh) |  |  | 2026-02-04 | 7KB | `26906afe` |
| [MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh](MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh) |  |  | 2026-02-04 | 7KB | `981fa315` |
| [MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh) |  |  | 2026-02-04 | 22KB | `a4ff1a81` |
| [MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh](MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh) |  |  | 2026-02-04 | 43KB | `db1e7a2e` |
| [MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh](MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh) |  |  | 2026-02-04 | 36KB | `a32fa745` |
| [MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh) |  |  | 2026-02-04 | 13KB | `5502caaf` |
| [MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh](MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh) |  |  | 2026-02-04 | 10KB | `89b49ae6` |
| [MT/MQL5/Include/Math/Stat/Beta.mqh](MT/MQL5/Include/Math/Stat/Beta.mqh) |  |  | 2026-02-04 | 32KB | `9aef6db1` |
| [MT/MQL5/Include/Math/Stat/Binomial.mqh](MT/MQL5/Include/Math/Stat/Binomial.mqh) |  |  | 2026-02-04 | 34KB | `eb1604d4` |
| [MT/MQL5/Include/Math/Stat/Cauchy.mqh](MT/MQL5/Include/Math/Stat/Cauchy.mqh) |  |  | 2026-02-04 | 24KB | `2a5b994b` |
| [MT/MQL5/Include/Math/Stat/ChiSquare.mqh](MT/MQL5/Include/Math/Stat/ChiSquare.mqh) |  |  | 2026-02-04 | 24KB | `31d24602` |
| [MT/MQL5/Include/Math/Stat/Exponential.mqh](MT/MQL5/Include/Math/Stat/Exponential.mqh) |  |  | 2026-02-04 | 24KB | `f1846a90` |
| [MT/MQL5/Include/Math/Stat/F.mqh](MT/MQL5/Include/Math/Stat/F.mqh) |  |  | 2026-02-04 | 26KB | `9e90f69b` |
| [MT/MQL5/Include/Math/Stat/Gamma.mqh](MT/MQL5/Include/Math/Stat/Gamma.mqh) |  |  | 2026-02-04 | 31KB | `358ed8cd` |
| [MT/MQL5/Include/Math/Stat/Geometric.mqh](MT/MQL5/Include/Math/Stat/Geometric.mqh) |  |  | 2026-02-04 | 24KB | `031a2627` |
| [MT/MQL5/Include/Math/Stat/Hypergeometric.mqh](MT/MQL5/Include/Math/Stat/Hypergeometric.mqh) |  |  | 2026-02-04 | 34KB | `2208c6d3` |
| [MT/MQL5/Include/Math/Stat/Logistic.mqh](MT/MQL5/Include/Math/Stat/Logistic.mqh) |  |  | 2026-02-04 | 27KB | `6a74c8a4` |
| [MT/MQL5/Include/Math/Stat/Lognormal.mqh](MT/MQL5/Include/Math/Stat/Lognormal.mqh) |  |  | 2026-02-04 | 28KB | `ca8a59c4` |
| [MT/MQL5/Include/Math/Stat/Math.mqh](MT/MQL5/Include/Math/Stat/Math.mqh) |  |  | 2026-02-04 | 424KB | `65212111` |
| [MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh](MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh) |  |  | 2026-02-04 | 28KB | `27a3e21c` |
| [MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh](MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh) |  |  | 2026-02-04 | 40KB | `ce6d8685` |
| [MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh](MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh) |  |  | 2026-02-04 | 36KB | `96a70f8c` |
| [MT/MQL5/Include/Math/Stat/NoncentralF.mqh](MT/MQL5/Include/Math/Stat/NoncentralF.mqh) |  |  | 2026-02-04 | 34KB | `9990ce6c` |
| [MT/MQL5/Include/Math/Stat/NoncentralT.mqh](MT/MQL5/Include/Math/Stat/NoncentralT.mqh) |  |  | 2026-02-04 | 46KB | `9e154d87` |
| [MT/MQL5/Include/Math/Stat/Normal.mqh](MT/MQL5/Include/Math/Stat/Normal.mqh) |  |  | 2026-02-04 | 39KB | `21ffb41d` |
| [MT/MQL5/Include/Math/Stat/Poisson.mqh](MT/MQL5/Include/Math/Stat/Poisson.mqh) |  |  | 2026-02-04 | 31KB | `df71df52` |
| [MT/MQL5/Include/Math/Stat/Stat.mqh](MT/MQL5/Include/Math/Stat/Stat.mqh) |  |  | 2026-02-04 | 1KB | `c8af779d` |
| [MT/MQL5/Include/Math/Stat/T.mqh](MT/MQL5/Include/Math/Stat/T.mqh) |  |  | 2026-02-04 | 27KB | `d3dbb617` |
| [MT/MQL5/Include/Math/Stat/Uniform.mqh](MT/MQL5/Include/Math/Stat/Uniform.mqh) |  |  | 2026-02-04 | 25KB | `8de48345` |
| [MT/MQL5/Include/Math/Stat/Weibull.mqh](MT/MQL5/Include/Math/Stat/Weibull.mqh) |  |  | 2026-02-04 | 26KB | `ff94f29f` |
| [MT/MQL5/Include/ORDERS.mqh](MT/MQL5/Include/ORDERS.mqh) |  |  | 2026-04-07 | 40KB | `6655a760` |
| [MT/MQL5/Include/OUTPUT.mqh](MT/MQL5/Include/OUTPUT.mqh) |  |  | 2026-04-07 | 18KB | `5a14ae04` |
| [MT/MQL5/Include/OpenCL/OpenCL.mqh](MT/MQL5/Include/OpenCL/OpenCL.mqh) |  |  | 2026-02-04 | 27KB | `a82fa081` |
| [MT/MQL5/Include/SERVICE.mqh](MT/MQL5/Include/SERVICE.mqh) |  |  | 2026-04-07 | 80KB | `aced0492` |
| [MT/MQL5/Include/Strings/String.mqh](MT/MQL5/Include/Strings/String.mqh) |  |  | 2026-02-04 | 13KB | `adbde208` |
| [MT/MQL5/Include/Tools/DateTime.mqh](MT/MQL5/Include/Tools/DateTime.mqh) |  |  | 2026-02-04 | 17KB | `e06f30f0` |
| [MT/MQL5/Include/Trade/AccountInfo.mqh](MT/MQL5/Include/Trade/AccountInfo.mqh) |  |  | 2026-02-04 | 17KB | `336acd5d` |
| [MT/MQL5/Include/Trade/DealInfo.mqh](MT/MQL5/Include/Trade/DealInfo.mqh) |  |  | 2026-02-04 | 15KB | `5f444466` |
| [MT/MQL5/Include/Trade/HistoryOrderInfo.mqh](MT/MQL5/Include/Trade/HistoryOrderInfo.mqh) |  |  | 2026-02-04 | 19KB | `3c45a5f3` |
| [MT/MQL5/Include/Trade/OrderInfo.mqh](MT/MQL5/Include/Trade/OrderInfo.mqh) |  |  | 2026-02-04 | 21KB | `c7977cef` |
| [MT/MQL5/Include/Trade/PositionInfo.mqh](MT/MQL5/Include/Trade/PositionInfo.mqh) |  |  | 2026-02-04 | 15KB | `8f85983c` |
| [MT/MQL5/Include/Trade/SymbolInfo.mqh](MT/MQL5/Include/Trade/SymbolInfo.mqh) |  |  | 2026-02-04 | 35KB | `bb2f2760` |
| [MT/MQL5/Include/Trade/TerminalInfo.mqh](MT/MQL5/Include/Trade/TerminalInfo.mqh) |  |  | 2026-02-04 | 10KB | `db1d371d` |
| [MT/MQL5/Include/Trade/Trade.mqh](MT/MQL5/Include/Trade/Trade.mqh) |  |  | 2026-02-04 | 67KB | `ebefad3b` |
| [MT/MQL5/Include/WinAPI/errhandlingapi.mqh](MT/MQL5/Include/WinAPI/errhandlingapi.mqh) |  |  | 2026-02-04 | 1KB | `9c6abbb5` |
| [MT/MQL5/Include/WinAPI/fileapi.mqh](MT/MQL5/Include/WinAPI/fileapi.mqh) |  |  | 2026-02-04 | 9KB | `ce8862f9` |
| [MT/MQL5/Include/WinAPI/handleapi.mqh](MT/MQL5/Include/WinAPI/handleapi.mqh) |  |  | 2026-02-04 | 1KB | `72389e0e` |
| [MT/MQL5/Include/WinAPI/libloaderapi.mqh](MT/MQL5/Include/WinAPI/libloaderapi.mqh) |  |  | 2026-02-04 | 2KB | `fbe9c927` |
| [MT/MQL5/Include/WinAPI/memoryapi.mqh](MT/MQL5/Include/WinAPI/memoryapi.mqh) |  |  | 2026-02-04 | 5KB | `115d0c9e` |
| [MT/MQL5/Include/WinAPI/processenv.mqh](MT/MQL5/Include/WinAPI/processenv.mqh) |  |  | 2026-02-04 | 1KB | `7788d30f` |
| [MT/MQL5/Include/WinAPI/processthreadsapi.mqh](MT/MQL5/Include/WinAPI/processthreadsapi.mqh) |  |  | 2026-02-04 | 10KB | `5d2c97c4` |
| [MT/MQL5/Include/WinAPI/securitybaseapi.mqh](MT/MQL5/Include/WinAPI/securitybaseapi.mqh) |  |  | 2026-02-04 | 16KB | `a8296031` |
| [MT/MQL5/Include/WinAPI/sysinfoapi.mqh](MT/MQL5/Include/WinAPI/sysinfoapi.mqh) |  |  | 2026-02-04 | 4KB | `f1e35723` |
| [MT/MQL5/Include/WinAPI/winapi.mqh](MT/MQL5/Include/WinAPI/winapi.mqh) |  |  | 2026-02-04 | 827B | `18ecf395` |
| [MT/MQL5/Include/WinAPI/winbase.mqh](MT/MQL5/Include/WinAPI/winbase.mqh) |  |  | 2026-02-04 | 43KB | `80b349f7` |
| [MT/MQL5/Include/WinAPI/windef.mqh](MT/MQL5/Include/WinAPI/windef.mqh) |  |  | 2026-02-04 | 8KB | `b3d4d5b1` |
| [MT/MQL5/Include/WinAPI/wingdi.mqh](MT/MQL5/Include/WinAPI/wingdi.mqh) |  |  | 2026-02-04 | 63KB | `000f20a9` |
| [MT/MQL5/Include/WinAPI/winnt.mqh](MT/MQL5/Include/WinAPI/winnt.mqh) |  |  | 2026-02-04 | 95KB | `0e776dbe` |
| [MT/MQL5/Include/WinAPI/winreg.mqh](MT/MQL5/Include/WinAPI/winreg.mqh) |  |  | 2026-02-04 | 5KB | `3681c95b` |
| [MT/MQL5/Include/WinAPI/winuser.mqh](MT/MQL5/Include/WinAPI/winuser.mqh) |  |  | 2026-02-04 | 81KB | `0a662398` |
| [MT/MQL5/Include/head_PIC.mqh](MT/MQL5/Include/head_PIC.mqh) |  |  | 2026-04-07 | 9KB | `356c8df3` |
| [MT/MQL5/Include/iGRAPH.mqh](MT/MQL5/Include/iGRAPH.mqh) |  |  | 2026-04-07 | 39KB | `f5abe888` |
| [MT/MQL5/Include/lib_ATR.mqh](MT/MQL5/Include/lib_ATR.mqh) |  |  | 2026-04-07 | 2KB | `dcc5b590` |
| [MT/MQL5/Include/lib_Flat.mqh](MT/MQL5/Include/lib_Flat.mqh) |  |  | 2026-04-07 | 13KB | `4536cf5c` |
| [MT/MQL5/Include/lib_ML_Signal.mqh](MT/MQL5/Include/lib_ML_Signal.mqh) |  |  | 2026-04-07 | 14KB | `996e3367` |
| [MT/MQL5/Include/lib_ML_Signal_TB.mqh](MT/MQL5/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-04-07 | 8KB | `86f9658b` |
| [MT/MQL5/Include/lib_PIC.mqh](MT/MQL5/Include/lib_PIC.mqh) |  |  | 2026-04-07 | 56KB | `cc8e0ac9` |
| [MT/MQL5/Include/stderror.mqh](MT/MQL5/Include/stderror.mqh) |  |  | 2026-04-07 | 9KB | `e8590cbe` |
| [MT/MQL5/Include/stdlib.mqh](MT/MQL5/Include/stdlib.mqh) |  |  | 2026-04-07 | 712B | `b86b17a9` |

## Wiki

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [wiki/concepts/signal-archetypes.md](wiki/concepts/signal-archetypes.md) |  | 2026-04-10 | 3KB | `01af7dbd` |
| [wiki/index.md](wiki/index.md) |  | 2026-04-20 | 1KB | `1eb92271` |
| [wiki/log.md](wiki/log.md) |  | 2026-04-20 | 10KB | `db28f418` |
| [wiki/research/execution-tracks.md](wiki/research/execution-tracks.md) |  | 2026-04-20 | 39KB | `6f15b726` |
| [wiki/research/signal-quality-research.md](wiki/research/signal-quality-research.md) |  | 2026-04-10 | 8KB | `a5355801` |
| [wiki/wiki.py](wiki/wiki.py) |  | 2026-04-10 | 18KB | `4bcfb243` |

## Agent Config

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.claude/memory/MEMORY.md](.claude/memory/MEMORY.md) |  | 2026-04-02 | 694B | `ca8a831e` |
| [.claude/memory/feedback_cyclic_encoding.md](.claude/memory/feedback_cyclic_encoding.md) |  | 2026-04-05 | 1KB | `7e05fc7c` |
| [.claude/memory/feedback_ml_approach.md](.claude/memory/feedback_ml_approach.md) |  | 2026-04-02 | 2KB | `1480e999` |
| [.claude/memory/feedback_no_auto_commit.md](.claude/memory/feedback_no_auto_commit.md) |  | 2026-04-05 | 752B | `e07d0571` |
| [.claude/memory/feedback_russian_reports.md](.claude/memory/feedback_russian_reports.md) |  | 2026-04-05 | 1KB | `e4464dc5` |
| [.claude/memory/project_ml_status.md](.claude/memory/project_ml_status.md) |  | 2026-04-13 | 2KB | `07fbf165` |
| [.claude/memory/user_profile.md](.claude/memory/user_profile.md) |  | 2026-03-18 | 890B | `8ca314d1` |
| [.claude/settings.json](.claude/settings.json) |  | 2026-04-16 | 742B | `8100fea3` |
| [.claude/settings.local.json](.claude/settings.local.json) |  | 2026-03-17 | 99B | `997fe658` |
| [.claude/skills/brainstorming/SKILL.md](.claude/skills/brainstorming/SKILL.md) |  | 2026-03-17 | 10KB | `3f82fad8` |
| [.claude/skills/brainstorming/spec-document-reviewer-prompt.md](.claude/skills/brainstorming/spec-document-reviewer-prompt.md) |  | 2026-03-17 | 1KB | `06b0277a` |
| [.claude/skills/brainstorming/visual-companion.md](.claude/skills/brainstorming/visual-companion.md) |  | 2026-03-17 | 11KB | `37305635` |
| [.claude/skills/csv-processing/SKILL.md](.claude/skills/csv-processing/SKILL.md) |  | 2026-04-16 | 2KB | `ae2e22e1` |
| [.claude/skills/dispatching-parallel-agents/SKILL.md](.claude/skills/dispatching-parallel-agents/SKILL.md) |  | 2026-03-17 | 6KB | `645864ea` |
| [.claude/skills/executing-plans/SKILL.md](.claude/skills/executing-plans/SKILL.md) |  | 2026-03-17 | 2KB | `1eedec6a` |
| [.claude/skills/finishing-a-development-branch/SKILL.md](.claude/skills/finishing-a-development-branch/SKILL.md) |  | 2026-03-02 | 4KB | `5068e5c2` |
| [.claude/skills/jupyter-processing/SKILL.md](.claude/skills/jupyter-processing/SKILL.md) |  | 2026-04-16 | 3KB | `6e2f7f1a` |
| [.claude/skills/receiving-code-review/SKILL.md](.claude/skills/receiving-code-review/SKILL.md) |  | 2026-03-02 | 6KB | `7bdb2c2c` |
| [.claude/skills/requesting-code-review/SKILL.md](.claude/skills/requesting-code-review/SKILL.md) |  | 2026-03-17 | 2KB | `03ae853d` |
| [.claude/skills/requesting-code-review/code-reviewer.md](.claude/skills/requesting-code-review/code-reviewer.md) |  | 2026-03-02 | 3KB | `a17ab05f` |
| [.claude/skills/stage-reporting/SKILL.md](.claude/skills/stage-reporting/SKILL.md) |  | 2026-04-16 | 4KB | `12338720` |
| [.claude/skills/subagent-driven-development/SKILL.md](.claude/skills/subagent-driven-development/SKILL.md) |  | 2026-03-18 | 11KB | `0a35f71a` |
| [.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md](.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md) |  | 2026-03-17 | 1KB | `923a1c03` |
| [.claude/skills/subagent-driven-development/implementer-prompt.md](.claude/skills/subagent-driven-development/implementer-prompt.md) |  | 2026-03-18 | 4KB | `4c6c977c` |
| [.claude/skills/subagent-driven-development/spec-reviewer-prompt.md](.claude/skills/subagent-driven-development/spec-reviewer-prompt.md) |  | 2026-03-02 | 1KB | `70330453` |
| [.claude/skills/systematic-debugging/CREATION-LOG.md](.claude/skills/systematic-debugging/CREATION-LOG.md) |  | 2026-03-02 | 4KB | `c0a1bd0d` |
| [.claude/skills/systematic-debugging/SKILL.md](.claude/skills/systematic-debugging/SKILL.md) |  | 2026-03-02 | 9KB | `05a9d191` |
| [.claude/skills/systematic-debugging/condition-based-waiting.md](.claude/skills/systematic-debugging/condition-based-waiting.md) |  | 2026-03-02 | 3KB | `84c01c63` |
| [.claude/skills/systematic-debugging/defense-in-depth.md](.claude/skills/systematic-debugging/defense-in-depth.md) |  | 2026-03-02 | 3KB | `f1213004` |
| [.claude/skills/systematic-debugging/root-cause-tracing.md](.claude/skills/systematic-debugging/root-cause-tracing.md) |  | 2026-03-02 | 5KB | `aa760aed` |
| [.claude/skills/systematic-debugging/test-academic.md](.claude/skills/systematic-debugging/test-academic.md) |  | 2026-03-02 | 653B | `f93a550e` |
| [.claude/skills/systematic-debugging/test-pressure-1.md](.claude/skills/systematic-debugging/test-pressure-1.md) |  | 2026-03-02 | 1KB | `3fbf9df1` |
| [.claude/skills/systematic-debugging/test-pressure-2.md](.claude/skills/systematic-debugging/test-pressure-2.md) |  | 2026-03-02 | 2KB | `dc10de1a` |
| [.claude/skills/systematic-debugging/test-pressure-3.md](.claude/skills/systematic-debugging/test-pressure-3.md) |  | 2026-03-02 | 2KB | `4c1b5df1` |
| [.claude/skills/test-driven-development/SKILL.md](.claude/skills/test-driven-development/SKILL.md) |  | 2026-03-02 | 9KB | `847d3947` |
| [.claude/skills/test-driven-development/testing-anti-patterns.md](.claude/skills/test-driven-development/testing-anti-patterns.md) |  | 2026-03-02 | 8KB | `70d9ec22` |
| [.claude/skills/update-docs-on-code-change/SKILL.md](.claude/skills/update-docs-on-code-change/SKILL.md) |  | 2026-04-17 | 8KB | `37b3b5b2` |
| [.claude/skills/using-git-worktrees/SKILL.md](.claude/skills/using-git-worktrees/SKILL.md) |  | 2026-03-02 | 5KB | `fb693c90` |
| [.claude/skills/using-superpowers/SKILL.md](.claude/skills/using-superpowers/SKILL.md) |  | 2026-03-17 | 5KB | `ecc31260` |
| [.claude/skills/using-superpowers/references/codex-tools.md](.claude/skills/using-superpowers/references/codex-tools.md) |  | 2026-03-17 | 960B | `70fe0aeb` |
| [.claude/skills/using-superpowers/references/gemini-tools.md](.claude/skills/using-superpowers/references/gemini-tools.md) |  | 2026-03-17 | 1KB | `5f43b981` |
| [.claude/skills/verification-before-completion/SKILL.md](.claude/skills/verification-before-completion/SKILL.md) |  | 2026-03-02 | 4KB | `830cfbe3` |
| [.claude/skills/wiki/SKILL.md](.claude/skills/wiki/SKILL.md) |  | 2026-04-16 | 8KB | `5e368d44` |
| [.claude/skills/writing-plans/SKILL.md](.claude/skills/writing-plans/SKILL.md) |  | 2026-03-17 | 5KB | `26d892e5` |
| [.claude/skills/writing-plans/plan-document-reviewer-prompt.md](.claude/skills/writing-plans/plan-document-reviewer-prompt.md) |  | 2026-03-17 | 1KB | `412ec6bb` |
| [.claude/skills/writing-skills/SKILL.md](.claude/skills/writing-skills/SKILL.md) |  | 2026-03-02 | 21KB | `5cfc05f1` |
| [.claude/skills/writing-skills/anthropic-best-practices.md](.claude/skills/writing-skills/anthropic-best-practices.md) |  | 2026-03-02 | 44KB | `95ea2856` |
| [.claude/skills/writing-skills/examples/CLAUDE_MD_TESTING.md](.claude/skills/writing-skills/examples/CLAUDE_MD_TESTING.md) |  | 2026-03-02 | 5KB | `9d292f89` |
| [.claude/skills/writing-skills/persuasion-principles.md](.claude/skills/writing-skills/persuasion-principles.md) |  | 2026-03-02 | 5KB | `672d4b80` |
| [.claude/skills/writing-skills/testing-skills-with-subagents.md](.claude/skills/writing-skills/testing-skills-with-subagents.md) |  | 2026-03-02 | 12KB | `24475f71` |
| [.kilocode/mcp.json](.kilocode/mcp.json) |  | 2026-04-10 | 481B | `14bc1e7d` |
| [.kilocode/package.json](.kilocode/package.json) |  | 2026-04-12 | 59B | `05e47241` |
| [.kilocode/rules-architect/user_rules.md](.kilocode/rules-architect/user_rules.md) |  | 2026-03-26 | 1KB | `351b6484` |
| [.kilocode/rules-ask/user_rules.md](.kilocode/rules-ask/user_rules.md) |  | 2026-03-26 | 1KB | `351b6484` |

