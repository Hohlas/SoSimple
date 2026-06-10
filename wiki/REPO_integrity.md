# REPO Integrity Map — SoSimple
> Auto-generated 2026-06-10 07:20 UTC · git `6b633fc`
> Refresh: `python wiki/wiki.py generate`  ·  Verify: `python wiki/wiki.py verify`

## Agent Access Protocol

1. Read this file first to get a project map (what exists, where, integrity hash).
2. Run `python wiki/wiki.py verify` to detect files changed since last index.
3. Navigate via paths in the tables; use `wiki/research/` and `wiki/concepts/` for synthesized knowledge.
4. After modifying significant files, run `generate` and commit `REPO_integrity.md`.

**Tracked**: 1405 files  ·  **Commit**: `6b633fc`  ·  **Generated**: 2026-06-10 07:20 UTC

## Root Docs

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [AGENTS.md](AGENTS.md) |  | 2026-06-07 | 14KB | `8d7db785` |
| [CHANGELOG.md](CHANGELOG.md) |  | 2026-06-06 | 159KB | `5dbfed89` |
| [CLAUDE.md](CLAUDE.md) |  | 2026-05-30 | 288B | `9c4cf5c6` |
| [CONTEXT_HANDOFF.md](CONTEXT_HANDOFF.md) |  | 2026-06-03 | 6KB | `16483aaf` |
| [MODULE_INDEX.md](MODULE_INDEX.md) |  | 2026-06-10 | 42KB | `68202968` |
| [README.md](README.md) |  | 2026-05-30 | 1KB | `1b96a51c` |

## Documentation

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/API/api_server.py.md](docs/API/api_server.py.md) | Документация экспериментального REST API inference-пути | 2026-05-30 | 1KB | `c7573738` |
| [docs/API/telemetry_signal_watcher.py.md](docs/API/telemetry_signal_watcher.py.md) |  | 2026-05-30 | 20KB | `bb5a5097` |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам | 2026-06-06 | 26KB | `b9448b9f` |
| [docs/ML/baseline_candidate_source.py.md](docs/ML/baseline_candidate_source.py.md) |  | 2026-06-03 | 906B | `405058a5` |
| [docs/ML/baseline_experiments.py.md](docs/ML/baseline_experiments.py.md) |  | 2026-05-30 | 2KB | `8dc50028` |
| [docs/ML/benchmark_cross_instrument_robustness.py.md](docs/ML/benchmark_cross_instrument_robustness.py.md) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты | 2026-05-30 | 3KB | `facaa586` |
| [docs/ML/benchmark_entry_path_all_rows_ranking.py.md](docs/ML/benchmark_entry_path_all_rows_ranking.py.md) | All-rows ranking benchmark без offline `signal != 0` gate | 2026-05-30 | 1KB | `0bc4a19a` |
| [docs/ML/benchmark_entry_path_causal_surrogate.py.md](docs/ML/benchmark_entry_path_causal_surrogate.py.md) | Causal surrogate benchmark для offline `label_all().signal` | 2026-05-30 | 1KB | `2fd85fde` |
| [docs/ML/benchmark_entry_path_direct_bar_model.py.md](docs/ML/benchmark_entry_path_direct_bar_model.py.md) | Direct BUY/SELL/SKIP benchmark для каждого бара | 2026-05-30 | 1KB | `531300e8` |
| [docs/ML/benchmark_entry_path_signal_only_ablation.py.md](docs/ML/benchmark_entry_path_signal_only_ablation.py.md) | Ablation benchmark вклада offline `signal != 0` | 2026-05-30 | 2KB | `f5a2fa77` |
| [docs/ML/benchmark_execution_policy_v2.py.md](docs/ML/benchmark_execution_policy_v2.py.md) | Benchmark вариантов выхода для готовых ML-сигналов | 2026-05-30 | 4KB | `03bec021` |
| [docs/ML/benchmark_signal_export_parity.py.md](docs/ML/benchmark_signal_export_parity.py.md) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log | 2026-05-30 | 2KB | `5c430c60` |
| [docs/ML/benchmark_system_correlation.py.md](docs/ML/benchmark_system_correlation.py.md) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам | 2026-05-30 | 4KB | `a0880c32` |
| [docs/ML/benchmark_take_skip_lib_pic_selection.py.md](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | Внешний отбор `take_skip_v2` по признакам `lib_PIC` | 2026-05-30 | 2KB | `085cc039` |
| [docs/ML/benchmark_telemetry_frequency_calibration.py.md](docs/ML/benchmark_telemetry_frequency_calibration.py.md) | Калибровка частого diagnostic telemetry режима | 2026-05-30 | 2KB | `ca3c7c56` |
| [docs/ML/conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы | 2026-05-30 | 5KB | `dca1ea47` |
| [docs/ML/export_entry_path_predictions.py.md](docs/ML/export_entry_path_predictions.py.md) | Inference entry_path-моделей на arbitrary labeled CSV без переобучения | 2026-05-30 | 4KB | `594cc77b` |
| [docs/ML/feature_bank_comparison_diagnostics.py.md](docs/ML/feature_bank_comparison_diagnostics.py.md) | Сравнение baseline/geometry/path feature-bank вариантов | 2026-05-30 | 2KB | `5bfce017` |
| [docs/ML/feature_importance_diagnostics.py.md](docs/ML/feature_importance_diagnostics.py.md) | Диагностика важности групп текущих fractal-признаков | 2026-05-30 | 2KB | `fd76dcaf` |
| [docs/ML/lib_pic_feature_profiles.py.md](docs/ML/lib_pic_feature_profiles.py.md) | Единая сборка профилей признаков `lib_PIC` | 2026-05-30 | 2KB | `3947bb49` |
| [docs/ML/lib_pic_geometry_feature_bank.py.md](docs/ML/lib_pic_geometry_feature_bank.py.md) | Производные признаки геометрии уровней `lib_PIC` | 2026-05-30 | 3KB | `1da45c79` |
| [docs/ML/lib_pic_path_reaction_feature_bank.py.md](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | Производные признаки исторической реакции цены `Up/Dn` после уровней | 2026-05-30 | 2KB | `9d18b5e1` |
| [docs/ML/live_safe_audit.py.md](docs/ML/live_safe_audit.py.md) | Core-типы live-safe audit и свод feature verdict → system verdict | 2026-05-30 | 556B | `8341abc1` |
| [docs/ML/live_safe_audit_registry.py.md](docs/ML/live_safe_audit_registry.py.md) | Реестр прибыльных ML-систем для повторного live-safe audit | 2026-05-30 | 469B | `8d81d796` |
| [docs/ML/model_sweep_candidate_source.py.md](docs/ML/model_sweep_candidate_source.py.md) |  | 2026-06-03 | 970B | `8867924b` |
| [docs/ML/neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики | 2026-06-06 | 26KB | `6eca467d` |
| [docs/ML/online_tester_reconciliation.py.md](docs/ML/online_tester_reconciliation.py.md) |  | 2026-05-30 | 3KB | `28aa6c93` |
| [docs/ML/prepare_entry_path_mt4_parity.py.md](docs/ML/prepare_entry_path_mt4_parity.py.md) | Подготовка frozen `entry_path_v1_live_safe + A @ 7.5%` export для MT4 parity | 2026-05-30 | 1KB | `5e881e55` |
| [docs/ML/run_entry_path_live_safe_retrain.py.md](docs/ML/run_entry_path_live_safe_retrain.py.md) |  | 2026-05-30 | 2KB | `72abe04a` |
| [docs/ML/run_entry_path_quantile_live_safe_retrain.py.md](docs/ML/run_entry_path_quantile_live_safe_retrain.py.md) |  | 2026-05-30 | 2KB | `82076ca6` |
| [docs/ML/run_live_safe_ml_audit.py.md](docs/ML/run_live_safe_ml_audit.py.md) | CLI для audit inventory, feature trace, legacy replay и verdict | 2026-05-30 | 708B | `445a83ae` |
| [docs/ML/run_take_skip_lib_pic_feature_matrix.py.md](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | Training matrix для `take_skip_v2` с признаками `lib_PIC` внутри модели | 2026-05-30 | 4KB | `8d21f1a7` |
| [docs/ML/run_take_skip_original_contour_feature_matrix.py.md](docs/ML/run_take_skip_original_contour_feature_matrix.py.md) | Training matrix для старого single-tensor `take_skip_v2` контура + `lib_PIC` признаки | 2026-05-30 | 6KB | `133b0f2e` |
| [docs/ML/stage09_stability_refreeze.py.md](docs/ML/stage09_stability_refreeze.py.md) |  | 2026-06-03 | 1KB | `833582b8` |
| [docs/ML/stage10_frozen_test_oos.py.md](docs/ML/stage10_frozen_test_oos.py.md) |  | 2026-06-03 | 1KB | `9fc4ae1d` |
| [docs/ML/telemetry_daily_reconciliation.py.md](docs/ML/telemetry_daily_reconciliation.py.md) | Ежедневная сверка telemetry ML-сигналов и MT4 MLP-логов | 2026-05-30 | 4KB | `b02fd806` |
| [docs/MT/lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC | 2026-05-30 | 8KB | `e40ecf3c` |
| [docs/MT/ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) | 2026-05-30 | 25KB | `aa7313db` |
| [docs/MT/trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() | 2026-05-30 | 45KB | `30e59566` |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document | 2026-05-30 | 4KB | `dba0c943` |
| [docs/README.md](docs/README.md) | Карта артефактов `docs/` и правила обновления | 2026-06-05 | 4KB | `ccce04ba` |
| [docs/audit/2026-05-18-codex-direct-direction-chain-audit.md](docs/audit/2026-05-18-codex-direct-direction-chain-audit.md) |  | 2026-05-30 | 8KB | `4771493f` |
| [docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md](docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md) |  | 2026-05-30 | 6KB | `799c481b` |
| [docs/audit/2026-05-18-consolidated-audit.md](docs/audit/2026-05-18-consolidated-audit.md) |  | 2026-05-30 | 16KB | `68633e6f` |
| [docs/audit/2026-05-18-kimi-independent-audit.md](docs/audit/2026-05-18-kimi-independent-audit.md) |  | 2026-05-30 | 15KB | `7dabafae` |
| [docs/audit/2026-05-18-kimi-phase-ii-plan.md](docs/audit/2026-05-18-kimi-phase-ii-plan.md) |  | 2026-05-30 | 17KB | `74b6b95a` |
| [docs/audit/2026-05-18-redo-prompt.md](docs/audit/2026-05-18-redo-prompt.md) |  | 2026-05-30 | 19KB | `6ca4032a` |
| [docs/audit/2026-05-24-methodology-review-notes.md](docs/audit/2026-05-24-methodology-review-notes.md) | Замечания по `docs/methodology/` и trigger-у `ml-methodology` | 2026-05-30 | 8KB | `6c948cab` |
| [docs/audit/2026-06-09-fractal-stop-fav-target-spec-audit.md](docs/audit/2026-06-09-fractal-stop-fav-target-spec-audit.md) | Вердикт по спецификации Fractal Stop + Fav Target | 2026-06-10 | 16KB | `ac300a57` |
| [docs/audit/README.md](docs/audit/README.md) | Карта audit-артефактов и правил их обновления | 2026-06-09 | 1KB | `f975017a` |
| [docs/audit/old_plan_example.md](docs/audit/old_plan_example.md) | Старый пример ML-плана для сравнения полноты структуры | 2026-05-30 | 34KB | `bdb0edad` |
| [docs/audit/to_do.md](docs/audit/to_do.md) |  | 2026-06-10 | 14KB | `10a64f0b` |
| [docs/dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv | 2026-06-05 | 14KB | `11dc384e` |
| [docs/methodology/00-research-management.md](docs/methodology/00-research-management.md) |  | 2026-06-03 | 4KB | `3b1e8db8` |
| [docs/methodology/01-raw-data-inventory.md](docs/methodology/01-raw-data-inventory.md) |  | 2026-05-30 | 5KB | `6bf55f21` |
| [docs/methodology/02-data-pipeline.md](docs/methodology/02-data-pipeline.md) |  | 2026-05-30 | 5KB | `0f86e056` |
| [docs/methodology/03-feature-contract-leakage.md](docs/methodology/03-feature-contract-leakage.md) |  | 2026-06-03 | 27KB | `aca8e4cb` |
| [docs/methodology/03b-feature-selection.md](docs/methodology/03b-feature-selection.md) |  | 2026-06-03 | 6KB | `657d35b9` |
| [docs/methodology/04-labeling.md](docs/methodology/04-labeling.md) |  | 2026-06-03 | 9KB | `dd9fcf87` |
| [docs/methodology/05-eda-data-quality.md](docs/methodology/05-eda-data-quality.md) |  | 2026-06-05 | 6KB | `8edd1fa8` |
| [docs/methodology/06-temporal-split.md](docs/methodology/06-temporal-split.md) |  | 2026-05-30 | 4KB | `fd036064` |
| [docs/methodology/07-baseline-first.md](docs/methodology/07-baseline-first.md) |  | 2026-06-03 | 3KB | `cb983afd` |
| [docs/methodology/08-model-development.md](docs/methodology/08-model-development.md) |  | 2026-06-05 | 7KB | `b9f0a29f` |
| [docs/methodology/09-validation-freeze.md](docs/methodology/09-validation-freeze.md) |  | 2026-06-03 | 3KB | `23603432` |
| [docs/methodology/10-frozen-test-oos.md](docs/methodology/10-frozen-test-oos.md) |  | 2026-06-03 | 3KB | `da6c66c6` |
| [docs/methodology/11-robustness.md](docs/methodology/11-robustness.md) |  | 2026-05-30 | 2KB | `6260afba` |
| [docs/methodology/12-backtest-costs.md](docs/methodology/12-backtest-costs.md) |  | 2026-06-03 | 7KB | `23dbbae4` |
| [docs/methodology/13-export-mt4-parity.md](docs/methodology/13-export-mt4-parity.md) |  | 2026-05-30 | 2KB | `c1028a82` |
| [docs/methodology/14-forward-test-online.md](docs/methodology/14-forward-test-online.md) |  | 2026-05-30 | 2KB | `c11c0bbb` |
| [docs/methodology/15-monitoring-retraining.md](docs/methodology/15-monitoring-retraining.md) |  | 2026-05-30 | 3KB | `c9457c9b` |
| [docs/methodology/16-reporting-audit.md](docs/methodology/16-reporting-audit.md) |  | 2026-05-30 | 3KB | `3d06dc34` |
| [docs/methodology/A1-checklist-dev.md](docs/methodology/A1-checklist-dev.md) |  | 2026-06-03 | 3KB | `c8f22299` |
| [docs/methodology/A2-checklist-audit.md](docs/methodology/A2-checklist-audit.md) |  | 2026-06-05 | 2KB | `06ece850` |
| [docs/methodology/A3-typical-false-conclusions.md](docs/methodology/A3-typical-false-conclusions.md) |  | 2026-06-03 | 3KB | `a1bbb839` |
| [docs/methodology/A4-verdicts-stop-conditions.md](docs/methodology/A4-verdicts-stop-conditions.md) |  | 2026-05-30 | 2KB | `f236f9e2` |
| [docs/methodology/README.md](docs/methodology/README.md) | Методика разработки и аудита ML-моделей ТС (16 этапов + приложения) | 2026-06-03 | 6KB | `c83472a1` |
| [docs/processing/fractal_preprocessing.py.md](docs/processing/fractal_preprocessing.py.md) | Документация общей сортировки фракталов | 2026-05-30 | 856B | `876e71c9` |
| [docs/processing/label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора | 2026-06-06 | 4KB | `22a08f92` |
| [docs/processing/label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict | 2026-05-30 | 1KB | `3fd26730` |
| [docs/processing/normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков | 2026-06-05 | 5KB | `5e8f661c` |
| [docs/processing/online_causal_preprocessing.py.md](docs/processing/online_causal_preprocessing.py.md) | Документация online-safe preprocessing | 2026-05-30 | 2KB | `a59d1bf7` |
| [docs/schemas/fractal_v23.schema.json](docs/schemas/fractal_v23.schema.json) |  | 2026-06-05 | 4KB | `deb79fbb` |
| [docs/schemas/fractal_v24_raw_price.schema.json](docs/schemas/fractal_v24_raw_price.schema.json) |  | 2026-06-05 | 5KB | `e3539efe` |
| [docs/statistics/EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу | 2026-05-30 | 17KB | `914b3a5e` |
| [docs/statistics/signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF | 2026-05-30 | 7KB | `052eb4f7` |
| [docs/statistics/statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике | 2026-05-30 | 6KB | `9835a477` |
| [docs/superpowers/plans/2026-03-22-triple-barrier.md](docs/superpowers/plans/2026-03-22-triple-barrier.md) |  | 2026-05-30 | 28KB | `fe31fa4e` |
| [docs/superpowers/plans/2026-03-25-updn-denormalization.md](docs/superpowers/plans/2026-03-25-updn-denormalization.md) |  | 2026-05-30 | 19KB | `01d8efee` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md) |  | 2026-05-30 | 22KB | `ba50388e` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md) |  | 2026-05-30 | 9KB | `7ed11b5f` |
| [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](docs/superpowers/plans/2026-04-01-signal-research-variant-2.md) |  | 2026-05-30 | 29KB | `09aa7ec8` |
| [docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md](docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md) |  | 2026-05-30 | 20KB | `43d44dc5` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-05-30 | 19KB | `b25009ee` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3.md) |  | 2026-05-30 | 3KB | `3b40fae8` |
| [docs/superpowers/plans/2026-04-03-signal-path-atlas.md](docs/superpowers/plans/2026-04-03-signal-path-atlas.md) |  | 2026-05-30 | 39KB | `b0fea2ba` |
| [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](docs/superpowers/plans/2026-04-03-signal-quality-filter.md) |  | 2026-05-30 | 39KB | `6518f11b` |
| [docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md](docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md) |  | 2026-05-30 | 7KB | `636d1a67` |
| [docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md](docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md) |  | 2026-05-30 | 7KB | `af4ec829` |
| [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md) |  | 2026-05-30 | 11KB | `44d803a8` |
| [docs/superpowers/plans/2026-04-07-validation-first-research.md](docs/superpowers/plans/2026-04-07-validation-first-research.md) |  | 2026-05-30 | 10KB | `c0b29ff8` |
| [docs/superpowers/plans/2026-04-08-entry-path-v1.md](docs/superpowers/plans/2026-04-08-entry-path-v1.md) |  | 2026-05-30 | 28KB | `86fb358e` |
| [docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md](docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-05-30 | 15KB | `e9cb346d` |
| [docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md](docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md) |  | 2026-05-30 | 22KB | `0a35f491` |
| [docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md](docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md) |  | 2026-05-30 | 29KB | `1ab66152` |
| [docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md](docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md) |  | 2026-05-30 | 26KB | `9b5a8151` |
| [docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md](docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md) |  | 2026-05-30 | 31KB | `155a7325` |
| [docs/superpowers/plans/2026-04-10-entry-path-cqr.md](docs/superpowers/plans/2026-04-10-entry-path-cqr.md) |  | 2026-05-30 | 24KB | `0f832c74` |
| [docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md](docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md) |  | 2026-05-30 | 15KB | `fe2b2167` |
| [docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md](docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md) |  | 2026-05-30 | 14KB | `5b49271e` |
| [docs/superpowers/plans/2026-04-13-early-timeout-bar12.md](docs/superpowers/plans/2026-04-13-early-timeout-bar12.md) |  | 2026-05-30 | 37KB | `908866bf` |
| [docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md](docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-05-30 | 20KB | `80750ee6` |
| [docs/superpowers/plans/2026-04-13-label-convention-audit.md](docs/superpowers/plans/2026-04-13-label-convention-audit.md) |  | 2026-05-30 | 31KB | `ea55d54a` |
| [docs/superpowers/plans/2026-04-13-ny-session-filter.md](docs/superpowers/plans/2026-04-13-ny-session-filter.md) |  | 2026-05-30 | 2KB | `325f4e90` |
| [docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md](docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md) |  | 2026-05-30 | 29KB | `74578dba` |
| [docs/superpowers/plans/2026-04-13-pred-adv-cap.md](docs/superpowers/plans/2026-04-13-pred-adv-cap.md) |  | 2026-05-30 | 2KB | `51f3e15c` |
| [docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md](docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md) |  | 2026-05-30 | 15KB | `50a68d1f` |
| [docs/superpowers/plans/2026-04-13-quantile-fav-composition.md](docs/superpowers/plans/2026-04-13-quantile-fav-composition.md) |  | 2026-05-30 | 25KB | `20186b5d` |
| [docs/superpowers/plans/2026-04-13-quantile-forward-validation.md](docs/superpowers/plans/2026-04-13-quantile-forward-validation.md) |  | 2026-05-30 | 13KB | `e4d63c4c` |
| [docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md](docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md) |  | 2026-05-30 | 11KB | `cfa70650` |
| [docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md](docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md) |  | 2026-05-30 | 18KB | `2d48d389` |
| [docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md](docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md) |  | 2026-05-30 | 21KB | `7c99ab9c` |
| [docs/superpowers/plans/2026-04-15-track-a-max-out.md](docs/superpowers/plans/2026-04-15-track-a-max-out.md) |  | 2026-05-30 | 27KB | `4a83f18e` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md) |  | 2026-05-30 | 31KB | `a6f904f0` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md) |  | 2026-05-30 | 21KB | `2085188e` |
| [docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md](docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md) |  | 2026-05-30 | 15KB | `3a35bea9` |
| [docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md](docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md) |  | 2026-05-30 | 32KB | `98abca8c` |
| [docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md](docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-05-30 | 2KB | `0617b8a6` |
| [docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md](docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md) |  | 2026-05-30 | 9KB | `a6b6e6e9` |
| [docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md](docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-05-30 | 2KB | `d3f1a358` |
| [docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md](docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-05-30 | 2KB | `23a84682` |
| [docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md](docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-05-30 | 6KB | `35ba356d` |
| [docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-05-30 | 2KB | `53f8ce75` |
| [docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-05-30 | 2KB | `e0278dfc` |
| [docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md](docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md) |  | 2026-05-30 | 5KB | `c19d12dc` |
| [docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md](docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md) |  | 2026-05-30 | 14KB | `c5fafc2a` |
| [docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md](docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md) |  | 2026-05-30 | 18KB | `773510b6` |
| [docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md](docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md) |  | 2026-05-30 | 12KB | `9dce2437` |
| [docs/superpowers/plans/2026-04-24-system-correlation-and-portfolio-check.md](docs/superpowers/plans/2026-04-24-system-correlation-and-portfolio-check.md) |  | 2026-05-30 | 15KB | `5f85893f` |
| [docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md](docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md) |  | 2026-05-30 | 25KB | `115736bf` |
| [docs/superpowers/plans/2026-05-05-live-safe-ml-audit.md](docs/superpowers/plans/2026-05-05-live-safe-ml-audit.md) |  | 2026-05-30 | 12KB | `b588445d` |
| [docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md](docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md) | План реализации live-safe `signal_candidate` по всей строке фракталов | 2026-05-30 | 38KB | `e504adff` |
| [docs/superpowers/plans/2026-05-15-entry-path-fractal-level-direct-direction.md](docs/superpowers/plans/2026-05-15-entry-path-fractal-level-direct-direction.md) | План реализации direct `SELL/SKIP/BUY` модели по всей строке фракталов | 2026-05-30 | 20KB | `8c855590` |
| [docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md](docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md) |  | 2026-05-30 | 29KB | `fda9e697` |
| [docs/superpowers/plans/2026-05-21-transformer-encoder-direction.md](docs/superpowers/plans/2026-05-21-transformer-encoder-direction.md) |  | 2026-05-30 | 12KB | `82edd7a2` |
| [docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md](docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md) |  | 2026-06-03 | 54KB | `5177783b` |
| [docs/superpowers/plans/2026-05-30-limit-order-hypothesis-testing.md](docs/superpowers/plans/2026-05-30-limit-order-hypothesis-testing.md) |  | 2026-06-03 | 10KB | `0759cd9a` |
| [docs/superpowers/plans/2026-06-01-feature-foundation-rebuild.md](docs/superpowers/plans/2026-06-01-feature-foundation-rebuild.md) |  | 2026-06-03 | 23KB | `182d5eea` |
| [docs/superpowers/plans/ME13_Diagnostics_Plan.md](docs/superpowers/plans/ME13_Diagnostics_Plan.md) |  | 2026-05-30 | 5KB | `10a0c4ea` |
| [docs/superpowers/roadmap.md](docs/superpowers/roadmap.md) |  | 2026-05-30 | 10KB | `b848ff4f` |
| [docs/superpowers/specs/2026-03-22-triple-barrier-design.md](docs/superpowers/specs/2026-03-22-triple-barrier-design.md) |  | 2026-05-30 | 12KB | `82b0860f` |
| [docs/superpowers/specs/2026-03-27-pf-improvement-design.md](docs/superpowers/specs/2026-03-27-pf-improvement-design.md) |  | 2026-05-30 | 18KB | `85d548d9` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md) |  | 2026-05-30 | 13KB | `477a2843` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md) |  | 2026-05-30 | 10KB | `db9fb094` |
| [docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md](docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md) |  | 2026-05-30 | 21KB | `dcb5dcd3` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md) |  | 2026-05-30 | 3KB | `15368fbf` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md) |  | 2026-05-30 | 10KB | `88d9ca83` |
| [docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md](docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md) |  | 2026-05-30 | 10KB | `81b0a31f` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md) |  | 2026-05-30 | 8KB | `60e115b4` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md) |  | 2026-05-30 | 7KB | `119b59e0` |
| [docs/superpowers/specs/2026-04-08-entry-path-v1-design.md](docs/superpowers/specs/2026-04-08-entry-path-v1-design.md) |  | 2026-05-30 | 17KB | `deafd06e` |
| [docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md) |  | 2026-05-30 | 12KB | `e771d628` |
| [docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md) |  | 2026-05-30 | 12KB | `402001b6` |
| [docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md](docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md) |  | 2026-05-30 | 12KB | `1a877fcd` |
| [docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md](docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md) |  | 2026-05-30 | 13KB | `2ef88bef` |
| [docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md](docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md) |  | 2026-05-30 | 8KB | `8272fe58` |
| [docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md](docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md) |  | 2026-05-30 | 7KB | `7fede3fc` |
| [docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md](docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md) |  | 2026-05-30 | 6KB | `f1f6cae8` |
| [docs/superpowers/specs/2026-04-15-quantile-next-research-design.md](docs/superpowers/specs/2026-04-15-quantile-next-research-design.md) |  | 2026-05-30 | 20KB | `8ac77369` |
| [docs/superpowers/specs/2026-04-15-track-a-max-out-design.md](docs/superpowers/specs/2026-04-15-track-a-max-out-design.md) |  | 2026-05-30 | 12KB | `2b4ee2f7` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md) |  | 2026-05-30 | 13KB | `299a938f` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md) |  | 2026-05-30 | 10KB | `48c918e2` |
| [docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md](docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md) |  | 2026-05-30 | 7KB | `0f97c51d` |
| [docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md](docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md) |  | 2026-05-30 | 7KB | `f7f0940d` |
| [docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md](docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md) |  | 2026-05-30 | 17KB | `b852c2fa` |
| [docs/superpowers/specs/2026-04-28-central-inference-service-design.md](docs/superpowers/specs/2026-04-28-central-inference-service-design.md) |  | 2026-05-30 | 7KB | `ecc8e915` |
| [docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md](docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md) |  | 2026-05-30 | 13KB | `b3d2235f` |
| [docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md](docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md) | Спецификация поиска live-safe `signal_candidate` по всей строке фракталов | 2026-06-02 | 43KB | `d9f3365c` |
| [docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md](docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md) | Спецификация direct `SELL/SKIP/BUY` модели по всей строке фракталов | 2026-05-30 | 12KB | `3bba26aa` |
| [docs/superpowers/specs/2026-05-27-limit-order-entry-design.md](docs/superpowers/specs/2026-05-27-limit-order-entry-design.md) |  | 2026-06-03 | 18KB | `1c33e671` |
| [docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md](docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md) | Спецификация Fractal Stop + Fav Target: этап только на пробой уровня и торговый слой | 2026-06-10 | 17KB | `44df96a5` |
| [docs/tests/tests.md](docs/tests/tests.md) |  | 2026-06-05 | 4KB | `6e80560a` |

## Reports

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md) |  | 2026-05-30 | 5KB | `37b9ec88` |
| [docs/reports/2026-04-02-signal-research-variant-3-prep.md](docs/reports/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-05-30 | 12KB | `d26a9270` |
| [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md) |  | 2026-05-30 | 15KB | `98244916` |
| [docs/reports/2026-04-03-signal-path-atlas.md](docs/reports/2026-04-03-signal-path-atlas.md) |  | 2026-05-30 | 8KB | `c68aa3b8` |
| [docs/reports/2026-04-04-archetype-filter-bridge.md](docs/reports/2026-04-04-archetype-filter-bridge.md) |  | 2026-05-30 | 14KB | `28e2bd45` |
| [docs/reports/2026-04-04-signal-path-atlas-readout.md](docs/reports/2026-04-04-signal-path-atlas-readout.md) |  | 2026-05-30 | 25KB | `fbfedb40` |
| [docs/reports/2026-04-04-signal-quality-filter.md](docs/reports/2026-04-04-signal-quality-filter.md) |  | 2026-05-30 | 12KB | `e2e74751` |
| [docs/reports/2026-04-08-entry-path-v1-baseline.md](docs/reports/2026-04-08-entry-path-v1-baseline.md) |  | 2026-05-30 | 10KB | `ff56ac36` |
| [docs/reports/2026-04-08-ml-exit-validation-first.md](docs/reports/2026-04-08-ml-exit-validation-first.md) |  | 2026-05-30 | 8KB | `f61986e3` |
| [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md) |  | 2026-05-30 | 8KB | `1783da26` |
| [docs/reports/2026-04-08-triple-barrier-hardening.md](docs/reports/2026-04-08-triple-barrier-hardening.md) |  | 2026-05-30 | 8KB | `ec8f88b7` |
| [docs/reports/2026-04-08-triple-barrier-runtime-verdict.md](docs/reports/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-05-30 | 9KB | `33e1602a` |
| [docs/reports/2026-04-09-entry-path-trade-filter.md](docs/reports/2026-04-09-entry-path-trade-filter.md) |  | 2026-05-30 | 10KB | `8553f63e` |
| [docs/reports/2026-04-09-entry-path-v1-loss-weighting.md](docs/reports/2026-04-09-entry-path-v1-loss-weighting.md) |  | 2026-05-30 | 7KB | `79f4b733` |
| [docs/reports/2026-04-09-mt4-parity-check-winner.md](docs/reports/2026-04-09-mt4-parity-check-winner.md) |  | 2026-05-30 | 8KB | `a8467fad` |
| [docs/reports/2026-04-10-entry-path-v1-quantile.md](docs/reports/2026-04-10-entry-path-v1-quantile.md) |  | 2026-05-30 | 6KB | `d4fef0e4` |
| [docs/reports/2026-04-12-quantile-status-decision.md](docs/reports/2026-04-12-quantile-status-decision.md) |  | 2026-05-30 | 10KB | `5375913e` |
| [docs/reports/2026-04-12-tb-verdict.md](docs/reports/2026-04-12-tb-verdict.md) |  | 2026-05-30 | 7KB | `089642df` |
| [docs/reports/2026-04-13-fav-3-vs-12-standalone.md](docs/reports/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-05-30 | 5KB | `8a929a77` |
| [docs/reports/2026-04-13-label-convention-audit.md](docs/reports/2026-04-13-label-convention-audit.md) |  | 2026-05-30 | 6KB | `3ddc2a23` |
| [docs/reports/2026-04-13-pf-uplift-discovery.md](docs/reports/2026-04-13-pf-uplift-discovery.md) |  | 2026-05-30 | 14KB | `f93b85c0` |
| [docs/reports/2026-04-13-quantile-fav-composition.md](docs/reports/2026-04-13-quantile-fav-composition.md) |  | 2026-05-30 | 8KB | `8dd53bda` |
| [docs/reports/2026-04-13-quantile-forward-validation.md](docs/reports/2026-04-13-quantile-forward-validation.md) |  | 2026-05-30 | 4KB | `1364686a` |
| [docs/reports/2026-04-15-entry-path-v1-frequency.md](docs/reports/2026-04-15-entry-path-v1-frequency.md) |  | 2026-05-30 | 6KB | `9f5043d0` |
| [docs/reports/2026-04-15-track-a-max-out.md](docs/reports/2026-04-15-track-a-max-out.md) |  | 2026-05-30 | 9KB | `ca11c38f` |
| [docs/reports/2026-04-16-trailing-stop-target-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-first-wave.md) |  | 2026-05-30 | 6KB | `5b0b7b8b` |
| [docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md) |  | 2026-05-30 | 6KB | `e812d460` |
| [docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md](docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md) |  | 2026-05-30 | 8KB | `6e26a3c3` |
| [docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md](docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md) |  | 2026-05-30 | 8KB | `c2ca8b3f` |
| [docs/reports/2026-04-18-mt4-trailing-stop-execution.md](docs/reports/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-05-30 | 5KB | `db5e5c66` |
| [docs/reports/2026-04-18-take-skip-frequency-followup.md](docs/reports/2026-04-18-take-skip-frequency-followup.md) |  | 2026-05-30 | 9KB | `edb6385b` |
| [docs/reports/2026-04-18-take-skip-rule-consumer.md](docs/reports/2026-04-18-take-skip-rule-consumer.md) |  | 2026-05-30 | 5KB | `bf29f837` |
| [docs/reports/2026-04-19-current-feature-importance-diagnostics.md](docs/reports/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-05-30 | 4KB | `e9beb824` |
| [docs/reports/2026-04-19-execution-policy-v2.md](docs/reports/2026-04-19-execution-policy-v2.md) |  | 2026-05-30 | 8KB | `f124b341` |
| [docs/reports/2026-04-19-feature-bank-clean-comparison.md](docs/reports/2026-04-19-feature-bank-clean-comparison.md) |  | 2026-05-30 | 3KB | `6c105216` |
| [docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md](docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-05-30 | 3KB | `8505936d` |
| [docs/reports/2026-04-19-lib-pic-feature-source-audit.md](docs/reports/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-05-30 | 8KB | `0b903977` |
| [docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md](docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-05-30 | 4KB | `c80ac4eb` |
| [docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-05-30 | 2KB | `64b8dea4` |
| [docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md](docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md) |  | 2026-05-30 | 9KB | `ac47d800` |
| [docs/reports/2026-04-20-take-skip-lib-pic-selection.md](docs/reports/2026-04-20-take-skip-lib-pic-selection.md) |  | 2026-05-30 | 4KB | `51a438b8` |
| [docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md](docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md) |  | 2026-05-30 | 13KB | `3e9f8318` |
| [docs/reports/2026-04-22-signal-export-parity.md](docs/reports/2026-04-22-signal-export-parity.md) |  | 2026-05-30 | 5KB | `64f8d26c` |
| [docs/reports/2026-04-24-cross-instrument-robustness-check.md](docs/reports/2026-04-24-cross-instrument-robustness-check.md) |  | 2026-05-30 | 8KB | `374bd822` |
| [docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md) |  | 2026-05-30 | 10KB | `29106e47` |
| [docs/reports/2026-04-24-system-correlation-and-portfolio-check.md](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md) |  | 2026-05-30 | 10KB | `77d28ff4` |
| [docs/reports/2026-04-27-telemetry-frequency-demo-launch.md](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) |  | 2026-05-30 | 10KB | `7c587ed0` |
| [docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md) |  | 2026-05-30 | 11KB | `e1210726` |
| [docs/reports/2026-04-29-online-inference-contract-hardening.md](docs/reports/2026-04-29-online-inference-contract-hardening.md) |  | 2026-05-30 | 6KB | `26968f89` |
| [docs/reports/2026-05-05-live-safe-ml-audit.md](docs/reports/2026-05-05-live-safe-ml-audit.md) |  | 2026-05-30 | 23KB | `91e0e4f8` |
| [docs/reports/2026-05-07-cpu-gpu-reproducibility.md](docs/reports/2026-05-07-cpu-gpu-reproducibility.md) |  | 2026-05-30 | 8KB | `589d954f` |
| [docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md](docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md) |  | 2026-05-30 | 6KB | `07ff396c` |
| [docs/reports/2026-05-07-entry-path-mt4-parity.md](docs/reports/2026-05-07-entry-path-mt4-parity.md) |  | 2026-05-30 | 4KB | `b8c63e3c` |
| [docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md](docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md) |  | 2026-05-30 | 3KB | `10ba83c4` |
| [docs/reports/2026-05-12-online-tester-execution-reconciliation.md](docs/reports/2026-05-12-online-tester-execution-reconciliation.md) |  | 2026-05-30 | 21KB | `cca94a62` |
| [docs/reports/2026-05-14-entry-path-all-rows-ranking.md](docs/reports/2026-05-14-entry-path-all-rows-ranking.md) |  | 2026-05-30 | 5KB | `3501a0c7` |
| [docs/reports/2026-05-14-entry-path-causal-surrogate.md](docs/reports/2026-05-14-entry-path-causal-surrogate.md) |  | 2026-05-30 | 3KB | `13aef3da` |
| [docs/reports/2026-05-14-entry-path-direct-bar-model.md](docs/reports/2026-05-14-entry-path-direct-bar-model.md) |  | 2026-05-30 | 4KB | `2038211f` |
| [docs/reports/2026-05-15-direct-direction-improvement.md](docs/reports/2026-05-15-direct-direction-improvement.md) |  | 2026-05-30 | 12KB | `edc04acb` |
| [docs/reports/2026-05-18-direct-direction-rebuild.md](docs/reports/2026-05-18-direct-direction-rebuild.md) |  | 2026-05-30 | 14KB | `c12d5722` |
| [docs/reports/2026-05-21-transformer-direction.md](docs/reports/2026-05-21-transformer-direction.md) |  | 2026-05-30 | 6KB | `510eda23` |
| [docs/reports/2026-05-25-methodology-cycle-stages-00-04.md](docs/reports/2026-05-25-methodology-cycle-stages-00-04.md) |  | 2026-06-03 | 19KB | `1c004781` |
| [docs/reports/2026-05-29-limit-order-entry.md](docs/reports/2026-05-29-limit-order-entry.md) |  | 2026-06-03 | 6KB | `1ce2dda6` |
| [docs/reports/2026-06-01-feature-ablation.md](docs/reports/2026-06-01-feature-ablation.md) |  | 2026-06-06 | 7KB | `8c0b1bd9` |
| [docs/reports/2026-06-03-direction-only-signal.md](docs/reports/2026-06-03-direction-only-signal.md) |  | 2026-06-05 | 10KB | `b8c975d2` |
| [docs/reports/2026-06-04-fractal-ablation.md](docs/reports/2026-06-04-fractal-ablation.md) |  | 2026-06-05 | 10KB | `f3481558` |
| [docs/reports/2026-06-05-rf-gridsearch.md](docs/reports/2026-06-05-rf-gridsearch.md) |  | 2026-06-06 | 5KB | `46b326bb` |
| [docs/reports/README.md](docs/reports/README.md) |  | 2026-05-30 | 2KB | `e07ce60f` |

## ML

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [ML/README.md](ML/README.md) |  |  | 2026-06-05 | 17KB | `8e6c2c98` |
| [ML/ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | 🏁 | 2026-06-05 | 4KB | `dd55ee84` |
| [ML/baseline/baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | 🏁 | 2026-06-05 | 40KB | `e1216862` |
| [ML/baseline/benchmark_limit_order_entry.py](ML/baseline/benchmark_limit_order_entry.py) |  |  | 2026-06-05 | 9KB | `32700fef` |
| [ML/baseline/direction_only_signal.py](ML/baseline/direction_only_signal.py) |  |  | 2026-06-05 | 6KB | `8d683a5b` |
| [ML/baseline/direction_updn_signal.py](ML/baseline/direction_updn_signal.py) |  |  | 2026-06-05 | 3KB | `70523b5b` |
| [ML/baseline/feature_ablation.py](ML/baseline/feature_ablation.py) |  |  | 2026-06-05 | 16KB | `704db67c` |
| [ML/baseline/fractal_ablation.py](ML/baseline/fractal_ablation.py) |  |  | 2026-06-05 | 9KB | `1e6b236f` |
| [ML/baseline/reports/baseline_report.md](ML/baseline/reports/baseline_report.md) |  |  | 2026-05-30 | 4KB | `66cbf52f` |
| [ML/baseline/reports/limit_order_spread_grid.md](ML/baseline/reports/limit_order_spread_grid.md) |  |  | 2026-06-03 | 3KB | `f8f3c27b` |
| [ML/baseline/rf_gridsearch.py](ML/baseline/rf_gridsearch.py) |  |  | 2026-06-05 | 6KB | `31bd8826` |
| [ML/baseline/tb_direction_signal.py](ML/baseline/tb_direction_signal.py) |  |  | 2026-06-05 | 8KB | `d211235a` |
| [ML/baseline_candidate_source.py](ML/baseline_candidate_source.py) | Stage 07 baseline-first runner для candidate-source v2 | ✅ | 2026-06-05 | 10KB | `d2608702` |
| [ML/benchmark_buy_only_direction.py](ML/benchmark_buy_only_direction.py) | BUY-only RF с исправленными признаками (Phase A/B/D rebuild) | ✅ | 2026-06-05 | 37KB | `59b3a74c` |
| [ML/benchmark_cross_instrument_robustness.py](ML/benchmark_cross_instrument_robustness.py) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты | ✅ | 2026-06-05 | 13KB | `d59921e5` |
| [ML/benchmark_entry_path_all_rows_ranking.py](ML/benchmark_entry_path_all_rows_ranking.py) | All-rows ranking benchmark без offline `signal != 0` gate | ✅ | 2026-06-05 | 16KB | `56cff1e7` |
| [ML/benchmark_entry_path_binary_direction.py](ML/benchmark_entry_path_binary_direction.py) |  |  | 2026-06-05 | 26KB | `03739d36` |
| [ML/benchmark_entry_path_causal_surrogate.py](ML/benchmark_entry_path_causal_surrogate.py) | Causal surrogate benchmark для offline `label_all().signal` | ✅ | 2026-06-05 | 19KB | `304f831a` |
| [ML/benchmark_entry_path_direct_bar_model.py](ML/benchmark_entry_path_direct_bar_model.py) | Direct BUY/SELL/SKIP benchmark для каждого бара без offline signal gate | ✅ | 2026-06-05 | 18KB | `ab227ac4` |
| [ML/benchmark_entry_path_fractal_level_direct_direction.py](ML/benchmark_entry_path_fractal_level_direct_direction.py) |  |  | 2026-06-05 | 29KB | `2194abb9` |
| [ML/benchmark_entry_path_fractal_level_signal.py](ML/benchmark_entry_path_fractal_level_signal.py) |  |  | 2026-06-05 | 7KB | `d2b2f04b` |
| [ML/benchmark_entry_path_score_direction.py](ML/benchmark_entry_path_score_direction.py) |  |  | 2026-06-05 | 14KB | `8abb3d20` |
| [ML/benchmark_entry_path_signal_only_ablation.py](ML/benchmark_entry_path_signal_only_ablation.py) | Ablation benchmark вклада offline `signal != 0` без ML score-фильтра | ✅ | 2026-06-05 | 11KB | `52aa4508` |
| [ML/benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | 🏁 | 2026-06-05 | 6KB | `1bc86818` |
| [ML/benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | 🏁 | 2026-06-05 | 7KB | `e469b58a` |
| [ML/benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | ✅ | 2026-06-05 | 13KB | `40bbefc1` |
| [ML/benchmark_entry_path_v1_quantile_n_boost.py](ML/benchmark_entry_path_v1_quantile_n_boost.py) |  |  | 2026-06-05 | 13KB | `6538fa97` |
| [ML/benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | ✅ | 2026-06-05 | 12KB | `34916e02` |
| [ML/benchmark_execution_policy_v2.py](ML/benchmark_execution_policy_v2.py) | Сравнение вариантов выхода для готовых ML-сигналов | ✅ | 2026-06-05 | 16KB | `514040ec` |
| [ML/benchmark_fav_3_vs_12_standalone.py](ML/benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-06-05 | 16KB | `8e4214fd` |
| [ML/benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | 🏁 | 2026-06-05 | 14KB | `b821a51b` |
| [ML/benchmark_quantile_early_timeout.py](ML/benchmark_quantile_early_timeout.py) |  |  | 2026-06-05 | 5KB | `dca2ba4f` |
| [ML/benchmark_quantile_fav_composition.py](ML/benchmark_quantile_fav_composition.py) |  |  | 2026-06-05 | 15KB | `97a02b70` |
| [ML/benchmark_quantile_forward_validation.py](ML/benchmark_quantile_forward_validation.py) |  |  | 2026-06-05 | 5KB | `a3386bcc` |
| [ML/benchmark_quantile_relaxed_composition.py](ML/benchmark_quantile_relaxed_composition.py) |  |  | 2026-06-05 | 8KB | `67b8d711` |
| [ML/benchmark_signal_export_parity.py](ML/benchmark_signal_export_parity.py) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log | ✅ | 2026-06-05 | 10KB | `a5ab05fc` |
| [ML/benchmark_system_correlation.py](ML/benchmark_system_correlation.py) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам | ✅ | 2026-06-05 | 24KB | `c2a02130` |
| [ML/benchmark_take_skip_lib_pic_selection.py](ML/benchmark_take_skip_lib_pic_selection.py) | Внешний слой отбора `take_skip_v2` по признакам `lib_PIC` без нового обучения | ✅ | 2026-06-05 | 18KB | `103dc4a1` |
| [ML/benchmark_take_skip_mt4_trailing_sequential.py](ML/benchmark_take_skip_mt4_trailing_sequential.py) | Read-only comparison of independent vs single-position trailing-stop execution for take/skip signals | ✅ | 2026-06-05 | 7KB | `1debf0f4` |
| [ML/benchmark_take_skip_trailing_stop.py](ML/benchmark_take_skip_trailing_stop.py) |  |  | 2026-06-05 | 8KB | `b1f8f35d` |
| [ML/benchmark_take_skip_trailing_stop_v2.py](ML/benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-06-05 | 5KB | `f1ef638b` |
| [ML/benchmark_take_skip_trailing_stop_v2_followup.py](ML/benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-06-05 | 10KB | `106613ee` |
| [ML/benchmark_telemetry_frequency_calibration.py](ML/benchmark_telemetry_frequency_calibration.py) | Калибровка частого diagnostic telemetry режима поверх take/skip score | ✅ | 2026-06-05 | 11KB | `51c02ce4` |
| [ML/benchmark_trailing_stop_target.py](ML/benchmark_trailing_stop_target.py) | Validation-first benchmark для trailing-stop target exports | ✅ | 2026-06-05 | 1KB | `7c96419a` |
| [ML/benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | ✅ | 2026-06-05 | 8KB | `d8cf04ba` |
| [ML/benchmark_triple_barrier_mt4_execution.py](ML/benchmark_triple_barrier_mt4_execution.py) |  |  | 2026-06-05 | 4KB | `3ef3e057` |
| [ML/compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | 🏁 | 2026-06-05 | 13KB | `adc3937c` |
| [ML/conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | 🏁 | 2026-06-05 | 14KB | `d316ff0e` |
| [ML/conformal/conformal_quantiles.json](ML/conformal/conformal_quantiles.json) |  |  | 2026-05-30 | 399B | `6d9e2e03` |
| [ML/data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ | 2026-06-05 | 73KB | `99819f65` |
| [ML/entry_path_direct_direction_targets.py](ML/entry_path_direct_direction_targets.py) |  |  | 2026-06-05 | 11KB | `4d77c81d` |
| [ML/entry_path_feature_bank.py](ML/entry_path_feature_bank.py) | Entry path feature bank: оконные сводки строки и row-wise context features | ✅ | 2026-06-05 | 3KB | `1445c400` |
| [ML/entry_path_level_targets.py](ML/entry_path_level_targets.py) |  |  | 2026-06-05 | 7KB | `0e33bad7` |
| [ML/entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | ✅ | 2026-06-05 | 17KB | `f60dbc66` |
| [ML/entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | ✅ | 2026-06-05 | 14KB | `54d61050` |
| [ML/entry_path_v1_quantile_ensemble.py](ML/entry_path_v1_quantile_ensemble.py) | Агрегация quantile-прогнозов по нескольким seed для n-boost проверки | ✅ | 2026-06-05 | 965B | `1f32dd16` |
| [ML/entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | ✅ | 2026-06-05 | 8KB | `6e03b05a` |
| [ML/evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | ✅ | 2026-06-05 | 40KB | `b22a681f` |
| [ML/experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | 🏁 | 2026-06-05 | 20KB | `ac98edd8` |
| [ML/export_entry_path_predictions.py](ML/export_entry_path_predictions.py) | Inference `entry_path_v1` / `entry_path_v1_quantile` на arbitrary labeled CSV без переобучения | ✅ | 2026-06-05 | 8KB | `367f4065` |
| [ML/export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export train/validation/test predictions for entry_path_v1_quantile | ✅ | 2026-06-05 | 6KB | `38bc75e8` |
| [ML/export_entry_path_v1_quantile_rule.py](ML/export_entry_path_v1_quantile_rule.py) |  |  | 2026-06-05 | 7KB | `aa96afd9` |
| [ML/export_take_skip_v2_predictions.py](ML/export_take_skip_v2_predictions.py) |  |  | 2026-06-05 | 10KB | `a904d007` |
| [ML/export_updn_active_predictions.py](ML/export_updn_active_predictions.py) |  |  | 2026-06-05 | 4KB | `515bde2e` |
| [ML/feature_bank_comparison_diagnostics.py](ML/feature_bank_comparison_diagnostics.py) | Сравнение baseline/geometry/path feature-bank вариантов | ✅ | 2026-06-05 | 9KB | `3599f7fa` |
| [ML/feature_importance_diagnostics.py](ML/feature_importance_diagnostics.py) | Диагностика важности групп текущих fractal-признаков | ✅ | 2026-06-05 | 16KB | `82e28b86` |
| [ML/feature_screen_entry_path.py](ML/feature_screen_entry_path.py) | Диагностический feature screening для entry_path_v1 | ✅ | 2026-06-05 | 782B | `473127c5` |
| [ML/fractal_level_feature_builder.py](ML/fractal_level_feature_builder.py) |  |  | 2026-06-05 | 22KB | `0e9565c0` |
| [ML/lib_pic_feature_profiles.py](ML/lib_pic_feature_profiles.py) | Единая сборка профилей признаков `lib_PIC` для диагностики и `entry_path_v1` | ✅ | 2026-06-05 | 4KB | `6da69e68` |
| [ML/lib_pic_geometry_feature_bank.py](ML/lib_pic_geometry_feature_bank.py) | Производные признаки геометрии уровней `lib_PIC` | ✅ | 2026-06-05 | 7KB | `24dd7aaa` |
| [ML/lib_pic_path_reaction_feature_bank.py](ML/lib_pic_path_reaction_feature_bank.py) | Производные признаки исторической реакции цены `Up/Dn` после уровней | ✅ | 2026-06-05 | 8KB | `a47b0ff1` |
| [ML/limit_order_train.py](ML/limit_order_train.py) |  |  | 2026-06-05 | 11KB | `5f2829eb` |
| [ML/live_safe_audit.py](ML/live_safe_audit.py) | Core-типы live-safe audit и свод feature verdict → system verdict | ✅ | 2026-06-05 | 5KB | `8aeb6ecd` |
| [ML/live_safe_audit_registry.py](ML/live_safe_audit_registry.py) | Реестр прибыльных ML-систем для повторного live-safe audit | ✅ | 2026-06-05 | 3KB | `20c94868` |
| [ML/losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ | 2026-06-05 | 9KB | `b66ced3d` |
| [ML/model_sweep_candidate_source.py](ML/model_sweep_candidate_source.py) | Stage 08 exploratory model sweep для candidate-source v2 | ✅ | 2026-06-05 | 19KB | `aa317cfd` |
| [ML/models/__init__.py](ML/models/__init__.py) |  |  | 2026-06-05 | 1KB | `15669a9b` |
| [ML/models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | 🏁 | 2026-06-05 | 4KB | `4aa2023e` |
| [ML/models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | 🏁 | 2026-06-05 | 4KB | `bd1fab57` |
| [ML/models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | ✅ | 2026-06-05 | 4KB | `597779ed` |
| [ML/models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | ✅ | 2026-06-05 | 4KB | `41ffb003` |
| [ML/models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | ✅ | 2026-06-05 | 4KB | `68bafa95` |
| [ML/models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 | 2026-06-05 | 5KB | `06ff47b8` |
| [ML/models/take_skip_dual_stream_transformer.py](ML/models/take_skip_dual_stream_transformer.py) | Dual-stream Transformer для `take_skip_v2`: sequence branch + `lib_PIC` feature branch | ✅ | 2026-06-05 | 3KB | `d645930f` |
| [ML/models/trailing_stop_target_quantile_transformer.py](ML/models/trailing_stop_target_quantile_transformer.py) | TrailingStopTargetQuantileTransformer — q10/q50/q90 heads для `trail_48_pnl_atr_x3` | ✅ | 2026-06-05 | 2KB | `61f57808` |
| [ML/models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | ✅ | 2026-06-05 | 7KB | `e1b62b6e` |
| [ML/multi_scale_fractal_features.py](ML/multi_scale_fractal_features.py) |  |  | 2026-06-05 | 1KB | `c73c28c3` |
| [ML/online_tester_reconciliation.py](ML/online_tester_reconciliation.py) | Сверка online/tester `ml_trade_events.csv` по `signal_time + direction` | ✅ | 2026-06-05 | 21KB | `24040876` |
| [ML/optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | 🏁 | 2026-06-05 | 19KB | `80f179e6` |
| [ML/pll_normalizer.py](ML/pll_normalizer.py) |  |  | 2026-06-05 | 8KB | `3ac39fd4` |
| [ML/prepare_entry_path_mt4_parity.py](ML/prepare_entry_path_mt4_parity.py) | Подготовка frozen `entry_path_v1_live_safe + A @ 7.5%` export для MT4 parity | ✅ | 2026-06-05 | 7KB | `0227d595` |
| [ML/prepare_raw_features.py](ML/prepare_raw_features.py) | Извлечение сырых признаков из OHLC для direct-direction (Phase 0) | ✅ | 2026-06-05 | 19KB | `e2098ef4` |
| [ML/reports/architecture_comparison_classification.md](ML/reports/architecture_comparison_classification.md) |  |  | 2026-05-30 | 3KB | `c0fe9f2d` |
| [ML/reports/architecture_comparison_regression.md](ML/reports/architecture_comparison_regression.md) |  |  | 2026-05-30 | 1KB | `3fe65254` |
| [ML/reports/architecture_comparison_regression_updn.md](ML/reports/architecture_comparison_regression_updn.md) |  |  | 2026-05-30 | 1KB | `bc5e1dc4` |
| [ML/reports/buy_only_direction_rebuild/frozen_test.json](ML/reports/buy_only_direction_rebuild/frozen_test.json) |  |  | 2026-05-30 | 1KB | `a326384f` |
| [ML/reports/buy_only_direction_rebuild/phase_a_summary.json](ML/reports/buy_only_direction_rebuild/phase_a_summary.json) |  |  | 2026-05-30 | 21KB | `fe504c56` |
| [ML/reports/buy_only_direction_rebuild/phase_b_summary.json](ML/reports/buy_only_direction_rebuild/phase_b_summary.json) |  |  | 2026-05-30 | 2KB | `7f10fe5d` |
| [ML/reports/buy_only_direction_rebuild/summary.json](ML/reports/buy_only_direction_rebuild/summary.json) |  |  | 2026-05-30 | 21KB | `fe504c56` |
| [ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-05-30 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/summary.json) |  |  | 2026-05-30 | 15KB | `d8c4143b` |
| [ML/reports/cross_instrument_robustness/finalize_labeled_temp.py](ML/reports/cross_instrument_robustness/finalize_labeled_temp.py) |  |  | 2026-06-05 | 2KB | `e8aae810` |
| [ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-05-30 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/summary.json) |  |  | 2026-05-30 | 15KB | `d7897cc3` |
| [ML/reports/cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json) |  |  | 2026-05-30 | 987B | `5134c6b8` |
| [ML/reports/cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json) |  |  | 2026-05-30 | 987B | `67ce56ee` |
| [ML/reports/cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json) |  |  | 2026-05-30 | 912B | `b7cef6eb` |
| [ML/reports/cross_instrument_robustness/manifest_cross_instrument_transfer.json](ML/reports/cross_instrument_robustness/manifest_cross_instrument_transfer.json) |  |  | 2026-05-30 | 3KB | `1e7814b0` |
| [ML/reports/cross_instrument_robustness/manifest_metaquotes_baseline.json](ML/reports/cross_instrument_robustness/manifest_metaquotes_baseline.json) |  |  | 2026-05-30 | 824B | `61aa0027` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer.json) |  |  | 2026-05-30 | 885B | `6f8aaed0` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_qf.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_qf.json) |  |  | 2026-05-30 | 667B | `236d2bff` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_test_labeled.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_test_labeled.json) |  |  | 2026-05-30 | 913B | `974ca96f` |
| [ML/reports/cross_instrument_robustness/manifest_xauusd_provider_drift.json](ML/reports/cross_instrument_robustness/manifest_xauusd_provider_drift.json) |  |  | 2026-05-30 | 825B | `3d686bf2` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline/run_metadata.json](ML/reports/cross_instrument_robustness/metaquotes_baseline/run_metadata.json) |  |  | 2026-05-30 | 95B | `543171a5` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline/summary.json](ML/reports/cross_instrument_robustness/metaquotes_baseline/summary.json) |  |  | 2026-05-30 | 30KB | `a8a1e20d` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json](ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json) |  |  | 2026-05-30 | 512B | `033d5470` |
| [ML/reports/cross_instrument_robustness/run_single_instrument_transfer.py](ML/reports/cross_instrument_robustness/run_single_instrument_transfer.py) |  |  | 2026-06-05 | 5KB | `7d257dff` |
| [ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/run_metadata.json) |  |  | 2026-05-30 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/summary.json) |  |  | 2026-05-30 | 14KB | `233fd4ed` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_qf/run_metadata.json](ML/reports/cross_instrument_robustness/xagusd_transfer_qf/run_metadata.json) |  |  | 2026-05-30 | 95B | `5cc06b98` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_qf/summary.json](ML/reports/cross_instrument_robustness/xagusd_transfer_qf/summary.json) |  |  | 2026-05-30 | 8KB | `9432f622` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-05-30 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/summary.json) |  |  | 2026-05-30 | 14KB | `e79a0708` |
| [ML/reports/cross_instrument_robustness/xauusd_provider_drift/run_metadata.json](ML/reports/cross_instrument_robustness/xauusd_provider_drift/run_metadata.json) |  |  | 2026-05-30 | 95B | `543171a5` |
| [ML/reports/cross_instrument_robustness/xauusd_provider_drift/summary.json](ML/reports/cross_instrument_robustness/xauusd_provider_drift/summary.json) |  |  | 2026-05-30 | 31KB | `6f9ff316` |
| [ML/reports/current_feature_importance/report.md](ML/reports/current_feature_importance/report.md) |  |  | 2026-05-30 | 2KB | `c58147a6` |
| [ML/reports/current_feature_importance/summary.json](ML/reports/current_feature_importance/summary.json) |  |  | 2026-05-30 | 498B | `a286b27a` |
| [ML/reports/direct_direction_chain_audit/minimal_repro_checks.json](ML/reports/direct_direction_chain_audit/minimal_repro_checks.json) |  |  | 2026-05-30 | 3KB | `221806f9` |
| [ML/reports/direction_only_signal.json](ML/reports/direction_only_signal.json) |  |  | 2026-06-05 | 2KB | `e760a7ba` |
| [ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/run_metadata.json) |  |  | 2026-05-30 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/summary.json) |  |  | 2026-05-30 | 10KB | `f4c3f606` |
| [ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/run_metadata.json) |  |  | 2026-05-30 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/summary.json) |  |  | 2026-05-30 | 9KB | `9456a70e` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json) |  |  | 2026-05-30 | 807B | `80a032aa` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json) |  |  | 2026-05-30 | 807B | `a49a431f` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json) |  |  | 2026-05-30 | 807B | `691efe84` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/XAGUSD/xagusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/XAGUSD/xagusd_transfer_manifest.json) |  |  | 2026-05-30 | 807B | `e298a870` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/xauusd_provider_drift_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/xauusd_provider_drift_manifest.json) |  |  | 2026-05-30 | 842B | `fdd42363` |
| [ML/reports/entry_path_cross_instrument_robustness/manifest_metaquotes_baseline.json](ML/reports/entry_path_cross_instrument_robustness/manifest_metaquotes_baseline.json) |  |  | 2026-05-30 | 775B | `6542c434` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/run_metadata.json) |  |  | 2026-05-30 | 95B | `77c70099` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json) |  |  | 2026-05-30 | 9KB | `ed311b43` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json) |  |  | 2026-05-30 | 353B | `388b418f` |
| [ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/run_metadata.json) |  |  | 2026-05-30 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/summary.json) |  |  | 2026-05-30 | 10KB | `cf25db3c` |
| [ML/reports/entry_path_cross_instrument_robustness/verdict_overview.json](ML/reports/entry_path_cross_instrument_robustness/verdict_overview.json) |  |  | 2026-05-30 | 3KB | `eebe1587` |
| [ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/run_metadata.json) |  |  | 2026-05-30 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/summary.json) |  |  | 2026-05-30 | 9KB | `83551bb6` |
| [ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/run_metadata.json) |  |  | 2026-05-30 | 95B | `77c70099` |
| [ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/summary.json](ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/summary.json) |  |  | 2026-05-30 | 9KB | `690af70a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 536B | `2dbd3e0a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `2f9e801c` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 536B | `7b9539cf` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 2KB | `062a50ec` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 544B | `7d0c8863` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `756079bf` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 541B | `201a0e3e` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `a077c548` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 528B | `a9a86071` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `ece7ee12` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 521B | `d4d1887c` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `e186a9fd` |
| [ML/reports/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 495B | `e8a9e03d` |
| [ML/reports/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `ead9e11c` |
| [ML/reports/entry_path_v1_all_rows_ranking/summary.json](ML/reports/entry_path_v1_all_rows_ranking/summary.json) |  |  | 2026-05-30 | 9KB | `c68a7074` |
| [ML/reports/entry_path_v1_all_rows_ranking/summary.md](ML/reports/entry_path_v1_all_rows_ranking/summary.md) |  |  | 2026-05-30 | 1KB | `975255a2` |
| [ML/reports/entry_path_v1_binary_direction/frozen_test.json](ML/reports/entry_path_v1_binary_direction/frozen_test.json) |  |  | 2026-05-30 | 1KB | `1dfea12b` |
| [ML/reports/entry_path_v1_binary_direction/summary.json](ML/reports/entry_path_v1_binary_direction/summary.json) |  |  | 2026-05-30 | 1KB | `8b9fe83c` |
| [ML/reports/entry_path_v1_causal_surrogate/summary.json](ML/reports/entry_path_v1_causal_surrogate/summary.json) |  |  | 2026-05-30 | 3KB | `30d10ab7` |
| [ML/reports/entry_path_v1_causal_surrogate/summary.md](ML/reports/entry_path_v1_causal_surrogate/summary.md) |  |  | 2026-05-30 | 542B | `0e0a1c3b` |
| [ML/reports/entry_path_v1_direct_bar_model/summary.json](ML/reports/entry_path_v1_direct_bar_model/summary.json) |  |  | 2026-05-30 | 6KB | `13bc1992` |
| [ML/reports/entry_path_v1_direct_bar_model/summary.md](ML/reports/entry_path_v1_direct_bar_model/summary.md) |  |  | 2026-05-30 | 694B | `902cd983` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E0_ablation_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E0_ablation_results.md) |  |  | 2026-05-30 | 2KB | `18906d28` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E1_binary_direction_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E1_binary_direction_results.md) |  |  | 2026-05-30 | 2KB | `a4ef3f83` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E2_hgb_lr_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E2_hgb_lr_results.md) |  |  | 2026-05-30 | 1KB | `96e420c3` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E3_zone_features_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E3_zone_features_results.md) |  |  | 2026-05-30 | 1KB | `205b1514` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E5_score_direction_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E5_score_direction_results.md) |  |  | 2026-05-30 | 2KB | `5117d4e1` |
| [ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md](ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md) |  |  | 2026-05-30 | 5KB | `58faba29` |
| [ML/reports/entry_path_v1_fractal_level_direct_direction/feature_audit.json](ML/reports/entry_path_v1_fractal_level_direct_direction/feature_audit.json) |  |  | 2026-05-30 | 3KB | `23085403` |
| [ML/reports/entry_path_v1_fractal_level_direct_direction/summary.json](ML/reports/entry_path_v1_fractal_level_direct_direction/summary.json) |  |  | 2026-05-30 | 10KB | `1c312dd6` |
| [ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json](ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json) |  |  | 2026-05-30 | 2KB | `d5b17f2a` |
| [ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json](ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json) |  |  | 2026-05-30 | 3KB | `70511070` |
| [ML/reports/entry_path_v1_frequency/final_verdict.json](ML/reports/entry_path_v1_frequency/final_verdict.json) |  |  | 2026-05-30 | 637B | `c96361ff` |
| [ML/reports/entry_path_v1_frequency/run_metadata.json](ML/reports/entry_path_v1_frequency/run_metadata.json) |  |  | 2026-05-30 | 218B | `4c8fa299` |
| [ML/reports/entry_path_v1_frequency/selected_candidate.json](ML/reports/entry_path_v1_frequency/selected_candidate.json) |  |  | 2026-05-30 | 251B | `f2b86a6f` |
| [ML/reports/entry_path_v1_frequency_v2/final_verdict.json](ML/reports/entry_path_v1_frequency_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `3fa39482` |
| [ML/reports/entry_path_v1_frequency_v2/run_metadata.json](ML/reports/entry_path_v1_frequency_v2/run_metadata.json) |  |  | 2026-05-30 | 243B | `6316d165` |
| [ML/reports/entry_path_v1_frequency_v2/selected_candidate.json](ML/reports/entry_path_v1_frequency_v2/selected_candidate.json) |  |  | 2026-05-30 | 513B | `b69272ad` |
| [ML/reports/entry_path_v1_live_safe/audit_a/a_family_seed_threshold_audit_summary.json](ML/reports/entry_path_v1_live_safe/audit_a/a_family_seed_threshold_audit_summary.json) |  |  | 2026-05-30 | 1KB | `d554a410` |
| [ML/reports/entry_path_v1_live_safe/audit_a/frozen_a_audit_summary.json](ML/reports/entry_path_v1_live_safe/audit_a/frozen_a_audit_summary.json) |  |  | 2026-05-30 | 1KB | `f031ea71` |
| [ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 519B | `db1d2a0f` |
| [ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `29edc3c4` |
| [ML/reports/entry_path_v1_live_safe/multi_seed_summary.json](ML/reports/entry_path_v1_live_safe/multi_seed_summary.json) |  |  | 2026-05-30 | 2KB | `aa15eb51` |
| [ML/reports/entry_path_v1_live_safe/runtime/runtime_export_metadata.json](ML/reports/entry_path_v1_live_safe/runtime/runtime_export_metadata.json) |  |  | 2026-05-22 | 1KB | `fd8c9377` |
| [ML/reports/entry_path_v1_live_safe/runtime/runtime_state.json](ML/reports/entry_path_v1_live_safe/runtime/runtime_state.json) |  |  | 2026-05-22 | 147B | `6319b661` |
| [ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 557B | `09c8c388` |
| [ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `1b9cf711` |
| [ML/reports/entry_path_v1_live_safe/seed_007/result.json](ML/reports/entry_path_v1_live_safe/seed_007/result.json) |  |  | 2026-05-30 | 2KB | `21ed6ab7` |
| [ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 528B | `4b967a95` |
| [ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `a5bedf83` |
| [ML/reports/entry_path_v1_live_safe/seed_017/result.json](ML/reports/entry_path_v1_live_safe/seed_017/result.json) |  |  | 2026-05-30 | 2KB | `3729f8b9` |
| [ML/reports/entry_path_v1_live_safe/seed_042/result.json](ML/reports/entry_path_v1_live_safe/seed_042/result.json) |  |  | 2026-05-30 | 2KB | `f8445a1d` |
| [ML/reports/entry_path_v1_live_safe/seed_042/selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_042/selected_rule.json) |  |  | 2026-05-30 | 1KB | `29edc3c4` |
| [ML/reports/entry_path_v1_live_safe/seed_042/trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_042/trade_filter_report.md) |  |  | 2026-05-30 | 519B | `db1d2a0f` |
| [ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 529B | `b10386a1` |
| [ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `c9132626` |
| [ML/reports/entry_path_v1_live_safe/seed_077/result.json](ML/reports/entry_path_v1_live_safe/seed_077/result.json) |  |  | 2026-05-30 | 2KB | `9ae2053a` |
| [ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_report.md) |  |  | 2026-05-30 | 530B | `1410cf6d` |
| [ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `b0da3773` |
| [ML/reports/entry_path_v1_live_safe/seed_123/result.json](ML/reports/entry_path_v1_live_safe/seed_123/result.json) |  |  | 2026-05-30 | 2KB | `1deffb2e` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/manifest.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/manifest.json) |  |  | 2026-05-07 | 77KB | `1c34773b` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/multi_seed_summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/multi_seed_summary.json) |  |  | 2026-05-07 | 3KB | `8e390e0e` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/entry_path_trade_filter_report.md) |  |  | 2026-05-07 | 568B | `dab58f2f` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `e03c5e81` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_007/summary.json) |  |  | 2026-05-07 | 13KB | `e83beaa4` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/entry_path_trade_filter_report.md) |  |  | 2026-05-07 | 571B | `4d3a7871` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `b042a4ee` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_017/summary.json) |  |  | 2026-05-07 | 13KB | `58ae1f30` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/entry_path_trade_filter_report.md) |  |  | 2026-05-07 | 570B | `d797c57d` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `7283f968` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/summary.json) |  |  | 2026-05-07 | 13KB | `2594d8dd` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/entry_path_trade_filter_report.md) |  |  | 2026-05-07 | 568B | `bd0ec8d3` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `ed97172f` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_077/summary.json) |  |  | 2026-05-07 | 12KB | `d8cbd80b` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/entry_path_trade_filter_report.md) |  |  | 2026-05-07 | 568B | `9e5bdf39` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/entry_path_trade_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `4ac5eeff` |
| [ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/summary.json](ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_123/summary.json) |  |  | 2026-05-07 | 13KB | `a413b33e` |
| [ML/reports/entry_path_v1_nearest_k16/summary.json](ML/reports/entry_path_v1_nearest_k16/summary.json) |  |  | 2026-05-30 | 38KB | `c2cd44e4` |
| [ML/reports/entry_path_v1_nearest_k4_geometry_only/summary.json](ML/reports/entry_path_v1_nearest_k4_geometry_only/summary.json) |  |  | 2026-05-30 | 6KB | `b830fcbe` |
| [ML/reports/entry_path_v1_nearest_k4_hgb/summary.json](ML/reports/entry_path_v1_nearest_k4_hgb/summary.json) |  |  | 2026-05-30 | 10KB | `4f0ded21` |
| [ML/reports/entry_path_v1_nearest_k4_lr/summary.json](ML/reports/entry_path_v1_nearest_k4_lr/summary.json) |  |  | 2026-05-30 | 10KB | `c8272495` |
| [ML/reports/entry_path_v1_nearest_k6/summary.json](ML/reports/entry_path_v1_nearest_k6/summary.json) |  |  | 2026-05-30 | 14KB | `88a47480` |
| [ML/reports/entry_path_v1_nearest_k8/summary.json](ML/reports/entry_path_v1_nearest_k8/summary.json) |  |  | 2026-05-30 | 19KB | `7c4b08bc` |
| [ML/reports/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 706B | `0d99ebcd` |
| [ML/reports/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `f665ab0d` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json) |  |  | 2026-05-30 | 2KB | `c04294b8` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost/n_boost_result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost/n_boost_result.json) |  |  | 2026-05-30 | 1KB | `bc8ca1d1` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 784B | `e322b4af` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `75b5246c` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/result.json) |  |  | 2026-05-30 | 2KB | `eae94c0a` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 730B | `3c9becc3` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `75dc9dfe` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/result.json) |  |  | 2026-05-30 | 2KB | `2f581d61` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 734B | `93515d31` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 2KB | `8f6e7efa` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/result.json) |  |  | 2026-05-30 | 2KB | `0754fd54` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 741B | `b661b8f9` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 2KB | `ef91132b` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/result.json) |  |  | 2026-05-30 | 2KB | `18710caf` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-30 | 729B | `0f00805b` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-30 | 1KB | `7d0d2ea6` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/result.json) |  |  | 2026-05-30 | 2KB | `4485f5d3` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/manifest.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/manifest.json) |  |  | 2026-05-07 | 94KB | `d4261fa7` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/multi_seed_summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/multi_seed_summary.json) |  |  | 2026-05-07 | 5KB | `6ef74aaa` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/baseline_a_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/baseline_a_report.md) |  |  | 2026-05-07 | 537B | `bd5e4b28` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/baseline_a_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/baseline_a_selected_rule.json) |  |  | 2026-05-07 | 1KB | `ff0cbc4b` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-07 | 806B | `497ccee3` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-07 | 1KB | `2df1f6c4` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_007/summary.json) |  |  | 2026-05-07 | 15KB | `8a6ef129` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/baseline_a_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/baseline_a_report.md) |  |  | 2026-05-07 | 537B | `eab7a343` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/baseline_a_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/baseline_a_selected_rule.json) |  |  | 2026-05-07 | 2KB | `bfdd4e83` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-07 | 746B | `b49223e2` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-07 | 1KB | `ee820fe5` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_017/summary.json) |  |  | 2026-05-07 | 15KB | `29503eaa` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/baseline_a_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/baseline_a_report.md) |  |  | 2026-05-07 | 537B | `8b3b53e3` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/baseline_a_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/baseline_a_selected_rule.json) |  |  | 2026-05-07 | 2KB | `1946e03d` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-07 | 759B | `12838781` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `5271f8fc` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_042/summary.json) |  |  | 2026-05-07 | 16KB | `13b80583` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/baseline_a_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/baseline_a_report.md) |  |  | 2026-05-07 | 537B | `1ea158a1` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/baseline_a_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/baseline_a_selected_rule.json) |  |  | 2026-05-07 | 1KB | `e1675839` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-07 | 807B | `079a6cba` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-07 | 2KB | `e44e6d28` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_077/summary.json) |  |  | 2026-05-07 | 15KB | `b6196236` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/baseline_a_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/baseline_a_report.md) |  |  | 2026-05-07 | 537B | `96a6a122` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/baseline_a_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/baseline_a_selected_rule.json) |  |  | 2026-05-07 | 1KB | `165812ed` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/entry_path_v1_quantile_filter_report.md) |  |  | 2026-05-07 | 743B | `ce12591c` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-05-07 | 1KB | `5129e82b` |
| [ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/summary.json](ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_123/summary.json) |  |  | 2026-05-07 | 15KB | `ffbf4300` |
| [ML/reports/entry_path_v1_quantile_selected_rule.json](ML/reports/entry_path_v1_quantile_selected_rule.json) |  |  | 2026-05-30 | 2KB | `a2fce0f7` |
| [ML/reports/entry_path_v1_score_direction/summary.json](ML/reports/entry_path_v1_score_direction/summary.json) |  |  | 2026-05-30 | 269B | `761b2790` |
| [ML/reports/entry_path_v1_signal_only_ablation/summary.json](ML/reports/entry_path_v1_signal_only_ablation/summary.json) |  |  | 2026-05-30 | 7KB | `6cf21739` |
| [ML/reports/entry_path_v1_signal_only_ablation/summary.md](ML/reports/entry_path_v1_signal_only_ablation/summary.md) |  |  | 2026-05-30 | 1KB | `ad02cfab` |
| [ML/reports/entry_path_v1_zones/summary.json](ML/reports/entry_path_v1_zones/summary.json) |  |  | 2026-05-30 | 14KB | `95fdf5ac` |
| [ML/reports/entry_path_v1_zones_plus_nearest_k4/summary.json](ML/reports/entry_path_v1_zones_plus_nearest_k4/summary.json) |  |  | 2026-05-30 | 24KB | `46eb5bcc` |
| [ML/reports/evaluate_test_H12.md](ML/reports/evaluate_test_H12.md) |  |  | 2026-05-30 | 513B | `8b8eb347` |
| [ML/reports/evaluate_test_entry_path_v1.md](ML/reports/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `a6f68803` |
| [ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md](ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md) |  |  | 2026-05-30 | 1KB | `46ed4ec9` |
| [ML/reports/evaluate_test_entry_path_v1_quantile.md](ML/reports/evaluate_test_entry_path_v1_quantile.md) |  |  | 2026-05-30 | 523B | `03c3cfb6` |
| [ML/reports/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-05-30 | 274B | `057fadd1` |
| [ML/reports/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-05-30 | 277B | `1c95661a` |
| [ML/reports/evaluate_test_tb.md](ML/reports/evaluate_test_tb.md) |  |  | 2026-05-30 | 1KB | `295448ff` |
| [ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-05-30 | 385B | `e972ae90` |
| [ML/reports/evaluate_test_trailing_stop_target_v1.md](ML/reports/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-05-30 | 304B | `087f3217` |
| [ML/reports/evaluate_validation_entry_path_v1.md](ML/reports/evaluate_validation_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `6eb89813` |
| [ML/reports/execution_policy_v2/frequency_trail_scan/summary.json](ML/reports/execution_policy_v2/frequency_trail_scan/summary.json) |  |  | 2026-05-30 | 3KB | `8a130d60` |
| [ML/reports/execution_policy_v2/summary.json](ML/reports/execution_policy_v2/summary.json) |  |  | 2026-05-30 | 26KB | `63d0a3c5` |
| [ML/reports/fav_3_vs_12_standalone/run_metadata.json](ML/reports/fav_3_vs_12_standalone/run_metadata.json) |  |  | 2026-05-30 | 1KB | `749e6a5b` |
| [ML/reports/fav_3_vs_12_standalone/selected_threshold.json](ML/reports/fav_3_vs_12_standalone/selected_threshold.json) |  |  | 2026-05-30 | 532B | `d941fc13` |
| [ML/reports/fav_3_vs_12_standalone/verdict.json](ML/reports/fav_3_vs_12_standalone/verdict.json) |  |  | 2026-05-30 | 893B | `1fc84a37` |
| [ML/reports/feature_bank_clean_comparison/report.md](ML/reports/feature_bank_clean_comparison/report.md) |  |  | 2026-05-30 | 1KB | `ea8f6f93` |
| [ML/reports/feature_bank_clean_comparison/summary.json](ML/reports/feature_bank_clean_comparison/summary.json) |  |  | 2026-05-30 | 1KB | `84b8ec2f` |
| [ML/reports/feature_bank_comparison/report.md](ML/reports/feature_bank_comparison/report.md) |  |  | 2026-05-30 | 1KB | `f4f494ed` |
| [ML/reports/feature_bank_comparison/summary.json](ML/reports/feature_bank_comparison/summary.json) |  |  | 2026-05-30 | 1KB | `97d30738` |
| [ML/reports/fractal_ablation.json](ML/reports/fractal_ablation.json) |  |  | 2026-06-05 | 14KB | `087d60c8` |
| [ML/reports/fractal_ablation_test.json](ML/reports/fractal_ablation_test.json) |  |  | 2026-06-05 | 10KB | `5de28e52` |
| [ML/reports/frozen_exit_policy.json](ML/reports/frozen_exit_policy.json) |  |  | 2026-05-30 | 537B | `4da12318` |
| [ML/reports/label_convention_audit.md](ML/reports/label_convention_audit.md) |  |  | 2026-05-30 | 3KB | `72706b95` |
| [ML/reports/limit_order_transformer.json](ML/reports/limit_order_transformer.json) |  |  | 2026-06-03 | 1KB | `e843ef45` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/artifact_inventory.json](ML/reports/live_safe_ml_audit/entry_path_v1/artifact_inventory.json) |  |  | 2026-05-30 | 997B | `2c0fea7b` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/entry_path_v1/legacy_export_metadata.json) |  |  | 2026-05-30 | 347B | `7e79d1b9` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/legacy_reproduction.json](ML/reports/live_safe_ml_audit/entry_path_v1/legacy_reproduction.json) |  |  | 2026-05-30 | 2KB | `7cd7e9b2` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/verdict.json](ML/reports/live_safe_ml_audit/entry_path_v1/verdict.json) |  |  | 2026-05-30 | 513B | `0989534c` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/artifact_inventory.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/artifact_inventory.json) |  |  | 2026-05-30 | 1KB | `1c5709af` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_export_metadata.json) |  |  | 2026-05-30 | 444B | `cba4678a` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_reproduction.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_reproduction.json) |  |  | 2026-05-30 | 1KB | `3a2da5c7` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/verdict.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/verdict.json) |  |  | 2026-05-30 | 539B | `d610f477` |
| [ML/reports/live_safe_ml_audit/feature_contract_summary.json](ML/reports/live_safe_ml_audit/feature_contract_summary.json) |  |  | 2026-05-30 | 658B | `edf19ffe` |
| [ML/reports/live_safe_ml_audit/frequency/artifact_inventory.json](ML/reports/live_safe_ml_audit/frequency/artifact_inventory.json) |  |  | 2026-05-30 | 870B | `309ff4de` |
| [ML/reports/live_safe_ml_audit/frequency/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/frequency/legacy_export_metadata.json) |  |  | 2026-05-30 | 715B | `efac01ff` |
| [ML/reports/live_safe_ml_audit/frequency/legacy_reproduction.json](ML/reports/live_safe_ml_audit/frequency/legacy_reproduction.json) |  |  | 2026-05-30 | 1KB | `ef368484` |
| [ML/reports/live_safe_ml_audit/frequency/verdict.json](ML/reports/live_safe_ml_audit/frequency/verdict.json) |  |  | 2026-05-30 | 729B | `b283e698` |
| [ML/reports/live_safe_ml_audit/legacy_export_summary.json](ML/reports/live_safe_ml_audit/legacy_export_summary.json) |  |  | 2026-05-30 | 4KB | `1421df0f` |
| [ML/reports/live_safe_ml_audit/legacy_reproduction_summary.json](ML/reports/live_safe_ml_audit/legacy_reproduction_summary.json) |  |  | 2026-05-30 | 8KB | `479e2c1c` |
| [ML/reports/live_safe_ml_audit/manifest.json](ML/reports/live_safe_ml_audit/manifest.json) |  |  | 2026-05-30 | 9KB | `48b1dbb4` |
| [ML/reports/live_safe_ml_audit/original_plus_path/artifact_inventory.json](ML/reports/live_safe_ml_audit/original_plus_path/artifact_inventory.json) |  |  | 2026-05-30 | 1KB | `d7a6d667` |
| [ML/reports/live_safe_ml_audit/original_plus_path/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/original_plus_path/legacy_export_metadata.json) |  |  | 2026-05-30 | 795B | `b0de7ed0` |
| [ML/reports/live_safe_ml_audit/original_plus_path/legacy_reproduction.json](ML/reports/live_safe_ml_audit/original_plus_path/legacy_reproduction.json) |  |  | 2026-05-30 | 1KB | `941b3788` |
| [ML/reports/live_safe_ml_audit/original_plus_path/verdict.json](ML/reports/live_safe_ml_audit/original_plus_path/verdict.json) |  |  | 2026-05-30 | 738B | `5e473c4d` |
| [ML/reports/live_safe_ml_audit/quality/artifact_inventory.json](ML/reports/live_safe_ml_audit/quality/artifact_inventory.json) |  |  | 2026-05-30 | 864B | `094256c6` |
| [ML/reports/live_safe_ml_audit/quality/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/quality/legacy_export_metadata.json) |  |  | 2026-05-30 | 708B | `61748342` |
| [ML/reports/live_safe_ml_audit/quality/legacy_reproduction.json](ML/reports/live_safe_ml_audit/quality/legacy_reproduction.json) |  |  | 2026-05-30 | 1KB | `ddcff55b` |
| [ML/reports/live_safe_ml_audit/quality/verdict.json](ML/reports/live_safe_ml_audit/quality/verdict.json) |  |  | 2026-05-30 | 727B | `6e173e29` |
| [ML/reports/live_safe_ml_audit/verdict_summary.json](ML/reports/live_safe_ml_audit/verdict_summary.json) |  |  | 2026-05-30 | 3KB | `d1d7c226` |
| [ML/reports/methodology_cycle_candidate_source_v2/README.md](ML/reports/methodology_cycle_candidate_source_v2/README.md) |  |  | 2026-06-03 | 3KB | `93b1a5fc` |
| [ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md](ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md) |  |  | 2026-06-03 | 2KB | `87798cc8` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json](ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json) |  |  | 2026-06-03 | 3KB | `929dd33f` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json](ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json) |  |  | 2026-06-03 | 5KB | `4f490eb2` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json](ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json) |  |  | 2026-06-03 | 4KB | `ab4f45ad` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json](ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json) |  |  | 2026-06-03 | 3KB | `cffbff43` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage03_leakage_gate.json](ML/reports/methodology_cycle_candidate_source_v2/stage03_leakage_gate.json) |  |  | 2026-06-03 | 4KB | `5f498f87` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage04_labeling_audit.json](ML/reports/methodology_cycle_candidate_source_v2/stage04_labeling_audit.json) |  |  | 2026-06-03 | 5KB | `d5009b71` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json](ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json) |  |  | 2026-06-03 | 3KB | `48862ccc` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage06_temporal_split_manifest.json](ML/reports/methodology_cycle_candidate_source_v2/stage06_temporal_split_manifest.json) |  |  | 2026-06-03 | 2KB | `29823971` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json](ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json) |  |  | 2026-06-03 | 16KB | `02fc44ba` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json](ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json) |  |  | 2026-06-03 | 2KB | `4d07ed46` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json](ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json) |  |  | 2026-06-03 | 2KB | `b0280abd` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json](ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json) |  |  | 2026-06-03 | 116KB | `07346468` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json](ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json) |  |  | 2026-06-03 | 7KB | `8c158f4f` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json](ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json) |  |  | 2026-05-30 | 3KB | `14b7cc3f` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json](ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json) |  |  | 2026-05-30 | 3KB | `bacc13b6` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.json](ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.json) |  |  | 2026-05-30 | 3KB | `5cb5fe58` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.md](ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.md) |  |  | 2026-05-30 | 279B | `75a53f21` |
| [ML/reports/n_boost_result.json](ML/reports/n_boost_result.json) |  |  | 2026-05-30 | 1KB | `9248dae1` |
| [ML/reports/optuna_best_params_bilstm_regression.json](ML/reports/optuna_best_params_bilstm_regression.json) |  |  | 2026-05-30 | 496B | `b1a36a79` |
| [ML/reports/optuna_best_params_cnn1d_classification.json](ML/reports/optuna_best_params_cnn1d_classification.json) |  |  | 2026-05-30 | 461B | `25ae2754` |
| [ML/reports/optuna_best_params_transformer_regression_updn.json](ML/reports/optuna_best_params_transformer_regression_updn.json) |  |  | 2026-05-30 | 539B | `5a6d031a` |
| [ML/reports/optuna_study_bilstm_regression_20260311_223415.json](ML/reports/optuna_study_bilstm_regression_20260311_223415.json) |  |  | 2026-05-30 | 1KB | `f908cbce` |
| [ML/reports/optuna_study_bilstm_regression_20260312_003636.json](ML/reports/optuna_study_bilstm_regression_20260312_003636.json) |  |  | 2026-05-30 | 31KB | `8318dd5a` |
| [ML/reports/optuna_study_bilstm_regression_20260312_105613.json](ML/reports/optuna_study_bilstm_regression_20260312_105613.json) |  |  | 2026-05-30 | 18KB | `9860a4c5` |
| [ML/reports/optuna_study_bilstm_regression_20260312_112811.json](ML/reports/optuna_study_bilstm_regression_20260312_112811.json) |  |  | 2026-05-30 | 18KB | `535d2951` |
| [ML/reports/optuna_study_bilstm_regression_20260316_102024.json](ML/reports/optuna_study_bilstm_regression_20260316_102024.json) |  |  | 2026-05-30 | 31KB | `ef829e93` |
| [ML/reports/optuna_study_cnn1d_classification_20260226_134119.json](ML/reports/optuna_study_cnn1d_classification_20260226_134119.json) |  |  | 2026-05-30 | 29KB | `a53f62cd` |
| [ML/reports/optuna_study_cnn1d_classification_20260227_231828.json](ML/reports/optuna_study_cnn1d_classification_20260227_231828.json) |  |  | 2026-05-30 | 28KB | `f8e66057` |
| [ML/reports/optuna_study_cnn1d_classification_20260228_100415.json](ML/reports/optuna_study_cnn1d_classification_20260228_100415.json) |  |  | 2026-05-30 | 29KB | `c38b7403` |
| [ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json](ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json) |  |  | 2026-05-30 | 33KB | `2c98a9f9` |
| [ML/reports/outcome_target_validation_benchmark.md](ML/reports/outcome_target_validation_benchmark.md) |  |  | 2026-05-30 | 763B | `9104e652` |
| [ML/reports/pf_uplift_discovery/baseline_numbers.json](ML/reports/pf_uplift_discovery/baseline_numbers.json) |  |  | 2026-05-30 | 2KB | `4519e3fe` |
| [ML/reports/pf_uplift_discovery/hypotheses_longlist.md](ML/reports/pf_uplift_discovery/hypotheses_longlist.md) |  |  | 2026-05-30 | 8KB | `61fcd585` |
| [ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json](ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json) |  |  | 2026-05-30 | 602B | `d5ab62dc` |
| [ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json](ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json) |  |  | 2026-05-30 | 536B | `afb475b6` |
| [ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json) |  |  | 2026-05-30 | 655B | `1db83311` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json) |  |  | 2026-05-30 | 665B | `8da7e815` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json) |  |  | 2026-05-30 | 623B | `866da98b` |
| [ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json](ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json) |  |  | 2026-05-30 | 614B | `2146acd5` |
| [ML/reports/pf_uplift_discovery/run_metadata.json](ML/reports/pf_uplift_discovery/run_metadata.json) |  |  | 2026-05-30 | 552B | `2ffaa2db` |
| [ML/reports/quantile_fav_composition/intersection_diagnostic.json](ML/reports/quantile_fav_composition/intersection_diagnostic.json) |  |  | 2026-05-30 | 270B | `8877d751` |
| [ML/reports/quantile_fav_composition/n_boost_composition.json](ML/reports/quantile_fav_composition/n_boost_composition.json) |  |  | 2026-05-30 | 155B | `164387a5` |
| [ML/reports/quantile_fav_composition/run_metadata.json](ML/reports/quantile_fav_composition/run_metadata.json) |  |  | 2026-05-30 | 4KB | `6aa02ee6` |
| [ML/reports/quantile_fav_composition/test_metrics.json](ML/reports/quantile_fav_composition/test_metrics.json) |  |  | 2026-05-30 | 1KB | `86714f9b` |
| [ML/reports/quantile_fav_composition/updn_active_source/metadata.json](ML/reports/quantile_fav_composition/updn_active_source/metadata.json) |  |  | 2026-05-30 | 619B | `d44841e2` |
| [ML/reports/quantile_fav_composition/validation_metrics.json](ML/reports/quantile_fav_composition/validation_metrics.json) |  |  | 2026-05-30 | 1KB | `7583bfeb` |
| [ML/reports/quantile_forward_validation/run_metadata.json](ML/reports/quantile_forward_validation/run_metadata.json) |  |  | 2026-05-30 | 554B | `eeb46771` |
| [ML/reports/quantile_forward_validation/summary.json](ML/reports/quantile_forward_validation/summary.json) |  |  | 2026-05-30 | 440B | `f208a93b` |
| [ML/reports/quantile_relaxed_composition/selected_baseline.json](ML/reports/quantile_relaxed_composition/selected_baseline.json) |  |  | 2026-05-30 | 118B | `3c6efae0` |
| [ML/reports/reproducibility_report_12H.md](ML/reports/reproducibility_report_12H.md) |  |  | 2026-05-30 | 1KB | `c9af48ba` |
| [ML/reports/rf_gridsearch.json](ML/reports/rf_gridsearch.json) |  |  | 2026-06-05 | 1KB | `66d3935f` |
| [ML/reports/signal_export_parity/original_plus_path_20260420/summary.json](ML/reports/signal_export_parity/original_plus_path_20260420/summary.json) |  |  | 2026-05-30 | 3KB | `b17fa136` |
| [ML/reports/signal_export_parity/original_plus_path_20260420/summary.md](ML/reports/signal_export_parity/original_plus_path_20260420/summary.md) |  |  | 2026-05-30 | 1KB | `aa632197` |
| [ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json](ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json) |  |  | 2026-05-30 | 2KB | `a2d1b9ae` |
| [ML/reports/system_correlation_portfolio/xauusd_system_correlation/run_metadata.json](ML/reports/system_correlation_portfolio/xauusd_system_correlation/run_metadata.json) |  |  | 2026-05-30 | 160B | `295db8d3` |
| [ML/reports/system_correlation_portfolio/xauusd_system_correlation/summary.json](ML/reports/system_correlation_portfolio/xauusd_system_correlation/summary.json) |  |  | 2026-05-30 | 8KB | `6f06d60e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/summary.json) |  |  | 2026-05-30 | 13KB | `18845574` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/summary.json) |  |  | 2026-05-30 | 13KB | `45f40666` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/summary.json) |  |  | 2026-05-30 | 13KB | `5ace345e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/summary.json) |  |  | 2026-05-30 | 13KB | `67c7c6b4` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/summary.json) |  |  | 2026-05-30 | 13KB | `9d6d29f3` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/summary.json) |  |  | 2026-05-30 | 13KB | `066a4de4` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/summary.json) |  |  | 2026-05-30 | 13KB | `8033d24e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/summary.json) |  |  | 2026-05-30 | 13KB | `66813a54` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/summary.json) |  |  | 2026-05-30 | 13KB | `9e9f484e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/manifest.json](ML/reports/take_skip_lib_pic_feature_matrix/manifest.json) |  |  | 2026-05-30 | 136KB | `f5ddd710` |
| [ML/reports/take_skip_lib_pic_selection/final_verdict.json](ML/reports/take_skip_lib_pic_selection/final_verdict.json) |  |  | 2026-05-30 | 5KB | `d5323101` |
| [ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/summary.json](ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/summary.json) |  |  | 2026-05-30 | 11KB | `230648aa` |
| [ML/reports/take_skip_live_safe_baseline/manifest.json](ML/reports/take_skip_live_safe_baseline/manifest.json) |  |  | 2026-05-30 | 13KB | `b69fcca8` |
| [ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/summary.json](ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/summary.json) |  |  | 2026-05-30 | 13KB | `a256cdf5` |
| [ML/reports/take_skip_live_safe_geometry/manifest.json](ML/reports/take_skip_live_safe_geometry/manifest.json) |  |  | 2026-05-30 | 15KB | `166e9b6b` |
| [ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-07 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/summary.json](ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/summary.json) |  |  | 2026-05-07 | 21KB | `95ef2fd4` |
| [ML/reports/take_skip_live_safe_geometry_path/manifest.json](ML/reports/take_skip_live_safe_geometry_path/manifest.json) |  |  | 2026-05-07 | 23KB | `d436d29a` |
| [ML/reports/take_skip_live_safe_path/live_safe_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_path/live_safe_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_path/live_safe_path_seq50/summary.json](ML/reports/take_skip_live_safe_path/live_safe_path_seq50/summary.json) |  |  | 2026-05-30 | 12KB | `ca389d9e` |
| [ML/reports/take_skip_live_safe_path/manifest.json](ML/reports/take_skip_live_safe_path/manifest.json) |  |  | 2026-05-30 | 14KB | `3e2117d0` |
| [ML/reports/take_skip_mt4_trailing_sequential/summary.json](ML/reports/take_skip_mt4_trailing_sequential/summary.json) |  |  | 2026-05-30 | 6KB | `80ed09d0` |
| [ML/reports/take_skip_original_contour_feature_matrix/manifest.json](ML/reports/take_skip_original_contour_feature_matrix/manifest.json) |  |  | 2026-05-30 | 141KB | `16fd569e` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 947B | `80f24abc` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/summary.json) |  |  | 2026-05-30 | 14KB | `9dc199bf` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 942B | `d3601dcb` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/summary.json) |  |  | 2026-05-30 | 14KB | `9d268fe8` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 940B | `d803eebc` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/summary.json) |  |  | 2026-05-30 | 14KB | `633b3988` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 995B | `ab51ed64` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/summary.json) |  |  | 2026-05-30 | 13KB | `5a9a3e85` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 985B | `4b87cdfa` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/summary.json) |  |  | 2026-05-30 | 15KB | `dde6609b` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 990B | `6ed19a6a` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/summary.json) |  |  | 2026-05-30 | 11KB | `c198bea1` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 995B | `9f7ffd5d` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/summary.json) |  |  | 2026-05-30 | 13KB | `d6217569` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 1009B | `7348dd7a` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/summary.json) |  |  | 2026-05-30 | 15KB | `b649eff8` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 1002B | `a27dd761` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/summary.json) |  |  | 2026-05-30 | 15KB | `cab95008` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/manifest.json](ML/reports/take_skip_original_contour_feature_matrix_control/manifest.json) |  |  | 2026-05-30 | 16KB | `7f73680d` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 949B | `3089f610` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/summary.json) |  |  | 2026-05-30 | 14KB | `d54f4bea` |
| [ML/reports/take_skip_trailing_stop_matrix/manifest.json](ML/reports/take_skip_trailing_stop_matrix/manifest.json) |  |  | 2026-05-30 | 10KB | `a62ab304` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-05-30 | 274B | `057fadd1` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/summary.json) |  |  | 2026-05-30 | 3KB | `cae85b28` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-05-30 | 274B | `352dd6b3` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/summary.json) |  |  | 2026-05-30 | 2KB | `d8a968e2` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-05-30 | 274B | `352dd6b3` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/summary.json) |  |  | 2026-05-30 | 3KB | `1ccb35bf` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/manifest.json](ML/reports/take_skip_trailing_stop_matrix_smoke/manifest.json) |  |  | 2026-05-30 | 2KB | `06beab4e` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-05-30 | 274B | `9ac140c5` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/summary.json) |  |  | 2026-05-30 | 2KB | `1b967591` |
| [ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json](ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json) |  |  | 2026-05-30 | 3KB | `c5aa0bfc` |
| [ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json) |  |  | 2026-05-30 | 723B | `071ea894` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json](ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json) |  |  | 2026-05-30 | 16KB | `5a4d337a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json) |  |  | 2026-05-30 | 964B | `04c514f5` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-05-30 | 277B | `20c0004a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json) |  |  | 2026-05-30 | 4KB | `14a5e536` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-05-30 | 963B | `1aafa9e6` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-05-30 | 277B | `4af22546` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json) |  |  | 2026-05-30 | 4KB | `6bd39710` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json) |  |  | 2026-05-30 | 962B | `f4370930` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-05-30 | 277B | `ab926937` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json) |  |  | 2026-05-30 | 4KB | `416def03` |
| [ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json) |  |  | 2026-05-30 | 1KB | `297c1f74` |
| [ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json) |  |  | 2026-05-30 | 903B | `3d56d55f` |
| [ML/reports/tb_direction_signal.json](ML/reports/tb_direction_signal.json) |  |  | 2026-06-05 | 16KB | `69d12535` |
| [ML/reports/tb_mt4_verdict/test_summary.json](ML/reports/tb_mt4_verdict/test_summary.json) |  |  | 2026-05-30 | 172B | `6ea3e9d3` |
| [ML/reports/tb_mt4_verdict/validation_summary.json](ML/reports/tb_mt4_verdict/validation_summary.json) |  |  | 2026-05-30 | 167B | `cc2e7d34` |
| [ML/reports/tb_selected_rule.json](ML/reports/tb_selected_rule.json) |  |  | 2026-05-30 | 279B | `3329dfb8` |
| [ML/reports/telemetry_frequency_v1/calibration/selected_rule.json](ML/reports/telemetry_frequency_v1/calibration/selected_rule.json) |  |  | 2026-05-30 | 439B | `50ecae6a` |
| [ML/reports/telemetry_frequency_v1/calibration/summary.json](ML/reports/telemetry_frequency_v1/calibration/summary.json) |  |  | 2026-05-30 | 701B | `4b48b3ec` |
| [ML/reports/telemetry_frequency_v1/calibration/summary.md](ML/reports/telemetry_frequency_v1/calibration/summary.md) |  |  | 2026-05-30 | 442B | `753c04fc` |
| [ML/reports/telemetry_frequency_v1/export_metadata.json](ML/reports/telemetry_frequency_v1/export_metadata.json) |  |  | 2026-05-30 | 732B | `a0ea9250` |
| [ML/reports/telemetry_frequency_v1/export_metadata_highfreq500.json](ML/reports/telemetry_frequency_v1/export_metadata_highfreq500.json) |  |  | 2026-05-30 | 757B | `42ee18bd` |
| [ML/reports/telemetry_frequency_v1/export_parity/summary.json](ML/reports/telemetry_frequency_v1/export_parity/summary.json) |  |  | 2026-05-30 | 1KB | `6e320726` |
| [ML/reports/telemetry_frequency_v1/export_parity/summary.md](ML/reports/telemetry_frequency_v1/export_parity/summary.md) |  |  | 2026-05-30 | 322B | `230e6422` |
| [ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.json) |  |  | 2026-05-30 | 776B | `ec66e9e2` |
| [ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.md) |  |  | 2026-05-30 | 335B | `5a667646` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.json) |  |  | 2026-05-30 | 724B | `200359b5` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.md) |  |  | 2026-05-30 | 336B | `3647c03e` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.json) |  |  | 2026-05-30 | 1KB | `f61e6e6c` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.md) |  |  | 2026-05-30 | 798B | `398dcef2` |
| [ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json](ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json) |  |  | 2026-05-13 | 726B | `0958f17c` |
| [ML/reports/telemetry_frequency_v1/runtime/runtime_state.json](ML/reports/telemetry_frequency_v1/runtime/runtime_state.json) |  |  | 2026-05-13 | 147B | `aedc4ced` |
| [ML/reports/telemetry_frequency_v1/tester_export_metadata_highfreq500.json](ML/reports/telemetry_frequency_v1/tester_export_metadata_highfreq500.json) |  |  | 2026-05-30 | 704B | `8f423454` |
| [ML/reports/telemetry_frequency_v1/tester_export_parity/summary.json](ML/reports/telemetry_frequency_v1/tester_export_parity/summary.json) |  |  | 2026-05-30 | 2KB | `027ea74c` |
| [ML/reports/telemetry_frequency_v1/tester_export_parity/summary.md](ML/reports/telemetry_frequency_v1/tester_export_parity/summary.md) |  |  | 2026-05-30 | 775B | `fb0a81e5` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.json) |  |  | 2026-05-30 | 966B | `192c5dc2` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.md) |  |  | 2026-05-30 | 235B | `b9da1e09` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.json) |  |  | 2026-05-30 | 969B | `251ec6c8` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.md) |  |  | 2026-05-30 | 238B | `57278fb0` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.json) |  |  | 2026-05-30 | 955B | `de7e96bf` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.md) |  |  | 2026-05-30 | 252B | `a406faba` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.json) |  |  | 2026-05-30 | 219B | `1c49a028` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.md) |  |  | 2026-05-30 | 244B | `56b6829e` |
| [ML/reports/threshold_analysis_12H.md](ML/reports/threshold_analysis_12H.md) |  |  | 2026-05-30 | 2KB | `2eba7e9d` |
| [ML/reports/threshold_analysis_24H.md](ML/reports/threshold_analysis_24H.md) |  |  | 2026-05-30 | 2KB | `b6b5b9d3` |
| [ML/reports/threshold_analysis_48H.md](ML/reports/threshold_analysis_48H.md) |  |  | 2026-05-30 | 2KB | `9f692fd3` |
| [ML/reports/threshold_analysis_tb.md](ML/reports/threshold_analysis_tb.md) |  |  | 2026-05-30 | 975B | `d501c624` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `4210c896` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 349B | `36a6a110` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 498B | `47947c94` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `92fbb96a` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json) |  |  | 2026-05-30 | 9KB | `c0697157` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `aae66f9e` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 347B | `c94aaebb` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 476B | `f8499cc8` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `6afa1767` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json) |  |  | 2026-05-30 | 9KB | `cb8bd8b7` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `23ded61c` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 347B | `e511119f` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 493B | `f3e78f8d` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `93b3aaca` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json) |  |  | 2026-05-30 | 9KB | `9611273d` |
| [ML/reports/track_a_max_out_matrix/manifest.json](ML/reports/track_a_max_out_matrix/manifest.json) |  |  | 2026-05-30 | 63KB | `d565f9d8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `49b4b8cc` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 327B | `0effabc3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 514B | `88f69647` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `24810803` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json) |  |  | 2026-05-30 | 9KB | `6c2cbc3e` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `200c62ad` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 325B | `5795728a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 492B | `eb63ea67` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `ea93c21a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json) |  |  | 2026-05-30 | 9KB | `1aeaccaa` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `84235cc8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 325B | `2eee4697` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 490B | `6af015f3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `249b3cf5` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json) |  |  | 2026-05-30 | 9KB | `39c00532` |
| [ML/reports/track_a_max_out_matrix_deep/manifest.json](ML/reports/track_a_max_out_matrix_deep/manifest.json) |  |  | 2026-05-30 | 25KB | `f1b2534a` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `52d97d3c` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 335B | `035d3a21` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 495B | `f4b312bb` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `d87b2158` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json) |  |  | 2026-05-30 | 11KB | `67c6488f` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-05-30 | 1KB | `c8010aa4` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-05-30 | 335B | `5ca74235` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-05-30 | 487B | `0a640325` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-05-30 | 1KB | `a6f68803` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json) |  |  | 2026-05-30 | 11KB | `c4f044c8` |
| [ML/reports/trailing_stop_target_matrix/manifest.json](ML/reports/trailing_stop_target_matrix/manifest.json) |  |  | 2026-05-30 | 13KB | `eca77374` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-05-30 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-05-30 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-05-30 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-05-30 | 304B | `087f3217` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json) |  |  | 2026-05-30 | 3KB | `27fe5256` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-05-30 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-05-30 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-05-30 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-05-30 | 304B | `82e3e008` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json) |  |  | 2026-05-30 | 3KB | `15b1b065` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-05-30 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-05-30 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-05-30 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-05-30 | 304B | `311c6d96` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json) |  |  | 2026-05-30 | 3KB | `e7960f2b` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json) |  |  | 2026-05-30 | 1KB | `a654ac5f` |
| [ML/reports/trailing_stop_target_quantile/manifest.json](ML/reports/trailing_stop_target_quantile/manifest.json) |  |  | 2026-05-30 | 3KB | `2e163aa4` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json) |  |  | 2026-05-30 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-05-30 | 385B | `e972ae90` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json) |  |  | 2026-05-30 | 2KB | `255c26ad` |
| [ML/reports/transformer_direction/feature_statistics.json](ML/reports/transformer_direction/feature_statistics.json) |  |  | 2026-05-30 | 410B | `0443aada` |
| [ML/reports/transformer_direction/target_combos.json](ML/reports/transformer_direction/target_combos.json) |  |  | 2026-05-30 | 424B | `8158d7d5` |
| [ML/reports/transformer_direction/target_statistics.json](ML/reports/transformer_direction/target_statistics.json) |  |  | 2026-05-30 | 7KB | `6120e49f` |
| [ML/reports/transformer_direction/validation_grid_finetune.json](ML/reports/transformer_direction/validation_grid_finetune.json) |  |  | 2026-05-30 | 1KB | `a0bc9c14` |
| [ML/reports/transformer_direction/validation_grid_frozen.json](ML/reports/transformer_direction/validation_grid_frozen.json) |  |  | 2026-05-30 | 4KB | `2151ede9` |
| [ML/reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | 🏁 | 2026-06-05 | 7KB | `9301d516` |
| [ML/run_entry_path_live_safe_retrain.py](ML/run_entry_path_live_safe_retrain.py) | Multi-seed retrain/export/benchmark для `entry_path_v1_live_safe` с seed-specific checkpoint папками | ✅ | 2026-06-05 | 8KB | `4d781bf1` |
| [ML/run_entry_path_quantile_live_safe_retrain.py](ML/run_entry_path_quantile_live_safe_retrain.py) | Multi-seed retrain/export/benchmark для `entry_path_v1_quantile` поверх CPU baseline `A @ 7.5%` | ✅ | 2026-06-05 | 13KB | `6ebfd944` |
| [ML/run_live_safe_ml_audit.py](ML/run_live_safe_ml_audit.py) | CLI для audit inventory, feature trace, legacy replay и verdict | ✅ | 2026-06-05 | 16KB | `e8733513` |
| [ML/run_take_skip_lib_pic_feature_matrix.py](ML/run_take_skip_lib_pic_feature_matrix.py) | Training matrix для `take_skip_v2` с профилями признаков `lib_PIC` внутри модели | 🚧 | 2026-06-05 | 25KB | `68fde791` |
| [ML/run_take_skip_original_contour_feature_matrix.py](ML/run_take_skip_original_contour_feature_matrix.py) | Training matrix для старого single-tensor `take_skip_v2` контура, включая live-safe baseline/path/geometry без Python future-признаков | 🚧 | 2026-06-05 | 31KB | `1d7c7b3c` |
| [ML/run_take_skip_trailing_stop_matrix.py](ML/run_take_skip_trailing_stop_matrix.py) |  |  | 2026-06-05 | 7KB | `77b1587b` |
| [ML/run_take_skip_trailing_stop_v2_matrix.py](ML/run_take_skip_trailing_stop_v2_matrix.py) |  |  | 2026-06-05 | 6KB | `2be9df55` |
| [ML/run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | ✅ | 2026-06-05 | 6KB | `0d1d781d` |
| [ML/run_trailing_stop_target_matrix.py](ML/run_trailing_stop_target_matrix.py) | Оркестратор bounded matrix для `trailing_stop_target_v1` | ✅ | 2026-06-05 | 9KB | `8c2ac272` |
| [ML/run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | ✅ | 2026-06-05 | 6KB | `ac5afba9` |
| [ML/stage09_stability_refreeze.py](ML/stage09_stability_refreeze.py) | Stage 09 — stability scan + canonical frozen rule (SOURCE OF TRUTH for stage09_frozen_rule.json) | ✅ | 2026-06-05 | 14KB | `813e9f29` |
| [ML/stage10_frozen_test_oos.py](ML/stage10_frozen_test_oos.py) | Stage 10 — one-shot frozen test/OOS evaluation for candidate-source v2 | ✅ | 2026-06-05 | 11KB | `e3f8847f` |
| [ML/take_skip_trailing_stop_task.py](ML/take_skip_trailing_stop_task.py) |  |  | 2026-06-05 | 4KB | `8e0a93f6` |
| [ML/take_skip_trailing_stop_v2_task.py](ML/take_skip_trailing_stop_v2_task.py) |  |  | 2026-06-05 | 4KB | `227844ec` |
| [ML/tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | 🏁 | 2026-06-05 | 2KB | `502427cf` |
| [ML/tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | ✅ | 2026-06-05 | 4KB | `f07ea73a` |
| [ML/telemetry_daily_reconciliation.py](ML/telemetry_daily_reconciliation.py) | Ежедневная сверка telemetry `ml_signals.csv` с MT4 MLP open/close log | ✅ | 2026-06-05 | 14KB | `3d1ff671` |
| [ML/threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | ✅ | 2026-06-05 | 47KB | `cb5483fc` |
| [ML/trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | ✅ | 2026-06-05 | 4KB | `9e87baba` |
| [ML/trailing_stop_target_task.py](ML/trailing_stop_target_task.py) | Trailing-stop target task: target contract, export helpers и metrics | ✅ | 2026-06-05 | 1KB | `05a05382` |
| [ML/train.py](ML/train.py) | Обучение ML-моделей; `--output-dir` изолирует checkpoint/result для seed/device аудита | ✅ | 2026-06-05 | 117KB | `09dec601` |
| [ML/transformer_direction_train.py](ML/transformer_direction_train.py) |  |  | 2026-06-05 | 32KB | `6833bf35` |
| [ML/triple_barrier_mt4_execution.py](ML/triple_barrier_mt4_execution.py) |  |  | 2026-06-05 | 6KB | `e2520e9d` |
| [ML/utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ | 2026-06-05 | 12KB | `1984242a` |
| [ML/validation_freeze.py](ML/validation_freeze.py) | Stage 09 — deterministic Transformer training + checkpoint + round-trip verification (does NOT generate frozen rule) | ✅ | 2026-06-05 | 12KB | `dff1e63f` |

## Processing

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [processing/README.md](processing/README.md) |  |  | 2026-06-05 | 2KB | `1bc42412` |
| [processing/denormalize_updn.py](processing/denormalize_updn.py) |  |  | 2026-06-05 | 7KB | `256f1fd6` |
| [processing/fractal_preprocessing.py](processing/fractal_preprocessing.py) | Общая сортировка фракталов внутри строки для training/online | ✅ | 2026-06-05 | 3KB | `37670f70` |
| [processing/label_audit.py](processing/label_audit.py) |  |  | 2026-06-05 | 4KB | `29974629` |
| [processing/label_main.py](processing/label_main.py) | CLI оркестратор pipeline | 🏁 | 2026-06-05 | 15KB | `7041199f` |
| [processing/label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | 🏁 | 2026-06-05 | 56KB | `d13b0a25` |
| [processing/normalize.py](processing/normalize.py) | Построчная нормализация признаков | 🏁 | 2026-06-05 | 28KB | `109b2cc6` |
| [processing/online_causal_preprocessing.py](processing/online_causal_preprocessing.py) | Online-safe preprocessing: сортировка + проверка фракталов + тихая rowwise-нормализация без future labels | ✅ | 2026-06-05 | 4KB | `c194aa91` |
| [processing/purge_split.py](processing/purge_split.py) |  |  | 2026-06-05 | 2KB | `9b5e1faf` |

## API

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [API/README.md](API/README.md) |  |  | 2026-05-30 | 7KB | `fce994e8` |
| [API/api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, общий live-safe preprocessing, ML-сигнал |  | 2026-06-05 | 6KB | `5174dd3b` |
| [API/exit_policy_research.py](API/exit_policy_research.py) | Offline research: сравнение ML-политик выхода и position management | 🏁 | 2026-06-05 | 14KB | `0caf0735` |
| [API/export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) | Применение frozen `entry_path_v1_quantile` rule к prediction CSV и экспорт `time;signal` | ✅ | 2026-06-05 | 8KB | `a5a84e1a` |
| [API/export_entry_path_v1_signals.py](API/export_entry_path_v1_signals.py) | Применение frozen `entry_path_v1` rule к prediction CSV и экспорт `time;signal` | ✅ | 2026-06-05 | 14KB | `7b69d64a` |
| [API/export_take_skip_trailing_stop_v2_signals.py](API/export_take_skip_trailing_stop_v2_signals.py) | Применение frozen take/skip v2 rule к prediction CSV и экспорт `time;signal` с optional metadata | ✅ | 2026-06-05 | 15KB | `e2430007` |
| [API/generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | ✅ | 2026-06-05 | 34KB | `d721c7a3` |
| [API/signal_path_atlas.py](API/signal_path_atlas.py) | Research CLI: ATR-normalized Signal Path Atlas, path archetypes, holdout validation | 🏁 | 2026-06-05 | 37KB | `9fd6cd00` |
| [API/signal_quality_research.py](API/signal_quality_research.py) | Signal Quality Filter Research (Variant 4): multi-horizon prediction features как фильтры | 🏁 | 2026-06-05 | 29KB | `31830287` |
| [API/signal_research.py](API/signal_research.py) | Research CLI: качество ML-сигналов по реальным OHLC (Variant 2/3) | 🏁 | 2026-06-05 | 72KB | `da83229a` |
| [API/telemetry_signal_watcher.py](API/telemetry_signal_watcher.py) | Фоновый online watcher telemetry-контура с contract guard: `Nero.csv` → causal preprocessing → prediction CSV → `ml_signals.csv` | ✅ | 2026-06-05 | 25KB | `4acdc2d4` |
| [API/test_api_client.py](API/test_api_client.py) | Интеграционный тест REST API-сервера (MT4) | 🏁 | 2026-06-05 | 1KB | `bf393de3` |

## Statistics

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [statistics/EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | 🏁 | 2026-05-30 | 188KB | `4c750fc3` |
| [statistics/README.md](statistics/README.md) |  |  | 2026-05-30 | 2KB | `8a02dc7e` |
| [statistics/analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | 🏁 | 2026-06-05 | 8KB | `f3ed1639` |
| [statistics/class_statistics.json](statistics/class_statistics.json) |  |  | 2026-05-30 | 6KB | `c107590a` |
| [statistics/data_contract_smoke_check.py](statistics/data_contract_smoke_check.py) |  |  | 2026-06-05 | 6KB | `6e303333` |
| [statistics/feature_catalog.json](statistics/feature_catalog.json) |  |  | 2026-05-30 | 70KB | `bb41c2d1` |
| [statistics/nero_features_metadata.json](statistics/nero_features_metadata.json) |  |  | 2026-05-30 | 6KB | `fc79c23a` |
| [statistics/reports/EDA_executed.ipynb](statistics/reports/EDA_executed.ipynb) |  |  | 2026-04-16 | 3MB | `--------` |
| [statistics/reports/EDA_report.md](statistics/reports/EDA_report.md) |  |  | 2026-05-30 | 59KB | `01e9ac82` |
| [statistics/signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | ✅ | 2026-06-05 | 49KB | `0088ddc3` |
| [statistics/statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | 🏁 | 2026-06-05 | 21KB | `c725dd71` |
| [statistics/statistics_summary.json](statistics/statistics_summary.json) |  |  | 2026-05-30 | 5KB | `1e7882c0` |

## Tests

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [tests/README.md](tests/README.md) |  |  | 2026-05-30 | 2KB | `4d2c2f12` |
| [tests/processing/test_limit_order_barriers.py](tests/processing/test_limit_order_barriers.py) |  |  | 2026-06-05 | 15KB | `da00aed8` |
| [tests/test_api_server_preprocessing.py](tests/test_api_server_preprocessing.py) | `API/api_server.py` shared online preprocessing contract | ✅ | 2026-06-05 | 1KB | `11e15c32` |
| [tests/test_benchmark_cross_instrument_robustness.py](tests/test_benchmark_cross_instrument_robustness.py) | `ML/benchmark_cross_instrument_robustness.py` | ✅ | 2026-06-05 | 9KB | `745821a7` |
| [tests/test_benchmark_entry_path_all_rows_ranking.py](tests/test_benchmark_entry_path_all_rows_ranking.py) | `ML/benchmark_entry_path_all_rows_ranking.py` | ✅ | 2026-06-05 | 3KB | `0e7bc727` |
| [tests/test_benchmark_entry_path_binary_direction.py](tests/test_benchmark_entry_path_binary_direction.py) |  |  | 2026-06-05 | 2KB | `4236bb92` |
| [tests/test_benchmark_entry_path_causal_surrogate.py](tests/test_benchmark_entry_path_causal_surrogate.py) | `ML/benchmark_entry_path_causal_surrogate.py` | ✅ | 2026-06-05 | 3KB | `3d39bd74` |
| [tests/test_benchmark_entry_path_direct_bar_model.py](tests/test_benchmark_entry_path_direct_bar_model.py) | `ML/benchmark_entry_path_direct_bar_model.py` | ✅ | 2026-06-05 | 3KB | `ac56085f` |
| [tests/test_benchmark_entry_path_fractal_level_direct_direction.py](tests/test_benchmark_entry_path_fractal_level_direct_direction.py) |  |  | 2026-06-05 | 1KB | `4d81e1e6` |
| [tests/test_benchmark_entry_path_signal_only_ablation.py](tests/test_benchmark_entry_path_signal_only_ablation.py) | `ML/benchmark_entry_path_signal_only_ablation.py` | ✅ | 2026-06-05 | 3KB | `142ff299` |
| [tests/test_benchmark_entry_path_v1_frequency.py](tests/test_benchmark_entry_path_v1_frequency.py) | `ML/benchmark_entry_path_v1_frequency.py` | ✅ | 2026-06-05 | 739B | `40f6843e` |
| [tests/test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | ✅ | 2026-06-05 | 2KB | `78d542d3` |
| [tests/test_benchmark_execution_policy_v2.py](tests/test_benchmark_execution_policy_v2.py) | `ML/benchmark_execution_policy_v2.py` | ✅ | 2026-06-05 | 3KB | `45faf793` |
| [tests/test_benchmark_fav_3_vs_12_standalone.py](tests/test_benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-06-05 | 11KB | `dcdcc7a1` |
| [tests/test_benchmark_outcome_targets.py](tests/test_benchmark_outcome_targets.py) | `ML/benchmark_outcome_targets.py` | ✅ | 2026-06-05 | 4KB | `e9159813` |
| [tests/test_benchmark_quantile_early_timeout.py](tests/test_benchmark_quantile_early_timeout.py) |  |  | 2026-06-05 | 1KB | `b4775c4c` |
| [tests/test_benchmark_quantile_fav_composition.py](tests/test_benchmark_quantile_fav_composition.py) |  |  | 2026-06-05 | 6KB | `e7f68596` |
| [tests/test_benchmark_quantile_forward_validation.py](tests/test_benchmark_quantile_forward_validation.py) |  |  | 2026-06-05 | 6KB | `3dc6e7a3` |
| [tests/test_benchmark_quantile_relaxed_composition.py](tests/test_benchmark_quantile_relaxed_composition.py) |  |  | 2026-06-05 | 5KB | `c7115be5` |
| [tests/test_benchmark_system_correlation.py](tests/test_benchmark_system_correlation.py) | `ML/benchmark_system_correlation.py` | ✅ | 2026-06-05 | 10KB | `d018d30a` |
| [tests/test_benchmark_take_skip_lib_pic_selection.py](tests/test_benchmark_take_skip_lib_pic_selection.py) | `ML/benchmark_take_skip_lib_pic_selection.py` | ✅ | 2026-06-05 | 5KB | `64aaec89` |
| [tests/test_benchmark_take_skip_trailing_stop.py](tests/test_benchmark_take_skip_trailing_stop.py) |  |  | 2026-06-05 | 4KB | `be0b1bdb` |
| [tests/test_benchmark_take_skip_trailing_stop_v2.py](tests/test_benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-06-05 | 4KB | `d9fdae18` |
| [tests/test_benchmark_take_skip_trailing_stop_v2_followup.py](tests/test_benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-06-05 | 8KB | `0195683d` |
| [tests/test_benchmark_telemetry_frequency_calibration.py](tests/test_benchmark_telemetry_frequency_calibration.py) | `ML/benchmark_telemetry_frequency_calibration.py` | ✅ | 2026-06-05 | 3KB | `6e1f8e04` |
| [tests/test_benchmark_trailing_stop_target.py](tests/test_benchmark_trailing_stop_target.py) | `ML/benchmark_trailing_stop_target.py` | ✅ | 2026-06-05 | 2KB | `fb9d2a36` |
| [tests/test_benchmark_trailing_stop_target_quantile.py](tests/test_benchmark_trailing_stop_target_quantile.py) | `ML/benchmark_trailing_stop_target_quantile.py` | ✅ | 2026-06-05 | 8KB | `05ca8680` |
| [tests/test_entry_path_direct_direction_targets.py](tests/test_entry_path_direct_direction_targets.py) |  |  | 2026-06-05 | 3KB | `f28963bf` |
| [tests/test_entry_path_dual_stream_transformer.py](tests/test_entry_path_dual_stream_transformer.py) | `ML/models/entry_path_dual_stream_transformer.py` | ✅ | 2026-06-05 | 1KB | `e9c80f90` |
| [tests/test_entry_path_feature_bank.py](tests/test_entry_path_feature_bank.py) | `ML/entry_path_feature_bank.py` | ✅ | 2026-06-05 | 3KB | `8ee46497` |
| [tests/test_entry_path_labels.py](tests/test_entry_path_labels.py) | `processing/label_signals.py` — entry_path_v1 helpers | ✅ | 2026-06-05 | 7KB | `3f65cbd5` |
| [tests/test_entry_path_level_targets.py](tests/test_entry_path_level_targets.py) |  |  | 2026-06-05 | 1KB | `eb92fa8f` |
| [tests/test_entry_path_loader_seq_len.py](tests/test_entry_path_loader_seq_len.py) | `ML/data_loader.py` — `entry_path_v1` sequence length contract | ✅ | 2026-06-05 | 4KB | `e5f1a2ce` |
| [tests/test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | ✅ | 2026-06-05 | 3KB | `2975dc23` |
| [tests/test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | ✅ | 2026-06-05 | 7KB | `8c945ae2` |
| [tests/test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | ✅ | 2026-06-05 | 8KB | `c10decb9` |
| [tests/test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | ✅ | 2026-06-05 | 12KB | `8390258c` |
| [tests/test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | ✅ | 2026-06-05 | 8KB | `58560b69` |
| [tests/test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | ✅ | 2026-06-05 | 4KB | `142bfe32` |
| [tests/test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | ✅ | 2026-06-05 | 1KB | `b9a1044c` |
| [tests/test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | ✅ | 2026-06-05 | 12KB | `229fb086` |
| [tests/test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | ✅ | 2026-06-05 | 2KB | `294562f5` |
| [tests/test_entry_path_v1_quantile_training.py](tests/test_entry_path_v1_quantile_training.py) |  |  | 2026-06-05 | 9KB | `bde15a71` |
| [tests/test_exit_policy_research.py](tests/test_exit_policy_research.py) | `API/exit_policy_research.py` | ✅ | 2026-06-05 | 4KB | `4c75d18c` |
| [tests/test_export_entry_path_predictions.py](tests/test_export_entry_path_predictions.py) | `ML/export_entry_path_predictions.py` | ✅ | 2026-06-05 | 6KB | `ada7fea6` |
| [tests/test_export_entry_path_v1_quantile_rule.py](tests/test_export_entry_path_v1_quantile_rule.py) |  |  | 2026-06-05 | 3KB | `e06bdfbb` |
| [tests/test_export_entry_path_v1_quantile_signals.py](tests/test_export_entry_path_v1_quantile_signals.py) |  |  | 2026-06-05 | 7KB | `237d172f` |
| [tests/test_export_entry_path_v1_signals.py](tests/test_export_entry_path_v1_signals.py) | `API/export_entry_path_v1_signals.py` | ✅ | 2026-06-05 | 9KB | `05e49b1a` |
| [tests/test_export_take_skip_trailing_stop_v2_signals.py](tests/test_export_take_skip_trailing_stop_v2_signals.py) |  |  | 2026-06-05 | 12KB | `66fd1496` |
| [tests/test_export_take_skip_v2_predictions.py](tests/test_export_take_skip_v2_predictions.py) |  |  | 2026-06-05 | 7KB | `35d5c947` |
| [tests/test_feature_bank_comparison_diagnostics.py](tests/test_feature_bank_comparison_diagnostics.py) | `ML/feature_bank_comparison_diagnostics.py` | ✅ | 2026-06-05 | 3KB | `83c6338e` |
| [tests/test_feature_importance_diagnostics.py](tests/test_feature_importance_diagnostics.py) | `ML/feature_importance_diagnostics.py` | ✅ | 2026-06-05 | 2KB | `666e9ecb` |
| [tests/test_feature_screen_entry_path.py](tests/test_feature_screen_entry_path.py) | `ML/feature_screen_entry_path.py` | ✅ | 2026-06-05 | 567B | `b99a62db` |
| [tests/test_fractal_level_feature_builder.py](tests/test_fractal_level_feature_builder.py) |  |  | 2026-06-05 | 8KB | `dae37ed1` |
| [tests/test_generate_signals_research.py](tests/test_generate_signals_research.py) | TB signal selection в `API/generate_signals.py` | ✅ | 2026-06-05 | 831B | `6bed18cd` |
| [tests/test_inverse_piecewise.py](tests/test_inverse_piecewise.py) | `processing/normalize.py` + `statistics/signal_tracer.py` — round-trip piecewise | ✅ | 2026-06-05 | 9KB | `3cc10cfe` |
| [tests/test_label_updn.py](tests/test_label_updn.py) | `processing/label_signals.py` — parse_fractal, label_updn | ✅ | 2026-06-05 | 4KB | `691c8d7a` |
| [tests/test_lib_pic_feature_profiles.py](tests/test_lib_pic_feature_profiles.py) | `ML/lib_pic_feature_profiles.py` | ✅ | 2026-06-05 | 3KB | `025247c8` |
| [tests/test_lib_pic_geometry_feature_bank.py](tests/test_lib_pic_geometry_feature_bank.py) | `ML/lib_pic_geometry_feature_bank.py` | ✅ | 2026-06-05 | 2KB | `5d44f49d` |
| [tests/test_lib_pic_path_reaction_feature_bank.py](tests/test_lib_pic_path_reaction_feature_bank.py) | `ML/lib_pic_path_reaction_feature_bank.py` | ✅ | 2026-06-05 | 3KB | `14cd19b8` |
| [tests/test_live_safe_audit.py](tests/test_live_safe_audit.py) | `ML/live_safe_audit.py`, `ML/live_safe_audit_registry.py`, `ML/run_live_safe_ml_audit.py` | ✅ | 2026-06-05 | 5KB | `3d37ad7d` |
| [tests/test_mql_telemetry_params_csv_contract.py](tests/test_mql_telemetry_params_csv_contract.py) | MQL telemetry `#.csv` / `EXTERN_VARS()` runtime contract | ✅ | 2026-06-05 | 8KB | `f2a68e78` |
| [tests/test_multi_scale_fractal_features.py](tests/test_multi_scale_fractal_features.py) |  |  | 2026-06-05 | 1KB | `de0eeac6` |
| [tests/test_online_causal_preprocessing.py](tests/test_online_causal_preprocessing.py) | `processing/online_causal_preprocessing.py` | ✅ | 2026-06-05 | 1KB | `7d04f504` |
| [tests/test_online_tester_reconciliation.py](tests/test_online_tester_reconciliation.py) |  |  | 2026-06-05 | 7KB | `e461ccdf` |
| [tests/test_outcome_tasks.py](tests/test_outcome_tasks.py) | outcome tasks в `ML/data_loader.py` | ✅ | 2026-06-05 | 1KB | `8be56a6e` |
| [tests/test_prepare_entry_path_mt4_parity.py](tests/test_prepare_entry_path_mt4_parity.py) | `ML/prepare_entry_path_mt4_parity.py` | ✅ | 2026-06-05 | 1KB | `43e1848e` |
| [tests/test_run_entry_path_live_safe_retrain.py](tests/test_run_entry_path_live_safe_retrain.py) |  |  | 2026-06-05 | 3KB | `0ed8f0c4` |
| [tests/test_run_entry_path_quantile_live_safe_retrain.py](tests/test_run_entry_path_quantile_live_safe_retrain.py) |  |  | 2026-06-05 | 6KB | `5f3b4b02` |
| [tests/test_run_take_skip_trailing_stop_matrix.py](tests/test_run_take_skip_trailing_stop_matrix.py) |  |  | 2026-06-05 | 3KB | `7c59dae6` |
| [tests/test_run_take_skip_trailing_stop_v2_matrix.py](tests/test_run_take_skip_trailing_stop_v2_matrix.py) |  |  | 2026-06-05 | 4KB | `b715d6b8` |
| [tests/test_run_trailing_stop_target_matrix.py](tests/test_run_trailing_stop_target_matrix.py) | `ML/run_trailing_stop_target_matrix.py` | ✅ | 2026-06-05 | 8KB | `325298f6` |
| [tests/test_run_trailing_stop_target_quantile.py](tests/test_run_trailing_stop_target_quantile.py) | `ML/run_trailing_stop_target_quantile.py` | ✅ | 2026-06-05 | 4KB | `9f4fc6e6` |
| [tests/test_signal_export_parity.py](tests/test_signal_export_parity.py) | `ML/benchmark_signal_export_parity.py` | ✅ | 2026-06-05 | 3KB | `5ff4a4e3` |
| [tests/test_signal_path_atlas.py](tests/test_signal_path_atlas.py) | `API/signal_path_atlas.py` — calendar split, path tensor, archetypes, CLI | ✅ | 2026-06-05 | 38KB | `a3364aec` |
| [tests/test_signal_quality_research.py](tests/test_signal_quality_research.py) | `API/signal_quality_research.py` — filter features, variance check, tree, holdout | ✅ | 2026-06-05 | 12KB | `51ebae32` |
| [tests/test_signal_research.py](tests/test_signal_research.py) | `API/signal_research.py` — ATR14, excursions, barriers, split | ✅ | 2026-06-05 | 41KB | `4b5920a6` |
| [tests/test_signal_tracer_tb.py](tests/test_signal_tracer_tb.py) | TB-specific parsing в `statistics/signal_tracer.py` | ✅ | 2026-06-05 | 2KB | `b2c52f5f` |
| [tests/test_take_skip_lib_pic_feature_matrix.py](tests/test_take_skip_lib_pic_feature_matrix.py) | `ML/run_take_skip_lib_pic_feature_matrix.py` и `ML/models/take_skip_dual_stream_transformer.py` | ✅ | 2026-06-05 | 6KB | `df9c696d` |
| [tests/test_take_skip_original_contour_feature_matrix.py](tests/test_take_skip_original_contour_feature_matrix.py) | `ML/run_take_skip_original_contour_feature_matrix.py` | ✅ | 2026-06-05 | 9KB | `88acdeac` |
| [tests/test_take_skip_trailing_stop_task.py](tests/test_take_skip_trailing_stop_task.py) |  |  | 2026-06-05 | 7KB | `f917ec48` |
| [tests/test_take_skip_trailing_stop_v2_task.py](tests/test_take_skip_trailing_stop_v2_task.py) |  |  | 2026-06-05 | 8KB | `5d31b732` |
| [tests/test_tb_label_invariants.py](tests/test_tb_label_invariants.py) |  |  | 2026-06-05 | 1KB | `46510bd4` |
| [tests/test_telemetry_daily_reconciliation.py](tests/test_telemetry_daily_reconciliation.py) | `ML/telemetry_daily_reconciliation.py` | ✅ | 2026-06-05 | 8KB | `7fd9bb8d` |
| [tests/test_telemetry_signal_watcher.py](tests/test_telemetry_signal_watcher.py) | `API/telemetry_signal_watcher.py` | ✅ | 2026-06-05 | 24KB | `759d5060` |
| [tests/test_track_a_max_out_matrix.py](tests/test_track_a_max_out_matrix.py) | `ML/run_track_a_max_out_matrix.py` | ✅ | 2026-06-05 | 706B | `da3502cc` |
| [tests/test_trade_target_labels.py](tests/test_trade_target_labels.py) | `processing/label_signals.py` — trade target labels | ✅ | 2026-06-05 | 2KB | `01005f96` |
| [tests/test_trailing_stop_target_labels.py](tests/test_trailing_stop_target_labels.py) | `processing/label_signals.py` — trailing-stop target labels | ✅ | 2026-06-05 | 5KB | `102ae22d` |
| [tests/test_trailing_stop_target_quantile_model.py](tests/test_trailing_stop_target_quantile_model.py) | `ML/models/trailing_stop_target_quantile_transformer.py` | ✅ | 2026-06-05 | 542B | `692f8730` |
| [tests/test_trailing_stop_target_quantile_task.py](tests/test_trailing_stop_target_quantile_task.py) | `ML/trailing_stop_target_quantile_task.py` и train/evaluate/export wiring | ✅ | 2026-06-05 | 17KB | `329c7acb` |
| [tests/test_trailing_stop_target_task.py](tests/test_trailing_stop_target_task.py) | `ML/trailing_stop_target_task.py` и trailing-stop export/evaluate wiring | ✅ | 2026-06-05 | 14KB | `ea6330c4` |
| [tests/test_triple_barrier_calibration.py](tests/test_triple_barrier_calibration.py) | EV/calibration helper для Triple Barrier | ✅ | 2026-06-05 | 745B | `b5e20abc` |
| [tests/test_triple_barrier_first_touch.py](tests/test_triple_barrier_first_touch.py) | first-touch helper для Triple Barrier разметки | ✅ | 2026-06-05 | 1KB | `58f2ba93` |
| [tests/test_triple_barrier_mt4_execution.py](tests/test_triple_barrier_mt4_execution.py) |  |  | 2026-06-05 | 4KB | `a5e04561` |
| [tests/test_triple_barrier_training.py](tests/test_triple_barrier_training.py) | transfer-learning kwargs для TB обучения | ✅ | 2026-06-05 | 1KB | `d46e3e22` |

## MQL

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [MT/.vscode/settings.json](MT/.vscode/settings.json) |  |  | 2026-05-30 | 928B | `d6834b74` |
| [MT/MQL4/.vscode/settings.json](MT/MQL4/.vscode/settings.json) |  |  | 2026-05-30 | 927B | `c3c0af89` |
| [MT/MQL4/Experts/$o$imple.mq4](MT/MQL4/Experts/$o$imple.mq4) |  |  | 2026-05-30 | 12KB | `02964edd` |
| [MT/MQL4/Include/Arrays/Array.mqh](MT/MQL4/Include/Arrays/Array.mqh) |  |  | 2026-05-27 | 6KB | `29d804ca` |
| [MT/MQL4/Include/Arrays/ArrayChar.mqh](MT/MQL4/Include/Arrays/ArrayChar.mqh) |  |  | 2026-05-27 | 23KB | `3df8fe54` |
| [MT/MQL4/Include/Arrays/ArrayDouble.mqh](MT/MQL4/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-05-27 | 24KB | `c44a2bc3` |
| [MT/MQL4/Include/Arrays/ArrayFloat.mqh](MT/MQL4/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-05-27 | 24KB | `92fa9ff2` |
| [MT/MQL4/Include/Arrays/ArrayInt.mqh](MT/MQL4/Include/Arrays/ArrayInt.mqh) |  |  | 2026-05-27 | 23KB | `ebbf910b` |
| [MT/MQL4/Include/Arrays/ArrayLong.mqh](MT/MQL4/Include/Arrays/ArrayLong.mqh) |  |  | 2026-05-27 | 23KB | `6ff220ef` |
| [MT/MQL4/Include/Arrays/ArrayObj.mqh](MT/MQL4/Include/Arrays/ArrayObj.mqh) |  |  | 2026-05-27 | 24KB | `d0b3a268` |
| [MT/MQL4/Include/Arrays/ArrayShort.mqh](MT/MQL4/Include/Arrays/ArrayShort.mqh) |  |  | 2026-05-27 | 24KB | `60d79bb6` |
| [MT/MQL4/Include/Arrays/ArrayString.mqh](MT/MQL4/Include/Arrays/ArrayString.mqh) |  |  | 2026-05-27 | 24KB | `83273ae5` |
| [MT/MQL4/Include/Arrays/List.mqh](MT/MQL4/Include/Arrays/List.mqh) |  |  | 2026-05-27 | 20KB | `63551a44` |
| [MT/MQL4/Include/Arrays/Tree.mqh](MT/MQL4/Include/Arrays/Tree.mqh) |  |  | 2026-05-27 | 13KB | `6f58f568` |
| [MT/MQL4/Include/Arrays/TreeNode.mqh](MT/MQL4/Include/Arrays/TreeNode.mqh) |  |  | 2026-05-27 | 6KB | `4c496c31` |
| [MT/MQL4/Include/COUNT.mqh](MT/MQL4/Include/COUNT.mqh) |  |  | 2026-05-30 | 8KB | `2ec8513b` |
| [MT/MQL4/Include/Canvas/Canvas.mqh](MT/MQL4/Include/Canvas/Canvas.mqh) |  |  | 2026-05-27 | 82KB | `35bff7bb` |
| [MT/MQL4/Include/ChartObjects/ChartObject.mqh](MT/MQL4/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-05-27 | 41KB | `1fe4ca68` |
| [MT/MQL4/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL4/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-05-27 | 7KB | `185cc1c1` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-05-27 | 23KB | `1bdc4250` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-05-27 | 20KB | `cd93d9d3` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-05-27 | 11KB | `681634d9` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-05-27 | 17KB | `9a593088` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-05-27 | 16KB | `f7a2a428` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-05-27 | 15KB | `870b6a4c` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-05-27 | 7KB | `ed4de27c` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-05-27 | 36KB | `e2dac30a` |
| [MT/MQL4/Include/Charts/Chart.mqh](MT/MQL4/Include/Charts/Chart.mqh) |  |  | 2026-05-27 | 62KB | `1a0d0ee5` |
| [MT/MQL4/Include/Controls/BmpButton.mqh](MT/MQL4/Include/Controls/BmpButton.mqh) |  |  | 2026-05-27 | 11KB | `e6636dc2` |
| [MT/MQL4/Include/Controls/Button.mqh](MT/MQL4/Include/Controls/Button.mqh) |  |  | 2026-05-27 | 6KB | `b420f9ff` |
| [MT/MQL4/Include/Controls/CheckBox.mqh](MT/MQL4/Include/Controls/CheckBox.mqh) |  |  | 2026-05-27 | 7KB | `5c78edfa` |
| [MT/MQL4/Include/Controls/CheckGroup.mqh](MT/MQL4/Include/Controls/CheckGroup.mqh) |  |  | 2026-05-27 | 13KB | `396afe09` |
| [MT/MQL4/Include/Controls/ComboBox.mqh](MT/MQL4/Include/Controls/ComboBox.mqh) |  |  | 2026-05-27 | 13KB | `6eddc276` |
| [MT/MQL4/Include/Controls/DateDropList.mqh](MT/MQL4/Include/Controls/DateDropList.mqh) |  |  | 2026-05-27 | 14KB | `64f7cc0b` |
| [MT/MQL4/Include/Controls/DatePicker.mqh](MT/MQL4/Include/Controls/DatePicker.mqh) |  |  | 2026-05-27 | 10KB | `e4fb2dba` |
| [MT/MQL4/Include/Controls/Defines.mqh](MT/MQL4/Include/Controls/Defines.mqh) |  |  | 2026-05-27 | 12KB | `24dff7f9` |
| [MT/MQL4/Include/Controls/Dialog.mqh](MT/MQL4/Include/Controls/Dialog.mqh) |  |  | 2026-05-27 | 37KB | `08542849` |
| [MT/MQL4/Include/Controls/Edit.mqh](MT/MQL4/Include/Controls/Edit.mqh) |  |  | 2026-05-27 | 8KB | `55d19722` |
| [MT/MQL4/Include/Controls/Label.mqh](MT/MQL4/Include/Controls/Label.mqh) |  |  | 2026-05-27 | 4KB | `69bc9423` |
| [MT/MQL4/Include/Controls/ListView.mqh](MT/MQL4/Include/Controls/ListView.mqh) |  |  | 2026-05-27 | 19KB | `cf4da8db` |
| [MT/MQL4/Include/Controls/Panel.mqh](MT/MQL4/Include/Controls/Panel.mqh) |  |  | 2026-05-27 | 5KB | `c3e6d302` |
| [MT/MQL4/Include/Controls/Picture.mqh](MT/MQL4/Include/Controls/Picture.mqh) |  |  | 2026-05-27 | 5KB | `12aeafe8` |
| [MT/MQL4/Include/Controls/RadioButton.mqh](MT/MQL4/Include/Controls/RadioButton.mqh) |  |  | 2026-05-27 | 6KB | `1f730fd0` |
| [MT/MQL4/Include/Controls/RadioGroup.mqh](MT/MQL4/Include/Controls/RadioGroup.mqh) |  |  | 2026-05-27 | 13KB | `ac89d216` |
| [MT/MQL4/Include/Controls/Rect.mqh](MT/MQL4/Include/Controls/Rect.mqh) |  |  | 2026-05-27 | 10KB | `e3b2d600` |
| [MT/MQL4/Include/Controls/Scrolls.mqh](MT/MQL4/Include/Controls/Scrolls.mqh) |  |  | 2026-05-27 | 26KB | `98c3c8a8` |
| [MT/MQL4/Include/Controls/SpinEdit.mqh](MT/MQL4/Include/Controls/SpinEdit.mqh) |  |  | 2026-05-27 | 10KB | `40a03d96` |
| [MT/MQL4/Include/Controls/TimePicker.mqh](MT/MQL4/Include/Controls/TimePicker.mqh) |  |  | 2026-05-27 | 14KB | `9ae8f057` |
| [MT/MQL4/Include/Controls/Wnd.mqh](MT/MQL4/Include/Controls/Wnd.mqh) |  |  | 2026-05-27 | 29KB | `55cbb430` |
| [MT/MQL4/Include/Controls/WndClient.mqh](MT/MQL4/Include/Controls/WndClient.mqh) |  |  | 2026-05-27 | 12KB | `560fb482` |
| [MT/MQL4/Include/Controls/WndContainer.mqh](MT/MQL4/Include/Controls/WndContainer.mqh) |  |  | 2026-05-27 | 15KB | `8827a68b` |
| [MT/MQL4/Include/Controls/WndObj.mqh](MT/MQL4/Include/Controls/WndObj.mqh) |  |  | 2026-05-27 | 10KB | `32def100` |
| [MT/MQL4/Include/ERRORs.mqh](MT/MQL4/Include/ERRORs.mqh) |  |  | 2026-05-30 | 20KB | `09c555ab` |
| [MT/MQL4/Include/FUNCTIONS.mqh](MT/MQL4/Include/FUNCTIONS.mqh) |  |  | 2026-05-30 | 18KB | `038b6541` |
| [MT/MQL4/Include/Files/File.mqh](MT/MQL4/Include/Files/File.mqh) |  |  | 2026-05-27 | 11KB | `d679fd98` |
| [MT/MQL4/Include/Files/FileBin.mqh](MT/MQL4/Include/Files/FileBin.mqh) |  |  | 2026-05-27 | 20KB | `7d828698` |
| [MT/MQL4/Include/Files/FilePipe.mqh](MT/MQL4/Include/Files/FilePipe.mqh) |  |  | 2026-05-27 | 12KB | `0272c296` |
| [MT/MQL4/Include/Files/FileTxt.mqh](MT/MQL4/Include/Files/FileTxt.mqh) |  |  | 2026-05-27 | 2KB | `e92ef484` |
| [MT/MQL4/Include/INPUT.mqh](MT/MQL4/Include/INPUT.mqh) |  |  | 2026-05-30 | 22KB | `27ad874f` |
| [MT/MQL4/Include/Indicators/BillWilliams.mqh](MT/MQL4/Include/Indicators/BillWilliams.mqh) |  |  | 2026-05-27 | 29KB | `c27ca4b9` |
| [MT/MQL4/Include/Indicators/Custom.mqh](MT/MQL4/Include/Indicators/Custom.mqh) |  |  | 2026-05-27 | 5KB | `97e02c64` |
| [MT/MQL4/Include/Indicators/Indicator.mqh](MT/MQL4/Include/Indicators/Indicator.mqh) |  |  | 2026-05-27 | 6KB | `76365508` |
| [MT/MQL4/Include/Indicators/Indicators.mqh](MT/MQL4/Include/Indicators/Indicators.mqh) |  |  | 2026-05-27 | 11KB | `7e280f54` |
| [MT/MQL4/Include/Indicators/Oscilators.mqh](MT/MQL4/Include/Indicators/Oscilators.mqh) |  |  | 2026-05-27 | 55KB | `64f2642f` |
| [MT/MQL4/Include/Indicators/Series.mqh](MT/MQL4/Include/Indicators/Series.mqh) |  |  | 2026-05-27 | 5KB | `f97ef82c` |
| [MT/MQL4/Include/Indicators/TimeSeries.mqh](MT/MQL4/Include/Indicators/TimeSeries.mqh) |  |  | 2026-05-27 | 19KB | `9d9048a3` |
| [MT/MQL4/Include/Indicators/Trend.mqh](MT/MQL4/Include/Indicators/Trend.mqh) |  |  | 2026-05-27 | 35KB | `81111941` |
| [MT/MQL4/Include/Indicators/Volumes.mqh](MT/MQL4/Include/Indicators/Volumes.mqh) |  |  | 2026-05-27 | 11KB | `dd2a52e4` |
| [MT/MQL4/Include/MAIN.mqh](MT/MQL4/Include/MAIN.mqh) |  |  | 2026-05-30 | 10KB | `37231467` |
| [MT/MQL4/Include/MM.mqh](MT/MQL4/Include/MM.mqh) |  |  | 2026-05-30 | 10KB | `c7d3005a` |
| [MT/MQL4/Include/MovingAverages.mqh](MT/MQL4/Include/MovingAverages.mqh) |  |  | 2026-05-27 | 8KB | `d87e9a1b` |
| [MT/MQL4/Include/ORDERS.mqh](MT/MQL4/Include/ORDERS.mqh) |  |  | 2026-05-30 | 40KB | `fbab4671` |
| [MT/MQL4/Include/OUTPUT.mqh](MT/MQL4/Include/OUTPUT.mqh) |  |  | 2026-05-30 | 19KB | `7ff1d32e` |
| [MT/MQL4/Include/Object.mqh](MT/MQL4/Include/Object.mqh) |  |  | 2026-05-27 | 1KB | `6519631b` |
| [MT/MQL4/Include/SERVICE.mqh](MT/MQL4/Include/SERVICE.mqh) |  |  | 2026-05-30 | 81KB | `67e9cd04` |
| [MT/MQL4/Include/StdLibErr.mqh](MT/MQL4/Include/StdLibErr.mqh) |  |  | 2026-05-30 | 683B | `987aa510` |
| [MT/MQL4/Include/Strings/String.mqh](MT/MQL4/Include/Strings/String.mqh) |  |  | 2026-05-27 | 13KB | `a2a8f645` |
| [MT/MQL4/Include/Tools/DateTime.mqh](MT/MQL4/Include/Tools/DateTime.mqh) |  |  | 2026-05-27 | 17KB | `f1732e44` |
| [MT/MQL4/Include/WinUser32.mqh](MT/MQL4/Include/WinUser32.mqh) |  |  | 2026-05-30 | 17KB | `c4be55b2` |
| [MT/MQL4/Include/head_PIC.mqh](MT/MQL4/Include/head_PIC.mqh) |  |  | 2026-05-30 | 9KB | `b5a78736` |
| [MT/MQL4/Include/iGRAPH.mqh](MT/MQL4/Include/iGRAPH.mqh) |  |  | 2026-05-30 | 38KB | `73d71482` |
| [MT/MQL4/Include/lib_ATR.mqh](MT/MQL4/Include/lib_ATR.mqh) |  |  | 2026-05-30 | 2KB | `e8fa3ca7` |
| [MT/MQL4/Include/lib_Flat.mqh](MT/MQL4/Include/lib_Flat.mqh) |  |  | 2026-05-30 | 13KB | `bc1a865b` |
| [MT/MQL4/Include/lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, single/multi-position telemetry trading | ✅ | 2026-05-30 | 43KB | `961e7c47` |
| [MT/MQL4/Include/lib_ML_Signal_TB.mqh](MT/MQL4/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-05-30 | 8KB | `86f9658b` |
| [MT/MQL4/Include/lib_ML_Signal_back.mqh](MT/MQL4/Include/lib_ML_Signal_back.mqh) |  |  | 2026-05-30 | 14KB | `996e3367` |
| [MT/MQL4/Include/lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | ⚠️ | 2026-06-03 | 57KB | `75237554` |
| [MT/MQL4/Include/stderror.mqh](MT/MQL4/Include/stderror.mqh) |  |  | 2026-05-30 | 9KB | `aec87c86` |
| [MT/MQL4/Include/stdlib.mqh](MT/MQL4/Include/stdlib.mqh) |  |  | 2026-05-30 | 662B | `268bec52` |
| [MT/MQL4/Indicators/ATR.mq4](MT/MQL4/Indicators/ATR.mq4) |  |  | 2026-05-30 | 3KB | `dd312b03` |
| [MT/MQL4/Indicators/ATR_original.mq4](MT/MQL4/Indicators/ATR_original.mq4) |  |  | 2026-05-30 | 3KB | `efe79c20` |
| [MT/MQL4/Indicators/Accelerator.mq4](MT/MQL4/Indicators/Accelerator.mq4) |  |  | 2026-05-27 | 3KB | `245c5aa7` |
| [MT/MQL4/Indicators/Accumulation.mq4](MT/MQL4/Indicators/Accumulation.mq4) |  |  | 2026-05-27 | 2KB | `a0c2fbe4` |
| [MT/MQL4/Indicators/Alligator.mq4](MT/MQL4/Indicators/Alligator.mq4) |  |  | 2026-05-27 | 3KB | `82fea67e` |
| [MT/MQL4/Indicators/Awesome.mq4](MT/MQL4/Indicators/Awesome.mq4) |  |  | 2026-05-27 | 3KB | `0e492ca3` |
| [MT/MQL4/Indicators/Bands.mq4](MT/MQL4/Indicators/Bands.mq4) |  |  | 2026-05-27 | 4KB | `894a6a9f` |
| [MT/MQL4/Indicators/Bears.mq4](MT/MQL4/Indicators/Bears.mq4) |  |  | 2026-05-27 | 2KB | `549f60ef` |
| [MT/MQL4/Indicators/Bulls.mq4](MT/MQL4/Indicators/Bulls.mq4) |  |  | 2026-05-27 | 2KB | `80e8e544` |
| [MT/MQL4/Indicators/CCI.mq4](MT/MQL4/Indicators/CCI.mq4) |  |  | 2026-05-27 | 4KB | `613fa2e1` |
| [MT/MQL4/Indicators/Custom Moving Averages.mq4](MT/MQL4/Indicators/Custom Moving Averages.mq4) |  |  | 2026-05-27 | 6KB | `1aa756f5` |
| [MT/MQL4/Indicators/Examples/SimplePanel/PanelDialog.mqh](MT/MQL4/Indicators/Examples/SimplePanel/PanelDialog.mqh) |  |  | 2026-05-27 | 15KB | `9a2575df` |
| [MT/MQL4/Indicators/Examples/SimplePanel/SimplePanel.mq4](MT/MQL4/Indicators/Examples/SimplePanel/SimplePanel.mq4) |  |  | 2026-05-27 | 2KB | `98b689e0` |
| [MT/MQL4/Indicators/Heiken Ashi.mq4](MT/MQL4/Indicators/Heiken Ashi.mq4) |  |  | 2026-05-27 | 4KB | `dc166238` |
| [MT/MQL4/Indicators/Ichimoku.mq4](MT/MQL4/Indicators/Ichimoku.mq4) |  |  | 2026-05-27 | 6KB | `cd834b55` |
| [MT/MQL4/Indicators/MACD.mq4](MT/MQL4/Indicators/MACD.mq4) |  |  | 2026-05-27 | 3KB | `11b86bdc` |
| [MT/MQL4/Indicators/Momentum.mq4](MT/MQL4/Indicators/Momentum.mq4) |  |  | 2026-05-27 | 2KB | `4e49723b` |
| [MT/MQL4/Indicators/OsMA.mq4](MT/MQL4/Indicators/OsMA.mq4) |  |  | 2026-05-27 | 3KB | `a4980656` |
| [MT/MQL4/Indicators/Parabolic.mq4](MT/MQL4/Indicators/Parabolic.mq4) |  |  | 2026-05-27 | 7KB | `432cb924` |
| [MT/MQL4/Indicators/RSI.mq4](MT/MQL4/Indicators/RSI.mq4) |  |  | 2026-05-27 | 4KB | `c3187582` |
| [MT/MQL4/Indicators/Stochastic.mq4](MT/MQL4/Indicators/Stochastic.mq4) |  |  | 2026-05-27 | 5KB | `0ecf23fb` |
| [MT/MQL4/Indicators/ZigZag.mq4](MT/MQL4/Indicators/ZigZag.mq4) |  |  | 2026-05-27 | 8KB | `511620e8` |
| [MT/MQL4/Indicators/iATR.mq4](MT/MQL4/Indicators/iATR.mq4) |  |  | 2026-05-30 | 3KB | `2053ea50` |
| [MT/MQL4/Indicators/iATRcycle.mq4](MT/MQL4/Indicators/iATRcycle.mq4) |  |  | 2026-05-30 | 2KB | `3a5033e7` |
| [MT/MQL4/Indicators/iExposure.mq4](MT/MQL4/Indicators/iExposure.mq4) |  |  | 2026-05-27 | 8KB | `7d98a88b` |
| [MT/MQL4/Indicators/iPIC.mq4](MT/MQL4/Indicators/iPIC.mq4) |  |  | 2026-05-30 | 13KB | `802c9a21` |
| [MT/MQL4/Indicators/iPOC.mq4](MT/MQL4/Indicators/iPOC.mq4) |  |  | 2026-05-30 | 7KB | `4b4df898` |
| [MT/MQL4/Indicators/iVolumeCluster.mq4](MT/MQL4/Indicators/iVolumeCluster.mq4) |  |  | 2026-05-30 | 44KB | `db9c3442` |
| [MT/MQL4/Libraries/StdLibErr.mqh](MT/MQL4/Libraries/StdLibErr.mqh) |  |  | 2026-05-30 | 673B | `01044c60` |
| [MT/MQL4/Libraries/WinUser32.mqh](MT/MQL4/Libraries/WinUser32.mqh) |  |  | 2026-05-30 | 17KB | `84f99057` |
| [MT/MQL4/Libraries/stderror.mqh](MT/MQL4/Libraries/stderror.mqh) |  |  | 2026-05-30 | 9KB | `47505e6c` |
| [MT/MQL4/Libraries/stdlib.mq4](MT/MQL4/Libraries/stdlib.mq4) |  |  | 2026-05-30 | 19KB | `cdb0a440` |
| [MT/MQL4/Libraries/stdlib.mqh](MT/MQL4/Libraries/stdlib.mqh) |  |  | 2026-05-30 | 648B | `5695494a` |
| [MT/MQL4/README.md](MT/MQL4/README.md) |  |  | 2026-05-30 | 728B | `88e64c48` |
| [MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4](MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4) |  |  | 2026-05-30 | 2KB | `7d447b15` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4) |  |  | 2026-05-30 | 3KB | `d0dbff33` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4) |  |  | 2026-05-30 | 4KB | `c0c67ebe` |
| [MT/MQL4/Scripts/ExportOHLC.mq4](MT/MQL4/Scripts/ExportOHLC.mq4) |  |  | 2026-05-30 | 2KB | `134c533f` |
| [MT/MQL4/Scripts/HistoryConvertor1002.mq4](MT/MQL4/Scripts/HistoryConvertor1002.mq4) |  |  | 2026-05-30 | 4KB | `2a904122` |
| [MT/MQL4/Scripts/MATLABLOG.mq4](MT/MQL4/Scripts/MATLABLOG.mq4) |  |  | 2026-05-30 | 10KB | `01bef2dd` |
| [MT/MQL4/Scripts/PeriodConverter.mq4](MT/MQL4/Scripts/PeriodConverter.mq4) |  |  | 2026-05-30 | 6KB | `b5a97900` |
| [MT/MQL4/Scripts/trade.mq4](MT/MQL4/Scripts/trade.mq4) |  |  | 2026-05-30 | 1KB | `7c2e252f` |
| [MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh](MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh) |  |  | 2026-05-30 | 3KB | `98d2d8a4` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh) |  |  | 2026-05-30 | 2KB | `ec173678` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh) |  |  | 2026-05-30 | 9KB | `3d047cfe` |
| [MT/MQL4/Trash/iSIG_TURTLE.mqh](MT/MQL4/Trash/iSIG_TURTLE.mqh) |  |  | 2026-05-30 | 3KB | `1b311295` |
| [MT/MQL4/Trash/lib_PIC_old.mqh](MT/MQL4/Trash/lib_PIC_old.mqh) |  |  | 2026-05-30 | 43KB | `59b6536b` |
| [MT/MQL4/Trash/lib_POC.mqh](MT/MQL4/Trash/lib_POC.mqh) |  |  | 2026-05-30 | 7KB | `130bc358` |
| [MT/MQL4/Trash/lib_REZENKO.mqh](MT/MQL4/Trash/lib_REZENKO.mqh) |  |  | 2026-05-30 | 8KB | `8128da38` |
| [MT/MQL4/Trash/lib_TRG.mqh](MT/MQL4/Trash/lib_TRG.mqh) |  |  | 2026-05-30 | 3KB | `e676d2c4` |
| [MT/MQL4/Trash/lib_Triangle.mqh](MT/MQL4/Trash/lib_Triangle.mqh) |  |  | 2026-05-30 | 9KB | `12350503` |
| [MT/MQL4/Trash/lib_ssss.mqh](MT/MQL4/Trash/lib_ssss.mqh) |  |  | 2026-05-30 | 3KB | `6c2e9b73` |
| [MT/MQL5/Include/Arrays/Array.mqh](MT/MQL5/Include/Arrays/Array.mqh) |  |  | 2026-05-30 | 6KB | `dcaa074e` |
| [MT/MQL5/Include/Arrays/ArrayChar.mqh](MT/MQL5/Include/Arrays/ArrayChar.mqh) |  |  | 2026-05-30 | 24KB | `54edbdc1` |
| [MT/MQL5/Include/Arrays/ArrayColor.mqh](MT/MQL5/Include/Arrays/ArrayColor.mqh) |  |  | 2026-05-30 | 24KB | `5de5acca` |
| [MT/MQL5/Include/Arrays/ArrayDatetime.mqh](MT/MQL5/Include/Arrays/ArrayDatetime.mqh) |  |  | 2026-05-30 | 24KB | `28aca33a` |
| [MT/MQL5/Include/Arrays/ArrayDouble.mqh](MT/MQL5/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-05-30 | 24KB | `b442d2c3` |
| [MT/MQL5/Include/Arrays/ArrayFloat.mqh](MT/MQL5/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-05-30 | 24KB | `58db64bf` |
| [MT/MQL5/Include/Arrays/ArrayInt.mqh](MT/MQL5/Include/Arrays/ArrayInt.mqh) |  |  | 2026-05-30 | 24KB | `60c3a599` |
| [MT/MQL5/Include/Arrays/ArrayLong.mqh](MT/MQL5/Include/Arrays/ArrayLong.mqh) |  |  | 2026-05-30 | 24KB | `93c0a2e1` |
| [MT/MQL5/Include/Arrays/ArrayObj.mqh](MT/MQL5/Include/Arrays/ArrayObj.mqh) |  |  | 2026-05-30 | 24KB | `1b604f04` |
| [MT/MQL5/Include/Arrays/ArrayShort.mqh](MT/MQL5/Include/Arrays/ArrayShort.mqh) |  |  | 2026-05-30 | 24KB | `588fba4c` |
| [MT/MQL5/Include/Arrays/ArrayString.mqh](MT/MQL5/Include/Arrays/ArrayString.mqh) |  |  | 2026-05-30 | 24KB | `d7e92876` |
| [MT/MQL5/Include/Arrays/ArrayUChar.mqh](MT/MQL5/Include/Arrays/ArrayUChar.mqh) |  |  | 2026-05-30 | 24KB | `b7d6f43f` |
| [MT/MQL5/Include/Arrays/ArrayUInt.mqh](MT/MQL5/Include/Arrays/ArrayUInt.mqh) |  |  | 2026-05-30 | 24KB | `e6097a29` |
| [MT/MQL5/Include/Arrays/ArrayULong.mqh](MT/MQL5/Include/Arrays/ArrayULong.mqh) |  |  | 2026-05-30 | 24KB | `6c18b082` |
| [MT/MQL5/Include/Arrays/ArrayUShort.mqh](MT/MQL5/Include/Arrays/ArrayUShort.mqh) |  |  | 2026-05-30 | 24KB | `92db202e` |
| [MT/MQL5/Include/Arrays/List.mqh](MT/MQL5/Include/Arrays/List.mqh) |  |  | 2026-05-30 | 20KB | `a173f72b` |
| [MT/MQL5/Include/Arrays/Tree.mqh](MT/MQL5/Include/Arrays/Tree.mqh) |  |  | 2026-05-30 | 13KB | `8824d2cf` |
| [MT/MQL5/Include/Arrays/TreeNode.mqh](MT/MQL5/Include/Arrays/TreeNode.mqh) |  |  | 2026-05-30 | 6KB | `efde8191` |
| [MT/MQL5/Include/COUNT.mqh](MT/MQL5/Include/COUNT.mqh) |  |  | 2026-05-30 | 8KB | `93b61a0a` |
| [MT/MQL5/Include/Canvas/Canvas.mqh](MT/MQL5/Include/Canvas/Canvas.mqh) |  |  | 2026-05-30 | 152KB | `4abe8ef4` |
| [MT/MQL5/Include/Canvas/Canvas3D.mqh](MT/MQL5/Include/Canvas/Canvas3D.mqh) |  |  | 2026-05-30 | 33KB | `f75c5970` |
| [MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh](MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh) |  |  | 2026-05-30 | 35KB | `018e7b5b` |
| [MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh](MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh) |  |  | 2026-05-30 | 11KB | `89f96b38` |
| [MT/MQL5/Include/Canvas/Charts/LineChart.mqh](MT/MQL5/Include/Canvas/Charts/LineChart.mqh) |  |  | 2026-05-30 | 12KB | `ac171461` |
| [MT/MQL5/Include/Canvas/Charts/PieChart.mqh](MT/MQL5/Include/Canvas/Charts/PieChart.mqh) |  |  | 2026-05-30 | 13KB | `81e44597` |
| [MT/MQL5/Include/Canvas/DX/DXBox.mqh](MT/MQL5/Include/Canvas/DX/DXBox.mqh) |  |  | 2026-05-30 | 3KB | `e9cbd560` |
| [MT/MQL5/Include/Canvas/DX/DXBuffers.mqh](MT/MQL5/Include/Canvas/DX/DXBuffers.mqh) |  |  | 2026-05-30 | 4KB | `da4319c8` |
| [MT/MQL5/Include/Canvas/DX/DXData.mqh](MT/MQL5/Include/Canvas/DX/DXData.mqh) |  |  | 2026-05-30 | 3KB | `4a5f2988` |
| [MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh](MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh) |  |  | 2026-05-30 | 12KB | `ce240376` |
| [MT/MQL5/Include/Canvas/DX/DXHandle.mqh](MT/MQL5/Include/Canvas/DX/DXHandle.mqh) |  |  | 2026-05-30 | 8KB | `7a799c15` |
| [MT/MQL5/Include/Canvas/DX/DXInput.mqh](MT/MQL5/Include/Canvas/DX/DXInput.mqh) |  |  | 2026-05-30 | 4KB | `2c890e23` |
| [MT/MQL5/Include/Canvas/DX/DXMath.mqh](MT/MQL5/Include/Canvas/DX/DXMath.mqh) |  |  | 2026-05-30 | 151KB | `cbff51f5` |
| [MT/MQL5/Include/Canvas/DX/DXMesh.mqh](MT/MQL5/Include/Canvas/DX/DXMesh.mqh) |  |  | 2026-05-30 | 15KB | `5bb993cf` |
| [MT/MQL5/Include/Canvas/DX/DXObject.mqh](MT/MQL5/Include/Canvas/DX/DXObject.mqh) |  |  | 2026-05-30 | 1KB | `605a2574` |
| [MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh](MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh) |  |  | 2026-05-30 | 2KB | `262b9064` |
| [MT/MQL5/Include/Canvas/DX/DXShader.mqh](MT/MQL5/Include/Canvas/DX/DXShader.mqh) |  |  | 2026-05-30 | 16KB | `fbeceb80` |
| [MT/MQL5/Include/Canvas/DX/DXSurface.mqh](MT/MQL5/Include/Canvas/DX/DXSurface.mqh) |  |  | 2026-05-30 | 6KB | `75cfc660` |
| [MT/MQL5/Include/Canvas/DX/DXTexture.mqh](MT/MQL5/Include/Canvas/DX/DXTexture.mqh) |  |  | 2026-05-30 | 6KB | `1a3377f2` |
| [MT/MQL5/Include/Canvas/DX/DXUtils.mqh](MT/MQL5/Include/Canvas/DX/DXUtils.mqh) |  |  | 2026-05-30 | 35KB | `81b0d9c9` |
| [MT/MQL5/Include/Canvas/FlameCanvas.mqh](MT/MQL5/Include/Canvas/FlameCanvas.mqh) |  |  | 2026-05-30 | 26KB | `8a0d3427` |
| [MT/MQL5/Include/ChartObjects/ChartObject.mqh](MT/MQL5/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-05-30 | 40KB | `f13eb438` |
| [MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-05-30 | 8KB | `7479429b` |
| [MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh](MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh) |  |  | 2026-05-30 | 16KB | `0d77ef95` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-05-30 | 23KB | `9c0cbe08` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-05-30 | 20KB | `26885f86` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-05-30 | 11KB | `11590972` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh) |  |  | 2026-05-30 | 9KB | `c0255f7d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-05-30 | 17KB | `6ae0eb18` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-05-30 | 16KB | `f4d66975` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-05-30 | 15KB | `7888e00d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-05-30 | 7KB | `d6d59613` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-05-30 | 37KB | `64387446` |
| [MT/MQL5/Include/Charts/Chart.mqh](MT/MQL5/Include/Charts/Chart.mqh) |  |  | 2026-05-30 | 62KB | `c5d96344` |
| [MT/MQL5/Include/Controls/BmpButton.mqh](MT/MQL5/Include/Controls/BmpButton.mqh) |  |  | 2026-05-30 | 11KB | `91c016b1` |
| [MT/MQL5/Include/Controls/Button.mqh](MT/MQL5/Include/Controls/Button.mqh) |  |  | 2026-05-30 | 6KB | `39ba2260` |
| [MT/MQL5/Include/Controls/CheckBox.mqh](MT/MQL5/Include/Controls/CheckBox.mqh) |  |  | 2026-05-30 | 7KB | `cd5744e7` |
| [MT/MQL5/Include/Controls/CheckGroup.mqh](MT/MQL5/Include/Controls/CheckGroup.mqh) |  |  | 2026-05-30 | 13KB | `3f03b33e` |
| [MT/MQL5/Include/Controls/ComboBox.mqh](MT/MQL5/Include/Controls/ComboBox.mqh) |  |  | 2026-05-30 | 13KB | `df4bb90f` |
| [MT/MQL5/Include/Controls/DateDropList.mqh](MT/MQL5/Include/Controls/DateDropList.mqh) |  |  | 2026-05-30 | 14KB | `85818981` |
| [MT/MQL5/Include/Controls/DatePicker.mqh](MT/MQL5/Include/Controls/DatePicker.mqh) |  |  | 2026-05-30 | 10KB | `2e2ce745` |
| [MT/MQL5/Include/Controls/Defines.mqh](MT/MQL5/Include/Controls/Defines.mqh) |  |  | 2026-05-30 | 12KB | `066dbc7d` |
| [MT/MQL5/Include/Controls/Dialog.mqh](MT/MQL5/Include/Controls/Dialog.mqh) |  |  | 2026-05-30 | 37KB | `d1e15482` |
| [MT/MQL5/Include/Controls/Edit.mqh](MT/MQL5/Include/Controls/Edit.mqh) |  |  | 2026-05-30 | 8KB | `aed92dbf` |
| [MT/MQL5/Include/Controls/Label.mqh](MT/MQL5/Include/Controls/Label.mqh) |  |  | 2026-05-30 | 4KB | `1d73f6a0` |
| [MT/MQL5/Include/Controls/ListView.mqh](MT/MQL5/Include/Controls/ListView.mqh) |  |  | 2026-05-30 | 19KB | `3ca374e7` |
| [MT/MQL5/Include/Controls/Panel.mqh](MT/MQL5/Include/Controls/Panel.mqh) |  |  | 2026-05-30 | 5KB | `836869ed` |
| [MT/MQL5/Include/Controls/Picture.mqh](MT/MQL5/Include/Controls/Picture.mqh) |  |  | 2026-05-30 | 5KB | `5e62233e` |
| [MT/MQL5/Include/Controls/RadioButton.mqh](MT/MQL5/Include/Controls/RadioButton.mqh) |  |  | 2026-05-30 | 6KB | `5537db3e` |
| [MT/MQL5/Include/Controls/RadioGroup.mqh](MT/MQL5/Include/Controls/RadioGroup.mqh) |  |  | 2026-05-30 | 13KB | `13d3d9bc` |
| [MT/MQL5/Include/Controls/Rect.mqh](MT/MQL5/Include/Controls/Rect.mqh) |  |  | 2026-05-30 | 10KB | `c0b73dc8` |
| [MT/MQL5/Include/Controls/Scrolls.mqh](MT/MQL5/Include/Controls/Scrolls.mqh) |  |  | 2026-05-30 | 26KB | `18fb49e5` |
| [MT/MQL5/Include/Controls/SpinEdit.mqh](MT/MQL5/Include/Controls/SpinEdit.mqh) |  |  | 2026-05-30 | 10KB | `1e7dded7` |
| [MT/MQL5/Include/Controls/Wnd.mqh](MT/MQL5/Include/Controls/Wnd.mqh) |  |  | 2026-05-30 | 29KB | `0c5fa8a9` |
| [MT/MQL5/Include/Controls/WndClient.mqh](MT/MQL5/Include/Controls/WndClient.mqh) |  |  | 2026-05-30 | 11KB | `25e7cdee` |
| [MT/MQL5/Include/Controls/WndContainer.mqh](MT/MQL5/Include/Controls/WndContainer.mqh) |  |  | 2026-05-30 | 15KB | `e5d88b28` |
| [MT/MQL5/Include/Controls/WndObj.mqh](MT/MQL5/Include/Controls/WndObj.mqh) |  |  | 2026-05-30 | 10KB | `79eb339d` |
| [MT/MQL5/Include/ERRORS.mqh](MT/MQL5/Include/ERRORS.mqh) |  |  | 2026-05-30 | 22B | `f437293a` |
| [MT/MQL5/Include/ERRORs.mqh](MT/MQL5/Include/ERRORs.mqh) |  |  | 2026-05-30 | 20KB | `3a30c213` |
| [MT/MQL5/Include/Expert/Expert.mqh](MT/MQL5/Include/Expert/Expert.mqh) |  |  | 2026-05-30 | 119KB | `667e739c` |
| [MT/MQL5/Include/Expert/ExpertBase.mqh](MT/MQL5/Include/Expert/ExpertBase.mqh) |  |  | 2026-05-30 | 26KB | `15d5fae3` |
| [MT/MQL5/Include/Expert/ExpertMoney.mqh](MT/MQL5/Include/Expert/ExpertMoney.mqh) |  |  | 2026-05-30 | 4KB | `9e6d6c11` |
| [MT/MQL5/Include/Expert/ExpertSignal.mqh](MT/MQL5/Include/Expert/ExpertSignal.mqh) |  |  | 2026-05-30 | 19KB | `b7a7ad81` |
| [MT/MQL5/Include/Expert/ExpertTrade.mqh](MT/MQL5/Include/Expert/ExpertTrade.mqh) |  |  | 2026-05-30 | 6KB | `b2b0f317` |
| [MT/MQL5/Include/Expert/ExpertTrailing.mqh](MT/MQL5/Include/Expert/ExpertTrailing.mqh) |  |  | 2026-05-30 | 1KB | `66a3a25d` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh) |  |  | 2026-05-30 | 3KB | `62d53ce2` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh) |  |  | 2026-05-30 | 3KB | `f8a1fe72` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh) |  |  | 2026-05-30 | 4KB | `38b6869e` |
| [MT/MQL5/Include/Expert/Money/MoneyNone.mqh](MT/MQL5/Include/Expert/Money/MoneyNone.mqh) |  |  | 2026-05-30 | 3KB | `b866ac59` |
| [MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh](MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh) |  |  | 2026-05-30 | 6KB | `22c850e8` |
| [MT/MQL5/Include/Expert/Signal/SignalAC.mqh](MT/MQL5/Include/Expert/Signal/SignalAC.mqh) |  |  | 2026-05-30 | 7KB | `c3fe7a79` |
| [MT/MQL5/Include/Expert/Signal/SignalAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalAMA.mqh) |  |  | 2026-05-30 | 12KB | `a5bbc59b` |
| [MT/MQL5/Include/Expert/Signal/SignalAO.mqh](MT/MQL5/Include/Expert/Signal/SignalAO.mqh) |  |  | 2026-05-30 | 13KB | `cadb934f` |
| [MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh) |  |  | 2026-05-30 | 11KB | `0a9fdc1f` |
| [MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh) |  |  | 2026-05-30 | 11KB | `9b6f9b73` |
| [MT/MQL5/Include/Expert/Signal/SignalCCI.mqh](MT/MQL5/Include/Expert/Signal/SignalCCI.mqh) |  |  | 2026-05-30 | 17KB | `8b02f15b` |
| [MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh) |  |  | 2026-05-30 | 11KB | `27a1b1b3` |
| [MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh](MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh) |  |  | 2026-05-30 | 16KB | `28378510` |
| [MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh](MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh) |  |  | 2026-05-30 | 9KB | `07c314dc` |
| [MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh) |  |  | 2026-05-30 | 11KB | `cc3ea8eb` |
| [MT/MQL5/Include/Expert/Signal/SignalITF.mqh](MT/MQL5/Include/Expert/Signal/SignalITF.mqh) |  |  | 2026-05-30 | 4KB | `0991d92b` |
| [MT/MQL5/Include/Expert/Signal/SignalMA.mqh](MT/MQL5/Include/Expert/Signal/SignalMA.mqh) |  |  | 2026-05-30 | 11KB | `51878396` |
| [MT/MQL5/Include/Expert/Signal/SignalMACD.mqh](MT/MQL5/Include/Expert/Signal/SignalMACD.mqh) |  |  | 2026-05-30 | 19KB | `6794035e` |
| [MT/MQL5/Include/Expert/Signal/SignalRSI.mqh](MT/MQL5/Include/Expert/Signal/SignalRSI.mqh) |  |  | 2026-05-30 | 18KB | `536ef112` |
| [MT/MQL5/Include/Expert/Signal/SignalRVI.mqh](MT/MQL5/Include/Expert/Signal/SignalRVI.mqh) |  |  | 2026-05-30 | 7KB | `89af5171` |
| [MT/MQL5/Include/Expert/Signal/SignalSAR.mqh](MT/MQL5/Include/Expert/Signal/SignalSAR.mqh) |  |  | 2026-05-30 | 7KB | `b84730ef` |
| [MT/MQL5/Include/Expert/Signal/SignalStoch.mqh](MT/MQL5/Include/Expert/Signal/SignalStoch.mqh) |  |  | 2026-05-30 | 19KB | `6cff6dd9` |
| [MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh) |  |  | 2026-05-30 | 11KB | `e8258b51` |
| [MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh](MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh) |  |  | 2026-05-30 | 17KB | `39e3f752` |
| [MT/MQL5/Include/Expert/Signal/SignalWPR.mqh](MT/MQL5/Include/Expert/Signal/SignalWPR.mqh) |  |  | 2026-05-30 | 16KB | `78fc2800` |
| [MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh](MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh) |  |  | 2026-05-30 | 5KB | `39c49839` |
| [MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh](MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh) |  |  | 2026-05-30 | 6KB | `a11d5980` |
| [MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh](MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh) |  |  | 2026-05-30 | 2KB | `bbdc0191` |
| [MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh](MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh) |  |  | 2026-05-30 | 5KB | `b73d3930` |
| [MT/MQL5/Include/FUNCTIONS.mqh](MT/MQL5/Include/FUNCTIONS.mqh) |  |  | 2026-05-30 | 15KB | `b3fce0c5` |
| [MT/MQL5/Include/Files/File.mqh](MT/MQL5/Include/Files/File.mqh) |  |  | 2026-05-30 | 11KB | `9b8c6449` |
| [MT/MQL5/Include/Files/FileBMP.mqh](MT/MQL5/Include/Files/FileBMP.mqh) |  |  | 2026-05-30 | 6KB | `5827c2f4` |
| [MT/MQL5/Include/Files/FileBin.mqh](MT/MQL5/Include/Files/FileBin.mqh) |  |  | 2026-05-30 | 20KB | `916879d9` |
| [MT/MQL5/Include/Files/FilePipe.mqh](MT/MQL5/Include/Files/FilePipe.mqh) |  |  | 2026-05-30 | 12KB | `197bd514` |
| [MT/MQL5/Include/Files/FileTxt.mqh](MT/MQL5/Include/Files/FileTxt.mqh) |  |  | 2026-05-30 | 2KB | `14f5dff2` |
| [MT/MQL5/Include/Generic/ArrayList.mqh](MT/MQL5/Include/Generic/ArrayList.mqh) |  |  | 2026-05-30 | 49KB | `b840b4bc` |
| [MT/MQL5/Include/Generic/HashMap.mqh](MT/MQL5/Include/Generic/HashMap.mqh) |  |  | 2026-05-30 | 25KB | `e22edcd0` |
| [MT/MQL5/Include/Generic/HashSet.mqh](MT/MQL5/Include/Generic/HashSet.mqh) |  |  | 2026-05-30 | 36KB | `d38ceded` |
| [MT/MQL5/Include/Generic/Interfaces/ICollection.mqh](MT/MQL5/Include/Generic/Interfaces/ICollection.mqh) |  |  | 2026-05-30 | 1KB | `402ea83c` |
| [MT/MQL5/Include/Generic/Interfaces/IComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IComparable.mqh) |  |  | 2026-05-30 | 1KB | `aa814da7` |
| [MT/MQL5/Include/Generic/Interfaces/IComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IComparer.mqh) |  |  | 2026-05-30 | 998B | `0cf6f120` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh) |  |  | 2026-05-30 | 1012B | `4979c4c7` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh) |  |  | 2026-05-30 | 1KB | `7e8c86a3` |
| [MT/MQL5/Include/Generic/Interfaces/IList.mqh](MT/MQL5/Include/Generic/Interfaces/IList.mqh) |  |  | 2026-05-30 | 1KB | `e5e9586d` |
| [MT/MQL5/Include/Generic/Interfaces/IMap.mqh](MT/MQL5/Include/Generic/Interfaces/IMap.mqh) |  |  | 2026-05-30 | 1KB | `303da59f` |
| [MT/MQL5/Include/Generic/Interfaces/ISet.mqh](MT/MQL5/Include/Generic/Interfaces/ISet.mqh) |  |  | 2026-05-30 | 1KB | `15eaf0e1` |
| [MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh](MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh) |  |  | 2026-05-30 | 4KB | `4d708d05` |
| [MT/MQL5/Include/Generic/Internal/CompareFunction.mqh](MT/MQL5/Include/Generic/Internal/CompareFunction.mqh) |  |  | 2026-05-30 | 7KB | `b5a08f39` |
| [MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh) |  |  | 2026-05-30 | 1KB | `2f430ea9` |
| [MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh) |  |  | 2026-05-30 | 1KB | `ea37b258` |
| [MT/MQL5/Include/Generic/Internal/EqualFunction.mqh](MT/MQL5/Include/Generic/Internal/EqualFunction.mqh) |  |  | 2026-05-30 | 1KB | `47e2bc02` |
| [MT/MQL5/Include/Generic/Internal/HashFunction.mqh](MT/MQL5/Include/Generic/Internal/HashFunction.mqh) |  |  | 2026-05-30 | 7KB | `87c69022` |
| [MT/MQL5/Include/Generic/Internal/Introsort.mqh](MT/MQL5/Include/Generic/Internal/Introsort.mqh) |  |  | 2026-05-30 | 8KB | `2bd4b00f` |
| [MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh](MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh) |  |  | 2026-05-30 | 3KB | `6d9e6603` |
| [MT/MQL5/Include/Generic/LinkedList.mqh](MT/MQL5/Include/Generic/LinkedList.mqh) |  |  | 2026-05-30 | 20KB | `1cdd7bab` |
| [MT/MQL5/Include/Generic/Queue.mqh](MT/MQL5/Include/Generic/Queue.mqh) |  |  | 2026-05-30 | 29KB | `1313ea7c` |
| [MT/MQL5/Include/Generic/RedBlackTree.mqh](MT/MQL5/Include/Generic/RedBlackTree.mqh) |  |  | 2026-05-30 | 73KB | `3b568c0d` |
| [MT/MQL5/Include/Generic/SortedMap.mqh](MT/MQL5/Include/Generic/SortedMap.mqh) |  |  | 2026-05-30 | 14KB | `5745fcdf` |
| [MT/MQL5/Include/Generic/SortedSet.mqh](MT/MQL5/Include/Generic/SortedSet.mqh) |  |  | 2026-05-30 | 24KB | `0efbc013` |
| [MT/MQL5/Include/Generic/Stack.mqh](MT/MQL5/Include/Generic/Stack.mqh) |  |  | 2026-05-30 | 8KB | `39c47e97` |
| [MT/MQL5/Include/Graphics/Axis.mqh](MT/MQL5/Include/Graphics/Axis.mqh) |  |  | 2026-05-30 | 12KB | `30e582f4` |
| [MT/MQL5/Include/Graphics/ColorGenerator.mqh](MT/MQL5/Include/Graphics/ColorGenerator.mqh) |  |  | 2026-05-30 | 3KB | `204f3a70` |
| [MT/MQL5/Include/Graphics/Curve.mqh](MT/MQL5/Include/Graphics/Curve.mqh) |  |  | 2026-05-30 | 22KB | `5b3764a4` |
| [MT/MQL5/Include/Graphics/Graphic.mqh](MT/MQL5/Include/Graphics/Graphic.mqh) |  |  | 2026-05-30 | 169KB | `0cca00f7` |
| [MT/MQL5/Include/INPUT.mqh](MT/MQL5/Include/INPUT.mqh) |  |  | 2026-05-30 | 22KB | `477b69ca` |
| [MT/MQL5/Include/Indicators/BillWilliams.mqh](MT/MQL5/Include/Indicators/BillWilliams.mqh) |  |  | 2026-05-30 | 32KB | `f57a6107` |
| [MT/MQL5/Include/Indicators/Custom.mqh](MT/MQL5/Include/Indicators/Custom.mqh) |  |  | 2026-05-30 | 7KB | `5e9fbee8` |
| [MT/MQL5/Include/Indicators/Indicator.mqh](MT/MQL5/Include/Indicators/Indicator.mqh) |  |  | 2026-05-30 | 19KB | `1e663d5c` |
| [MT/MQL5/Include/Indicators/Indicators.mqh](MT/MQL5/Include/Indicators/Indicators.mqh) |  |  | 2026-05-30 | 11KB | `e8cd4f31` |
| [MT/MQL5/Include/Indicators/Oscilators.mqh](MT/MQL5/Include/Indicators/Oscilators.mqh) |  |  | 2026-05-30 | 72KB | `18221239` |
| [MT/MQL5/Include/Indicators/Series.mqh](MT/MQL5/Include/Indicators/Series.mqh) |  |  | 2026-05-30 | 12KB | `e0040d48` |
| [MT/MQL5/Include/Indicators/TimeSeries.mqh](MT/MQL5/Include/Indicators/TimeSeries.mqh) |  |  | 2026-05-30 | 61KB | `9aa20382` |
| [MT/MQL5/Include/Indicators/Trend.mqh](MT/MQL5/Include/Indicators/Trend.mqh) |  |  | 2026-05-30 | 72KB | `eb97c7df` |
| [MT/MQL5/Include/Indicators/Volumes.mqh](MT/MQL5/Include/Indicators/Volumes.mqh) |  |  | 2026-05-30 | 17KB | `81921db6` |
| [MT/MQL5/Include/MAIN.mqh](MT/MQL5/Include/MAIN.mqh) |  |  | 2026-05-30 | 10KB | `53cf2ce0` |
| [MT/MQL5/Include/MM.mqh](MT/MQL5/Include/MM.mqh) |  |  | 2026-05-30 | 10KB | `8b02452d` |
| [MT/MQL5/Include/MQL4Compat.mqh](MT/MQL5/Include/MQL4Compat.mqh) |  |  | 2026-05-30 | 28KB | `b26d5ab4` |
| [MT/MQL5/Include/Math/Alglib/alglib.mqh](MT/MQL5/Include/Math/Alglib/alglib.mqh) |  |  | 2026-04-16 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/alglibinternal.mqh](MT/MQL5/Include/Math/Alglib/alglibinternal.mqh) |  |  | 2026-05-30 | 579KB | `175c1183` |
| [MT/MQL5/Include/Math/Alglib/alglibmisc.mqh](MT/MQL5/Include/Math/Alglib/alglibmisc.mqh) |  |  | 2026-05-30 | 119KB | `7466a12d` |
| [MT/MQL5/Include/Math/Alglib/ap.mqh](MT/MQL5/Include/Math/Alglib/ap.mqh) |  |  | 2026-05-30 | 89KB | `a7e4677f` |
| [MT/MQL5/Include/Math/Alglib/arrayresize.mqh](MT/MQL5/Include/Math/Alglib/arrayresize.mqh) |  |  | 2026-05-30 | 3KB | `e64b72cb` |
| [MT/MQL5/Include/Math/Alglib/bitconvert.mqh](MT/MQL5/Include/Math/Alglib/bitconvert.mqh) |  |  | 2026-05-30 | 13KB | `c9dffd4e` |
| [MT/MQL5/Include/Math/Alglib/dataanalysis.mqh](MT/MQL5/Include/Math/Alglib/dataanalysis.mqh) |  |  | 2026-05-30 | 1MB | `596bc4ac` |
| [MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh](MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh) |  |  | 2026-05-30 | 21KB | `ebc422fa` |
| [MT/MQL5/Include/Math/Alglib/diffequations.mqh](MT/MQL5/Include/Math/Alglib/diffequations.mqh) |  |  | 2026-05-30 | 32KB | `e612f10b` |
| [MT/MQL5/Include/Math/Alglib/fasttransforms.mqh](MT/MQL5/Include/Math/Alglib/fasttransforms.mqh) |  |  | 2026-05-30 | 92KB | `f6bbf7c2` |
| [MT/MQL5/Include/Math/Alglib/integration.mqh](MT/MQL5/Include/Math/Alglib/integration.mqh) |  |  | 2026-05-30 | 116KB | `f8600aaa` |
| [MT/MQL5/Include/Math/Alglib/interpolation.mqh](MT/MQL5/Include/Math/Alglib/interpolation.mqh) |  |  | 2026-05-30 | 1MB | `43be4546` |
| [MT/MQL5/Include/Math/Alglib/linalg.mqh](MT/MQL5/Include/Math/Alglib/linalg.mqh) |  |  | 2026-05-30 | 1MB | `73b32040` |
| [MT/MQL5/Include/Math/Alglib/matrix.mqh](MT/MQL5/Include/Math/Alglib/matrix.mqh) |  |  | 2026-05-30 | 45KB | `52f0963f` |
| [MT/MQL5/Include/Math/Alglib/optimization.mqh](MT/MQL5/Include/Math/Alglib/optimization.mqh) |  |  | 2026-04-16 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/solvers.mqh](MT/MQL5/Include/Math/Alglib/solvers.mqh) |  |  | 2026-05-30 | 295KB | `cfe0276c` |
| [MT/MQL5/Include/Math/Alglib/specialfunctions.mqh](MT/MQL5/Include/Math/Alglib/specialfunctions.mqh) |  |  | 2026-05-30 | 235KB | `a4f6fa85` |
| [MT/MQL5/Include/Math/Alglib/statistics.mqh](MT/MQL5/Include/Math/Alglib/statistics.mqh) |  |  | 2026-05-30 | 407KB | `3156c1e5` |
| [MT/MQL5/Include/Math/Fuzzy/dictionary.mqh](MT/MQL5/Include/Math/Fuzzy/dictionary.mqh) |  |  | 2026-05-30 | 8KB | `5fc3e371` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh) |  |  | 2026-05-30 | 17KB | `2b675722` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh) |  |  | 2026-05-30 | 3KB | `b5744882` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh) |  |  | 2026-05-30 | 5KB | `c70f7f31` |
| [MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh) |  |  | 2026-05-30 | 11KB | `0c24ddb8` |
| [MT/MQL5/Include/Math/Fuzzy/helper.mqh](MT/MQL5/Include/Math/Fuzzy/helper.mqh) |  |  | 2026-05-30 | 7KB | `26906afe` |
| [MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh](MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh) |  |  | 2026-05-30 | 7KB | `981fa315` |
| [MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh) |  |  | 2026-05-30 | 22KB | `a4ff1a81` |
| [MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh](MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh) |  |  | 2026-05-30 | 43KB | `db1e7a2e` |
| [MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh](MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh) |  |  | 2026-05-30 | 36KB | `a32fa745` |
| [MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh) |  |  | 2026-05-30 | 13KB | `5502caaf` |
| [MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh](MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh) |  |  | 2026-05-30 | 10KB | `89b49ae6` |
| [MT/MQL5/Include/Math/Stat/Beta.mqh](MT/MQL5/Include/Math/Stat/Beta.mqh) |  |  | 2026-05-30 | 32KB | `9aef6db1` |
| [MT/MQL5/Include/Math/Stat/Binomial.mqh](MT/MQL5/Include/Math/Stat/Binomial.mqh) |  |  | 2026-05-30 | 34KB | `eb1604d4` |
| [MT/MQL5/Include/Math/Stat/Cauchy.mqh](MT/MQL5/Include/Math/Stat/Cauchy.mqh) |  |  | 2026-05-30 | 24KB | `2a5b994b` |
| [MT/MQL5/Include/Math/Stat/ChiSquare.mqh](MT/MQL5/Include/Math/Stat/ChiSquare.mqh) |  |  | 2026-05-30 | 24KB | `31d24602` |
| [MT/MQL5/Include/Math/Stat/Exponential.mqh](MT/MQL5/Include/Math/Stat/Exponential.mqh) |  |  | 2026-05-30 | 24KB | `f1846a90` |
| [MT/MQL5/Include/Math/Stat/F.mqh](MT/MQL5/Include/Math/Stat/F.mqh) |  |  | 2026-05-30 | 26KB | `9e90f69b` |
| [MT/MQL5/Include/Math/Stat/Gamma.mqh](MT/MQL5/Include/Math/Stat/Gamma.mqh) |  |  | 2026-05-30 | 31KB | `358ed8cd` |
| [MT/MQL5/Include/Math/Stat/Geometric.mqh](MT/MQL5/Include/Math/Stat/Geometric.mqh) |  |  | 2026-05-30 | 24KB | `031a2627` |
| [MT/MQL5/Include/Math/Stat/Hypergeometric.mqh](MT/MQL5/Include/Math/Stat/Hypergeometric.mqh) |  |  | 2026-05-30 | 34KB | `2208c6d3` |
| [MT/MQL5/Include/Math/Stat/Logistic.mqh](MT/MQL5/Include/Math/Stat/Logistic.mqh) |  |  | 2026-05-30 | 27KB | `6a74c8a4` |
| [MT/MQL5/Include/Math/Stat/Lognormal.mqh](MT/MQL5/Include/Math/Stat/Lognormal.mqh) |  |  | 2026-05-30 | 28KB | `ca8a59c4` |
| [MT/MQL5/Include/Math/Stat/Math.mqh](MT/MQL5/Include/Math/Stat/Math.mqh) |  |  | 2026-05-30 | 424KB | `65212111` |
| [MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh](MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh) |  |  | 2026-05-30 | 28KB | `27a3e21c` |
| [MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh](MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh) |  |  | 2026-05-30 | 40KB | `ce6d8685` |
| [MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh](MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh) |  |  | 2026-05-30 | 36KB | `96a70f8c` |
| [MT/MQL5/Include/Math/Stat/NoncentralF.mqh](MT/MQL5/Include/Math/Stat/NoncentralF.mqh) |  |  | 2026-05-30 | 34KB | `9990ce6c` |
| [MT/MQL5/Include/Math/Stat/NoncentralT.mqh](MT/MQL5/Include/Math/Stat/NoncentralT.mqh) |  |  | 2026-05-30 | 46KB | `9e154d87` |
| [MT/MQL5/Include/Math/Stat/Normal.mqh](MT/MQL5/Include/Math/Stat/Normal.mqh) |  |  | 2026-05-30 | 39KB | `21ffb41d` |
| [MT/MQL5/Include/Math/Stat/Poisson.mqh](MT/MQL5/Include/Math/Stat/Poisson.mqh) |  |  | 2026-05-30 | 31KB | `df71df52` |
| [MT/MQL5/Include/Math/Stat/Stat.mqh](MT/MQL5/Include/Math/Stat/Stat.mqh) |  |  | 2026-05-30 | 1KB | `c8af779d` |
| [MT/MQL5/Include/Math/Stat/T.mqh](MT/MQL5/Include/Math/Stat/T.mqh) |  |  | 2026-05-30 | 27KB | `d3dbb617` |
| [MT/MQL5/Include/Math/Stat/Uniform.mqh](MT/MQL5/Include/Math/Stat/Uniform.mqh) |  |  | 2026-05-30 | 25KB | `8de48345` |
| [MT/MQL5/Include/Math/Stat/Weibull.mqh](MT/MQL5/Include/Math/Stat/Weibull.mqh) |  |  | 2026-05-30 | 26KB | `ff94f29f` |
| [MT/MQL5/Include/ORDERS.mqh](MT/MQL5/Include/ORDERS.mqh) |  |  | 2026-05-30 | 40KB | `6655a760` |
| [MT/MQL5/Include/OUTPUT.mqh](MT/MQL5/Include/OUTPUT.mqh) |  |  | 2026-05-30 | 18KB | `5a14ae04` |
| [MT/MQL5/Include/OpenCL/OpenCL.mqh](MT/MQL5/Include/OpenCL/OpenCL.mqh) |  |  | 2026-05-30 | 27KB | `a82fa081` |
| [MT/MQL5/Include/SERVICE.mqh](MT/MQL5/Include/SERVICE.mqh) |  |  | 2026-05-30 | 80KB | `aced0492` |
| [MT/MQL5/Include/Strings/String.mqh](MT/MQL5/Include/Strings/String.mqh) |  |  | 2026-05-30 | 13KB | `adbde208` |
| [MT/MQL5/Include/Tools/DateTime.mqh](MT/MQL5/Include/Tools/DateTime.mqh) |  |  | 2026-05-30 | 17KB | `e06f30f0` |
| [MT/MQL5/Include/Trade/AccountInfo.mqh](MT/MQL5/Include/Trade/AccountInfo.mqh) |  |  | 2026-05-30 | 17KB | `336acd5d` |
| [MT/MQL5/Include/Trade/DealInfo.mqh](MT/MQL5/Include/Trade/DealInfo.mqh) |  |  | 2026-05-30 | 15KB | `5f444466` |
| [MT/MQL5/Include/Trade/HistoryOrderInfo.mqh](MT/MQL5/Include/Trade/HistoryOrderInfo.mqh) |  |  | 2026-05-30 | 19KB | `3c45a5f3` |
| [MT/MQL5/Include/Trade/OrderInfo.mqh](MT/MQL5/Include/Trade/OrderInfo.mqh) |  |  | 2026-05-30 | 21KB | `c7977cef` |
| [MT/MQL5/Include/Trade/PositionInfo.mqh](MT/MQL5/Include/Trade/PositionInfo.mqh) |  |  | 2026-05-30 | 15KB | `8f85983c` |
| [MT/MQL5/Include/Trade/SymbolInfo.mqh](MT/MQL5/Include/Trade/SymbolInfo.mqh) |  |  | 2026-05-30 | 35KB | `bb2f2760` |
| [MT/MQL5/Include/Trade/TerminalInfo.mqh](MT/MQL5/Include/Trade/TerminalInfo.mqh) |  |  | 2026-05-30 | 10KB | `db1d371d` |
| [MT/MQL5/Include/Trade/Trade.mqh](MT/MQL5/Include/Trade/Trade.mqh) |  |  | 2026-05-30 | 67KB | `ebefad3b` |
| [MT/MQL5/Include/WinAPI/errhandlingapi.mqh](MT/MQL5/Include/WinAPI/errhandlingapi.mqh) |  |  | 2026-05-30 | 1KB | `9c6abbb5` |
| [MT/MQL5/Include/WinAPI/fileapi.mqh](MT/MQL5/Include/WinAPI/fileapi.mqh) |  |  | 2026-05-30 | 9KB | `ce8862f9` |
| [MT/MQL5/Include/WinAPI/handleapi.mqh](MT/MQL5/Include/WinAPI/handleapi.mqh) |  |  | 2026-05-30 | 1KB | `72389e0e` |
| [MT/MQL5/Include/WinAPI/libloaderapi.mqh](MT/MQL5/Include/WinAPI/libloaderapi.mqh) |  |  | 2026-05-30 | 2KB | `fbe9c927` |
| [MT/MQL5/Include/WinAPI/memoryapi.mqh](MT/MQL5/Include/WinAPI/memoryapi.mqh) |  |  | 2026-05-30 | 5KB | `115d0c9e` |
| [MT/MQL5/Include/WinAPI/processenv.mqh](MT/MQL5/Include/WinAPI/processenv.mqh) |  |  | 2026-05-30 | 1KB | `7788d30f` |
| [MT/MQL5/Include/WinAPI/processthreadsapi.mqh](MT/MQL5/Include/WinAPI/processthreadsapi.mqh) |  |  | 2026-05-30 | 10KB | `5d2c97c4` |
| [MT/MQL5/Include/WinAPI/securitybaseapi.mqh](MT/MQL5/Include/WinAPI/securitybaseapi.mqh) |  |  | 2026-05-30 | 16KB | `a8296031` |
| [MT/MQL5/Include/WinAPI/sysinfoapi.mqh](MT/MQL5/Include/WinAPI/sysinfoapi.mqh) |  |  | 2026-05-30 | 4KB | `f1e35723` |
| [MT/MQL5/Include/WinAPI/winapi.mqh](MT/MQL5/Include/WinAPI/winapi.mqh) |  |  | 2026-05-30 | 827B | `18ecf395` |
| [MT/MQL5/Include/WinAPI/winbase.mqh](MT/MQL5/Include/WinAPI/winbase.mqh) |  |  | 2026-05-30 | 43KB | `80b349f7` |
| [MT/MQL5/Include/WinAPI/windef.mqh](MT/MQL5/Include/WinAPI/windef.mqh) |  |  | 2026-05-30 | 8KB | `b3d4d5b1` |
| [MT/MQL5/Include/WinAPI/wingdi.mqh](MT/MQL5/Include/WinAPI/wingdi.mqh) |  |  | 2026-05-30 | 63KB | `000f20a9` |
| [MT/MQL5/Include/WinAPI/winnt.mqh](MT/MQL5/Include/WinAPI/winnt.mqh) |  |  | 2026-05-30 | 95KB | `0e776dbe` |
| [MT/MQL5/Include/WinAPI/winreg.mqh](MT/MQL5/Include/WinAPI/winreg.mqh) |  |  | 2026-05-30 | 5KB | `3681c95b` |
| [MT/MQL5/Include/WinAPI/winuser.mqh](MT/MQL5/Include/WinAPI/winuser.mqh) |  |  | 2026-05-30 | 81KB | `0a662398` |
| [MT/MQL5/Include/head_PIC.mqh](MT/MQL5/Include/head_PIC.mqh) |  |  | 2026-05-30 | 9KB | `356c8df3` |
| [MT/MQL5/Include/iGRAPH.mqh](MT/MQL5/Include/iGRAPH.mqh) |  |  | 2026-05-30 | 39KB | `f5abe888` |
| [MT/MQL5/Include/lib_ATR.mqh](MT/MQL5/Include/lib_ATR.mqh) |  |  | 2026-05-30 | 2KB | `dcc5b590` |
| [MT/MQL5/Include/lib_Flat.mqh](MT/MQL5/Include/lib_Flat.mqh) |  |  | 2026-05-30 | 13KB | `4536cf5c` |
| [MT/MQL5/Include/lib_ML_Signal.mqh](MT/MQL5/Include/lib_ML_Signal.mqh) |  |  | 2026-05-30 | 14KB | `996e3367` |
| [MT/MQL5/Include/lib_ML_Signal_TB.mqh](MT/MQL5/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-05-30 | 8KB | `86f9658b` |
| [MT/MQL5/Include/lib_PIC.mqh](MT/MQL5/Include/lib_PIC.mqh) |  |  | 2026-05-30 | 56KB | `cc8e0ac9` |
| [MT/MQL5/Include/stderror.mqh](MT/MQL5/Include/stderror.mqh) |  |  | 2026-05-30 | 9KB | `e8590cbe` |
| [MT/MQL5/Include/stdlib.mqh](MT/MQL5/Include/stdlib.mqh) |  |  | 2026-05-30 | 712B | `b86b17a9` |

## Wiki

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [wiki/.archive/execution-tracks-monolith-deprecated.md](wiki/.archive/execution-tracks-monolith-deprecated.md) |  | 2026-05-30 | 89KB | `11a5246a` |
| [wiki/concepts/signal-archetypes.md](wiki/concepts/signal-archetypes.md) |  | 2026-06-06 | 3KB | `52a35182` |
| [wiki/index.md](wiki/index.md) |  | 2026-06-06 | 3KB | `2383c407` |
| [wiki/log.md](wiki/log.md) |  | 2026-05-30 | 26KB | `9b968e93` |
| [wiki/research/execution-tracks-direct-direction-audit.md](wiki/research/execution-tracks-direct-direction-audit.md) |  | 2026-05-30 | 7KB | `db2ea437` |
| [wiki/research/execution-tracks-early-research.md](wiki/research/execution-tracks-early-research.md) |  | 2026-05-30 | 5KB | `8d497df0` |
| [wiki/research/execution-tracks-entry-path-v1.md](wiki/research/execution-tracks-entry-path-v1.md) |  | 2026-06-06 | 21KB | `ed6e7d2e` |
| [wiki/research/execution-tracks-live-safe-audit.md](wiki/research/execution-tracks-live-safe-audit.md) |  | 2026-05-30 | 11KB | `d9a70550` |
| [wiki/research/execution-tracks-overview.md](wiki/research/execution-tracks-overview.md) |  | 2026-05-30 | 4KB | `fecf262c` |
| [wiki/research/execution-tracks-reconciliation-plus-audit.md](wiki/research/execution-tracks-reconciliation-plus-audit.md) |  | 2026-05-30 | 7KB | `0f145788` |
| [wiki/research/execution-tracks-reproducibility-plus-parity.md](wiki/research/execution-tracks-reproducibility-plus-parity.md) |  | 2026-05-30 | 5KB | `1ab23523` |
| [wiki/research/execution-tracks-robustness-plus-portfolio.md](wiki/research/execution-tracks-robustness-plus-portfolio.md) |  | 2026-05-30 | 6KB | `91183bdb` |
| [wiki/research/execution-tracks-take-skip-v2.md](wiki/research/execution-tracks-take-skip-v2.md) |  | 2026-06-06 | 24KB | `ec105d66` |
| [wiki/research/execution-tracks-telemetry-plus-mql.md](wiki/research/execution-tracks-telemetry-plus-mql.md) |  | 2026-05-30 | 10KB | `7b5c0cf0` |
| [wiki/research/limit-order-feature-foundation.md](wiki/research/limit-order-feature-foundation.md) |  | 2026-06-06 | 4KB | `2bea4655` |
| [wiki/research/methodology-cycle-candidate-source-v2.md](wiki/research/methodology-cycle-candidate-source-v2.md) |  | 2026-06-06 | 3KB | `fdb94cc5` |
| [wiki/research/signal-quality-research.md](wiki/research/signal-quality-research.md) |  | 2026-05-30 | 8KB | `a5355801` |
| [wiki/wiki.py](wiki/wiki.py) |  | 2026-05-30 | 18KB | `0d2c8d8e` |

## Agent Config

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.kilocode/mcp.json](.kilocode/mcp.json) |  | 2026-05-30 | 481B | `14bc1e7d` |
| [.kilocode/package-lock.json](.kilocode/package-lock.json) |  | 2026-05-30 | 3KB | `ca4a6cad` |
| [.kilocode/rules-architect/user_rules.md](.kilocode/rules-architect/user_rules.md) |  | 2026-05-30 | 1KB | `351b6484` |
| [.kilocode/rules-ask/user_rules.md](.kilocode/rules-ask/user_rules.md) |  | 2026-05-30 | 1KB | `351b6484` |

## Other

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.opencode/agents/reviewer.md](.opencode/agents/reviewer.md) |  | 2026-06-03 | 3KB | `362f90fe` |
| [.opencode/package-lock.json](.opencode/package-lock.json) |  | 2026-05-20 | 13KB | `afac1cb9` |
| [.opencode/package.json](.opencode/package.json) |  | 2026-05-20 | 64B | `9c478c62` |
| [opencode.json](opencode.json) |  | 2026-06-07 | 327B | `62dd80d0` |

