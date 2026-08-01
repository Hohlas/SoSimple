# REPO Integrity Map — SoSimple
> Auto-generated 2026-08-01 07:42 UTC · git `69bd42a`
> Refresh: `python wiki/wiki.py generate`  ·  Verify: `python wiki/wiki.py verify`

## Agent Access Protocol

1. Read this file first to get a project map (what exists, where, integrity hash).
2. Run `python wiki/wiki.py verify` to detect files changed since last index.
3. Navigate via paths in the tables; use `wiki/research/` and `wiki/concepts/` for synthesized knowledge.
4. After modifying significant files, run `generate` and commit `REPO_integrity.md`.

**Tracked**: 3593 files  ·  **Commit**: `69bd42a`  ·  **Generated**: 2026-08-01 07:42 UTC

## Root Docs

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [AGENTS.md](AGENTS.md) |  | 2026-07-29 | 10KB | `8b0976f5` |
| [CHANGELOG.md](CHANGELOG.md) |  | 2026-08-01 | 167KB | `9dc1ab17` |
| [CLAUDE.md](CLAUDE.md) |  | 2026-06-17 | 288B | `9c4cf5c6` |
| [CONTEXT_HANDOFF.md](CONTEXT_HANDOFF.md) |  | 2026-08-01 | 2KB | `30159fa1` |
| [MODULE_INDEX.md](MODULE_INDEX.md) |  | 2026-08-01 | 59KB | `c7384b83` |
| [README.md](README.md) |  | 2026-06-17 | 1KB | `1b96a51c` |

## Documentation

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/API/api_server.py.md](docs/API/api_server.py.md) | Документация экспериментального REST API inference-пути | 2026-06-17 | 1KB | `c7573738` |
| [docs/API/telemetry_signal_watcher.py.md](docs/API/telemetry_signal_watcher.py.md) |  | 2026-06-17 | 20KB | `bb5a5097` |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам | 2026-07-20 | 26KB | `e29295c8` |
| [docs/ML/analyze_stage6_2_range_w1_postmortem.py.md](docs/ML/analyze_stage6_2_range_w1_postmortem.py.md) |  | 2026-07-20 | 1KB | `24414c2c` |
| [docs/ML/audit_fractal0_fixed11_candidate.py.md](docs/ML/audit_fractal0_fixed11_candidate.py.md) |  | 2026-07-29 | 2KB | `97f60ae2` |
| [docs/ML/audit_leaderboard_closure.py.md](docs/ML/audit_leaderboard_closure.py.md) |  | 2026-07-29 | 2KB | `f9139c2f` |
| [docs/ML/audit_leaderboard_robustness.py.md](docs/ML/audit_leaderboard_robustness.py.md) |  | 2026-07-29 | 2KB | `45f5565a` |
| [docs/ML/audit_time_only_robustness.py.md](docs/ML/audit_time_only_robustness.py.md) |  | 2026-07-29 | 2KB | `aeafc3d7` |
| [docs/ML/baseline_candidate_source.py.md](docs/ML/baseline_candidate_source.py.md) |  | 2026-06-17 | 906B | `405058a5` |
| [docs/ML/baseline_experiments.py.md](docs/ML/baseline_experiments.py.md) |  | 2026-06-17 | 2KB | `8dc50028` |
| [docs/ML/benchmark_cross_instrument_robustness.py.md](docs/ML/benchmark_cross_instrument_robustness.py.md) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты | 2026-06-17 | 3KB | `facaa586` |
| [docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md](docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md) |  | 2026-07-20 | 3KB | `7e0fdf41` |
| [docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md](docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md) |  | 2026-07-20 | 9KB | `95daba6d` |
| [docs/ML/benchmark_entry_based_amplitude_movement.py.md](docs/ML/benchmark_entry_based_amplitude_movement.py.md) |  | 2026-07-20 | 3KB | `e3cb4d50` |
| [docs/ML/benchmark_entry_based_movement_filter.py.md](docs/ML/benchmark_entry_based_movement_filter.py.md) |  | 2026-07-20 | 4KB | `7dde5fcc` |
| [docs/ML/benchmark_entry_based_movement_filter_freeze.py.md](docs/ML/benchmark_entry_based_movement_filter_freeze.py.md) |  | 2026-07-20 | 6KB | `89fd386a` |
| [docs/ML/benchmark_entry_based_next_open_closeout.py.md](docs/ML/benchmark_entry_based_next_open_closeout.py.md) |  | 2026-07-20 | 4KB | `07a4b4b8` |
| [docs/ML/benchmark_entry_based_powerful_tabular.py.md](docs/ML/benchmark_entry_based_powerful_tabular.py.md) |  | 2026-07-20 | 2KB | `36dab164` |
| [docs/ML/benchmark_entry_based_sequence_transformer.py.md](docs/ML/benchmark_entry_based_sequence_transformer.py.md) |  | 2026-07-20 | 3KB | `0977f096` |
| [docs/ML/benchmark_entry_based_updn_fractal_selection_ablation.py.md](docs/ML/benchmark_entry_based_updn_fractal_selection_ablation.py.md) |  | 2026-07-20 | 4KB | `69b30968` |
| [docs/ML/benchmark_entry_path_all_rows_ranking.py.md](docs/ML/benchmark_entry_path_all_rows_ranking.py.md) | All-rows ranking benchmark без offline `signal != 0` gate | 2026-06-17 | 1KB | `0bc4a19a` |
| [docs/ML/benchmark_entry_path_causal_surrogate.py.md](docs/ML/benchmark_entry_path_causal_surrogate.py.md) | Causal surrogate benchmark для offline `label_all().signal` | 2026-06-17 | 1KB | `2fd85fde` |
| [docs/ML/benchmark_entry_path_direct_bar_model.py.md](docs/ML/benchmark_entry_path_direct_bar_model.py.md) | Direct BUY/SELL/SKIP benchmark для каждого бара | 2026-06-17 | 1KB | `531300e8` |
| [docs/ML/benchmark_entry_path_signal_only_ablation.py.md](docs/ML/benchmark_entry_path_signal_only_ablation.py.md) | Ablation benchmark вклада offline `signal != 0` | 2026-06-17 | 2KB | `f5a2fa77` |
| [docs/ML/benchmark_execution_policy_v2.py.md](docs/ML/benchmark_execution_policy_v2.py.md) | Benchmark вариантов выхода для готовых ML-сигналов | 2026-06-17 | 4KB | `03bec021` |
| [docs/ML/benchmark_fractal0_entry_exit_grid.py.md](docs/ML/benchmark_fractal0_entry_exit_grid.py.md) |  | 2026-07-29 | 8KB | `980c4582` |
| [docs/ML/benchmark_fractal0_entry_quality_filter.py.md](docs/ML/benchmark_fractal0_entry_quality_filter.py.md) |  | 2026-07-29 | 14KB | `56a42e1e` |
| [docs/ML/benchmark_fractal0_price_entry_mechanics.py.md](docs/ML/benchmark_fractal0_price_entry_mechanics.py.md) |  | 2026-07-20 | 1KB | `ffe4c83f` |
| [docs/ML/benchmark_signal_export_parity.py.md](docs/ML/benchmark_signal_export_parity.py.md) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log | 2026-06-17 | 2KB | `5c430c60` |
| [docs/ML/benchmark_stage4_6_clean_cycle.py.md](docs/ML/benchmark_stage4_6_clean_cycle.py.md) |  | 2026-06-17 | 1KB | `b7950d61` |
| [docs/ML/benchmark_stage5_transformer_breach.py.md](docs/ML/benchmark_stage5_transformer_breach.py.md) |  | 2026-06-29 | 15KB | `3ebbe683` |
| [docs/ML/benchmark_stage6_2_price_action.py.md](docs/ML/benchmark_stage6_2_price_action.py.md) |  | 2026-07-20 | 1KB | `a58e9a24` |
| [docs/ML/benchmark_system_correlation.py.md](docs/ML/benchmark_system_correlation.py.md) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам | 2026-06-17 | 4KB | `a0880c32` |
| [docs/ML/benchmark_take_skip_lib_pic_selection.py.md](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | Внешний отбор `take_skip_v2` по признакам `lib_PIC` | 2026-06-17 | 2KB | `085cc039` |
| [docs/ML/benchmark_telemetry_frequency_calibration.py.md](docs/ML/benchmark_telemetry_frequency_calibration.py.md) | Калибровка частого diagnostic telemetry режима | 2026-06-17 | 2KB | `ca3c7c56` |
| [docs/ML/conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы | 2026-06-17 | 5KB | `dca1ea47` |
| [docs/ML/diagnose_stage4_3.py.md](docs/ML/diagnose_stage4_3.py.md) |  | 2026-06-17 | 2KB | `32c8cbf2` |
| [docs/ML/diagnose_stage4_4.py.md](docs/ML/diagnose_stage4_4.py.md) |  | 2026-06-17 | 2KB | `300d2a52` |
| [docs/ML/diagnose_stage4_5_exit_mechanics.py.md](docs/ML/diagnose_stage4_5_exit_mechanics.py.md) |  | 2026-06-17 | 1KB | `eb573597` |
| [docs/ML/diagnose_stage5_prep.py.md](docs/ML/diagnose_stage5_prep.py.md) |  | 2026-06-17 | 1KB | `c02a4faa` |
| [docs/ML/export_entry_path_predictions.py.md](docs/ML/export_entry_path_predictions.py.md) | Inference entry_path-моделей на arbitrary labeled CSV без переобучения | 2026-06-17 | 4KB | `594cc77b` |
| [docs/ML/feature_bank_comparison_diagnostics.py.md](docs/ML/feature_bank_comparison_diagnostics.py.md) | Сравнение baseline/geometry/path feature-bank вариантов | 2026-06-17 | 2KB | `5bfce017` |
| [docs/ML/feature_importance_diagnostics.py.md](docs/ML/feature_importance_diagnostics.py.md) | Диагностика важности групп текущих fractal-признаков | 2026-06-17 | 2KB | `fd76dcaf` |
| [docs/ML/fractal0_fixed11_internal_closure_rerun.py.md](docs/ML/fractal0_fixed11_internal_closure_rerun.py.md) |  | 2026-07-29 | 2KB | `cbe7c6f0` |
| [docs/ML/fractal_breach_transformer.py.md](docs/ML/fractal_breach_transformer.py.md) |  | 2026-06-20 | 1KB | `46f52377` |
| [docs/ML/lib_pic_feature_profiles.py.md](docs/ML/lib_pic_feature_profiles.py.md) | Единая сборка профилей признаков `lib_PIC` | 2026-06-17 | 2KB | `3947bb49` |
| [docs/ML/lib_pic_geometry_feature_bank.py.md](docs/ML/lib_pic_geometry_feature_bank.py.md) | Производные признаки геометрии уровней `lib_PIC` | 2026-06-17 | 3KB | `1da45c79` |
| [docs/ML/lib_pic_path_reaction_feature_bank.py.md](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | Производные признаки исторической реакции цены `Up/Dn` после уровней | 2026-06-17 | 2KB | `9d18b5e1` |
| [docs/ML/live_safe_audit.py.md](docs/ML/live_safe_audit.py.md) | Core-типы live-safe audit и свод feature verdict → system verdict | 2026-06-17 | 556B | `8341abc1` |
| [docs/ML/live_safe_audit_registry.py.md](docs/ML/live_safe_audit_registry.py.md) | Реестр прибыльных ML-систем для повторного live-safe audit | 2026-06-17 | 469B | `8d81d796` |
| [docs/ML/model_sweep_candidate_source.py.md](docs/ML/model_sweep_candidate_source.py.md) |  | 2026-06-17 | 970B | `8867924b` |
| [docs/ML/neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики | 2026-06-17 | 26KB | `6eca467d` |
| [docs/ML/online_tester_reconciliation.py.md](docs/ML/online_tester_reconciliation.py.md) |  | 2026-06-17 | 3KB | `28aa6c93` |
| [docs/ML/prepare_entry_path_mt4_parity.py.md](docs/ML/prepare_entry_path_mt4_parity.py.md) | Подготовка frozen `entry_path_v1_live_safe + A @ 7.5%` export для MT4 parity | 2026-06-17 | 1KB | `5e881e55` |
| [docs/ML/prune_fractal0_fixed11_mutual_correlation.py.md](docs/ML/prune_fractal0_fixed11_mutual_correlation.py.md) | Read-only pruning 11 fixed Fractal0 rules by mutual overlap | 2026-07-29 | 1KB | `81ee8c21` |
| [docs/ML/run_entry_path_live_safe_retrain.py.md](docs/ML/run_entry_path_live_safe_retrain.py.md) |  | 2026-06-17 | 2KB | `72abe04a` |
| [docs/ML/run_entry_path_quantile_live_safe_retrain.py.md](docs/ML/run_entry_path_quantile_live_safe_retrain.py.md) |  | 2026-06-17 | 2KB | `82076ca6` |
| [docs/ML/run_fractal0_fixed11_rich_entry_locked_test.py.md](docs/ML/run_fractal0_fixed11_rich_entry_locked_test.py.md) |  | 2026-07-29 | 2KB | `663a2e64` |
| [docs/ML/run_live_safe_ml_audit.py.md](docs/ML/run_live_safe_ml_audit.py.md) | CLI для audit inventory, feature trace, legacy replay и verdict | 2026-06-17 | 708B | `445a83ae` |
| [docs/ML/run_take_skip_lib_pic_feature_matrix.py.md](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | Training matrix для `take_skip_v2` с признаками `lib_PIC` внутри модели | 2026-06-17 | 4KB | `8d21f1a7` |
| [docs/ML/run_take_skip_original_contour_feature_matrix.py.md](docs/ML/run_take_skip_original_contour_feature_matrix.py.md) | Training matrix для старого single-tensor `take_skip_v2` контура + `lib_PIC` признаки | 2026-06-17 | 6KB | `133b0f2e` |
| [docs/ML/stage09_stability_refreeze.py.md](docs/ML/stage09_stability_refreeze.py.md) |  | 2026-06-17 | 1KB | `833582b8` |
| [docs/ML/stage10_frozen_test_oos.py.md](docs/ML/stage10_frozen_test_oos.py.md) |  | 2026-06-17 | 1KB | `9fc4ae1d` |
| [docs/ML/telemetry_daily_reconciliation.py.md](docs/ML/telemetry_daily_reconciliation.py.md) | Ежедневная сверка telemetry ML-сигналов и MT4 MLP-логов | 2026-06-17 | 4KB | `b02fd806` |
| [docs/MT/lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC | 2026-06-17 | 8KB | `e40ecf3c` |
| [docs/MT/ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) | 2026-07-29 | 30KB | `663c1deb` |
| [docs/MT/trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() | 2026-07-29 | 51KB | `db3b04db` |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document | 2026-06-17 | 4KB | `dba0c943` |
| [docs/README.md](docs/README.md) | Карта артефактов `docs/` и правила обновления | 2026-07-20 | 4KB | `48d1282c` |
| [docs/audit/2026-05-18-codex-direct-direction-chain-audit.md](docs/audit/2026-05-18-codex-direct-direction-chain-audit.md) |  | 2026-06-17 | 8KB | `4771493f` |
| [docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md](docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md) |  | 2026-06-17 | 6KB | `799c481b` |
| [docs/audit/2026-05-18-consolidated-audit.md](docs/audit/2026-05-18-consolidated-audit.md) |  | 2026-06-17 | 16KB | `68633e6f` |
| [docs/audit/2026-05-18-kimi-independent-audit.md](docs/audit/2026-05-18-kimi-independent-audit.md) |  | 2026-06-17 | 15KB | `7dabafae` |
| [docs/audit/2026-05-18-kimi-phase-ii-plan.md](docs/audit/2026-05-18-kimi-phase-ii-plan.md) |  | 2026-06-17 | 17KB | `74b6b95a` |
| [docs/audit/2026-05-18-redo-prompt.md](docs/audit/2026-05-18-redo-prompt.md) |  | 2026-06-17 | 19KB | `6ca4032a` |
| [docs/audit/2026-05-24-methodology-review-notes.md](docs/audit/2026-05-24-methodology-review-notes.md) | Замечания по `docs/methodology/` и trigger-у `ml-methodology` | 2026-06-17 | 8KB | `6c948cab` |
| [docs/audit/2026-06-09-fractal-stop-fav-target-spec-audit.md](docs/audit/2026-06-09-fractal-stop-fav-target-spec-audit.md) | Вердикт по спецификации Fractal Stop + Fav Target | 2026-06-17 | 16KB | `ac300a57` |
| [docs/audit/2026-06-11-stage4-GLM-audit.md](docs/audit/2026-06-11-stage4-GLM-audit.md) |  | 2026-06-17 | 24KB | `9823cfa7` |
| [docs/audit/2026-06-11-stage4-Qwen-audit.md](docs/audit/2026-06-11-stage4-Qwen-audit.md) |  | 2026-06-17 | 16KB | `9c8be030` |
| [docs/audit/2026-06-11-stage4-trade-xgboost-audit.md](docs/audit/2026-06-11-stage4-trade-xgboost-audit.md) |  | 2026-06-17 | 11KB | `14db190e` |
| [docs/audit/2026-06-14-stage4-brainstorm_GLM.md](docs/audit/2026-06-14-stage4-brainstorm_GLM.md) |  | 2026-06-17 | 4KB | `64bfdac4` |
| [docs/audit/2026-06-14-stage4-brainstorm_Qwen.md](docs/audit/2026-06-14-stage4-brainstorm_Qwen.md) |  | 2026-06-17 | 9KB | `98bed871` |
| [docs/audit/2026-06-14-stage4-brainstorm_codex.md](docs/audit/2026-06-14-stage4-brainstorm_codex.md) |  | 2026-06-17 | 14KB | `b8d6e325` |
| [docs/audit/2026-06-14-stage4-brainstorm_deep.md](docs/audit/2026-06-14-stage4-brainstorm_deep.md) |  | 2026-06-17 | 16KB | `0d8e78b2` |
| [docs/audit/2026-06-14-stage4-brainstorm_mimo.md](docs/audit/2026-06-14-stage4-brainstorm_mimo.md) |  | 2026-06-17 | 7KB | `875a2cfd` |
| [docs/audit/2026-06-14-stage4-brainstorm_result_codex.md](docs/audit/2026-06-14-stage4-brainstorm_result_codex.md) |  | 2026-06-17 | 20KB | `fd09b561` |
| [docs/audit/2026-06-14-stage4-brainstorm_result_deep.md](docs/audit/2026-06-14-stage4-brainstorm_result_deep.md) |  | 2026-06-17 | 12KB | `faaf44f1` |
| [docs/audit/2026-06-30-Вывод-по-Stage-5-6.md](docs/audit/2026-06-30-Вывод-по-Stage-5-6.md) |  | 2026-07-20 | 7KB | `91677d99` |
| [docs/audit/README.md](docs/audit/README.md) | Карта audit-артефактов и правил их обновления | 2026-06-17 | 1KB | `67407e17` |
| [docs/audit/next.md](docs/audit/next.md) | Текущий research-план после Stage 4.3 | 2026-07-20 | 6KB | `eee5c1aa` |
| [docs/audit/project_structure_modernisation.md](docs/audit/project_structure_modernisation.md) |  | 2026-07-20 | 5KB | `d94835a0` |
| [docs/audit/to_do.md](docs/audit/to_do.md) |  | 2026-07-21 | 30KB | `5f0824a6` |
| [docs/dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv | 2026-06-17 | 14KB | `11dc384e` |
| [docs/methodology/00-research-management.md](docs/methodology/00-research-management.md) |  | 2026-07-20 | 10KB | `96323966` |
| [docs/methodology/01-raw-data-inventory.md](docs/methodology/01-raw-data-inventory.md) |  | 2026-07-29 | 6KB | `e4dad714` |
| [docs/methodology/02-data-pipeline.md](docs/methodology/02-data-pipeline.md) |  | 2026-07-20 | 7KB | `3edd87b0` |
| [docs/methodology/03-feature-contract-leakage.md](docs/methodology/03-feature-contract-leakage.md) |  | 2026-07-20 | 31KB | `a1757847` |
| [docs/methodology/03b-feature-selection.md](docs/methodology/03b-feature-selection.md) |  | 2026-06-20 | 6KB | `13a28e56` |
| [docs/methodology/04-labeling.md](docs/methodology/04-labeling.md) |  | 2026-07-20 | 10KB | `b6ff44a6` |
| [docs/methodology/05-eda-data-quality.md](docs/methodology/05-eda-data-quality.md) |  | 2026-07-20 | 7KB | `345e9aa3` |
| [docs/methodology/06-temporal-split.md](docs/methodology/06-temporal-split.md) |  | 2026-07-20 | 9KB | `23deff38` |
| [docs/methodology/06b-oracle-preflight.md](docs/methodology/06b-oracle-preflight.md) | Предварительная oracle-проверка теоретического потолка торговой постановки | 2026-07-20 | 9KB | `da8d2f19` |
| [docs/methodology/07-baseline-first.md](docs/methodology/07-baseline-first.md) |  | 2026-07-20 | 5KB | `5446b875` |
| [docs/methodology/08-model-development.md](docs/methodology/08-model-development.md) |  | 2026-07-20 | 15KB | `8f893540` |
| [docs/methodology/09-validation-freeze.md](docs/methodology/09-validation-freeze.md) |  | 2026-07-29 | 11KB | `d394dfe6` |
| [docs/methodology/10-frozen-test-oos.md](docs/methodology/10-frozen-test-oos.md) |  | 2026-07-20 | 3KB | `17fd2a84` |
| [docs/methodology/11-robustness.md](docs/methodology/11-robustness.md) |  | 2026-07-20 | 11KB | `bf60036a` |
| [docs/methodology/12-backtest-costs.md](docs/methodology/12-backtest-costs.md) |  | 2026-07-29 | 12KB | `03a3ec5a` |
| [docs/methodology/13-export-mt4-parity.md](docs/methodology/13-export-mt4-parity.md) |  | 2026-07-29 | 5KB | `2f0c7aa0` |
| [docs/methodology/13b-mt5-execution-parity.md](docs/methodology/13b-mt5-execution-parity.md) |  | 2026-07-30 | 8KB | `4bd789b2` |
| [docs/methodology/14-forward-test-online.md](docs/methodology/14-forward-test-online.md) |  | 2026-07-20 | 2KB | `25d2c512` |
| [docs/methodology/15-monitoring-retraining.md](docs/methodology/15-monitoring-retraining.md) |  | 2026-07-20 | 3KB | `c463688b` |
| [docs/methodology/16-reporting-audit.md](docs/methodology/16-reporting-audit.md) |  | 2026-07-20 | 8KB | `33c362bc` |
| [docs/methodology/A1-checklist-dev.md](docs/methodology/A1-checklist-dev.md) |  | 2026-07-20 | 3KB | `1adbbef0` |
| [docs/methodology/A2-checklist-audit.md](docs/methodology/A2-checklist-audit.md) |  | 2026-07-20 | 5KB | `fa741eb4` |
| [docs/methodology/A3-typical-false-conclusions.md](docs/methodology/A3-typical-false-conclusions.md) |  | 2026-07-20 | 5KB | `0b8f610b` |
| [docs/methodology/A4-verdicts-stop-conditions.md](docs/methodology/A4-verdicts-stop-conditions.md) |  | 2026-07-20 | 5KB | `5c52891f` |
| [docs/methodology/A5-post-mortem-diagnostics.md](docs/methodology/A5-post-mortem-diagnostics.md) | Post-mortem диагностика FAIL/reject | 2026-07-20 | 30KB | `1fe0bd1d` |
| [docs/methodology/A6-fractal-feature-profile-catalog.md](docs/methodology/A6-fractal-feature-profile-catalog.md) | Каталог fractal feature profiles | 2026-07-20 | 15KB | `968752dc` |
| [docs/methodology/A7-feature-distribution-audit.md](docs/methodology/A7-feature-distribution-audit.md) |  | 2026-07-20 | 17KB | `4e827324` |
| [docs/methodology/A8-feature-target-catalog.md](docs/methodology/A8-feature-target-catalog.md) |  | 2026-07-20 | 19KB | `c3844712` |
| [docs/methodology/README.md](docs/methodology/README.md) | Методика разработки и аудита ML-моделей ТС (16 этапов + oracle-preflight + приложения) | 2026-07-29 | 9KB | `b05aa54b` |
| [docs/processing/fractal_preprocessing.py.md](docs/processing/fractal_preprocessing.py.md) | Документация общей сортировки фракталов | 2026-06-17 | 856B | `876e71c9` |
| [docs/processing/label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора | 2026-06-17 | 4KB | `22a08f92` |
| [docs/processing/label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict | 2026-06-17 | 2KB | `8f996d16` |
| [docs/processing/normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков | 2026-06-17 | 5KB | `5e8f661c` |
| [docs/processing/online_causal_preprocessing.py.md](docs/processing/online_causal_preprocessing.py.md) | Документация online-safe preprocessing | 2026-06-17 | 2KB | `a59d1bf7` |
| [docs/schemas/fractal_v23.schema.json](docs/schemas/fractal_v23.schema.json) |  | 2026-06-17 | 4KB | `deb79fbb` |
| [docs/schemas/fractal_v24_raw_price.schema.json](docs/schemas/fractal_v24_raw_price.schema.json) |  | 2026-06-17 | 5KB | `e3539efe` |
| [docs/schemas/mt5_nero_csv_contract.md](docs/schemas/mt5_nero_csv_contract.md) |  | 2026-07-31 | 2KB | `84b44f2b` |
| [docs/schemas/mt5_open_position_feature_contract.md](docs/schemas/mt5_open_position_feature_contract.md) |  | 2026-07-30 | 2KB | `dda9fc21` |
| [docs/statistics/EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу | 2026-06-17 | 17KB | `914b3a5e` |
| [docs/statistics/signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF | 2026-06-17 | 7KB | `052eb4f7` |
| [docs/statistics/statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике | 2026-06-17 | 6KB | `9835a477` |
| [docs/superpowers/README.md](docs/superpowers/README.md) |  | 2026-06-24 | 1KB | `46894f42` |
| [docs/superpowers/audit.md](docs/superpowers/audit.md) |  | 2026-08-01 | 18KB | `f6532cba` |
| [docs/superpowers/plans/2026-03-22-triple-barrier.md](docs/superpowers/plans/2026-03-22-triple-barrier.md) |  | 2026-06-17 | 28KB | `fe31fa4e` |
| [docs/superpowers/plans/2026-03-25-updn-denormalization.md](docs/superpowers/plans/2026-03-25-updn-denormalization.md) |  | 2026-06-17 | 19KB | `01d8efee` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md) |  | 2026-06-17 | 22KB | `ba50388e` |
| [docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md) |  | 2026-06-17 | 9KB | `7ed11b5f` |
| [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](docs/superpowers/plans/2026-04-01-signal-research-variant-2.md) |  | 2026-06-17 | 29KB | `09aa7ec8` |
| [docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md](docs/superpowers/plans/2026-04-02-layered-context-stage-reporting.md) |  | 2026-06-17 | 20KB | `43d44dc5` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-06-17 | 19KB | `b25009ee` |
| [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](docs/superpowers/plans/2026-04-02-signal-research-variant-3.md) |  | 2026-06-17 | 3KB | `3b40fae8` |
| [docs/superpowers/plans/2026-04-03-signal-path-atlas.md](docs/superpowers/plans/2026-04-03-signal-path-atlas.md) |  | 2026-06-17 | 39KB | `b0fea2ba` |
| [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](docs/superpowers/plans/2026-04-03-signal-quality-filter.md) |  | 2026-06-17 | 39KB | `6518f11b` |
| [docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md](docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md) |  | 2026-06-17 | 7KB | `636d1a67` |
| [docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md](docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md) |  | 2026-06-17 | 7KB | `af4ec829` |
| [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md) |  | 2026-06-17 | 11KB | `44d803a8` |
| [docs/superpowers/plans/2026-04-07-validation-first-research.md](docs/superpowers/plans/2026-04-07-validation-first-research.md) |  | 2026-06-17 | 10KB | `c0b29ff8` |
| [docs/superpowers/plans/2026-04-08-entry-path-v1.md](docs/superpowers/plans/2026-04-08-entry-path-v1.md) |  | 2026-06-17 | 28KB | `86fb358e` |
| [docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md](docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-06-17 | 15KB | `e9cb346d` |
| [docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md](docs/superpowers/plans/2026-04-09-entry-path-conformal-filter.md) |  | 2026-06-17 | 22KB | `0a35f491` |
| [docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md](docs/superpowers/plans/2026-04-09-entry-path-trade-filter.md) |  | 2026-06-17 | 29KB | `1ab66152` |
| [docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md](docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md) |  | 2026-06-17 | 26KB | `9b5a8151` |
| [docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md](docs/superpowers/plans/2026-04-10-entry-path-adaptive-conformal.md) |  | 2026-06-17 | 31KB | `155a7325` |
| [docs/superpowers/plans/2026-04-10-entry-path-cqr.md](docs/superpowers/plans/2026-04-10-entry-path-cqr.md) |  | 2026-06-17 | 24KB | `0f832c74` |
| [docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md](docs/superpowers/plans/2026-04-10-llm-wiki-improvements.md) |  | 2026-06-17 | 15KB | `fe2b2167` |
| [docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md](docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md) |  | 2026-06-17 | 14KB | `5b49271e` |
| [docs/superpowers/plans/2026-04-13-early-timeout-bar12.md](docs/superpowers/plans/2026-04-13-early-timeout-bar12.md) |  | 2026-06-17 | 37KB | `908866bf` |
| [docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md](docs/superpowers/plans/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-06-17 | 20KB | `80750ee6` |
| [docs/superpowers/plans/2026-04-13-label-convention-audit.md](docs/superpowers/plans/2026-04-13-label-convention-audit.md) |  | 2026-06-17 | 31KB | `ea55d54a` |
| [docs/superpowers/plans/2026-04-13-ny-session-filter.md](docs/superpowers/plans/2026-04-13-ny-session-filter.md) |  | 2026-06-17 | 2KB | `325f4e90` |
| [docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md](docs/superpowers/plans/2026-04-13-pf-uplift-beyond-ml.md) |  | 2026-06-17 | 29KB | `74578dba` |
| [docs/superpowers/plans/2026-04-13-pred-adv-cap.md](docs/superpowers/plans/2026-04-13-pred-adv-cap.md) |  | 2026-06-17 | 2KB | `51f3e15c` |
| [docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md](docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md) |  | 2026-06-17 | 15KB | `50a68d1f` |
| [docs/superpowers/plans/2026-04-13-quantile-fav-composition.md](docs/superpowers/plans/2026-04-13-quantile-fav-composition.md) |  | 2026-06-17 | 25KB | `20186b5d` |
| [docs/superpowers/plans/2026-04-13-quantile-forward-validation.md](docs/superpowers/plans/2026-04-13-quantile-forward-validation.md) |  | 2026-06-17 | 13KB | `e4d63c4c` |
| [docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md](docs/superpowers/plans/2026-04-15-direct-trade-decision-model.md) |  | 2026-06-17 | 11KB | `cfa70650` |
| [docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md](docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md) |  | 2026-06-17 | 18KB | `2d48d389` |
| [docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md](docs/superpowers/plans/2026-04-15-relaxed-baseline-composition.md) |  | 2026-06-17 | 21KB | `7c99ab9c` |
| [docs/superpowers/plans/2026-04-15-track-a-max-out.md](docs/superpowers/plans/2026-04-15-track-a-max-out.md) |  | 2026-06-17 | 27KB | `4a83f18e` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md) |  | 2026-06-17 | 31KB | `a6f904f0` |
| [docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md](docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md) |  | 2026-06-17 | 21KB | `2085188e` |
| [docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md](docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md) |  | 2026-06-17 | 15KB | `3a35bea9` |
| [docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md](docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md) |  | 2026-06-17 | 32KB | `98abca8c` |
| [docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md](docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-06-17 | 2KB | `0617b8a6` |
| [docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md](docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md) |  | 2026-06-17 | 9KB | `a6b6e6e9` |
| [docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md](docs/superpowers/plans/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-06-17 | 2KB | `d3f1a358` |
| [docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md](docs/superpowers/plans/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-06-17 | 2KB | `23a84682` |
| [docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md](docs/superpowers/plans/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-06-17 | 6KB | `35ba356d` |
| [docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-06-17 | 2KB | `53f8ce75` |
| [docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/superpowers/plans/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-06-17 | 2KB | `e0278dfc` |
| [docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md](docs/superpowers/plans/2026-04-20-lib-pic-feature-training-track.md) |  | 2026-06-17 | 5KB | `c19d12dc` |
| [docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md](docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md) |  | 2026-06-17 | 14KB | `c5fafc2a` |
| [docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md](docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md) |  | 2026-06-17 | 18KB | `773510b6` |
| [docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md](docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md) |  | 2026-06-17 | 12KB | `9dce2437` |
| [docs/superpowers/plans/2026-04-24-system-correlation-and-portfolio-check.md](docs/superpowers/plans/2026-04-24-system-correlation-and-portfolio-check.md) |  | 2026-06-17 | 15KB | `5f85893f` |
| [docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md](docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md) |  | 2026-06-17 | 25KB | `115736bf` |
| [docs/superpowers/plans/2026-05-05-live-safe-ml-audit.md](docs/superpowers/plans/2026-05-05-live-safe-ml-audit.md) |  | 2026-06-17 | 12KB | `b588445d` |
| [docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md](docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md) | План реализации live-safe `signal_candidate` по всей строке фракталов | 2026-06-17 | 38KB | `e504adff` |
| [docs/superpowers/plans/2026-05-15-entry-path-fractal-level-direct-direction.md](docs/superpowers/plans/2026-05-15-entry-path-fractal-level-direct-direction.md) | План реализации direct `SELL/SKIP/BUY` модели по всей строке фракталов | 2026-06-17 | 20KB | `8c855590` |
| [docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md](docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md) |  | 2026-06-17 | 29KB | `fda9e697` |
| [docs/superpowers/plans/2026-05-21-transformer-encoder-direction.md](docs/superpowers/plans/2026-05-21-transformer-encoder-direction.md) |  | 2026-06-17 | 12KB | `82edd7a2` |
| [docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md](docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md) |  | 2026-06-17 | 54KB | `5177783b` |
| [docs/superpowers/plans/2026-05-30-limit-order-hypothesis-testing.md](docs/superpowers/plans/2026-05-30-limit-order-hypothesis-testing.md) |  | 2026-06-17 | 10KB | `0759cd9a` |
| [docs/superpowers/plans/2026-06-01-feature-foundation-rebuild.md](docs/superpowers/plans/2026-06-01-feature-foundation-rebuild.md) |  | 2026-06-17 | 23KB | `182d5eea` |
| [docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md](docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md) | План Stage 1 Fractal Stop Breach: разметка пробоя уровня, baseline и frozen test | 2026-06-17 | 40KB | `2e962d0d` |
| [docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md](docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md) | План Stage 2 Fractal Stop + Fav Target: торговый слой поверх breach-сигнала | 2026-06-17 | 38KB | `c6c34f52` |
| [docs/superpowers/plans/2026-06-14-stage4_3-diagnostics.md](docs/superpowers/plans/2026-06-14-stage4_3-diagnostics.md) |  | 2026-06-17 | 28KB | `80ec1ba1` |
| [docs/superpowers/plans/2026-06-15-stage4_4-micro-check.md](docs/superpowers/plans/2026-06-15-stage4_4-micro-check.md) |  | 2026-06-17 | 27KB | `d3b5dc25` |
| [docs/superpowers/plans/2026-06-15-stage4_5-trailing-partial-exit.md](docs/superpowers/plans/2026-06-15-stage4_5-trailing-partial-exit.md) |  | 2026-06-17 | 7KB | `273125e8` |
| [docs/superpowers/plans/2026-06-15-stage4_6-clean-candidate-cycle.md](docs/superpowers/plans/2026-06-15-stage4_6-clean-candidate-cycle.md) |  | 2026-06-17 | 6KB | `12342f1d` |
| [docs/superpowers/plans/2026-06-15-stage4_remaining-hypotheses-master.md](docs/superpowers/plans/2026-06-15-stage4_remaining-hypotheses-master.md) |  | 2026-06-17 | 9KB | `cc159e05` |
| [docs/superpowers/plans/2026-06-15-stage5_prep-diagnostics.md](docs/superpowers/plans/2026-06-15-stage5_prep-diagnostics.md) |  | 2026-06-17 | 7KB | `136f54dc` |
| [docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md](docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md) | План Stage 5.0 Transformer Breach | 2026-06-20 | 30KB | `bae3c711` |
| [docs/superpowers/plans/2026-06-18-stage5_0a-corridor-full-preflight.md](docs/superpowers/plans/2026-06-18-stage5_0a-corridor-full-preflight.md) | План Stage 5.0a Corridor Full Preflight | 2026-06-20 | 14KB | `ef48d3ce` |
| [docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md](docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md) | План Stage 5.0a Feature Preflight: A7-аудит профилей признаков до повторного обучения Transformer | 2026-06-20 | 16KB | `b6cad904` |
| [docs/superpowers/plans/2026-06-21-stage5_0a-transform-comparison.md](docs/superpowers/plans/2026-06-21-stage5_0a-transform-comparison.md) |  | 2026-06-24 | 3KB | `93189c70` |
| [docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md](docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md) |  | 2026-06-24 | 31KB | `6962ea4f` |
| [docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md](docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md) |  | 2026-06-24 | 55KB | `17c2f7c1` |
| [docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md](docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md) |  | 2026-06-24 | 46KB | `581c76bc` |
| [docs/superpowers/plans/2026-06-23-stage5_0e-small-transformer-overfit-check.md](docs/superpowers/plans/2026-06-23-stage5_0e-small-transformer-overfit-check.md) |  | 2026-06-24 | 18KB | `4168bc01` |
| [docs/superpowers/plans/2026-06-23-stage5_0f-signal-stationarity.md](docs/superpowers/plans/2026-06-23-stage5_0f-signal-stationarity.md) |  | 2026-06-24 | 57KB | `215639fb` |
| [docs/superpowers/plans/2026-06-24-stage5_1-structural-field-ablation.md](docs/superpowers/plans/2026-06-24-stage5_1-structural-field-ablation.md) |  | 2026-06-29 | 61KB | `206eeaa5` |
| [docs/superpowers/plans/2026-06-24-stage5_1b-updn-field-ablation.md](docs/superpowers/plans/2026-06-24-stage5_1b-updn-field-ablation.md) |  | 2026-06-29 | 72KB | `c0fac99a` |
| [docs/superpowers/plans/2026-06-25-stage5_2-time-to-breach-regression.md](docs/superpowers/plans/2026-06-25-stage5_2-time-to-breach-regression.md) |  | 2026-06-29 | 57KB | `db7d429b` |
| [docs/superpowers/plans/2026-06-26-stage5_3-time-to-breach-target-reformulation.md](docs/superpowers/plans/2026-06-26-stage5_3-time-to-breach-target-reformulation.md) |  | 2026-06-29 | 53KB | `ff2c4787` |
| [docs/superpowers/plans/2026-06-29-stage5_4-fast-price-atr-ablation.md](docs/superpowers/plans/2026-06-29-stage5_4-fast-price-atr-ablation.md) |  | 2026-06-29 | 71KB | `e8302278` |
| [docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md](docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md) |  | 2026-07-20 | 59KB | `0938de7a` |
| [docs/superpowers/plans/2026-06-29-stage6_1-baseline-plus-geometry-delta.md](docs/superpowers/plans/2026-06-29-stage6_1-baseline-plus-geometry-delta.md) |  | 2026-07-20 | 18KB | `44ae1cf9` |
| [docs/superpowers/plans/2026-06-29-stage6_1-h12-relative-fractal-geometry.md](docs/superpowers/plans/2026-06-29-stage6_1-h12-relative-fractal-geometry.md) |  | 2026-07-20 | 51KB | `9a0874f6` |
| [docs/superpowers/plans/2026-06-30-regression-updn-target-foundation.md](docs/superpowers/plans/2026-06-30-regression-updn-target-foundation.md) |  | 2026-07-20 | 30KB | `e53b90e4` |
| [docs/superpowers/plans/2026-06-30-stage6_2-h12-price-action-feature-family.md](docs/superpowers/plans/2026-06-30-stage6_2-h12-price-action-feature-family.md) |  | 2026-07-20 | 60KB | `83351232` |
| [docs/superpowers/plans/2026-06-30-stage6_2-range-w1-postmortem.md](docs/superpowers/plans/2026-06-30-stage6_2-range-w1-postmortem.md) |  | 2026-07-20 | 36KB | `29a57550` |
| [docs/superpowers/plans/2026-06-30-stage6_3-h6-feature-parity-check.md](docs/superpowers/plans/2026-06-30-stage6_3-h6-feature-parity-check.md) |  | 2026-07-20 | 9KB | `77ba0972` |
| [docs/superpowers/plans/2026-07-02-entry-based-updn-price-feature-matrix.md](docs/superpowers/plans/2026-07-02-entry-based-updn-price-feature-matrix.md) |  | 2026-07-20 | 22KB | `467bd49b` |
| [docs/superpowers/plans/2026-07-02-next-open-entry-updn-foundation.md](docs/superpowers/plans/2026-07-02-next-open-entry-updn-foundation.md) |  | 2026-07-20 | 22KB | `44b4a44c` |
| [docs/superpowers/plans/2026-07-02-regression-updn-already-moved-audit.md](docs/superpowers/plans/2026-07-02-regression-updn-already-moved-audit.md) |  | 2026-07-20 | 57KB | `085a51d6` |
| [docs/superpowers/plans/2026-07-03-fractal-selection-ablation-entry-based-target.md](docs/superpowers/plans/2026-07-03-fractal-selection-ablation-entry-based-target.md) |  | 2026-07-20 | 34KB | `b3050713` |
| [docs/superpowers/plans/2026-07-04-entry-based-next-open-closeout.md](docs/superpowers/plans/2026-07-04-entry-based-next-open-closeout.md) |  | 2026-07-20 | 49KB | `4e328f17` |
| [docs/superpowers/plans/2026-07-05-entry-based-powerful-tabular-models.md](docs/superpowers/plans/2026-07-05-entry-based-powerful-tabular-models.md) |  | 2026-07-20 | 63KB | `2df74471` |
| [docs/superpowers/plans/2026-07-06-entry-based-fractal-sequence-transformer.md](docs/superpowers/plans/2026-07-06-entry-based-fractal-sequence-transformer.md) |  | 2026-07-20 | 44KB | `a90560aa` |
| [docs/superpowers/plans/2026-07-07-entry-based-amplitude-movement-regime-audit.md](docs/superpowers/plans/2026-07-07-entry-based-amplitude-movement-regime-audit.md) |  | 2026-07-20 | 72KB | `6cc1d967` |
| [docs/superpowers/plans/2026-07-07-entry-based-movement-filter-design.md](docs/superpowers/plans/2026-07-07-entry-based-movement-filter-design.md) |  | 2026-07-20 | 20KB | `15fae646` |
| [docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md](docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md) |  | 2026-07-20 | 19KB | `cd9c7d72` |
| [docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md](docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md) |  | 2026-07-20 | 55KB | `76b5b4e7` |
| [docs/superpowers/plans/2026-07-08-entry-based-movement-filter-replication-freeze.md](docs/superpowers/plans/2026-07-08-entry-based-movement-filter-replication-freeze.md) |  | 2026-07-20 | 30KB | `e3869a19` |
| [docs/superpowers/plans/2026-07-10-direction-inside-frozen-mask-narrow-replication.md](docs/superpowers/plans/2026-07-10-direction-inside-frozen-mask-narrow-replication.md) |  | 2026-07-20 | 41KB | `5647980d` |
| [docs/superpowers/plans/2026-07-10-fractal0-price-entry-mechanics.md](docs/superpowers/plans/2026-07-10-fractal0-price-entry-mechanics.md) |  | 2026-07-20 | 55KB | `a3ae710a` |
| [docs/superpowers/plans/2026-07-10-research-first-methodology-sync.md](docs/superpowers/plans/2026-07-10-research-first-methodology-sync.md) |  | 2026-07-20 | 17KB | `9c8ea4c0` |
| [docs/superpowers/plans/2026-07-20-fractal0-entry-exit-grid.md](docs/superpowers/plans/2026-07-20-fractal0-entry-exit-grid.md) |  | 2026-07-29 | 60KB | `61bf4737` |
| [docs/superpowers/plans/2026-07-21-fractal0-entry-quality-filter.md](docs/superpowers/plans/2026-07-21-fractal0-entry-quality-filter.md) |  | 2026-07-29 | 25KB | `aef9533b` |
| [docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md](docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md) |  | 2026-07-29 | 59KB | `4f1c49f6` |
| [docs/superpowers/plans/2026-07-21-fractal0-stop-grid-m5.md](docs/superpowers/plans/2026-07-21-fractal0-stop-grid-m5.md) |  | 2026-07-29 | 25KB | `58b0a6e6` |
| [docs/superpowers/plans/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md](docs/superpowers/plans/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md) |  | 2026-07-29 | 81KB | `e2847072` |
| [docs/superpowers/plans/2026-07-22-fractal0-rich-entry-shortlist-replication-probe.md](docs/superpowers/plans/2026-07-22-fractal0-rich-entry-shortlist-replication-probe.md) |  | 2026-07-29 | 14KB | `07746cec` |
| [docs/superpowers/plans/2026-07-23-fractal0-fixed11-internal-closure-rerun.md](docs/superpowers/plans/2026-07-23-fractal0-fixed11-internal-closure-rerun.md) |  | 2026-07-29 | 61KB | `c5276367` |
| [docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md](docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md) |  | 2026-07-29 | 32KB | `721c5f02` |
| [docs/superpowers/plans/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md](docs/superpowers/plans/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md) |  | 2026-07-29 | 54KB | `fc6a5e9a` |
| [docs/superpowers/plans/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md](docs/superpowers/plans/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md) |  | 2026-07-29 | 80KB | `32dd4131` |
| [docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md](docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md) |  | 2026-07-29 | 53KB | `958b565b` |
| [docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md](docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md) |  | 2026-07-29 | 15KB | `e52b9233` |
| [docs/superpowers/plans/2026-07-27-fixed11-mutual-correlation-pruning.md](docs/superpowers/plans/2026-07-27-fixed11-mutual-correlation-pruning.md) |  | 2026-07-29 | 14KB | `ac1038f1` |
| [docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md](docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md) |  | 2026-07-29 | 31KB | `8a7257f3` |
| [docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md](docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md) |  | 2026-07-29 | 29KB | `1503352f` |
| [docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md](docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md) |  | 2026-07-29 | 63KB | `550fbc1e` |
| [docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md](docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md) |  | 2026-07-30 | 64KB | `2ea9a4e9` |
| [docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md](docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md) |  | 2026-07-31 | 22KB | `fa284fa8` |
| [docs/superpowers/plans/2026-07-31-mt5-batch-selection.md](docs/superpowers/plans/2026-07-31-mt5-batch-selection.md) |  | 2026-08-01 | 23KB | `4038a63f` |
| [docs/superpowers/plans/2026-07-31-mt5-nero-parity-v2.md](docs/superpowers/plans/2026-07-31-mt5-nero-parity-v2.md) |  | 2026-07-31 | 3KB | `590be343` |
| [docs/superpowers/plans/2026-07-31-mt5-nero-parity.md](docs/superpowers/plans/2026-07-31-mt5-nero-parity.md) |  | 2026-07-31 | 23KB | `5da03558` |
| [docs/superpowers/plans/2026-07-31-mt5-ontradetransaction-lifecycle.md](docs/superpowers/plans/2026-07-31-mt5-ontradetransaction-lifecycle.md) |  | 2026-07-31 | 10KB | `ceb6bd5a` |
| [docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md](docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md) |  | 2026-08-01 | 49KB | `dedc6303` |
| [docs/superpowers/plans/ME13_Diagnostics_Plan.md](docs/superpowers/plans/ME13_Diagnostics_Plan.md) |  | 2026-06-17 | 5KB | `10a0c4ea` |
| [docs/superpowers/roadmap.md](docs/superpowers/roadmap.md) |  | 2026-08-01 | 7KB | `064b82a7` |
| [docs/superpowers/specs/2026-03-22-triple-barrier-design.md](docs/superpowers/specs/2026-03-22-triple-barrier-design.md) |  | 2026-06-17 | 12KB | `82b0860f` |
| [docs/superpowers/specs/2026-03-27-pf-improvement-design.md](docs/superpowers/specs/2026-03-27-pf-improvement-design.md) |  | 2026-06-17 | 18KB | `85d548d9` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md) |  | 2026-06-17 | 13KB | `477a2843` |
| [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md) |  | 2026-06-17 | 10KB | `db9fb094` |
| [docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md](docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md) |  | 2026-06-17 | 21KB | `dcb5dcd3` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md) |  | 2026-06-17 | 3KB | `15368fbf` |
| [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md) |  | 2026-06-17 | 10KB | `88d9ca83` |
| [docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md](docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md) |  | 2026-06-17 | 10KB | `81b0a31f` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md) |  | 2026-06-17 | 8KB | `60e115b4` |
| [docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md](docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md) |  | 2026-06-17 | 7KB | `119b59e0` |
| [docs/superpowers/specs/2026-04-08-entry-path-v1-design.md](docs/superpowers/specs/2026-04-08-entry-path-v1-design.md) |  | 2026-06-17 | 17KB | `deafd06e` |
| [docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-conformal-filter-design.md) |  | 2026-06-17 | 12KB | `e771d628` |
| [docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md](docs/superpowers/specs/2026-04-09-entry-path-trade-filter-design.md) |  | 2026-06-17 | 12KB | `402001b6` |
| [docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md](docs/superpowers/specs/2026-04-10-entry-path-cqr-design.md) |  | 2026-06-17 | 12KB | `1a877fcd` |
| [docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md](docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md) |  | 2026-06-17 | 13KB | `2ef88bef` |
| [docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md](docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md) |  | 2026-06-17 | 8KB | `8272fe58` |
| [docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md](docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md) |  | 2026-06-17 | 7KB | `7fede3fc` |
| [docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md](docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md) |  | 2026-06-17 | 6KB | `f1f6cae8` |
| [docs/superpowers/specs/2026-04-15-quantile-next-research-design.md](docs/superpowers/specs/2026-04-15-quantile-next-research-design.md) |  | 2026-06-17 | 20KB | `8ac77369` |
| [docs/superpowers/specs/2026-04-15-track-a-max-out-design.md](docs/superpowers/specs/2026-04-15-track-a-max-out-design.md) |  | 2026-06-17 | 12KB | `2b4ee2f7` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md) |  | 2026-06-17 | 13KB | `299a938f` |
| [docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md](docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md) |  | 2026-06-17 | 10KB | `48c918e2` |
| [docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md](docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md) |  | 2026-06-17 | 7KB | `0f97c51d` |
| [docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md](docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md) |  | 2026-06-17 | 7KB | `f7f0940d` |
| [docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md](docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md) |  | 2026-06-17 | 17KB | `b852c2fa` |
| [docs/superpowers/specs/2026-04-28-central-inference-service-design.md](docs/superpowers/specs/2026-04-28-central-inference-service-design.md) |  | 2026-06-17 | 7KB | `ecc8e915` |
| [docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md](docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md) |  | 2026-06-17 | 13KB | `b3d2235f` |
| [docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md](docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md) | Спецификация поиска live-safe `signal_candidate` по всей строке фракталов | 2026-06-17 | 43KB | `d9f3365c` |
| [docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md](docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md) | Спецификация direct `SELL/SKIP/BUY` модели по всей строке фракталов | 2026-06-17 | 12KB | `3bba26aa` |
| [docs/superpowers/specs/2026-05-27-limit-order-entry-design.md](docs/superpowers/specs/2026-05-27-limit-order-entry-design.md) |  | 2026-06-17 | 18KB | `1c33e671` |
| [docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md](docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md) | Спецификация Fractal Stop + Fav Target: этап только на пробой уровня и торговый слой | 2026-06-17 | 17KB | `44df96a5` |
| [docs/superpowers/specs/2026-06-23-stage5_0f-signal-stationarity-design.md](docs/superpowers/specs/2026-06-23-stage5_0f-signal-stationarity-design.md) |  | 2026-06-24 | 22KB | `7e3289aa` |
| [docs/superpowers/specs/2026-06-24-stage5_1-structural-fractal-field-ablation-design.md](docs/superpowers/specs/2026-06-24-stage5_1-structural-fractal-field-ablation-design.md) |  | 2026-06-29 | 18KB | `7c2d03a8` |
| [docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md](docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md) |  | 2026-06-29 | 32KB | `942aba53` |
| [docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md](docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md) |  | 2026-06-29 | 23KB | `8c41f47b` |
| [docs/superpowers/specs/2026-06-29-stage6_1-baseline-plus-geometry-delta-design.md](docs/superpowers/specs/2026-06-29-stage6_1-baseline-plus-geometry-delta-design.md) |  | 2026-07-20 | 3KB | `ad0ca2f6` |
| [docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md](docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md) |  | 2026-07-20 | 11KB | `5731ade6` |
| [docs/superpowers/specs/2026-07-10-research-first-methodology-redesign.md](docs/superpowers/specs/2026-07-10-research-first-methodology-redesign.md) |  | 2026-07-20 | 16KB | `8fa556cd` |
| [docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md](docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md) |  | 2026-07-29 | 31KB | `b684a5b7` |
| [docs/superpowers/specs/2026-07-21-fractal0-rich-entry-quality-design.md](docs/superpowers/specs/2026-07-21-fractal0-rich-entry-quality-design.md) |  | 2026-07-29 | 26KB | `f4a00cfe` |
| [docs/tests/tests.md](docs/tests/tests.md) |  | 2026-07-20 | 15KB | `f69190cc` |

## Reports

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md) |  | 2026-06-17 | 5KB | `37b9ec88` |
| [docs/reports/2026-04-02-signal-research-variant-3-prep.md](docs/reports/2026-04-02-signal-research-variant-3-prep.md) |  | 2026-06-17 | 12KB | `d26a9270` |
| [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md) |  | 2026-06-17 | 15KB | `98244916` |
| [docs/reports/2026-04-03-signal-path-atlas.md](docs/reports/2026-04-03-signal-path-atlas.md) |  | 2026-06-17 | 8KB | `c68aa3b8` |
| [docs/reports/2026-04-04-archetype-filter-bridge.md](docs/reports/2026-04-04-archetype-filter-bridge.md) |  | 2026-06-17 | 14KB | `28e2bd45` |
| [docs/reports/2026-04-04-signal-path-atlas-readout.md](docs/reports/2026-04-04-signal-path-atlas-readout.md) |  | 2026-06-17 | 25KB | `fbfedb40` |
| [docs/reports/2026-04-04-signal-quality-filter.md](docs/reports/2026-04-04-signal-quality-filter.md) |  | 2026-06-17 | 12KB | `e2e74751` |
| [docs/reports/2026-04-08-entry-path-v1-baseline.md](docs/reports/2026-04-08-entry-path-v1-baseline.md) |  | 2026-06-17 | 10KB | `ff56ac36` |
| [docs/reports/2026-04-08-ml-exit-validation-first.md](docs/reports/2026-04-08-ml-exit-validation-first.md) |  | 2026-06-17 | 8KB | `f61986e3` |
| [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md) |  | 2026-06-17 | 8KB | `1783da26` |
| [docs/reports/2026-04-08-triple-barrier-hardening.md](docs/reports/2026-04-08-triple-barrier-hardening.md) |  | 2026-06-17 | 8KB | `ec8f88b7` |
| [docs/reports/2026-04-08-triple-barrier-runtime-verdict.md](docs/reports/2026-04-08-triple-barrier-runtime-verdict.md) |  | 2026-06-17 | 9KB | `33e1602a` |
| [docs/reports/2026-04-09-entry-path-trade-filter.md](docs/reports/2026-04-09-entry-path-trade-filter.md) |  | 2026-06-17 | 10KB | `8553f63e` |
| [docs/reports/2026-04-09-entry-path-v1-loss-weighting.md](docs/reports/2026-04-09-entry-path-v1-loss-weighting.md) |  | 2026-06-17 | 7KB | `79f4b733` |
| [docs/reports/2026-04-09-mt4-parity-check-winner.md](docs/reports/2026-04-09-mt4-parity-check-winner.md) |  | 2026-06-17 | 8KB | `a8467fad` |
| [docs/reports/2026-04-10-entry-path-v1-quantile.md](docs/reports/2026-04-10-entry-path-v1-quantile.md) |  | 2026-06-17 | 6KB | `d4fef0e4` |
| [docs/reports/2026-04-12-quantile-status-decision.md](docs/reports/2026-04-12-quantile-status-decision.md) |  | 2026-06-17 | 10KB | `5375913e` |
| [docs/reports/2026-04-12-tb-verdict.md](docs/reports/2026-04-12-tb-verdict.md) |  | 2026-06-17 | 7KB | `089642df` |
| [docs/reports/2026-04-13-fav-3-vs-12-standalone.md](docs/reports/2026-04-13-fav-3-vs-12-standalone.md) |  | 2026-06-17 | 5KB | `8a929a77` |
| [docs/reports/2026-04-13-label-convention-audit.md](docs/reports/2026-04-13-label-convention-audit.md) |  | 2026-06-17 | 6KB | `3ddc2a23` |
| [docs/reports/2026-04-13-pf-uplift-discovery.md](docs/reports/2026-04-13-pf-uplift-discovery.md) |  | 2026-06-17 | 14KB | `f93b85c0` |
| [docs/reports/2026-04-13-quantile-fav-composition.md](docs/reports/2026-04-13-quantile-fav-composition.md) |  | 2026-06-17 | 8KB | `8dd53bda` |
| [docs/reports/2026-04-13-quantile-forward-validation.md](docs/reports/2026-04-13-quantile-forward-validation.md) |  | 2026-06-17 | 4KB | `1364686a` |
| [docs/reports/2026-04-15-entry-path-v1-frequency.md](docs/reports/2026-04-15-entry-path-v1-frequency.md) |  | 2026-06-17 | 6KB | `9f5043d0` |
| [docs/reports/2026-04-15-track-a-max-out.md](docs/reports/2026-04-15-track-a-max-out.md) |  | 2026-06-17 | 9KB | `ca11c38f` |
| [docs/reports/2026-04-16-trailing-stop-target-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-first-wave.md) |  | 2026-06-17 | 6KB | `5b0b7b8b` |
| [docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md) |  | 2026-06-17 | 6KB | `e812d460` |
| [docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md](docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md) |  | 2026-06-17 | 8KB | `6e26a3c3` |
| [docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md](docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md) |  | 2026-06-17 | 8KB | `c2ca8b3f` |
| [docs/reports/2026-04-18-mt4-trailing-stop-execution.md](docs/reports/2026-04-18-mt4-trailing-stop-execution.md) |  | 2026-06-17 | 5KB | `db5e5c66` |
| [docs/reports/2026-04-18-take-skip-frequency-followup.md](docs/reports/2026-04-18-take-skip-frequency-followup.md) |  | 2026-06-17 | 9KB | `edb6385b` |
| [docs/reports/2026-04-18-take-skip-rule-consumer.md](docs/reports/2026-04-18-take-skip-rule-consumer.md) |  | 2026-06-17 | 5KB | `bf29f837` |
| [docs/reports/2026-04-19-current-feature-importance-diagnostics.md](docs/reports/2026-04-19-current-feature-importance-diagnostics.md) |  | 2026-06-17 | 4KB | `e9beb824` |
| [docs/reports/2026-04-19-execution-policy-v2.md](docs/reports/2026-04-19-execution-policy-v2.md) |  | 2026-06-17 | 8KB | `f124b341` |
| [docs/reports/2026-04-19-feature-bank-clean-comparison.md](docs/reports/2026-04-19-feature-bank-clean-comparison.md) |  | 2026-06-17 | 3KB | `6c105216` |
| [docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md](docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md) |  | 2026-06-17 | 3KB | `8505936d` |
| [docs/reports/2026-04-19-lib-pic-feature-source-audit.md](docs/reports/2026-04-19-lib-pic-feature-source-audit.md) |  | 2026-06-17 | 8KB | `0b903977` |
| [docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md](docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md) |  | 2026-06-17 | 4KB | `c80ac4eb` |
| [docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md](docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md) |  | 2026-06-17 | 2KB | `64b8dea4` |
| [docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md](docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md) |  | 2026-06-17 | 9KB | `ac47d800` |
| [docs/reports/2026-04-20-take-skip-lib-pic-selection.md](docs/reports/2026-04-20-take-skip-lib-pic-selection.md) |  | 2026-06-17 | 4KB | `51a438b8` |
| [docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md](docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md) |  | 2026-06-17 | 13KB | `3e9f8318` |
| [docs/reports/2026-04-22-signal-export-parity.md](docs/reports/2026-04-22-signal-export-parity.md) |  | 2026-06-17 | 5KB | `64f8d26c` |
| [docs/reports/2026-04-24-cross-instrument-robustness-check.md](docs/reports/2026-04-24-cross-instrument-robustness-check.md) |  | 2026-06-17 | 8KB | `374bd822` |
| [docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md) |  | 2026-06-17 | 10KB | `29106e47` |
| [docs/reports/2026-04-24-system-correlation-and-portfolio-check.md](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md) |  | 2026-06-17 | 10KB | `77d28ff4` |
| [docs/reports/2026-04-27-telemetry-frequency-demo-launch.md](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) |  | 2026-06-17 | 10KB | `7c587ed0` |
| [docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md) |  | 2026-06-17 | 11KB | `e1210726` |
| [docs/reports/2026-04-29-online-inference-contract-hardening.md](docs/reports/2026-04-29-online-inference-contract-hardening.md) |  | 2026-06-17 | 6KB | `26968f89` |
| [docs/reports/2026-05-05-live-safe-ml-audit.md](docs/reports/2026-05-05-live-safe-ml-audit.md) |  | 2026-06-17 | 23KB | `91e0e4f8` |
| [docs/reports/2026-05-07-cpu-gpu-reproducibility.md](docs/reports/2026-05-07-cpu-gpu-reproducibility.md) |  | 2026-06-17 | 8KB | `589d954f` |
| [docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md](docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md) |  | 2026-06-17 | 6KB | `07ff396c` |
| [docs/reports/2026-05-07-entry-path-mt4-parity.md](docs/reports/2026-05-07-entry-path-mt4-parity.md) |  | 2026-06-17 | 4KB | `b8c63e3c` |
| [docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md](docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md) |  | 2026-06-17 | 3KB | `10ba83c4` |
| [docs/reports/2026-05-12-online-tester-execution-reconciliation.md](docs/reports/2026-05-12-online-tester-execution-reconciliation.md) |  | 2026-06-17 | 21KB | `cca94a62` |
| [docs/reports/2026-05-14-entry-path-all-rows-ranking.md](docs/reports/2026-05-14-entry-path-all-rows-ranking.md) |  | 2026-06-17 | 5KB | `3501a0c7` |
| [docs/reports/2026-05-14-entry-path-causal-surrogate.md](docs/reports/2026-05-14-entry-path-causal-surrogate.md) |  | 2026-06-17 | 3KB | `13aef3da` |
| [docs/reports/2026-05-14-entry-path-direct-bar-model.md](docs/reports/2026-05-14-entry-path-direct-bar-model.md) |  | 2026-06-17 | 4KB | `2038211f` |
| [docs/reports/2026-05-15-direct-direction-improvement.md](docs/reports/2026-05-15-direct-direction-improvement.md) |  | 2026-06-17 | 12KB | `edc04acb` |
| [docs/reports/2026-05-18-direct-direction-rebuild.md](docs/reports/2026-05-18-direct-direction-rebuild.md) |  | 2026-06-17 | 14KB | `c12d5722` |
| [docs/reports/2026-05-21-transformer-direction.md](docs/reports/2026-05-21-transformer-direction.md) |  | 2026-06-17 | 6KB | `510eda23` |
| [docs/reports/2026-05-25-methodology-cycle-stages-00-04.md](docs/reports/2026-05-25-methodology-cycle-stages-00-04.md) |  | 2026-06-17 | 19KB | `1c004781` |
| [docs/reports/2026-05-29-limit-order-entry.md](docs/reports/2026-05-29-limit-order-entry.md) |  | 2026-06-17 | 6KB | `1ce2dda6` |
| [docs/reports/2026-06-01-feature-ablation.md](docs/reports/2026-06-01-feature-ablation.md) |  | 2026-06-17 | 7KB | `8c0b1bd9` |
| [docs/reports/2026-06-03-direction-only-signal.md](docs/reports/2026-06-03-direction-only-signal.md) |  | 2026-06-17 | 10KB | `b8c975d2` |
| [docs/reports/2026-06-04-fractal-ablation.md](docs/reports/2026-06-04-fractal-ablation.md) |  | 2026-06-17 | 10KB | `f3481558` |
| [docs/reports/2026-06-05-rf-gridsearch.md](docs/reports/2026-06-05-rf-gridsearch.md) |  | 2026-06-17 | 5KB | `46b326bb` |
| [docs/reports/2026-06-10-feature-profiles-stage3.md](docs/reports/2026-06-10-feature-profiles-stage3.md) |  | 2026-06-17 | 19KB | `2ea9e68c` |
| [docs/reports/2026-06-10-fractal-stop-breach-stage1.md](docs/reports/2026-06-10-fractal-stop-breach-stage1.md) | Итоговый отчёт Stage 1: breach-разметка, baseline, frozen test и переход к Stage 2 | 2026-06-17 | 8KB | `253de991` |
| [docs/reports/2026-06-10-fractal-stop-fav-stage2.md](docs/reports/2026-06-10-fractal-stop-fav-stage2.md) | Итоговый отчёт Stage 2: fav-разметка, торговый слой, RF FAIL и oracle-диагностика | 2026-06-17 | 19KB | `59f83b51` |
| [docs/reports/2026-06-11-stage4-trade-xgboost.md](docs/reports/2026-06-11-stage4-trade-xgboost.md) |  | 2026-06-17 | 33KB | `349720ce` |
| [docs/reports/2026-06-14-stage4-deep-diagnostics.md](docs/reports/2026-06-14-stage4-deep-diagnostics.md) |  | 2026-06-17 | 6KB | `990ef37a` |
| [docs/reports/2026-06-15-stage4_3-diagnostics.md](docs/reports/2026-06-15-stage4_3-diagnostics.md) |  | 2026-06-17 | 18KB | `53b87377` |
| [docs/reports/2026-06-15-stage4_4-micro-check.md](docs/reports/2026-06-15-stage4_4-micro-check.md) |  | 2026-06-17 | 9KB | `da25f30e` |
| [docs/reports/2026-06-15-stage4_5-exit-mechanics.md](docs/reports/2026-06-15-stage4_5-exit-mechanics.md) |  | 2026-06-17 | 4KB | `c9e1b2f7` |
| [docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md](docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md) |  | 2026-06-17 | 4KB | `1c332d7c` |
| [docs/reports/2026-06-15-stage5-prep-diagnostics.md](docs/reports/2026-06-15-stage5-prep-diagnostics.md) |  | 2026-06-17 | 7KB | `352a8984` |
| [docs/reports/2026-06-15-walk-forward-diagnostics.md](docs/reports/2026-06-15-walk-forward-diagnostics.md) |  | 2026-06-20 | 8KB | `e7b8a674` |
| [docs/reports/2026-06-17-stage5-transformer-breach.md](docs/reports/2026-06-17-stage5-transformer-breach.md) |  | 2026-06-20 | 11KB | `4b270c27` |
| [docs/reports/2026-06-18-stage5_0a-feature-preflight.md](docs/reports/2026-06-18-stage5_0a-feature-preflight.md) |  | 2026-06-20 | 11KB | `1a72413d` |
| [docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md](docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md) |  | 2026-06-24 | 21KB | `af77a753` |
| [docs/reports/2026-06-21-stage5_0b-asinh-rerun.md](docs/reports/2026-06-21-stage5_0b-asinh-rerun.md) |  | 2026-06-24 | 16KB | `c443edc0` |
| [docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md](docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md) |  | 2026-06-24 | 11KB | `0f9bb444` |
| [docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md](docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md) |  | 2026-06-24 | 14KB | `7290f925` |
| [docs/reports/2026-06-23-stage5_0e-small-transformer-check.md](docs/reports/2026-06-23-stage5_0e-small-transformer-check.md) |  | 2026-06-24 | 9KB | `e11ffaa6` |
| [docs/reports/2026-06-24-stage5_0f-signal-stationarity.md](docs/reports/2026-06-24-stage5_0f-signal-stationarity.md) |  | 2026-06-24 | 29KB | `9b99d5bd` |
| [docs/reports/2026-06-24-stage5_1-structural-field-ablation.md](docs/reports/2026-06-24-stage5_1-structural-field-ablation.md) |  | 2026-06-29 | 23KB | `3b85f473` |
| [docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md](docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md) |  | 2026-06-29 | 22KB | `e47d9458` |
| [docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md](docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md) |  | 2026-06-29 | 17KB | `c99aba27` |
| [docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md](docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md) |  | 2026-06-29 | 17KB | `99983a37` |
| [docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md](docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md) |  | 2026-06-29 | 8KB | `c11ad432` |
| [docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md](docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md) |  | 2026-07-20 | 9KB | `3f1cff23` |
| [docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md](docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md) |  | 2026-07-20 | 18KB | `80774af5` |
| [docs/reports/2026-06-30-regression-updn-target-foundation.md](docs/reports/2026-06-30-regression-updn-target-foundation.md) |  | 2026-07-20 | 15KB | `2e629297` |
| [docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md](docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md) |  | 2026-07-20 | 13KB | `a7a26748` |
| [docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md](docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md) |  | 2026-07-20 | 7KB | `674ecf07` |
| [docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md](docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md) |  | 2026-07-20 | 13KB | `04a16eec` |
| [docs/reports/2026-07-01-regression-updn-ratio-audit.md](docs/reports/2026-07-01-regression-updn-ratio-audit.md) |  | 2026-07-20 | 13KB | `8991f98e` |
| [docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md](docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md) |  | 2026-07-20 | 17KB | `05a83fbe` |
| [docs/reports/2026-07-02-next-open-entry-updn-foundation.md](docs/reports/2026-07-02-next-open-entry-updn-foundation.md) |  | 2026-07-20 | 14KB | `fcbbbaf2` |
| [docs/reports/2026-07-02-regression-updn-already-moved-audit.md](docs/reports/2026-07-02-regression-updn-already-moved-audit.md) |  | 2026-07-20 | 11KB | `204ff3fc` |
| [docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md](docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md) |  | 2026-07-20 | 17KB | `7ec6722b` |
| [docs/reports/2026-07-04-entry-based-next-open-closeout.md](docs/reports/2026-07-04-entry-based-next-open-closeout.md) |  | 2026-07-20 | 14KB | `4550f805` |
| [docs/reports/2026-07-06-entry-based-powerful-tabular-models.md](docs/reports/2026-07-06-entry-based-powerful-tabular-models.md) |  | 2026-07-20 | 16KB | `77a6feb1` |
| [docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md](docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md) |  | 2026-07-20 | 12KB | `fa358840` |
| [docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md](docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md) |  | 2026-07-20 | 24KB | `9e5be1ad` |
| [docs/reports/2026-07-07-entry-based-movement-filter-design.md](docs/reports/2026-07-07-entry-based-movement-filter-design.md) |  | 2026-07-20 | 10KB | `2522ea1a` |
| [docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md](docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md) |  | 2026-07-20 | 8KB | `6c380c1b` |
| [docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md](docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md) | Итоговый отчёт freeze-репликации одного entry-based movement-filter без direction/PnL/PF и без открытия `locked_test` | 2026-07-20 | 13KB | `bf821cdf` |
| [docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md](docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md) |  | 2026-07-20 | 9KB | `28c0eb53` |
| [docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md](docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md) |  | 2026-07-20 | 8KB | `85885de8` |
| [docs/reports/2026-07-10-fractal0-price-entry-mechanics.md](docs/reports/2026-07-10-fractal0-price-entry-mechanics.md) |  | 2026-07-20 | 6KB | `f147cfc6` |
| [docs/reports/2026-07-21-fractal0-entry-exit-grid.md](docs/reports/2026-07-21-fractal0-entry-exit-grid.md) |  | 2026-07-29 | 13KB | `63625f45` |
| [docs/reports/2026-07-21-fractal0-entry-quality-filter.md](docs/reports/2026-07-21-fractal0-entry-quality-filter.md) |  | 2026-07-29 | 11KB | `bca56abf` |
| [docs/reports/2026-07-21-fractal0-rich-entry-quality.md](docs/reports/2026-07-21-fractal0-rich-entry-quality.md) |  | 2026-07-29 | 18KB | `7994be66` |
| [docs/reports/2026-07-21-fractal0-stop-grid-m5.md](docs/reports/2026-07-21-fractal0-stop-grid-m5.md) |  | 2026-07-29 | 16KB | `8d4cc249` |
| [docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md](docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md) |  | 2026-07-29 | 27KB | `3f5a0204` |
| [docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md](docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md) |  | 2026-07-29 | 12KB | `d422b89f` |
| [docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md](docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md) |  | 2026-07-29 | 10KB | `bccc7161` |
| [docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md](docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md) |  | 2026-07-29 | 10KB | `ec2503bf` |
| [docs/reports/2026-07-23-time-only-robustness-audit.md](docs/reports/2026-07-23-time-only-robustness-audit.md) |  | 2026-07-29 | 9KB | `b90f6a05` |
| [docs/reports/2026-07-24-fractal0-fixed11-locked-test.md](docs/reports/2026-07-24-fractal0-fixed11-locked-test.md) |  | 2026-07-29 | 17KB | `5eac9b41` |
| [docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md](docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md) |  | 2026-07-29 | 8KB | `88a957c4` |
| [docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md](docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md) |  | 2026-07-29 | 10KB | `fe9774d5` |
| [docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md](docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md) |  | 2026-07-29 | 12KB | `5aa0c736` |
| [docs/reports/2026-07-29-fixed11-current-history-rerun.md](docs/reports/2026-07-29-fixed11-current-history-rerun.md) |  | 2026-07-29 | 23KB | `e0a084a7` |
| [docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md](docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md) |  | 2026-07-29 | 12KB | `536d886f` |
| [docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md](docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md) |  | 2026-07-29 | 18KB | `fa4c8910` |
| [docs/reports/2026-07-29-mt5-batch-selection-design.md](docs/reports/2026-07-29-mt5-batch-selection-design.md) |  | 2026-07-30 | 2KB | `c19dfd31` |
| [docs/reports/2026-07-29-mt5-execution-loop-migration.md](docs/reports/2026-07-29-mt5-execution-loop-migration.md) |  | 2026-07-30 | 8KB | `07ca23fc` |
| [docs/reports/2026-07-29-mt5-feasibility.md](docs/reports/2026-07-29-mt5-feasibility.md) |  | 2026-07-30 | 2KB | `d33acf94` |
| [docs/reports/2026-07-29-mt5-manual-tester-runbook.md](docs/reports/2026-07-29-mt5-manual-tester-runbook.md) |  | 2026-07-30 | 1KB | `0d991232` |
| [docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md](docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md) |  | 2026-07-31 | 12KB | `3d58f7bc` |
| [docs/reports/2026-07-31-mt5-batch-selection.md](docs/reports/2026-07-31-mt5-batch-selection.md) |  | 2026-08-01 | 14KB | `084ca3c5` |
| [docs/reports/2026-07-31-mt5-nero-parity.md](docs/reports/2026-07-31-mt5-nero-parity.md) |  | 2026-07-31 | 5KB | `4d409cce` |
| [docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md](docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md) |  | 2026-07-31 | 11KB | `4717b1dc` |
| [docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md](docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md) |  | 2026-08-01 | 9KB | `e3595e5c` |
| [docs/reports/README.md](docs/reports/README.md) |  | 2026-07-06 | 2KB | `9a64f8af` |

## ML

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [ML/README.md](ML/README.md) |  |  | 2026-06-17 | 17KB | `8e6c2c98` |
| [ML/ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | 🏁 | 2026-06-17 | 4KB | `dd55ee84` |
| [ML/baseline/analyze_regression_updn_already_moved_audit.py](ML/baseline/analyze_regression_updn_already_moved_audit.py) | Audit: движение до next-open entry | ✅ | 2026-07-20 | 28KB | `04568800` |
| [ML/baseline/analyze_stage6_2_range_w1_postmortem.py](ML/baseline/analyze_stage6_2_range_w1_postmortem.py) | Stage 6.2 post-mortem | ✅ | 2026-07-20 | 28KB | `6450da16` |
| [ML/baseline/audit_fractal0_fixed11_candidate.py](ML/baseline/audit_fractal0_fixed11_candidate.py) | Read-only candidate audit для `fractal0_fixed11_rich_entry_locked_test*` без нового выбора по `locked_test` | ✅ | 2026-07-29 | 24KB | `49c3009b` |
| [ML/baseline/audit_leaderboard_closure.py](ML/baseline/audit_leaderboard_closure.py) | Closure/disclosure audit для 11 fixed leaderboard rows: cost, calendar, timezone, sequential positions и multi-seed без нового поиска | ✅ | 2026-07-29 | 26KB | `0b231fc1` |
| [ML/baseline/audit_leaderboard_robustness.py](ML/baseline/audit_leaderboard_robustness.py) | Validation-slice audit 11 fixed normalized rich-entry leaderboard input rows без нового поиска и без `locked_test` | ✅ | 2026-07-29 | 30KB | `88ed537e` |
| [ML/baseline/audit_time_only_robustness.py](ML/baseline/audit_time_only_robustness.py) | Validation-slice audit fixed normalized `time_only` winner без нового поиска и без `locked_test` | ✅ | 2026-07-29 | 28KB | `943d65a5` |
| [ML/baseline/baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | 🏁 | 2026-06-17 | 40KB | `e1216862` |
| [ML/baseline/benchmark_direction_inside_frozen_movement_regime.py](ML/baseline/benchmark_direction_inside_frozen_movement_regime.py) | Direction check inside frozen movement mask | ✅ | 2026-07-20 | 30KB | `691d70bc` |
| [ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py](ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py) | Rich feature direction check and narrow seed replication inside frozen movement mask with resume/progress | ✅ | 2026-07-20 | 74KB | `b2680e6e` |
| [ML/baseline/benchmark_entry_based_amplitude_movement.py](ML/baseline/benchmark_entry_based_amplitude_movement.py) | Entry-based amplitude movement-regime audit | ✅ | 2026-07-20 | 59KB | `f107dda3` |
| [ML/baseline/benchmark_entry_based_movement_filter.py](ML/baseline/benchmark_entry_based_movement_filter.py) | Entry-based simple movement filter | ⚠️ | 2026-07-20 | 27KB | `099f88d6` |
| [ML/baseline/benchmark_entry_based_movement_filter_freeze.py](ML/baseline/benchmark_entry_based_movement_filter_freeze.py) | Entry-based movement filter freeze runner | ✅ | 2026-07-20 | 33KB | `0e12e5a3` |
| [ML/baseline/benchmark_entry_based_next_open_closeout.py](ML/baseline/benchmark_entry_based_next_open_closeout.py) | Entry-based closeout runner | ✅ | 2026-07-20 | 32KB | `e118810a` |
| [ML/baseline/benchmark_entry_based_powerful_tabular.py](ML/baseline/benchmark_entry_based_powerful_tabular.py) | Entry-based tabular runner | ✅ | 2026-07-20 | 45KB | `09236427` |
| [ML/baseline/benchmark_entry_based_sequence_transformer.py](ML/baseline/benchmark_entry_based_sequence_transformer.py) | Entry-based sequence Transformer runner | ✅ | 2026-07-20 | 46KB | `f8d73f1a` |
| [ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py](ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py) | Entry-based fractal ablation | ✅ | 2026-07-20 | 51KB | `cbbee1d3` |
| [ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py](ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py) | Entry-based Up/Dn price-feature matrix | ✅ | 2026-07-20 | 30KB | `1dd98792` |
| [ML/baseline/benchmark_fractal0_entry_exit_grid.py](ML/baseline/benchmark_fractal0_entry_exit_grid.py) | Fractal0 entry/exit grid со stop-policy grid, M5 fill timestamp / same-H1 ordering, ML-exit и permutation correction | ✅ | 2026-07-29 | 83KB | `8c22e81f` |
| [ML/baseline/benchmark_fractal0_entry_quality_filter.py](ML/baseline/benchmark_fractal0_entry_quality_filter.py) | ML-entry, rich-entry и normalized rich-entry quality фильтр для Fractal0 E3 поверх stop-grid winner без нового симулятора | ✅ | 2026-07-29 | 130KB | `1be7905b` |
| [ML/baseline/benchmark_fractal0_price_entry_mechanics.py](ML/baseline/benchmark_fractal0_price_entry_mechanics.py) | Oracle-preflight входа через возврат цены к зоне `fractal0_price` | ✅ | 2026-07-20 | 30KB | `9be21f55` |
| [ML/baseline/benchmark_fractal_stop_breach.py](ML/baseline/benchmark_fractal_stop_breach.py) | Stage 1 Fractal Stop Breach | ✅ | 2026-06-17 | 13KB | `186f1abf` |
| [ML/baseline/benchmark_fractal_stop_fav.py](ML/baseline/benchmark_fractal_stop_fav.py) | Stage 2 Fractal Stop Fav | ✅ | 2026-06-17 | 26KB | `5b982cce` |
| [ML/baseline/benchmark_fractal_stop_stage3.py](ML/baseline/benchmark_fractal_stop_stage3.py) |  |  | 2026-06-17 | 14KB | `83382da4` |
| [ML/baseline/benchmark_fractal_stop_stage3_1.py](ML/baseline/benchmark_fractal_stop_stage3_1.py) |  |  | 2026-06-17 | 16KB | `7d967447` |
| [ML/baseline/benchmark_fractal_stop_stage3_2.py](ML/baseline/benchmark_fractal_stop_stage3_2.py) |  |  | 2026-06-17 | 24KB | `6548f9c3` |
| [ML/baseline/benchmark_fractal_stop_stage4.py](ML/baseline/benchmark_fractal_stop_stage4.py) | Stage 4 Fractal Stop benchmark | ✅ | 2026-06-17 | 27KB | `cbb0c1a2` |
| [ML/baseline/benchmark_fractal_stop_stage4_1.py](ML/baseline/benchmark_fractal_stop_stage4_1.py) | Stage 4.1 controls | ✅ | 2026-06-17 | 34KB | `455369c6` |
| [ML/baseline/benchmark_fractal_stop_stage4_2.py](ML/baseline/benchmark_fractal_stop_stage4_2.py) | Stage 4.2 corrected diagnostic | ✅ | 2026-06-17 | 27KB | `1151a158` |
| [ML/baseline/benchmark_limit_order_entry.py](ML/baseline/benchmark_limit_order_entry.py) |  |  | 2026-06-17 | 9KB | `32700fef` |
| [ML/baseline/benchmark_next_open_entry_updn_foundation.py](ML/baseline/benchmark_next_open_entry_updn_foundation.py) | Next-open entry Up/Dn foundation | ✅ | 2026-07-20 | 19KB | `1463ca6c` |
| [ML/baseline/benchmark_regression_updn_target_foundation.py](ML/baseline/benchmark_regression_updn_target_foundation.py) | Regression Up/Dn target foundation | ✅ | 2026-07-20 | 34KB | `742e5523` |
| [ML/baseline/benchmark_stage4_6_clean_cycle.py](ML/baseline/benchmark_stage4_6_clean_cycle.py) | Stage 4.6 clean cycle | ✅ | 2026-06-17 | 17KB | `d9822538` |
| [ML/baseline/benchmark_stage5_transformer_breach.py](ML/baseline/benchmark_stage5_transformer_breach.py) | Stage 5 Transformer Breach | 🏁 | 2026-06-29 | 363KB | `ae8b81ac` |
| [ML/baseline/benchmark_stage6_1_relative_geometry.py](ML/baseline/benchmark_stage6_1_relative_geometry.py) | Stage 6.1 relative fractal geometry profiles | ✅ | 2026-07-20 | 32KB | `6cde1ca0` |
| [ML/baseline/benchmark_stage6_2_price_action.py](ML/baseline/benchmark_stage6_2_price_action.py) | Stage 6.2 price-action family | ✅ | 2026-07-20 | 35KB | `d45863fb` |
| [ML/baseline/benchmark_stage6_3_h6_feature_parity.py](ML/baseline/benchmark_stage6_3_h6_feature_parity.py) | Stage 6.3 H6/H12 feature parity audit | ✅ | 2026-07-20 | 28KB | `d3c357c7` |
| [ML/baseline/benchmark_stage6_outcome_based.py](ML/baseline/benchmark_stage6_outcome_based.py) | Stage 6.0 outcome-based triple-barrier baseline | ✅ | 2026-07-20 | 40KB | `02e85144` |
| [ML/baseline/compare_nero_by_time.py](ML/baseline/compare_nero_by_time.py) |  |  | 2026-07-31 | 8KB | `38a1a0ab` |
| [ML/baseline/compare_nero_parity.py](ML/baseline/compare_nero_parity.py) |  |  | 2026-07-31 | 9KB | `c1d663ca` |
| [ML/baseline/diagnose_stage4_3.py](ML/baseline/diagnose_stage4_3.py) | Stage 4.3 loss decomposition | ✅ | 2026-06-17 | 64KB | `84f7957b` |
| [ML/baseline/diagnose_stage4_4.py](ML/baseline/diagnose_stage4_4.py) | Stage 4.4 micro-check | ✅ | 2026-06-17 | 29KB | `c1595a48` |
| [ML/baseline/diagnose_stage4_5_exit_mechanics.py](ML/baseline/diagnose_stage4_5_exit_mechanics.py) | Stage 4.5 exit mechanics | ✅ | 2026-06-17 | 22KB | `2d551922` |
| [ML/baseline/diagnose_stage4_gap.py](ML/baseline/diagnose_stage4_gap.py) |  |  | 2026-06-17 | 27KB | `ed1a52e9` |
| [ML/baseline/diagnose_stage5_prep.py](ML/baseline/diagnose_stage5_prep.py) | Stage 5 prep diagnostic | ✅ | 2026-06-17 | 17KB | `d1c5792c` |
| [ML/baseline/diagnose_walk_forward.py](ML/baseline/diagnose_walk_forward.py) |  |  | 2026-06-20 | 24KB | `749b0549` |
| [ML/baseline/direction_only_signal.py](ML/baseline/direction_only_signal.py) |  |  | 2026-06-17 | 6KB | `8d683a5b` |
| [ML/baseline/direction_updn_signal.py](ML/baseline/direction_updn_signal.py) |  |  | 2026-06-17 | 3KB | `70523b5b` |
| [ML/baseline/export_mt5_entry_signals.py](ML/baseline/export_mt5_entry_signals.py) |  |  | 2026-07-30 | 9KB | `4ea65af5` |
| [ML/baseline/feature_ablation.py](ML/baseline/feature_ablation.py) |  |  | 2026-06-17 | 16KB | `704db67c` |
| [ML/baseline/fractal0_fixed11_internal_closure_rerun.py](ML/baseline/fractal0_fixed11_internal_closure_rerun.py) | Producer-level fixed11 internal closure rerun: stress-cost, timezone/calendar и multi-seed без `locked_test` | ✅ | 2026-07-29 | 69KB | `694fec17` |
| [ML/baseline/fractal_ablation.py](ML/baseline/fractal_ablation.py) |  |  | 2026-06-17 | 9KB | `1e6b236f` |
| [ML/baseline/improve_stage4.py](ML/baseline/improve_stage4.py) |  |  | 2026-06-17 | 33KB | `e5c6ddc8` |
| [ML/baseline/mt5_execution_diagnostics.py](ML/baseline/mt5_execution_diagnostics.py) |  |  | 2026-08-01 | 25KB | `42661ce8` |
| [ML/baseline/mt5_signal_schema.py](ML/baseline/mt5_signal_schema.py) |  |  | 2026-07-31 | 3KB | `a7bffca3` |
| [ML/baseline/oracle_fractal_stop_fav.py](ML/baseline/oracle_fractal_stop_fav.py) | Oracle Fractal Stop Fav | ✅ | 2026-06-17 | 8KB | `02e614cf` |
| [ML/baseline/parse_mt5_execution_report.py](ML/baseline/parse_mt5_execution_report.py) |  |  | 2026-07-31 | 5KB | `ac5ac478` |
| [ML/baseline/prepare_mt5_entry_source.py](ML/baseline/prepare_mt5_entry_source.py) |  |  | 2026-07-30 | 4KB | `287d79bb` |
| [ML/baseline/prune_fractal0_fixed11_mutual_correlation.py](ML/baseline/prune_fractal0_fixed11_mutual_correlation.py) | Read-only pruning 11 fixed Fractal0 rules by mutual overlap без нового winner по `locked_test` | ✅ | 2026-07-29 | 31KB | `7bed97a1` |
| [ML/baseline/reports/baseline_report.md](ML/baseline/reports/baseline_report.md) |  |  | 2026-06-17 | 4KB | `66cbf52f` |
| [ML/baseline/reports/limit_order_spread_grid.md](ML/baseline/reports/limit_order_spread_grid.md) |  |  | 2026-06-17 | 3KB | `f8f3c27b` |
| [ML/baseline/rf_gridsearch.py](ML/baseline/rf_gridsearch.py) |  |  | 2026-06-17 | 6KB | `31bd8826` |
| [ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py](ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py) | Wrapper 11 fixed normalized rich-entry rules для locked-test/rerun с M5 fill timestamp и diagnostic contract fields | ✅ | 2026-07-29 | 20KB | `956b1768` |
| [ML/baseline/run_mt5_batch.py](ML/baseline/run_mt5_batch.py) |  |  | 2026-07-31 | 24KB | `94cc9edc` |
| [ML/baseline/tb_direction_signal.py](ML/baseline/tb_direction_signal.py) |  |  | 2026-06-17 | 8KB | `d211235a` |
| [ML/baseline/trail_stop_stage4.py](ML/baseline/trail_stop_stage4.py) |  |  | 2026-06-17 | 21KB | `684b667a` |
| [ML/baseline_candidate_source.py](ML/baseline_candidate_source.py) | Stage 07 baseline-first runner для candidate-source v2 | ✅ | 2026-06-17 | 10KB | `d2608702` |
| [ML/benchmark_buy_only_direction.py](ML/benchmark_buy_only_direction.py) | BUY-only RF с исправленными признаками (Phase A/B/D rebuild) | ✅ | 2026-06-17 | 37KB | `59b3a74c` |
| [ML/benchmark_cross_instrument_robustness.py](ML/benchmark_cross_instrument_robustness.py) | Cross-instrument robustness | ✅ | 2026-06-17 | 13KB | `d59921e5` |
| [ML/benchmark_entry_path_all_rows_ranking.py](ML/benchmark_entry_path_all_rows_ranking.py) | All-rows ranking benchmark | ✅ | 2026-06-17 | 16KB | `56cff1e7` |
| [ML/benchmark_entry_path_binary_direction.py](ML/benchmark_entry_path_binary_direction.py) | Binary-direction benchmark для entry_path | ✅ | 2026-06-17 | 26KB | `03739d36` |
| [ML/benchmark_entry_path_causal_surrogate.py](ML/benchmark_entry_path_causal_surrogate.py) | Causal surrogate benchmark | ✅ | 2026-06-17 | 19KB | `304f831a` |
| [ML/benchmark_entry_path_direct_bar_model.py](ML/benchmark_entry_path_direct_bar_model.py) | Direct bar model benchmark | ✅ | 2026-06-17 | 18KB | `ab227ac4` |
| [ML/benchmark_entry_path_fractal_level_direct_direction.py](ML/benchmark_entry_path_fractal_level_direct_direction.py) | Fractal-level direct-direction benchmark | ✅ | 2026-06-17 | 29KB | `2194abb9` |
| [ML/benchmark_entry_path_fractal_level_signal.py](ML/benchmark_entry_path_fractal_level_signal.py) | Fractal-level signal benchmark для entry_path | ✅ | 2026-06-17 | 7KB | `d2b2f04b` |
| [ML/benchmark_entry_path_score_direction.py](ML/benchmark_entry_path_score_direction.py) | Score-direction benchmark для entry_path | ✅ | 2026-06-17 | 14KB | `8abb3d20` |
| [ML/benchmark_entry_path_signal_only_ablation.py](ML/benchmark_entry_path_signal_only_ablation.py) | Signal-only ablation | ✅ | 2026-06-17 | 11KB | `52aa4508` |
| [ML/benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | 🏁 | 2026-06-17 | 6KB | `1bc86818` |
| [ML/benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | 🏁 | 2026-06-17 | 7KB | `e469b58a` |
| [ML/benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | ✅ | 2026-06-17 | 13KB | `40bbefc1` |
| [ML/benchmark_entry_path_v1_quantile_n_boost.py](ML/benchmark_entry_path_v1_quantile_n_boost.py) |  |  | 2026-06-17 | 13KB | `6538fa97` |
| [ML/benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | ✅ | 2026-06-17 | 12KB | `34916e02` |
| [ML/benchmark_execution_policy_v2.py](ML/benchmark_execution_policy_v2.py) | Execution policy benchmark | ✅ | 2026-06-17 | 16KB | `514040ec` |
| [ML/benchmark_fav_3_vs_12_standalone.py](ML/benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-06-17 | 16KB | `8e4214fd` |
| [ML/benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | 🏁 | 2026-06-17 | 14KB | `b821a51b` |
| [ML/benchmark_quantile_early_timeout.py](ML/benchmark_quantile_early_timeout.py) |  |  | 2026-06-17 | 5KB | `dca2ba4f` |
| [ML/benchmark_quantile_fav_composition.py](ML/benchmark_quantile_fav_composition.py) |  |  | 2026-06-17 | 15KB | `97a02b70` |
| [ML/benchmark_quantile_forward_validation.py](ML/benchmark_quantile_forward_validation.py) |  |  | 2026-06-17 | 5KB | `a3386bcc` |
| [ML/benchmark_quantile_relaxed_composition.py](ML/benchmark_quantile_relaxed_composition.py) |  |  | 2026-06-17 | 8KB | `67b8d711` |
| [ML/benchmark_signal_export_parity.py](ML/benchmark_signal_export_parity.py) | Signal export parity audit | ✅ | 2026-06-17 | 10KB | `a5ab05fc` |
| [ML/benchmark_system_correlation.py](ML/benchmark_system_correlation.py) | System correlation benchmark | ✅ | 2026-06-17 | 24KB | `c2a02130` |
| [ML/benchmark_take_skip_lib_pic_selection.py](ML/benchmark_take_skip_lib_pic_selection.py) | Take/skip selection by `lib_PIC` | ✅ | 2026-06-17 | 18KB | `103dc4a1` |
| [ML/benchmark_take_skip_mt4_trailing_sequential.py](ML/benchmark_take_skip_mt4_trailing_sequential.py) | Take/skip MT4 trailing comparison | ✅ | 2026-06-17 | 7KB | `1debf0f4` |
| [ML/benchmark_take_skip_trailing_stop.py](ML/benchmark_take_skip_trailing_stop.py) |  |  | 2026-06-17 | 8KB | `b1f8f35d` |
| [ML/benchmark_take_skip_trailing_stop_v2.py](ML/benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-06-17 | 5KB | `f1ef638b` |
| [ML/benchmark_take_skip_trailing_stop_v2_followup.py](ML/benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-06-17 | 10KB | `106613ee` |
| [ML/benchmark_telemetry_frequency_calibration.py](ML/benchmark_telemetry_frequency_calibration.py) | Telemetry frequency calibration | ✅ | 2026-06-17 | 11KB | `51c02ce4` |
| [ML/benchmark_trailing_stop_target.py](ML/benchmark_trailing_stop_target.py) | Validation-first benchmark для trailing-stop target exports | ✅ | 2026-06-17 | 1KB | `7c96419a` |
| [ML/benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | ✅ | 2026-06-17 | 8KB | `d8cf04ba` |
| [ML/benchmark_triple_barrier_mt4_execution.py](ML/benchmark_triple_barrier_mt4_execution.py) |  |  | 2026-06-17 | 4KB | `3ef3e057` |
| [ML/compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | 🏁 | 2026-06-17 | 13KB | `adc3937c` |
| [ML/conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | 🏁 | 2026-06-17 | 14KB | `d316ff0e` |
| [ML/conformal/conformal_quantiles.json](ML/conformal/conformal_quantiles.json) |  |  | 2026-06-17 | 399B | `6d9e2e03` |
| [ML/data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ | 2026-06-17 | 73KB | `99819f65` |
| [ML/entry_path_direct_direction_targets.py](ML/entry_path_direct_direction_targets.py) | Target helpers для direct direction | ✅ | 2026-06-17 | 11KB | `4d77c81d` |
| [ML/entry_path_feature_bank.py](ML/entry_path_feature_bank.py) | Entry path feature bank: оконные сводки строки и row-wise context features | ✅ | 2026-06-17 | 3KB | `1445c400` |
| [ML/entry_path_level_targets.py](ML/entry_path_level_targets.py) | Target helpers для fractal-level entry path | ✅ | 2026-06-17 | 7KB | `0e33bad7` |
| [ML/entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | ✅ | 2026-06-17 | 17KB | `f60dbc66` |
| [ML/entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | ✅ | 2026-06-17 | 14KB | `54d61050` |
| [ML/entry_path_v1_quantile_ensemble.py](ML/entry_path_v1_quantile_ensemble.py) | Агрегация quantile-прогнозов по нескольким seed для n-boost проверки | ✅ | 2026-06-17 | 965B | `1f32dd16` |
| [ML/entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | ✅ | 2026-06-17 | 8KB | `6e03b05a` |
| [ML/evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | ✅ | 2026-06-17 | 40KB | `b22a681f` |
| [ML/experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | 🏁 | 2026-06-17 | 20KB | `ac98edd8` |
| [ML/export_entry_path_predictions.py](ML/export_entry_path_predictions.py) | Entry-path inference export | ✅ | 2026-06-17 | 8KB | `367f4065` |
| [ML/export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export quantile predictions | ✅ | 2026-06-17 | 6KB | `38bc75e8` |
| [ML/export_entry_path_v1_quantile_rule.py](ML/export_entry_path_v1_quantile_rule.py) |  |  | 2026-06-17 | 7KB | `aa96afd9` |
| [ML/export_take_skip_v2_predictions.py](ML/export_take_skip_v2_predictions.py) | Экспорт take/skip v2 predictions | ✅ | 2026-06-17 | 10KB | `a904d007` |
| [ML/export_updn_active_predictions.py](ML/export_updn_active_predictions.py) |  |  | 2026-06-17 | 4KB | `515bde2e` |
| [ML/feature_bank_comparison_diagnostics.py](ML/feature_bank_comparison_diagnostics.py) | Сравнение feature-bank вариантов | ✅ | 2026-06-17 | 9KB | `3599f7fa` |
| [ML/feature_importance_diagnostics.py](ML/feature_importance_diagnostics.py) | Диагностика важности feature groups | ✅ | 2026-06-17 | 16KB | `82e28b86` |
| [ML/feature_screen_entry_path.py](ML/feature_screen_entry_path.py) | Диагностический feature screening для entry_path_v1 | ✅ | 2026-06-17 | 782B | `473127c5` |
| [ML/fractal_level_feature_builder.py](ML/fractal_level_feature_builder.py) | Feature builder для fractal-level задач | ✅ | 2026-06-17 | 22KB | `0e9565c0` |
| [ML/lib_pic_feature_profiles.py](ML/lib_pic_feature_profiles.py) | Профили признаков `lib_PIC` | ✅ | 2026-06-17 | 4KB | `6da69e68` |
| [ML/lib_pic_geometry_feature_bank.py](ML/lib_pic_geometry_feature_bank.py) | Производные признаки геометрии уровней `lib_PIC` | ✅ | 2026-06-17 | 7KB | `24dd7aaa` |
| [ML/lib_pic_path_reaction_feature_bank.py](ML/lib_pic_path_reaction_feature_bank.py) | Path-reaction признаки `lib_PIC` | ✅ | 2026-06-17 | 8KB | `a47b0ff1` |
| [ML/limit_order_train.py](ML/limit_order_train.py) |  |  | 2026-06-17 | 11KB | `5f2829eb` |
| [ML/live_safe_audit.py](ML/live_safe_audit.py) | Core-типы live-safe audit и свод feature verdict → system verdict | ✅ | 2026-06-17 | 5KB | `8aeb6ecd` |
| [ML/live_safe_audit_registry.py](ML/live_safe_audit_registry.py) | Реестр прибыльных ML-систем для повторного live-safe audit | ✅ | 2026-06-17 | 3KB | `20c94868` |
| [ML/losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ | 2026-06-17 | 9KB | `b66ced3d` |
| [ML/model_sweep_candidate_source.py](ML/model_sweep_candidate_source.py) | Stage 08 model sweep | ✅ | 2026-06-17 | 19KB | `aa317cfd` |
| [ML/models/__init__.py](ML/models/__init__.py) |  |  | 2026-06-17 | 1KB | `15669a9b` |
| [ML/models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | 🏁 | 2026-06-17 | 4KB | `4aa2023e` |
| [ML/models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | 🏁 | 2026-06-17 | 4KB | `bd1fab57` |
| [ML/models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | ✅ | 2026-06-17 | 4KB | `597779ed` |
| [ML/models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | ✅ | 2026-06-17 | 4KB | `41ffb003` |
| [ML/models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | ✅ | 2026-06-17 | 4KB | `68bafa95` |
| [ML/models/fractal_breach_transformer.py](ML/models/fractal_breach_transformer.py) | Stage 5 breach Transformer | 🏁 | 2026-06-20 | 6KB | `090fddf9` |
| [ML/models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 | 2026-06-17 | 5KB | `06ff47b8` |
| [ML/models/take_skip_dual_stream_transformer.py](ML/models/take_skip_dual_stream_transformer.py) | Dual-stream Transformer для `take_skip_v2`: sequence branch + `lib_PIC` feature branch | ✅ | 2026-06-17 | 3KB | `d645930f` |
| [ML/models/trailing_stop_target_quantile_transformer.py](ML/models/trailing_stop_target_quantile_transformer.py) | Trailing-stop quantile Transformer | ✅ | 2026-06-17 | 2KB | `61f57808` |
| [ML/models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | ✅ | 2026-06-17 | 7KB | `e1b62b6e` |
| [ML/multi_scale_fractal_features.py](ML/multi_scale_fractal_features.py) | Multi-scale fractal feature bank | ✅ | 2026-06-17 | 1KB | `c73c28c3` |
| [ML/online_tester_reconciliation.py](ML/online_tester_reconciliation.py) | Online/tester reconciliation | ✅ | 2026-06-17 | 21KB | `24040876` |
| [ML/optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | 🏁 | 2026-06-17 | 19KB | `80f179e6` |
| [ML/pll_normalizer.py](ML/pll_normalizer.py) |  |  | 2026-06-17 | 8KB | `3ac39fd4` |
| [ML/prepare_entry_path_mt4_parity.py](ML/prepare_entry_path_mt4_parity.py) | Entry-path MT4 parity export | ✅ | 2026-06-17 | 7KB | `0227d595` |
| [ML/prepare_raw_features.py](ML/prepare_raw_features.py) | Извлечение сырых признаков из OHLC для direct-direction (Phase 0) | ✅ | 2026-06-17 | 19KB | `e2098ef4` |
| [ML/reports/architecture_comparison_classification.md](ML/reports/architecture_comparison_classification.md) |  |  | 2026-06-17 | 3KB | `c0fe9f2d` |
| [ML/reports/architecture_comparison_regression.md](ML/reports/architecture_comparison_regression.md) |  |  | 2026-06-17 | 1KB | `3fe65254` |
| [ML/reports/architecture_comparison_regression_updn.md](ML/reports/architecture_comparison_regression_updn.md) |  |  | 2026-06-17 | 1KB | `bc5e1dc4` |
| [ML/reports/buy_only_direction_rebuild/frozen_test.json](ML/reports/buy_only_direction_rebuild/frozen_test.json) |  |  | 2026-06-17 | 1KB | `a326384f` |
| [ML/reports/buy_only_direction_rebuild/phase_a_summary.json](ML/reports/buy_only_direction_rebuild/phase_a_summary.json) |  |  | 2026-06-17 | 21KB | `fe504c56` |
| [ML/reports/buy_only_direction_rebuild/phase_b_summary.json](ML/reports/buy_only_direction_rebuild/phase_b_summary.json) |  |  | 2026-06-17 | 2KB | `7f10fe5d` |
| [ML/reports/buy_only_direction_rebuild/summary.json](ML/reports/buy_only_direction_rebuild/summary.json) |  |  | 2026-06-17 | 21KB | `fe504c56` |
| [ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-06-17 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/summary.json) |  |  | 2026-06-17 | 15KB | `d8c4143b` |
| [ML/reports/cross_instrument_robustness/finalize_labeled_temp.py](ML/reports/cross_instrument_robustness/finalize_labeled_temp.py) |  |  | 2026-06-17 | 2KB | `e8aae810` |
| [ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-06-17 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/summary.json) |  |  | 2026-06-17 | 15KB | `d7897cc3` |
| [ML/reports/cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json) |  |  | 2026-06-17 | 987B | `5134c6b8` |
| [ML/reports/cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json) |  |  | 2026-06-17 | 987B | `67ce56ee` |
| [ML/reports/cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json](ML/reports/cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json) |  |  | 2026-06-17 | 912B | `b7cef6eb` |
| [ML/reports/cross_instrument_robustness/manifest_cross_instrument_transfer.json](ML/reports/cross_instrument_robustness/manifest_cross_instrument_transfer.json) |  |  | 2026-06-17 | 3KB | `1e7814b0` |
| [ML/reports/cross_instrument_robustness/manifest_metaquotes_baseline.json](ML/reports/cross_instrument_robustness/manifest_metaquotes_baseline.json) |  |  | 2026-06-17 | 824B | `61aa0027` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer.json) |  |  | 2026-06-17 | 885B | `6f8aaed0` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_qf.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_qf.json) |  |  | 2026-06-17 | 667B | `236d2bff` |
| [ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_test_labeled.json](ML/reports/cross_instrument_robustness/manifest_xagusd_transfer_test_labeled.json) |  |  | 2026-06-17 | 913B | `974ca96f` |
| [ML/reports/cross_instrument_robustness/manifest_xauusd_provider_drift.json](ML/reports/cross_instrument_robustness/manifest_xauusd_provider_drift.json) |  |  | 2026-06-17 | 825B | `3d686bf2` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline/run_metadata.json](ML/reports/cross_instrument_robustness/metaquotes_baseline/run_metadata.json) |  |  | 2026-06-17 | 95B | `543171a5` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline/summary.json](ML/reports/cross_instrument_robustness/metaquotes_baseline/summary.json) |  |  | 2026-06-17 | 30KB | `a8a1e20d` |
| [ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json](ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json) |  |  | 2026-06-17 | 512B | `033d5470` |
| [ML/reports/cross_instrument_robustness/run_single_instrument_transfer.py](ML/reports/cross_instrument_robustness/run_single_instrument_transfer.py) |  |  | 2026-06-17 | 5KB | `7d257dff` |
| [ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/run_metadata.json) |  |  | 2026-06-17 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/summary.json) |  |  | 2026-06-17 | 14KB | `233fd4ed` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_qf/run_metadata.json](ML/reports/cross_instrument_robustness/xagusd_transfer_qf/run_metadata.json) |  |  | 2026-06-17 | 95B | `5cc06b98` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_qf/summary.json](ML/reports/cross_instrument_robustness/xagusd_transfer_qf/summary.json) |  |  | 2026-06-17 | 8KB | `9432f622` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/run_metadata.json](ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/run_metadata.json) |  |  | 2026-06-17 | 95B | `b8c4d5ef` |
| [ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/summary.json](ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/summary.json) |  |  | 2026-06-17 | 14KB | `e79a0708` |
| [ML/reports/cross_instrument_robustness/xauusd_provider_drift/run_metadata.json](ML/reports/cross_instrument_robustness/xauusd_provider_drift/run_metadata.json) |  |  | 2026-06-17 | 95B | `543171a5` |
| [ML/reports/cross_instrument_robustness/xauusd_provider_drift/summary.json](ML/reports/cross_instrument_robustness/xauusd_provider_drift/summary.json) |  |  | 2026-06-17 | 31KB | `6f9ff316` |
| [ML/reports/current_feature_importance/report.md](ML/reports/current_feature_importance/report.md) |  |  | 2026-06-17 | 2KB | `c58147a6` |
| [ML/reports/current_feature_importance/summary.json](ML/reports/current_feature_importance/summary.json) |  |  | 2026-06-17 | 498B | `a286b27a` |
| [ML/reports/direct_direction_chain_audit/minimal_repro_checks.json](ML/reports/direct_direction_chain_audit/minimal_repro_checks.json) |  |  | 2026-06-17 | 3KB | `221806f9` |
| [ML/reports/direction_inside_frozen_movement_regime.json](ML/reports/direction_inside_frozen_movement_regime.json) |  |  | 2026-07-20 | 22KB | `f879bd3a` |
| [ML/reports/direction_only_signal.json](ML/reports/direction_only_signal.json) |  |  | 2026-06-17 | 2KB | `e760a7ba` |
| [ML/reports/entry_based_movement_filter.json](ML/reports/entry_based_movement_filter.json) |  |  | 2026-07-20 | 5KB | `4df425e2` |
| [ML/reports/entry_based_movement_filter_freeze.json](ML/reports/entry_based_movement_filter_freeze.json) |  |  | 2026-07-20 | 14KB | `e0dcfc86` |
| [ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/run_metadata.json) |  |  | 2026-06-17 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/summary.json) |  |  | 2026-06-17 | 10KB | `f4c3f606` |
| [ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/run_metadata.json) |  |  | 2026-06-17 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/summary.json) |  |  | 2026-06-17 | 9KB | `9456a70e` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/EURUSD/eurusd_transfer_manifest.json) |  |  | 2026-06-17 | 807B | `80a032aa` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/GBPUSD/gbpusd_transfer_manifest.json) |  |  | 2026-06-17 | 807B | `a49a431f` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json) |  |  | 2026-06-17 | 807B | `691efe84` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/XAGUSD/xagusd_transfer_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/XAGUSD/xagusd_transfer_manifest.json) |  |  | 2026-06-17 | 807B | `e298a870` |
| [ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/xauusd_provider_drift_manifest.json](ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/xauusd_provider_drift_manifest.json) |  |  | 2026-06-17 | 842B | `fdd42363` |
| [ML/reports/entry_path_cross_instrument_robustness/manifest_metaquotes_baseline.json](ML/reports/entry_path_cross_instrument_robustness/manifest_metaquotes_baseline.json) |  |  | 2026-06-17 | 775B | `6542c434` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/run_metadata.json) |  |  | 2026-06-17 | 95B | `77c70099` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json) |  |  | 2026-06-17 | 9KB | `ed311b43` |
| [ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json](ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json) |  |  | 2026-06-17 | 353B | `388b418f` |
| [ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/run_metadata.json) |  |  | 2026-06-17 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/summary.json) |  |  | 2026-06-17 | 10KB | `cf25db3c` |
| [ML/reports/entry_path_cross_instrument_robustness/verdict_overview.json](ML/reports/entry_path_cross_instrument_robustness/verdict_overview.json) |  |  | 2026-06-17 | 3KB | `eebe1587` |
| [ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/run_metadata.json) |  |  | 2026-06-17 | 95B | `5cc06b98` |
| [ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/summary.json](ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/summary.json) |  |  | 2026-06-17 | 9KB | `83551bb6` |
| [ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/run_metadata.json](ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/run_metadata.json) |  |  | 2026-06-17 | 95B | `77c70099` |
| [ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/summary.json](ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/summary.json) |  |  | 2026-06-17 | 9KB | `690af70a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 536B | `2dbd3e0a` |
| [ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_head_split/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `2f9e801c` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 536B | `7b9539cf` |
| [ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls20/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 2KB | `062a50ec` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 544B | `7d0c8863` |
| [ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_pathcls_sequence/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `756079bf` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 541B | `201a0e3e` |
| [ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_after_selection_guard/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `a077c548` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 528B | `a9a86071` |
| [ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_compare_path6/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `ece7ee12` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 521B | `d4d1887c` |
| [ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_narrow/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `e186a9fd` |
| [ML/reports/entry_path_trade_filter_report.md](ML/reports/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 495B | `e8a9e03d` |
| [ML/reports/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `ead9e11c` |
| [ML/reports/entry_path_v1_all_rows_ranking/summary.json](ML/reports/entry_path_v1_all_rows_ranking/summary.json) |  |  | 2026-06-17 | 9KB | `c68a7074` |
| [ML/reports/entry_path_v1_all_rows_ranking/summary.md](ML/reports/entry_path_v1_all_rows_ranking/summary.md) |  |  | 2026-06-17 | 1KB | `975255a2` |
| [ML/reports/entry_path_v1_binary_direction/frozen_test.json](ML/reports/entry_path_v1_binary_direction/frozen_test.json) |  |  | 2026-06-17 | 1KB | `1dfea12b` |
| [ML/reports/entry_path_v1_binary_direction/summary.json](ML/reports/entry_path_v1_binary_direction/summary.json) |  |  | 2026-06-17 | 1KB | `8b9fe83c` |
| [ML/reports/entry_path_v1_causal_surrogate/summary.json](ML/reports/entry_path_v1_causal_surrogate/summary.json) |  |  | 2026-06-17 | 3KB | `30d10ab7` |
| [ML/reports/entry_path_v1_causal_surrogate/summary.md](ML/reports/entry_path_v1_causal_surrogate/summary.md) |  |  | 2026-06-17 | 542B | `0e0a1c3b` |
| [ML/reports/entry_path_v1_direct_bar_model/summary.json](ML/reports/entry_path_v1_direct_bar_model/summary.json) |  |  | 2026-06-17 | 6KB | `13bc1992` |
| [ML/reports/entry_path_v1_direct_bar_model/summary.md](ML/reports/entry_path_v1_direct_bar_model/summary.md) |  |  | 2026-06-17 | 694B | `902cd983` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E0_ablation_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E0_ablation_results.md) |  |  | 2026-06-17 | 2KB | `18906d28` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E1_binary_direction_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E1_binary_direction_results.md) |  |  | 2026-06-17 | 2KB | `a4ef3f83` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E2_hgb_lr_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E2_hgb_lr_results.md) |  |  | 2026-06-17 | 1KB | `96e420c3` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E3_zone_features_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E3_zone_features_results.md) |  |  | 2026-06-17 | 1KB | `205b1514` |
| [ML/reports/entry_path_v1_direct_direction_improvement/E5_score_direction_results.md](ML/reports/entry_path_v1_direct_direction_improvement/E5_score_direction_results.md) |  |  | 2026-06-17 | 2KB | `5117d4e1` |
| [ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md](ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md) |  |  | 2026-06-17 | 5KB | `58faba29` |
| [ML/reports/entry_path_v1_fractal_level_direct_direction/feature_audit.json](ML/reports/entry_path_v1_fractal_level_direct_direction/feature_audit.json) |  |  | 2026-06-17 | 3KB | `23085403` |
| [ML/reports/entry_path_v1_fractal_level_direct_direction/summary.json](ML/reports/entry_path_v1_fractal_level_direct_direction/summary.json) |  |  | 2026-06-17 | 10KB | `1c312dd6` |
| [ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json](ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json) |  |  | 2026-06-17 | 2KB | `d5b17f2a` |
| [ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json](ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json) |  |  | 2026-06-17 | 3KB | `70511070` |
| [ML/reports/entry_path_v1_frequency/final_verdict.json](ML/reports/entry_path_v1_frequency/final_verdict.json) |  |  | 2026-06-17 | 637B | `c96361ff` |
| [ML/reports/entry_path_v1_frequency/run_metadata.json](ML/reports/entry_path_v1_frequency/run_metadata.json) |  |  | 2026-06-17 | 218B | `4c8fa299` |
| [ML/reports/entry_path_v1_frequency/selected_candidate.json](ML/reports/entry_path_v1_frequency/selected_candidate.json) |  |  | 2026-06-17 | 251B | `f2b86a6f` |
| [ML/reports/entry_path_v1_frequency_v2/final_verdict.json](ML/reports/entry_path_v1_frequency_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `3fa39482` |
| [ML/reports/entry_path_v1_frequency_v2/run_metadata.json](ML/reports/entry_path_v1_frequency_v2/run_metadata.json) |  |  | 2026-06-17 | 243B | `6316d165` |
| [ML/reports/entry_path_v1_frequency_v2/selected_candidate.json](ML/reports/entry_path_v1_frequency_v2/selected_candidate.json) |  |  | 2026-06-17 | 513B | `b69272ad` |
| [ML/reports/entry_path_v1_live_safe/audit_a/a_family_seed_threshold_audit_summary.json](ML/reports/entry_path_v1_live_safe/audit_a/a_family_seed_threshold_audit_summary.json) |  |  | 2026-06-17 | 1KB | `d554a410` |
| [ML/reports/entry_path_v1_live_safe/audit_a/frozen_a_audit_summary.json](ML/reports/entry_path_v1_live_safe/audit_a/frozen_a_audit_summary.json) |  |  | 2026-06-17 | 1KB | `f031ea71` |
| [ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 519B | `db1d2a0f` |
| [ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `29edc3c4` |
| [ML/reports/entry_path_v1_live_safe/multi_seed_summary.json](ML/reports/entry_path_v1_live_safe/multi_seed_summary.json) |  |  | 2026-06-17 | 2KB | `aa15eb51` |
| [ML/reports/entry_path_v1_live_safe/runtime/runtime_export_metadata.json](ML/reports/entry_path_v1_live_safe/runtime/runtime_export_metadata.json) |  |  | 2026-05-22 | 1KB | `fd8c9377` |
| [ML/reports/entry_path_v1_live_safe/runtime/runtime_state.json](ML/reports/entry_path_v1_live_safe/runtime/runtime_state.json) |  |  | 2026-05-22 | 147B | `6319b661` |
| [ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 557B | `09c8c388` |
| [ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_007/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `1b9cf711` |
| [ML/reports/entry_path_v1_live_safe/seed_007/result.json](ML/reports/entry_path_v1_live_safe/seed_007/result.json) |  |  | 2026-06-17 | 2KB | `21ed6ab7` |
| [ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 528B | `4b967a95` |
| [ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_017/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `a5bedf83` |
| [ML/reports/entry_path_v1_live_safe/seed_017/result.json](ML/reports/entry_path_v1_live_safe/seed_017/result.json) |  |  | 2026-06-17 | 2KB | `3729f8b9` |
| [ML/reports/entry_path_v1_live_safe/seed_042/result.json](ML/reports/entry_path_v1_live_safe/seed_042/result.json) |  |  | 2026-06-17 | 2KB | `f8445a1d` |
| [ML/reports/entry_path_v1_live_safe/seed_042/selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_042/selected_rule.json) |  |  | 2026-06-17 | 1KB | `29edc3c4` |
| [ML/reports/entry_path_v1_live_safe/seed_042/trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_042/trade_filter_report.md) |  |  | 2026-06-17 | 519B | `db1d2a0f` |
| [ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 529B | `b10386a1` |
| [ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_077/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `c9132626` |
| [ML/reports/entry_path_v1_live_safe/seed_077/result.json](ML/reports/entry_path_v1_live_safe/seed_077/result.json) |  |  | 2026-06-17 | 2KB | `9ae2053a` |
| [ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_report.md](ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_report.md) |  |  | 2026-06-17 | 530B | `1410cf6d` |
| [ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_selected_rule.json](ML/reports/entry_path_v1_live_safe/seed_123/entry_path_trade_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `b0da3773` |
| [ML/reports/entry_path_v1_live_safe/seed_123/result.json](ML/reports/entry_path_v1_live_safe/seed_123/result.json) |  |  | 2026-06-17 | 2KB | `1deffb2e` |
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
| [ML/reports/entry_path_v1_nearest_k16/summary.json](ML/reports/entry_path_v1_nearest_k16/summary.json) |  |  | 2026-06-17 | 38KB | `c2cd44e4` |
| [ML/reports/entry_path_v1_nearest_k4_geometry_only/summary.json](ML/reports/entry_path_v1_nearest_k4_geometry_only/summary.json) |  |  | 2026-06-17 | 6KB | `b830fcbe` |
| [ML/reports/entry_path_v1_nearest_k4_hgb/summary.json](ML/reports/entry_path_v1_nearest_k4_hgb/summary.json) |  |  | 2026-06-17 | 10KB | `4f0ded21` |
| [ML/reports/entry_path_v1_nearest_k4_lr/summary.json](ML/reports/entry_path_v1_nearest_k4_lr/summary.json) |  |  | 2026-06-17 | 10KB | `c8272495` |
| [ML/reports/entry_path_v1_nearest_k6/summary.json](ML/reports/entry_path_v1_nearest_k6/summary.json) |  |  | 2026-06-17 | 14KB | `88a47480` |
| [ML/reports/entry_path_v1_nearest_k8/summary.json](ML/reports/entry_path_v1_nearest_k8/summary.json) |  |  | 2026-06-17 | 19KB | `7c4b08bc` |
| [ML/reports/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 706B | `0d99ebcd` |
| [ML/reports/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `f665ab0d` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json) |  |  | 2026-06-17 | 2KB | `c04294b8` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost/n_boost_result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost/n_boost_result.json) |  |  | 2026-06-17 | 1KB | `bc8ca1d1` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 784B | `e322b4af` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `75b5246c` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_007/result.json) |  |  | 2026-06-17 | 2KB | `eae94c0a` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 730B | `3c9becc3` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `75dc9dfe` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_017/result.json) |  |  | 2026-06-17 | 2KB | `2f581d61` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 734B | `93515d31` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 2KB | `8f6e7efa` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_042/result.json) |  |  | 2026-06-17 | 2KB | `0754fd54` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 741B | `b661b8f9` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 2KB | `ef91132b` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_077/result.json) |  |  | 2026-06-17 | 2KB | `18710caf` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_report.md](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_report.md) |  |  | 2026-06-17 | 729B | `0f00805b` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/entry_path_v1_quantile_filter_selected_rule.json) |  |  | 2026-06-17 | 1KB | `7d0d2ea6` |
| [ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/result.json](ML/reports/entry_path_v1_quantile_live_safe_baseline/seed_123/result.json) |  |  | 2026-06-17 | 2KB | `4485f5d3` |
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
| [ML/reports/entry_path_v1_quantile_selected_rule.json](ML/reports/entry_path_v1_quantile_selected_rule.json) |  |  | 2026-06-17 | 2KB | `a2fce0f7` |
| [ML/reports/entry_path_v1_score_direction/summary.json](ML/reports/entry_path_v1_score_direction/summary.json) |  |  | 2026-06-17 | 269B | `761b2790` |
| [ML/reports/entry_path_v1_signal_only_ablation/summary.json](ML/reports/entry_path_v1_signal_only_ablation/summary.json) |  |  | 2026-06-17 | 7KB | `6cf21739` |
| [ML/reports/entry_path_v1_signal_only_ablation/summary.md](ML/reports/entry_path_v1_signal_only_ablation/summary.md) |  |  | 2026-06-17 | 1KB | `ad02cfab` |
| [ML/reports/entry_path_v1_zones/summary.json](ML/reports/entry_path_v1_zones/summary.json) |  |  | 2026-06-17 | 14KB | `95fdf5ac` |
| [ML/reports/entry_path_v1_zones_plus_nearest_k4/summary.json](ML/reports/entry_path_v1_zones_plus_nearest_k4/summary.json) |  |  | 2026-06-17 | 24KB | `46eb5bcc` |
| [ML/reports/evaluate_test_H12.md](ML/reports/evaluate_test_H12.md) |  |  | 2026-06-17 | 513B | `8b8eb347` |
| [ML/reports/evaluate_test_entry_path_v1.md](ML/reports/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `a6f68803` |
| [ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md](ML/reports/evaluate_test_entry_path_v1_features_baseline_clean.md) |  |  | 2026-06-17 | 1KB | `46ed4ec9` |
| [ML/reports/evaluate_test_entry_path_v1_quantile.md](ML/reports/evaluate_test_entry_path_v1_quantile.md) |  |  | 2026-06-17 | 523B | `03c3cfb6` |
| [ML/reports/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-06-17 | 274B | `057fadd1` |
| [ML/reports/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-06-17 | 277B | `1c95661a` |
| [ML/reports/evaluate_test_tb.md](ML/reports/evaluate_test_tb.md) |  |  | 2026-06-17 | 1KB | `295448ff` |
| [ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-06-17 | 385B | `e972ae90` |
| [ML/reports/evaluate_test_trailing_stop_target_v1.md](ML/reports/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-06-17 | 304B | `087f3217` |
| [ML/reports/evaluate_validation_entry_path_v1.md](ML/reports/evaluate_validation_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `6eb89813` |
| [ML/reports/execution_policy_v2/frequency_trail_scan/summary.json](ML/reports/execution_policy_v2/frequency_trail_scan/summary.json) |  |  | 2026-06-17 | 3KB | `8a130d60` |
| [ML/reports/execution_policy_v2/summary.json](ML/reports/execution_policy_v2/summary.json) |  |  | 2026-06-17 | 26KB | `63d0a3c5` |
| [ML/reports/fav_3_vs_12_standalone/run_metadata.json](ML/reports/fav_3_vs_12_standalone/run_metadata.json) |  |  | 2026-06-17 | 1KB | `749e6a5b` |
| [ML/reports/fav_3_vs_12_standalone/selected_threshold.json](ML/reports/fav_3_vs_12_standalone/selected_threshold.json) |  |  | 2026-06-17 | 532B | `d941fc13` |
| [ML/reports/fav_3_vs_12_standalone/verdict.json](ML/reports/fav_3_vs_12_standalone/verdict.json) |  |  | 2026-06-17 | 893B | `1fc84a37` |
| [ML/reports/feature_bank_clean_comparison/report.md](ML/reports/feature_bank_clean_comparison/report.md) |  |  | 2026-06-17 | 1KB | `ea8f6f93` |
| [ML/reports/feature_bank_clean_comparison/summary.json](ML/reports/feature_bank_clean_comparison/summary.json) |  |  | 2026-06-17 | 1KB | `84b8ec2f` |
| [ML/reports/feature_bank_comparison/report.md](ML/reports/feature_bank_comparison/report.md) |  |  | 2026-06-17 | 1KB | `f4f494ed` |
| [ML/reports/feature_bank_comparison/summary.json](ML/reports/feature_bank_comparison/summary.json) |  |  | 2026-06-17 | 1KB | `97d30738` |
| [ML/reports/fractal0_entry_exit_grid.json](ML/reports/fractal0_entry_exit_grid.json) |  |  | 2026-07-29 | 37KB | `e2d18822` |
| [ML/reports/fractal0_entry_exit_grid_m5_full.json](ML/reports/fractal0_entry_exit_grid_m5_full.json) |  |  | 2026-07-29 | 36KB | `1fdf8f40` |
| [ML/reports/fractal0_entry_exit_grid_m5_winner.json](ML/reports/fractal0_entry_exit_grid_m5_winner.json) |  |  | 2026-07-29 | 3KB | `832edcae` |
| [ML/reports/fractal0_entry_quality_filter.json](ML/reports/fractal0_entry_quality_filter.json) |  |  | 2026-07-29 | 29KB | `1968cec0` |
| [ML/reports/fractal0_fixed11_candidate_audit.json](ML/reports/fractal0_fixed11_candidate_audit.json) |  |  | 2026-07-29 | 6KB | `25e76fe9` |
| [ML/reports/fractal0_fixed11_current_history_comparison.json](ML/reports/fractal0_fixed11_current_history_comparison.json) |  |  | 2026-07-29 | 16KB | `09ff58f8` |
| [ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json](ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json) |  |  | 2026-07-29 | 1KB | `f9c41c45` |
| [ML/reports/fractal0_fixed11_internal_closure_rerun.json](ML/reports/fractal0_fixed11_internal_closure_rerun.json) |  |  | 2026-07-29 | 10KB | `8680ed76` |
| [ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json](ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json) |  |  | 2026-07-29 | 194KB | `b616f0c9` |
| [ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json](ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json) |  |  | 2026-07-29 | 3KB | `4165a1a9` |
| [ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json](ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json) |  |  | 2026-07-29 | 2KB | `0d1e0a82` |
| [ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json](ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json) |  |  | 2026-07-29 | 14KB | `5d4041b3` |
| [ML/reports/fractal0_fixed11_retained_mt4_parity/fixed11_rule_signal_exports.json](ML/reports/fractal0_fixed11_retained_mt4_parity/fixed11_rule_signal_exports.json) |  |  | 2026-07-29 | 3KB | `4c1d8c05` |
| [ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json](ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json) |  |  | 2026-07-29 | 2KB | `00a86f7d` |
| [ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py](ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py) |  |  | 2026-07-29 | 14KB | `f2c1cee7` |
| [ML/reports/fractal0_fixed11_rich_entry_locked_test.json](ML/reports/fractal0_fixed11_rich_entry_locked_test.json) |  |  | 2026-07-29 | 2KB | `374ed486` |
| [ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json](ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json) |  |  | 2026-07-29 | 3KB | `6a8ea239` |
| [ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json](ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json) |  |  | 2026-07-29 | 4KB | `5bd02cdf` |
| [ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json](ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json) |  |  | 2026-07-29 | 4KB | `e6ae7b37` |
| [ML/reports/fractal0_stop_grid_m5.json](ML/reports/fractal0_stop_grid_m5.json) |  |  | 2026-07-29 | 51KB | `99c3e349` |
| [ML/reports/fractal_ablation.json](ML/reports/fractal_ablation.json) |  |  | 2026-06-17 | 14KB | `087d60c8` |
| [ML/reports/fractal_ablation_test.json](ML/reports/fractal_ablation_test.json) |  |  | 2026-06-17 | 10KB | `5de28e52` |
| [ML/reports/fractal_stop_breach_baseline.json](ML/reports/fractal_stop_breach_baseline.json) |  |  | 2026-06-17 | 12KB | `9920d61d` |
| [ML/reports/fractal_stop_breach_frozen_test.json](ML/reports/fractal_stop_breach_frozen_test.json) |  |  | 2026-06-17 | 7KB | `22b13f6c` |
| [ML/reports/fractal_stop_fav_frozen_rule.json](ML/reports/fractal_stop_fav_frozen_rule.json) |  |  | 2026-06-17 | 308B | `a5acd8d7` |
| [ML/reports/fractal_stop_fav_frozen_test.json](ML/reports/fractal_stop_fav_frozen_test.json) |  |  | 2026-06-17 | 4KB | `9a68bebd` |
| [ML/reports/frozen_exit_policy.json](ML/reports/frozen_exit_policy.json) |  |  | 2026-06-17 | 537B | `4da12318` |
| [ML/reports/label_convention_audit.md](ML/reports/label_convention_audit.md) |  |  | 2026-06-17 | 3KB | `72706b95` |
| [ML/reports/leaderboard_closure_audit.json](ML/reports/leaderboard_closure_audit.json) |  |  | 2026-07-29 | 4KB | `b3bde77c` |
| [ML/reports/limit_order_transformer.json](ML/reports/limit_order_transformer.json) |  |  | 2026-06-17 | 1KB | `e843ef45` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/artifact_inventory.json](ML/reports/live_safe_ml_audit/entry_path_v1/artifact_inventory.json) |  |  | 2026-06-17 | 997B | `2c0fea7b` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/entry_path_v1/legacy_export_metadata.json) |  |  | 2026-06-17 | 347B | `7e79d1b9` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/legacy_reproduction.json](ML/reports/live_safe_ml_audit/entry_path_v1/legacy_reproduction.json) |  |  | 2026-06-17 | 2KB | `7cd7e9b2` |
| [ML/reports/live_safe_ml_audit/entry_path_v1/verdict.json](ML/reports/live_safe_ml_audit/entry_path_v1/verdict.json) |  |  | 2026-06-17 | 513B | `0989534c` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/artifact_inventory.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/artifact_inventory.json) |  |  | 2026-06-17 | 1KB | `1c5709af` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_export_metadata.json) |  |  | 2026-06-17 | 444B | `cba4678a` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_reproduction.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/legacy_reproduction.json) |  |  | 2026-06-17 | 1KB | `3a2da5c7` |
| [ML/reports/live_safe_ml_audit/entry_path_v1_quantile/verdict.json](ML/reports/live_safe_ml_audit/entry_path_v1_quantile/verdict.json) |  |  | 2026-06-17 | 539B | `d610f477` |
| [ML/reports/live_safe_ml_audit/feature_contract_summary.json](ML/reports/live_safe_ml_audit/feature_contract_summary.json) |  |  | 2026-06-17 | 658B | `edf19ffe` |
| [ML/reports/live_safe_ml_audit/frequency/artifact_inventory.json](ML/reports/live_safe_ml_audit/frequency/artifact_inventory.json) |  |  | 2026-06-17 | 870B | `309ff4de` |
| [ML/reports/live_safe_ml_audit/frequency/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/frequency/legacy_export_metadata.json) |  |  | 2026-06-17 | 715B | `efac01ff` |
| [ML/reports/live_safe_ml_audit/frequency/legacy_reproduction.json](ML/reports/live_safe_ml_audit/frequency/legacy_reproduction.json) |  |  | 2026-06-17 | 1KB | `ef368484` |
| [ML/reports/live_safe_ml_audit/frequency/verdict.json](ML/reports/live_safe_ml_audit/frequency/verdict.json) |  |  | 2026-06-17 | 729B | `b283e698` |
| [ML/reports/live_safe_ml_audit/legacy_export_summary.json](ML/reports/live_safe_ml_audit/legacy_export_summary.json) |  |  | 2026-06-17 | 4KB | `1421df0f` |
| [ML/reports/live_safe_ml_audit/legacy_reproduction_summary.json](ML/reports/live_safe_ml_audit/legacy_reproduction_summary.json) |  |  | 2026-06-17 | 8KB | `479e2c1c` |
| [ML/reports/live_safe_ml_audit/manifest.json](ML/reports/live_safe_ml_audit/manifest.json) |  |  | 2026-06-17 | 9KB | `48b1dbb4` |
| [ML/reports/live_safe_ml_audit/original_plus_path/artifact_inventory.json](ML/reports/live_safe_ml_audit/original_plus_path/artifact_inventory.json) |  |  | 2026-06-17 | 1KB | `d7a6d667` |
| [ML/reports/live_safe_ml_audit/original_plus_path/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/original_plus_path/legacy_export_metadata.json) |  |  | 2026-06-17 | 795B | `b0de7ed0` |
| [ML/reports/live_safe_ml_audit/original_plus_path/legacy_reproduction.json](ML/reports/live_safe_ml_audit/original_plus_path/legacy_reproduction.json) |  |  | 2026-06-17 | 1KB | `941b3788` |
| [ML/reports/live_safe_ml_audit/original_plus_path/verdict.json](ML/reports/live_safe_ml_audit/original_plus_path/verdict.json) |  |  | 2026-06-17 | 738B | `5e473c4d` |
| [ML/reports/live_safe_ml_audit/quality/artifact_inventory.json](ML/reports/live_safe_ml_audit/quality/artifact_inventory.json) |  |  | 2026-06-17 | 864B | `094256c6` |
| [ML/reports/live_safe_ml_audit/quality/legacy_export_metadata.json](ML/reports/live_safe_ml_audit/quality/legacy_export_metadata.json) |  |  | 2026-06-17 | 708B | `61748342` |
| [ML/reports/live_safe_ml_audit/quality/legacy_reproduction.json](ML/reports/live_safe_ml_audit/quality/legacy_reproduction.json) |  |  | 2026-06-17 | 1KB | `ddcff55b` |
| [ML/reports/live_safe_ml_audit/quality/verdict.json](ML/reports/live_safe_ml_audit/quality/verdict.json) |  |  | 2026-06-17 | 727B | `6e173e29` |
| [ML/reports/live_safe_ml_audit/verdict_summary.json](ML/reports/live_safe_ml_audit/verdict_summary.json) |  |  | 2026-06-17 | 3KB | `d1d7c226` |
| [ML/reports/methodology_cycle_candidate_source_v2/README.md](ML/reports/methodology_cycle_candidate_source_v2/README.md) |  |  | 2026-06-17 | 3KB | `93b1a5fc` |
| [ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md](ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md) |  |  | 2026-06-17 | 2KB | `87798cc8` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json](ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json) |  |  | 2026-06-17 | 3KB | `929dd33f` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json](ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json) |  |  | 2026-06-17 | 5KB | `4f490eb2` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json](ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json) |  |  | 2026-06-17 | 4KB | `ab4f45ad` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json](ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json) |  |  | 2026-06-17 | 3KB | `cffbff43` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage03_leakage_gate.json](ML/reports/methodology_cycle_candidate_source_v2/stage03_leakage_gate.json) |  |  | 2026-06-17 | 4KB | `5f498f87` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage04_labeling_audit.json](ML/reports/methodology_cycle_candidate_source_v2/stage04_labeling_audit.json) |  |  | 2026-06-17 | 5KB | `d5009b71` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json](ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json) |  |  | 2026-06-17 | 3KB | `48862ccc` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage06_temporal_split_manifest.json](ML/reports/methodology_cycle_candidate_source_v2/stage06_temporal_split_manifest.json) |  |  | 2026-06-17 | 2KB | `29823971` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json](ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json) |  |  | 2026-06-17 | 16KB | `02fc44ba` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json](ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json) |  |  | 2026-06-17 | 2KB | `4d07ed46` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json](ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json) |  |  | 2026-06-17 | 2KB | `b0280abd` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json](ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json) |  |  | 2026-06-17 | 116KB | `07346468` |
| [ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json](ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json) |  |  | 2026-06-17 | 7KB | `8c158f4f` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json](ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json) |  |  | 2026-06-17 | 3KB | `14b7cc3f` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json](ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json) |  |  | 2026-06-17 | 3KB | `bacc13b6` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.json](ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.json) |  |  | 2026-06-17 | 3KB | `5cb5fe58` |
| [ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.md](ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025/summary.md) |  |  | 2026-06-17 | 279B | `75a53f21` |
| [ML/reports/mt5_execution_loop/README.md](ML/reports/mt5_execution_loop/README.md) |  |  | 2026-07-30 | 739B | `34a0d75f` |
| [ML/reports/mt5_execution_loop/batch/_smoke/metrics.json](ML/reports/mt5_execution_loop/batch/_smoke/metrics.json) |  |  | 2026-07-31 | 866B | `060d2e0d` |
| [ML/reports/mt5_execution_loop/batch/batch_summary.json](ML/reports/mt5_execution_loop/batch/batch_summary.json) |  |  | 2026-07-31 | 66KB | `e8e53bc7` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `e0e11c22` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.05/metrics.json) |  |  | 2026-07-31 | 883B | `d11f2f13` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `0ef53a4c` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.1/metrics.json) |  |  | 2026-07-31 | 898B | `4d612af7` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `97bf0926` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.2/metrics.json) |  |  | 2026-07-31 | 906B | `d8309907` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `74c6d578` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_12h_thr0.3/metrics.json) |  |  | 2026-07-31 | 900B | `9703e5a5` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `3c2b72f6` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.05/metrics.json) |  |  | 2026-07-31 | 887B | `85fbae75` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `cef379f8` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.1/metrics.json) |  |  | 2026-07-31 | 896B | `94f5c93d` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `bbdcc4b5` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.2/metrics.json) |  |  | 2026-07-31 | 883B | `83e78655` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `2c4b8775` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_24h_thr0.3/metrics.json) |  |  | 2026-07-31 | 884B | `09fad76a` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `56559f46` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.05/metrics.json) |  |  | 2026-07-31 | 898B | `36ed941a` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `f79bdd5e` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.1/metrics.json) |  |  | 2026-07-31 | 901B | `6625ceaf` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `4da43faf` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.2/metrics.json) |  |  | 2026-07-31 | 913B | `409d3c63` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `c97d5a4c` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_3h_thr0.3/metrics.json) |  |  | 2026-07-31 | 914B | `9e9122a1` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `6838ec85` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.05/metrics.json) |  |  | 2026-07-31 | 895B | `f0d5e51b` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `ad28f579` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.1/metrics.json) |  |  | 2026-07-31 | 898B | `33112b61` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `39fee4c8` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.2/metrics.json) |  |  | 2026-07-31 | 911B | `0c0acba6` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `bf8c366d` |
| [ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/simple_combined_extra_trees_small_6h_thr0.3/metrics.json) |  |  | 2026-07-31 | 912B | `67436c0b` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `a4b29ab2` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.05/metrics.json) |  |  | 2026-07-31 | 895B | `767f4151` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `fc21593c` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.1/metrics.json) |  |  | 2026-07-31 | 883B | `fbdcb423` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `a147d41e` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.2/metrics.json) |  |  | 2026-07-31 | 895B | `739c2857` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `388cd82a` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_12h_thr0.3/metrics.json) |  |  | 2026-07-31 | 902B | `a5a957af` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `60ad081e` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.05/metrics.json) |  |  | 2026-07-31 | 896B | `57fa377e` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `05003ca2` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.1/metrics.json) |  |  | 2026-07-31 | 884B | `8dc4a00a` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `7a1a5a8a` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.2/metrics.json) |  |  | 2026-07-31 | 884B | `2786f73f` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `0181dc34` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_24h_thr0.3/metrics.json) |  |  | 2026-07-31 | 900B | `4926f537` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `6e2aae56` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.05/metrics.json) |  |  | 2026-07-31 | 898B | `28c1bc74` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `dd3ad334` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.1/metrics.json) |  |  | 2026-07-31 | 899B | `5c35bb54` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `29f03def` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.2/metrics.json) |  |  | 2026-07-31 | 914B | `7649eae4` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `33494778` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_extra_trees_small_6h_thr0.3/metrics.json) |  |  | 2026-07-31 | 899B | `4fa81eaa` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.05/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.05/entry_signals.json) |  |  | 2026-07-31 | 1KB | `48b9526b` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.05/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.05/metrics.json) |  |  | 2026-07-31 | 887B | `0d863343` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.1/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.1/entry_signals.json) |  |  | 2026-07-31 | 1KB | `6d1819f2` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.1/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.1/metrics.json) |  |  | 2026-07-31 | 885B | `b81adec2` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.2/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.2/entry_signals.json) |  |  | 2026-07-31 | 1KB | `0c73e4ac` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.2/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.2/metrics.json) |  |  | 2026-07-31 | 905B | `e1b5f7f4` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.3/entry_signals.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.3/entry_signals.json) |  |  | 2026-07-31 | 1KB | `25cb08cc` |
| [ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.3/metrics.json](ML/reports/mt5_execution_loop/batch/time_plus_atr_hist_gradient_boosting_3h_thr0.3/metrics.json) |  |  | 2026-07-31 | 894B | `0bd0109e` |
| [ML/reports/mt5_execution_loop/batch_selection_contract.json](ML/reports/mt5_execution_loop/batch_selection_contract.json) |  |  | 2026-07-31 | 1KB | `69734050` |
| [ML/reports/mt5_execution_loop/diagnostics/error_inventory.json](ML/reports/mt5_execution_loop/diagnostics/error_inventory.json) |  |  | 2026-08-01 | 13KB | `66a1b685` |
| [ML/reports/mt5_execution_loop/diagnostics/error_summary.json](ML/reports/mt5_execution_loop/diagnostics/error_summary.json) |  |  | 2026-08-01 | 8KB | `bc49c7bd` |
| [ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json](ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json) |  |  | 2026-08-01 | 25KB | `15bf13e2` |
| [ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json](ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json) |  |  | 2026-08-01 | 58KB | `b275d3c9` |
| [ML/reports/mt5_execution_loop/manual_run_manifest_template.json](ML/reports/mt5_execution_loop/manual_run_manifest_template.json) |  |  | 2026-07-30 | 714B | `5a2309af` |
| [ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.json](ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.json) |  |  | 2026-07-30 | 1KB | `3d88d62b` |
| [ML/reports/mt5_execution_loop/mt5_entry_source_20260730_entry_quality_filter.json](ML/reports/mt5_execution_loop/mt5_entry_source_20260730_entry_quality_filter.json) |  |  | 2026-07-30 | 732B | `9285f6a5` |
| [ML/reports/mt5_execution_loop/mt5_environment_manifest.json](ML/reports/mt5_execution_loop/mt5_environment_manifest.json) |  |  | 2026-07-30 | 1KB | `507f42d0` |
| [ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json](ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json) |  |  | 2026-07-31 | 648B | `a4462ed5` |
| [ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json](ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json) |  |  | 2026-07-31 | 902B | `387cf50e` |
| [ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json](ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json) |  |  | 2026-07-30 | 704B | `54270838` |
| [ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json](ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json) |  |  | 2026-07-31 | 2KB | `913a972f` |
| [ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json](ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json) |  |  | 2026-07-31 | 4KB | `dd3efb21` |
| [ML/reports/mt5_nero_parity/mt5_nero_parity_manifest.json](ML/reports/mt5_nero_parity/mt5_nero_parity_manifest.json) |  |  | 2026-07-31 | 1KB | `efd3bffc` |
| [ML/reports/mt5_nero_parity/nero_parity_by_time.json](ML/reports/mt5_nero_parity/nero_parity_by_time.json) |  |  | 2026-07-31 | 655B | `67aeccb6` |
| [ML/reports/mt5_nero_parity/nero_parity_comparison.json](ML/reports/mt5_nero_parity/nero_parity_comparison.json) |  |  | 2026-07-31 | 3KB | `115a6b1f` |
| [ML/reports/mt5_nero_parity/nero_parity_comparison_v2.json](ML/reports/mt5_nero_parity/nero_parity_comparison_v2.json) |  |  | 2026-07-31 | 3KB | `f18f908e` |
| [ML/reports/n_boost_result.json](ML/reports/n_boost_result.json) |  |  | 2026-06-17 | 1KB | `9248dae1` |
| [ML/reports/next_open_entry_updn_foundation.json](ML/reports/next_open_entry_updn_foundation.json) |  |  | 2026-07-20 | 22KB | `5e26459c` |
| [ML/reports/optuna_best_params_bilstm_regression.json](ML/reports/optuna_best_params_bilstm_regression.json) |  |  | 2026-06-17 | 496B | `b1a36a79` |
| [ML/reports/optuna_best_params_cnn1d_classification.json](ML/reports/optuna_best_params_cnn1d_classification.json) |  |  | 2026-06-17 | 461B | `25ae2754` |
| [ML/reports/optuna_best_params_transformer_regression_updn.json](ML/reports/optuna_best_params_transformer_regression_updn.json) |  |  | 2026-06-17 | 539B | `5a6d031a` |
| [ML/reports/optuna_study_bilstm_regression_20260311_223415.json](ML/reports/optuna_study_bilstm_regression_20260311_223415.json) |  |  | 2026-06-17 | 1KB | `f908cbce` |
| [ML/reports/optuna_study_bilstm_regression_20260312_003636.json](ML/reports/optuna_study_bilstm_regression_20260312_003636.json) |  |  | 2026-06-17 | 31KB | `8318dd5a` |
| [ML/reports/optuna_study_bilstm_regression_20260312_105613.json](ML/reports/optuna_study_bilstm_regression_20260312_105613.json) |  |  | 2026-06-17 | 18KB | `9860a4c5` |
| [ML/reports/optuna_study_bilstm_regression_20260312_112811.json](ML/reports/optuna_study_bilstm_regression_20260312_112811.json) |  |  | 2026-06-17 | 18KB | `535d2951` |
| [ML/reports/optuna_study_bilstm_regression_20260316_102024.json](ML/reports/optuna_study_bilstm_regression_20260316_102024.json) |  |  | 2026-06-17 | 31KB | `ef829e93` |
| [ML/reports/optuna_study_cnn1d_classification_20260226_134119.json](ML/reports/optuna_study_cnn1d_classification_20260226_134119.json) |  |  | 2026-06-17 | 29KB | `a53f62cd` |
| [ML/reports/optuna_study_cnn1d_classification_20260227_231828.json](ML/reports/optuna_study_cnn1d_classification_20260227_231828.json) |  |  | 2026-06-17 | 28KB | `f8e66057` |
| [ML/reports/optuna_study_cnn1d_classification_20260228_100415.json](ML/reports/optuna_study_cnn1d_classification_20260228_100415.json) |  |  | 2026-06-17 | 29KB | `c38b7403` |
| [ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json](ML/reports/optuna_study_transformer_regression_updn_20260319_172657.json) |  |  | 2026-06-17 | 33KB | `2c98a9f9` |
| [ML/reports/oracle_fractal_stop_fav.json](ML/reports/oracle_fractal_stop_fav.json) |  |  | 2026-06-17 | 57KB | `38a0f5b5` |
| [ML/reports/outcome_target_validation_benchmark.md](ML/reports/outcome_target_validation_benchmark.md) |  |  | 2026-06-17 | 763B | `9104e652` |
| [ML/reports/pf_uplift_discovery/baseline_numbers.json](ML/reports/pf_uplift_discovery/baseline_numbers.json) |  |  | 2026-06-17 | 2KB | `4519e3fe` |
| [ML/reports/pf_uplift_discovery/hypotheses_longlist.md](ML/reports/pf_uplift_discovery/hypotheses_longlist.md) |  |  | 2026-06-17 | 8KB | `61fcd585` |
| [ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json](ML/reports/pf_uplift_discovery/probe_f_interval_width_le_q50.json) |  |  | 2026-06-17 | 602B | `d5ab62dc` |
| [ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json](ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json) |  |  | 2026-06-17 | 536B | `afb475b6` |
| [ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json) |  |  | 2026-06-17 | 655B | `1db83311` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q1_exclusion.json) |  |  | 2026-06-17 | 665B | `8da7e815` |
| [ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json](ML/reports/pf_uplift_discovery/probe_r_vol_q4_exclusion.json) |  |  | 2026-06-17 | 623B | `866da98b` |
| [ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json](ML/reports/pf_uplift_discovery/probe_s_Early_timeout_hold_b.json) |  |  | 2026-06-17 | 614B | `2146acd5` |
| [ML/reports/pf_uplift_discovery/run_metadata.json](ML/reports/pf_uplift_discovery/run_metadata.json) |  |  | 2026-06-17 | 552B | `2ffaa2db` |
| [ML/reports/quantile_fav_composition/intersection_diagnostic.json](ML/reports/quantile_fav_composition/intersection_diagnostic.json) |  |  | 2026-06-17 | 270B | `8877d751` |
| [ML/reports/quantile_fav_composition/n_boost_composition.json](ML/reports/quantile_fav_composition/n_boost_composition.json) |  |  | 2026-06-17 | 155B | `164387a5` |
| [ML/reports/quantile_fav_composition/run_metadata.json](ML/reports/quantile_fav_composition/run_metadata.json) |  |  | 2026-06-17 | 4KB | `6aa02ee6` |
| [ML/reports/quantile_fav_composition/test_metrics.json](ML/reports/quantile_fav_composition/test_metrics.json) |  |  | 2026-06-17 | 1KB | `86714f9b` |
| [ML/reports/quantile_fav_composition/updn_active_source/metadata.json](ML/reports/quantile_fav_composition/updn_active_source/metadata.json) |  |  | 2026-06-17 | 619B | `d44841e2` |
| [ML/reports/quantile_fav_composition/validation_metrics.json](ML/reports/quantile_fav_composition/validation_metrics.json) |  |  | 2026-06-17 | 1KB | `7583bfeb` |
| [ML/reports/quantile_forward_validation/run_metadata.json](ML/reports/quantile_forward_validation/run_metadata.json) |  |  | 2026-06-17 | 554B | `eeb46771` |
| [ML/reports/quantile_forward_validation/summary.json](ML/reports/quantile_forward_validation/summary.json) |  |  | 2026-06-17 | 440B | `f208a93b` |
| [ML/reports/quantile_relaxed_composition/selected_baseline.json](ML/reports/quantile_relaxed_composition/selected_baseline.json) |  |  | 2026-06-17 | 118B | `3c6efae0` |
| [ML/reports/regression_updn_already_moved_audit.json](ML/reports/regression_updn_already_moved_audit.json) |  |  | 2026-07-20 | 42KB | `0ceab39f` |
| [ML/reports/reproducibility_report_12H.md](ML/reports/reproducibility_report_12H.md) |  |  | 2026-06-17 | 1KB | `c9af48ba` |
| [ML/reports/rf_gridsearch.json](ML/reports/rf_gridsearch.json) |  |  | 2026-06-17 | 1KB | `66d3935f` |
| [ML/reports/signal_export_parity/original_plus_path_20260420/summary.json](ML/reports/signal_export_parity/original_plus_path_20260420/summary.json) |  |  | 2026-06-17 | 3KB | `b17fa136` |
| [ML/reports/signal_export_parity/original_plus_path_20260420/summary.md](ML/reports/signal_export_parity/original_plus_path_20260420/summary.md) |  |  | 2026-06-17 | 1KB | `aa632197` |
| [ML/reports/stage3_1_profiles.json](ML/reports/stage3_1_profiles.json) |  |  | 2026-06-17 | 41KB | `0d1523da` |
| [ML/reports/stage3_profiles.json](ML/reports/stage3_profiles.json) |  |  | 2026-06-17 | 23KB | `397bda74` |
| [ML/reports/stage4_1.json](ML/reports/stage4_1.json) |  |  | 2026-06-17 | 6KB | `81f4f4f1` |
| [ML/reports/stage4_2_diagnostic.json](ML/reports/stage4_2_diagnostic.json) |  |  | 2026-06-17 | 1KB | `ed511aae` |
| [ML/reports/stage4_3_diagnostics.json](ML/reports/stage4_3_diagnostics.json) |  |  | 2026-06-17 | 50KB | `65448869` |
| [ML/reports/stage4_4_micro_check.json](ML/reports/stage4_4_micro_check.json) |  |  | 2026-06-17 | 15KB | `e0850d4e` |
| [ML/reports/stage4_5_exit_mechanics.json](ML/reports/stage4_5_exit_mechanics.json) |  |  | 2026-06-17 | 4KB | `a8de34ca` |
| [ML/reports/stage4_6_clean_cycle.json](ML/reports/stage4_6_clean_cycle.json) |  |  | 2026-06-17 | 3KB | `a1d1598c` |
| [ML/reports/stage4_gap_diagnostics.json](ML/reports/stage4_gap_diagnostics.json) |  |  | 2026-06-17 | 3KB | `930b5cab` |
| [ML/reports/stage4_improvements.json](ML/reports/stage4_improvements.json) |  |  | 2026-06-17 | 4KB | `1ac61b5e` |
| [ML/reports/stage4_trade.json](ML/reports/stage4_trade.json) |  |  | 2026-06-17 | 11KB | `090781cd` |
| [ML/reports/stage4_trade_geom.json](ML/reports/stage4_trade_geom.json) |  |  | 2026-06-17 | 11KB | `b48673bf` |
| [ML/reports/stage5_0d_diagnostic_screening.json](ML/reports/stage5_0d_diagnostic_screening.json) |  |  | 2026-06-24 | 36KB | `53265c38` |
| [ML/reports/stage5_prep_diagnostics.json](ML/reports/stage5_prep_diagnostics.json) |  |  | 2026-06-17 | 4KB | `50fdcdd1` |
| [ML/reports/stage5_transformer_breach.json](ML/reports/stage5_transformer_breach.json) |  |  | 2026-06-20 | 32KB | `3d15c106` |
| [ML/reports/stage6_2_range_w1_postmortem.json](ML/reports/stage6_2_range_w1_postmortem.json) |  |  | 2026-07-20 | 7KB | `30a164cf` |
| [ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json](ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json) |  |  | 2026-06-17 | 2KB | `a2d1b9ae` |
| [ML/reports/system_correlation_portfolio/xauusd_system_correlation/run_metadata.json](ML/reports/system_correlation_portfolio/xauusd_system_correlation/run_metadata.json) |  |  | 2026-06-17 | 160B | `295db8d3` |
| [ML/reports/system_correlation_portfolio/xauusd_system_correlation/summary.json](ML/reports/system_correlation_portfolio/xauusd_system_correlation/summary.json) |  |  | 2026-06-17 | 8KB | `6f06d60e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq100/summary.json) |  |  | 2026-06-17 | 13KB | `18845574` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq20/summary.json) |  |  | 2026-06-17 | 13KB | `45f40666` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_geometry_path_seq50/summary.json) |  |  | 2026-06-17 | 13KB | `5ace345e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq100/summary.json) |  |  | 2026-06-17 | 13KB | `67c7c6b4` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq20/summary.json) |  |  | 2026-06-17 | 13KB | `9d6d29f3` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_path_seq50/summary.json) |  |  | 2026-06-17 | 13KB | `066a4de4` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq100/summary.json) |  |  | 2026-06-17 | 13KB | `8033d24e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq20/summary.json) |  |  | 2026-06-17 | 13KB | `66813a54` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/benchmark/final_verdict.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/summary.json](ML/reports/take_skip_lib_pic_feature_matrix/baseline_clean_seq50/summary.json) |  |  | 2026-06-17 | 13KB | `9e9f484e` |
| [ML/reports/take_skip_lib_pic_feature_matrix/manifest.json](ML/reports/take_skip_lib_pic_feature_matrix/manifest.json) |  |  | 2026-06-17 | 136KB | `f5ddd710` |
| [ML/reports/take_skip_lib_pic_selection/final_verdict.json](ML/reports/take_skip_lib_pic_selection/final_verdict.json) |  |  | 2026-06-17 | 5KB | `d5323101` |
| [ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/summary.json](ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/summary.json) |  |  | 2026-06-17 | 11KB | `230648aa` |
| [ML/reports/take_skip_live_safe_baseline/manifest.json](ML/reports/take_skip_live_safe_baseline/manifest.json) |  |  | 2026-06-17 | 13KB | `b69fcca8` |
| [ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/summary.json](ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/summary.json) |  |  | 2026-06-17 | 13KB | `a256cdf5` |
| [ML/reports/take_skip_live_safe_geometry/manifest.json](ML/reports/take_skip_live_safe_geometry/manifest.json) |  |  | 2026-06-17 | 15KB | `166e9b6b` |
| [ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-05-07 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/summary.json](ML/reports/take_skip_live_safe_geometry_path/live_safe_geometry_path_seq50/summary.json) |  |  | 2026-05-07 | 21KB | `95ef2fd4` |
| [ML/reports/take_skip_live_safe_geometry_path/manifest.json](ML/reports/take_skip_live_safe_geometry_path/manifest.json) |  |  | 2026-05-07 | 23KB | `d436d29a` |
| [ML/reports/take_skip_live_safe_path/live_safe_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_live_safe_path/live_safe_path_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_live_safe_path/live_safe_path_seq50/summary.json](ML/reports/take_skip_live_safe_path/live_safe_path_seq50/summary.json) |  |  | 2026-06-17 | 12KB | `ca389d9e` |
| [ML/reports/take_skip_live_safe_path/manifest.json](ML/reports/take_skip_live_safe_path/manifest.json) |  |  | 2026-06-17 | 14KB | `3e2117d0` |
| [ML/reports/take_skip_mt4_trailing_sequential/summary.json](ML/reports/take_skip_mt4_trailing_sequential/summary.json) |  |  | 2026-06-17 | 6KB | `80ed09d0` |
| [ML/reports/take_skip_original_contour_feature_matrix/manifest.json](ML/reports/take_skip_original_contour_feature_matrix/manifest.json) |  |  | 2026-06-17 | 141KB | `16fd569e` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 947B | `80f24abc` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq100/summary.json) |  |  | 2026-06-17 | 14KB | `9dc199bf` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 942B | `d3601dcb` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq20/summary.json) |  |  | 2026-06-17 | 14KB | `9d268fe8` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 940B | `d803eebc` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_baseline_seq50/summary.json) |  |  | 2026-06-17 | 14KB | `633b3988` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 995B | `ab51ed64` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq100/summary.json) |  |  | 2026-06-17 | 13KB | `5a9a3e85` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 985B | `4b87cdfa` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq20/summary.json) |  |  | 2026-06-17 | 15KB | `dde6609b` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 990B | `6ed19a6a` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_geometry_path_seq50/summary.json) |  |  | 2026-06-17 | 11KB | `c198bea1` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 995B | `9f7ffd5d` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq100/summary.json) |  |  | 2026-06-17 | 13KB | `d6217569` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 1009B | `7348dd7a` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq20/summary.json) |  |  | 2026-06-17 | 15KB | `b649eff8` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 1002B | `a27dd761` |
| [ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/summary.json) |  |  | 2026-06-17 | 15KB | `cab95008` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/manifest.json](ML/reports/take_skip_original_contour_feature_matrix_control/manifest.json) |  |  | 2026-06-17 | 16KB | `7f73680d` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/final_verdict.json](ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 949B | `3089f610` |
| [ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/summary.json](ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/summary.json) |  |  | 2026-06-17 | 14KB | `d54f4bea` |
| [ML/reports/take_skip_trailing_stop_matrix/manifest.json](ML/reports/take_skip_trailing_stop_matrix/manifest.json) |  |  | 2026-06-17 | 10KB | `a62ab304` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-06-17 | 274B | `057fadd1` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/summary.json) |  |  | 2026-06-17 | 3KB | `cae85b28` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-06-17 | 274B | `352dd6b3` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/summary.json) |  |  | 2026-06-17 | 2KB | `d8a968e2` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-06-17 | 274B | `352dd6b3` |
| [ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/summary.json](ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/summary.json) |  |  | 2026-06-17 | 3KB | `1ccb35bf` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/manifest.json](ML/reports/take_skip_trailing_stop_matrix_smoke/manifest.json) |  |  | 2026-06-17 | 2KB | `06beab4e` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 77B | `187c03e9` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/evaluate_test_take_skip_trailing_stop_v1.md) |  |  | 2026-06-17 | 274B | `9ac140c5` |
| [ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_matrix_smoke/transformer_seq20/summary.json) |  |  | 2026-06-17 | 2KB | `1b967591` |
| [ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json](ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json) |  |  | 2026-06-17 | 3KB | `c5aa0bfc` |
| [ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json) |  |  | 2026-06-17 | 723B | `071ea894` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json](ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json) |  |  | 2026-06-17 | 16KB | `5a4d337a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/benchmark/final_verdict.json) |  |  | 2026-06-17 | 964B | `04c514f5` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-06-17 | 277B | `20c0004a` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json) |  |  | 2026-06-17 | 4KB | `14a5e536` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/benchmark/final_verdict.json) |  |  | 2026-06-17 | 963B | `1aafa9e6` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-06-17 | 277B | `4af22546` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json) |  |  | 2026-06-17 | 4KB | `6bd39710` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/benchmark/final_verdict.json) |  |  | 2026-06-17 | 962B | `f4370930` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/evaluate_test_take_skip_trailing_stop_v2.md) |  |  | 2026-06-17 | 277B | `ab926937` |
| [ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json](ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json) |  |  | 2026-06-17 | 4KB | `416def03` |
| [ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json) |  |  | 2026-06-17 | 1KB | `297c1f74` |
| [ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json](ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json) |  |  | 2026-06-17 | 903B | `3d56d55f` |
| [ML/reports/tb_direction_signal.json](ML/reports/tb_direction_signal.json) |  |  | 2026-06-17 | 16KB | `69d12535` |
| [ML/reports/tb_mt4_verdict/test_summary.json](ML/reports/tb_mt4_verdict/test_summary.json) |  |  | 2026-06-17 | 172B | `6ea3e9d3` |
| [ML/reports/tb_mt4_verdict/validation_summary.json](ML/reports/tb_mt4_verdict/validation_summary.json) |  |  | 2026-06-17 | 167B | `cc2e7d34` |
| [ML/reports/tb_selected_rule.json](ML/reports/tb_selected_rule.json) |  |  | 2026-06-17 | 279B | `3329dfb8` |
| [ML/reports/telemetry_frequency_v1/calibration/selected_rule.json](ML/reports/telemetry_frequency_v1/calibration/selected_rule.json) |  |  | 2026-06-17 | 439B | `50ecae6a` |
| [ML/reports/telemetry_frequency_v1/calibration/summary.json](ML/reports/telemetry_frequency_v1/calibration/summary.json) |  |  | 2026-06-17 | 701B | `4b48b3ec` |
| [ML/reports/telemetry_frequency_v1/calibration/summary.md](ML/reports/telemetry_frequency_v1/calibration/summary.md) |  |  | 2026-06-17 | 442B | `753c04fc` |
| [ML/reports/telemetry_frequency_v1/export_metadata.json](ML/reports/telemetry_frequency_v1/export_metadata.json) |  |  | 2026-06-17 | 732B | `a0ea9250` |
| [ML/reports/telemetry_frequency_v1/export_metadata_highfreq500.json](ML/reports/telemetry_frequency_v1/export_metadata_highfreq500.json) |  |  | 2026-06-17 | 757B | `42ee18bd` |
| [ML/reports/telemetry_frequency_v1/export_parity/summary.json](ML/reports/telemetry_frequency_v1/export_parity/summary.json) |  |  | 2026-06-17 | 1KB | `6e320726` |
| [ML/reports/telemetry_frequency_v1/export_parity/summary.md](ML/reports/telemetry_frequency_v1/export_parity/summary.md) |  |  | 2026-06-17 | 322B | `230e6422` |
| [ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.json) |  |  | 2026-06-17 | 776B | `ec66e9e2` |
| [ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_export_parity/summary.md) |  |  | 2026-06-17 | 335B | `5a667646` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.json) |  |  | 2026-06-17 | 724B | `200359b5` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_tester_export_parity/summary.md) |  |  | 2026-06-17 | 336B | `3647c03e` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.json](ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.json) |  |  | 2026-06-17 | 1KB | `f61e6e6c` |
| [ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.md](ML/reports/telemetry_frequency_v1/highfreq500_tester_log_parity/summary.md) |  |  | 2026-06-17 | 798B | `398dcef2` |
| [ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json](ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json) |  |  | 2026-05-13 | 726B | `0958f17c` |
| [ML/reports/telemetry_frequency_v1/runtime/runtime_state.json](ML/reports/telemetry_frequency_v1/runtime/runtime_state.json) |  |  | 2026-05-13 | 147B | `aedc4ced` |
| [ML/reports/telemetry_frequency_v1/tester_export_metadata_highfreq500.json](ML/reports/telemetry_frequency_v1/tester_export_metadata_highfreq500.json) |  |  | 2026-06-17 | 704B | `8f423454` |
| [ML/reports/telemetry_frequency_v1/tester_export_parity/summary.json](ML/reports/telemetry_frequency_v1/tester_export_parity/summary.json) |  |  | 2026-06-17 | 2KB | `027ea74c` |
| [ML/reports/telemetry_frequency_v1/tester_export_parity/summary.md](ML/reports/telemetry_frequency_v1/tester_export_parity/summary.md) |  |  | 2026-06-17 | 775B | `fb0a81e5` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.json) |  |  | 2026-06-17 | 966B | `192c5dc2` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation/summary.md) |  |  | 2026-06-17 | 235B | `b9da1e09` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.json) |  |  | 2026-06-17 | 969B | `251ec6c8` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_2025/summary.md) |  |  | 2026-06-17 | 238B | `57278fb0` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.json) |  |  | 2026-06-17 | 955B | `de7e96bf` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025/summary.md) |  |  | 2026-06-17 | 252B | `a406faba` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.json](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.json) |  |  | 2026-06-17 | 219B | `1c49a028` |
| [ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.md](ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.md) |  |  | 2026-06-17 | 244B | `56b6829e` |
| [ML/reports/threshold_analysis_12H.md](ML/reports/threshold_analysis_12H.md) |  |  | 2026-06-17 | 2KB | `2eba7e9d` |
| [ML/reports/threshold_analysis_24H.md](ML/reports/threshold_analysis_24H.md) |  |  | 2026-06-17 | 2KB | `b6b5b9d3` |
| [ML/reports/threshold_analysis_48H.md](ML/reports/threshold_analysis_48H.md) |  |  | 2026-06-17 | 2KB | `9f692fd3` |
| [ML/reports/threshold_analysis_tb.md](ML/reports/threshold_analysis_tb.md) |  |  | 2026-06-17 | 975B | `d501c624` |
| [ML/reports/time_only_robustness_audit.json](ML/reports/time_only_robustness_audit.json) |  |  | 2026-07-29 | 7KB | `b82c0866` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `4210c896` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 349B | `36a6a110` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 498B | `47947c94` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `92fbb96a` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq100/summary.json) |  |  | 2026-06-17 | 9KB | `c0697157` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `aae66f9e` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 347B | `c94aaebb` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 476B | `f8499cc8` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `6afa1767` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq20/summary.json) |  |  | 2026-06-17 | 9KB | `cb8bd8b7` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `23ded61c` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 347B | `e511119f` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 493B | `f3e78f8d` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `93b3aaca` |
| [ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json](ML/reports/track_a_max_out_matrix/entry_path_dual_stream_seq50/summary.json) |  |  | 2026-06-17 | 9KB | `9611273d` |
| [ML/reports/track_a_max_out_matrix/manifest.json](ML/reports/track_a_max_out_matrix/manifest.json) |  |  | 2026-06-17 | 63KB | `d565f9d8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `49b4b8cc` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 327B | `0effabc3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq100/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 514B | `88f69647` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq100/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `24810803` |
| [ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq100/summary.json) |  |  | 2026-06-17 | 9KB | `6c2cbc3e` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `200c62ad` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 325B | `5795728a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 492B | `eb63ea67` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `ea93c21a` |
| [ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq20/summary.json) |  |  | 2026-06-17 | 9KB | `1aeaccaa` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `84235cc8` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 325B | `2eee4697` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 490B | `6af015f3` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `249b3cf5` |
| [ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix/transformer_seq50/summary.json) |  |  | 2026-06-17 | 9KB | `39c00532` |
| [ML/reports/track_a_max_out_matrix_deep/manifest.json](ML/reports/track_a_max_out_matrix_deep/manifest.json) |  |  | 2026-06-17 | 25KB | `f1b2534a` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `52d97d3c` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 335B | `035d3a21` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 495B | `f4b312bb` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `d87b2158` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq20/summary.json) |  |  | 2026-06-17 | 11KB | `67c6488f` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/final_verdict.json) |  |  | 2026-06-17 | 1KB | `c8010aa4` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/run_metadata.json) |  |  | 2026-06-17 | 335B | `5ca74235` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/benchmark_v2/selected_candidate.json) |  |  | 2026-06-17 | 487B | `0a640325` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/evaluate_test_entry_path_v1.md) |  |  | 2026-06-17 | 1KB | `a6f68803` |
| [ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json](ML/reports/track_a_max_out_matrix_deep/transformer_seq50/summary.json) |  |  | 2026-06-17 | 11KB | `c4f044c8` |
| [ML/reports/trail_stop_stage4.json](ML/reports/trail_stop_stage4.json) |  |  | 2026-06-17 | 4KB | `ada42d2e` |
| [ML/reports/trailing_stop_target_matrix/manifest.json](ML/reports/trailing_stop_target_matrix/manifest.json) |  |  | 2026-06-17 | 13KB | `eca77374` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-06-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-06-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-06-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq100/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-06-17 | 304B | `087f3217` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq100/summary.json) |  |  | 2026-06-17 | 3KB | `27fe5256` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-06-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-06-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-06-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq20/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-06-17 | 304B | `82e3e008` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq20/summary.json) |  |  | 2026-06-17 | 3KB | `15b1b065` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x2/final_verdict.json) |  |  | 2026-06-17 | 119B | `8dfded7c` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x3/final_verdict.json) |  |  | 2026-06-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/benchmark_trail_48_pnl_atr_x5/final_verdict.json) |  |  | 2026-06-17 | 119B | `35422041` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md](ML/reports/trailing_stop_target_matrix/transformer_seq50/evaluate_test_trailing_stop_target_v1.md) |  |  | 2026-06-17 | 304B | `311c6d96` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary.json) |  |  | 2026-06-17 | 3KB | `e7960f2b` |
| [ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json](ML/reports/trailing_stop_target_matrix/transformer_seq50/summary_seq50_manual.json) |  |  | 2026-06-17 | 1KB | `a654ac5f` |
| [ML/reports/trailing_stop_target_quantile/manifest.json](ML/reports/trailing_stop_target_quantile/manifest.json) |  |  | 2026-06-17 | 3KB | `2e163aa4` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json) |  |  | 2026-06-17 | 119B | `2a316a25` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/evaluate_test_trailing_stop_target_quantile_v1.md) |  |  | 2026-06-17 | 385B | `e972ae90` |
| [ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json](ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json) |  |  | 2026-06-17 | 2KB | `255c26ad` |
| [ML/reports/transformer_direction/feature_statistics.json](ML/reports/transformer_direction/feature_statistics.json) |  |  | 2026-06-17 | 410B | `0443aada` |
| [ML/reports/transformer_direction/target_combos.json](ML/reports/transformer_direction/target_combos.json) |  |  | 2026-06-17 | 424B | `8158d7d5` |
| [ML/reports/transformer_direction/target_statistics.json](ML/reports/transformer_direction/target_statistics.json) |  |  | 2026-06-17 | 7KB | `6120e49f` |
| [ML/reports/transformer_direction/validation_grid_finetune.json](ML/reports/transformer_direction/validation_grid_finetune.json) |  |  | 2026-06-17 | 1KB | `a0bc9c14` |
| [ML/reports/transformer_direction/validation_grid_frozen.json](ML/reports/transformer_direction/validation_grid_frozen.json) |  |  | 2026-06-17 | 4KB | `2151ede9` |
| [ML/reports/walk_forward_diagnostics.json](ML/reports/walk_forward_diagnostics.json) |  |  | 2026-06-20 | 13KB | `c49a13f3` |
| [ML/reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | 🏁 | 2026-06-17 | 7KB | `9301d516` |
| [ML/run_entry_path_live_safe_retrain.py](ML/run_entry_path_live_safe_retrain.py) | Multi-seed live-safe retrain | ✅ | 2026-06-17 | 8KB | `4d781bf1` |
| [ML/run_entry_path_quantile_live_safe_retrain.py](ML/run_entry_path_quantile_live_safe_retrain.py) | Multi-seed quantile retrain | ✅ | 2026-06-17 | 13KB | `6ebfd944` |
| [ML/run_live_safe_ml_audit.py](ML/run_live_safe_ml_audit.py) | CLI для audit inventory, feature trace, legacy replay и verdict | ✅ | 2026-06-17 | 16KB | `e8733513` |
| [ML/run_take_skip_lib_pic_feature_matrix.py](ML/run_take_skip_lib_pic_feature_matrix.py) | Take/skip `lib_PIC` feature matrix | 🚧 | 2026-06-17 | 25KB | `68fde791` |
| [ML/run_take_skip_original_contour_feature_matrix.py](ML/run_take_skip_original_contour_feature_matrix.py) | Original-contour feature matrix | 🚧 | 2026-06-17 | 31KB | `1d7c7b3c` |
| [ML/run_take_skip_trailing_stop_matrix.py](ML/run_take_skip_trailing_stop_matrix.py) | Matrix runner для take/skip trailing stop | ✅ | 2026-06-17 | 7KB | `77b1587b` |
| [ML/run_take_skip_trailing_stop_v2_matrix.py](ML/run_take_skip_trailing_stop_v2_matrix.py) | Matrix runner для take/skip v2 | ✅ | 2026-06-17 | 6KB | `2be9df55` |
| [ML/run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | ✅ | 2026-06-17 | 6KB | `0d1d781d` |
| [ML/run_trailing_stop_target_matrix.py](ML/run_trailing_stop_target_matrix.py) | Оркестратор bounded matrix для `trailing_stop_target_v1` | ✅ | 2026-06-17 | 9KB | `8c2ac272` |
| [ML/run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | ✅ | 2026-06-17 | 6KB | `ac5afba9` |
| [ML/stage09_stability_refreeze.py](ML/stage09_stability_refreeze.py) | Stage 09 stability refreeze | ✅ | 2026-06-17 | 14KB | `813e9f29` |
| [ML/stage10_frozen_test_oos.py](ML/stage10_frozen_test_oos.py) | Stage 10 frozen OOS test | ✅ | 2026-06-17 | 11KB | `e3f8847f` |
| [ML/take_skip_trailing_stop_task.py](ML/take_skip_trailing_stop_task.py) | Task helpers для take/skip trailing stop | ✅ | 2026-06-17 | 4KB | `8e0a93f6` |
| [ML/take_skip_trailing_stop_v2_task.py](ML/take_skip_trailing_stop_v2_task.py) | Task helpers для take/skip v2 | ✅ | 2026-06-17 | 4KB | `227844ec` |
| [ML/tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | 🏁 | 2026-06-17 | 2KB | `502427cf` |
| [ML/tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | ✅ | 2026-06-17 | 4KB | `f07ea73a` |
| [ML/telemetry_daily_reconciliation.py](ML/telemetry_daily_reconciliation.py) | Daily telemetry reconciliation | ✅ | 2026-06-17 | 14KB | `3d1ff671` |
| [ML/threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | ✅ | 2026-06-17 | 47KB | `cb5483fc` |
| [ML/trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | ✅ | 2026-06-17 | 4KB | `9e87baba` |
| [ML/trailing_stop_target_task.py](ML/trailing_stop_target_task.py) | Trailing-stop target task: target contract, export helpers и metrics | ✅ | 2026-06-17 | 1KB | `05a05382` |
| [ML/train.py](ML/train.py) | Обучение ML-моделей; `--output-dir` изолирует checkpoint/result для seed/device аудита | ✅ | 2026-06-17 | 117KB | `09dec601` |
| [ML/transformer_direction_train.py](ML/transformer_direction_train.py) |  |  | 2026-06-17 | 32KB | `6833bf35` |
| [ML/triple_barrier_mt4_execution.py](ML/triple_barrier_mt4_execution.py) |  |  | 2026-06-17 | 6KB | `e2520e9d` |
| [ML/utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ | 2026-06-17 | 12KB | `1984242a` |
| [ML/validation_freeze.py](ML/validation_freeze.py) | Stage 09 — deterministic Transformer training + checkpoint + round-trip verification (does NOT generate frozen rule) | ✅ | 2026-06-17 | 12KB | `dff1e63f` |

## Processing

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [processing/README.md](processing/README.md) |  |  | 2026-06-17 | 2KB | `1bc42412` |
| [processing/denormalize_updn.py](processing/denormalize_updn.py) | Восстановление Up/Dn из нормализованных величин | ✅ | 2026-06-17 | 7KB | `256f1fd6` |
| [processing/fractal_preprocessing.py](processing/fractal_preprocessing.py) | Общая сортировка фракталов внутри строки для training/online | ✅ | 2026-06-17 | 3KB | `37670f70` |
| [processing/label_audit.py](processing/label_audit.py) | Аудит разметки и контрактов labels | ✅ | 2026-06-17 | 4KB | `29974629` |
| [processing/label_main.py](processing/label_main.py) | CLI оркестратор pipeline | 🏁 | 2026-06-29 | 16KB | `ecd899bb` |
| [processing/label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | 🏁 | 2026-07-20 | 69KB | `0145d44a` |
| [processing/normalize.py](processing/normalize.py) | Построчная нормализация признаков | 🏁 | 2026-06-17 | 28KB | `109b2cc6` |
| [processing/online_causal_preprocessing.py](processing/online_causal_preprocessing.py) | Online-safe preprocessing | ✅ | 2026-06-17 | 4KB | `c194aa91` |
| [processing/purge_split.py](processing/purge_split.py) | Purge/embargo границ train/val/test | ✅ | 2026-06-17 | 2KB | `9b5e1faf` |
| [processing/rebuild_xauusd_top_level_updn.py](processing/rebuild_xauusd_top_level_updn.py) | Пересборка top-level Up/Dn для XAUUSD | ✅ | 2026-07-20 | 5KB | `ee31485e` |

## API

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [API/README.md](API/README.md) |  |  | 2026-06-17 | 7KB | `fce994e8` |
| [API/api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, общий live-safe preprocessing, ML-сигнал |  | 2026-06-17 | 6KB | `5174dd3b` |
| [API/exit_policy_research.py](API/exit_policy_research.py) | Offline research: сравнение ML-политик выхода и position management | 🏁 | 2026-06-17 | 14KB | `0caf0735` |
| [API/export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) | Экспорт frozen quantile signals | ✅ | 2026-06-17 | 8KB | `a5a84e1a` |
| [API/export_entry_path_v1_signals.py](API/export_entry_path_v1_signals.py) | Экспорт frozen `entry_path_v1` signals | ✅ | 2026-06-17 | 14KB | `7b69d64a` |
| [API/export_take_skip_trailing_stop_v2_signals.py](API/export_take_skip_trailing_stop_v2_signals.py) | Экспорт take/skip v2 signals | ✅ | 2026-06-17 | 15KB | `e2430007` |
| [API/generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | ✅ | 2026-06-17 | 34KB | `d721c7a3` |
| [API/signal_path_atlas.py](API/signal_path_atlas.py) | Research CLI: ATR-normalized Signal Path Atlas, path archetypes, holdout validation | 🏁 | 2026-06-17 | 37KB | `9fd6cd00` |
| [API/signal_quality_research.py](API/signal_quality_research.py) | Signal Quality Filter Research (Variant 4): multi-horizon prediction features как фильтры | 🏁 | 2026-06-17 | 29KB | `31830287` |
| [API/signal_research.py](API/signal_research.py) | Research CLI: качество ML-сигналов по реальным OHLC (Variant 2/3) | 🏁 | 2026-06-17 | 72KB | `da83229a` |
| [API/telemetry_signal_watcher.py](API/telemetry_signal_watcher.py) | Online watcher telemetry-контура | ✅ | 2026-06-17 | 25KB | `4acdc2d4` |
| [API/test_api_client.py](API/test_api_client.py) | Интеграционный тест REST API-сервера (MT4) | 🏁 | 2026-06-17 | 1KB | `bf393de3` |

## Statistics

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [statistics/EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | 🏁 | 2026-06-17 | 188KB | `4c750fc3` |
| [statistics/README.md](statistics/README.md) |  |  | 2026-06-17 | 2KB | `8a02dc7e` |
| [statistics/analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | 🏁 | 2026-06-17 | 8KB | `f3ed1639` |
| [statistics/class_statistics.json](statistics/class_statistics.json) |  |  | 2026-06-17 | 6KB | `c107590a` |
| [statistics/data_contract_smoke_check.py](statistics/data_contract_smoke_check.py) | Быстрая проверка контрактов данных | ✅ | 2026-07-02 | 7KB | `10449680` |
| [statistics/feature_catalog.json](statistics/feature_catalog.json) |  |  | 2026-06-17 | 70KB | `bb41c2d1` |
| [statistics/nero_features_metadata.json](statistics/nero_features_metadata.json) |  |  | 2026-06-17 | 6KB | `fc79c23a` |
| [statistics/reports/EDA_executed.ipynb](statistics/reports/EDA_executed.ipynb) |  |  | 2026-04-16 | 3MB | `--------` |
| [statistics/reports/EDA_report.md](statistics/reports/EDA_report.md) |  |  | 2026-06-17 | 59KB | `01e9ac82` |
| [statistics/signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | ✅ | 2026-06-17 | 49KB | `0088ddc3` |
| [statistics/statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | 🏁 | 2026-06-17 | 21KB | `c725dd71` |
| [statistics/statistics_summary.json](statistics/statistics_summary.json) |  |  | 2026-06-17 | 5KB | `1e7882c0` |

## Tests

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [tests/README.md](tests/README.md) |  |  | 2026-06-17 | 2KB | `81083268` |
| [tests/processing/test_fractal_stop_breach_labels.py](tests/processing/test_fractal_stop_breach_labels.py) | `processing/label_signals.py` — Stage 1 breach-разметка `fractal0` | ✅ | 2026-06-29 | 12KB | `8041410c` |
| [tests/processing/test_fractal_stop_fav.py](tests/processing/test_fractal_stop_fav.py) | `processing/label_signals.py` — Stage 2 fav-разметка и симулятор Fractal Stop Fav | ✅ | 2026-06-17 | 6KB | `a8e96dc0` |
| [tests/processing/test_limit_order_barriers.py](tests/processing/test_limit_order_barriers.py) |  |  | 2026-06-17 | 15KB | `da00aed8` |
| [tests/test_api_server_preprocessing.py](tests/test_api_server_preprocessing.py) | `API/api_server.py` shared online preprocessing contract | ✅ | 2026-06-17 | 1KB | `11e15c32` |
| [tests/test_benchmark_cross_instrument_robustness.py](tests/test_benchmark_cross_instrument_robustness.py) | `ML/benchmark_cross_instrument_robustness.py` | ✅ | 2026-06-17 | 9KB | `745821a7` |
| [tests/test_benchmark_entry_path_all_rows_ranking.py](tests/test_benchmark_entry_path_all_rows_ranking.py) | `ML/benchmark_entry_path_all_rows_ranking.py` | ✅ | 2026-06-17 | 3KB | `0e7bc727` |
| [tests/test_benchmark_entry_path_binary_direction.py](tests/test_benchmark_entry_path_binary_direction.py) |  |  | 2026-06-17 | 2KB | `4236bb92` |
| [tests/test_benchmark_entry_path_causal_surrogate.py](tests/test_benchmark_entry_path_causal_surrogate.py) | `ML/benchmark_entry_path_causal_surrogate.py` | ✅ | 2026-06-17 | 3KB | `3d39bd74` |
| [tests/test_benchmark_entry_path_direct_bar_model.py](tests/test_benchmark_entry_path_direct_bar_model.py) | `ML/benchmark_entry_path_direct_bar_model.py` | ✅ | 2026-06-17 | 3KB | `ac56085f` |
| [tests/test_benchmark_entry_path_fractal_level_direct_direction.py](tests/test_benchmark_entry_path_fractal_level_direct_direction.py) |  |  | 2026-06-17 | 1KB | `4d81e1e6` |
| [tests/test_benchmark_entry_path_signal_only_ablation.py](tests/test_benchmark_entry_path_signal_only_ablation.py) | `ML/benchmark_entry_path_signal_only_ablation.py` | ✅ | 2026-06-17 | 3KB | `142ff299` |
| [tests/test_benchmark_entry_path_v1_frequency.py](tests/test_benchmark_entry_path_v1_frequency.py) | `ML/benchmark_entry_path_v1_frequency.py` | ✅ | 2026-06-17 | 739B | `40f6843e` |
| [tests/test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | ✅ | 2026-06-17 | 2KB | `78d542d3` |
| [tests/test_benchmark_execution_policy_v2.py](tests/test_benchmark_execution_policy_v2.py) | `ML/benchmark_execution_policy_v2.py` | ✅ | 2026-06-17 | 3KB | `45faf793` |
| [tests/test_benchmark_fav_3_vs_12_standalone.py](tests/test_benchmark_fav_3_vs_12_standalone.py) |  |  | 2026-06-17 | 11KB | `dcdcc7a1` |
| [tests/test_benchmark_outcome_targets.py](tests/test_benchmark_outcome_targets.py) | `ML/benchmark_outcome_targets.py` | ✅ | 2026-06-17 | 4KB | `e9159813` |
| [tests/test_benchmark_quantile_early_timeout.py](tests/test_benchmark_quantile_early_timeout.py) |  |  | 2026-06-17 | 1KB | `b4775c4c` |
| [tests/test_benchmark_quantile_fav_composition.py](tests/test_benchmark_quantile_fav_composition.py) |  |  | 2026-06-17 | 6KB | `e7f68596` |
| [tests/test_benchmark_quantile_forward_validation.py](tests/test_benchmark_quantile_forward_validation.py) |  |  | 2026-06-17 | 6KB | `3dc6e7a3` |
| [tests/test_benchmark_quantile_relaxed_composition.py](tests/test_benchmark_quantile_relaxed_composition.py) |  |  | 2026-06-17 | 5KB | `c7115be5` |
| [tests/test_benchmark_system_correlation.py](tests/test_benchmark_system_correlation.py) | `ML/benchmark_system_correlation.py` | ✅ | 2026-06-17 | 10KB | `d018d30a` |
| [tests/test_benchmark_take_skip_lib_pic_selection.py](tests/test_benchmark_take_skip_lib_pic_selection.py) | `ML/benchmark_take_skip_lib_pic_selection.py` | ✅ | 2026-06-17 | 5KB | `64aaec89` |
| [tests/test_benchmark_take_skip_trailing_stop.py](tests/test_benchmark_take_skip_trailing_stop.py) |  |  | 2026-06-17 | 4KB | `be0b1bdb` |
| [tests/test_benchmark_take_skip_trailing_stop_v2.py](tests/test_benchmark_take_skip_trailing_stop_v2.py) |  |  | 2026-06-17 | 4KB | `d9fdae18` |
| [tests/test_benchmark_take_skip_trailing_stop_v2_followup.py](tests/test_benchmark_take_skip_trailing_stop_v2_followup.py) |  |  | 2026-06-17 | 8KB | `0195683d` |
| [tests/test_benchmark_telemetry_frequency_calibration.py](tests/test_benchmark_telemetry_frequency_calibration.py) | `ML/benchmark_telemetry_frequency_calibration.py` | ✅ | 2026-06-17 | 3KB | `6e1f8e04` |
| [tests/test_benchmark_trailing_stop_target.py](tests/test_benchmark_trailing_stop_target.py) | `ML/benchmark_trailing_stop_target.py` | ✅ | 2026-06-17 | 2KB | `fb9d2a36` |
| [tests/test_benchmark_trailing_stop_target_quantile.py](tests/test_benchmark_trailing_stop_target_quantile.py) | `ML/benchmark_trailing_stop_target_quantile.py` | ✅ | 2026-06-17 | 8KB | `05ca8680` |
| [tests/test_diagnose_stage4_3.py](tests/test_diagnose_stage4_3.py) |  |  | 2026-06-17 | 7KB | `744416e4` |
| [tests/test_diagnose_stage4_4.py](tests/test_diagnose_stage4_4.py) |  |  | 2026-06-17 | 5KB | `92b2ee48` |
| [tests/test_diagnose_stage5_prep.py](tests/test_diagnose_stage5_prep.py) |  |  | 2026-06-17 | 3KB | `bdbbbf12` |
| [tests/test_direction_inside_frozen_movement_regime.py](tests/test_direction_inside_frozen_movement_regime.py) | `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py` | ✅ | 2026-07-20 | 22KB | `0e4763c3` |
| [tests/test_direction_inside_frozen_movement_regime_rich_features.py](tests/test_direction_inside_frozen_movement_regime_rich_features.py) | `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py` | ✅ | 2026-07-20 | 31KB | `a4f9cfcb` |
| [tests/test_entry_based_amplitude_movement.py](tests/test_entry_based_amplitude_movement.py) | entry-based amplitude movement-regime audit | ✅ | 2026-07-20 | 34KB | `4789fd32` |
| [tests/test_entry_based_movement_filter.py](tests/test_entry_based_movement_filter.py) | `ML/baseline/benchmark_entry_based_movement_filter.py` | ⚠️ | 2026-07-20 | 16KB | `c32b142a` |
| [tests/test_entry_based_movement_filter_freeze.py](tests/test_entry_based_movement_filter_freeze.py) | `ML/baseline/benchmark_entry_based_movement_filter_freeze.py` | ✅ | 2026-07-20 | 16KB | `84faba19` |
| [tests/test_entry_based_next_open_closeout.py](tests/test_entry_based_next_open_closeout.py) | entry-based closeout runner | ✅ | 2026-07-20 | 14KB | `d407400f` |
| [tests/test_entry_based_powerful_tabular.py](tests/test_entry_based_powerful_tabular.py) | entry-based powerful tabular runner | ✅ | 2026-07-20 | 18KB | `ea7f4653` |
| [tests/test_entry_based_sequence_transformer.py](tests/test_entry_based_sequence_transformer.py) | entry-based sequence Transformer runner | ✅ | 2026-07-20 | 12KB | `11a3aecc` |
| [tests/test_entry_based_updn_fractal_selection_ablation.py](tests/test_entry_based_updn_fractal_selection_ablation.py) | entry-based fractal ablation runner | ✅ | 2026-07-20 | 16KB | `68712af1` |
| [tests/test_entry_based_updn_price_feature_matrix.py](tests/test_entry_based_updn_price_feature_matrix.py) | `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py` | ✅ | 2026-07-20 | 14KB | `9f72d46c` |
| [tests/test_entry_path_direct_direction_targets.py](tests/test_entry_path_direct_direction_targets.py) |  |  | 2026-06-17 | 3KB | `f28963bf` |
| [tests/test_entry_path_dual_stream_transformer.py](tests/test_entry_path_dual_stream_transformer.py) | `ML/models/entry_path_dual_stream_transformer.py` | ✅ | 2026-06-17 | 1KB | `e9c80f90` |
| [tests/test_entry_path_feature_bank.py](tests/test_entry_path_feature_bank.py) | `ML/entry_path_feature_bank.py` | ✅ | 2026-06-17 | 3KB | `8ee46497` |
| [tests/test_entry_path_labels.py](tests/test_entry_path_labels.py) | `processing/label_signals.py` — entry_path_v1 helpers | ✅ | 2026-06-17 | 7KB | `fd49cce2` |
| [tests/test_entry_path_level_targets.py](tests/test_entry_path_level_targets.py) |  |  | 2026-06-17 | 1KB | `eb92fa8f` |
| [tests/test_entry_path_loader_seq_len.py](tests/test_entry_path_loader_seq_len.py) | `ML/data_loader.py` — `entry_path_v1` sequence length contract | ✅ | 2026-06-17 | 4KB | `e5f1a2ce` |
| [tests/test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | ✅ | 2026-06-17 | 3KB | `2975dc23` |
| [tests/test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | ✅ | 2026-06-17 | 7KB | `8c945ae2` |
| [tests/test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | ✅ | 2026-06-17 | 8KB | `c10decb9` |
| [tests/test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | ✅ | 2026-06-17 | 12KB | `8390258c` |
| [tests/test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | ✅ | 2026-06-17 | 8KB | `58560b69` |
| [tests/test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | ✅ | 2026-06-17 | 4KB | `142bfe32` |
| [tests/test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | ✅ | 2026-06-17 | 1KB | `b9a1044c` |
| [tests/test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | ✅ | 2026-06-17 | 12KB | `229fb086` |
| [tests/test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | ✅ | 2026-06-17 | 2KB | `294562f5` |
| [tests/test_entry_path_v1_quantile_training.py](tests/test_entry_path_v1_quantile_training.py) |  |  | 2026-06-17 | 9KB | `bde15a71` |
| [tests/test_exit_policy_research.py](tests/test_exit_policy_research.py) | `API/exit_policy_research.py` | ✅ | 2026-06-17 | 4KB | `4c75d18c` |
| [tests/test_export_entry_path_predictions.py](tests/test_export_entry_path_predictions.py) | `ML/export_entry_path_predictions.py` | ✅ | 2026-06-17 | 6KB | `ada7fea6` |
| [tests/test_export_entry_path_v1_quantile_rule.py](tests/test_export_entry_path_v1_quantile_rule.py) |  |  | 2026-06-17 | 3KB | `e06bdfbb` |
| [tests/test_export_entry_path_v1_quantile_signals.py](tests/test_export_entry_path_v1_quantile_signals.py) |  |  | 2026-06-17 | 7KB | `237d172f` |
| [tests/test_export_entry_path_v1_signals.py](tests/test_export_entry_path_v1_signals.py) | `API/export_entry_path_v1_signals.py` | ✅ | 2026-06-17 | 9KB | `05e49b1a` |
| [tests/test_export_take_skip_trailing_stop_v2_signals.py](tests/test_export_take_skip_trailing_stop_v2_signals.py) |  |  | 2026-06-17 | 12KB | `66fd1496` |
| [tests/test_export_take_skip_v2_predictions.py](tests/test_export_take_skip_v2_predictions.py) |  |  | 2026-06-17 | 7KB | `35d5c947` |
| [tests/test_feature_bank_comparison_diagnostics.py](tests/test_feature_bank_comparison_diagnostics.py) | `ML/feature_bank_comparison_diagnostics.py` | ✅ | 2026-06-17 | 3KB | `83c6338e` |
| [tests/test_feature_importance_diagnostics.py](tests/test_feature_importance_diagnostics.py) | `ML/feature_importance_diagnostics.py` | ✅ | 2026-06-17 | 2KB | `666e9ecb` |
| [tests/test_feature_screen_entry_path.py](tests/test_feature_screen_entry_path.py) | `ML/feature_screen_entry_path.py` | ✅ | 2026-06-17 | 567B | `b99a62db` |
| [tests/test_fractal0_entry_exit_grid.py](tests/test_fractal0_entry_exit_grid.py) | `ML/baseline/benchmark_fractal0_entry_exit_grid.py` | ✅ | 2026-07-29 | 34KB | `fa619ff9` |
| [tests/test_fractal0_entry_quality_filter.py](tests/test_fractal0_entry_quality_filter.py) |  |  | 2026-07-29 | 38KB | `2d763bb8` |
| [tests/test_fractal0_fixed11_candidate_audit.py](tests/test_fractal0_fixed11_candidate_audit.py) |  |  | 2026-07-29 | 17KB | `8e2c75a0` |
| [tests/test_fractal0_fixed11_internal_closure_rerun.py](tests/test_fractal0_fixed11_internal_closure_rerun.py) |  |  | 2026-07-29 | 31KB | `861e59e9` |
| [tests/test_fractal0_fixed11_mutual_correlation_pruning.py](tests/test_fractal0_fixed11_mutual_correlation_pruning.py) | `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py` | ✅ | 2026-07-29 | 17KB | `152eeaa1` |
| [tests/test_fractal0_fixed11_rich_entry_locked_test.py](tests/test_fractal0_fixed11_rich_entry_locked_test.py) |  |  | 2026-07-29 | 1012B | `c0e00480` |
| [tests/test_fractal0_price_entry_mechanics.py](tests/test_fractal0_price_entry_mechanics.py) | `ML/baseline/benchmark_fractal0_price_entry_mechanics.py` | ✅ | 2026-07-20 | 10KB | `c364834b` |
| [tests/test_fractal_level_feature_builder.py](tests/test_fractal_level_feature_builder.py) |  |  | 2026-06-17 | 8KB | `dae37ed1` |
| [tests/test_generate_signals_research.py](tests/test_generate_signals_research.py) | TB signal selection в `API/generate_signals.py` | ✅ | 2026-06-17 | 831B | `6bed18cd` |
| [tests/test_inverse_piecewise.py](tests/test_inverse_piecewise.py) | `processing/normalize.py` + `statistics/signal_tracer.py` — round-trip piecewise | ✅ | 2026-06-17 | 9KB | `3cc10cfe` |
| [tests/test_label_updn.py](tests/test_label_updn.py) | `processing/label_signals.py` — parse_fractal, label_updn | ✅ | 2026-07-20 | 6KB | `9c704c7e` |
| [tests/test_leaderboard_closure_audit.py](tests/test_leaderboard_closure_audit.py) |  |  | 2026-07-29 | 9KB | `bfb04c6a` |
| [tests/test_leaderboard_robustness_audit.py](tests/test_leaderboard_robustness_audit.py) |  |  | 2026-07-29 | 14KB | `eb3c6516` |
| [tests/test_lib_pic_feature_profiles.py](tests/test_lib_pic_feature_profiles.py) | `ML/lib_pic_feature_profiles.py` | ✅ | 2026-06-17 | 3KB | `025247c8` |
| [tests/test_lib_pic_geometry_feature_bank.py](tests/test_lib_pic_geometry_feature_bank.py) | `ML/lib_pic_geometry_feature_bank.py` | ✅ | 2026-06-17 | 2KB | `5d44f49d` |
| [tests/test_lib_pic_path_reaction_feature_bank.py](tests/test_lib_pic_path_reaction_feature_bank.py) | `ML/lib_pic_path_reaction_feature_bank.py` | ✅ | 2026-06-17 | 3KB | `14cd19b8` |
| [tests/test_live_safe_audit.py](tests/test_live_safe_audit.py) | `ML/live_safe_audit.py`, `ML/live_safe_audit_registry.py`, `ML/run_live_safe_ml_audit.py` | ✅ | 2026-06-17 | 5KB | `3d37ad7d` |
| [tests/test_ml_fractal_parser_contract.py](tests/test_ml_fractal_parser_contract.py) | `ML/` — запрет использовать parser разметки как ML feature extractor | ✅ | 2026-06-17 | 3KB | `281dac57` |
| [tests/test_mql_telemetry_params_csv_contract.py](tests/test_mql_telemetry_params_csv_contract.py) | MQL telemetry `#.csv` / `EXTERN_VARS()` runtime contract | ✅ | 2026-07-29 | 19KB | `b95df2f2` |
| [tests/test_mt5_execution_diagnostics.py](tests/test_mt5_execution_diagnostics.py) |  |  | 2026-08-01 | 13KB | `0a33677e` |
| [tests/test_mt5_nero_parity.py](tests/test_mt5_nero_parity.py) |  |  | 2026-07-31 | 6KB | `563137e4` |
| [tests/test_mt5_signal_executor_schema.py](tests/test_mt5_signal_executor_schema.py) |  |  | 2026-07-31 | 11KB | `90cf3bf7` |
| [tests/test_multi_scale_fractal_features.py](tests/test_multi_scale_fractal_features.py) |  |  | 2026-06-17 | 1KB | `de0eeac6` |
| [tests/test_next_open_entry_updn_foundation.py](tests/test_next_open_entry_updn_foundation.py) | `ML/baseline/benchmark_next_open_entry_updn_foundation.py` | ✅ | 2026-07-20 | 3KB | `b453393c` |
| [tests/test_online_causal_preprocessing.py](tests/test_online_causal_preprocessing.py) | `processing/online_causal_preprocessing.py` | ✅ | 2026-06-17 | 1KB | `7d04f504` |
| [tests/test_online_tester_reconciliation.py](tests/test_online_tester_reconciliation.py) |  |  | 2026-06-17 | 7KB | `e461ccdf` |
| [tests/test_outcome_tasks.py](tests/test_outcome_tasks.py) | outcome tasks в `ML/data_loader.py` | ✅ | 2026-06-17 | 1KB | `8be56a6e` |
| [tests/test_parse_mt5_execution_report.py](tests/test_parse_mt5_execution_report.py) |  |  | 2026-07-31 | 6KB | `9fbf79bb` |
| [tests/test_prepare_entry_path_mt4_parity.py](tests/test_prepare_entry_path_mt4_parity.py) | `ML/prepare_entry_path_mt4_parity.py` | ✅ | 2026-06-17 | 1KB | `43e1848e` |
| [tests/test_rebuild_xauusd_top_level_updn.py](tests/test_rebuild_xauusd_top_level_updn.py) |  |  | 2026-07-20 | 3KB | `5554cbb1` |
| [tests/test_regression_updn_already_moved_audit.py](tests/test_regression_updn_already_moved_audit.py) | `ML/baseline/analyze_regression_updn_already_moved_audit.py` | ✅ | 2026-07-20 | 7KB | `a41a8003` |
| [tests/test_regression_updn_target_foundation.py](tests/test_regression_updn_target_foundation.py) | `ML/baseline/benchmark_regression_updn_target_foundation.py` | ✅ | 2026-07-20 | 10KB | `ae507443` |
| [tests/test_run_entry_path_live_safe_retrain.py](tests/test_run_entry_path_live_safe_retrain.py) |  |  | 2026-06-17 | 3KB | `0ed8f0c4` |
| [tests/test_run_entry_path_quantile_live_safe_retrain.py](tests/test_run_entry_path_quantile_live_safe_retrain.py) |  |  | 2026-06-17 | 6KB | `5f3b4b02` |
| [tests/test_run_take_skip_trailing_stop_matrix.py](tests/test_run_take_skip_trailing_stop_matrix.py) |  |  | 2026-06-17 | 3KB | `7c59dae6` |
| [tests/test_run_take_skip_trailing_stop_v2_matrix.py](tests/test_run_take_skip_trailing_stop_v2_matrix.py) |  |  | 2026-06-17 | 4KB | `b715d6b8` |
| [tests/test_run_trailing_stop_target_matrix.py](tests/test_run_trailing_stop_target_matrix.py) | `ML/run_trailing_stop_target_matrix.py` | ✅ | 2026-06-17 | 8KB | `325298f6` |
| [tests/test_run_trailing_stop_target_quantile.py](tests/test_run_trailing_stop_target_quantile.py) | `ML/run_trailing_stop_target_quantile.py` | ✅ | 2026-06-17 | 4KB | `9f4fc6e6` |
| [tests/test_signal_export_parity.py](tests/test_signal_export_parity.py) | `ML/benchmark_signal_export_parity.py` | ✅ | 2026-06-17 | 3KB | `5ff4a4e3` |
| [tests/test_signal_path_atlas.py](tests/test_signal_path_atlas.py) | `API/signal_path_atlas.py` — calendar split, path tensor, archetypes, CLI | ✅ | 2026-06-17 | 38KB | `a3364aec` |
| [tests/test_signal_quality_research.py](tests/test_signal_quality_research.py) | `API/signal_quality_research.py` — filter features, variance check, tree, holdout | ✅ | 2026-06-17 | 12KB | `51ebae32` |
| [tests/test_signal_research.py](tests/test_signal_research.py) | `API/signal_research.py` — ATR14, excursions, barriers, split | ✅ | 2026-06-17 | 41KB | `4b5920a6` |
| [tests/test_signal_tracer_tb.py](tests/test_signal_tracer_tb.py) | TB-specific parsing в `statistics/signal_tracer.py` | ✅ | 2026-06-17 | 2KB | `b2c52f5f` |
| [tests/test_stage4_5_exit_mechanics.py](tests/test_stage4_5_exit_mechanics.py) |  |  | 2026-06-17 | 5KB | `6e91f20c` |
| [tests/test_stage4_6_clean_cycle.py](tests/test_stage4_6_clean_cycle.py) |  |  | 2026-06-17 | 3KB | `5f2c5556` |
| [tests/test_stage5_transformer_breach.py](tests/test_stage5_transformer_breach.py) | Stage 5.0 Transformer Breach: профили признаков, tensor shapes, corridor validation, модель, split guard | ✅ | 2026-06-29 | 195KB | `90ebfbb7` |
| [tests/test_stage6_1_relative_geometry.py](tests/test_stage6_1_relative_geometry.py) | `ML/baseline/benchmark_stage6_1_relative_geometry.py` | ✅ | 2026-07-20 | 18KB | `7c87a914` |
| [tests/test_stage6_2_price_action.py](tests/test_stage6_2_price_action.py) | `ML/baseline/benchmark_stage6_2_price_action.py` | ✅ | 2026-07-20 | 13KB | `e5bf3730` |
| [tests/test_stage6_2_range_w1_postmortem.py](tests/test_stage6_2_range_w1_postmortem.py) | `ML/baseline/analyze_stage6_2_range_w1_postmortem.py` | ✅ | 2026-07-20 | 6KB | `2fc4c754` |
| [tests/test_stage6_3_h6_feature_parity.py](tests/test_stage6_3_h6_feature_parity.py) | `ML/baseline/benchmark_stage6_3_h6_feature_parity.py` | ✅ | 2026-07-20 | 16KB | `e099f106` |
| [tests/test_stage6_outcome_based.py](tests/test_stage6_outcome_based.py) | `ML/baseline/benchmark_stage6_outcome_based.py` | ✅ | 2026-07-20 | 10KB | `fe6c4420` |
| [tests/test_take_skip_lib_pic_feature_matrix.py](tests/test_take_skip_lib_pic_feature_matrix.py) | `ML/run_take_skip_lib_pic_feature_matrix.py` и `ML/models/take_skip_dual_stream_transformer.py` | ✅ | 2026-06-17 | 6KB | `df9c696d` |
| [tests/test_take_skip_original_contour_feature_matrix.py](tests/test_take_skip_original_contour_feature_matrix.py) | `ML/run_take_skip_original_contour_feature_matrix.py` | ✅ | 2026-06-17 | 9KB | `88acdeac` |
| [tests/test_take_skip_trailing_stop_task.py](tests/test_take_skip_trailing_stop_task.py) |  |  | 2026-06-17 | 7KB | `f917ec48` |
| [tests/test_take_skip_trailing_stop_v2_task.py](tests/test_take_skip_trailing_stop_v2_task.py) |  |  | 2026-06-17 | 8KB | `5d31b732` |
| [tests/test_tb_label_invariants.py](tests/test_tb_label_invariants.py) |  |  | 2026-06-17 | 1KB | `46510bd4` |
| [tests/test_telemetry_daily_reconciliation.py](tests/test_telemetry_daily_reconciliation.py) | `ML/telemetry_daily_reconciliation.py` | ✅ | 2026-06-17 | 8KB | `7fd9bb8d` |
| [tests/test_telemetry_signal_watcher.py](tests/test_telemetry_signal_watcher.py) | `API/telemetry_signal_watcher.py` | ✅ | 2026-06-17 | 24KB | `759d5060` |
| [tests/test_time_only_robustness_audit.py](tests/test_time_only_robustness_audit.py) |  |  | 2026-07-29 | 9KB | `790cf8bc` |
| [tests/test_track_a_max_out_matrix.py](tests/test_track_a_max_out_matrix.py) | `ML/run_track_a_max_out_matrix.py` | ✅ | 2026-06-17 | 706B | `da3502cc` |
| [tests/test_trade_target_labels.py](tests/test_trade_target_labels.py) | `processing/label_signals.py` — trade target labels | ✅ | 2026-06-17 | 2KB | `01005f96` |
| [tests/test_trailing_stop_target_labels.py](tests/test_trailing_stop_target_labels.py) | `processing/label_signals.py` — trailing-stop target labels | ✅ | 2026-06-17 | 5KB | `102ae22d` |
| [tests/test_trailing_stop_target_quantile_model.py](tests/test_trailing_stop_target_quantile_model.py) | `ML/models/trailing_stop_target_quantile_transformer.py` | ✅ | 2026-06-17 | 542B | `692f8730` |
| [tests/test_trailing_stop_target_quantile_task.py](tests/test_trailing_stop_target_quantile_task.py) | `ML/trailing_stop_target_quantile_task.py` и train/evaluate/export wiring | ✅ | 2026-06-17 | 17KB | `329c7acb` |
| [tests/test_trailing_stop_target_task.py](tests/test_trailing_stop_target_task.py) | `ML/trailing_stop_target_task.py` и trailing-stop export/evaluate wiring | ✅ | 2026-06-17 | 14KB | `ea6330c4` |
| [tests/test_triple_barrier_calibration.py](tests/test_triple_barrier_calibration.py) | EV/calibration helper для Triple Barrier | ✅ | 2026-06-17 | 745B | `b5e20abc` |
| [tests/test_triple_barrier_first_touch.py](tests/test_triple_barrier_first_touch.py) | first-touch helper для Triple Barrier разметки | ✅ | 2026-06-17 | 1KB | `58f2ba93` |
| [tests/test_triple_barrier_mt4_execution.py](tests/test_triple_barrier_mt4_execution.py) |  |  | 2026-06-17 | 4KB | `a5e04561` |
| [tests/test_triple_barrier_training.py](tests/test_triple_barrier_training.py) | transfer-learning kwargs для TB обучения | ✅ | 2026-06-17 | 1KB | `d46e3e22` |

## MQL

| Path | Description | Status | Modified | Size | Hash |
|------|-------------|--------|----------|------|------|
| [MT/.vscode/settings.json](MT/.vscode/settings.json) |  |  | 2026-06-17 | 928B | `d6834b74` |
| [MT/MQL4/.vscode/settings.json](MT/MQL4/.vscode/settings.json) |  |  | 2026-06-17 | 927B | `c3c0af89` |
| [MT/MQL4/Experts/$o$imple.mq4](MT/MQL4/Experts/$o$imple.mq4) |  |  | 2026-07-29 | 12KB | `06af5552` |
| [MT/MQL4/Include/Arrays/Array.mqh](MT/MQL4/Include/Arrays/Array.mqh) |  |  | 2026-07-21 | 6KB | `29d804ca` |
| [MT/MQL4/Include/Arrays/ArrayChar.mqh](MT/MQL4/Include/Arrays/ArrayChar.mqh) |  |  | 2026-07-21 | 23KB | `3df8fe54` |
| [MT/MQL4/Include/Arrays/ArrayDouble.mqh](MT/MQL4/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-07-21 | 24KB | `c44a2bc3` |
| [MT/MQL4/Include/Arrays/ArrayFloat.mqh](MT/MQL4/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-07-21 | 24KB | `92fa9ff2` |
| [MT/MQL4/Include/Arrays/ArrayInt.mqh](MT/MQL4/Include/Arrays/ArrayInt.mqh) |  |  | 2026-07-21 | 23KB | `ebbf910b` |
| [MT/MQL4/Include/Arrays/ArrayLong.mqh](MT/MQL4/Include/Arrays/ArrayLong.mqh) |  |  | 2026-07-21 | 23KB | `6ff220ef` |
| [MT/MQL4/Include/Arrays/ArrayObj.mqh](MT/MQL4/Include/Arrays/ArrayObj.mqh) |  |  | 2026-07-21 | 24KB | `d0b3a268` |
| [MT/MQL4/Include/Arrays/ArrayShort.mqh](MT/MQL4/Include/Arrays/ArrayShort.mqh) |  |  | 2026-07-21 | 24KB | `60d79bb6` |
| [MT/MQL4/Include/Arrays/ArrayString.mqh](MT/MQL4/Include/Arrays/ArrayString.mqh) |  |  | 2026-07-21 | 24KB | `83273ae5` |
| [MT/MQL4/Include/Arrays/List.mqh](MT/MQL4/Include/Arrays/List.mqh) |  |  | 2026-07-21 | 20KB | `63551a44` |
| [MT/MQL4/Include/Arrays/Tree.mqh](MT/MQL4/Include/Arrays/Tree.mqh) |  |  | 2026-07-21 | 13KB | `6f58f568` |
| [MT/MQL4/Include/Arrays/TreeNode.mqh](MT/MQL4/Include/Arrays/TreeNode.mqh) |  |  | 2026-07-21 | 6KB | `4c496c31` |
| [MT/MQL4/Include/COUNT.mqh](MT/MQL4/Include/COUNT.mqh) |  |  | 2026-06-17 | 8KB | `2ec8513b` |
| [MT/MQL4/Include/Canvas/Canvas.mqh](MT/MQL4/Include/Canvas/Canvas.mqh) |  |  | 2026-07-21 | 82KB | `35bff7bb` |
| [MT/MQL4/Include/ChartObjects/ChartObject.mqh](MT/MQL4/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-07-21 | 41KB | `1fe4ca68` |
| [MT/MQL4/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL4/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-07-21 | 7KB | `185cc1c1` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-07-21 | 23KB | `1bdc4250` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-07-21 | 20KB | `cd93d9d3` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-07-21 | 11KB | `681634d9` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-07-21 | 17KB | `9a593088` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-07-21 | 16KB | `f7a2a428` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-07-21 | 15KB | `870b6a4c` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-07-21 | 7KB | `ed4de27c` |
| [MT/MQL4/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL4/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-07-21 | 36KB | `e2dac30a` |
| [MT/MQL4/Include/Charts/Chart.mqh](MT/MQL4/Include/Charts/Chart.mqh) |  |  | 2026-07-21 | 62KB | `1a0d0ee5` |
| [MT/MQL4/Include/Controls/BmpButton.mqh](MT/MQL4/Include/Controls/BmpButton.mqh) |  |  | 2026-07-21 | 11KB | `e6636dc2` |
| [MT/MQL4/Include/Controls/Button.mqh](MT/MQL4/Include/Controls/Button.mqh) |  |  | 2026-07-21 | 6KB | `b420f9ff` |
| [MT/MQL4/Include/Controls/CheckBox.mqh](MT/MQL4/Include/Controls/CheckBox.mqh) |  |  | 2026-07-21 | 7KB | `5c78edfa` |
| [MT/MQL4/Include/Controls/CheckGroup.mqh](MT/MQL4/Include/Controls/CheckGroup.mqh) |  |  | 2026-07-21 | 13KB | `396afe09` |
| [MT/MQL4/Include/Controls/ComboBox.mqh](MT/MQL4/Include/Controls/ComboBox.mqh) |  |  | 2026-07-21 | 13KB | `6eddc276` |
| [MT/MQL4/Include/Controls/DateDropList.mqh](MT/MQL4/Include/Controls/DateDropList.mqh) |  |  | 2026-07-21 | 14KB | `64f7cc0b` |
| [MT/MQL4/Include/Controls/DatePicker.mqh](MT/MQL4/Include/Controls/DatePicker.mqh) |  |  | 2026-07-21 | 10KB | `e4fb2dba` |
| [MT/MQL4/Include/Controls/Defines.mqh](MT/MQL4/Include/Controls/Defines.mqh) |  |  | 2026-07-21 | 12KB | `24dff7f9` |
| [MT/MQL4/Include/Controls/Dialog.mqh](MT/MQL4/Include/Controls/Dialog.mqh) |  |  | 2026-07-21 | 37KB | `08542849` |
| [MT/MQL4/Include/Controls/Edit.mqh](MT/MQL4/Include/Controls/Edit.mqh) |  |  | 2026-07-21 | 8KB | `55d19722` |
| [MT/MQL4/Include/Controls/Label.mqh](MT/MQL4/Include/Controls/Label.mqh) |  |  | 2026-07-21 | 4KB | `69bc9423` |
| [MT/MQL4/Include/Controls/ListView.mqh](MT/MQL4/Include/Controls/ListView.mqh) |  |  | 2026-07-21 | 19KB | `cf4da8db` |
| [MT/MQL4/Include/Controls/Panel.mqh](MT/MQL4/Include/Controls/Panel.mqh) |  |  | 2026-07-21 | 5KB | `c3e6d302` |
| [MT/MQL4/Include/Controls/Picture.mqh](MT/MQL4/Include/Controls/Picture.mqh) |  |  | 2026-07-21 | 5KB | `12aeafe8` |
| [MT/MQL4/Include/Controls/RadioButton.mqh](MT/MQL4/Include/Controls/RadioButton.mqh) |  |  | 2026-07-21 | 6KB | `1f730fd0` |
| [MT/MQL4/Include/Controls/RadioGroup.mqh](MT/MQL4/Include/Controls/RadioGroup.mqh) |  |  | 2026-07-21 | 13KB | `ac89d216` |
| [MT/MQL4/Include/Controls/Rect.mqh](MT/MQL4/Include/Controls/Rect.mqh) |  |  | 2026-07-21 | 10KB | `e3b2d600` |
| [MT/MQL4/Include/Controls/Scrolls.mqh](MT/MQL4/Include/Controls/Scrolls.mqh) |  |  | 2026-07-21 | 26KB | `98c3c8a8` |
| [MT/MQL4/Include/Controls/SpinEdit.mqh](MT/MQL4/Include/Controls/SpinEdit.mqh) |  |  | 2026-07-21 | 10KB | `40a03d96` |
| [MT/MQL4/Include/Controls/TimePicker.mqh](MT/MQL4/Include/Controls/TimePicker.mqh) |  |  | 2026-07-21 | 14KB | `9ae8f057` |
| [MT/MQL4/Include/Controls/Wnd.mqh](MT/MQL4/Include/Controls/Wnd.mqh) |  |  | 2026-07-21 | 29KB | `55cbb430` |
| [MT/MQL4/Include/Controls/WndClient.mqh](MT/MQL4/Include/Controls/WndClient.mqh) |  |  | 2026-07-21 | 12KB | `560fb482` |
| [MT/MQL4/Include/Controls/WndContainer.mqh](MT/MQL4/Include/Controls/WndContainer.mqh) |  |  | 2026-07-21 | 15KB | `8827a68b` |
| [MT/MQL4/Include/Controls/WndObj.mqh](MT/MQL4/Include/Controls/WndObj.mqh) |  |  | 2026-07-21 | 10KB | `32def100` |
| [MT/MQL4/Include/ERRORs.mqh](MT/MQL4/Include/ERRORs.mqh) |  |  | 2026-06-17 | 20KB | `09c555ab` |
| [MT/MQL4/Include/FUNCTIONS.mqh](MT/MQL4/Include/FUNCTIONS.mqh) |  |  | 2026-06-17 | 18KB | `038b6541` |
| [MT/MQL4/Include/Files/File.mqh](MT/MQL4/Include/Files/File.mqh) |  |  | 2026-07-21 | 11KB | `d679fd98` |
| [MT/MQL4/Include/Files/FileBin.mqh](MT/MQL4/Include/Files/FileBin.mqh) |  |  | 2026-07-21 | 20KB | `7d828698` |
| [MT/MQL4/Include/Files/FilePipe.mqh](MT/MQL4/Include/Files/FilePipe.mqh) |  |  | 2026-07-21 | 12KB | `0272c296` |
| [MT/MQL4/Include/Files/FileTxt.mqh](MT/MQL4/Include/Files/FileTxt.mqh) |  |  | 2026-07-21 | 2KB | `e92ef484` |
| [MT/MQL4/Include/INPUT.mqh](MT/MQL4/Include/INPUT.mqh) |  |  | 2026-06-17 | 22KB | `27ad874f` |
| [MT/MQL4/Include/Indicators/BillWilliams.mqh](MT/MQL4/Include/Indicators/BillWilliams.mqh) |  |  | 2026-07-21 | 29KB | `c27ca4b9` |
| [MT/MQL4/Include/Indicators/Custom.mqh](MT/MQL4/Include/Indicators/Custom.mqh) |  |  | 2026-07-21 | 5KB | `97e02c64` |
| [MT/MQL4/Include/Indicators/Indicator.mqh](MT/MQL4/Include/Indicators/Indicator.mqh) |  |  | 2026-07-21 | 6KB | `76365508` |
| [MT/MQL4/Include/Indicators/Indicators.mqh](MT/MQL4/Include/Indicators/Indicators.mqh) |  |  | 2026-07-21 | 11KB | `7e280f54` |
| [MT/MQL4/Include/Indicators/Oscilators.mqh](MT/MQL4/Include/Indicators/Oscilators.mqh) |  |  | 2026-07-21 | 55KB | `64f2642f` |
| [MT/MQL4/Include/Indicators/Series.mqh](MT/MQL4/Include/Indicators/Series.mqh) |  |  | 2026-07-21 | 5KB | `f97ef82c` |
| [MT/MQL4/Include/Indicators/TimeSeries.mqh](MT/MQL4/Include/Indicators/TimeSeries.mqh) |  |  | 2026-07-21 | 19KB | `9d9048a3` |
| [MT/MQL4/Include/Indicators/Trend.mqh](MT/MQL4/Include/Indicators/Trend.mqh) |  |  | 2026-07-21 | 35KB | `81111941` |
| [MT/MQL4/Include/Indicators/Volumes.mqh](MT/MQL4/Include/Indicators/Volumes.mqh) |  |  | 2026-07-21 | 11KB | `dd2a52e4` |
| [MT/MQL4/Include/MAIN.mqh](MT/MQL4/Include/MAIN.mqh) |  |  | 2026-07-29 | 10KB | `4f526ceb` |
| [MT/MQL4/Include/MM.mqh](MT/MQL4/Include/MM.mqh) |  |  | 2026-06-17 | 10KB | `c7d3005a` |
| [MT/MQL4/Include/MovingAverages.mqh](MT/MQL4/Include/MovingAverages.mqh) |  |  | 2026-07-21 | 8KB | `d87e9a1b` |
| [MT/MQL4/Include/ORDERS.mqh](MT/MQL4/Include/ORDERS.mqh) |  |  | 2026-06-17 | 40KB | `fbab4671` |
| [MT/MQL4/Include/OUTPUT.mqh](MT/MQL4/Include/OUTPUT.mqh) |  |  | 2026-06-17 | 19KB | `7ff1d32e` |
| [MT/MQL4/Include/Object.mqh](MT/MQL4/Include/Object.mqh) |  |  | 2026-07-21 | 1KB | `6519631b` |
| [MT/MQL4/Include/SERVICE.mqh](MT/MQL4/Include/SERVICE.mqh) |  |  | 2026-06-17 | 81KB | `67e9cd04` |
| [MT/MQL4/Include/StdLibErr.mqh](MT/MQL4/Include/StdLibErr.mqh) |  |  | 2026-07-21 | 683B | `987aa510` |
| [MT/MQL4/Include/Strings/String.mqh](MT/MQL4/Include/Strings/String.mqh) |  |  | 2026-07-21 | 13KB | `a2a8f645` |
| [MT/MQL4/Include/Tools/DateTime.mqh](MT/MQL4/Include/Tools/DateTime.mqh) |  |  | 2026-07-21 | 17KB | `f1732e44` |
| [MT/MQL4/Include/WinUser32.mqh](MT/MQL4/Include/WinUser32.mqh) |  |  | 2026-07-21 | 17KB | `c4be55b2` |
| [MT/MQL4/Include/head_PIC.mqh](MT/MQL4/Include/head_PIC.mqh) |  |  | 2026-06-17 | 9KB | `b5a78736` |
| [MT/MQL4/Include/iGRAPH.mqh](MT/MQL4/Include/iGRAPH.mqh) |  |  | 2026-06-17 | 38KB | `73d71482` |
| [MT/MQL4/Include/lib_ATR.mqh](MT/MQL4/Include/lib_ATR.mqh) |  |  | 2026-06-17 | 2KB | `e8fa3ca7` |
| [MT/MQL4/Include/lib_Flat.mqh](MT/MQL4/Include/lib_Flat.mqh) |  |  | 2026-06-17 | 13KB | `bc1a865b` |
| [MT/MQL4/Include/lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, single/multi-position telemetry trading | ✅ | 2026-07-29 | 68KB | `ee3ba971` |
| [MT/MQL4/Include/lib_ML_Signal_TB.mqh](MT/MQL4/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-06-17 | 8KB | `86f9658b` |
| [MT/MQL4/Include/lib_ML_Signal_back.mqh](MT/MQL4/Include/lib_ML_Signal_back.mqh) |  |  | 2026-06-17 | 14KB | `996e3367` |
| [MT/MQL4/Include/lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | ⚠️ | 2026-06-17 | 57KB | `75237554` |
| [MT/MQL4/Include/stderror.mqh](MT/MQL4/Include/stderror.mqh) |  |  | 2026-07-21 | 9KB | `aec87c86` |
| [MT/MQL4/Include/stdlib.mqh](MT/MQL4/Include/stdlib.mqh) |  |  | 2026-07-21 | 662B | `268bec52` |
| [MT/MQL4/Indicators/ATR.mq4](MT/MQL4/Indicators/ATR.mq4) |  |  | 2026-07-21 | 3KB | `dd312b03` |
| [MT/MQL4/Indicators/ATR_original.mq4](MT/MQL4/Indicators/ATR_original.mq4) |  |  | 2026-06-17 | 3KB | `efe79c20` |
| [MT/MQL4/Indicators/Accelerator.mq4](MT/MQL4/Indicators/Accelerator.mq4) |  |  | 2026-07-21 | 3KB | `245c5aa7` |
| [MT/MQL4/Indicators/Accumulation.mq4](MT/MQL4/Indicators/Accumulation.mq4) |  |  | 2026-07-21 | 2KB | `a0c2fbe4` |
| [MT/MQL4/Indicators/Alligator.mq4](MT/MQL4/Indicators/Alligator.mq4) |  |  | 2026-07-21 | 3KB | `82fea67e` |
| [MT/MQL4/Indicators/Awesome.mq4](MT/MQL4/Indicators/Awesome.mq4) |  |  | 2026-07-21 | 3KB | `0e492ca3` |
| [MT/MQL4/Indicators/Bands.mq4](MT/MQL4/Indicators/Bands.mq4) |  |  | 2026-07-21 | 4KB | `894a6a9f` |
| [MT/MQL4/Indicators/Bears.mq4](MT/MQL4/Indicators/Bears.mq4) |  |  | 2026-07-21 | 2KB | `549f60ef` |
| [MT/MQL4/Indicators/Bulls.mq4](MT/MQL4/Indicators/Bulls.mq4) |  |  | 2026-07-21 | 2KB | `80e8e544` |
| [MT/MQL4/Indicators/CCI.mq4](MT/MQL4/Indicators/CCI.mq4) |  |  | 2026-07-21 | 4KB | `613fa2e1` |
| [MT/MQL4/Indicators/Custom Moving Averages.mq4](MT/MQL4/Indicators/Custom Moving Averages.mq4) |  |  | 2026-07-21 | 6KB | `1aa756f5` |
| [MT/MQL4/Indicators/Examples/SimplePanel/PanelDialog.mqh](MT/MQL4/Indicators/Examples/SimplePanel/PanelDialog.mqh) |  |  | 2026-07-21 | 15KB | `9a2575df` |
| [MT/MQL4/Indicators/Examples/SimplePanel/SimplePanel.mq4](MT/MQL4/Indicators/Examples/SimplePanel/SimplePanel.mq4) |  |  | 2026-07-21 | 2KB | `98b689e0` |
| [MT/MQL4/Indicators/Heiken Ashi.mq4](MT/MQL4/Indicators/Heiken Ashi.mq4) |  |  | 2026-07-21 | 4KB | `dc166238` |
| [MT/MQL4/Indicators/Ichimoku.mq4](MT/MQL4/Indicators/Ichimoku.mq4) |  |  | 2026-07-21 | 6KB | `cd834b55` |
| [MT/MQL4/Indicators/MACD.mq4](MT/MQL4/Indicators/MACD.mq4) |  |  | 2026-07-21 | 3KB | `11b86bdc` |
| [MT/MQL4/Indicators/Momentum.mq4](MT/MQL4/Indicators/Momentum.mq4) |  |  | 2026-07-21 | 2KB | `4e49723b` |
| [MT/MQL4/Indicators/OsMA.mq4](MT/MQL4/Indicators/OsMA.mq4) |  |  | 2026-07-21 | 3KB | `a4980656` |
| [MT/MQL4/Indicators/Parabolic.mq4](MT/MQL4/Indicators/Parabolic.mq4) |  |  | 2026-07-21 | 7KB | `432cb924` |
| [MT/MQL4/Indicators/RSI.mq4](MT/MQL4/Indicators/RSI.mq4) |  |  | 2026-07-21 | 4KB | `c3187582` |
| [MT/MQL4/Indicators/SpreadCollector.mq4](MT/MQL4/Indicators/SpreadCollector.mq4) |  |  | 2026-07-29 | 3KB | `4964ffa4` |
| [MT/MQL4/Indicators/Stochastic.mq4](MT/MQL4/Indicators/Stochastic.mq4) |  |  | 2026-07-21 | 5KB | `0ecf23fb` |
| [MT/MQL4/Indicators/ZigZag.mq4](MT/MQL4/Indicators/ZigZag.mq4) |  |  | 2026-07-21 | 8KB | `511620e8` |
| [MT/MQL4/Indicators/iATR.mq4](MT/MQL4/Indicators/iATR.mq4) |  |  | 2026-06-17 | 3KB | `2053ea50` |
| [MT/MQL4/Indicators/iATRcycle.mq4](MT/MQL4/Indicators/iATRcycle.mq4) |  |  | 2026-06-17 | 2KB | `3a5033e7` |
| [MT/MQL4/Indicators/iExposure.mq4](MT/MQL4/Indicators/iExposure.mq4) |  |  | 2026-07-21 | 8KB | `7d98a88b` |
| [MT/MQL4/Indicators/iPIC.mq4](MT/MQL4/Indicators/iPIC.mq4) |  |  | 2026-06-17 | 13KB | `802c9a21` |
| [MT/MQL4/Indicators/iPOC.mq4](MT/MQL4/Indicators/iPOC.mq4) |  |  | 2026-06-17 | 7KB | `4b4df898` |
| [MT/MQL4/Indicators/iVolumeCluster.mq4](MT/MQL4/Indicators/iVolumeCluster.mq4) |  |  | 2026-06-17 | 44KB | `db9c3442` |
| [MT/MQL4/Libraries/StdLibErr.mqh](MT/MQL4/Libraries/StdLibErr.mqh) |  |  | 2026-06-17 | 673B | `01044c60` |
| [MT/MQL4/Libraries/WinUser32.mqh](MT/MQL4/Libraries/WinUser32.mqh) |  |  | 2026-06-17 | 17KB | `84f99057` |
| [MT/MQL4/Libraries/stderror.mqh](MT/MQL4/Libraries/stderror.mqh) |  |  | 2026-06-17 | 9KB | `47505e6c` |
| [MT/MQL4/Libraries/stdlib.mq4](MT/MQL4/Libraries/stdlib.mq4) |  |  | 2026-07-21 | 19KB | `cdb0a440` |
| [MT/MQL4/Libraries/stdlib.mqh](MT/MQL4/Libraries/stdlib.mqh) |  |  | 2026-06-17 | 648B | `5695494a` |
| [MT/MQL4/README.md](MT/MQL4/README.md) |  |  | 2026-06-20 | 820B | `4fc86c9a` |
| [MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4](MT/MQL4/Scripts/Examples/DLL/DLLSampleTester.mq4) |  |  | 2026-07-21 | 2KB | `7d447b15` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClient.mq4) |  |  | 2026-07-21 | 3KB | `d0dbff33` |
| [MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4](MT/MQL4/Scripts/Examples/Pipes/PipeClientPure.mq4) |  |  | 2026-07-21 | 4KB | `c0c67ebe` |
| [MT/MQL4/Scripts/ExportOHLC.mq4](MT/MQL4/Scripts/ExportOHLC.mq4) |  |  | 2026-06-17 | 2KB | `134c533f` |
| [MT/MQL4/Scripts/HistoryConvertor1002.mq4](MT/MQL4/Scripts/HistoryConvertor1002.mq4) |  |  | 2026-06-17 | 4KB | `2a904122` |
| [MT/MQL4/Scripts/MATLABLOG.mq4](MT/MQL4/Scripts/MATLABLOG.mq4) |  |  | 2026-06-17 | 10KB | `01bef2dd` |
| [MT/MQL4/Scripts/PeriodConverter.mq4](MT/MQL4/Scripts/PeriodConverter.mq4) |  |  | 2026-07-21 | 6KB | `b5a97900` |
| [MT/MQL4/Scripts/trade.mq4](MT/MQL4/Scripts/trade.mq4) |  |  | 2026-06-17 | 1KB | `7c2e252f` |
| [MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh](MT/MQL4/Trash/iSIG_FALSE_BREAK.mqh) |  |  | 2026-06-17 | 3KB | `98d2d8a4` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS.mqh) |  |  | 2026-06-17 | 2KB | `ec173678` |
| [MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh](MT/MQL4/Trash/iSIG_FIRST_LEVELS_CONFIRM.mqh) |  |  | 2026-06-17 | 9KB | `3d047cfe` |
| [MT/MQL4/Trash/iSIG_TURTLE.mqh](MT/MQL4/Trash/iSIG_TURTLE.mqh) |  |  | 2026-06-17 | 3KB | `1b311295` |
| [MT/MQL4/Trash/lib_PIC_old.mqh](MT/MQL4/Trash/lib_PIC_old.mqh) |  |  | 2026-06-17 | 43KB | `59b6536b` |
| [MT/MQL4/Trash/lib_POC.mqh](MT/MQL4/Trash/lib_POC.mqh) |  |  | 2026-06-17 | 7KB | `130bc358` |
| [MT/MQL4/Trash/lib_REZENKO.mqh](MT/MQL4/Trash/lib_REZENKO.mqh) |  |  | 2026-06-17 | 8KB | `8128da38` |
| [MT/MQL4/Trash/lib_TRG.mqh](MT/MQL4/Trash/lib_TRG.mqh) |  |  | 2026-06-17 | 3KB | `e676d2c4` |
| [MT/MQL4/Trash/lib_Triangle.mqh](MT/MQL4/Trash/lib_Triangle.mqh) |  |  | 2026-06-17 | 9KB | `12350503` |
| [MT/MQL4/Trash/lib_ssss.mqh](MT/MQL4/Trash/lib_ssss.mqh) |  |  | 2026-06-17 | 3KB | `6c2e9b73` |
| [MT/MQL5/Experts/Examples/Controls/ControlsDialog.mqh](MT/MQL5/Experts/Examples/Controls/ControlsDialog.mqh) |  |  | 2026-07-30 | 17KB | `3a941284` |
| [MT/MQL5/Experts/Examples/Math 3D Morpher/Functions.mqh](MT/MQL5/Experts/Examples/Math 3D Morpher/Functions.mqh) |  |  | 2026-07-30 | 13KB | `866fe895` |
| [MT/MQL5/Experts/Examples/Math 3D/Functions.mqh](MT/MQL5/Experts/Examples/Math 3D/Functions.mqh) |  |  | 2026-07-30 | 7KB | `b2294241` |
| [MT/MQL5/Include/Arrays/Array.mqh](MT/MQL5/Include/Arrays/Array.mqh) |  |  | 2026-06-17 | 6KB | `dcaa074e` |
| [MT/MQL5/Include/Arrays/ArrayChar.mqh](MT/MQL5/Include/Arrays/ArrayChar.mqh) |  |  | 2026-06-17 | 24KB | `54edbdc1` |
| [MT/MQL5/Include/Arrays/ArrayColor.mqh](MT/MQL5/Include/Arrays/ArrayColor.mqh) |  |  | 2026-06-17 | 24KB | `5de5acca` |
| [MT/MQL5/Include/Arrays/ArrayDatetime.mqh](MT/MQL5/Include/Arrays/ArrayDatetime.mqh) |  |  | 2026-06-17 | 24KB | `28aca33a` |
| [MT/MQL5/Include/Arrays/ArrayDouble.mqh](MT/MQL5/Include/Arrays/ArrayDouble.mqh) |  |  | 2026-06-17 | 24KB | `b442d2c3` |
| [MT/MQL5/Include/Arrays/ArrayFloat.mqh](MT/MQL5/Include/Arrays/ArrayFloat.mqh) |  |  | 2026-06-17 | 24KB | `58db64bf` |
| [MT/MQL5/Include/Arrays/ArrayInt.mqh](MT/MQL5/Include/Arrays/ArrayInt.mqh) |  |  | 2026-06-17 | 24KB | `60c3a599` |
| [MT/MQL5/Include/Arrays/ArrayLong.mqh](MT/MQL5/Include/Arrays/ArrayLong.mqh) |  |  | 2026-06-17 | 24KB | `93c0a2e1` |
| [MT/MQL5/Include/Arrays/ArrayObj.mqh](MT/MQL5/Include/Arrays/ArrayObj.mqh) |  |  | 2026-06-17 | 24KB | `1b604f04` |
| [MT/MQL5/Include/Arrays/ArrayShort.mqh](MT/MQL5/Include/Arrays/ArrayShort.mqh) |  |  | 2026-06-17 | 24KB | `588fba4c` |
| [MT/MQL5/Include/Arrays/ArrayString.mqh](MT/MQL5/Include/Arrays/ArrayString.mqh) |  |  | 2026-06-17 | 24KB | `d7e92876` |
| [MT/MQL5/Include/Arrays/ArrayUChar.mqh](MT/MQL5/Include/Arrays/ArrayUChar.mqh) |  |  | 2026-06-17 | 24KB | `b7d6f43f` |
| [MT/MQL5/Include/Arrays/ArrayUInt.mqh](MT/MQL5/Include/Arrays/ArrayUInt.mqh) |  |  | 2026-06-17 | 24KB | `e6097a29` |
| [MT/MQL5/Include/Arrays/ArrayULong.mqh](MT/MQL5/Include/Arrays/ArrayULong.mqh) |  |  | 2026-06-17 | 24KB | `6c18b082` |
| [MT/MQL5/Include/Arrays/ArrayUShort.mqh](MT/MQL5/Include/Arrays/ArrayUShort.mqh) |  |  | 2026-06-17 | 24KB | `92db202e` |
| [MT/MQL5/Include/Arrays/List.mqh](MT/MQL5/Include/Arrays/List.mqh) |  |  | 2026-06-17 | 20KB | `a173f72b` |
| [MT/MQL5/Include/Arrays/Tree.mqh](MT/MQL5/Include/Arrays/Tree.mqh) |  |  | 2026-06-17 | 13KB | `8824d2cf` |
| [MT/MQL5/Include/Arrays/TreeNode.mqh](MT/MQL5/Include/Arrays/TreeNode.mqh) |  |  | 2026-06-17 | 6KB | `efde8191` |
| [MT/MQL5/Include/COUNT.mqh](MT/MQL5/Include/COUNT.mqh) |  |  | 2026-07-31 | 8KB | `20eca809` |
| [MT/MQL5/Include/Canvas/Canvas.mqh](MT/MQL5/Include/Canvas/Canvas.mqh) |  |  | 2026-06-17 | 152KB | `4abe8ef4` |
| [MT/MQL5/Include/Canvas/Canvas3D.mqh](MT/MQL5/Include/Canvas/Canvas3D.mqh) |  |  | 2026-07-30 | 16KB | `d4f14337` |
| [MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh](MT/MQL5/Include/Canvas/Charts/ChartCanvas.mqh) |  |  | 2026-06-17 | 35KB | `018e7b5b` |
| [MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh](MT/MQL5/Include/Canvas/Charts/HistogramChart.mqh) |  |  | 2026-06-17 | 11KB | `89f96b38` |
| [MT/MQL5/Include/Canvas/Charts/LineChart.mqh](MT/MQL5/Include/Canvas/Charts/LineChart.mqh) |  |  | 2026-06-17 | 12KB | `ac171461` |
| [MT/MQL5/Include/Canvas/Charts/PieChart.mqh](MT/MQL5/Include/Canvas/Charts/PieChart.mqh) |  |  | 2026-06-17 | 13KB | `81e44597` |
| [MT/MQL5/Include/Canvas/DX/DXBox.mqh](MT/MQL5/Include/Canvas/DX/DXBox.mqh) |  |  | 2026-06-17 | 3KB | `e9cbd560` |
| [MT/MQL5/Include/Canvas/DX/DXBuffers.mqh](MT/MQL5/Include/Canvas/DX/DXBuffers.mqh) |  |  | 2026-06-17 | 4KB | `da4319c8` |
| [MT/MQL5/Include/Canvas/DX/DXData.mqh](MT/MQL5/Include/Canvas/DX/DXData.mqh) |  |  | 2026-07-30 | 1KB | `f058c01b` |
| [MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh](MT/MQL5/Include/Canvas/DX/DXDispatcher.mqh) |  |  | 2026-06-17 | 12KB | `ce240376` |
| [MT/MQL5/Include/Canvas/DX/DXHandle.mqh](MT/MQL5/Include/Canvas/DX/DXHandle.mqh) |  |  | 2026-07-30 | 4KB | `671d5db4` |
| [MT/MQL5/Include/Canvas/DX/DXInput.mqh](MT/MQL5/Include/Canvas/DX/DXInput.mqh) |  |  | 2026-07-30 | 2KB | `f206c389` |
| [MT/MQL5/Include/Canvas/DX/DXMath.mqh](MT/MQL5/Include/Canvas/DX/DXMath.mqh) |  |  | 2026-06-17 | 151KB | `cbff51f5` |
| [MT/MQL5/Include/Canvas/DX/DXMesh.mqh](MT/MQL5/Include/Canvas/DX/DXMesh.mqh) |  |  | 2026-06-17 | 15KB | `5bb993cf` |
| [MT/MQL5/Include/Canvas/DX/DXObject.mqh](MT/MQL5/Include/Canvas/DX/DXObject.mqh) |  |  | 2026-07-30 | 871B | `f97c1ed0` |
| [MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh](MT/MQL5/Include/Canvas/DX/DXObjectBase.mqh) |  |  | 2026-07-30 | 1KB | `649ce810` |
| [MT/MQL5/Include/Canvas/DX/DXShader.mqh](MT/MQL5/Include/Canvas/DX/DXShader.mqh) |  |  | 2026-07-30 | 8KB | `cb45590c` |
| [MT/MQL5/Include/Canvas/DX/DXSurface.mqh](MT/MQL5/Include/Canvas/DX/DXSurface.mqh) |  |  | 2026-06-17 | 6KB | `75cfc660` |
| [MT/MQL5/Include/Canvas/DX/DXTexture.mqh](MT/MQL5/Include/Canvas/DX/DXTexture.mqh) |  |  | 2026-07-30 | 3KB | `d349fe1c` |
| [MT/MQL5/Include/Canvas/DX/DXUtils.mqh](MT/MQL5/Include/Canvas/DX/DXUtils.mqh) |  |  | 2026-06-17 | 35KB | `81b0d9c9` |
| [MT/MQL5/Include/Canvas/FlameCanvas.mqh](MT/MQL5/Include/Canvas/FlameCanvas.mqh) |  |  | 2026-06-17 | 26KB | `8a0d3427` |
| [MT/MQL5/Include/ChartObjects/ChartObject.mqh](MT/MQL5/Include/ChartObjects/ChartObject.mqh) |  |  | 2026-06-17 | 40KB | `f13eb438` |
| [MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh](MT/MQL5/Include/ChartObjects/ChartObjectPanel.mqh) |  |  | 2026-06-17 | 8KB | `7479429b` |
| [MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh](MT/MQL5/Include/ChartObjects/ChartObjectSubChart.mqh) |  |  | 2026-06-17 | 16KB | `0d77ef95` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsArrows.mqh) |  |  | 2026-06-17 | 23KB | `9c0cbe08` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsBmpControls.mqh) |  |  | 2026-06-17 | 20KB | `26885f86` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsChannels.mqh) |  |  | 2026-06-17 | 11KB | `11590972` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsElliott.mqh) |  |  | 2026-06-17 | 9KB | `c0255f7d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsFibo.mqh) |  |  | 2026-06-17 | 17KB | `6ae0eb18` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsGann.mqh) |  |  | 2026-06-17 | 16KB | `f4d66975` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsLines.mqh) |  |  | 2026-06-17 | 15KB | `7888e00d` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsShapes.mqh) |  |  | 2026-06-17 | 7KB | `d6d59613` |
| [MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh](MT/MQL5/Include/ChartObjects/ChartObjectsTxtControls.mqh) |  |  | 2026-06-17 | 37KB | `64387446` |
| [MT/MQL5/Include/Charts/Chart.mqh](MT/MQL5/Include/Charts/Chart.mqh) |  |  | 2026-06-17 | 62KB | `c5d96344` |
| [MT/MQL5/Include/Controls/BmpButton.mqh](MT/MQL5/Include/Controls/BmpButton.mqh) |  |  | 2026-07-30 | 11KB | `a26fafa2` |
| [MT/MQL5/Include/Controls/Button.mqh](MT/MQL5/Include/Controls/Button.mqh) |  |  | 2026-07-30 | 6KB | `288dfc39` |
| [MT/MQL5/Include/Controls/CheckBox.mqh](MT/MQL5/Include/Controls/CheckBox.mqh) |  |  | 2026-06-17 | 7KB | `cd5744e7` |
| [MT/MQL5/Include/Controls/CheckGroup.mqh](MT/MQL5/Include/Controls/CheckGroup.mqh) |  |  | 2026-06-17 | 13KB | `3f03b33e` |
| [MT/MQL5/Include/Controls/ComboBox.mqh](MT/MQL5/Include/Controls/ComboBox.mqh) |  |  | 2026-06-17 | 13KB | `df4bb90f` |
| [MT/MQL5/Include/Controls/DateDropList.mqh](MT/MQL5/Include/Controls/DateDropList.mqh) |  |  | 2026-06-17 | 14KB | `85818981` |
| [MT/MQL5/Include/Controls/DatePicker.mqh](MT/MQL5/Include/Controls/DatePicker.mqh) |  |  | 2026-06-17 | 10KB | `2e2ce745` |
| [MT/MQL5/Include/Controls/Defines.mqh](MT/MQL5/Include/Controls/Defines.mqh) |  |  | 2026-06-17 | 12KB | `066dbc7d` |
| [MT/MQL5/Include/Controls/Dialog.mqh](MT/MQL5/Include/Controls/Dialog.mqh) |  |  | 2026-06-17 | 37KB | `d1e15482` |
| [MT/MQL5/Include/Controls/Edit.mqh](MT/MQL5/Include/Controls/Edit.mqh) |  |  | 2026-06-17 | 8KB | `aed92dbf` |
| [MT/MQL5/Include/Controls/Label.mqh](MT/MQL5/Include/Controls/Label.mqh) |  |  | 2026-06-17 | 4KB | `1d73f6a0` |
| [MT/MQL5/Include/Controls/ListView.mqh](MT/MQL5/Include/Controls/ListView.mqh) |  |  | 2026-07-30 | 19KB | `b8186ebf` |
| [MT/MQL5/Include/Controls/Panel.mqh](MT/MQL5/Include/Controls/Panel.mqh) |  |  | 2026-06-17 | 5KB | `836869ed` |
| [MT/MQL5/Include/Controls/Picture.mqh](MT/MQL5/Include/Controls/Picture.mqh) |  |  | 2026-06-17 | 5KB | `5e62233e` |
| [MT/MQL5/Include/Controls/RadioButton.mqh](MT/MQL5/Include/Controls/RadioButton.mqh) |  |  | 2026-06-17 | 6KB | `5537db3e` |
| [MT/MQL5/Include/Controls/RadioGroup.mqh](MT/MQL5/Include/Controls/RadioGroup.mqh) |  |  | 2026-07-30 | 13KB | `485c2901` |
| [MT/MQL5/Include/Controls/Rect.mqh](MT/MQL5/Include/Controls/Rect.mqh) |  |  | 2026-06-17 | 10KB | `c0b73dc8` |
| [MT/MQL5/Include/Controls/Scrolls.mqh](MT/MQL5/Include/Controls/Scrolls.mqh) |  |  | 2026-07-30 | 26KB | `628f32da` |
| [MT/MQL5/Include/Controls/SpinEdit.mqh](MT/MQL5/Include/Controls/SpinEdit.mqh) |  |  | 2026-06-17 | 10KB | `1e7dded7` |
| [MT/MQL5/Include/Controls/Wnd.mqh](MT/MQL5/Include/Controls/Wnd.mqh) |  |  | 2026-06-17 | 29KB | `0c5fa8a9` |
| [MT/MQL5/Include/Controls/WndClient.mqh](MT/MQL5/Include/Controls/WndClient.mqh) |  |  | 2026-06-17 | 11KB | `25e7cdee` |
| [MT/MQL5/Include/Controls/WndContainer.mqh](MT/MQL5/Include/Controls/WndContainer.mqh) |  |  | 2026-06-17 | 15KB | `e5d88b28` |
| [MT/MQL5/Include/Controls/WndObj.mqh](MT/MQL5/Include/Controls/WndObj.mqh) |  |  | 2026-06-17 | 10KB | `79eb339d` |
| [MT/MQL5/Include/ERRORS.mqh](MT/MQL5/Include/ERRORS.mqh) |  |  | 2026-06-17 | 22B | `f437293a` |
| [MT/MQL5/Include/ERRORs.mqh](MT/MQL5/Include/ERRORs.mqh) |  |  | 2026-06-17 | 20KB | `3a30c213` |
| [MT/MQL5/Include/Expert/Expert.mqh](MT/MQL5/Include/Expert/Expert.mqh) |  |  | 2026-07-30 | 59KB | `b7172ac5` |
| [MT/MQL5/Include/Expert/ExpertBase.mqh](MT/MQL5/Include/Expert/ExpertBase.mqh) |  |  | 2026-06-17 | 26KB | `15d5fae3` |
| [MT/MQL5/Include/Expert/ExpertMoney.mqh](MT/MQL5/Include/Expert/ExpertMoney.mqh) |  |  | 2026-06-17 | 4KB | `9e6d6c11` |
| [MT/MQL5/Include/Expert/ExpertSignal.mqh](MT/MQL5/Include/Expert/ExpertSignal.mqh) |  |  | 2026-06-17 | 19KB | `b7a7ad81` |
| [MT/MQL5/Include/Expert/ExpertTrade.mqh](MT/MQL5/Include/Expert/ExpertTrade.mqh) |  |  | 2026-06-17 | 6KB | `b2b0f317` |
| [MT/MQL5/Include/Expert/ExpertTrailing.mqh](MT/MQL5/Include/Expert/ExpertTrailing.mqh) |  |  | 2026-06-17 | 1KB | `66a3a25d` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedLot.mqh) |  |  | 2026-06-17 | 3KB | `62d53ce2` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedMargin.mqh) |  |  | 2026-06-17 | 3KB | `f8a1fe72` |
| [MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh](MT/MQL5/Include/Expert/Money/MoneyFixedRisk.mqh) |  |  | 2026-06-17 | 4KB | `38b6869e` |
| [MT/MQL5/Include/Expert/Money/MoneyNone.mqh](MT/MQL5/Include/Expert/Money/MoneyNone.mqh) |  |  | 2026-06-17 | 3KB | `b866ac59` |
| [MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh](MT/MQL5/Include/Expert/Money/MoneySizeOptimized.mqh) |  |  | 2026-06-17 | 6KB | `22c850e8` |
| [MT/MQL5/Include/Expert/Signal/SignalAC.mqh](MT/MQL5/Include/Expert/Signal/SignalAC.mqh) |  |  | 2026-06-17 | 7KB | `c3fe7a79` |
| [MT/MQL5/Include/Expert/Signal/SignalAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalAMA.mqh) |  |  | 2026-06-17 | 12KB | `a5bbc59b` |
| [MT/MQL5/Include/Expert/Signal/SignalAO.mqh](MT/MQL5/Include/Expert/Signal/SignalAO.mqh) |  |  | 2026-06-17 | 13KB | `cadb934f` |
| [MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBearsPower.mqh) |  |  | 2026-06-17 | 11KB | `0a9fdc1f` |
| [MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh](MT/MQL5/Include/Expert/Signal/SignalBullsPower.mqh) |  |  | 2026-06-17 | 11KB | `9b6f9b73` |
| [MT/MQL5/Include/Expert/Signal/SignalCCI.mqh](MT/MQL5/Include/Expert/Signal/SignalCCI.mqh) |  |  | 2026-06-17 | 17KB | `8b02f15b` |
| [MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalDEMA.mqh) |  |  | 2026-06-17 | 11KB | `27a1b1b3` |
| [MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh](MT/MQL5/Include/Expert/Signal/SignalDeMarker.mqh) |  |  | 2026-06-17 | 16KB | `28378510` |
| [MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh](MT/MQL5/Include/Expert/Signal/SignalEnvelopes.mqh) |  |  | 2026-06-17 | 9KB | `07c314dc` |
| [MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh](MT/MQL5/Include/Expert/Signal/SignalFrAMA.mqh) |  |  | 2026-06-17 | 11KB | `cc3ea8eb` |
| [MT/MQL5/Include/Expert/Signal/SignalITF.mqh](MT/MQL5/Include/Expert/Signal/SignalITF.mqh) |  |  | 2026-06-17 | 4KB | `0991d92b` |
| [MT/MQL5/Include/Expert/Signal/SignalMA.mqh](MT/MQL5/Include/Expert/Signal/SignalMA.mqh) |  |  | 2026-06-17 | 11KB | `51878396` |
| [MT/MQL5/Include/Expert/Signal/SignalMACD.mqh](MT/MQL5/Include/Expert/Signal/SignalMACD.mqh) |  |  | 2026-06-17 | 19KB | `6794035e` |
| [MT/MQL5/Include/Expert/Signal/SignalRSI.mqh](MT/MQL5/Include/Expert/Signal/SignalRSI.mqh) |  |  | 2026-06-17 | 18KB | `536ef112` |
| [MT/MQL5/Include/Expert/Signal/SignalRVI.mqh](MT/MQL5/Include/Expert/Signal/SignalRVI.mqh) |  |  | 2026-06-17 | 7KB | `89af5171` |
| [MT/MQL5/Include/Expert/Signal/SignalSAR.mqh](MT/MQL5/Include/Expert/Signal/SignalSAR.mqh) |  |  | 2026-06-17 | 7KB | `b84730ef` |
| [MT/MQL5/Include/Expert/Signal/SignalStoch.mqh](MT/MQL5/Include/Expert/Signal/SignalStoch.mqh) |  |  | 2026-06-17 | 19KB | `6cff6dd9` |
| [MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh](MT/MQL5/Include/Expert/Signal/SignalTEMA.mqh) |  |  | 2026-06-17 | 11KB | `e8258b51` |
| [MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh](MT/MQL5/Include/Expert/Signal/SignalTRIX.mqh) |  |  | 2026-06-17 | 17KB | `39e3f752` |
| [MT/MQL5/Include/Expert/Signal/SignalWPR.mqh](MT/MQL5/Include/Expert/Signal/SignalWPR.mqh) |  |  | 2026-06-17 | 16KB | `78fc2800` |
| [MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh](MT/MQL5/Include/Expert/Trailing/TrailingFixedPips.mqh) |  |  | 2026-06-17 | 5KB | `39c49839` |
| [MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh](MT/MQL5/Include/Expert/Trailing/TrailingMA.mqh) |  |  | 2026-06-17 | 6KB | `a11d5980` |
| [MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh](MT/MQL5/Include/Expert/Trailing/TrailingNone.mqh) |  |  | 2026-06-17 | 2KB | `bbdc0191` |
| [MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh](MT/MQL5/Include/Expert/Trailing/TrailingParabolicSAR.mqh) |  |  | 2026-06-17 | 5KB | `b73d3930` |
| [MT/MQL5/Include/FUNCTIONS.mqh](MT/MQL5/Include/FUNCTIONS.mqh) |  |  | 2026-06-17 | 15KB | `b3fce0c5` |
| [MT/MQL5/Include/Files/File.mqh](MT/MQL5/Include/Files/File.mqh) |  |  | 2026-06-17 | 11KB | `9b8c6449` |
| [MT/MQL5/Include/Files/FileBMP.mqh](MT/MQL5/Include/Files/FileBMP.mqh) |  |  | 2026-06-17 | 6KB | `5827c2f4` |
| [MT/MQL5/Include/Files/FileBin.mqh](MT/MQL5/Include/Files/FileBin.mqh) |  |  | 2026-06-17 | 20KB | `916879d9` |
| [MT/MQL5/Include/Files/FilePipe.mqh](MT/MQL5/Include/Files/FilePipe.mqh) |  |  | 2026-07-30 | 12KB | `6b77ae1c` |
| [MT/MQL5/Include/Files/FileTxt.mqh](MT/MQL5/Include/Files/FileTxt.mqh) |  |  | 2026-06-17 | 2KB | `14f5dff2` |
| [MT/MQL5/Include/Generic/ArrayList.mqh](MT/MQL5/Include/Generic/ArrayList.mqh) |  |  | 2026-07-30 | 24KB | `b2a5a567` |
| [MT/MQL5/Include/Generic/HashMap.mqh](MT/MQL5/Include/Generic/HashMap.mqh) |  |  | 2026-06-17 | 25KB | `e22edcd0` |
| [MT/MQL5/Include/Generic/HashSet.mqh](MT/MQL5/Include/Generic/HashSet.mqh) |  |  | 2026-06-17 | 36KB | `d38ceded` |
| [MT/MQL5/Include/Generic/Interfaces/ICollection.mqh](MT/MQL5/Include/Generic/Interfaces/ICollection.mqh) |  |  | 2026-06-17 | 1KB | `402ea83c` |
| [MT/MQL5/Include/Generic/Interfaces/IComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IComparable.mqh) |  |  | 2026-06-17 | 1KB | `aa814da7` |
| [MT/MQL5/Include/Generic/Interfaces/IComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IComparer.mqh) |  |  | 2026-06-17 | 998B | `0cf6f120` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparable.mqh) |  |  | 2026-06-17 | 1012B | `4979c4c7` |
| [MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh](MT/MQL5/Include/Generic/Interfaces/IEqualityComparer.mqh) |  |  | 2026-06-17 | 1KB | `7e8c86a3` |
| [MT/MQL5/Include/Generic/Interfaces/IList.mqh](MT/MQL5/Include/Generic/Interfaces/IList.mqh) |  |  | 2026-06-17 | 1KB | `e5e9586d` |
| [MT/MQL5/Include/Generic/Interfaces/IMap.mqh](MT/MQL5/Include/Generic/Interfaces/IMap.mqh) |  |  | 2026-06-17 | 1KB | `303da59f` |
| [MT/MQL5/Include/Generic/Interfaces/ISet.mqh](MT/MQL5/Include/Generic/Interfaces/ISet.mqh) |  |  | 2026-06-17 | 1KB | `15eaf0e1` |
| [MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh](MT/MQL5/Include/Generic/Internal/ArrayFunction.mqh) |  |  | 2026-06-17 | 4KB | `4d708d05` |
| [MT/MQL5/Include/Generic/Internal/CompareFunction.mqh](MT/MQL5/Include/Generic/Internal/CompareFunction.mqh) |  |  | 2026-06-17 | 7KB | `b5a08f39` |
| [MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultComparer.mqh) |  |  | 2026-06-17 | 1KB | `2f430ea9` |
| [MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh](MT/MQL5/Include/Generic/Internal/DefaultEqualityComparer.mqh) |  |  | 2026-06-17 | 1KB | `ea37b258` |
| [MT/MQL5/Include/Generic/Internal/EqualFunction.mqh](MT/MQL5/Include/Generic/Internal/EqualFunction.mqh) |  |  | 2026-06-17 | 1KB | `47e2bc02` |
| [MT/MQL5/Include/Generic/Internal/HashFunction.mqh](MT/MQL5/Include/Generic/Internal/HashFunction.mqh) |  |  | 2026-06-17 | 7KB | `87c69022` |
| [MT/MQL5/Include/Generic/Internal/Introsort.mqh](MT/MQL5/Include/Generic/Internal/Introsort.mqh) |  |  | 2026-06-17 | 8KB | `2bd4b00f` |
| [MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh](MT/MQL5/Include/Generic/Internal/PrimeGenerator.mqh) |  |  | 2026-06-17 | 3KB | `6d9e6603` |
| [MT/MQL5/Include/Generic/LinkedList.mqh](MT/MQL5/Include/Generic/LinkedList.mqh) |  |  | 2026-06-17 | 20KB | `1cdd7bab` |
| [MT/MQL5/Include/Generic/Queue.mqh](MT/MQL5/Include/Generic/Queue.mqh) |  |  | 2026-07-30 | 14KB | `4cad5f26` |
| [MT/MQL5/Include/Generic/RedBlackTree.mqh](MT/MQL5/Include/Generic/RedBlackTree.mqh) |  |  | 2026-07-30 | 36KB | `cfab06e3` |
| [MT/MQL5/Include/Generic/SortedMap.mqh](MT/MQL5/Include/Generic/SortedMap.mqh) |  |  | 2026-06-17 | 14KB | `5745fcdf` |
| [MT/MQL5/Include/Generic/SortedSet.mqh](MT/MQL5/Include/Generic/SortedSet.mqh) |  |  | 2026-06-17 | 24KB | `0efbc013` |
| [MT/MQL5/Include/Generic/Stack.mqh](MT/MQL5/Include/Generic/Stack.mqh) |  |  | 2026-06-17 | 8KB | `39c47e97` |
| [MT/MQL5/Include/Graphics/Axis.mqh](MT/MQL5/Include/Graphics/Axis.mqh) |  |  | 2026-06-17 | 12KB | `30e582f4` |
| [MT/MQL5/Include/Graphics/ColorGenerator.mqh](MT/MQL5/Include/Graphics/ColorGenerator.mqh) |  |  | 2026-06-17 | 3KB | `204f3a70` |
| [MT/MQL5/Include/Graphics/Curve.mqh](MT/MQL5/Include/Graphics/Curve.mqh) |  |  | 2026-06-17 | 22KB | `5b3764a4` |
| [MT/MQL5/Include/Graphics/Graphic.mqh](MT/MQL5/Include/Graphics/Graphic.mqh) |  |  | 2026-07-30 | 84KB | `dfd8a2e0` |
| [MT/MQL5/Include/INPUT.mqh](MT/MQL5/Include/INPUT.mqh) |  |  | 2026-07-30 | 22KB | `74c21417` |
| [MT/MQL5/Include/Indicators/BillWilliams.mqh](MT/MQL5/Include/Indicators/BillWilliams.mqh) |  |  | 2026-06-17 | 32KB | `f57a6107` |
| [MT/MQL5/Include/Indicators/Custom.mqh](MT/MQL5/Include/Indicators/Custom.mqh) |  |  | 2026-06-17 | 7KB | `5e9fbee8` |
| [MT/MQL5/Include/Indicators/Indicator.mqh](MT/MQL5/Include/Indicators/Indicator.mqh) |  |  | 2026-06-17 | 19KB | `1e663d5c` |
| [MT/MQL5/Include/Indicators/Indicators.mqh](MT/MQL5/Include/Indicators/Indicators.mqh) |  |  | 2026-06-17 | 11KB | `e8cd4f31` |
| [MT/MQL5/Include/Indicators/Oscilators.mqh](MT/MQL5/Include/Indicators/Oscilators.mqh) |  |  | 2026-06-17 | 72KB | `18221239` |
| [MT/MQL5/Include/Indicators/Series.mqh](MT/MQL5/Include/Indicators/Series.mqh) |  |  | 2026-06-17 | 12KB | `e0040d48` |
| [MT/MQL5/Include/Indicators/TimeSeries.mqh](MT/MQL5/Include/Indicators/TimeSeries.mqh) |  |  | 2026-06-17 | 61KB | `9aa20382` |
| [MT/MQL5/Include/Indicators/Trend.mqh](MT/MQL5/Include/Indicators/Trend.mqh) |  |  | 2026-06-17 | 72KB | `eb97c7df` |
| [MT/MQL5/Include/Indicators/Volumes.mqh](MT/MQL5/Include/Indicators/Volumes.mqh) |  |  | 2026-06-17 | 17KB | `81921db6` |
| [MT/MQL5/Include/MAIN.mqh](MT/MQL5/Include/MAIN.mqh) |  |  | 2026-07-31 | 10KB | `a4804fcd` |
| [MT/MQL5/Include/MM.mqh](MT/MQL5/Include/MM.mqh) |  |  | 2026-06-17 | 10KB | `8b02452d` |
| [MT/MQL5/Include/MQL4Compat.mqh](MT/MQL5/Include/MQL4Compat.mqh) |  |  | 2026-07-31 | 28KB | `ba6980dd` |
| [MT/MQL5/Include/Math/Alglib/alglib.mqh](MT/MQL5/Include/Math/Alglib/alglib.mqh) |  |  | 2026-04-16 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/alglibinternal.mqh](MT/MQL5/Include/Math/Alglib/alglibinternal.mqh) |  |  | 2026-06-17 | 579KB | `175c1183` |
| [MT/MQL5/Include/Math/Alglib/alglibmisc.mqh](MT/MQL5/Include/Math/Alglib/alglibmisc.mqh) |  |  | 2026-06-17 | 119KB | `7466a12d` |
| [MT/MQL5/Include/Math/Alglib/ap.mqh](MT/MQL5/Include/Math/Alglib/ap.mqh) |  |  | 2026-06-17 | 89KB | `a7e4677f` |
| [MT/MQL5/Include/Math/Alglib/arrayresize.mqh](MT/MQL5/Include/Math/Alglib/arrayresize.mqh) |  |  | 2026-06-17 | 3KB | `e64b72cb` |
| [MT/MQL5/Include/Math/Alglib/bitconvert.mqh](MT/MQL5/Include/Math/Alglib/bitconvert.mqh) |  |  | 2026-06-17 | 13KB | `c9dffd4e` |
| [MT/MQL5/Include/Math/Alglib/dataanalysis.mqh](MT/MQL5/Include/Math/Alglib/dataanalysis.mqh) |  |  | 2026-06-17 | 1MB | `596bc4ac` |
| [MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh](MT/MQL5/Include/Math/Alglib/delegatefunctions.mqh) |  |  | 2026-06-17 | 21KB | `ebc422fa` |
| [MT/MQL5/Include/Math/Alglib/diffequations.mqh](MT/MQL5/Include/Math/Alglib/diffequations.mqh) |  |  | 2026-06-17 | 32KB | `e612f10b` |
| [MT/MQL5/Include/Math/Alglib/fasttransforms.mqh](MT/MQL5/Include/Math/Alglib/fasttransforms.mqh) |  |  | 2026-06-17 | 92KB | `f6bbf7c2` |
| [MT/MQL5/Include/Math/Alglib/integration.mqh](MT/MQL5/Include/Math/Alglib/integration.mqh) |  |  | 2026-06-17 | 116KB | `f8600aaa` |
| [MT/MQL5/Include/Math/Alglib/interpolation.mqh](MT/MQL5/Include/Math/Alglib/interpolation.mqh) |  |  | 2026-06-17 | 1MB | `43be4546` |
| [MT/MQL5/Include/Math/Alglib/linalg.mqh](MT/MQL5/Include/Math/Alglib/linalg.mqh) |  |  | 2026-06-17 | 1MB | `73b32040` |
| [MT/MQL5/Include/Math/Alglib/matrix.mqh](MT/MQL5/Include/Math/Alglib/matrix.mqh) |  |  | 2026-06-17 | 45KB | `52f0963f` |
| [MT/MQL5/Include/Math/Alglib/optimization.mqh](MT/MQL5/Include/Math/Alglib/optimization.mqh) |  |  | 2026-04-16 | 2MB | `--------` |
| [MT/MQL5/Include/Math/Alglib/solvers.mqh](MT/MQL5/Include/Math/Alglib/solvers.mqh) |  |  | 2026-06-17 | 295KB | `cfe0276c` |
| [MT/MQL5/Include/Math/Alglib/specialfunctions.mqh](MT/MQL5/Include/Math/Alglib/specialfunctions.mqh) |  |  | 2026-06-17 | 235KB | `a4f6fa85` |
| [MT/MQL5/Include/Math/Alglib/statistics.mqh](MT/MQL5/Include/Math/Alglib/statistics.mqh) |  |  | 2026-06-17 | 407KB | `3156c1e5` |
| [MT/MQL5/Include/Math/Fuzzy/dictionary.mqh](MT/MQL5/Include/Math/Fuzzy/dictionary.mqh) |  |  | 2026-06-17 | 8KB | `5fc3e371` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyrule.mqh) |  |  | 2026-06-17 | 17KB | `2b675722` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyterm.mqh) |  |  | 2026-06-17 | 3KB | `b5744882` |
| [MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh](MT/MQL5/Include/Math/Fuzzy/fuzzyvariable.mqh) |  |  | 2026-06-17 | 5KB | `c70f7f31` |
| [MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/genericfuzzysystem.mqh) |  |  | 2026-06-17 | 11KB | `0c24ddb8` |
| [MT/MQL5/Include/Math/Fuzzy/helper.mqh](MT/MQL5/Include/Math/Fuzzy/helper.mqh) |  |  | 2026-06-17 | 7KB | `26906afe` |
| [MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh](MT/MQL5/Include/Math/Fuzzy/inferencemethod.mqh) |  |  | 2026-06-17 | 7KB | `981fa315` |
| [MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/mamdanifuzzysystem.mqh) |  |  | 2026-06-17 | 22KB | `a4ff1a81` |
| [MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh](MT/MQL5/Include/Math/Fuzzy/membershipfunction.mqh) |  |  | 2026-06-17 | 43KB | `db1e7a2e` |
| [MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh](MT/MQL5/Include/Math/Fuzzy/ruleparser.mqh) |  |  | 2026-06-17 | 36KB | `a32fa745` |
| [MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh](MT/MQL5/Include/Math/Fuzzy/sugenofuzzysystem.mqh) |  |  | 2026-06-17 | 13KB | `5502caaf` |
| [MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh](MT/MQL5/Include/Math/Fuzzy/sugenovariable.mqh) |  |  | 2026-06-17 | 10KB | `89b49ae6` |
| [MT/MQL5/Include/Math/Stat/Beta.mqh](MT/MQL5/Include/Math/Stat/Beta.mqh) |  |  | 2026-07-30 | 30KB | `1b5e4a15` |
| [MT/MQL5/Include/Math/Stat/Binomial.mqh](MT/MQL5/Include/Math/Stat/Binomial.mqh) |  |  | 2026-07-30 | 33KB | `8dee31b1` |
| [MT/MQL5/Include/Math/Stat/Cauchy.mqh](MT/MQL5/Include/Math/Stat/Cauchy.mqh) |  |  | 2026-06-17 | 24KB | `2a5b994b` |
| [MT/MQL5/Include/Math/Stat/ChiSquare.mqh](MT/MQL5/Include/Math/Stat/ChiSquare.mqh) |  |  | 2026-07-30 | 25KB | `1769d1b0` |
| [MT/MQL5/Include/Math/Stat/Exponential.mqh](MT/MQL5/Include/Math/Stat/Exponential.mqh) |  |  | 2026-06-17 | 24KB | `f1846a90` |
| [MT/MQL5/Include/Math/Stat/F.mqh](MT/MQL5/Include/Math/Stat/F.mqh) |  |  | 2026-07-30 | 26KB | `770405fe` |
| [MT/MQL5/Include/Math/Stat/Gamma.mqh](MT/MQL5/Include/Math/Stat/Gamma.mqh) |  |  | 2026-07-30 | 31KB | `9f974026` |
| [MT/MQL5/Include/Math/Stat/Geometric.mqh](MT/MQL5/Include/Math/Stat/Geometric.mqh) |  |  | 2026-06-17 | 24KB | `031a2627` |
| [MT/MQL5/Include/Math/Stat/Hypergeometric.mqh](MT/MQL5/Include/Math/Stat/Hypergeometric.mqh) |  |  | 2026-07-30 | 33KB | `83878510` |
| [MT/MQL5/Include/Math/Stat/Logistic.mqh](MT/MQL5/Include/Math/Stat/Logistic.mqh) |  |  | 2026-06-17 | 27KB | `6a74c8a4` |
| [MT/MQL5/Include/Math/Stat/Lognormal.mqh](MT/MQL5/Include/Math/Stat/Lognormal.mqh) |  |  | 2026-07-30 | 29KB | `034e865c` |
| [MT/MQL5/Include/Math/Stat/Math.mqh](MT/MQL5/Include/Math/Stat/Math.mqh) |  |  | 2026-07-30 | 213KB | `2da08049` |
| [MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh](MT/MQL5/Include/Math/Stat/NegativeBinomial.mqh) |  |  | 2026-07-30 | 28KB | `bbf1f88a` |
| [MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh](MT/MQL5/Include/Math/Stat/NoncentralBeta.mqh) |  |  | 2026-07-30 | 33KB | `e39db2fe` |
| [MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh](MT/MQL5/Include/Math/Stat/NoncentralChiSquare.mqh) |  |  | 2026-07-30 | 31KB | `bdeb1e88` |
| [MT/MQL5/Include/Math/Stat/NoncentralF.mqh](MT/MQL5/Include/Math/Stat/NoncentralF.mqh) |  |  | 2026-07-30 | 33KB | `d8b8846a` |
| [MT/MQL5/Include/Math/Stat/NoncentralT.mqh](MT/MQL5/Include/Math/Stat/NoncentralT.mqh) |  |  | 2026-07-30 | 37KB | `7d379810` |
| [MT/MQL5/Include/Math/Stat/Normal.mqh](MT/MQL5/Include/Math/Stat/Normal.mqh) |  |  | 2026-06-17 | 39KB | `21ffb41d` |
| [MT/MQL5/Include/Math/Stat/Poisson.mqh](MT/MQL5/Include/Math/Stat/Poisson.mqh) |  |  | 2026-07-30 | 31KB | `974c0906` |
| [MT/MQL5/Include/Math/Stat/Stat.mqh](MT/MQL5/Include/Math/Stat/Stat.mqh) |  |  | 2026-06-17 | 1KB | `c8af779d` |
| [MT/MQL5/Include/Math/Stat/T.mqh](MT/MQL5/Include/Math/Stat/T.mqh) |  |  | 2026-07-30 | 25KB | `0f716e3f` |
| [MT/MQL5/Include/Math/Stat/Uniform.mqh](MT/MQL5/Include/Math/Stat/Uniform.mqh) |  |  | 2026-07-30 | 25KB | `a8824c8c` |
| [MT/MQL5/Include/Math/Stat/Weibull.mqh](MT/MQL5/Include/Math/Stat/Weibull.mqh) |  |  | 2026-06-17 | 26KB | `ff94f29f` |
| [MT/MQL5/Include/MovingAverages.mqh](MT/MQL5/Include/MovingAverages.mqh) |  |  | 2026-07-30 | 10KB | `f6fe4342` |
| [MT/MQL5/Include/ORDERS.mqh](MT/MQL5/Include/ORDERS.mqh) |  |  | 2026-06-17 | 40KB | `6655a760` |
| [MT/MQL5/Include/OUTPUT.mqh](MT/MQL5/Include/OUTPUT.mqh) |  |  | 2026-06-17 | 18KB | `5a14ae04` |
| [MT/MQL5/Include/Object.mqh](MT/MQL5/Include/Object.mqh) |  |  | 2026-07-30 | 1KB | `fdd7e3eb` |
| [MT/MQL5/Include/OpenCL/OpenCL.mqh](MT/MQL5/Include/OpenCL/OpenCL.mqh) |  |  | 2026-06-17 | 27KB | `a82fa081` |
| [MT/MQL5/Include/SERVICE.mqh](MT/MQL5/Include/SERVICE.mqh) |  |  | 2026-07-31 | 81KB | `2a0fb9c1` |
| [MT/MQL5/Include/StdLibErr.mqh](MT/MQL5/Include/StdLibErr.mqh) |  |  | 2026-07-30 | 683B | `da8a5f96` |
| [MT/MQL5/Include/Strings/String.mqh](MT/MQL5/Include/Strings/String.mqh) |  |  | 2026-06-17 | 13KB | `adbde208` |
| [MT/MQL5/Include/Tools/DateTime.mqh](MT/MQL5/Include/Tools/DateTime.mqh) |  |  | 2026-06-17 | 17KB | `e06f30f0` |
| [MT/MQL5/Include/Trade/AccountInfo.mqh](MT/MQL5/Include/Trade/AccountInfo.mqh) |  |  | 2026-06-17 | 17KB | `336acd5d` |
| [MT/MQL5/Include/Trade/DealInfo.mqh](MT/MQL5/Include/Trade/DealInfo.mqh) |  |  | 2026-06-17 | 15KB | `5f444466` |
| [MT/MQL5/Include/Trade/HistoryOrderInfo.mqh](MT/MQL5/Include/Trade/HistoryOrderInfo.mqh) |  |  | 2026-06-17 | 19KB | `3c45a5f3` |
| [MT/MQL5/Include/Trade/OrderInfo.mqh](MT/MQL5/Include/Trade/OrderInfo.mqh) |  |  | 2026-06-17 | 21KB | `c7977cef` |
| [MT/MQL5/Include/Trade/PositionInfo.mqh](MT/MQL5/Include/Trade/PositionInfo.mqh) |  |  | 2026-06-17 | 15KB | `8f85983c` |
| [MT/MQL5/Include/Trade/SymbolInfo.mqh](MT/MQL5/Include/Trade/SymbolInfo.mqh) |  |  | 2026-06-17 | 35KB | `bb2f2760` |
| [MT/MQL5/Include/Trade/TerminalInfo.mqh](MT/MQL5/Include/Trade/TerminalInfo.mqh) |  |  | 2026-06-17 | 10KB | `db1d371d` |
| [MT/MQL5/Include/Trade/Trade.mqh](MT/MQL5/Include/Trade/Trade.mqh) |  |  | 2026-06-17 | 67KB | `ebefad3b` |
| [MT/MQL5/Include/VirtualKeys.mqh](MT/MQL5/Include/VirtualKeys.mqh) |  |  | 2026-07-30 | 5KB | `bcddfd0c` |
| [MT/MQL5/Include/WinAPI/errhandlingapi.mqh](MT/MQL5/Include/WinAPI/errhandlingapi.mqh) |  |  | 2026-06-17 | 1KB | `9c6abbb5` |
| [MT/MQL5/Include/WinAPI/fileapi.mqh](MT/MQL5/Include/WinAPI/fileapi.mqh) |  |  | 2026-06-17 | 9KB | `ce8862f9` |
| [MT/MQL5/Include/WinAPI/handleapi.mqh](MT/MQL5/Include/WinAPI/handleapi.mqh) |  |  | 2026-06-17 | 1KB | `72389e0e` |
| [MT/MQL5/Include/WinAPI/libloaderapi.mqh](MT/MQL5/Include/WinAPI/libloaderapi.mqh) |  |  | 2026-06-17 | 2KB | `fbe9c927` |
| [MT/MQL5/Include/WinAPI/memoryapi.mqh](MT/MQL5/Include/WinAPI/memoryapi.mqh) |  |  | 2026-06-17 | 5KB | `115d0c9e` |
| [MT/MQL5/Include/WinAPI/processenv.mqh](MT/MQL5/Include/WinAPI/processenv.mqh) |  |  | 2026-06-17 | 1KB | `7788d30f` |
| [MT/MQL5/Include/WinAPI/processthreadsapi.mqh](MT/MQL5/Include/WinAPI/processthreadsapi.mqh) |  |  | 2026-06-17 | 10KB | `5d2c97c4` |
| [MT/MQL5/Include/WinAPI/securitybaseapi.mqh](MT/MQL5/Include/WinAPI/securitybaseapi.mqh) |  |  | 2026-06-17 | 16KB | `a8296031` |
| [MT/MQL5/Include/WinAPI/sysinfoapi.mqh](MT/MQL5/Include/WinAPI/sysinfoapi.mqh) |  |  | 2026-06-17 | 4KB | `f1e35723` |
| [MT/MQL5/Include/WinAPI/winapi.mqh](MT/MQL5/Include/WinAPI/winapi.mqh) |  |  | 2026-06-17 | 827B | `18ecf395` |
| [MT/MQL5/Include/WinAPI/winbase.mqh](MT/MQL5/Include/WinAPI/winbase.mqh) |  |  | 2026-06-17 | 43KB | `80b349f7` |
| [MT/MQL5/Include/WinAPI/windef.mqh](MT/MQL5/Include/WinAPI/windef.mqh) |  |  | 2026-06-17 | 8KB | `b3d4d5b1` |
| [MT/MQL5/Include/WinAPI/wingdi.mqh](MT/MQL5/Include/WinAPI/wingdi.mqh) |  |  | 2026-06-17 | 63KB | `000f20a9` |
| [MT/MQL5/Include/WinAPI/winnt.mqh](MT/MQL5/Include/WinAPI/winnt.mqh) |  |  | 2026-06-17 | 95KB | `0e776dbe` |
| [MT/MQL5/Include/WinAPI/winreg.mqh](MT/MQL5/Include/WinAPI/winreg.mqh) |  |  | 2026-06-17 | 5KB | `3681c95b` |
| [MT/MQL5/Include/WinAPI/winuser.mqh](MT/MQL5/Include/WinAPI/winuser.mqh) |  |  | 2026-06-17 | 81KB | `0a662398` |
| [MT/MQL5/Include/head_PIC.mqh](MT/MQL5/Include/head_PIC.mqh) |  |  | 2026-06-17 | 9KB | `356c8df3` |
| [MT/MQL5/Include/iGRAPH.mqh](MT/MQL5/Include/iGRAPH.mqh) |  |  | 2026-06-17 | 39KB | `f5abe888` |
| [MT/MQL5/Include/lib_ATR.mqh](MT/MQL5/Include/lib_ATR.mqh) |  |  | 2026-06-17 | 2KB | `dcc5b590` |
| [MT/MQL5/Include/lib_Flat.mqh](MT/MQL5/Include/lib_Flat.mqh) |  |  | 2026-06-17 | 13KB | `4536cf5c` |
| [MT/MQL5/Include/lib_ML_Signal.mqh](MT/MQL5/Include/lib_ML_Signal.mqh) |  |  | 2026-07-31 | 36KB | `9e5e0d85` |
| [MT/MQL5/Include/lib_ML_Signal_TB.mqh](MT/MQL5/Include/lib_ML_Signal_TB.mqh) |  |  | 2026-06-17 | 8KB | `86f9658b` |
| [MT/MQL5/Include/lib_PIC.mqh](MT/MQL5/Include/lib_PIC.mqh) |  |  | 2026-07-31 | 56KB | `0f3624b1` |
| [MT/MQL5/Include/stderror.mqh](MT/MQL5/Include/stderror.mqh) |  |  | 2026-06-17 | 9KB | `e8590cbe` |
| [MT/MQL5/Include/stdlib.mqh](MT/MQL5/Include/stdlib.mqh) |  |  | 2026-06-17 | 712B | `b86b17a9` |
| [MT/MQL5/Indicators/Examples/Panels/ChartPanel/PanelDialog.mqh](MT/MQL5/Indicators/Examples/Panels/ChartPanel/PanelDialog.mqh) |  |  | 2026-07-30 | 14KB | `338b566f` |
| [MT/MQL5/Indicators/Examples/Panels/SimplePanel/PanelDialog.mqh](MT/MQL5/Indicators/Examples/Panels/SimplePanel/PanelDialog.mqh) |  |  | 2026-07-30 | 14KB | `1449bcd5` |
| [MT/MQL5/Profiles/Agents/metaeditor-default.md](MT/MQL5/Profiles/Agents/metaeditor-default.md) |  |  | 2026-07-30 | 11KB | `055d51de` |
| [MT/MQL5/Profiles/Agents/metatrader-default.md](MT/MQL5/Profiles/Agents/metatrader-default.md) |  |  | 2026-07-30 | 11KB | `055d51de` |
| [MT/MQL5/Scripts/Examples/AccountInfo/AccountInfoSampleInit.mqh](MT/MQL5/Scripts/Examples/AccountInfo/AccountInfoSampleInit.mqh) |  |  | 2026-07-30 | 917B | `b15a7966` |
| [MT/MQL5/Scripts/Examples/ObjectChart/ChartSampleInit.mqh](MT/MQL5/Scripts/Examples/ObjectChart/ChartSampleInit.mqh) |  |  | 2026-07-30 | 4KB | `e53084b5` |
| [MT/MQL5/Scripts/Examples/ObjectSphere/Sphere.mqh](MT/MQL5/Scripts/Examples/ObjectSphere/Sphere.mqh) |  |  | 2026-07-30 | 7KB | `825b71cb` |
| [MT/MQL5/Scripts/Examples/OrderInfo/OrderInfoSampleInit.mqh](MT/MQL5/Scripts/Examples/OrderInfo/OrderInfoSampleInit.mqh) |  |  | 2026-07-30 | 931B | `94eaf5c3` |
| [MT/MQL5/Scripts/Examples/PositionInfo/PositionInfoSampleInit.mqh](MT/MQL5/Scripts/Examples/PositionInfo/PositionInfoSampleInit.mqh) |  |  | 2026-07-30 | 830B | `5d96b8d8` |
| [MT/MQL5/Scripts/Examples/SymbolInfo/SymbolInfoSampleInit.mqh](MT/MQL5/Scripts/Examples/SymbolInfo/SymbolInfoSampleInit.mqh) |  |  | 2026-07-30 | 1KB | `0aee5312` |
| [MT/MQL5/Scripts/UnitTests/Alglib/TestClasses.mqh](MT/MQL5/Scripts/UnitTests/Alglib/TestClasses.mqh) |  |  | 2026-07-30 | 2MB | `--------` |
| [MT/MQL5/Scripts/UnitTests/Alglib/TestInterfaces.mqh](MT/MQL5/Scripts/UnitTests/Alglib/TestInterfaces.mqh) |  |  | 2026-07-30 | 679KB | `dddad8cb` |
| [MT/README.md](MT/README.md) |  |  | 2026-06-20 | 4KB | `470c4642` |

## Wiki

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [wiki/.archive/execution-tracks-monolith-deprecated.md](wiki/.archive/execution-tracks-monolith-deprecated.md) |  | 2026-06-17 | 89KB | `11a5246a` |
| [wiki/README.md](wiki/README.md) |  | 2026-07-29 | 1KB | `41ec7dc6` |
| [wiki/concepts/folded-mov-channels.md](wiki/concepts/folded-mov-channels.md) |  | 2026-06-17 | 4KB | `04d2d382` |
| [wiki/concepts/signal-archetypes.md](wiki/concepts/signal-archetypes.md) |  | 2026-06-17 | 3KB | `52a35182` |
| [wiki/index.md](wiki/index.md) |  | 2026-08-01 | 6KB | `11ef84ed` |
| [wiki/log.md](wiki/log.md) |  | 2026-08-01 | 81KB | `e888b461` |
| [wiki/research/execution-tracks-direct-direction-audit.md](wiki/research/execution-tracks-direct-direction-audit.md) |  | 2026-06-17 | 7KB | `db2ea437` |
| [wiki/research/execution-tracks-early-research.md](wiki/research/execution-tracks-early-research.md) |  | 2026-06-17 | 5KB | `8d497df0` |
| [wiki/research/execution-tracks-entry-path-v1.md](wiki/research/execution-tracks-entry-path-v1.md) |  | 2026-06-17 | 21KB | `ed6e7d2e` |
| [wiki/research/execution-tracks-live-safe-audit.md](wiki/research/execution-tracks-live-safe-audit.md) |  | 2026-06-17 | 11KB | `d9a70550` |
| [wiki/research/execution-tracks-overview.md](wiki/research/execution-tracks-overview.md) |  | 2026-06-17 | 4KB | `fecf262c` |
| [wiki/research/execution-tracks-reconciliation-plus-audit.md](wiki/research/execution-tracks-reconciliation-plus-audit.md) |  | 2026-06-17 | 7KB | `0f145788` |
| [wiki/research/execution-tracks-reproducibility-plus-parity.md](wiki/research/execution-tracks-reproducibility-plus-parity.md) |  | 2026-06-17 | 5KB | `1ab23523` |
| [wiki/research/execution-tracks-robustness-plus-portfolio.md](wiki/research/execution-tracks-robustness-plus-portfolio.md) |  | 2026-06-17 | 6KB | `91183bdb` |
| [wiki/research/execution-tracks-take-skip-v2.md](wiki/research/execution-tracks-take-skip-v2.md) |  | 2026-06-17 | 24KB | `ec105d66` |
| [wiki/research/execution-tracks-telemetry-plus-mql.md](wiki/research/execution-tracks-telemetry-plus-mql.md) |  | 2026-06-17 | 10KB | `7b5c0cf0` |
| [wiki/research/fractal-stop-research.md](wiki/research/fractal-stop-research.md) |  | 2026-07-30 | 143KB | `84f493d1` |
| [wiki/research/limit-order-feature-foundation.md](wiki/research/limit-order-feature-foundation.md) |  | 2026-06-17 | 4KB | `2bea4655` |
| [wiki/research/methodology-cycle-candidate-source-v2.md](wiki/research/methodology-cycle-candidate-source-v2.md) |  | 2026-06-17 | 3KB | `fdb94cc5` |
| [wiki/research/mt5-execution-loop.md](wiki/research/mt5-execution-loop.md) |  | 2026-08-01 | 5KB | `cb8019db` |
| [wiki/research/signal-quality-research.md](wiki/research/signal-quality-research.md) |  | 2026-06-17 | 8KB | `a5355801` |
| [wiki/wiki.py](wiki/wiki.py) |  | 2026-06-17 | 18KB | `0d2c8d8e` |

## Agent Config

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.kilocode/mcp.json](.kilocode/mcp.json) |  | 2026-06-17 | 481B | `14bc1e7d` |
| [.kilocode/package-lock.json](.kilocode/package-lock.json) |  | 2026-06-17 | 3KB | `ca4a6cad` |
| [.kilocode/rules-architect/user_rules.md](.kilocode/rules-architect/user_rules.md) |  | 2026-06-17 | 1KB | `351b6484` |
| [.kilocode/rules-ask/user_rules.md](.kilocode/rules-ask/user_rules.md) |  | 2026-06-17 | 1KB | `351b6484` |

## Other

| Path | Description | Modified | Size | Hash |
|------|-------------|----------|------|------|
| [.mimocode/plans/1781449924517-mighty-star.md](.mimocode/plans/1781449924517-mighty-star.md) |  | 2026-06-17 | 7KB | `a2896455` |
| [.opencode/agents/reviewer.md](.opencode/agents/reviewer.md) |  | 2026-06-20 | 4KB | `4ec43f10` |
| [.opencode/opencode.json](.opencode/opencode.json) |  | 2026-07-20 | 105B | `bd28a1b3` |
| [.opencode/package-lock.json](.opencode/package-lock.json) |  | 2026-05-20 | 13KB | `afac1cb9` |
| [.opencode/package.json](.opencode/package.json) |  | 2026-05-20 | 64B | `9c478c62` |
| [.superpowers/sdd/2026-07-30-mt5-single-rule-diagnostic-run/task-1-brief.md](.superpowers/sdd/2026-07-30-mt5-single-rule-diagnostic-run/task-1-brief.md) |  | 2026-07-30 | 3KB | `e694d25f` |
| [.superpowers/sdd/2026-07-30-mt5-single-rule-diagnostic-run/task-1-report.md](.superpowers/sdd/2026-07-30-mt5-single-rule-diagnostic-run/task-1-report.md) |  | 2026-07-30 | 2KB | `eba4f27a` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/progress.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/progress.md) |  | 2026-08-01 | 528B | `493f9674` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-1-brief.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-1-brief.md) |  | 2026-08-01 | 8KB | `150b6175` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-1-report.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-1-report.md) |  | 2026-08-01 | 1KB | `8d854c5f` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-2-brief.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-2-brief.md) |  | 2026-08-01 | 7KB | `2c4b2b36` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-2-report.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-2-report.md) |  | 2026-08-01 | 4KB | `4d0b8c0d` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-3-brief.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-3-brief.md) |  | 2026-08-01 | 7KB | `c7d8498f` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-3-report.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-3-report.md) |  | 2026-08-01 | 1KB | `567e5f69` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-4-brief.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-4-brief.md) |  | 2026-08-01 | 8KB | `0b64601a` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-4-report.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-4-report.md) |  | 2026-08-01 | 1KB | `36ade673` |
| [.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-5-brief.md](.superpowers/sdd/2026-08-01-mt5-execution-hygiene-postbatch/task-5-brief.md) |  | 2026-08-01 | 8KB | `5dd22d65` |
| [graphify-out/.graphify_labels.json](graphify-out/.graphify_labels.json) |  | 2026-08-01 | 53KB | `45b92d89` |
| [graphify-out/2026-07-07/.graphify_labels.json](graphify-out/2026-07-07/.graphify_labels.json) |  | 2026-07-07 | 41KB | `974e6f34` |
| [graphify-out/2026-07-07/GRAPH_REPORT.md](graphify-out/2026-07-07/GRAPH_REPORT.md) |  | 2026-07-07 | 329KB | `b44fa01c` |
| [graphify-out/2026-07-08/.graphify_labels.json](graphify-out/2026-07-08/.graphify_labels.json) |  | 2026-07-08 | 48KB | `47ef2de8` |
| [graphify-out/2026-07-08/GRAPH_REPORT.md](graphify-out/2026-07-08/GRAPH_REPORT.md) |  | 2026-07-08 | 288KB | `99b96678` |
| [graphify-out/2026-07-09/.graphify_labels.json](graphify-out/2026-07-09/.graphify_labels.json) |  | 2026-07-09 | 48KB | `a8851cd4` |
| [graphify-out/2026-07-09/GRAPH_REPORT.md](graphify-out/2026-07-09/GRAPH_REPORT.md) |  | 2026-07-09 | 290KB | `80ebee6a` |
| [graphify-out/2026-07-10/.graphify_labels.json](graphify-out/2026-07-10/.graphify_labels.json) |  | 2026-07-10 | 49KB | `061b3f0c` |
| [graphify-out/2026-07-10/GRAPH_REPORT.md](graphify-out/2026-07-10/GRAPH_REPORT.md) |  | 2026-07-10 | 291KB | `4ca12462` |
| [graphify-out/2026-07-20/.graphify_labels.json](graphify-out/2026-07-20/.graphify_labels.json) |  | 2026-07-20 | 49KB | `b88f3203` |
| [graphify-out/2026-07-20/GRAPH_REPORT.md](graphify-out/2026-07-20/GRAPH_REPORT.md) |  | 2026-07-20 | 293KB | `b3b6fefa` |
| [graphify-out/2026-07-22/.graphify_labels.json](graphify-out/2026-07-22/.graphify_labels.json) |  | 2026-07-20 | 49KB | `3a283a36` |
| [graphify-out/2026-07-22/GRAPH_REPORT.md](graphify-out/2026-07-22/GRAPH_REPORT.md) |  | 2026-07-20 | 297KB | `27750780` |
| [graphify-out/2026-07-23/.graphify_labels.json](graphify-out/2026-07-23/.graphify_labels.json) |  | 2026-07-23 | 49KB | `703da3be` |
| [graphify-out/2026-07-23/GRAPH_REPORT.md](graphify-out/2026-07-23/GRAPH_REPORT.md) |  | 2026-07-23 | 300KB | `8f308a65` |
| [graphify-out/2026-07-24/.graphify_labels.json](graphify-out/2026-07-24/.graphify_labels.json) |  | 2026-07-24 | 51KB | `46b94271` |
| [graphify-out/2026-07-24/GRAPH_REPORT.md](graphify-out/2026-07-24/GRAPH_REPORT.md) |  | 2026-07-24 | 309KB | `07cc2655` |
| [graphify-out/2026-07-25/.graphify_labels.json](graphify-out/2026-07-25/.graphify_labels.json) |  | 2026-07-24 | 51KB | `226cadb3` |
| [graphify-out/2026-07-25/GRAPH_REPORT.md](graphify-out/2026-07-25/GRAPH_REPORT.md) |  | 2026-07-24 | 314KB | `774070f6` |
| [graphify-out/2026-07-27/.graphify_labels.json](graphify-out/2026-07-27/.graphify_labels.json) |  | 2026-07-27 | 51KB | `7b6acf42` |
| [graphify-out/2026-07-27/GRAPH_REPORT.md](graphify-out/2026-07-27/GRAPH_REPORT.md) |  | 2026-07-27 | 313KB | `4d8e2c99` |
| [graphify-out/2026-07-28/.graphify_labels.json](graphify-out/2026-07-28/.graphify_labels.json) |  | 2026-07-28 | 51KB | `db0e3bd3` |
| [graphify-out/2026-07-28/GRAPH_REPORT.md](graphify-out/2026-07-28/GRAPH_REPORT.md) |  | 2026-07-28 | 314KB | `4298cc89` |
| [graphify-out/2026-07-29/.graphify_labels.json](graphify-out/2026-07-29/.graphify_labels.json) |  | 2026-07-29 | 51KB | `5cd8a6e8` |
| [graphify-out/2026-07-29/GRAPH_REPORT.md](graphify-out/2026-07-29/GRAPH_REPORT.md) |  | 2026-07-29 | 309KB | `51e1f410` |
| [graphify-out/2026-07-30/.graphify_labels.json](graphify-out/2026-07-30/.graphify_labels.json) |  | 2026-07-30 | 52KB | `f93632c8` |
| [graphify-out/2026-07-30/GRAPH_REPORT.md](graphify-out/2026-07-30/GRAPH_REPORT.md) |  | 2026-07-30 | 318KB | `e23b8f03` |
| [graphify-out/2026-07-31/.graphify_labels.json](graphify-out/2026-07-31/.graphify_labels.json) |  | 2026-07-31 | 53KB | `10a39579` |
| [graphify-out/2026-07-31/GRAPH_REPORT.md](graphify-out/2026-07-31/GRAPH_REPORT.md) |  | 2026-07-31 | 324KB | `9d18d9cf` |
| [graphify-out/2026-08-01/.graphify_labels.json](graphify-out/2026-08-01/.graphify_labels.json) |  | 2026-07-31 | 52KB | `7f121dd8` |
| [graphify-out/2026-08-01/GRAPH_REPORT.md](graphify-out/2026-08-01/GRAPH_REPORT.md) |  | 2026-07-31 | 317KB | `ae41da0e` |
| [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) |  | 2026-08-01 | 322KB | `b928c90a` |
| [graphify-out/cache/ast/v0.9.8/00272354297312ab71fced4688851e223c59ee595787f25ba8b052eb12ef6d03.json](graphify-out/cache/ast/v0.9.8/00272354297312ab71fced4688851e223c59ee595787f25ba8b052eb12ef6d03.json) |  | 2026-07-08 | 135KB | `54d7dbf7` |
| [graphify-out/cache/ast/v0.9.8/0031b7e4444bb7d47f5f5f0a8c8e52794bdd75c255d786a67d66c7ff83723529.json](graphify-out/cache/ast/v0.9.8/0031b7e4444bb7d47f5f5f0a8c8e52794bdd75c255d786a67d66c7ff83723529.json) |  | 2026-07-08 | 17KB | `f7a19787` |
| [graphify-out/cache/ast/v0.9.8/00786492bf33bc63eac4efd674fd8b019aa576b4f1c563a37f235929c8dfc8ef.json](graphify-out/cache/ast/v0.9.8/00786492bf33bc63eac4efd674fd8b019aa576b4f1c563a37f235929c8dfc8ef.json) |  | 2026-07-07 | 846B | `0a6019ff` |
| [graphify-out/cache/ast/v0.9.8/00e7e687796c75f3b2774c02d031b872161a8aaa77600bc8c64bfe0297a501d7.json](graphify-out/cache/ast/v0.9.8/00e7e687796c75f3b2774c02d031b872161a8aaa77600bc8c64bfe0297a501d7.json) |  | 2026-07-08 | 11KB | `1e567b4e` |
| [graphify-out/cache/ast/v0.9.8/010ee2192d71f1ebfd02b5d820b585663c7cc887a2fb747e841234c95cd67b44.json](graphify-out/cache/ast/v0.9.8/010ee2192d71f1ebfd02b5d820b585663c7cc887a2fb747e841234c95cd67b44.json) |  | 2026-07-08 | 880B | `74a84aa9` |
| [graphify-out/cache/ast/v0.9.8/01148ed0ccdd549a92c8adb1bf5cb21f5aa7eab3af82b9ced25fdb664563485b.json](graphify-out/cache/ast/v0.9.8/01148ed0ccdd549a92c8adb1bf5cb21f5aa7eab3af82b9ced25fdb664563485b.json) |  | 2026-07-08 | 9KB | `98b5e836` |
| [graphify-out/cache/ast/v0.9.8/0171fce04341a9a814a51b8fc8831da11b769a6e3dd07d48363ef6d0b2bbebbf.json](graphify-out/cache/ast/v0.9.8/0171fce04341a9a814a51b8fc8831da11b769a6e3dd07d48363ef6d0b2bbebbf.json) |  | 2026-07-10 | 18KB | `ebd4956d` |
| [graphify-out/cache/ast/v0.9.8/019ab52388af26b3181a5dd6ac505725fd4d56100c61402584856d2aff23a02e.json](graphify-out/cache/ast/v0.9.8/019ab52388af26b3181a5dd6ac505725fd4d56100c61402584856d2aff23a02e.json) |  | 2026-07-25 | 8KB | `34fbb3aa` |
| [graphify-out/cache/ast/v0.9.8/019d2c2b43f28a6ca528c1637814227bf920d4b239d941c79aeb9cc0338f6e46.json](graphify-out/cache/ast/v0.9.8/019d2c2b43f28a6ca528c1637814227bf920d4b239d941c79aeb9cc0338f6e46.json) |  | 2026-07-24 | 7KB | `02681697` |
| [graphify-out/cache/ast/v0.9.8/01dbe3e22272228bcb75aa5f78f1e19842b8fe412994396c8af600bc74fbf209.json](graphify-out/cache/ast/v0.9.8/01dbe3e22272228bcb75aa5f78f1e19842b8fe412994396c8af600bc74fbf209.json) |  | 2026-07-07 | 255B | `bc6eae52` |
| [graphify-out/cache/ast/v0.9.8/02533d11a6bc39bef65990f12e34269fc67549b8d1963eb46c5e490be809ead6.json](graphify-out/cache/ast/v0.9.8/02533d11a6bc39bef65990f12e34269fc67549b8d1963eb46c5e490be809ead6.json) |  | 2026-07-08 | 1KB | `f40b2cd2` |
| [graphify-out/cache/ast/v0.9.8/02b79b4c7a4021e1833be8af207516adb720423b8907ea57730324c98c6cb01e.json](graphify-out/cache/ast/v0.9.8/02b79b4c7a4021e1833be8af207516adb720423b8907ea57730324c98c6cb01e.json) |  | 2026-07-22 | 8KB | `e3cd352b` |
| [graphify-out/cache/ast/v0.9.8/02c02681a9f0be9fb38a96d2b0be0bb66ef1fb1bd967e79b2ffdeaef001a4e1e.json](graphify-out/cache/ast/v0.9.8/02c02681a9f0be9fb38a96d2b0be0bb66ef1fb1bd967e79b2ffdeaef001a4e1e.json) |  | 2026-07-08 | 28KB | `4ed73595` |
| [graphify-out/cache/ast/v0.9.8/02de6622549e449455adc03fc72a0a0e484892d1a41cb9a8ddd19b7a4149d192.json](graphify-out/cache/ast/v0.9.8/02de6622549e449455adc03fc72a0a0e484892d1a41cb9a8ddd19b7a4149d192.json) |  | 2026-07-07 | 19KB | `e3dfda1a` |
| [graphify-out/cache/ast/v0.9.8/02e3e6567f8006c17858ae8fc31c9ca5035999574bce0e4e1ef3e0c1455fc44d.json](graphify-out/cache/ast/v0.9.8/02e3e6567f8006c17858ae8fc31c9ca5035999574bce0e4e1ef3e0c1455fc44d.json) |  | 2026-07-08 | 23KB | `7a157d6f` |
| [graphify-out/cache/ast/v0.9.8/031d42d3a9f2fccfcc2e3b390772ab7a52e302c56319d38cbd589c510382ff80.json](graphify-out/cache/ast/v0.9.8/031d42d3a9f2fccfcc2e3b390772ab7a52e302c56319d38cbd589c510382ff80.json) |  | 2026-07-08 | 14KB | `ec3f2da1` |
| [graphify-out/cache/ast/v0.9.8/03949df3ededee0741792169893fafae4bc3ef553fce0e8d771120389416b306.json](graphify-out/cache/ast/v0.9.8/03949df3ededee0741792169893fafae4bc3ef553fce0e8d771120389416b306.json) |  | 2026-07-08 | 17KB | `80522dd0` |
| [graphify-out/cache/ast/v0.9.8/0415081efc220fba5056bf7b75924827950beb59d9835a3263380dfe3bb8c638.json](graphify-out/cache/ast/v0.9.8/0415081efc220fba5056bf7b75924827950beb59d9835a3263380dfe3bb8c638.json) |  | 2026-07-08 | 5KB | `9a1c0af1` |
| [graphify-out/cache/ast/v0.9.8/042911628cd514fba1c2ffce73414ec5f16295c4e1a2a06c835d8179e76aa899.json](graphify-out/cache/ast/v0.9.8/042911628cd514fba1c2ffce73414ec5f16295c4e1a2a06c835d8179e76aa899.json) |  | 2026-07-08 | 25KB | `0599d944` |
| [graphify-out/cache/ast/v0.9.8/052d560adf40e09bfecf7fae97e77c37df3bf744831fd31c203818e97a859346.json](graphify-out/cache/ast/v0.9.8/052d560adf40e09bfecf7fae97e77c37df3bf744831fd31c203818e97a859346.json) |  | 2026-07-08 | 19KB | `9a7ce472` |
| [graphify-out/cache/ast/v0.9.8/05c344f9dce75a2f789cf1a2239413a9ecee0c8530b5aa9e4dd28b9983c226ee.json](graphify-out/cache/ast/v0.9.8/05c344f9dce75a2f789cf1a2239413a9ecee0c8530b5aa9e4dd28b9983c226ee.json) |  | 2026-07-08 | 44KB | `6cb6fb90` |
| [graphify-out/cache/ast/v0.9.8/060db94cb4a49403d9a183f7d4cfda1d2664c17b30e2b908af54fef631a2d5c2.json](graphify-out/cache/ast/v0.9.8/060db94cb4a49403d9a183f7d4cfda1d2664c17b30e2b908af54fef631a2d5c2.json) |  | 2026-07-30 | 19KB | `b27b3ae2` |
| [graphify-out/cache/ast/v0.9.8/06188963189a2757bd4bc2401effd13008afef7bd25c98f7eb64303a0493c735.json](graphify-out/cache/ast/v0.9.8/06188963189a2757bd4bc2401effd13008afef7bd25c98f7eb64303a0493c735.json) |  | 2026-07-08 | 11KB | `512eb14b` |
| [graphify-out/cache/ast/v0.9.8/06e0226b2a8b3fc0ce61d6ddfbf4c7eafa69bc67079b1635263ea141fff14fb0.json](graphify-out/cache/ast/v0.9.8/06e0226b2a8b3fc0ce61d6ddfbf4c7eafa69bc67079b1635263ea141fff14fb0.json) |  | 2026-07-08 | 5KB | `2e57b849` |
| [graphify-out/cache/ast/v0.9.8/06f2984c00af0ebcfface89b4ba47ab22037614ee8fe661b108d36a867b85593.json](graphify-out/cache/ast/v0.9.8/06f2984c00af0ebcfface89b4ba47ab22037614ee8fe661b108d36a867b85593.json) |  | 2026-07-08 | 26KB | `54ec8b81` |
| [graphify-out/cache/ast/v0.9.8/06ff9d7922023b9ff3fa5f78336cb56e8463974f9bd5007a528b52bfd1c073e0.json](graphify-out/cache/ast/v0.9.8/06ff9d7922023b9ff3fa5f78336cb56e8463974f9bd5007a528b52bfd1c073e0.json) |  | 2026-07-07 | 5KB | `29c50d7a` |
| [graphify-out/cache/ast/v0.9.8/0738bef7fb891288545e9930cf6111b8fe186c433c3abb78ebd0f893d50fcc98.json](graphify-out/cache/ast/v0.9.8/0738bef7fb891288545e9930cf6111b8fe186c433c3abb78ebd0f893d50fcc98.json) |  | 2026-07-08 | 3KB | `8b70b5d6` |
| [graphify-out/cache/ast/v0.9.8/074f3b6e8363dd69caf6835dbd3ee9efb1285958cb4ab09a9057055a454f277d.json](graphify-out/cache/ast/v0.9.8/074f3b6e8363dd69caf6835dbd3ee9efb1285958cb4ab09a9057055a454f277d.json) |  | 2026-07-08 | 2KB | `c8096da2` |
| [graphify-out/cache/ast/v0.9.8/0769b2ad2a0e4d20814459a4bf408e4aa2b334051856e16f8dfe7edda04e10bb.json](graphify-out/cache/ast/v0.9.8/0769b2ad2a0e4d20814459a4bf408e4aa2b334051856e16f8dfe7edda04e10bb.json) |  | 2026-07-08 | 10KB | `280614cb` |
| [graphify-out/cache/ast/v0.9.8/079a0a120a9d99bb5b71a944b7446ca7bd8b3f75cdf953671be030ac60c27366.json](graphify-out/cache/ast/v0.9.8/079a0a120a9d99bb5b71a944b7446ca7bd8b3f75cdf953671be030ac60c27366.json) |  | 2026-07-08 | 4KB | `041597ca` |
| [graphify-out/cache/ast/v0.9.8/07ef3a9e35ee281d20ce6e4dc1f93324828f71e534fcf879930621f60c45bc0f.json](graphify-out/cache/ast/v0.9.8/07ef3a9e35ee281d20ce6e4dc1f93324828f71e534fcf879930621f60c45bc0f.json) |  | 2026-07-08 | 107KB | `7f4f6730` |
| [graphify-out/cache/ast/v0.9.8/08002bbbf1bd9687a3fb5354cb3b4b8ea6f991843753fbfc1a2cc531355b2710.json](graphify-out/cache/ast/v0.9.8/08002bbbf1bd9687a3fb5354cb3b4b8ea6f991843753fbfc1a2cc531355b2710.json) |  | 2026-07-08 | 35KB | `81d01cc2` |
| [graphify-out/cache/ast/v0.9.8/083ef32108d803d4e9caf26aa275f10b2bc4240ea9a927d0478e064bd77f4ceb.json](graphify-out/cache/ast/v0.9.8/083ef32108d803d4e9caf26aa275f10b2bc4240ea9a927d0478e064bd77f4ceb.json) |  | 2026-07-23 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/0898130be08fa2d8e4e22c29ad74783a6ba9cd4d70743fe7af7a9998bfbbb0e3.json](graphify-out/cache/ast/v0.9.8/0898130be08fa2d8e4e22c29ad74783a6ba9cd4d70743fe7af7a9998bfbbb0e3.json) |  | 2026-07-07 | 15KB | `7ba1d1e9` |
| [graphify-out/cache/ast/v0.9.8/08c9f950c423096f9947baad20e5e188e7a9be054bedda5a4206d0801f035ff6.json](graphify-out/cache/ast/v0.9.8/08c9f950c423096f9947baad20e5e188e7a9be054bedda5a4206d0801f035ff6.json) |  | 2026-07-08 | 10KB | `31f29ca9` |
| [graphify-out/cache/ast/v0.9.8/08d89f3a96cfdca501ffdce8a049f6f3db0adbae4174e37dd7543e7fa98dfe41.json](graphify-out/cache/ast/v0.9.8/08d89f3a96cfdca501ffdce8a049f6f3db0adbae4174e37dd7543e7fa98dfe41.json) |  | 2026-07-08 | 14KB | `e436559b` |
| [graphify-out/cache/ast/v0.9.8/08f853baa5adcc36410ba4b99399f89bf55057252c88eaf59078cdae566daed0.json](graphify-out/cache/ast/v0.9.8/08f853baa5adcc36410ba4b99399f89bf55057252c88eaf59078cdae566daed0.json) |  | 2026-07-08 | 37KB | `8e92fdf2` |
| [graphify-out/cache/ast/v0.9.8/090224d1f1c9ab940121360104d78c6fdf32eafa9a9a0e9c5e316d4d685876a8.json](graphify-out/cache/ast/v0.9.8/090224d1f1c9ab940121360104d78c6fdf32eafa9a9a0e9c5e316d4d685876a8.json) |  | 2026-07-08 | 4KB | `de682a07` |
| [graphify-out/cache/ast/v0.9.8/0919073ead06491cda2a3f7b9b507e69116121608d8d3df6ad99718b5e5ee8ec.json](graphify-out/cache/ast/v0.9.8/0919073ead06491cda2a3f7b9b507e69116121608d8d3df6ad99718b5e5ee8ec.json) |  | 2026-07-07 | 798B | `de141f5d` |
| [graphify-out/cache/ast/v0.9.8/091c0e9c283d2efc5a8ae15089c9cd7c9fa22afce3f565d0728d30f07c494a29.json](graphify-out/cache/ast/v0.9.8/091c0e9c283d2efc5a8ae15089c9cd7c9fa22afce3f565d0728d30f07c494a29.json) |  | 2026-07-08 | 845B | `6c082442` |
| [graphify-out/cache/ast/v0.9.8/091d6a63bd2ed634784a9608655d3092ce6c5a2286825be7c3a5ddafe2a39070.json](graphify-out/cache/ast/v0.9.8/091d6a63bd2ed634784a9608655d3092ce6c5a2286825be7c3a5ddafe2a39070.json) |  | 2026-07-07 | 19KB | `fedd501e` |
| [graphify-out/cache/ast/v0.9.8/091e221302528f42fb657f4bb48e837d06c3846c6a422cdeaae8ef6a7c01b49b.json](graphify-out/cache/ast/v0.9.8/091e221302528f42fb657f4bb48e837d06c3846c6a422cdeaae8ef6a7c01b49b.json) |  | 2026-07-07 | 23KB | `c093d17c` |
| [graphify-out/cache/ast/v0.9.8/0924b0e0541adcdb5912fb12b9fac2901f4e23b710214fe56df2f0b57d071c09.json](graphify-out/cache/ast/v0.9.8/0924b0e0541adcdb5912fb12b9fac2901f4e23b710214fe56df2f0b57d071c09.json) |  | 2026-07-07 | 14KB | `1f87feb7` |
| [graphify-out/cache/ast/v0.9.8/09381c5735f971f0f9f69d1be863025ad2243f37c66a7665d2aabea77039c5e3.json](graphify-out/cache/ast/v0.9.8/09381c5735f971f0f9f69d1be863025ad2243f37c66a7665d2aabea77039c5e3.json) |  | 2026-07-08 | 6KB | `9f374f1d` |
| [graphify-out/cache/ast/v0.9.8/093da23209fe44771e6ec27bca44207c019cbada1495e0621c66c63090702bed.json](graphify-out/cache/ast/v0.9.8/093da23209fe44771e6ec27bca44207c019cbada1495e0621c66c63090702bed.json) |  | 2026-07-31 | 15KB | `c5a4c0da` |
| [graphify-out/cache/ast/v0.9.8/095e8b3d0575f7805ed5328d901fa533f577725fb5d28d5489a9bb8a00ba3c19.json](graphify-out/cache/ast/v0.9.8/095e8b3d0575f7805ed5328d901fa533f577725fb5d28d5489a9bb8a00ba3c19.json) |  | 2026-07-08 | 26KB | `b6457b7f` |
| [graphify-out/cache/ast/v0.9.8/09bea294abbc3119ccfbc6e917df049d3d9b13225a80b79a749cbe956f572efc.json](graphify-out/cache/ast/v0.9.8/09bea294abbc3119ccfbc6e917df049d3d9b13225a80b79a749cbe956f572efc.json) |  | 2026-07-07 | 25KB | `3bfdfb0a` |
| [graphify-out/cache/ast/v0.9.8/0a4812605f3f95a1da27ff94d0e388bb1496fd67af2bf530d36cb84c85f71075.json](graphify-out/cache/ast/v0.9.8/0a4812605f3f95a1da27ff94d0e388bb1496fd67af2bf530d36cb84c85f71075.json) |  | 2026-07-07 | 19KB | `c6291b28` |
| [graphify-out/cache/ast/v0.9.8/0ac762f3547e69f705084a672d417df863d73d1c2c45a057d3f5f594770bbdf1.json](graphify-out/cache/ast/v0.9.8/0ac762f3547e69f705084a672d417df863d73d1c2c45a057d3f5f594770bbdf1.json) |  | 2026-07-08 | 8KB | `08f52a37` |
| [graphify-out/cache/ast/v0.9.8/0b345139d609d9f79bbabeed8bdf9e17fda190be29a10890c789a447eabecf00.json](graphify-out/cache/ast/v0.9.8/0b345139d609d9f79bbabeed8bdf9e17fda190be29a10890c789a447eabecf00.json) |  | 2026-07-08 | 53KB | `5b8fb737` |
| [graphify-out/cache/ast/v0.9.8/0c49df0a9defad6c3c78a3c61cc9e246e25e7a2a1b1062b851ac70cdc3234750.json](graphify-out/cache/ast/v0.9.8/0c49df0a9defad6c3c78a3c61cc9e246e25e7a2a1b1062b851ac70cdc3234750.json) |  | 2026-07-08 | 7KB | `39c833c8` |
| [graphify-out/cache/ast/v0.9.8/0c65b6594a30fe8d487a1e0a7f3d312e4b917701c4e836d036ef702f1e9b16a0.json](graphify-out/cache/ast/v0.9.8/0c65b6594a30fe8d487a1e0a7f3d312e4b917701c4e836d036ef702f1e9b16a0.json) |  | 2026-07-08 | 4KB | `12c35b6c` |
| [graphify-out/cache/ast/v0.9.8/0cd567123660341a959b0a788611e3e86c26473cb3535c3d9546621ab0df6d51.json](graphify-out/cache/ast/v0.9.8/0cd567123660341a959b0a788611e3e86c26473cb3535c3d9546621ab0df6d51.json) |  | 2026-07-07 | 801B | `0feb7c60` |
| [graphify-out/cache/ast/v0.9.8/0d5e4ef84c4bdb262671589688bc74f6c673ac0956afb8e7222899f03f85b69d.json](graphify-out/cache/ast/v0.9.8/0d5e4ef84c4bdb262671589688bc74f6c673ac0956afb8e7222899f03f85b69d.json) |  | 2026-07-08 | 5KB | `b0e77950` |
| [graphify-out/cache/ast/v0.9.8/0d6ff61a46c87f3206c1ffc815ca62936eb4c5ebb7f962d208bc3ed1910b6b55.json](graphify-out/cache/ast/v0.9.8/0d6ff61a46c87f3206c1ffc815ca62936eb4c5ebb7f962d208bc3ed1910b6b55.json) |  | 2026-07-08 | 8KB | `e7789346` |
| [graphify-out/cache/ast/v0.9.8/0d99d70e5e6681f19b67a1cd824ef7e44d3e534f7e340cd27e458b8d92595fca.json](graphify-out/cache/ast/v0.9.8/0d99d70e5e6681f19b67a1cd824ef7e44d3e534f7e340cd27e458b8d92595fca.json) |  | 2026-07-24 | 9KB | `ec6f8ffa` |
| [graphify-out/cache/ast/v0.9.8/0dc4946b78c355c2c6b10ddd683e698e23a813774d27b1cab506edb6394092c6.json](graphify-out/cache/ast/v0.9.8/0dc4946b78c355c2c6b10ddd683e698e23a813774d27b1cab506edb6394092c6.json) |  | 2026-07-08 | 14KB | `8140a839` |
| [graphify-out/cache/ast/v0.9.8/0dd2f03f9f0d83aa6a5496c21bcbafdaec5e06fc823aaef73441980117a265c4.json](graphify-out/cache/ast/v0.9.8/0dd2f03f9f0d83aa6a5496c21bcbafdaec5e06fc823aaef73441980117a265c4.json) |  | 2026-07-08 | 4KB | `35b2bc4b` |
| [graphify-out/cache/ast/v0.9.8/0dec9370716edfcd96a6a542abc52a965b1806199cb6f248c05068d4666c7983.json](graphify-out/cache/ast/v0.9.8/0dec9370716edfcd96a6a542abc52a965b1806199cb6f248c05068d4666c7983.json) |  | 2026-07-08 | 10KB | `8e46a9ec` |
| [graphify-out/cache/ast/v0.9.8/0dfe340ccf59ace30687848ef1b32a5593ba84d4ba00f4b73364ae7b7a4fface.json](graphify-out/cache/ast/v0.9.8/0dfe340ccf59ace30687848ef1b32a5593ba84d4ba00f4b73364ae7b7a4fface.json) |  | 2026-07-08 | 9KB | `5bd8b99d` |
| [graphify-out/cache/ast/v0.9.8/0e0f63e5ceb1b7a33a41226e751f96358761d0c0db025b646371852a17109807.json](graphify-out/cache/ast/v0.9.8/0e0f63e5ceb1b7a33a41226e751f96358761d0c0db025b646371852a17109807.json) |  | 2026-07-08 | 15KB | `59a6b88d` |
| [graphify-out/cache/ast/v0.9.8/0e1410aba3c5894fbd570359003bc55b56a4fbc52c4b47386c964e392df5613f.json](graphify-out/cache/ast/v0.9.8/0e1410aba3c5894fbd570359003bc55b56a4fbc52c4b47386c964e392df5613f.json) |  | 2026-07-29 | 66KB | `d7f64093` |
| [graphify-out/cache/ast/v0.9.8/0e359e18761cc89f5a559dacdcbe02a4ee3660227a01e1b49a80d31e93dc6ab7.json](graphify-out/cache/ast/v0.9.8/0e359e18761cc89f5a559dacdcbe02a4ee3660227a01e1b49a80d31e93dc6ab7.json) |  | 2026-07-07 | 16KB | `2a36e3cd` |
| [graphify-out/cache/ast/v0.9.8/0e3c081b2e7a7ce57f9ef79df69bb51a04a90854809c9e63c3e85ee382fab171.json](graphify-out/cache/ast/v0.9.8/0e3c081b2e7a7ce57f9ef79df69bb51a04a90854809c9e63c3e85ee382fab171.json) |  | 2026-07-08 | 8KB | `5598c8ba` |
| [graphify-out/cache/ast/v0.9.8/0e4b29577d9f58dc192894c7b8e8b9bded5d5850ae5437b22fc8d9283173c1f0.json](graphify-out/cache/ast/v0.9.8/0e4b29577d9f58dc192894c7b8e8b9bded5d5850ae5437b22fc8d9283173c1f0.json) |  | 2026-07-29 | 64KB | `9a88b47a` |
| [graphify-out/cache/ast/v0.9.8/0e7fb3b6ec55617be9083b7870b8caf22aea200cb9cf10255449a1501004ea0e.json](graphify-out/cache/ast/v0.9.8/0e7fb3b6ec55617be9083b7870b8caf22aea200cb9cf10255449a1501004ea0e.json) |  | 2026-07-08 | 3KB | `6b001e3e` |
| [graphify-out/cache/ast/v0.9.8/0edd9f39418a12ffda12c17ad9e6ab71ae1835d69e76e3bedfbb34cec7a0056a.json](graphify-out/cache/ast/v0.9.8/0edd9f39418a12ffda12c17ad9e6ab71ae1835d69e76e3bedfbb34cec7a0056a.json) |  | 2026-07-08 | 28KB | `699ced26` |
| [graphify-out/cache/ast/v0.9.8/0f3943ea04379ffd6aade82b659f5d4a443ae4c0ba49615e48959f1e1e964d61.json](graphify-out/cache/ast/v0.9.8/0f3943ea04379ffd6aade82b659f5d4a443ae4c0ba49615e48959f1e1e964d61.json) |  | 2026-07-08 | 43KB | `86766ae5` |
| [graphify-out/cache/ast/v0.9.8/0f4a4537dd2a0125eaf60e9f9ac0fd2bf371599b60c0a036b618c6032bc4e80e.json](graphify-out/cache/ast/v0.9.8/0f4a4537dd2a0125eaf60e9f9ac0fd2bf371599b60c0a036b618c6032bc4e80e.json) |  | 2026-07-08 | 7KB | `9b2b3c9e` |
| [graphify-out/cache/ast/v0.9.8/0f714776c03b8484404723a725aead337dfdeb01584663f764dd706044507304.json](graphify-out/cache/ast/v0.9.8/0f714776c03b8484404723a725aead337dfdeb01584663f764dd706044507304.json) |  | 2026-07-08 | 22KB | `bcff2e20` |
| [graphify-out/cache/ast/v0.9.8/0f7ed8fabd311545b41c47a672d3c2392c2dd993716e5da66c03206287f17161.json](graphify-out/cache/ast/v0.9.8/0f7ed8fabd311545b41c47a672d3c2392c2dd993716e5da66c03206287f17161.json) |  | 2026-07-07 | 16KB | `43cf4189` |
| [graphify-out/cache/ast/v0.9.8/0fc96f785699687c5d8ea014b9cb6de0917d5e377e2d72f4fa655304c627a59a.json](graphify-out/cache/ast/v0.9.8/0fc96f785699687c5d8ea014b9cb6de0917d5e377e2d72f4fa655304c627a59a.json) |  | 2026-07-08 | 8KB | `3c7fe195` |
| [graphify-out/cache/ast/v0.9.8/101b2b31666d4f15e61445129d7620e9cfc254778a7d4582369d29f336d00713.json](graphify-out/cache/ast/v0.9.8/101b2b31666d4f15e61445129d7620e9cfc254778a7d4582369d29f336d00713.json) |  | 2026-07-08 | 2KB | `55c9c47e` |
| [graphify-out/cache/ast/v0.9.8/101c7275d9f8cf9881eabdb6f6ae48235419c4310099d2e1cd725f2e0fc87f2f.json](graphify-out/cache/ast/v0.9.8/101c7275d9f8cf9881eabdb6f6ae48235419c4310099d2e1cd725f2e0fc87f2f.json) |  | 2026-07-24 | 8KB | `fa2948d5` |
| [graphify-out/cache/ast/v0.9.8/10b08ddc6ebd5d84db33f97bff540b49d0b63582a255161dc403cb1e01f3a2fe.json](graphify-out/cache/ast/v0.9.8/10b08ddc6ebd5d84db33f97bff540b49d0b63582a255161dc403cb1e01f3a2fe.json) |  | 2026-07-07 | 16KB | `06bcff8e` |
| [graphify-out/cache/ast/v0.9.8/10ebb1371a90f903d08fcd6398060742e2a4c85dbde86690fd9ee4d519c499f9.json](graphify-out/cache/ast/v0.9.8/10ebb1371a90f903d08fcd6398060742e2a4c85dbde86690fd9ee4d519c499f9.json) |  | 2026-07-08 | 3KB | `c5211975` |
| [graphify-out/cache/ast/v0.9.8/112755fc7e00b7cec1b2dc638a360c5b7a453fd3e61ad9a4beccd9aba4977656.json](graphify-out/cache/ast/v0.9.8/112755fc7e00b7cec1b2dc638a360c5b7a453fd3e61ad9a4beccd9aba4977656.json) |  | 2026-07-08 | 32KB | `fbf16019` |
| [graphify-out/cache/ast/v0.9.8/112ece3257c83c1e61f8372c8709a7c5d8b211a624916874f68d0e550e7ce7f3.json](graphify-out/cache/ast/v0.9.8/112ece3257c83c1e61f8372c8709a7c5d8b211a624916874f68d0e550e7ce7f3.json) |  | 2026-07-08 | 39KB | `aed43e02` |
| [graphify-out/cache/ast/v0.9.8/11698e3c74fb27fae13aafc1a3b5c56e1977bf64d271edceac752edab13a50f1.json](graphify-out/cache/ast/v0.9.8/11698e3c74fb27fae13aafc1a3b5c56e1977bf64d271edceac752edab13a50f1.json) |  | 2026-07-07 | 7KB | `fa32e596` |
| [graphify-out/cache/ast/v0.9.8/11a05601eee383b86fcb1a3e4597dc67a36251f96d1992591bef9602b66e12c2.json](graphify-out/cache/ast/v0.9.8/11a05601eee383b86fcb1a3e4597dc67a36251f96d1992591bef9602b66e12c2.json) |  | 2026-07-31 | 10KB | `2aed4341` |
| [graphify-out/cache/ast/v0.9.8/11c6b1fe88721b0422ec768fb9876b570d7f475c92ec4bf7ca5506b1aac0cdc9.json](graphify-out/cache/ast/v0.9.8/11c6b1fe88721b0422ec768fb9876b570d7f475c92ec4bf7ca5506b1aac0cdc9.json) |  | 2026-07-09 | 45KB | `9163989b` |
| [graphify-out/cache/ast/v0.9.8/11ccb1abf86d3867c5440690f44a0b4f96678d5567b9fa5e3bf4c338d0733579.json](graphify-out/cache/ast/v0.9.8/11ccb1abf86d3867c5440690f44a0b4f96678d5567b9fa5e3bf4c338d0733579.json) |  | 2026-07-08 | 5KB | `837fc993` |
| [graphify-out/cache/ast/v0.9.8/1282a0f72cd7013507c6d5f134cd55b9a4d926d62640a7108929b74a6a4b8c35.json](graphify-out/cache/ast/v0.9.8/1282a0f72cd7013507c6d5f134cd55b9a4d926d62640a7108929b74a6a4b8c35.json) |  | 2026-07-08 | 28KB | `d095df9e` |
| [graphify-out/cache/ast/v0.9.8/12b6577b672334a9566046d18e8b3f49f467c9e858c500589b9e61d9c8a7db5d.json](graphify-out/cache/ast/v0.9.8/12b6577b672334a9566046d18e8b3f49f467c9e858c500589b9e61d9c8a7db5d.json) |  | 2026-07-07 | 12KB | `42c2fcbb` |
| [graphify-out/cache/ast/v0.9.8/12c85f2cff226e23ba74b4950685a8885a0f4a25019a73744a10aea0913a31fc.json](graphify-out/cache/ast/v0.9.8/12c85f2cff226e23ba74b4950685a8885a0f4a25019a73744a10aea0913a31fc.json) |  | 2026-07-08 | 36KB | `018c0aac` |
| [graphify-out/cache/ast/v0.9.8/12c9484b2a3478636f0553c3fdeaa45475bf568f6f9fb2b64955c432fe71f3f0.json](graphify-out/cache/ast/v0.9.8/12c9484b2a3478636f0553c3fdeaa45475bf568f6f9fb2b64955c432fe71f3f0.json) |  | 2026-07-08 | 2KB | `199a9333` |
| [graphify-out/cache/ast/v0.9.8/12dafbd036677c09e23197971136b0bbe3afec39dd058b6632d8719b7dd64e7f.json](graphify-out/cache/ast/v0.9.8/12dafbd036677c09e23197971136b0bbe3afec39dd058b6632d8719b7dd64e7f.json) |  | 2026-07-08 | 1KB | `e83e1472` |
| [graphify-out/cache/ast/v0.9.8/12ef59d241695f445692bd254832aca2344a6c4b24697e0d60f2ab9019135a28.json](graphify-out/cache/ast/v0.9.8/12ef59d241695f445692bd254832aca2344a6c4b24697e0d60f2ab9019135a28.json) |  | 2026-07-22 | 8KB | `e1aa4453` |
| [graphify-out/cache/ast/v0.9.8/136dca00217ac832f39b3318b0f51dd3236e2440eb0b5bb04aba58dcc6d5b0b2.json](graphify-out/cache/ast/v0.9.8/136dca00217ac832f39b3318b0f51dd3236e2440eb0b5bb04aba58dcc6d5b0b2.json) |  | 2026-07-08 | 6KB | `c2e67d38` |
| [graphify-out/cache/ast/v0.9.8/13833a8b27dd73ad6c80ed299137effb52b8056b0ab98060964f37d692c43def.json](graphify-out/cache/ast/v0.9.8/13833a8b27dd73ad6c80ed299137effb52b8056b0ab98060964f37d692c43def.json) |  | 2026-07-08 | 9KB | `6219c78d` |
| [graphify-out/cache/ast/v0.9.8/13bca2f4bbcd009f30034ea1a985d0257d413493a854d70dcaf96b2aeea7a314.json](graphify-out/cache/ast/v0.9.8/13bca2f4bbcd009f30034ea1a985d0257d413493a854d70dcaf96b2aeea7a314.json) |  | 2026-07-08 | 21KB | `5355711d` |
| [graphify-out/cache/ast/v0.9.8/13bfae0e86919dd34656dac0c3f8cce8ca172dcb032b05c0991a30a0e9352a21.json](graphify-out/cache/ast/v0.9.8/13bfae0e86919dd34656dac0c3f8cce8ca172dcb032b05c0991a30a0e9352a21.json) |  | 2026-07-08 | 9KB | `3cc647a2` |
| [graphify-out/cache/ast/v0.9.8/13e1638a9be0d85f04472d66f0c636551485037d8b1f7faaf0f982d32d4cc7bd.json](graphify-out/cache/ast/v0.9.8/13e1638a9be0d85f04472d66f0c636551485037d8b1f7faaf0f982d32d4cc7bd.json) |  | 2026-07-20 | 29KB | `47b4993d` |
| [graphify-out/cache/ast/v0.9.8/14036bfdedaeffbd8e81caab79e1ee8331c5eb02522b9a49aeecb1c2471250c8.json](graphify-out/cache/ast/v0.9.8/14036bfdedaeffbd8e81caab79e1ee8331c5eb02522b9a49aeecb1c2471250c8.json) |  | 2026-07-08 | 5KB | `60c530f9` |
| [graphify-out/cache/ast/v0.9.8/147fc9a743b71244a94a2a5acac1a804f462abe8d64f913e8758a57cca8f02be.json](graphify-out/cache/ast/v0.9.8/147fc9a743b71244a94a2a5acac1a804f462abe8d64f913e8758a57cca8f02be.json) |  | 2026-07-08 | 3KB | `e1b3610c` |
| [graphify-out/cache/ast/v0.9.8/149673d0d4dbdc73cfed45cdca7629b999f502d4c40bb7b981164739e81e4058.json](graphify-out/cache/ast/v0.9.8/149673d0d4dbdc73cfed45cdca7629b999f502d4c40bb7b981164739e81e4058.json) |  | 2026-07-07 | 15KB | `fead6b99` |
| [graphify-out/cache/ast/v0.9.8/14995f2129246a29b4d431a97806b5828135da8a87519fdf9d2b4f353b30e859.json](graphify-out/cache/ast/v0.9.8/14995f2129246a29b4d431a97806b5828135da8a87519fdf9d2b4f353b30e859.json) |  | 2026-07-30 | 2KB | `8a05c88d` |
| [graphify-out/cache/ast/v0.9.8/14ce8f4268834ba0d5f11298ca2ecc9545548594bef5c6a0600db1a54f6c18b9.json](graphify-out/cache/ast/v0.9.8/14ce8f4268834ba0d5f11298ca2ecc9545548594bef5c6a0600db1a54f6c18b9.json) |  | 2026-07-29 | 6KB | `9d98a468` |
| [graphify-out/cache/ast/v0.9.8/150f4feb73e1f2dffb37211a058f4b113e975e116e61ef72ff917714fa689fa6.json](graphify-out/cache/ast/v0.9.8/150f4feb73e1f2dffb37211a058f4b113e975e116e61ef72ff917714fa689fa6.json) |  | 2026-07-08 | 12KB | `60475caf` |
| [graphify-out/cache/ast/v0.9.8/1565599dabced929444c3b61fba8a2fe0e5fc880837f7e38ebd1308580d506c1.json](graphify-out/cache/ast/v0.9.8/1565599dabced929444c3b61fba8a2fe0e5fc880837f7e38ebd1308580d506c1.json) |  | 2026-07-08 | 4KB | `77160858` |
| [graphify-out/cache/ast/v0.9.8/15ccb40518ff35743c03959b116931f02bc4dcdaaf29ffbdd66a5e182cbdd0a9.json](graphify-out/cache/ast/v0.9.8/15ccb40518ff35743c03959b116931f02bc4dcdaaf29ffbdd66a5e182cbdd0a9.json) |  | 2026-07-08 | 66KB | `7edd589b` |
| [graphify-out/cache/ast/v0.9.8/15d77ef498cd9dfd4bd847724484c19b679dd593f188085955eb4d3c75a43aa7.json](graphify-out/cache/ast/v0.9.8/15d77ef498cd9dfd4bd847724484c19b679dd593f188085955eb4d3c75a43aa7.json) |  | 2026-07-27 | 29KB | `263e7445` |
| [graphify-out/cache/ast/v0.9.8/15f91e56b675935f82133038a1638aa328c41cdea40c48ad0f470d43835888c5.json](graphify-out/cache/ast/v0.9.8/15f91e56b675935f82133038a1638aa328c41cdea40c48ad0f470d43835888c5.json) |  | 2026-07-31 | 7KB | `48dd2644` |
| [graphify-out/cache/ast/v0.9.8/16060a25505a5ee1158574107c3344640e53fae3643c620ebaaac3ef7e5e1d35.json](graphify-out/cache/ast/v0.9.8/16060a25505a5ee1158574107c3344640e53fae3643c620ebaaac3ef7e5e1d35.json) |  | 2026-07-08 | 3KB | `492923f2` |
| [graphify-out/cache/ast/v0.9.8/1663ee67f769af35949d60821aa97c24830338e85637ae3dc200a902184b99c7.json](graphify-out/cache/ast/v0.9.8/1663ee67f769af35949d60821aa97c24830338e85637ae3dc200a902184b99c7.json) |  | 2026-07-08 | 8KB | `ad85734c` |
| [graphify-out/cache/ast/v0.9.8/169260ee1def59d69fcb6c1e91d2ef70475161eefc65201268bf224469b8165b.json](graphify-out/cache/ast/v0.9.8/169260ee1def59d69fcb6c1e91d2ef70475161eefc65201268bf224469b8165b.json) |  | 2026-07-08 | 35KB | `10d614a8` |
| [graphify-out/cache/ast/v0.9.8/170b436456a8fb81b8ab7474fba9bba083be0114d2c7c4d9f54aadcf6885b25a.json](graphify-out/cache/ast/v0.9.8/170b436456a8fb81b8ab7474fba9bba083be0114d2c7c4d9f54aadcf6885b25a.json) |  | 2026-07-07 | 25KB | `f5cdf3f9` |
| [graphify-out/cache/ast/v0.9.8/17259455c68a4db9086852b7713fb7cdf34e8f539bdb9dc8fd8f2aa274e98ed2.json](graphify-out/cache/ast/v0.9.8/17259455c68a4db9086852b7713fb7cdf34e8f539bdb9dc8fd8f2aa274e98ed2.json) |  | 2026-07-08 | 10KB | `0f5acfb7` |
| [graphify-out/cache/ast/v0.9.8/17677d1f82610813328133c25cca512351f1a47487cd83dd009a5fa1fd56ee2b.json](graphify-out/cache/ast/v0.9.8/17677d1f82610813328133c25cca512351f1a47487cd83dd009a5fa1fd56ee2b.json) |  | 2026-07-07 | 15KB | `d523c2d1` |
| [graphify-out/cache/ast/v0.9.8/179cb0793000f6a9c4972600dee47016813b7a99733e979b1f3d82afe93f70be.json](graphify-out/cache/ast/v0.9.8/179cb0793000f6a9c4972600dee47016813b7a99733e979b1f3d82afe93f70be.json) |  | 2026-07-08 | 8KB | `7debe92b` |
| [graphify-out/cache/ast/v0.9.8/17cb7312f85383cd29c0b0cb3f72a6565afd24486736a20eb02b929c5b05bb00.json](graphify-out/cache/ast/v0.9.8/17cb7312f85383cd29c0b0cb3f72a6565afd24486736a20eb02b929c5b05bb00.json) |  | 2026-07-08 | 10KB | `e6035653` |
| [graphify-out/cache/ast/v0.9.8/17d6cf99cedb222efbffd1a7dae83643871b4fe9279e6f666c3338609bf85106.json](graphify-out/cache/ast/v0.9.8/17d6cf99cedb222efbffd1a7dae83643871b4fe9279e6f666c3338609bf85106.json) |  | 2026-07-29 | 10KB | `45b0ab88` |
| [graphify-out/cache/ast/v0.9.8/183cf88f93f832d476259547a1531323a34b1d4801753865169904e5cc3928af.json](graphify-out/cache/ast/v0.9.8/183cf88f93f832d476259547a1531323a34b1d4801753865169904e5cc3928af.json) |  | 2026-07-08 | 5KB | `3b3f0179` |
| [graphify-out/cache/ast/v0.9.8/18a35e001d6616b4b33776b2f8714f3d5d7e335778857d34d3c944831085c2ac.json](graphify-out/cache/ast/v0.9.8/18a35e001d6616b4b33776b2f8714f3d5d7e335778857d34d3c944831085c2ac.json) |  | 2026-07-22 | 71KB | `433d7dbd` |
| [graphify-out/cache/ast/v0.9.8/18a5d711c8005c185c67716e5e42e4ddaba49d81fe66339af1a626b2b47948c6.json](graphify-out/cache/ast/v0.9.8/18a5d711c8005c185c67716e5e42e4ddaba49d81fe66339af1a626b2b47948c6.json) |  | 2026-07-08 | 6KB | `df7b8448` |
| [graphify-out/cache/ast/v0.9.8/18b6f2166a9db50a757e239721636ef63977730ce84abdb7bd4c2875a7b8d0d9.json](graphify-out/cache/ast/v0.9.8/18b6f2166a9db50a757e239721636ef63977730ce84abdb7bd4c2875a7b8d0d9.json) |  | 2026-07-29 | 56KB | `13269dd2` |
| [graphify-out/cache/ast/v0.9.8/18c18dabb40e92f1eaae66de5ac67dfa170ac2437e98f2dc88eb6ad15d06a837.json](graphify-out/cache/ast/v0.9.8/18c18dabb40e92f1eaae66de5ac67dfa170ac2437e98f2dc88eb6ad15d06a837.json) |  | 2026-07-08 | 12KB | `a390de13` |
| [graphify-out/cache/ast/v0.9.8/18fcb7983c3b8b0bd68f9bb07a7f1ae12a8efd72250a3e9a4185685093de0f4d.json](graphify-out/cache/ast/v0.9.8/18fcb7983c3b8b0bd68f9bb07a7f1ae12a8efd72250a3e9a4185685093de0f4d.json) |  | 2026-07-08 | 8KB | `88912f7f` |
| [graphify-out/cache/ast/v0.9.8/1942e14431f47027fa00479eda4bb4cf1c0bd1263d2d8a8c0da3a645292ab268.json](graphify-out/cache/ast/v0.9.8/1942e14431f47027fa00479eda4bb4cf1c0bd1263d2d8a8c0da3a645292ab268.json) |  | 2026-07-08 | 32KB | `aff167bb` |
| [graphify-out/cache/ast/v0.9.8/194f53c7557967d5acd10d16e846a4c4108e0e78883cb1108bd6c1bf012124d3.json](graphify-out/cache/ast/v0.9.8/194f53c7557967d5acd10d16e846a4c4108e0e78883cb1108bd6c1bf012124d3.json) |  | 2026-07-08 | 17KB | `3e12c1fc` |
| [graphify-out/cache/ast/v0.9.8/1994dd52985fdc653c5842ff85a796ad0418254dc7ceae2f4739a9e54bd7f477.json](graphify-out/cache/ast/v0.9.8/1994dd52985fdc653c5842ff85a796ad0418254dc7ceae2f4739a9e54bd7f477.json) |  | 2026-07-08 | 9KB | `644425ee` |
| [graphify-out/cache/ast/v0.9.8/19c579df9896745445c00d118cb10eb73936855be9ea1848fb31ca97de42437a.json](graphify-out/cache/ast/v0.9.8/19c579df9896745445c00d118cb10eb73936855be9ea1848fb31ca97de42437a.json) |  | 2026-07-07 | 2KB | `1fb65f6a` |
| [graphify-out/cache/ast/v0.9.8/19d182f2056154ce43b0aae7064e8b185a6254161403aaece6c41e6e5441120b.json](graphify-out/cache/ast/v0.9.8/19d182f2056154ce43b0aae7064e8b185a6254161403aaece6c41e6e5441120b.json) |  | 2026-07-30 | 18KB | `9df8f0da` |
| [graphify-out/cache/ast/v0.9.8/1a51f5a52dae45d07927c424c2202cfaa45ca1a96f135b477b3106f610ea7cfb.json](graphify-out/cache/ast/v0.9.8/1a51f5a52dae45d07927c424c2202cfaa45ca1a96f135b477b3106f610ea7cfb.json) |  | 2026-07-07 | 18KB | `6c81206d` |
| [graphify-out/cache/ast/v0.9.8/1a645d7559891c54d4e1aa7828c117db5820743deca69552b56fb35e81f016c5.json](graphify-out/cache/ast/v0.9.8/1a645d7559891c54d4e1aa7828c117db5820743deca69552b56fb35e81f016c5.json) |  | 2026-07-07 | 20KB | `ccd6f28d` |
| [graphify-out/cache/ast/v0.9.8/1ac361ed5c8d8a4a5a373f695088b4c2a1d607ff97221214cc433cd6a9fd051a.json](graphify-out/cache/ast/v0.9.8/1ac361ed5c8d8a4a5a373f695088b4c2a1d607ff97221214cc433cd6a9fd051a.json) |  | 2026-07-07 | 13KB | `25b3ca5a` |
| [graphify-out/cache/ast/v0.9.8/1af8694667bbe0b4d2ceaab087432d82008a2afb56848d39f5af660141bd62cf.json](graphify-out/cache/ast/v0.9.8/1af8694667bbe0b4d2ceaab087432d82008a2afb56848d39f5af660141bd62cf.json) |  | 2026-07-08 | 5KB | `f1e3c2d4` |
| [graphify-out/cache/ast/v0.9.8/1b0fa91aa4af4f0e5a608c01918c42b6a4d1785ab4ceb511cd44a078a5d33799.json](graphify-out/cache/ast/v0.9.8/1b0fa91aa4af4f0e5a608c01918c42b6a4d1785ab4ceb511cd44a078a5d33799.json) |  | 2026-07-08 | 5KB | `70310ae7` |
| [graphify-out/cache/ast/v0.9.8/1b8419e6a1ca1dca54710868658644554cc2c91a8fe43ccac66018fb0813a6ae.json](graphify-out/cache/ast/v0.9.8/1b8419e6a1ca1dca54710868658644554cc2c91a8fe43ccac66018fb0813a6ae.json) |  | 2026-07-08 | 13KB | `b922fd76` |
| [graphify-out/cache/ast/v0.9.8/1bd6d34a1dd3a0e0448707b90d2ebb525f3276f68f436f186b78f6da5d75f6cf.json](graphify-out/cache/ast/v0.9.8/1bd6d34a1dd3a0e0448707b90d2ebb525f3276f68f436f186b78f6da5d75f6cf.json) |  | 2026-07-08 | 11KB | `8c15ed4c` |
| [graphify-out/cache/ast/v0.9.8/1bee58a18a1e2e6b35fd7f97e8aea805c5a075858bba33a79548437ad73dc46f.json](graphify-out/cache/ast/v0.9.8/1bee58a18a1e2e6b35fd7f97e8aea805c5a075858bba33a79548437ad73dc46f.json) |  | 2026-07-07 | 106KB | `da0d33ea` |
| [graphify-out/cache/ast/v0.9.8/1bf48dc5d126c8c4afdd1517ef6df5a64ce9839da04d58ef6dec23c2012031d2.json](graphify-out/cache/ast/v0.9.8/1bf48dc5d126c8c4afdd1517ef6df5a64ce9839da04d58ef6dec23c2012031d2.json) |  | 2026-07-08 | 1KB | `f515b5af` |
| [graphify-out/cache/ast/v0.9.8/1c5746efc17886c3755a70d43521aa67fa0aa0e8d1ab5156d8670447aaa0d758.json](graphify-out/cache/ast/v0.9.8/1c5746efc17886c3755a70d43521aa67fa0aa0e8d1ab5156d8670447aaa0d758.json) |  | 2026-07-20 | 4KB | `a66f27d0` |
| [graphify-out/cache/ast/v0.9.8/1c7f93b9119d2f67b9939a2477da9d4696bcfdb60b7b8e384ed72188466ae0cd.json](graphify-out/cache/ast/v0.9.8/1c7f93b9119d2f67b9939a2477da9d4696bcfdb60b7b8e384ed72188466ae0cd.json) |  | 2026-07-08 | 17KB | `91fcb841` |
| [graphify-out/cache/ast/v0.9.8/1cc9a8e5479fc5d5e3e3fe3697eea2e087ef5393dcdfab89ea9920ebb4b8d731.json](graphify-out/cache/ast/v0.9.8/1cc9a8e5479fc5d5e3e3fe3697eea2e087ef5393dcdfab89ea9920ebb4b8d731.json) |  | 2026-07-08 | 1KB | `3bfd8eb7` |
| [graphify-out/cache/ast/v0.9.8/1cca50e9a90db4b806736bc4c7cad9dddacf963da47692727220bc8f6c77f9ab.json](graphify-out/cache/ast/v0.9.8/1cca50e9a90db4b806736bc4c7cad9dddacf963da47692727220bc8f6c77f9ab.json) |  | 2026-07-08 | 3KB | `1c82c38c` |
| [graphify-out/cache/ast/v0.9.8/1d24c9d2f1801c92ee8fe3eee8fd4e04df7a67dde3fd33b9925d7ae7f22d20eb.json](graphify-out/cache/ast/v0.9.8/1d24c9d2f1801c92ee8fe3eee8fd4e04df7a67dde3fd33b9925d7ae7f22d20eb.json) |  | 2026-07-08 | 57KB | `bbb4b1d5` |
| [graphify-out/cache/ast/v0.9.8/1d3eca185c74c1e64947a64f5c395f8549d1c1fc5f1c6b1739d7ae9ec2ca0f0f.json](graphify-out/cache/ast/v0.9.8/1d3eca185c74c1e64947a64f5c395f8549d1c1fc5f1c6b1739d7ae9ec2ca0f0f.json) |  | 2026-07-08 | 11KB | `e80412d6` |
| [graphify-out/cache/ast/v0.9.8/1d77916871038bf4de69498c67e5a3e4ba087b02be248aae9dd7c01a01a4fff3.json](graphify-out/cache/ast/v0.9.8/1d77916871038bf4de69498c67e5a3e4ba087b02be248aae9dd7c01a01a4fff3.json) |  | 2026-07-30 | 3KB | `362c4a5e` |
| [graphify-out/cache/ast/v0.9.8/1d99bebf53d09c1e354721aafc4fb4aed8f2b7c093e758ce16d938e9ee97fc3e.json](graphify-out/cache/ast/v0.9.8/1d99bebf53d09c1e354721aafc4fb4aed8f2b7c093e758ce16d938e9ee97fc3e.json) |  | 2026-07-07 | 96KB | `8f3e17f5` |
| [graphify-out/cache/ast/v0.9.8/1da4bd9c7401d1566806eb498102fcad1a1594b8e32600c165a765d4326ed26e.json](graphify-out/cache/ast/v0.9.8/1da4bd9c7401d1566806eb498102fcad1a1594b8e32600c165a765d4326ed26e.json) |  | 2026-07-22 | 5KB | `685ad9fe` |
| [graphify-out/cache/ast/v0.9.8/1db1929a569dd1877efc4e1d69be932d74095dcb0b92ec1c2706d0e0db61f162.json](graphify-out/cache/ast/v0.9.8/1db1929a569dd1877efc4e1d69be932d74095dcb0b92ec1c2706d0e0db61f162.json) |  | 2026-07-07 | 20KB | `5b0ad1ac` |
| [graphify-out/cache/ast/v0.9.8/1db55dd26132709329f194434f46cc614fadfbfbcbca1e8f6a66694e6bec5479.json](graphify-out/cache/ast/v0.9.8/1db55dd26132709329f194434f46cc614fadfbfbcbca1e8f6a66694e6bec5479.json) |  | 2026-07-08 | 7KB | `8b50de65` |
| [graphify-out/cache/ast/v0.9.8/1dd8ece4982e5f098ec3843d41c8d602b375c62da68008e14cd6858111ff1400.json](graphify-out/cache/ast/v0.9.8/1dd8ece4982e5f098ec3843d41c8d602b375c62da68008e14cd6858111ff1400.json) |  | 2026-07-08 | 9KB | `0955568d` |
| [graphify-out/cache/ast/v0.9.8/1de6c1414e23e9a11b9ec7fe2049c3a8f9279fc861ce52b70deed02eca944b8c.json](graphify-out/cache/ast/v0.9.8/1de6c1414e23e9a11b9ec7fe2049c3a8f9279fc861ce52b70deed02eca944b8c.json) |  | 2026-07-27 | 9KB | `e57ab185` |
| [graphify-out/cache/ast/v0.9.8/1df23a0ea31b03763361b07143b9f744f7c36af07b24091402fa35046e955eff.json](graphify-out/cache/ast/v0.9.8/1df23a0ea31b03763361b07143b9f744f7c36af07b24091402fa35046e955eff.json) |  | 2026-07-30 | 3KB | `fb62d941` |
| [graphify-out/cache/ast/v0.9.8/1e0b3258f0a89600fca06e1d6078070f358e772c50573a2deedd825490d0821e.json](graphify-out/cache/ast/v0.9.8/1e0b3258f0a89600fca06e1d6078070f358e772c50573a2deedd825490d0821e.json) |  | 2026-07-08 | 9KB | `758331b5` |
| [graphify-out/cache/ast/v0.9.8/1e2dd51d27ee54a8fdc0d848c3d796e75bc48e8e92a1660d1fea49149735314b.json](graphify-out/cache/ast/v0.9.8/1e2dd51d27ee54a8fdc0d848c3d796e75bc48e8e92a1660d1fea49149735314b.json) |  | 2026-07-07 | 60KB | `bb7d538a` |
| [graphify-out/cache/ast/v0.9.8/1e5d68e3c6d73c7b1826d5fe1f226c2abe596dc01d10d8216fc88bdc33a2e533.json](graphify-out/cache/ast/v0.9.8/1e5d68e3c6d73c7b1826d5fe1f226c2abe596dc01d10d8216fc88bdc33a2e533.json) |  | 2026-07-10 | 81KB | `90eeef31` |
| [graphify-out/cache/ast/v0.9.8/1e6fa49c605fd9d17177699114e67c7b56295bf25aeab50974419c9d58452752.json](graphify-out/cache/ast/v0.9.8/1e6fa49c605fd9d17177699114e67c7b56295bf25aeab50974419c9d58452752.json) |  | 2026-07-07 | 247B | `30045dcd` |
| [graphify-out/cache/ast/v0.9.8/1ea35563df40762f4a419779c108e3155c885e1f15f36c3829605b089d6cf621.json](graphify-out/cache/ast/v0.9.8/1ea35563df40762f4a419779c108e3155c885e1f15f36c3829605b089d6cf621.json) |  | 2026-07-08 | 18KB | `6d0fddcc` |
| [graphify-out/cache/ast/v0.9.8/1ec5b53468971e1865223d25b1ec8dbb995d83ca8d329f65d9a4867e87b8d552.json](graphify-out/cache/ast/v0.9.8/1ec5b53468971e1865223d25b1ec8dbb995d83ca8d329f65d9a4867e87b8d552.json) |  | 2026-07-08 | 130KB | `72ed3e5e` |
| [graphify-out/cache/ast/v0.9.8/1eccdb053280515c972fb971792008e1222486a19f2a90c70f6d8c9c1e21e963.json](graphify-out/cache/ast/v0.9.8/1eccdb053280515c972fb971792008e1222486a19f2a90c70f6d8c9c1e21e963.json) |  | 2026-07-24 | 122KB | `7307fceb` |
| [graphify-out/cache/ast/v0.9.8/1eceb5939e89ab6ced456859c4de3fc79e4d7afe84ce59fc923fd24fd9166323.json](graphify-out/cache/ast/v0.9.8/1eceb5939e89ab6ced456859c4de3fc79e4d7afe84ce59fc923fd24fd9166323.json) |  | 2026-07-08 | 52KB | `856a8a96` |
| [graphify-out/cache/ast/v0.9.8/1eeebdffbc97909aa58826a3329d2e580aca0461ea7c83a6332ecdaac04ba6d5.json](graphify-out/cache/ast/v0.9.8/1eeebdffbc97909aa58826a3329d2e580aca0461ea7c83a6332ecdaac04ba6d5.json) |  | 2026-07-30 | 9KB | `981be656` |
| [graphify-out/cache/ast/v0.9.8/1ef8f14e120488c1347eaa4e149f4d1e28003c381c088799a217d8804a091638.json](graphify-out/cache/ast/v0.9.8/1ef8f14e120488c1347eaa4e149f4d1e28003c381c088799a217d8804a091638.json) |  | 2026-07-08 | 8KB | `f2fd0367` |
| [graphify-out/cache/ast/v0.9.8/1f28fa0ac130ff4adf3707180b327597ebfe044b0424cf7c9bfcabf1f748be3a.json](graphify-out/cache/ast/v0.9.8/1f28fa0ac130ff4adf3707180b327597ebfe044b0424cf7c9bfcabf1f748be3a.json) |  | 2026-07-08 | 23KB | `b550f1c4` |
| [graphify-out/cache/ast/v0.9.8/1f2ac8b82ec1d5d1ccdcac6e735ec480d9da22255ef68ab30c1ee297b0b6ad62.json](graphify-out/cache/ast/v0.9.8/1f2ac8b82ec1d5d1ccdcac6e735ec480d9da22255ef68ab30c1ee297b0b6ad62.json) |  | 2026-07-08 | 24KB | `327c9c74` |
| [graphify-out/cache/ast/v0.9.8/1f38972804d6512fd010fb0915571d1b01cb4ff3e604acbbe6659a05c808f4e1.json](graphify-out/cache/ast/v0.9.8/1f38972804d6512fd010fb0915571d1b01cb4ff3e604acbbe6659a05c808f4e1.json) |  | 2026-07-08 | 8KB | `e6eac052` |
| [graphify-out/cache/ast/v0.9.8/1f6b8200c02d37b5e72e20ecf52f676896c3e79aab3ffe93d244108a2896d8cc.json](graphify-out/cache/ast/v0.9.8/1f6b8200c02d37b5e72e20ecf52f676896c3e79aab3ffe93d244108a2896d8cc.json) |  | 2026-07-08 | 23KB | `c4d22921` |
| [graphify-out/cache/ast/v0.9.8/1f72e21d5dd8f04ae68951c48836880adbd850f3db16924f44f64f2f7b33d829.json](graphify-out/cache/ast/v0.9.8/1f72e21d5dd8f04ae68951c48836880adbd850f3db16924f44f64f2f7b33d829.json) |  | 2026-07-08 | 26KB | `698a0999` |
| [graphify-out/cache/ast/v0.9.8/1f89bf2a00d5b6b8f22e16d0c59cabc95358c8a8039ae89bc8989ff7039a3f5e.json](graphify-out/cache/ast/v0.9.8/1f89bf2a00d5b6b8f22e16d0c59cabc95358c8a8039ae89bc8989ff7039a3f5e.json) |  | 2026-07-08 | 110KB | `8588a127` |
| [graphify-out/cache/ast/v0.9.8/1f94e8bceefaad39dd4e47fcd12293144b5c812ece98d491679b32284340931d.json](graphify-out/cache/ast/v0.9.8/1f94e8bceefaad39dd4e47fcd12293144b5c812ece98d491679b32284340931d.json) |  | 2026-07-08 | 3KB | `2fd7182b` |
| [graphify-out/cache/ast/v0.9.8/1fb1b2aae6f1fbd1f007960c4466f90712d052c4384b1b8bdb0c0753315405f1.json](graphify-out/cache/ast/v0.9.8/1fb1b2aae6f1fbd1f007960c4466f90712d052c4384b1b8bdb0c0753315405f1.json) |  | 2026-07-07 | 4KB | `08ae6036` |
| [graphify-out/cache/ast/v0.9.8/202466cc90cbf443c99b8b444007df1f9e465eff0af03aad9f5fb37f65c3d7fe.json](graphify-out/cache/ast/v0.9.8/202466cc90cbf443c99b8b444007df1f9e465eff0af03aad9f5fb37f65c3d7fe.json) |  | 2026-07-30 | 9KB | `a4d37e0e` |
| [graphify-out/cache/ast/v0.9.8/202e7af32edbc7d3eb8cbe8cbabe66741133bce83f015a4719f74532e465441b.json](graphify-out/cache/ast/v0.9.8/202e7af32edbc7d3eb8cbe8cbabe66741133bce83f015a4719f74532e465441b.json) |  | 2026-07-22 | 3KB | `88a05787` |
| [graphify-out/cache/ast/v0.9.8/206ae554d15a6419e11c315fb31d45255e636d9117b6d961dc0effcc684b102a.json](graphify-out/cache/ast/v0.9.8/206ae554d15a6419e11c315fb31d45255e636d9117b6d961dc0effcc684b102a.json) |  | 2026-07-08 | 50KB | `0e94ea79` |
| [graphify-out/cache/ast/v0.9.8/206b61001df8bbd0cf9329348da7d175a35634a7e43ffd6d947e9fd4077529ea.json](graphify-out/cache/ast/v0.9.8/206b61001df8bbd0cf9329348da7d175a35634a7e43ffd6d947e9fd4077529ea.json) |  | 2026-07-08 | 10KB | `233f6730` |
| [graphify-out/cache/ast/v0.9.8/209a3f3d9d6d0d7be1fa4b672b747e99138ab8cd642a3f6970fc0ac26253e182.json](graphify-out/cache/ast/v0.9.8/209a3f3d9d6d0d7be1fa4b672b747e99138ab8cd642a3f6970fc0ac26253e182.json) |  | 2026-07-23 | 8KB | `b3ce71b1` |
| [graphify-out/cache/ast/v0.9.8/20a29c493bb839c29bf9ac2b161405eff34d84125b39fcf3f20531b3f832f494.json](graphify-out/cache/ast/v0.9.8/20a29c493bb839c29bf9ac2b161405eff34d84125b39fcf3f20531b3f832f494.json) |  | 2026-07-08 | 11KB | `722ee61a` |
| [graphify-out/cache/ast/v0.9.8/20ab9aeb9f9099fb04a67518ad13c1082667ea33d7cbbc672bac64a4b8aca406.json](graphify-out/cache/ast/v0.9.8/20ab9aeb9f9099fb04a67518ad13c1082667ea33d7cbbc672bac64a4b8aca406.json) |  | 2026-07-07 | 80KB | `89897a72` |
| [graphify-out/cache/ast/v0.9.8/20c7321b4c865e9a4a6ec65bf6cfcd07d0188ccc30492689e8873a74ec590ad5.json](graphify-out/cache/ast/v0.9.8/20c7321b4c865e9a4a6ec65bf6cfcd07d0188ccc30492689e8873a74ec590ad5.json) |  | 2026-07-08 | 8KB | `5a4ea15e` |
| [graphify-out/cache/ast/v0.9.8/216c1d511248b35211d21f2da0296f1c60d7ac5ad87dd7a13d5c47e362c7cb1f.json](graphify-out/cache/ast/v0.9.8/216c1d511248b35211d21f2da0296f1c60d7ac5ad87dd7a13d5c47e362c7cb1f.json) |  | 2026-07-08 | 23KB | `b7ae8425` |
| [graphify-out/cache/ast/v0.9.8/2191f4a09e733d35bdc87b8ee4220d5f85b0ded1dee03d289c9026ea1704c1a0.json](graphify-out/cache/ast/v0.9.8/2191f4a09e733d35bdc87b8ee4220d5f85b0ded1dee03d289c9026ea1704c1a0.json) |  | 2026-07-08 | 113KB | `4b33e2f9` |
| [graphify-out/cache/ast/v0.9.8/2192b0116905240c6f3b7ff8155bd060f67a83dc983eafaaa1b56c7ade1cbecb.json](graphify-out/cache/ast/v0.9.8/2192b0116905240c6f3b7ff8155bd060f67a83dc983eafaaa1b56c7ade1cbecb.json) |  | 2026-07-07 | 3KB | `e57a14e8` |
| [graphify-out/cache/ast/v0.9.8/22041781269c8e6b8e27785c41d49a9500a7f22a11060f3582aecaa821d652b9.json](graphify-out/cache/ast/v0.9.8/22041781269c8e6b8e27785c41d49a9500a7f22a11060f3582aecaa821d652b9.json) |  | 2026-07-08 | 12KB | `07e88f70` |
| [graphify-out/cache/ast/v0.9.8/22570e30ef650480a9c80b8f854895e863acb2633c519a60375d7a8dbb80a7f6.json](graphify-out/cache/ast/v0.9.8/22570e30ef650480a9c80b8f854895e863acb2633c519a60375d7a8dbb80a7f6.json) |  | 2026-07-08 | 11KB | `4ded2b69` |
| [graphify-out/cache/ast/v0.9.8/22596144b8e1e6cffb6cea282c44680dee83f89c083abea400e3797933db97e8.json](graphify-out/cache/ast/v0.9.8/22596144b8e1e6cffb6cea282c44680dee83f89c083abea400e3797933db97e8.json) |  | 2026-07-08 | 2KB | `dd13e7a1` |
| [graphify-out/cache/ast/v0.9.8/2267ec62f3180821371c24509280f0589400d2baa41e910cc07b289673d211e1.json](graphify-out/cache/ast/v0.9.8/2267ec62f3180821371c24509280f0589400d2baa41e910cc07b289673d211e1.json) |  | 2026-07-08 | 77KB | `e429c8f8` |
| [graphify-out/cache/ast/v0.9.8/227297cdcaf877b5ed4ca60662ddd08ae690542fee98a2b2806e83b598731d79.json](graphify-out/cache/ast/v0.9.8/227297cdcaf877b5ed4ca60662ddd08ae690542fee98a2b2806e83b598731d79.json) |  | 2026-07-08 | 8KB | `87ec34b2` |
| [graphify-out/cache/ast/v0.9.8/229d367411f055f7520ccefc40026bcde5b387ae74fe5645e2c6771eb23aeaba.json](graphify-out/cache/ast/v0.9.8/229d367411f055f7520ccefc40026bcde5b387ae74fe5645e2c6771eb23aeaba.json) |  | 2026-07-08 | 2KB | `2fafa613` |
| [graphify-out/cache/ast/v0.9.8/22c8e88c4b579fc248d57254c7ccc51a3cabf2f39a0f5078a2ffed78ceb58b21.json](graphify-out/cache/ast/v0.9.8/22c8e88c4b579fc248d57254c7ccc51a3cabf2f39a0f5078a2ffed78ceb58b21.json) |  | 2026-07-08 | 9KB | `790ed25c` |
| [graphify-out/cache/ast/v0.9.8/23618a4b0c55aa79bb608c51f91ca61eded1293cb1ec3f3923f0cc84ffd6dc15.json](graphify-out/cache/ast/v0.9.8/23618a4b0c55aa79bb608c51f91ca61eded1293cb1ec3f3923f0cc84ffd6dc15.json) |  | 2026-07-08 | 101KB | `b42f4afe` |
| [graphify-out/cache/ast/v0.9.8/23640e7c1a703000ffb1839f02365b6600ed9a07805bce84addd4a65cf7b6515.json](graphify-out/cache/ast/v0.9.8/23640e7c1a703000ffb1839f02365b6600ed9a07805bce84addd4a65cf7b6515.json) |  | 2026-07-08 | 26KB | `6ab53ca5` |
| [graphify-out/cache/ast/v0.9.8/238a6fba1d40791c00fdd0685a139072880427cd1d6f4f04818a3f5b730e532e.json](graphify-out/cache/ast/v0.9.8/238a6fba1d40791c00fdd0685a139072880427cd1d6f4f04818a3f5b730e532e.json) |  | 2026-07-22 | 23KB | `33eb1281` |
| [graphify-out/cache/ast/v0.9.8/238fab9bc9109f3583b1a92da45bad163ab0614e4c376e8e1acc75ae4e771ad1.json](graphify-out/cache/ast/v0.9.8/238fab9bc9109f3583b1a92da45bad163ab0614e4c376e8e1acc75ae4e771ad1.json) |  | 2026-07-08 | 20KB | `5168b20b` |
| [graphify-out/cache/ast/v0.9.8/23c1c45a6e98dcdb9707c932b0d53f5034c7fcb890e94868311fdf54c015d2e8.json](graphify-out/cache/ast/v0.9.8/23c1c45a6e98dcdb9707c932b0d53f5034c7fcb890e94868311fdf54c015d2e8.json) |  | 2026-07-08 | 103KB | `04c020eb` |
| [graphify-out/cache/ast/v0.9.8/23d990e3c8c069b4f1517312328cf588946496281bb80f200a12add07ac25020.json](graphify-out/cache/ast/v0.9.8/23d990e3c8c069b4f1517312328cf588946496281bb80f200a12add07ac25020.json) |  | 2026-07-24 | 4KB | `a28246bb` |
| [graphify-out/cache/ast/v0.9.8/24076ca7486e57aa02028e962df157d4346d2aa6618ba57cf89ce3c77643be88.json](graphify-out/cache/ast/v0.9.8/24076ca7486e57aa02028e962df157d4346d2aa6618ba57cf89ce3c77643be88.json) |  | 2026-07-29 | 13KB | `15315a4c` |
| [graphify-out/cache/ast/v0.9.8/2408a6890d8b1d33dc02e028c1271bab165d447aa9c634c2bf77815282c4fdec.json](graphify-out/cache/ast/v0.9.8/2408a6890d8b1d33dc02e028c1271bab165d447aa9c634c2bf77815282c4fdec.json) |  | 2026-07-08 | 8KB | `619daa67` |
| [graphify-out/cache/ast/v0.9.8/2461162e1830049470c22808cf0afadef672ab26eb0306fdaa7a916bce9e2813.json](graphify-out/cache/ast/v0.9.8/2461162e1830049470c22808cf0afadef672ab26eb0306fdaa7a916bce9e2813.json) |  | 2026-07-07 | 2KB | `58ca5dae` |
| [graphify-out/cache/ast/v0.9.8/24729f53f18e5f9f287344c0be45e3af6b757c20da0ca75da57b957f7ccd0ab5.json](graphify-out/cache/ast/v0.9.8/24729f53f18e5f9f287344c0be45e3af6b757c20da0ca75da57b957f7ccd0ab5.json) |  | 2026-07-23 | 4KB | `746b184c` |
| [graphify-out/cache/ast/v0.9.8/24a0d508a77219d34d2f52afff922dfdc497063350dae50b6ea747fd87ab8db6.json](graphify-out/cache/ast/v0.9.8/24a0d508a77219d34d2f52afff922dfdc497063350dae50b6ea747fd87ab8db6.json) |  | 2026-07-08 | 8KB | `15f1cf15` |
| [graphify-out/cache/ast/v0.9.8/2505910c1e5bd1a917abed389c8bf07a1bb6dac5cad5aeed8584132986655412.json](graphify-out/cache/ast/v0.9.8/2505910c1e5bd1a917abed389c8bf07a1bb6dac5cad5aeed8584132986655412.json) |  | 2026-07-08 | 48KB | `04d05965` |
| [graphify-out/cache/ast/v0.9.8/2576dbbb2fb3a28fa1f9b280d43208b34ff23aeb492e62e86edc63862dae063a.json](graphify-out/cache/ast/v0.9.8/2576dbbb2fb3a28fa1f9b280d43208b34ff23aeb492e62e86edc63862dae063a.json) |  | 2026-07-08 | 1KB | `8552ac19` |
| [graphify-out/cache/ast/v0.9.8/2632f6c964ebbcad3cbde6c9ad93a8f430c4ec2dbcadb0526a75c42e2829947f.json](graphify-out/cache/ast/v0.9.8/2632f6c964ebbcad3cbde6c9ad93a8f430c4ec2dbcadb0526a75c42e2829947f.json) |  | 2026-07-08 | 13KB | `d019e917` |
| [graphify-out/cache/ast/v0.9.8/263c8c954fcbf559882e25bdbda20acc5f7ddaa94f920146217d9d209cde76a6.json](graphify-out/cache/ast/v0.9.8/263c8c954fcbf559882e25bdbda20acc5f7ddaa94f920146217d9d209cde76a6.json) |  | 2026-08-01 | 65KB | `b35150d4` |
| [graphify-out/cache/ast/v0.9.8/263da5ed77c29de5e846a42c4c1bcad5f5307c4f6080dbf3ea6736eb9a5404f1.json](graphify-out/cache/ast/v0.9.8/263da5ed77c29de5e846a42c4c1bcad5f5307c4f6080dbf3ea6736eb9a5404f1.json) |  | 2026-07-08 | 18KB | `61f5cd80` |
| [graphify-out/cache/ast/v0.9.8/26aa7932bd82ab0653c229492e74602c2b29af9a1619a9c14b423e6cf7672a92.json](graphify-out/cache/ast/v0.9.8/26aa7932bd82ab0653c229492e74602c2b29af9a1619a9c14b423e6cf7672a92.json) |  | 2026-07-07 | 825B | `7b1f3d48` |
| [graphify-out/cache/ast/v0.9.8/26dc3db48b80e52e0eba1f9ba0092c3b1e88067366e8acc331d5983ba7d2bb5d.json](graphify-out/cache/ast/v0.9.8/26dc3db48b80e52e0eba1f9ba0092c3b1e88067366e8acc331d5983ba7d2bb5d.json) |  | 2026-07-08 | 11KB | `05b83d00` |
| [graphify-out/cache/ast/v0.9.8/26ef7da4f36497d3573173ddad88ea281170c99ef39fadebceb00397dcbc2b8c.json](graphify-out/cache/ast/v0.9.8/26ef7da4f36497d3573173ddad88ea281170c99ef39fadebceb00397dcbc2b8c.json) |  | 2026-07-08 | 63KB | `0acb9ec0` |
| [graphify-out/cache/ast/v0.9.8/26fcb5a15a88635adadb063f9864c72565b9b645c5cac837337bc30e0530a5ea.json](graphify-out/cache/ast/v0.9.8/26fcb5a15a88635adadb063f9864c72565b9b645c5cac837337bc30e0530a5ea.json) |  | 2026-07-08 | 12KB | `8325aede` |
| [graphify-out/cache/ast/v0.9.8/2723d53508f4d49d209907e8cd0aaa4f2840a583ac0e43aabc68a5cdc0667449.json](graphify-out/cache/ast/v0.9.8/2723d53508f4d49d209907e8cd0aaa4f2840a583ac0e43aabc68a5cdc0667449.json) |  | 2026-07-08 | 11KB | `b5110052` |
| [graphify-out/cache/ast/v0.9.8/2740b0245bdc2afb049a64db74f10fe99caeb54bca68285d1c1d6932c787f6e0.json](graphify-out/cache/ast/v0.9.8/2740b0245bdc2afb049a64db74f10fe99caeb54bca68285d1c1d6932c787f6e0.json) |  | 2026-07-24 | 2KB | `2bf8bb9a` |
| [graphify-out/cache/ast/v0.9.8/2747cec76d8d09d09f8f0a79afa061b42cb9d65445718d582b69e01e3a224ff8.json](graphify-out/cache/ast/v0.9.8/2747cec76d8d09d09f8f0a79afa061b42cb9d65445718d582b69e01e3a224ff8.json) |  | 2026-07-08 | 10KB | `f054cfca` |
| [graphify-out/cache/ast/v0.9.8/279bc4679e5b1d65d77fbd4475d75aa761bcd06a9942b12935c04ae5ac576d60.json](graphify-out/cache/ast/v0.9.8/279bc4679e5b1d65d77fbd4475d75aa761bcd06a9942b12935c04ae5ac576d60.json) |  | 2026-07-29 | 9KB | `ce95555f` |
| [graphify-out/cache/ast/v0.9.8/27c54167b13ea8e08c48eb78a5eac77057930d74590b0bb10217768d4d0af2bd.json](graphify-out/cache/ast/v0.9.8/27c54167b13ea8e08c48eb78a5eac77057930d74590b0bb10217768d4d0af2bd.json) |  | 2026-07-08 | 11KB | `0dd05ae9` |
| [graphify-out/cache/ast/v0.9.8/2807b41337fbdf586ab9cb1d418c0edfa2b0f26fb1835885f42c848b9b5a40a6.json](graphify-out/cache/ast/v0.9.8/2807b41337fbdf586ab9cb1d418c0edfa2b0f26fb1835885f42c848b9b5a40a6.json) |  | 2026-07-08 | 12KB | `baab40a1` |
| [graphify-out/cache/ast/v0.9.8/2845fbccb5a8aaacd5d86a9cf765a1611ebf7e21bb07426a86dccf6bfed0f902.json](graphify-out/cache/ast/v0.9.8/2845fbccb5a8aaacd5d86a9cf765a1611ebf7e21bb07426a86dccf6bfed0f902.json) |  | 2026-07-08 | 126KB | `624ec21b` |
| [graphify-out/cache/ast/v0.9.8/2849c1a3c53d7c70f79fe9522aece4f9d673e0b942a33673e567bcf0ee44cdd8.json](graphify-out/cache/ast/v0.9.8/2849c1a3c53d7c70f79fe9522aece4f9d673e0b942a33673e567bcf0ee44cdd8.json) |  | 2026-07-08 | 10KB | `db44c0f6` |
| [graphify-out/cache/ast/v0.9.8/294899c715493f8d1c1d22ee60cf529eade1d02e285d0f6da5dd226a0135f17d.json](graphify-out/cache/ast/v0.9.8/294899c715493f8d1c1d22ee60cf529eade1d02e285d0f6da5dd226a0135f17d.json) |  | 2026-07-08 | 27KB | `45f98288` |
| [graphify-out/cache/ast/v0.9.8/295391dfb904b7853f81c600337ca0afabf208b5c7575ccd44d0690fa82847f9.json](graphify-out/cache/ast/v0.9.8/295391dfb904b7853f81c600337ca0afabf208b5c7575ccd44d0690fa82847f9.json) |  | 2026-07-07 | 15KB | `06c93767` |
| [graphify-out/cache/ast/v0.9.8/297368ecce188c0c124a3b46725710835dfa55fc67884dc6874f34e3086f40fa.json](graphify-out/cache/ast/v0.9.8/297368ecce188c0c124a3b46725710835dfa55fc67884dc6874f34e3086f40fa.json) |  | 2026-07-08 | 8KB | `b779cf83` |
| [graphify-out/cache/ast/v0.9.8/298c94d487c4385fa47e43af4a5f1165823f4ab5b9729111fff94f7662eb37a5.json](graphify-out/cache/ast/v0.9.8/298c94d487c4385fa47e43af4a5f1165823f4ab5b9729111fff94f7662eb37a5.json) |  | 2026-07-29 | 7KB | `257fd11b` |
| [graphify-out/cache/ast/v0.9.8/2990ff3864a646d07f0b2ae2dced76e080d01c07c213f29ea1b754f592d201d1.json](graphify-out/cache/ast/v0.9.8/2990ff3864a646d07f0b2ae2dced76e080d01c07c213f29ea1b754f592d201d1.json) |  | 2026-07-08 | 37KB | `55ce8b30` |
| [graphify-out/cache/ast/v0.9.8/29df3abf0c83a25ffe58a83001ca40decc9790770c4b23bc7e7d35b7fc2c2b0a.json](graphify-out/cache/ast/v0.9.8/29df3abf0c83a25ffe58a83001ca40decc9790770c4b23bc7e7d35b7fc2c2b0a.json) |  | 2026-07-08 | 6KB | `4571ef1a` |
| [graphify-out/cache/ast/v0.9.8/2a0d3aa5fa0cb8673d19ea217320f360e01be567b0b908ceed61af7834afdb68.json](graphify-out/cache/ast/v0.9.8/2a0d3aa5fa0cb8673d19ea217320f360e01be567b0b908ceed61af7834afdb68.json) |  | 2026-07-08 | 19KB | `aba91fdc` |
| [graphify-out/cache/ast/v0.9.8/2a279a3e4fe97d92fc75d2d9a0da2192dd5cbcf93926edab9a25166a9ac0c394.json](graphify-out/cache/ast/v0.9.8/2a279a3e4fe97d92fc75d2d9a0da2192dd5cbcf93926edab9a25166a9ac0c394.json) |  | 2026-07-24 | 4KB | `c107fc73` |
| [graphify-out/cache/ast/v0.9.8/2a346c4d35ef0e73c7c3f480c8be71f7bfed11a76c3c57ea10b193d8f33fb48d.json](graphify-out/cache/ast/v0.9.8/2a346c4d35ef0e73c7c3f480c8be71f7bfed11a76c3c57ea10b193d8f33fb48d.json) |  | 2026-07-08 | 34KB | `e80920de` |
| [graphify-out/cache/ast/v0.9.8/2a4e918eed719ca273ee48052f9a6830b033e2366884edbf6c0a775725730b33.json](graphify-out/cache/ast/v0.9.8/2a4e918eed719ca273ee48052f9a6830b033e2366884edbf6c0a775725730b33.json) |  | 2026-07-08 | 7KB | `569b3c96` |
| [graphify-out/cache/ast/v0.9.8/2a53c631f29e0293f354fdfd5aa5ee0a37514ac4cea22db73b2ed660ae15d53b.json](graphify-out/cache/ast/v0.9.8/2a53c631f29e0293f354fdfd5aa5ee0a37514ac4cea22db73b2ed660ae15d53b.json) |  | 2026-07-08 | 33KB | `342fcb14` |
| [graphify-out/cache/ast/v0.9.8/2afcb96eb918eea8bfb933e8cbd089e496f5ea262dddaa4558260c0b180656fe.json](graphify-out/cache/ast/v0.9.8/2afcb96eb918eea8bfb933e8cbd089e496f5ea262dddaa4558260c0b180656fe.json) |  | 2026-07-08 | 3KB | `05f0abbf` |
| [graphify-out/cache/ast/v0.9.8/2b06165723304675fd3d481d645621fced47ce81059ea242b99ac81a5b2062e3.json](graphify-out/cache/ast/v0.9.8/2b06165723304675fd3d481d645621fced47ce81059ea242b99ac81a5b2062e3.json) |  | 2026-07-29 | 5KB | `3b03e6c2` |
| [graphify-out/cache/ast/v0.9.8/2b45422a8e21c77a5c8c61864d0e449018b977f5c92c830a18264fd7f49d55ab.json](graphify-out/cache/ast/v0.9.8/2b45422a8e21c77a5c8c61864d0e449018b977f5c92c830a18264fd7f49d55ab.json) |  | 2026-07-08 | 10KB | `2bc43a1b` |
| [graphify-out/cache/ast/v0.9.8/2b46759d55dac1f9d2dd1c306ee3c1d298a6130d3c94a87ce1ad6a95b2c7c9d8.json](graphify-out/cache/ast/v0.9.8/2b46759d55dac1f9d2dd1c306ee3c1d298a6130d3c94a87ce1ad6a95b2c7c9d8.json) |  | 2026-07-08 | 15KB | `9d66e046` |
| [graphify-out/cache/ast/v0.9.8/2b95e76d7db4a7d1c6e9cbbb25c3db2512851ef7e997038d68eea86a7e6060c5.json](graphify-out/cache/ast/v0.9.8/2b95e76d7db4a7d1c6e9cbbb25c3db2512851ef7e997038d68eea86a7e6060c5.json) |  | 2026-07-08 | 51KB | `b2e17b2e` |
| [graphify-out/cache/ast/v0.9.8/2c5f02d50013d90b6415ca95a4a4e4bc293df211ec70f1510d6c4a4f58686479.json](graphify-out/cache/ast/v0.9.8/2c5f02d50013d90b6415ca95a4a4e4bc293df211ec70f1510d6c4a4f58686479.json) |  | 2026-07-08 | 43KB | `6d22232a` |
| [graphify-out/cache/ast/v0.9.8/2c6f178c8effb87b77c07bb7325766da82993284b4ed860795437d8ab4f3fe15.json](graphify-out/cache/ast/v0.9.8/2c6f178c8effb87b77c07bb7325766da82993284b4ed860795437d8ab4f3fe15.json) |  | 2026-07-31 | 7KB | `48dd2644` |
| [graphify-out/cache/ast/v0.9.8/2cb57d10e366526865d22e949897164bf22f7cc67988466bc5d9f15a7a136cb1.json](graphify-out/cache/ast/v0.9.8/2cb57d10e366526865d22e949897164bf22f7cc67988466bc5d9f15a7a136cb1.json) |  | 2026-07-08 | 15KB | `d7ec7a77` |
| [graphify-out/cache/ast/v0.9.8/2cbccae9e25a1ee76c5a1af041bfc624a387ae3ab8a851e17928c07844a70061.json](graphify-out/cache/ast/v0.9.8/2cbccae9e25a1ee76c5a1af041bfc624a387ae3ab8a851e17928c07844a70061.json) |  | 2026-07-08 | 4KB | `69e1cd6b` |
| [graphify-out/cache/ast/v0.9.8/2d188a71baf735f090345a5cfc55d8e6111035cfbf4568a98f683f7870495f5f.json](graphify-out/cache/ast/v0.9.8/2d188a71baf735f090345a5cfc55d8e6111035cfbf4568a98f683f7870495f5f.json) |  | 2026-07-08 | 12KB | `3dfe8178` |
| [graphify-out/cache/ast/v0.9.8/2dd48161a9dabf11dab3a213806a29365c036288068407e5174c91fb390759d3.json](graphify-out/cache/ast/v0.9.8/2dd48161a9dabf11dab3a213806a29365c036288068407e5174c91fb390759d3.json) |  | 2026-07-10 | 10KB | `8cff7953` |
| [graphify-out/cache/ast/v0.9.8/2dd899dfb853fe8ee11d52ca47ac1ecfbc3c36deae165fd8bb54fdfabb67794f.json](graphify-out/cache/ast/v0.9.8/2dd899dfb853fe8ee11d52ca47ac1ecfbc3c36deae165fd8bb54fdfabb67794f.json) |  | 2026-07-07 | 16KB | `41cf9986` |
| [graphify-out/cache/ast/v0.9.8/2de2216befdbc3690e31c81a9e6a842dfe08c8d19cc29397562dbe273e8c1653.json](graphify-out/cache/ast/v0.9.8/2de2216befdbc3690e31c81a9e6a842dfe08c8d19cc29397562dbe273e8c1653.json) |  | 2026-07-08 | 16KB | `c96b8a80` |
| [graphify-out/cache/ast/v0.9.8/2dff84b54e53f8eec385bed559f439c89db2d1f32c22d4030ca92058d90aa4fb.json](graphify-out/cache/ast/v0.9.8/2dff84b54e53f8eec385bed559f439c89db2d1f32c22d4030ca92058d90aa4fb.json) |  | 2026-07-08 | 26KB | `d3bf4986` |
| [graphify-out/cache/ast/v0.9.8/2e25d93476591f9488aaa2b2540e59da29b5a4a60ce194957984de7ad3e21760.json](graphify-out/cache/ast/v0.9.8/2e25d93476591f9488aaa2b2540e59da29b5a4a60ce194957984de7ad3e21760.json) |  | 2026-07-08 | 8KB | `8e3d6fee` |
| [graphify-out/cache/ast/v0.9.8/2f3ecb66d7ddc7d0d95431e5645bb7a61e79e66d1e72f44b9627d7d3f8b27e7f.json](graphify-out/cache/ast/v0.9.8/2f3ecb66d7ddc7d0d95431e5645bb7a61e79e66d1e72f44b9627d7d3f8b27e7f.json) |  | 2026-07-08 | 43KB | `742ac6c8` |
| [graphify-out/cache/ast/v0.9.8/2f4db95c1c24e17781960b3ad31231a1ee3892442255b740739ae04c6bc66480.json](graphify-out/cache/ast/v0.9.8/2f4db95c1c24e17781960b3ad31231a1ee3892442255b740739ae04c6bc66480.json) |  | 2026-07-30 | 9KB | `56410654` |
| [graphify-out/cache/ast/v0.9.8/2f5dea11d065853f806344a7fe9c960e082eb15fdd9d74bc77d78b56b020a1ae.json](graphify-out/cache/ast/v0.9.8/2f5dea11d065853f806344a7fe9c960e082eb15fdd9d74bc77d78b56b020a1ae.json) |  | 2026-07-31 | 3KB | `f812a92c` |
| [graphify-out/cache/ast/v0.9.8/2f8ac8401a17b34afdf3cf327efec67738e436b124a1fcfa45932aec38bd1002.json](graphify-out/cache/ast/v0.9.8/2f8ac8401a17b34afdf3cf327efec67738e436b124a1fcfa45932aec38bd1002.json) |  | 2026-07-08 | 12KB | `c700b870` |
| [graphify-out/cache/ast/v0.9.8/301a642a516a9adef3415204d6644f6e1eca800a782f4a5f2cd4502491c3de0f.json](graphify-out/cache/ast/v0.9.8/301a642a516a9adef3415204d6644f6e1eca800a782f4a5f2cd4502491c3de0f.json) |  | 2026-07-30 | 4KB | `ece1daf8` |
| [graphify-out/cache/ast/v0.9.8/3025fe829b3a7de59afac52c8b3612f87a66b499de6b7f3ed56b5e2e7ebaedd2.json](graphify-out/cache/ast/v0.9.8/3025fe829b3a7de59afac52c8b3612f87a66b499de6b7f3ed56b5e2e7ebaedd2.json) |  | 2026-07-08 | 25KB | `5a3d8d7e` |
| [graphify-out/cache/ast/v0.9.8/30274d269b8cfbd194c5a305e48897901f962a710e0ed86fcecbe631df38a5c9.json](graphify-out/cache/ast/v0.9.8/30274d269b8cfbd194c5a305e48897901f962a710e0ed86fcecbe631df38a5c9.json) |  | 2026-07-08 | 13KB | `20d7aa4c` |
| [graphify-out/cache/ast/v0.9.8/3027a2523e5c6d5daa9773e4fd1cedddb05c8ffd411074e1437ea21911e0c4c2.json](graphify-out/cache/ast/v0.9.8/3027a2523e5c6d5daa9773e4fd1cedddb05c8ffd411074e1437ea21911e0c4c2.json) |  | 2026-07-08 | 64KB | `daaef945` |
| [graphify-out/cache/ast/v0.9.8/30d3a6e979aead0a8fc877a9b56e12af7e20becd71890f1b33a43d7f3b271cf0.json](graphify-out/cache/ast/v0.9.8/30d3a6e979aead0a8fc877a9b56e12af7e20becd71890f1b33a43d7f3b271cf0.json) |  | 2026-07-07 | 1KB | `523f1ab2` |
| [graphify-out/cache/ast/v0.9.8/312206fb5b887deddbb70fbdcbb6ce2d2d982af099be394735301773a3d1ce3c.json](graphify-out/cache/ast/v0.9.8/312206fb5b887deddbb70fbdcbb6ce2d2d982af099be394735301773a3d1ce3c.json) |  | 2026-07-30 | 56KB | `a3a5bf04` |
| [graphify-out/cache/ast/v0.9.8/315cf4f11494a0864f9e449fe97d671d93e86e1987a563f1a6ef14b85f53a94e.json](graphify-out/cache/ast/v0.9.8/315cf4f11494a0864f9e449fe97d671d93e86e1987a563f1a6ef14b85f53a94e.json) |  | 2026-07-31 | 3KB | `5666c147` |
| [graphify-out/cache/ast/v0.9.8/31726c3485f8e38bceb513de8e1837febc053b5ab810cb11af58617423f7bbd3.json](graphify-out/cache/ast/v0.9.8/31726c3485f8e38bceb513de8e1837febc053b5ab810cb11af58617423f7bbd3.json) |  | 2026-07-08 | 5KB | `efec7e03` |
| [graphify-out/cache/ast/v0.9.8/31c19d2f06404a0abfec4dd657e5fca57be02202cee930f0c1310855d30b4ed5.json](graphify-out/cache/ast/v0.9.8/31c19d2f06404a0abfec4dd657e5fca57be02202cee930f0c1310855d30b4ed5.json) |  | 2026-07-20 | 46KB | `eb9b3082` |
| [graphify-out/cache/ast/v0.9.8/31ccf58e04c3339ae7f3485220861e403880aaea525281381a68bb69b1e6134b.json](graphify-out/cache/ast/v0.9.8/31ccf58e04c3339ae7f3485220861e403880aaea525281381a68bb69b1e6134b.json) |  | 2026-07-08 | 4KB | `68a3ef86` |
| [graphify-out/cache/ast/v0.9.8/31cd87b0fa5538c67589309086b141a73a58ae47556bd4dd31a631598e5bf6b6.json](graphify-out/cache/ast/v0.9.8/31cd87b0fa5538c67589309086b141a73a58ae47556bd4dd31a631598e5bf6b6.json) |  | 2026-07-27 | 95KB | `acc63669` |
| [graphify-out/cache/ast/v0.9.8/31dda97a80c84d39811727604d533770ab2cc9f6867220ed04cd8c0858ee1199.json](graphify-out/cache/ast/v0.9.8/31dda97a80c84d39811727604d533770ab2cc9f6867220ed04cd8c0858ee1199.json) |  | 2026-07-08 | 16KB | `6d49175b` |
| [graphify-out/cache/ast/v0.9.8/31ddc60107b129f3781169d2ee3d7d70306afc7b6c1aee2cd7d3cc70034290dc.json](graphify-out/cache/ast/v0.9.8/31ddc60107b129f3781169d2ee3d7d70306afc7b6c1aee2cd7d3cc70034290dc.json) |  | 2026-07-08 | 5KB | `b7251fd8` |
| [graphify-out/cache/ast/v0.9.8/31e16ae7c7283d2372561f0331140c074331e1bd13d8e00bccf7e6d2156f4048.json](graphify-out/cache/ast/v0.9.8/31e16ae7c7283d2372561f0331140c074331e1bd13d8e00bccf7e6d2156f4048.json) |  | 2026-07-10 | 8KB | `a3441520` |
| [graphify-out/cache/ast/v0.9.8/320a37bc35fbe6c7d0180330b1619745774b4644e91796d8e2fa0af2990c9ff8.json](graphify-out/cache/ast/v0.9.8/320a37bc35fbe6c7d0180330b1619745774b4644e91796d8e2fa0af2990c9ff8.json) |  | 2026-07-08 | 11KB | `21e791e7` |
| [graphify-out/cache/ast/v0.9.8/322a42fa3ec86b6c87097da5d87a48b29ab7465c96769c187b3d0d910fd4c5a2.json](graphify-out/cache/ast/v0.9.8/322a42fa3ec86b6c87097da5d87a48b29ab7465c96769c187b3d0d910fd4c5a2.json) |  | 2026-07-08 | 12KB | `423232f4` |
| [graphify-out/cache/ast/v0.9.8/3271adb95a42c386a7de97899b92a538d8047a043bf15efd66fafc07bd25909d.json](graphify-out/cache/ast/v0.9.8/3271adb95a42c386a7de97899b92a538d8047a043bf15efd66fafc07bd25909d.json) |  | 2026-07-31 | 58KB | `ad719aa0` |
| [graphify-out/cache/ast/v0.9.8/3276763ea0697e732c616b2d9329d18926476b95ce63febc6bbad74529706469.json](graphify-out/cache/ast/v0.9.8/3276763ea0697e732c616b2d9329d18926476b95ce63febc6bbad74529706469.json) |  | 2026-07-08 | 6KB | `a0235125` |
| [graphify-out/cache/ast/v0.9.8/32f48b7a0d301edb9bacb96f364b3f2883569bb0bf36e282424be62f527700bf.json](graphify-out/cache/ast/v0.9.8/32f48b7a0d301edb9bacb96f364b3f2883569bb0bf36e282424be62f527700bf.json) |  | 2026-07-08 | 12KB | `823ed629` |
| [graphify-out/cache/ast/v0.9.8/33246f1e12de6f986df84c46aafd792956fd0f93ef6032a1187d4d2a02fcbc34.json](graphify-out/cache/ast/v0.9.8/33246f1e12de6f986df84c46aafd792956fd0f93ef6032a1187d4d2a02fcbc34.json) |  | 2026-07-08 | 10KB | `088fb22c` |
| [graphify-out/cache/ast/v0.9.8/335f2ab2e6d09f6f9ae7c17afc2e2e6e59e4fdea468d1b1ed89372cf6a7f610f.json](graphify-out/cache/ast/v0.9.8/335f2ab2e6d09f6f9ae7c17afc2e2e6e59e4fdea468d1b1ed89372cf6a7f610f.json) |  | 2026-07-08 | 12KB | `5496cb31` |
| [graphify-out/cache/ast/v0.9.8/336de9b6db4998cfe07b5fa9a9dc7cfa3095fb9f1942046a93254e5014fbc425.json](graphify-out/cache/ast/v0.9.8/336de9b6db4998cfe07b5fa9a9dc7cfa3095fb9f1942046a93254e5014fbc425.json) |  | 2026-07-08 | 36KB | `e07011ca` |
| [graphify-out/cache/ast/v0.9.8/339a169128f15a14aa3e54f044453162ba566093e2f974f7ff126a8b8894d653.json](graphify-out/cache/ast/v0.9.8/339a169128f15a14aa3e54f044453162ba566093e2f974f7ff126a8b8894d653.json) |  | 2026-07-07 | 16KB | `52208d1c` |
| [graphify-out/cache/ast/v0.9.8/33c86aa7a68f6dbdda6406b3d5934498a9a7265b4d97a8033b420fc6e960007b.json](graphify-out/cache/ast/v0.9.8/33c86aa7a68f6dbdda6406b3d5934498a9a7265b4d97a8033b420fc6e960007b.json) |  | 2026-07-08 | 2KB | `17b2d986` |
| [graphify-out/cache/ast/v0.9.8/33cf7f9f99e8a532843ccbcffd3348c6a7de0683990f69d64bdda84b348fa91f.json](graphify-out/cache/ast/v0.9.8/33cf7f9f99e8a532843ccbcffd3348c6a7de0683990f69d64bdda84b348fa91f.json) |  | 2026-07-08 | 27KB | `96067908` |
| [graphify-out/cache/ast/v0.9.8/342c9dd79db47d107d23ea6278bb183f1924a95131ba85f80f53f67b56db51f8.json](graphify-out/cache/ast/v0.9.8/342c9dd79db47d107d23ea6278bb183f1924a95131ba85f80f53f67b56db51f8.json) |  | 2026-07-08 | 44KB | `20abe195` |
| [graphify-out/cache/ast/v0.9.8/3441f2b1a65f37ddf5f43a0bda46fb9209b2c1f4ffdb2509b27c2be95428411a.json](graphify-out/cache/ast/v0.9.8/3441f2b1a65f37ddf5f43a0bda46fb9209b2c1f4ffdb2509b27c2be95428411a.json) |  | 2026-07-30 | 17KB | `91ba168f` |
| [graphify-out/cache/ast/v0.9.8/3525e1167e76af103522cfe7fe6118d3b022fabacd6eb15409705489a90be79a.json](graphify-out/cache/ast/v0.9.8/3525e1167e76af103522cfe7fe6118d3b022fabacd6eb15409705489a90be79a.json) |  | 2026-07-08 | 5KB | `b0233f42` |
| [graphify-out/cache/ast/v0.9.8/35468eea89a578948c4383daa7d0f3bc44ddb67ddc4c70f9871d15d9d5f9df3b.json](graphify-out/cache/ast/v0.9.8/35468eea89a578948c4383daa7d0f3bc44ddb67ddc4c70f9871d15d9d5f9df3b.json) |  | 2026-07-22 | 9KB | `c1b56764` |
| [graphify-out/cache/ast/v0.9.8/354c6e3c5b46d930de810e663ef36fc43e7fe1c04b998801c2c248cc0b7074ab.json](graphify-out/cache/ast/v0.9.8/354c6e3c5b46d930de810e663ef36fc43e7fe1c04b998801c2c248cc0b7074ab.json) |  | 2026-07-08 | 22KB | `944710f2` |
| [graphify-out/cache/ast/v0.9.8/36984379909949cafbd4278bf6ea5f1f51fd0d3cad4fcf6b76b5c2dc42a4ca96.json](graphify-out/cache/ast/v0.9.8/36984379909949cafbd4278bf6ea5f1f51fd0d3cad4fcf6b76b5c2dc42a4ca96.json) |  | 2026-07-08 | 10KB | `8006fa55` |
| [graphify-out/cache/ast/v0.9.8/36a1cc4781db9bc84a18ea083681d0bdda12abf4ed62fc9ca7f5e8d7e69e0d34.json](graphify-out/cache/ast/v0.9.8/36a1cc4781db9bc84a18ea083681d0bdda12abf4ed62fc9ca7f5e8d7e69e0d34.json) |  | 2026-07-08 | 13KB | `9ec2ab96` |
| [graphify-out/cache/ast/v0.9.8/36dbc60a4d3f86af41aaf6a1cd9634ab6031876ea9db043c38f826bdd141a752.json](graphify-out/cache/ast/v0.9.8/36dbc60a4d3f86af41aaf6a1cd9634ab6031876ea9db043c38f826bdd141a752.json) |  | 2026-07-09 | 6KB | `737a0d20` |
| [graphify-out/cache/ast/v0.9.8/36de11ec48547aef6a3baf854b014026158c7848fb1d25dda977f83fae83f752.json](graphify-out/cache/ast/v0.9.8/36de11ec48547aef6a3baf854b014026158c7848fb1d25dda977f83fae83f752.json) |  | 2026-07-08 | 21KB | `7a967608` |
| [graphify-out/cache/ast/v0.9.8/376b2d25d459655cc55d44d7112b33fb012abe48cc4c97ab953aa05f38242100.json](graphify-out/cache/ast/v0.9.8/376b2d25d459655cc55d44d7112b33fb012abe48cc4c97ab953aa05f38242100.json) |  | 2026-07-08 | 10KB | `42588f8c` |
| [graphify-out/cache/ast/v0.9.8/37d8bb40b13b83311bd75280804f8c8835cf2ca9cc4198c10fb07bc4b67d1048.json](graphify-out/cache/ast/v0.9.8/37d8bb40b13b83311bd75280804f8c8835cf2ca9cc4198c10fb07bc4b67d1048.json) |  | 2026-07-07 | 18KB | `199bde05` |
| [graphify-out/cache/ast/v0.9.8/386a9d892815c133af95a3548d83d602b23dea824971d7d0053409c77d5acfdd.json](graphify-out/cache/ast/v0.9.8/386a9d892815c133af95a3548d83d602b23dea824971d7d0053409c77d5acfdd.json) |  | 2026-07-07 | 14KB | `59c4d0a6` |
| [graphify-out/cache/ast/v0.9.8/3870651428b3b536f7115f11cbbf6e40edd53e2f361657a3d3b08d96ee2abe59.json](graphify-out/cache/ast/v0.9.8/3870651428b3b536f7115f11cbbf6e40edd53e2f361657a3d3b08d96ee2abe59.json) |  | 2026-07-29 | 9KB | `2ff7bd40` |
| [graphify-out/cache/ast/v0.9.8/388d1d1c2a99ed64beec2b416b964240af7e52c036320165042a31d67699ef96.json](graphify-out/cache/ast/v0.9.8/388d1d1c2a99ed64beec2b416b964240af7e52c036320165042a31d67699ef96.json) |  | 2026-07-07 | 28KB | `5e02e47c` |
| [graphify-out/cache/ast/v0.9.8/38a7d34c11e3747135a8ad9e597b030bef6be2e64ef6e7c03ee86bf851365bbd.json](graphify-out/cache/ast/v0.9.8/38a7d34c11e3747135a8ad9e597b030bef6be2e64ef6e7c03ee86bf851365bbd.json) |  | 2026-07-31 | 19KB | `fa5d560c` |
| [graphify-out/cache/ast/v0.9.8/38bd25ea0b5e7ffc22c1edc9d8ee2c6a459795315810f089f11f48d89d337cff.json](graphify-out/cache/ast/v0.9.8/38bd25ea0b5e7ffc22c1edc9d8ee2c6a459795315810f089f11f48d89d337cff.json) |  | 2026-07-07 | 7KB | `1fbe70f5` |
| [graphify-out/cache/ast/v0.9.8/38c09bf86ba84aae4cd6d301633dc880185eacdf814f5765a6f5fa76ac7b5bd2.json](graphify-out/cache/ast/v0.9.8/38c09bf86ba84aae4cd6d301633dc880185eacdf814f5765a6f5fa76ac7b5bd2.json) |  | 2026-07-08 | 5KB | `4fd64a6c` |
| [graphify-out/cache/ast/v0.9.8/391036a3876d10bc5cc817fce588fbb4479a9186b657d3ce18ce8d88bca968db.json](graphify-out/cache/ast/v0.9.8/391036a3876d10bc5cc817fce588fbb4479a9186b657d3ce18ce8d88bca968db.json) |  | 2026-07-10 | 9KB | `332a4722` |
| [graphify-out/cache/ast/v0.9.8/39b086baa0e091e17880daf6b4ab95af828ce82f0488ab35af03de8d45e87a40.json](graphify-out/cache/ast/v0.9.8/39b086baa0e091e17880daf6b4ab95af828ce82f0488ab35af03de8d45e87a40.json) |  | 2026-07-07 | 16KB | `35085118` |
| [graphify-out/cache/ast/v0.9.8/39b57efda4f474d72db9be9f4cdf6e3e0dc7f216c152453d0b6de49055374de3.json](graphify-out/cache/ast/v0.9.8/39b57efda4f474d72db9be9f4cdf6e3e0dc7f216c152453d0b6de49055374de3.json) |  | 2026-07-08 | 4KB | `11c0da0e` |
| [graphify-out/cache/ast/v0.9.8/39cc8db16f44728570913bf0382465254bf1ffb072442c68dd8c7252b6eb1d69.json](graphify-out/cache/ast/v0.9.8/39cc8db16f44728570913bf0382465254bf1ffb072442c68dd8c7252b6eb1d69.json) |  | 2026-07-08 | 42KB | `087a4964` |
| [graphify-out/cache/ast/v0.9.8/3a1af3e3d38fbceb669a79dc3c85fb001fb82418ac10d099e97b7cc00eab80d1.json](graphify-out/cache/ast/v0.9.8/3a1af3e3d38fbceb669a79dc3c85fb001fb82418ac10d099e97b7cc00eab80d1.json) |  | 2026-07-08 | 6KB | `20ec6fe1` |
| [graphify-out/cache/ast/v0.9.8/3b33004c1b5a26e1325a683996c55856877faf1c11155639fbfc2a1aec01144b.json](graphify-out/cache/ast/v0.9.8/3b33004c1b5a26e1325a683996c55856877faf1c11155639fbfc2a1aec01144b.json) |  | 2026-07-08 | 6KB | `0037448d` |
| [graphify-out/cache/ast/v0.9.8/3b3f812bcc5b58c38ccb2b1962816813f5d5dac4c9dc932240b9f4b77e59cd74.json](graphify-out/cache/ast/v0.9.8/3b3f812bcc5b58c38ccb2b1962816813f5d5dac4c9dc932240b9f4b77e59cd74.json) |  | 2026-07-27 | 9KB | `87b4b5c5` |
| [graphify-out/cache/ast/v0.9.8/3b4350c2a37292b27e34df8300d7a75b3ffb357a6d60e48749448845e6a665bc.json](graphify-out/cache/ast/v0.9.8/3b4350c2a37292b27e34df8300d7a75b3ffb357a6d60e48749448845e6a665bc.json) |  | 2026-07-08 | 29KB | `5c84326a` |
| [graphify-out/cache/ast/v0.9.8/3b49fba84cce5f047706f25fc011ca55f7c519e57d901e3a9001464ac21df805.json](graphify-out/cache/ast/v0.9.8/3b49fba84cce5f047706f25fc011ca55f7c519e57d901e3a9001464ac21df805.json) |  | 2026-07-08 | 4KB | `dfe8925d` |
| [graphify-out/cache/ast/v0.9.8/3b9230088999f11e702ee71d6ed636a96502bef7d2eaf9901ee8606b88776c05.json](graphify-out/cache/ast/v0.9.8/3b9230088999f11e702ee71d6ed636a96502bef7d2eaf9901ee8606b88776c05.json) |  | 2026-07-08 | 12KB | `76394e83` |
| [graphify-out/cache/ast/v0.9.8/3ba5c03eafe8ae6aae80dc7d071b6a4d239cd51fe41c1c601ea34ad88cb1a1f4.json](graphify-out/cache/ast/v0.9.8/3ba5c03eafe8ae6aae80dc7d071b6a4d239cd51fe41c1c601ea34ad88cb1a1f4.json) |  | 2026-07-08 | 6KB | `c97355df` |
| [graphify-out/cache/ast/v0.9.8/3be2c35a6c0712ef882155bffcc48dd991117a30f03bbdb584dd0f9f7fafbd40.json](graphify-out/cache/ast/v0.9.8/3be2c35a6c0712ef882155bffcc48dd991117a30f03bbdb584dd0f9f7fafbd40.json) |  | 2026-07-27 | 13KB | `89cca3b1` |
| [graphify-out/cache/ast/v0.9.8/3c08615b2d80aaf472346912931bd635cf2ac7135cfc85599b4be3eaf747b2bd.json](graphify-out/cache/ast/v0.9.8/3c08615b2d80aaf472346912931bd635cf2ac7135cfc85599b4be3eaf747b2bd.json) |  | 2026-07-07 | 5KB | `d849df16` |
| [graphify-out/cache/ast/v0.9.8/3c172b198e1cc34973bf7bdc872ccb17a41b65beaf727f8381cf83d037e416c9.json](graphify-out/cache/ast/v0.9.8/3c172b198e1cc34973bf7bdc872ccb17a41b65beaf727f8381cf83d037e416c9.json) |  | 2026-07-31 | 12KB | `6c5eac96` |
| [graphify-out/cache/ast/v0.9.8/3c3bf57cffff7d8e260bf4c294b3790b4f08a4a060e856b01d0b9cda43c68882.json](graphify-out/cache/ast/v0.9.8/3c3bf57cffff7d8e260bf4c294b3790b4f08a4a060e856b01d0b9cda43c68882.json) |  | 2026-07-08 | 11KB | `e619ccd2` |
| [graphify-out/cache/ast/v0.9.8/3c3d9db721fd6dc7aff2f52496b17f98228f62182cd16c54f6af57aee991f3aa.json](graphify-out/cache/ast/v0.9.8/3c3d9db721fd6dc7aff2f52496b17f98228f62182cd16c54f6af57aee991f3aa.json) |  | 2026-07-27 | 9KB | `87b4b5c5` |
| [graphify-out/cache/ast/v0.9.8/3cbf7c01396d788415af6c1a2b06b68c71dd7a5b37046a56cfa1909efb5484ac.json](graphify-out/cache/ast/v0.9.8/3cbf7c01396d788415af6c1a2b06b68c71dd7a5b37046a56cfa1909efb5484ac.json) |  | 2026-07-31 | 9KB | `a0af361d` |
| [graphify-out/cache/ast/v0.9.8/3cfb662f099c51a9d3e292fead5edd13d386f96154a2ca650e312e7715863c1e.json](graphify-out/cache/ast/v0.9.8/3cfb662f099c51a9d3e292fead5edd13d386f96154a2ca650e312e7715863c1e.json) |  | 2026-07-22 | 7KB | `30cb8749` |
| [graphify-out/cache/ast/v0.9.8/3d11e91324a942e79dd74ed17e95e5ca0ec80bf213281e885866e683a2b95a5b.json](graphify-out/cache/ast/v0.9.8/3d11e91324a942e79dd74ed17e95e5ca0ec80bf213281e885866e683a2b95a5b.json) |  | 2026-07-08 | 14KB | `5675219f` |
| [graphify-out/cache/ast/v0.9.8/3d60227a95909d9c000b702e66431794c4c92baceafe0dff3bdeb2d0edca3768.json](graphify-out/cache/ast/v0.9.8/3d60227a95909d9c000b702e66431794c4c92baceafe0dff3bdeb2d0edca3768.json) |  | 2026-07-08 | 11KB | `da8327d0` |
| [graphify-out/cache/ast/v0.9.8/3da5ecd5d72d6cef337dc28481801e1e69b32b5c09e7792ef1cd30b8c0aa6def.json](graphify-out/cache/ast/v0.9.8/3da5ecd5d72d6cef337dc28481801e1e69b32b5c09e7792ef1cd30b8c0aa6def.json) |  | 2026-07-08 | 4KB | `0e6b55ff` |
| [graphify-out/cache/ast/v0.9.8/3dd638f793f00635545f674267ff581ee73acae17a984ffb663edf2a0f0b8933.json](graphify-out/cache/ast/v0.9.8/3dd638f793f00635545f674267ff581ee73acae17a984ffb663edf2a0f0b8933.json) |  | 2026-07-08 | 10KB | `1fae6a0e` |
| [graphify-out/cache/ast/v0.9.8/3ddee2f44a6e2c8c4c8231289e1d52102a80a7a049880c9eab676fa90f42ae73.json](graphify-out/cache/ast/v0.9.8/3ddee2f44a6e2c8c4c8231289e1d52102a80a7a049880c9eab676fa90f42ae73.json) |  | 2026-07-27 | 55KB | `5f9dc602` |
| [graphify-out/cache/ast/v0.9.8/3deb2eb12b8a2cdcafbe0135b2eb94e4002b4126003dce01c24c4ce019d88aa8.json](graphify-out/cache/ast/v0.9.8/3deb2eb12b8a2cdcafbe0135b2eb94e4002b4126003dce01c24c4ce019d88aa8.json) |  | 2026-07-24 | 3KB | `3624535a` |
| [graphify-out/cache/ast/v0.9.8/3f588af826bfc5e9b87ee39edacc90a8f01d6622ef8465a714e98ca326befa03.json](graphify-out/cache/ast/v0.9.8/3f588af826bfc5e9b87ee39edacc90a8f01d6622ef8465a714e98ca326befa03.json) |  | 2026-07-08 | 16KB | `3b5be9aa` |
| [graphify-out/cache/ast/v0.9.8/3f8eedc75f5bf7aa9e08f12f9f5751b4e8e88de58ac8b7e5fd52722301560a2a.json](graphify-out/cache/ast/v0.9.8/3f8eedc75f5bf7aa9e08f12f9f5751b4e8e88de58ac8b7e5fd52722301560a2a.json) |  | 2026-07-07 | 18KB | `7ce5210c` |
| [graphify-out/cache/ast/v0.9.8/3fa7305b6310e0719e74b5e9ddd0c7fa4315fb07a834f60f98f1646d9d40a4aa.json](graphify-out/cache/ast/v0.9.8/3fa7305b6310e0719e74b5e9ddd0c7fa4315fb07a834f60f98f1646d9d40a4aa.json) |  | 2026-07-30 | 2KB | `6244132a` |
| [graphify-out/cache/ast/v0.9.8/3fac8c66ac8d31ee5b657d51c8bdfd05fdc346dcaa72b3ed0b06f2529da4e4fd.json](graphify-out/cache/ast/v0.9.8/3fac8c66ac8d31ee5b657d51c8bdfd05fdc346dcaa72b3ed0b06f2529da4e4fd.json) |  | 2026-07-08 | 99KB | `44cb53ad` |
| [graphify-out/cache/ast/v0.9.8/401b71fd3dbe8aa044a60462b3699b1dc9f902f0e12157bf2957097e77ff437e.json](graphify-out/cache/ast/v0.9.8/401b71fd3dbe8aa044a60462b3699b1dc9f902f0e12157bf2957097e77ff437e.json) |  | 2026-07-08 | 6KB | `5f3bbc45` |
| [graphify-out/cache/ast/v0.9.8/401f0f2ed9561b36d2f0df6aefb1b28c020868bb02af75c15b3fc54442938cae.json](graphify-out/cache/ast/v0.9.8/401f0f2ed9561b36d2f0df6aefb1b28c020868bb02af75c15b3fc54442938cae.json) |  | 2026-07-07 | 23KB | `ad0245f0` |
| [graphify-out/cache/ast/v0.9.8/40239c8b625698523e1246b5e33b0e5c0b55acec6f8b8dad82597b0fe3c6cfd5.json](graphify-out/cache/ast/v0.9.8/40239c8b625698523e1246b5e33b0e5c0b55acec6f8b8dad82597b0fe3c6cfd5.json) |  | 2026-07-07 | 11KB | `beff9972` |
| [graphify-out/cache/ast/v0.9.8/40707394dc7b4887ce92985548b9634d241bb48b43f333c5be0d44aacb6b1547.json](graphify-out/cache/ast/v0.9.8/40707394dc7b4887ce92985548b9634d241bb48b43f333c5be0d44aacb6b1547.json) |  | 2026-07-08 | 26KB | `9353250e` |
| [graphify-out/cache/ast/v0.9.8/409542d95910afbc07eaaba8aba21f782e71e89c16702e758e2d01ea71cc6617.json](graphify-out/cache/ast/v0.9.8/409542d95910afbc07eaaba8aba21f782e71e89c16702e758e2d01ea71cc6617.json) |  | 2026-07-08 | 35KB | `438a3003` |
| [graphify-out/cache/ast/v0.9.8/4096628a777b2a4de16e9fb753cdf89444b00f10a1e2f038e723a49591b895e7.json](graphify-out/cache/ast/v0.9.8/4096628a777b2a4de16e9fb753cdf89444b00f10a1e2f038e723a49591b895e7.json) |  | 2026-07-22 | 21KB | `b2a532b3` |
| [graphify-out/cache/ast/v0.9.8/40a092641d5b7c0b0bdcdd7ca6e3db8ebff5cd52652145f8bfe3121e8b60cf89.json](graphify-out/cache/ast/v0.9.8/40a092641d5b7c0b0bdcdd7ca6e3db8ebff5cd52652145f8bfe3121e8b60cf89.json) |  | 2026-07-08 | 3KB | `acf99f10` |
| [graphify-out/cache/ast/v0.9.8/40ae4943f0103688358d58197ddd909be27443ffff8731c2f23afca744765a93.json](graphify-out/cache/ast/v0.9.8/40ae4943f0103688358d58197ddd909be27443ffff8731c2f23afca744765a93.json) |  | 2026-07-09 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/40c4ebc5f978b7a50691d192585a3e23f3f577c39c940244221d608035c5d9fa.json](graphify-out/cache/ast/v0.9.8/40c4ebc5f978b7a50691d192585a3e23f3f577c39c940244221d608035c5d9fa.json) |  | 2026-07-08 | 5KB | `f7df2045` |
| [graphify-out/cache/ast/v0.9.8/411b15115e5b8b6730e9ac25eb94b0291ab33f9212e2de7eba7abb0b50a17988.json](graphify-out/cache/ast/v0.9.8/411b15115e5b8b6730e9ac25eb94b0291ab33f9212e2de7eba7abb0b50a17988.json) |  | 2026-07-24 | 14KB | `e15a5c12` |
| [graphify-out/cache/ast/v0.9.8/41282e42c81a293e628575bb5a6c01f9f3dbe3cff5efcf95b549d46d8a022d90.json](graphify-out/cache/ast/v0.9.8/41282e42c81a293e628575bb5a6c01f9f3dbe3cff5efcf95b549d46d8a022d90.json) |  | 2026-07-08 | 7KB | `e98e243f` |
| [graphify-out/cache/ast/v0.9.8/413c11e92d3104b41872dc7703d969e078c243aa04056288883564e623c378fd.json](graphify-out/cache/ast/v0.9.8/413c11e92d3104b41872dc7703d969e078c243aa04056288883564e623c378fd.json) |  | 2026-07-24 | 54KB | `fb7f8c70` |
| [graphify-out/cache/ast/v0.9.8/416ccdc852bc7b834d0a3bba8743d436f4441d3d84b3f613910d5ca4ab7183ce.json](graphify-out/cache/ast/v0.9.8/416ccdc852bc7b834d0a3bba8743d436f4441d3d84b3f613910d5ca4ab7183ce.json) |  | 2026-07-07 | 1KB | `d99bd6a3` |
| [graphify-out/cache/ast/v0.9.8/419453aba5581704ee3212bfff0b5662c346ab40bca3149bcb29d6b68578eb34.json](graphify-out/cache/ast/v0.9.8/419453aba5581704ee3212bfff0b5662c346ab40bca3149bcb29d6b68578eb34.json) |  | 2026-07-07 | 17KB | `373983b1` |
| [graphify-out/cache/ast/v0.9.8/41a9277a1e4ed53c30095041b45ad9f794dc3910114448aeeac104c70731688a.json](graphify-out/cache/ast/v0.9.8/41a9277a1e4ed53c30095041b45ad9f794dc3910114448aeeac104c70731688a.json) |  | 2026-07-22 | 10KB | `c31b8ae7` |
| [graphify-out/cache/ast/v0.9.8/41b36649da2d20cabb82e35d96804d10a4ac42b495ae84765b171c66c246c74b.json](graphify-out/cache/ast/v0.9.8/41b36649da2d20cabb82e35d96804d10a4ac42b495ae84765b171c66c246c74b.json) |  | 2026-07-31 | 6KB | `fd95b819` |
| [graphify-out/cache/ast/v0.9.8/41c7c383511a28eced007887b87a2dc0494666f1a2a32e3c95abb6f3d583ef05.json](graphify-out/cache/ast/v0.9.8/41c7c383511a28eced007887b87a2dc0494666f1a2a32e3c95abb6f3d583ef05.json) |  | 2026-07-08 | 2KB | `f320e32d` |
| [graphify-out/cache/ast/v0.9.8/424d904b00927ed15d7b15c9bb7bf99de6dd8d503c8f0cee9ac5c920438621d1.json](graphify-out/cache/ast/v0.9.8/424d904b00927ed15d7b15c9bb7bf99de6dd8d503c8f0cee9ac5c920438621d1.json) |  | 2026-07-08 | 44KB | `9ddbb91a` |
| [graphify-out/cache/ast/v0.9.8/4261644f11d59f9238a3b183a259190550029f261a92d456662714e77df6fc3f.json](graphify-out/cache/ast/v0.9.8/4261644f11d59f9238a3b183a259190550029f261a92d456662714e77df6fc3f.json) |  | 2026-07-08 | 91KB | `7da88488` |
| [graphify-out/cache/ast/v0.9.8/429b07f27be44941a11f38abf2f450173c4d6fcef83b453315849e4987f6ac78.json](graphify-out/cache/ast/v0.9.8/429b07f27be44941a11f38abf2f450173c4d6fcef83b453315849e4987f6ac78.json) |  | 2026-07-10 | 14KB | `65c7b8b8` |
| [graphify-out/cache/ast/v0.9.8/42a9637ede11b982035718d1f9e5076a39228469ee4e772b7a3972e4d21f8c8e.json](graphify-out/cache/ast/v0.9.8/42a9637ede11b982035718d1f9e5076a39228469ee4e772b7a3972e4d21f8c8e.json) |  | 2026-07-08 | 7KB | `40662fcd` |
| [graphify-out/cache/ast/v0.9.8/4306875d997f18f91891f35ba8eb86c685eb9c33c834ccefd29b341eacc39424.json](graphify-out/cache/ast/v0.9.8/4306875d997f18f91891f35ba8eb86c685eb9c33c834ccefd29b341eacc39424.json) |  | 2026-07-08 | 6KB | `59ee421b` |
| [graphify-out/cache/ast/v0.9.8/43298657b40b689068961ca1f1f9cf936b25461a7db4af39bae0f13639612fef.json](graphify-out/cache/ast/v0.9.8/43298657b40b689068961ca1f1f9cf936b25461a7db4af39bae0f13639612fef.json) |  | 2026-07-08 | 146KB | `a7c72e82` |
| [graphify-out/cache/ast/v0.9.8/4371236530f458982759109a9129d637e1fe02f50f77195198c1049564e06ec1.json](graphify-out/cache/ast/v0.9.8/4371236530f458982759109a9129d637e1fe02f50f77195198c1049564e06ec1.json) |  | 2026-07-08 | 9KB | `cef7586f` |
| [graphify-out/cache/ast/v0.9.8/4398ffb9c8838b4c9483b1a5f8baec948800286591884d8591be6e0b84927a19.json](graphify-out/cache/ast/v0.9.8/4398ffb9c8838b4c9483b1a5f8baec948800286591884d8591be6e0b84927a19.json) |  | 2026-07-08 | 14KB | `921ce247` |
| [graphify-out/cache/ast/v0.9.8/448a9ff0753ba2ede7635d0252d08a01db4bc5fe08d592b7ab4d525eb20eab30.json](graphify-out/cache/ast/v0.9.8/448a9ff0753ba2ede7635d0252d08a01db4bc5fe08d592b7ab4d525eb20eab30.json) |  | 2026-07-08 | 9KB | `8d464965` |
| [graphify-out/cache/ast/v0.9.8/449205f79a3a738af46f17ac15d43ced52d5e38405cb20c3686662ef487b9734.json](graphify-out/cache/ast/v0.9.8/449205f79a3a738af46f17ac15d43ced52d5e38405cb20c3686662ef487b9734.json) |  | 2026-07-08 | 26KB | `1030b435` |
| [graphify-out/cache/ast/v0.9.8/44e7287ebfd615d6857cc475707232a602e113545146a6b6fcdf0fdcf93ae5a7.json](graphify-out/cache/ast/v0.9.8/44e7287ebfd615d6857cc475707232a602e113545146a6b6fcdf0fdcf93ae5a7.json) |  | 2026-07-08 | 6KB | `d3eaebce` |
| [graphify-out/cache/ast/v0.9.8/456415b50a5ecdd44d98338f4fa3bc7cdc9247ab5ad4bbbc7a751a46fd581665.json](graphify-out/cache/ast/v0.9.8/456415b50a5ecdd44d98338f4fa3bc7cdc9247ab5ad4bbbc7a751a46fd581665.json) |  | 2026-07-08 | 3KB | `80e5e563` |
| [graphify-out/cache/ast/v0.9.8/45d0e308ed5e55f0b2fb0b990d7e687fb5cc975d9282608d08e444a54b0ca7bb.json](graphify-out/cache/ast/v0.9.8/45d0e308ed5e55f0b2fb0b990d7e687fb5cc975d9282608d08e444a54b0ca7bb.json) |  | 2026-07-07 | 43KB | `65338ae5` |
| [graphify-out/cache/ast/v0.9.8/45dbdf7ef5f77edb0624e3b58fecd5660a28cc16d80993f34c355aa0dfe5b8a3.json](graphify-out/cache/ast/v0.9.8/45dbdf7ef5f77edb0624e3b58fecd5660a28cc16d80993f34c355aa0dfe5b8a3.json) |  | 2026-07-08 | 5KB | `58055b24` |
| [graphify-out/cache/ast/v0.9.8/45f0d01ebdccaa2d60f349f493f34b494a9aab33a078896a23be880bb1582d79.json](graphify-out/cache/ast/v0.9.8/45f0d01ebdccaa2d60f349f493f34b494a9aab33a078896a23be880bb1582d79.json) |  | 2026-07-08 | 13KB | `62a556af` |
| [graphify-out/cache/ast/v0.9.8/46661ff32d8e70739bf55b31aab0c1736a977a4aa637f667cb16b4a528c3aa25.json](graphify-out/cache/ast/v0.9.8/46661ff32d8e70739bf55b31aab0c1736a977a4aa637f667cb16b4a528c3aa25.json) |  | 2026-07-08 | 8KB | `1c90345f` |
| [graphify-out/cache/ast/v0.9.8/46821a0db4ce6627e98443d023733a60e61dc8bf5b1b0c1c6468486c6848cc11.json](graphify-out/cache/ast/v0.9.8/46821a0db4ce6627e98443d023733a60e61dc8bf5b1b0c1c6468486c6848cc11.json) |  | 2026-07-08 | 5KB | `c6d835d7` |
| [graphify-out/cache/ast/v0.9.8/4697ee15db0a208fcdef6e77ce632f8222cdc7267d7f82a2849b89f8e27c9116.json](graphify-out/cache/ast/v0.9.8/4697ee15db0a208fcdef6e77ce632f8222cdc7267d7f82a2849b89f8e27c9116.json) |  | 2026-07-27 | 3KB | `6f6c1283` |
| [graphify-out/cache/ast/v0.9.8/46a8ea3be4138b3a4f6ba352a146b87da6ae4317750fe6bd3b4775a127f39fa4.json](graphify-out/cache/ast/v0.9.8/46a8ea3be4138b3a4f6ba352a146b87da6ae4317750fe6bd3b4775a127f39fa4.json) |  | 2026-07-29 | 13KB | `d29be7e6` |
| [graphify-out/cache/ast/v0.9.8/4706f2b63bc0df3b11300059f084705b8efc8b49e77203962d67f096acf7c9a7.json](graphify-out/cache/ast/v0.9.8/4706f2b63bc0df3b11300059f084705b8efc8b49e77203962d67f096acf7c9a7.json) |  | 2026-07-07 | 18KB | `5be21e6d` |
| [graphify-out/cache/ast/v0.9.8/48360a9a2d5daad51e8b13c2cea763416dfd6ffefe328732621980e8012f87c9.json](graphify-out/cache/ast/v0.9.8/48360a9a2d5daad51e8b13c2cea763416dfd6ffefe328732621980e8012f87c9.json) |  | 2026-07-08 | 4KB | `d90d691e` |
| [graphify-out/cache/ast/v0.9.8/487f4addaed7b1ff55d0d706c33aa95cc48ebc861d11b01d68ca60cbd160b97b.json](graphify-out/cache/ast/v0.9.8/487f4addaed7b1ff55d0d706c33aa95cc48ebc861d11b01d68ca60cbd160b97b.json) |  | 2026-07-08 | 13KB | `d647255f` |
| [graphify-out/cache/ast/v0.9.8/4885391ae43cb3ac9e88794577033e096bb6129a1a1699101ab1110670abacf9.json](graphify-out/cache/ast/v0.9.8/4885391ae43cb3ac9e88794577033e096bb6129a1a1699101ab1110670abacf9.json) |  | 2026-07-08 | 31KB | `2f02f95f` |
| [graphify-out/cache/ast/v0.9.8/495968cd32ab5e2a40891b4b629b85a666dc36a011f990154e2403e0ce503787.json](graphify-out/cache/ast/v0.9.8/495968cd32ab5e2a40891b4b629b85a666dc36a011f990154e2403e0ce503787.json) |  | 2026-07-08 | 833B | `6f358862` |
| [graphify-out/cache/ast/v0.9.8/497a61f7a477d617b97ad64f44a040fd87afafb51f6101f554a636b30c4837e0.json](graphify-out/cache/ast/v0.9.8/497a61f7a477d617b97ad64f44a040fd87afafb51f6101f554a636b30c4837e0.json) |  | 2026-07-07 | 17KB | `a3740c20` |
| [graphify-out/cache/ast/v0.9.8/49877abb3c998855f80504625b613ae5ebef615267f8f5bcd527f157525983a4.json](graphify-out/cache/ast/v0.9.8/49877abb3c998855f80504625b613ae5ebef615267f8f5bcd527f157525983a4.json) |  | 2026-07-22 | 4KB | `2c7074dc` |
| [graphify-out/cache/ast/v0.9.8/4988a93e443a1857767b9da43e0e57f4d3964b878d587174dc60c99a4450cd79.json](graphify-out/cache/ast/v0.9.8/4988a93e443a1857767b9da43e0e57f4d3964b878d587174dc60c99a4450cd79.json) |  | 2026-07-08 | 16KB | `7e45045a` |
| [graphify-out/cache/ast/v0.9.8/498cf6819f649314e8cb056d33c849996903d1151888140d7bc4b568c5202a33.json](graphify-out/cache/ast/v0.9.8/498cf6819f649314e8cb056d33c849996903d1151888140d7bc4b568c5202a33.json) |  | 2026-07-08 | 4KB | `239e1d75` |
| [graphify-out/cache/ast/v0.9.8/499a07ee9826073d42ce9599eae6fbaef716c874bcb723cc6c7554ab4c8945a6.json](graphify-out/cache/ast/v0.9.8/499a07ee9826073d42ce9599eae6fbaef716c874bcb723cc6c7554ab4c8945a6.json) |  | 2026-07-08 | 9KB | `00f52ab1` |
| [graphify-out/cache/ast/v0.9.8/4a17cdc92c80e0826158648b222de8df7ad3c31f0c8f6a1832bbe725adedba7e.json](graphify-out/cache/ast/v0.9.8/4a17cdc92c80e0826158648b222de8df7ad3c31f0c8f6a1832bbe725adedba7e.json) |  | 2026-07-08 | 13KB | `f1d0707f` |
| [graphify-out/cache/ast/v0.9.8/4a51e097c6557cc5b8a190aaeeb1cf467fc8ba540ee20f19a48f07d32194e79e.json](graphify-out/cache/ast/v0.9.8/4a51e097c6557cc5b8a190aaeeb1cf467fc8ba540ee20f19a48f07d32194e79e.json) |  | 2026-07-08 | 2KB | `1cb0370b` |
| [graphify-out/cache/ast/v0.9.8/4a67df1e1b7bb5bb5b80a929aa4a0c043bbd662785fa615e8c8347aa82381f66.json](graphify-out/cache/ast/v0.9.8/4a67df1e1b7bb5bb5b80a929aa4a0c043bbd662785fa615e8c8347aa82381f66.json) |  | 2026-07-08 | 10KB | `9752c0ce` |
| [graphify-out/cache/ast/v0.9.8/4a6e608ec09d36fc914f8cc87a048b6b68a0a0a2cb29fd3c9da6df238fa7b210.json](graphify-out/cache/ast/v0.9.8/4a6e608ec09d36fc914f8cc87a048b6b68a0a0a2cb29fd3c9da6df238fa7b210.json) |  | 2026-07-08 | 15KB | `6681a94e` |
| [graphify-out/cache/ast/v0.9.8/4aed268cb23626e2c05566103fb2ba9368165719d4835783614446f0b4bb0fe0.json](graphify-out/cache/ast/v0.9.8/4aed268cb23626e2c05566103fb2ba9368165719d4835783614446f0b4bb0fe0.json) |  | 2026-07-08 | 6KB | `e06bef4d` |
| [graphify-out/cache/ast/v0.9.8/4b1fc24593120b13c7870f68e04a05cc09e2e5eecce9d870b60b5552a81e7a92.json](graphify-out/cache/ast/v0.9.8/4b1fc24593120b13c7870f68e04a05cc09e2e5eecce9d870b60b5552a81e7a92.json) |  | 2026-07-08 | 9KB | `850157cb` |
| [graphify-out/cache/ast/v0.9.8/4b34e5b0fd15cae51309043a67af2f5420a7b3ceb5e87fd146eaf893958de51a.json](graphify-out/cache/ast/v0.9.8/4b34e5b0fd15cae51309043a67af2f5420a7b3ceb5e87fd146eaf893958de51a.json) |  | 2026-07-29 | 11KB | `bb830609` |
| [graphify-out/cache/ast/v0.9.8/4b7193739c2dc0c25fed018b8b1068406df0b14e917b3b096722277f655b02a6.json](graphify-out/cache/ast/v0.9.8/4b7193739c2dc0c25fed018b8b1068406df0b14e917b3b096722277f655b02a6.json) |  | 2026-07-08 | 3KB | `8b7d8be1` |
| [graphify-out/cache/ast/v0.9.8/4b937953b2304fdc4fff05af307b498f4aa258c2d5d937be53f1054c074b3af0.json](graphify-out/cache/ast/v0.9.8/4b937953b2304fdc4fff05af307b498f4aa258c2d5d937be53f1054c074b3af0.json) |  | 2026-07-08 | 1KB | `a43d6f02` |
| [graphify-out/cache/ast/v0.9.8/4be2f5bcfc256eed5494ade8000482ebb38dabdf3822ebd481801bf1a45e25f1.json](graphify-out/cache/ast/v0.9.8/4be2f5bcfc256eed5494ade8000482ebb38dabdf3822ebd481801bf1a45e25f1.json) |  | 2026-07-08 | 19KB | `f7a8dda2` |
| [graphify-out/cache/ast/v0.9.8/4c212873c97e0322d81ba2e77f4565484fd6981c244c22f49428ef214f7b2ed0.json](graphify-out/cache/ast/v0.9.8/4c212873c97e0322d81ba2e77f4565484fd6981c244c22f49428ef214f7b2ed0.json) |  | 2026-07-08 | 44KB | `b82ff842` |
| [graphify-out/cache/ast/v0.9.8/4c6caf983056ff33671c82605ba1b611f25eb97020b577fe11ef4f2ad446b0aa.json](graphify-out/cache/ast/v0.9.8/4c6caf983056ff33671c82605ba1b611f25eb97020b577fe11ef4f2ad446b0aa.json) |  | 2026-07-07 | 21KB | `49f04f22` |
| [graphify-out/cache/ast/v0.9.8/4cb700074adedbebfe9ddb0be1a5a679eb4962e4b64172a5afbc66aead593bbe.json](graphify-out/cache/ast/v0.9.8/4cb700074adedbebfe9ddb0be1a5a679eb4962e4b64172a5afbc66aead593bbe.json) |  | 2026-07-08 | 9KB | `ddc37f0f` |
| [graphify-out/cache/ast/v0.9.8/4dbe791935fa03cc86d3105e32fed3ae58cc9f41306922d9e190e345ab617ee4.json](graphify-out/cache/ast/v0.9.8/4dbe791935fa03cc86d3105e32fed3ae58cc9f41306922d9e190e345ab617ee4.json) |  | 2026-07-08 | 18KB | `d5ec3d37` |
| [graphify-out/cache/ast/v0.9.8/4e0056cb95ccb0baa32ea8768456eaedc60b7bece15207b21f66979d6d28598d.json](graphify-out/cache/ast/v0.9.8/4e0056cb95ccb0baa32ea8768456eaedc60b7bece15207b21f66979d6d28598d.json) |  | 2026-07-08 | 7KB | `c945ec80` |
| [graphify-out/cache/ast/v0.9.8/4e245130721d864df834f48c7e88adc503ab4f7c7e9c572c684b461bb76d260d.json](graphify-out/cache/ast/v0.9.8/4e245130721d864df834f48c7e88adc503ab4f7c7e9c572c684b461bb76d260d.json) |  | 2026-07-08 | 4KB | `dd058425` |
| [graphify-out/cache/ast/v0.9.8/4e4e65c541206c544b4567ed6f5278b2c97b9834ba702cc8b7322502c24c9d83.json](graphify-out/cache/ast/v0.9.8/4e4e65c541206c544b4567ed6f5278b2c97b9834ba702cc8b7322502c24c9d83.json) |  | 2026-07-07 | 21KB | `880592bd` |
| [graphify-out/cache/ast/v0.9.8/4ea16c2387dcb2a87d7314fe1313c4f6415a744543c26424ee6a13380bee3b48.json](graphify-out/cache/ast/v0.9.8/4ea16c2387dcb2a87d7314fe1313c4f6415a744543c26424ee6a13380bee3b48.json) |  | 2026-07-08 | 57KB | `8d8c09f5` |
| [graphify-out/cache/ast/v0.9.8/4ed6398d81d68963520db916f6312f976f966d65765733bd4188e0474797127e.json](graphify-out/cache/ast/v0.9.8/4ed6398d81d68963520db916f6312f976f966d65765733bd4188e0474797127e.json) |  | 2026-07-31 | 21KB | `a68e6e42` |
| [graphify-out/cache/ast/v0.9.8/4f652059b9cffe7ff0e8002e27622edbca89ad6aae4c440f70882dffea8140c3.json](graphify-out/cache/ast/v0.9.8/4f652059b9cffe7ff0e8002e27622edbca89ad6aae4c440f70882dffea8140c3.json) |  | 2026-07-10 | 7KB | `17305234` |
| [graphify-out/cache/ast/v0.9.8/4f9e014737e58d766c706313fd53ac5d510d3896c25dd119a3b2b568df9e3038.json](graphify-out/cache/ast/v0.9.8/4f9e014737e58d766c706313fd53ac5d510d3896c25dd119a3b2b568df9e3038.json) |  | 2026-07-08 | 5KB | `e3181b61` |
| [graphify-out/cache/ast/v0.9.8/4fcaff4c57cc8305d02f3f9b412eae447afbcbc58beabf01013bac28cce64727.json](graphify-out/cache/ast/v0.9.8/4fcaff4c57cc8305d02f3f9b412eae447afbcbc58beabf01013bac28cce64727.json) |  | 2026-07-08 | 5KB | `caa59d8e` |
| [graphify-out/cache/ast/v0.9.8/50ab425b244fa61755092830b8837d007bd90a6343e9311b0ec058d882584af8.json](graphify-out/cache/ast/v0.9.8/50ab425b244fa61755092830b8837d007bd90a6343e9311b0ec058d882584af8.json) |  | 2026-07-07 | 28KB | `ffa6ee2a` |
| [graphify-out/cache/ast/v0.9.8/50d6d62265aceeac5dc866018f5cd1bc93ce97854fa2264ce9da93f395cb244f.json](graphify-out/cache/ast/v0.9.8/50d6d62265aceeac5dc866018f5cd1bc93ce97854fa2264ce9da93f395cb244f.json) |  | 2026-07-08 | 26KB | `f9f62c1b` |
| [graphify-out/cache/ast/v0.9.8/50ed19d63ec7967ac4a5236c03faa9ac879bf7728d930a958822c7eff9fba4d5.json](graphify-out/cache/ast/v0.9.8/50ed19d63ec7967ac4a5236c03faa9ac879bf7728d930a958822c7eff9fba4d5.json) |  | 2026-07-07 | 12KB | `e9d4d77b` |
| [graphify-out/cache/ast/v0.9.8/50f5c1bc813215c4de23cbbeb4a4d0ca71d872406d1e271996c12f079ddab7e6.json](graphify-out/cache/ast/v0.9.8/50f5c1bc813215c4de23cbbeb4a4d0ca71d872406d1e271996c12f079ddab7e6.json) |  | 2026-07-08 | 8KB | `0ba1eee1` |
| [graphify-out/cache/ast/v0.9.8/510d27e35dbbed8becfde97a094ca57532b077bd93ec92643269b0c4177b6638.json](graphify-out/cache/ast/v0.9.8/510d27e35dbbed8becfde97a094ca57532b077bd93ec92643269b0c4177b6638.json) |  | 2026-07-08 | 11KB | `becb085f` |
| [graphify-out/cache/ast/v0.9.8/511da9024e36b8ee9a72b86e364805180a948110e8dbbda42a0ebb5cc087d592.json](graphify-out/cache/ast/v0.9.8/511da9024e36b8ee9a72b86e364805180a948110e8dbbda42a0ebb5cc087d592.json) |  | 2026-07-07 | 17KB | `afa50532` |
| [graphify-out/cache/ast/v0.9.8/5148096e50837dac50b627128cd27532ff1eab196265411e7367ee454bb5bc63.json](graphify-out/cache/ast/v0.9.8/5148096e50837dac50b627128cd27532ff1eab196265411e7367ee454bb5bc63.json) |  | 2026-07-08 | 63KB | `b5f05df2` |
| [graphify-out/cache/ast/v0.9.8/51a4fb1f530b9f774ccd3b754789b10d6d3253d4ecfa33270fc6d0a1b110579f.json](graphify-out/cache/ast/v0.9.8/51a4fb1f530b9f774ccd3b754789b10d6d3253d4ecfa33270fc6d0a1b110579f.json) |  | 2026-07-08 | 4KB | `50316696` |
| [graphify-out/cache/ast/v0.9.8/523d11271cdb44b02a37ac076cf600d4d1bc6993df8dfecfea6182b1044a01a9.json](graphify-out/cache/ast/v0.9.8/523d11271cdb44b02a37ac076cf600d4d1bc6993df8dfecfea6182b1044a01a9.json) |  | 2026-07-08 | 7KB | `ecec1991` |
| [graphify-out/cache/ast/v0.9.8/52a779c598464b0fcbf2cfe08d7fd474bc4ee50892c69add5ab7026265048f27.json](graphify-out/cache/ast/v0.9.8/52a779c598464b0fcbf2cfe08d7fd474bc4ee50892c69add5ab7026265048f27.json) |  | 2026-07-08 | 12KB | `73d5158a` |
| [graphify-out/cache/ast/v0.9.8/5320819562178fe1df1b3a8234ca114f34384bfeb382d8350875d28a645723b6.json](graphify-out/cache/ast/v0.9.8/5320819562178fe1df1b3a8234ca114f34384bfeb382d8350875d28a645723b6.json) |  | 2026-07-08 | 28KB | `bc6b464e` |
| [graphify-out/cache/ast/v0.9.8/5336312fb28f66030f83d795f4aac09bf098248117553c36dc009099b6cbbe8e.json](graphify-out/cache/ast/v0.9.8/5336312fb28f66030f83d795f4aac09bf098248117553c36dc009099b6cbbe8e.json) |  | 2026-07-30 | 3KB | `4d9b516f` |
| [graphify-out/cache/ast/v0.9.8/53865b1b497ee9441d65cf969660799490abfbc21b8f4c5f8d247dde1cc88d5b.json](graphify-out/cache/ast/v0.9.8/53865b1b497ee9441d65cf969660799490abfbc21b8f4c5f8d247dde1cc88d5b.json) |  | 2026-07-07 | 10KB | `34d485f7` |
| [graphify-out/cache/ast/v0.9.8/5397ee5c5e87a877778d006b261c21120a018f92ce35e98e226996039ad06cc3.json](graphify-out/cache/ast/v0.9.8/5397ee5c5e87a877778d006b261c21120a018f92ce35e98e226996039ad06cc3.json) |  | 2026-07-08 | 20KB | `0ecd48e4` |
| [graphify-out/cache/ast/v0.9.8/53acd0afc1d0efc18ead95904ba914f480641dad5c10316aeb8917bc502048c3.json](graphify-out/cache/ast/v0.9.8/53acd0afc1d0efc18ead95904ba914f480641dad5c10316aeb8917bc502048c3.json) |  | 2026-07-08 | 23KB | `c2cd59aa` |
| [graphify-out/cache/ast/v0.9.8/53c7a4c13bd8dbe42d0616b32d14d95611990fcc7b6b1bb6f314b0bfe45dcb7b.json](graphify-out/cache/ast/v0.9.8/53c7a4c13bd8dbe42d0616b32d14d95611990fcc7b6b1bb6f314b0bfe45dcb7b.json) |  | 2026-07-07 | 155KB | `3cc13c59` |
| [graphify-out/cache/ast/v0.9.8/53d17f3d3abfda86ad0e2bfd7f79ed53a8c460e7773d33cde1eee14da1258e2c.json](graphify-out/cache/ast/v0.9.8/53d17f3d3abfda86ad0e2bfd7f79ed53a8c460e7773d33cde1eee14da1258e2c.json) |  | 2026-07-10 | 4KB | `c1271a1d` |
| [graphify-out/cache/ast/v0.9.8/53ff1f7e9b8ea13c73f1c7c4cd3e76914d1dd663de5f516581cf42afd2cc85cd.json](graphify-out/cache/ast/v0.9.8/53ff1f7e9b8ea13c73f1c7c4cd3e76914d1dd663de5f516581cf42afd2cc85cd.json) |  | 2026-07-07 | 12KB | `7621e324` |
| [graphify-out/cache/ast/v0.9.8/54047e10eeb6320c75bb24e8f7b6b6ca63aced65fae467dc82fe821388730627.json](graphify-out/cache/ast/v0.9.8/54047e10eeb6320c75bb24e8f7b6b6ca63aced65fae467dc82fe821388730627.json) |  | 2026-07-08 | 118KB | `8c3bd1d7` |
| [graphify-out/cache/ast/v0.9.8/54ad088b85cf2b282d79552975959fef2d6a1ac01d142c7170a4b57bb1fecfd9.json](graphify-out/cache/ast/v0.9.8/54ad088b85cf2b282d79552975959fef2d6a1ac01d142c7170a4b57bb1fecfd9.json) |  | 2026-07-07 | 763B | `1d68ab8d` |
| [graphify-out/cache/ast/v0.9.8/54e15a9e328b88a8a85d08433685141bad2c2cd6e58bdf9746d77f9399bf7476.json](graphify-out/cache/ast/v0.9.8/54e15a9e328b88a8a85d08433685141bad2c2cd6e58bdf9746d77f9399bf7476.json) |  | 2026-07-08 | 6KB | `c7ce18a4` |
| [graphify-out/cache/ast/v0.9.8/5507a1a26175dc35682b5ff360cc04496a5000b8e60ed4d5f0e8d04ac8939e5e.json](graphify-out/cache/ast/v0.9.8/5507a1a26175dc35682b5ff360cc04496a5000b8e60ed4d5f0e8d04ac8939e5e.json) |  | 2026-07-23 | 14KB | `2a70b2e0` |
| [graphify-out/cache/ast/v0.9.8/551b330505d1510d2ffe62385afd629a4dff918d93e7c5b82abd120a91738854.json](graphify-out/cache/ast/v0.9.8/551b330505d1510d2ffe62385afd629a4dff918d93e7c5b82abd120a91738854.json) |  | 2026-07-24 | 20KB | `25f67183` |
| [graphify-out/cache/ast/v0.9.8/551c859c8c6d37d751673a03a5cb41c2c73d70fb5b1068817da98e27c958b4b2.json](graphify-out/cache/ast/v0.9.8/551c859c8c6d37d751673a03a5cb41c2c73d70fb5b1068817da98e27c958b4b2.json) |  | 2026-07-23 | 13KB | `0cf80e18` |
| [graphify-out/cache/ast/v0.9.8/554b2525b0e0ffb9c56d7d73d71f8dc49fd7cc96eeef01e88127fd95f76b2613.json](graphify-out/cache/ast/v0.9.8/554b2525b0e0ffb9c56d7d73d71f8dc49fd7cc96eeef01e88127fd95f76b2613.json) |  | 2026-07-08 | 61KB | `1504a8d7` |
| [graphify-out/cache/ast/v0.9.8/554cbc8443af0a7571518f94af62f556a387dd361aaa7a73ed70c98a8ca019e3.json](graphify-out/cache/ast/v0.9.8/554cbc8443af0a7571518f94af62f556a387dd361aaa7a73ed70c98a8ca019e3.json) |  | 2026-07-08 | 32KB | `bb8e499a` |
| [graphify-out/cache/ast/v0.9.8/5550146359b4660605501d00768b1a931178c2c77e937c5437ed7af4d4691f9a.json](graphify-out/cache/ast/v0.9.8/5550146359b4660605501d00768b1a931178c2c77e937c5437ed7af4d4691f9a.json) |  | 2026-07-07 | 12KB | `e1d9f8e2` |
| [graphify-out/cache/ast/v0.9.8/555d03c0e0c0fd0655668edb32d663610e32fb00786ec5372e8faebb83108f7e.json](graphify-out/cache/ast/v0.9.8/555d03c0e0c0fd0655668edb32d663610e32fb00786ec5372e8faebb83108f7e.json) |  | 2026-07-30 | 15KB | `a534061a` |
| [graphify-out/cache/ast/v0.9.8/55912dd128870a5bed9add267fd414479fe2cc6d00b6d1cc65a328fc09adf316.json](graphify-out/cache/ast/v0.9.8/55912dd128870a5bed9add267fd414479fe2cc6d00b6d1cc65a328fc09adf316.json) |  | 2026-07-08 | 6KB | `4943ac70` |
| [graphify-out/cache/ast/v0.9.8/55950d7cb4960d37fc48d0c96dce7529e484a0c7d6e193c3f214737394e9dbd8.json](graphify-out/cache/ast/v0.9.8/55950d7cb4960d37fc48d0c96dce7529e484a0c7d6e193c3f214737394e9dbd8.json) |  | 2026-07-08 | 3KB | `617afe4d` |
| [graphify-out/cache/ast/v0.9.8/55ada45d20eef2fa9894baee1a4f378baf2b1e4b2e40937e0ea5ce9ecbf63a54.json](graphify-out/cache/ast/v0.9.8/55ada45d20eef2fa9894baee1a4f378baf2b1e4b2e40937e0ea5ce9ecbf63a54.json) |  | 2026-07-08 | 37KB | `cb9d71ae` |
| [graphify-out/cache/ast/v0.9.8/55f2bad0427cd61f9c30421caeb6aed285de0ffd1c9d773711d6f0d3201617f9.json](graphify-out/cache/ast/v0.9.8/55f2bad0427cd61f9c30421caeb6aed285de0ffd1c9d773711d6f0d3201617f9.json) |  | 2026-07-07 | 82KB | `696b8cd8` |
| [graphify-out/cache/ast/v0.9.8/5617c4163e39cc32ef723d7d56ea536bb40f823587d7fda1a55549720b83ed29.json](graphify-out/cache/ast/v0.9.8/5617c4163e39cc32ef723d7d56ea536bb40f823587d7fda1a55549720b83ed29.json) |  | 2026-07-08 | 3KB | `6b8cb941` |
| [graphify-out/cache/ast/v0.9.8/565e102e2f734146cb89c64893baa61b7dd60f26f780ba2da8f6310cebdd2f8b.json](graphify-out/cache/ast/v0.9.8/565e102e2f734146cb89c64893baa61b7dd60f26f780ba2da8f6310cebdd2f8b.json) |  | 2026-07-07 | 16KB | `8c127400` |
| [graphify-out/cache/ast/v0.9.8/56ac3eaf6ec26c38e442a75afae91ad2e6f6d9f84187a36f4cc4e879bebfb38b.json](graphify-out/cache/ast/v0.9.8/56ac3eaf6ec26c38e442a75afae91ad2e6f6d9f84187a36f4cc4e879bebfb38b.json) |  | 2026-07-08 | 12KB | `7a122ff7` |
| [graphify-out/cache/ast/v0.9.8/56b70e319b936832a32316622e5c379bb4bea6a2365224f4e6b84284e5dde2c6.json](graphify-out/cache/ast/v0.9.8/56b70e319b936832a32316622e5c379bb4bea6a2365224f4e6b84284e5dde2c6.json) |  | 2026-07-08 | 25KB | `47734074` |
| [graphify-out/cache/ast/v0.9.8/56d406ea5801e4db4da447bf6b17ffc9030211a67c16293acfd7e0e2b56c3b6a.json](graphify-out/cache/ast/v0.9.8/56d406ea5801e4db4da447bf6b17ffc9030211a67c16293acfd7e0e2b56c3b6a.json) |  | 2026-07-08 | 13KB | `058027ba` |
| [graphify-out/cache/ast/v0.9.8/56dff6e3d62cbd54e11e90cf883404e45d2536fd5b7cd1bec9b0f8a563ba7c7b.json](graphify-out/cache/ast/v0.9.8/56dff6e3d62cbd54e11e90cf883404e45d2536fd5b7cd1bec9b0f8a563ba7c7b.json) |  | 2026-07-08 | 7KB | `d2e07c5c` |
| [graphify-out/cache/ast/v0.9.8/575fb6705259d380b773c6f3ac7e00ae35de19981043e7879a65879546401b65.json](graphify-out/cache/ast/v0.9.8/575fb6705259d380b773c6f3ac7e00ae35de19981043e7879a65879546401b65.json) |  | 2026-07-29 | 13KB | `918a2a82` |
| [graphify-out/cache/ast/v0.9.8/576c130ec9fc0a18f238504274edfb77ddd7a20ca7e44501ea521b6bce7371d5.json](graphify-out/cache/ast/v0.9.8/576c130ec9fc0a18f238504274edfb77ddd7a20ca7e44501ea521b6bce7371d5.json) |  | 2026-07-24 | 106KB | `3102774a` |
| [graphify-out/cache/ast/v0.9.8/57e3d98318646ea481b0de1408483810e227e86a9ed2673a9c7202cfa14c6ff1.json](graphify-out/cache/ast/v0.9.8/57e3d98318646ea481b0de1408483810e227e86a9ed2673a9c7202cfa14c6ff1.json) |  | 2026-07-25 | 13KB | `dc96b3bd` |
| [graphify-out/cache/ast/v0.9.8/5801dd603326e0386a55f151a97a32b9e1a9d507cb45f931ca1f4947dadb450b.json](graphify-out/cache/ast/v0.9.8/5801dd603326e0386a55f151a97a32b9e1a9d507cb45f931ca1f4947dadb450b.json) |  | 2026-07-08 | 7KB | `25d08079` |
| [graphify-out/cache/ast/v0.9.8/5813282381b76248867730da7827c9a9eef5bd9f8f7105a2ff81f5235f3254ab.json](graphify-out/cache/ast/v0.9.8/5813282381b76248867730da7827c9a9eef5bd9f8f7105a2ff81f5235f3254ab.json) |  | 2026-07-08 | 7KB | `6f1fe3ac` |
| [graphify-out/cache/ast/v0.9.8/58437c093902a91b29bc8b06c06a2a0ec8bf1d274a02dd517a75043234b4379f.json](graphify-out/cache/ast/v0.9.8/58437c093902a91b29bc8b06c06a2a0ec8bf1d274a02dd517a75043234b4379f.json) |  | 2026-07-08 | 8KB | `e3b17f63` |
| [graphify-out/cache/ast/v0.9.8/5846667bbee654d6fa0faa19a5ecb52d44b7bbb2af61ec02e19f42de8c662643.json](graphify-out/cache/ast/v0.9.8/5846667bbee654d6fa0faa19a5ecb52d44b7bbb2af61ec02e19f42de8c662643.json) |  | 2026-07-08 | 12KB | `59f6969b` |
| [graphify-out/cache/ast/v0.9.8/585e3475707dff921e1ffeb9f9446e7e104c8ca191d88aa590ca45e634ac28e0.json](graphify-out/cache/ast/v0.9.8/585e3475707dff921e1ffeb9f9446e7e104c8ca191d88aa590ca45e634ac28e0.json) |  | 2026-07-08 | 8KB | `61b01c51` |
| [graphify-out/cache/ast/v0.9.8/585ed3079e593ff0d71553848c76de5508b032010ce90dcd08609f670bd68763.json](graphify-out/cache/ast/v0.9.8/585ed3079e593ff0d71553848c76de5508b032010ce90dcd08609f670bd68763.json) |  | 2026-07-08 | 30KB | `874882d7` |
| [graphify-out/cache/ast/v0.9.8/58cf56d79b7c47c63133615f6871a71dcb573633188ef709363abf8ea70d12d4.json](graphify-out/cache/ast/v0.9.8/58cf56d79b7c47c63133615f6871a71dcb573633188ef709363abf8ea70d12d4.json) |  | 2026-07-24 | 10KB | `44e77e53` |
| [graphify-out/cache/ast/v0.9.8/58f7c9caa4be1c6843153ac22bbccd1306a08ba5680930eac4fd02093f5c8832.json](graphify-out/cache/ast/v0.9.8/58f7c9caa4be1c6843153ac22bbccd1306a08ba5680930eac4fd02093f5c8832.json) |  | 2026-07-08 | 5KB | `6bb9f3ac` |
| [graphify-out/cache/ast/v0.9.8/58f8851c7ace4d5209da3fb6711ebadd4c44f0951853e55d3e990a594db56efd.json](graphify-out/cache/ast/v0.9.8/58f8851c7ace4d5209da3fb6711ebadd4c44f0951853e55d3e990a594db56efd.json) |  | 2026-07-09 | 13KB | `ee343443` |
| [graphify-out/cache/ast/v0.9.8/5920b3c18e7d1f30941b5625199152c4bf41089c35bb4c95f7236dfdb2dacc50.json](graphify-out/cache/ast/v0.9.8/5920b3c18e7d1f30941b5625199152c4bf41089c35bb4c95f7236dfdb2dacc50.json) |  | 2026-07-08 | 120KB | `3b631272` |
| [graphify-out/cache/ast/v0.9.8/5932b209ce66c334ac5f4533ebd2095e97149200a25868e6499bf29ec8ec6c28.json](graphify-out/cache/ast/v0.9.8/5932b209ce66c334ac5f4533ebd2095e97149200a25868e6499bf29ec8ec6c28.json) |  | 2026-07-30 | 4KB | `412a1211` |
| [graphify-out/cache/ast/v0.9.8/5983b362b36ebfa9e72ff812cf7d06c50176cb6b0701a6e37de9849dbc0f64eb.json](graphify-out/cache/ast/v0.9.8/5983b362b36ebfa9e72ff812cf7d06c50176cb6b0701a6e37de9849dbc0f64eb.json) |  | 2026-07-24 | 8KB | `3c6421c1` |
| [graphify-out/cache/ast/v0.9.8/59939c35d7c3a384ee49270ad4a534be6fb735f0e49f8ad35b72b6a29bd2bf34.json](graphify-out/cache/ast/v0.9.8/59939c35d7c3a384ee49270ad4a534be6fb735f0e49f8ad35b72b6a29bd2bf34.json) |  | 2026-07-22 | 10KB | `b02a4cb6` |
| [graphify-out/cache/ast/v0.9.8/5a8583914db9942cf8d5c003f51ca6a844ad08e74424fe1347ab546d226c67dd.json](graphify-out/cache/ast/v0.9.8/5a8583914db9942cf8d5c003f51ca6a844ad08e74424fe1347ab546d226c67dd.json) |  | 2026-07-08 | 92KB | `0fe58612` |
| [graphify-out/cache/ast/v0.9.8/5aa521c3d4ced0a307c27e2d2f8ed7bfc4dda052e9d7b791c02a2e722e0279b7.json](graphify-out/cache/ast/v0.9.8/5aa521c3d4ced0a307c27e2d2f8ed7bfc4dda052e9d7b791c02a2e722e0279b7.json) |  | 2026-07-08 | 13KB | `7472dcd2` |
| [graphify-out/cache/ast/v0.9.8/5ab417a08b4cc10afc86238e2a8840356c7babdbd5e6308d59d51eada84d19e3.json](graphify-out/cache/ast/v0.9.8/5ab417a08b4cc10afc86238e2a8840356c7babdbd5e6308d59d51eada84d19e3.json) |  | 2026-07-30 | 7KB | `59a44653` |
| [graphify-out/cache/ast/v0.9.8/5ac9c207b4c13430c69d7d956ae18a1389ec7b2ecb7ee0c51c06f3d4dc66897f.json](graphify-out/cache/ast/v0.9.8/5ac9c207b4c13430c69d7d956ae18a1389ec7b2ecb7ee0c51c06f3d4dc66897f.json) |  | 2026-07-08 | 8KB | `47100a7e` |
| [graphify-out/cache/ast/v0.9.8/5b0c1fce48a1feaa5dfde91e09acde3fcc16a85af028fd4fb26af0826db46080.json](graphify-out/cache/ast/v0.9.8/5b0c1fce48a1feaa5dfde91e09acde3fcc16a85af028fd4fb26af0826db46080.json) |  | 2026-07-22 | 6KB | `27be8747` |
| [graphify-out/cache/ast/v0.9.8/5b2cca1ba0dce2f2044d8043eb264155bbc2f36f54b97f5ce85d994c6dd66d00.json](graphify-out/cache/ast/v0.9.8/5b2cca1ba0dce2f2044d8043eb264155bbc2f36f54b97f5ce85d994c6dd66d00.json) |  | 2026-07-08 | 33KB | `5d02d8b5` |
| [graphify-out/cache/ast/v0.9.8/5b515d0e74b8bd44a1c1f9bf824db61797c2980d32880acafc3a41ec1b941ec1.json](graphify-out/cache/ast/v0.9.8/5b515d0e74b8bd44a1c1f9bf824db61797c2980d32880acafc3a41ec1b941ec1.json) |  | 2026-07-08 | 40KB | `3978c176` |
| [graphify-out/cache/ast/v0.9.8/5b72acd11e9926d8aa52b79ea10b3cc51ccaff10fb649af27cd54ff5b37a0649.json](graphify-out/cache/ast/v0.9.8/5b72acd11e9926d8aa52b79ea10b3cc51ccaff10fb649af27cd54ff5b37a0649.json) |  | 2026-07-08 | 3KB | `3097a102` |
| [graphify-out/cache/ast/v0.9.8/5ba48e3a2d3b011ae78268f3b4a0515b96c24721dbf808388bcc4f0f8e03876d.json](graphify-out/cache/ast/v0.9.8/5ba48e3a2d3b011ae78268f3b4a0515b96c24721dbf808388bcc4f0f8e03876d.json) |  | 2026-08-01 | 9KB | `a806347a` |
| [graphify-out/cache/ast/v0.9.8/5bb46c3dbc51d32468d3b44ae24f597c45527b6f40772117011b8e66f043d2ca.json](graphify-out/cache/ast/v0.9.8/5bb46c3dbc51d32468d3b44ae24f597c45527b6f40772117011b8e66f043d2ca.json) |  | 2026-07-08 | 16KB | `c177c70e` |
| [graphify-out/cache/ast/v0.9.8/5c072eb9a8459e4c3d46c44bf5c1689cbb9051c1c9f1517fd7bef365e417ef87.json](graphify-out/cache/ast/v0.9.8/5c072eb9a8459e4c3d46c44bf5c1689cbb9051c1c9f1517fd7bef365e417ef87.json) |  | 2026-07-08 | 144KB | `770bb3a0` |
| [graphify-out/cache/ast/v0.9.8/5c2fa6a5da873a9dc3affb85d3e5d280d0093f5b7199e2e79457b25d2dce7e16.json](graphify-out/cache/ast/v0.9.8/5c2fa6a5da873a9dc3affb85d3e5d280d0093f5b7199e2e79457b25d2dce7e16.json) |  | 2026-07-08 | 15KB | `d2e17264` |
| [graphify-out/cache/ast/v0.9.8/5c8d96e5a895743462264c7bba5c783aacef3c6e5b56f8d175c2ce0006920fd5.json](graphify-out/cache/ast/v0.9.8/5c8d96e5a895743462264c7bba5c783aacef3c6e5b56f8d175c2ce0006920fd5.json) |  | 2026-07-08 | 21KB | `5ed18c85` |
| [graphify-out/cache/ast/v0.9.8/5c956d0e73d7960f5c80da790314b06186558f94835db867db6e4c0d11476a77.json](graphify-out/cache/ast/v0.9.8/5c956d0e73d7960f5c80da790314b06186558f94835db867db6e4c0d11476a77.json) |  | 2026-07-08 | 7KB | `e2d875f0` |
| [graphify-out/cache/ast/v0.9.8/5cc188cdb378380cbd30dc99729a6d14b6210cef7568795d0cc2ed524fccc1fe.json](graphify-out/cache/ast/v0.9.8/5cc188cdb378380cbd30dc99729a6d14b6210cef7568795d0cc2ed524fccc1fe.json) |  | 2026-07-08 | 5KB | `8363e026` |
| [graphify-out/cache/ast/v0.9.8/5cc2b25df94f00f1a0b21eaaacdf5bd9fbed7e745ab98ab418bd3f6039a4e11b.json](graphify-out/cache/ast/v0.9.8/5cc2b25df94f00f1a0b21eaaacdf5bd9fbed7e745ab98ab418bd3f6039a4e11b.json) |  | 2026-07-08 | 8KB | `aa4c316d` |
| [graphify-out/cache/ast/v0.9.8/5ccd1d92a23d98b5d2d8901f0965a982821b8057bacb0d394cfd4b229af0bcd6.json](graphify-out/cache/ast/v0.9.8/5ccd1d92a23d98b5d2d8901f0965a982821b8057bacb0d394cfd4b229af0bcd6.json) |  | 2026-07-08 | 28KB | `e5249339` |
| [graphify-out/cache/ast/v0.9.8/5ce6b633e69c50faaa48241b82db9e89fc416ba77f67f8b33c41f4479fa1036a.json](graphify-out/cache/ast/v0.9.8/5ce6b633e69c50faaa48241b82db9e89fc416ba77f67f8b33c41f4479fa1036a.json) |  | 2026-07-08 | 31KB | `1fb4ef4b` |
| [graphify-out/cache/ast/v0.9.8/5ceb9608dda89f06dd2e1b25928315f6be0c0ef1d12f716a7e924406ff969e7f.json](graphify-out/cache/ast/v0.9.8/5ceb9608dda89f06dd2e1b25928315f6be0c0ef1d12f716a7e924406ff969e7f.json) |  | 2026-07-07 | 18KB | `4daeb221` |
| [graphify-out/cache/ast/v0.9.8/5cf95416a15dcfd40f95ab2a67ab7edfade00a469e19631d404c945c27331abe.json](graphify-out/cache/ast/v0.9.8/5cf95416a15dcfd40f95ab2a67ab7edfade00a469e19631d404c945c27331abe.json) |  | 2026-07-29 | 5KB | `fdcddb35` |
| [graphify-out/cache/ast/v0.9.8/5d105bdb543c3dbd537460d0e097d5488517ab0a21e0e1e520513f43670b95f1.json](graphify-out/cache/ast/v0.9.8/5d105bdb543c3dbd537460d0e097d5488517ab0a21e0e1e520513f43670b95f1.json) |  | 2026-07-08 | 4KB | `eb4f7cc2` |
| [graphify-out/cache/ast/v0.9.8/5da08e41064a8331a70ff81ecea7ec4992adf9a62f2a2274dd89867e148b5a96.json](graphify-out/cache/ast/v0.9.8/5da08e41064a8331a70ff81ecea7ec4992adf9a62f2a2274dd89867e148b5a96.json) |  | 2026-07-07 | 820B | `391e47cf` |
| [graphify-out/cache/ast/v0.9.8/5dded1c30dc278325d596be2e524f3fcf3fd6b77f015f2cf8f6aa6b2d6e72654.json](graphify-out/cache/ast/v0.9.8/5dded1c30dc278325d596be2e524f3fcf3fd6b77f015f2cf8f6aa6b2d6e72654.json) |  | 2026-07-08 | 20KB | `39bebe28` |
| [graphify-out/cache/ast/v0.9.8/5df11efcf8155016a490d81626e8f203c1bc586d3b817920bde7c7980e94f8c1.json](graphify-out/cache/ast/v0.9.8/5df11efcf8155016a490d81626e8f203c1bc586d3b817920bde7c7980e94f8c1.json) |  | 2026-07-08 | 6KB | `ff596df8` |
| [graphify-out/cache/ast/v0.9.8/5e8126731af6e88a1cd2afde54b6995a64fd7453d120e8dd17400f6e0baffbf8.json](graphify-out/cache/ast/v0.9.8/5e8126731af6e88a1cd2afde54b6995a64fd7453d120e8dd17400f6e0baffbf8.json) |  | 2026-07-29 | 13KB | `b294bdd4` |
| [graphify-out/cache/ast/v0.9.8/5ea3a7725ed35747757032c7ef184988ce07bf3326d6290896db08ab3a7ada47.json](graphify-out/cache/ast/v0.9.8/5ea3a7725ed35747757032c7ef184988ce07bf3326d6290896db08ab3a7ada47.json) |  | 2026-07-07 | 4KB | `e6cec6b2` |
| [graphify-out/cache/ast/v0.9.8/5ed52418ddc6561bc32f7328f59be55f7986a565693cf8662dbc7c617df04f9e.json](graphify-out/cache/ast/v0.9.8/5ed52418ddc6561bc32f7328f59be55f7986a565693cf8662dbc7c617df04f9e.json) |  | 2026-07-07 | 21KB | `d78679e5` |
| [graphify-out/cache/ast/v0.9.8/5f10746f8ff4c0acf951ada19fb80dd6943044f881f2b43d6c4ea9b436563b83.json](graphify-out/cache/ast/v0.9.8/5f10746f8ff4c0acf951ada19fb80dd6943044f881f2b43d6c4ea9b436563b83.json) |  | 2026-07-08 | 21KB | `733d9c78` |
| [graphify-out/cache/ast/v0.9.8/5f5c4f104e6c8b42dc8c0378208b13a4ddf78fe74f75fd12901b3173b884ac86.json](graphify-out/cache/ast/v0.9.8/5f5c4f104e6c8b42dc8c0378208b13a4ddf78fe74f75fd12901b3173b884ac86.json) |  | 2026-07-08 | 62KB | `1513567d` |
| [graphify-out/cache/ast/v0.9.8/5f821ed11d7e73eba466e25129f93330cf5eaabb2f9f5d7cdda7eb24cf15f3b3.json](graphify-out/cache/ast/v0.9.8/5f821ed11d7e73eba466e25129f93330cf5eaabb2f9f5d7cdda7eb24cf15f3b3.json) |  | 2026-07-08 | 7KB | `2e700703` |
| [graphify-out/cache/ast/v0.9.8/5fbce562fa58997f3279a0f8562a2e547a9e52273b1fd2e93438395bfe33a4a9.json](graphify-out/cache/ast/v0.9.8/5fbce562fa58997f3279a0f8562a2e547a9e52273b1fd2e93438395bfe33a4a9.json) |  | 2026-07-31 | 9KB | `a4d37e0e` |
| [graphify-out/cache/ast/v0.9.8/5fcfc3c53ad53fe4b4af4c2632d672b43ef3f6b78dc64d329ebd38618d71efbd.json](graphify-out/cache/ast/v0.9.8/5fcfc3c53ad53fe4b4af4c2632d672b43ef3f6b78dc64d329ebd38618d71efbd.json) |  | 2026-07-07 | 16KB | `47b35a1d` |
| [graphify-out/cache/ast/v0.9.8/60507c8767cb902890525331046983a1dd89e81c57ef5246ae274a936ac23a79.json](graphify-out/cache/ast/v0.9.8/60507c8767cb902890525331046983a1dd89e81c57ef5246ae274a936ac23a79.json) |  | 2026-07-22 | 50KB | `913e9f14` |
| [graphify-out/cache/ast/v0.9.8/608d8b06105945f65f29048fbabf9682e2a7684cd402d79a5834900efbb49f67.json](graphify-out/cache/ast/v0.9.8/608d8b06105945f65f29048fbabf9682e2a7684cd402d79a5834900efbb49f67.json) |  | 2026-07-08 | 2KB | `37523c62` |
| [graphify-out/cache/ast/v0.9.8/60d2b36f5decf1a0723b27d049dc556816f5528ab9a53b952e44b75c0db5b931.json](graphify-out/cache/ast/v0.9.8/60d2b36f5decf1a0723b27d049dc556816f5528ab9a53b952e44b75c0db5b931.json) |  | 2026-07-07 | 16KB | `ac8e6327` |
| [graphify-out/cache/ast/v0.9.8/60d7f75a2b371d9f8b98580080a5edf44124bd03c6a0d08e3a2bd8cae99d9a80.json](graphify-out/cache/ast/v0.9.8/60d7f75a2b371d9f8b98580080a5edf44124bd03c6a0d08e3a2bd8cae99d9a80.json) |  | 2026-07-22 | 7KB | `16f395de` |
| [graphify-out/cache/ast/v0.9.8/60ef7cb74a5e4c874ab314a979bc364af67762183a3f0499ff1e679d3f0a1a8c.json](graphify-out/cache/ast/v0.9.8/60ef7cb74a5e4c874ab314a979bc364af67762183a3f0499ff1e679d3f0a1a8c.json) |  | 2026-07-08 | 87KB | `a5b2646f` |
| [graphify-out/cache/ast/v0.9.8/60f0535d9c33f83b20ec7f816543197b9909a6062aebee4bd94ab44d749ace20.json](graphify-out/cache/ast/v0.9.8/60f0535d9c33f83b20ec7f816543197b9909a6062aebee4bd94ab44d749ace20.json) |  | 2026-07-08 | 15KB | `d5614715` |
| [graphify-out/cache/ast/v0.9.8/616adb19748f0341339920c9d03b0eca9df6332fd354f4acd7661b7e15ac67b4.json](graphify-out/cache/ast/v0.9.8/616adb19748f0341339920c9d03b0eca9df6332fd354f4acd7661b7e15ac67b4.json) |  | 2026-07-08 | 10KB | `89261532` |
| [graphify-out/cache/ast/v0.9.8/61c2cf39df16e8132fa1cfbe1ac05243de982548c170155631fc53111ebd90d2.json](graphify-out/cache/ast/v0.9.8/61c2cf39df16e8132fa1cfbe1ac05243de982548c170155631fc53111ebd90d2.json) |  | 2026-07-24 | 78KB | `d529dffb` |
| [graphify-out/cache/ast/v0.9.8/61c2fe4c1400f452ae556c26cbd3676432d47b2ce77f0ad57a09cd2144ad61a3.json](graphify-out/cache/ast/v0.9.8/61c2fe4c1400f452ae556c26cbd3676432d47b2ce77f0ad57a09cd2144ad61a3.json) |  | 2026-07-08 | 3KB | `699586ff` |
| [graphify-out/cache/ast/v0.9.8/61e77ce7f62d7a73fc62e40338ed026706c732e8503d82d72e14cc01e0e8b47d.json](graphify-out/cache/ast/v0.9.8/61e77ce7f62d7a73fc62e40338ed026706c732e8503d82d72e14cc01e0e8b47d.json) |  | 2026-07-08 | 10KB | `e00ff336` |
| [graphify-out/cache/ast/v0.9.8/6204403545072e545f67251e27bd293f579973a8444173efe43d57836f214f02.json](graphify-out/cache/ast/v0.9.8/6204403545072e545f67251e27bd293f579973a8444173efe43d57836f214f02.json) |  | 2026-07-07 | 41KB | `7fb8275c` |
| [graphify-out/cache/ast/v0.9.8/6214ae76a414f3f30e1d7fe60ef275c13c6cd245d40f1f9f4d836723fa4c1139.json](graphify-out/cache/ast/v0.9.8/6214ae76a414f3f30e1d7fe60ef275c13c6cd245d40f1f9f4d836723fa4c1139.json) |  | 2026-07-08 | 3KB | `8a5f5bf2` |
| [graphify-out/cache/ast/v0.9.8/621b1e0d815a6a83c16ff6234a35c1a78609dab6061ddb78327df8e630ceb33f.json](graphify-out/cache/ast/v0.9.8/621b1e0d815a6a83c16ff6234a35c1a78609dab6061ddb78327df8e630ceb33f.json) |  | 2026-07-08 | 17KB | `f4d49076` |
| [graphify-out/cache/ast/v0.9.8/6230c3177b913244740085c2a6c487d85afb3ca67b31f456646cc9fb29d6982c.json](graphify-out/cache/ast/v0.9.8/6230c3177b913244740085c2a6c487d85afb3ca67b31f456646cc9fb29d6982c.json) |  | 2026-07-09 | 8KB | `8155ea7f` |
| [graphify-out/cache/ast/v0.9.8/6275e90b2d5bc964eca193312233a9aaadc4d6d32a83d7caeb3bf35bf362817d.json](graphify-out/cache/ast/v0.9.8/6275e90b2d5bc964eca193312233a9aaadc4d6d32a83d7caeb3bf35bf362817d.json) |  | 2026-07-08 | 19KB | `e6ba8dd5` |
| [graphify-out/cache/ast/v0.9.8/629974d767afb5b67572a4b2aca49a8a474ad282a4ab6be95461de40d4b18f41.json](graphify-out/cache/ast/v0.9.8/629974d767afb5b67572a4b2aca49a8a474ad282a4ab6be95461de40d4b18f41.json) |  | 2026-07-07 | 6KB | `b632a389` |
| [graphify-out/cache/ast/v0.9.8/62c3cf8c7038a6b3653baa63a71d47b5fdbf7e15b002e876247faebd6ace4270.json](graphify-out/cache/ast/v0.9.8/62c3cf8c7038a6b3653baa63a71d47b5fdbf7e15b002e876247faebd6ace4270.json) |  | 2026-07-08 | 7KB | `ba8839f3` |
| [graphify-out/cache/ast/v0.9.8/62c56123978dd2030c0039eff315f6a7bb2ba0a2c20dfb1604cf3b436d8ea81c.json](graphify-out/cache/ast/v0.9.8/62c56123978dd2030c0039eff315f6a7bb2ba0a2c20dfb1604cf3b436d8ea81c.json) |  | 2026-07-07 | 157KB | `21630ac5` |
| [graphify-out/cache/ast/v0.9.8/630e06237384d9ce395eda923884335982725b3bace562455a73b790dd37dbc0.json](graphify-out/cache/ast/v0.9.8/630e06237384d9ce395eda923884335982725b3bace562455a73b790dd37dbc0.json) |  | 2026-07-08 | 16KB | `5460a167` |
| [graphify-out/cache/ast/v0.9.8/634b65d343e6c123379f102a604a551ffcfc2d863f981a6dca7db72abbdc89a7.json](graphify-out/cache/ast/v0.9.8/634b65d343e6c123379f102a604a551ffcfc2d863f981a6dca7db72abbdc89a7.json) |  | 2026-07-08 | 30KB | `41be37d8` |
| [graphify-out/cache/ast/v0.9.8/6359016871090100e6a10f0054cb5deedb22a8d8b03a8bc5f3b770cfae209c45.json](graphify-out/cache/ast/v0.9.8/6359016871090100e6a10f0054cb5deedb22a8d8b03a8bc5f3b770cfae209c45.json) |  | 2026-07-07 | 21KB | `d7f51732` |
| [graphify-out/cache/ast/v0.9.8/638f2ce016454562ffb43565b849fd203439317af1c1a2d53f2727f441dc96dc.json](graphify-out/cache/ast/v0.9.8/638f2ce016454562ffb43565b849fd203439317af1c1a2d53f2727f441dc96dc.json) |  | 2026-07-08 | 24KB | `97e0d86c` |
| [graphify-out/cache/ast/v0.9.8/64063edb67184b66002b946d216d1e3f2a6417231d0514e4134cbc9a83173a7f.json](graphify-out/cache/ast/v0.9.8/64063edb67184b66002b946d216d1e3f2a6417231d0514e4134cbc9a83173a7f.json) |  | 2026-07-08 | 10KB | `3087119b` |
| [graphify-out/cache/ast/v0.9.8/6416c59e93774dcd2dc49e6360444599d737ee6c092d79c635a5c65ded064ea9.json](graphify-out/cache/ast/v0.9.8/6416c59e93774dcd2dc49e6360444599d737ee6c092d79c635a5c65ded064ea9.json) |  | 2026-07-08 | 3KB | `045ecc24` |
| [graphify-out/cache/ast/v0.9.8/643cc4ffe27c6856de2fd41f7326872a3232fcf6c21708efd2b078ae2ba410e9.json](graphify-out/cache/ast/v0.9.8/643cc4ffe27c6856de2fd41f7326872a3232fcf6c21708efd2b078ae2ba410e9.json) |  | 2026-07-08 | 29KB | `31da9d01` |
| [graphify-out/cache/ast/v0.9.8/645580a1bca9fe7b3471cc5e14756be3419b6f128307d38cb5ff2a88f42dde35.json](graphify-out/cache/ast/v0.9.8/645580a1bca9fe7b3471cc5e14756be3419b6f128307d38cb5ff2a88f42dde35.json) |  | 2026-07-24 | 112KB | `8ca6b33a` |
| [graphify-out/cache/ast/v0.9.8/64ca540323538e7c4bb60e066fa36293101454dbeb7c6dd81bc6e560d8269ee4.json](graphify-out/cache/ast/v0.9.8/64ca540323538e7c4bb60e066fa36293101454dbeb7c6dd81bc6e560d8269ee4.json) |  | 2026-07-31 | 16KB | `bf82ce1c` |
| [graphify-out/cache/ast/v0.9.8/64d0c76070200c467b7c5adb850f509e00c75c1a3f69fb12556d92015b403db6.json](graphify-out/cache/ast/v0.9.8/64d0c76070200c467b7c5adb850f509e00c75c1a3f69fb12556d92015b403db6.json) |  | 2026-07-07 | 11KB | `e0e9647c` |
| [graphify-out/cache/ast/v0.9.8/64dbbc20f170c6cdd662ba8b0eabc90d948d39e2fc6e311b05039b598cd98df2.json](graphify-out/cache/ast/v0.9.8/64dbbc20f170c6cdd662ba8b0eabc90d948d39e2fc6e311b05039b598cd98df2.json) |  | 2026-07-30 | 17KB | `e30ab7db` |
| [graphify-out/cache/ast/v0.9.8/64e034e4170230b2afb1eace0e355878a4ce7c5fbddbaf9fcd5cfff4022343cb.json](graphify-out/cache/ast/v0.9.8/64e034e4170230b2afb1eace0e355878a4ce7c5fbddbaf9fcd5cfff4022343cb.json) |  | 2026-07-08 | 157KB | `ff289375` |
| [graphify-out/cache/ast/v0.9.8/6513c5e9e9faaa91e32787c714fe67d8e5478c9453646de5a84a17f008cca720.json](graphify-out/cache/ast/v0.9.8/6513c5e9e9faaa91e32787c714fe67d8e5478c9453646de5a84a17f008cca720.json) |  | 2026-07-08 | 17KB | `edaa8b0e` |
| [graphify-out/cache/ast/v0.9.8/652374ebed9aa26dc9b21816aa2ba6964aa6f6f19ee539038e2f5e78a59e3435.json](graphify-out/cache/ast/v0.9.8/652374ebed9aa26dc9b21816aa2ba6964aa6f6f19ee539038e2f5e78a59e3435.json) |  | 2026-07-08 | 12KB | `aecc5a5f` |
| [graphify-out/cache/ast/v0.9.8/655da4a54f3e8e565e841df59e9c0e1f956f50d15974baf8a4a6319918216ced.json](graphify-out/cache/ast/v0.9.8/655da4a54f3e8e565e841df59e9c0e1f956f50d15974baf8a4a6319918216ced.json) |  | 2026-07-08 | 9KB | `68629449` |
| [graphify-out/cache/ast/v0.9.8/65d507b234fc41a165f04499e95d2fbe3312e821a85b60ebaaded384eb12f02c.json](graphify-out/cache/ast/v0.9.8/65d507b234fc41a165f04499e95d2fbe3312e821a85b60ebaaded384eb12f02c.json) |  | 2026-07-08 | 18KB | `b4e18f9a` |
| [graphify-out/cache/ast/v0.9.8/6626ead3e8a7b18fd62d2f0615fca58c9f8c5b2f53a7818ca01153e7ac2ca7cc.json](graphify-out/cache/ast/v0.9.8/6626ead3e8a7b18fd62d2f0615fca58c9f8c5b2f53a7818ca01153e7ac2ca7cc.json) |  | 2026-07-08 | 7KB | `ef7f9f29` |
| [graphify-out/cache/ast/v0.9.8/66375d86e06b5aff6c3e80aeb9dc0ba68a2b86ad7e37417c83fa56b9e55f17c8.json](graphify-out/cache/ast/v0.9.8/66375d86e06b5aff6c3e80aeb9dc0ba68a2b86ad7e37417c83fa56b9e55f17c8.json) |  | 2026-07-08 | 4KB | `f3f3218d` |
| [graphify-out/cache/ast/v0.9.8/66a1346195366c12e866a6cfe031e908e010168d69d3dae74f55fd3d1e71ca9a.json](graphify-out/cache/ast/v0.9.8/66a1346195366c12e866a6cfe031e908e010168d69d3dae74f55fd3d1e71ca9a.json) |  | 2026-07-08 | 10KB | `74c2c991` |
| [graphify-out/cache/ast/v0.9.8/66ab8d72d92a87e99f946a22a0141f312727e25e837c916be301679c94662ebb.json](graphify-out/cache/ast/v0.9.8/66ab8d72d92a87e99f946a22a0141f312727e25e837c916be301679c94662ebb.json) |  | 2026-07-29 | 8KB | `10a203e1` |
| [graphify-out/cache/ast/v0.9.8/66e30844e1693ae1a4a826e79ac67b77f8fe6d77d12fbf030a679e480b1cbed5.json](graphify-out/cache/ast/v0.9.8/66e30844e1693ae1a4a826e79ac67b77f8fe6d77d12fbf030a679e480b1cbed5.json) |  | 2026-07-08 | 9KB | `1ba787ec` |
| [graphify-out/cache/ast/v0.9.8/677d62db8f0cbb5175598707950ffff428483c73c1e21b0ffb77e378d51f9d8c.json](graphify-out/cache/ast/v0.9.8/677d62db8f0cbb5175598707950ffff428483c73c1e21b0ffb77e378d51f9d8c.json) |  | 2026-07-08 | 15KB | `ab96ee34` |
| [graphify-out/cache/ast/v0.9.8/67be740985d7b214d2a4164130dff4b31cd8640f9b2776f5c09e9bad18221e72.json](graphify-out/cache/ast/v0.9.8/67be740985d7b214d2a4164130dff4b31cd8640f9b2776f5c09e9bad18221e72.json) |  | 2026-07-08 | 10KB | `351382a6` |
| [graphify-out/cache/ast/v0.9.8/67dd692d1e4ff1ade85d9dc1bfcb59b67373bb2ca8f026a68d410f181a2911c7.json](graphify-out/cache/ast/v0.9.8/67dd692d1e4ff1ade85d9dc1bfcb59b67373bb2ca8f026a68d410f181a2911c7.json) |  | 2026-07-09 | 10KB | `9f263f76` |
| [graphify-out/cache/ast/v0.9.8/67f56f42f3da41e3ff993ed1ead858a8f9245ed2979ddd2ea04d0c18f52ce21b.json](graphify-out/cache/ast/v0.9.8/67f56f42f3da41e3ff993ed1ead858a8f9245ed2979ddd2ea04d0c18f52ce21b.json) |  | 2026-07-07 | 13KB | `b0373354` |
| [graphify-out/cache/ast/v0.9.8/681e60c795a924a73eaa35308c344421798a0ca458029a0b6ce0b628d3c77d5c.json](graphify-out/cache/ast/v0.9.8/681e60c795a924a73eaa35308c344421798a0ca458029a0b6ce0b628d3c77d5c.json) |  | 2026-07-20 | 8KB | `f1ee30ab` |
| [graphify-out/cache/ast/v0.9.8/682a76fd00e4b61dcbd7e930bdc2e0e6f00d62f317fbbbc036e9ffc2520b2326.json](graphify-out/cache/ast/v0.9.8/682a76fd00e4b61dcbd7e930bdc2e0e6f00d62f317fbbbc036e9ffc2520b2326.json) |  | 2026-07-07 | 17KB | `d6eee104` |
| [graphify-out/cache/ast/v0.9.8/68f0a5e9d11a5051fc9da33403f949c012f94af60071ec76ddbf9ca69d88d033.json](graphify-out/cache/ast/v0.9.8/68f0a5e9d11a5051fc9da33403f949c012f94af60071ec76ddbf9ca69d88d033.json) |  | 2026-07-07 | 11KB | `656afc41` |
| [graphify-out/cache/ast/v0.9.8/68ff5ac03917dc11a70ddf09b0b8ed2b73fc566163859162f0f4490a7bcc414f.json](graphify-out/cache/ast/v0.9.8/68ff5ac03917dc11a70ddf09b0b8ed2b73fc566163859162f0f4490a7bcc414f.json) |  | 2026-07-08 | 5KB | `c09ff43c` |
| [graphify-out/cache/ast/v0.9.8/69564116aa39838dd9a59dc1edb637c2e1d2abfdfcbd62687c9dae6fe6ac31ed.json](graphify-out/cache/ast/v0.9.8/69564116aa39838dd9a59dc1edb637c2e1d2abfdfcbd62687c9dae6fe6ac31ed.json) |  | 2026-07-08 | 1KB | `9f5b840c` |
| [graphify-out/cache/ast/v0.9.8/69fe903ae28cad73edbcea3da0ef990917892b731d38497626c20f133145a07f.json](graphify-out/cache/ast/v0.9.8/69fe903ae28cad73edbcea3da0ef990917892b731d38497626c20f133145a07f.json) |  | 2026-07-07 | 28KB | `9d159898` |
| [graphify-out/cache/ast/v0.9.8/6a219cc1c91a891f405a00e966568433249ca90e4392a5fbd200a36afc9b6a73.json](graphify-out/cache/ast/v0.9.8/6a219cc1c91a891f405a00e966568433249ca90e4392a5fbd200a36afc9b6a73.json) |  | 2026-07-08 | 11KB | `80625ea6` |
| [graphify-out/cache/ast/v0.9.8/6a4f1aaf81a73a74b9b2eec049a717fcac5282080506655808d2f94f4356dbeb.json](graphify-out/cache/ast/v0.9.8/6a4f1aaf81a73a74b9b2eec049a717fcac5282080506655808d2f94f4356dbeb.json) |  | 2026-07-08 | 45KB | `e957677b` |
| [graphify-out/cache/ast/v0.9.8/6addd8690b5536652c48185a5af6676e17b806722c7c8601f44fb8c515c2b60c.json](graphify-out/cache/ast/v0.9.8/6addd8690b5536652c48185a5af6676e17b806722c7c8601f44fb8c515c2b60c.json) |  | 2026-07-08 | 15KB | `53d3d377` |
| [graphify-out/cache/ast/v0.9.8/6b1d2f3f6f0f7149e0627a874c47f0cfe4817d489a19e362ff99e899a5209587.json](graphify-out/cache/ast/v0.9.8/6b1d2f3f6f0f7149e0627a874c47f0cfe4817d489a19e362ff99e899a5209587.json) |  | 2026-07-08 | 10KB | `8d9968c2` |
| [graphify-out/cache/ast/v0.9.8/6b2bb331c335f4f1ad8f649e97a2b815de962f40b401c92b42dc4ef2fd59218d.json](graphify-out/cache/ast/v0.9.8/6b2bb331c335f4f1ad8f649e97a2b815de962f40b401c92b42dc4ef2fd59218d.json) |  | 2026-07-08 | 3KB | `b52a1a35` |
| [graphify-out/cache/ast/v0.9.8/6bbee8dbf6dbee96126cd70a32f77752844ccd03d3d5e88cb0aabb959a700d1c.json](graphify-out/cache/ast/v0.9.8/6bbee8dbf6dbee96126cd70a32f77752844ccd03d3d5e88cb0aabb959a700d1c.json) |  | 2026-07-27 | 71KB | `9dd28c90` |
| [graphify-out/cache/ast/v0.9.8/6bccf4ef27071a7f4f8267cc65df892a7fd9bcfa462809f493d254bd9dd27e9b.json](graphify-out/cache/ast/v0.9.8/6bccf4ef27071a7f4f8267cc65df892a7fd9bcfa462809f493d254bd9dd27e9b.json) |  | 2026-07-08 | 16KB | `ab393df7` |
| [graphify-out/cache/ast/v0.9.8/6bd4028af0b36f64f206327ba07731bb43349e0753f06bacd984c8c9de805466.json](graphify-out/cache/ast/v0.9.8/6bd4028af0b36f64f206327ba07731bb43349e0753f06bacd984c8c9de805466.json) |  | 2026-07-08 | 23KB | `e091dad1` |
| [graphify-out/cache/ast/v0.9.8/6c42954c70832804591708bdc80fb56d1ea62cec299824f62ec8ef613506a430.json](graphify-out/cache/ast/v0.9.8/6c42954c70832804591708bdc80fb56d1ea62cec299824f62ec8ef613506a430.json) |  | 2026-07-08 | 15KB | `26f7492c` |
| [graphify-out/cache/ast/v0.9.8/6c6127341bad689e0d78f11be28a7dcc53c9034bf9230516cdeda512f6fdc3c7.json](graphify-out/cache/ast/v0.9.8/6c6127341bad689e0d78f11be28a7dcc53c9034bf9230516cdeda512f6fdc3c7.json) |  | 2026-07-08 | 18KB | `5febf2b9` |
| [graphify-out/cache/ast/v0.9.8/6ccd058103c9ba5f2d0f7dc3fde354a2db6998d2096a601f0b042885d99f964a.json](graphify-out/cache/ast/v0.9.8/6ccd058103c9ba5f2d0f7dc3fde354a2db6998d2096a601f0b042885d99f964a.json) |  | 2026-07-07 | 10KB | `7df29ef4` |
| [graphify-out/cache/ast/v0.9.8/6d26a72edb665f341a80d031babae09ec14ea18db3730a8e26d6023dfa73a61c.json](graphify-out/cache/ast/v0.9.8/6d26a72edb665f341a80d031babae09ec14ea18db3730a8e26d6023dfa73a61c.json) |  | 2026-07-08 | 16KB | `cd72535c` |
| [graphify-out/cache/ast/v0.9.8/6d318a76e2ca00afd7d6211ef08979698f4a18b210b96b0f32e0d27c6286754d.json](graphify-out/cache/ast/v0.9.8/6d318a76e2ca00afd7d6211ef08979698f4a18b210b96b0f32e0d27c6286754d.json) |  | 2026-07-24 | 9KB | `d574de49` |
| [graphify-out/cache/ast/v0.9.8/6d3ac3db55cd1e79152f5c223095c15c0f0ee414254cca6672c82b4e0754364c.json](graphify-out/cache/ast/v0.9.8/6d3ac3db55cd1e79152f5c223095c15c0f0ee414254cca6672c82b4e0754364c.json) |  | 2026-07-08 | 95KB | `45245f80` |
| [graphify-out/cache/ast/v0.9.8/6d3ea2a20ff35c5b15c4e288ed7b21c1ac84cd4615f006fce440297503e74714.json](graphify-out/cache/ast/v0.9.8/6d3ea2a20ff35c5b15c4e288ed7b21c1ac84cd4615f006fce440297503e74714.json) |  | 2026-07-08 | 3KB | `53377806` |
| [graphify-out/cache/ast/v0.9.8/6d4c0e1426fdeaee8a7ca8a50e06578cfb57d5d1c4a936cabe2c887e800a932e.json](graphify-out/cache/ast/v0.9.8/6d4c0e1426fdeaee8a7ca8a50e06578cfb57d5d1c4a936cabe2c887e800a932e.json) |  | 2026-07-08 | 63KB | `a80d6fa1` |
| [graphify-out/cache/ast/v0.9.8/6d8adb100a382634ca065c5005eb2a4f143caf324f63811f7a0fafc672aaeb25.json](graphify-out/cache/ast/v0.9.8/6d8adb100a382634ca065c5005eb2a4f143caf324f63811f7a0fafc672aaeb25.json) |  | 2026-07-08 | 8KB | `2e6f1aa6` |
| [graphify-out/cache/ast/v0.9.8/6e5588b5ed974d05d9308594fc162fad11bcf47165c190380f3d4a21ddf6ba08.json](graphify-out/cache/ast/v0.9.8/6e5588b5ed974d05d9308594fc162fad11bcf47165c190380f3d4a21ddf6ba08.json) |  | 2026-07-08 | 15KB | `37b623f9` |
| [graphify-out/cache/ast/v0.9.8/6e55f0502b72e693e24278ef8d9f822794bd07d7ab9cea5040b72e5ff10a166b.json](graphify-out/cache/ast/v0.9.8/6e55f0502b72e693e24278ef8d9f822794bd07d7ab9cea5040b72e5ff10a166b.json) |  | 2026-07-29 | 16KB | `92261ed2` |
| [graphify-out/cache/ast/v0.9.8/6eac5e64d96cb4f907fc0bb3e2c9807032375d2081f1f998aa1e41f1a636b429.json](graphify-out/cache/ast/v0.9.8/6eac5e64d96cb4f907fc0bb3e2c9807032375d2081f1f998aa1e41f1a636b429.json) |  | 2026-07-07 | 44KB | `2c7b4140` |
| [graphify-out/cache/ast/v0.9.8/6ec449962db367d4fb55faf4be5a2fa4ef45f58a8011ff0ae02d57943c094b5c.json](graphify-out/cache/ast/v0.9.8/6ec449962db367d4fb55faf4be5a2fa4ef45f58a8011ff0ae02d57943c094b5c.json) |  | 2026-07-20 | 89KB | `26effd5c` |
| [graphify-out/cache/ast/v0.9.8/6ed138b6bfb398ded289fdb929bef755a1b2efb1cdc5d48f9209d26554cf6b04.json](graphify-out/cache/ast/v0.9.8/6ed138b6bfb398ded289fdb929bef755a1b2efb1cdc5d48f9209d26554cf6b04.json) |  | 2026-07-24 | 11KB | `e679f120` |
| [graphify-out/cache/ast/v0.9.8/6ed535f36401cdfc14e7154fa2923249344bec3c894740e5764b9107819d6f63.json](graphify-out/cache/ast/v0.9.8/6ed535f36401cdfc14e7154fa2923249344bec3c894740e5764b9107819d6f63.json) |  | 2026-07-08 | 11KB | `f01916be` |
| [graphify-out/cache/ast/v0.9.8/6edf13b76b558f00bdf47115adc1bdb58c6efc67f45ec26d4fad97cd5ebdc79d.json](graphify-out/cache/ast/v0.9.8/6edf13b76b558f00bdf47115adc1bdb58c6efc67f45ec26d4fad97cd5ebdc79d.json) |  | 2026-07-29 | 12KB | `890b4b84` |
| [graphify-out/cache/ast/v0.9.8/6f881c4850ba718d01ced28b028e8330e5895c701a20bb962d1f4c4a465a3330.json](graphify-out/cache/ast/v0.9.8/6f881c4850ba718d01ced28b028e8330e5895c701a20bb962d1f4c4a465a3330.json) |  | 2026-07-20 | 4KB | `49673589` |
| [graphify-out/cache/ast/v0.9.8/6fd8a07078fdf93f11abcb2513e16dcc725d049fc8d0bad63bf90c42c5bf682f.json](graphify-out/cache/ast/v0.9.8/6fd8a07078fdf93f11abcb2513e16dcc725d049fc8d0bad63bf90c42c5bf682f.json) |  | 2026-07-08 | 9KB | `b670a093` |
| [graphify-out/cache/ast/v0.9.8/700e215ce1b2b9ec8d84070e09639ea4ca4175900fa362b9f25be3e95a2b60e1.json](graphify-out/cache/ast/v0.9.8/700e215ce1b2b9ec8d84070e09639ea4ca4175900fa362b9f25be3e95a2b60e1.json) |  | 2026-07-22 | 69KB | `ed3f0f3b` |
| [graphify-out/cache/ast/v0.9.8/702f9c6362c3ac815ea7609703d4c152623cb692519b1cd96d2f7f2f78000c87.json](graphify-out/cache/ast/v0.9.8/702f9c6362c3ac815ea7609703d4c152623cb692519b1cd96d2f7f2f78000c87.json) |  | 2026-07-08 | 10KB | `45fe6a4b` |
| [graphify-out/cache/ast/v0.9.8/7045e07058d30f0b3b057998bf664570e7600fedd6b28aaa6d7528ce933d2e71.json](graphify-out/cache/ast/v0.9.8/7045e07058d30f0b3b057998bf664570e7600fedd6b28aaa6d7528ce933d2e71.json) |  | 2026-07-09 | 10KB | `e525ea42` |
| [graphify-out/cache/ast/v0.9.8/704788ac17d277997d22a65c1c3e3c314baacb470c4e62810fbace40a0f1bfd6.json](graphify-out/cache/ast/v0.9.8/704788ac17d277997d22a65c1c3e3c314baacb470c4e62810fbace40a0f1bfd6.json) |  | 2026-07-08 | 98KB | `7316b146` |
| [graphify-out/cache/ast/v0.9.8/706a8d13c003ce9e275d3675b150ba7d02f95d5751addf35f89a5b9ccf5d5aa6.json](graphify-out/cache/ast/v0.9.8/706a8d13c003ce9e275d3675b150ba7d02f95d5751addf35f89a5b9ccf5d5aa6.json) |  | 2026-07-08 | 35KB | `87eb6161` |
| [graphify-out/cache/ast/v0.9.8/709ef3982f0c8817dfa6bc6d081109343d2702e60ab60797541e9a185ae4ff86.json](graphify-out/cache/ast/v0.9.8/709ef3982f0c8817dfa6bc6d081109343d2702e60ab60797541e9a185ae4ff86.json) |  | 2026-07-08 | 35KB | `5e49b76c` |
| [graphify-out/cache/ast/v0.9.8/70dbab2b1670c39d1be5ce14addf50dafc951b1a7990b2a727713ebd93ccdcb9.json](graphify-out/cache/ast/v0.9.8/70dbab2b1670c39d1be5ce14addf50dafc951b1a7990b2a727713ebd93ccdcb9.json) |  | 2026-07-08 | 4KB | `fb7f96e3` |
| [graphify-out/cache/ast/v0.9.8/70fd302152490fdf9f412dd777b20563d31fd3468814a549f1e2fdd1c8e346d3.json](graphify-out/cache/ast/v0.9.8/70fd302152490fdf9f412dd777b20563d31fd3468814a549f1e2fdd1c8e346d3.json) |  | 2026-07-08 | 10KB | `3f7cf231` |
| [graphify-out/cache/ast/v0.9.8/7124c3e16b510c848773846f0ce4aa59432fae68450bf8677816e0b46830fc38.json](graphify-out/cache/ast/v0.9.8/7124c3e16b510c848773846f0ce4aa59432fae68450bf8677816e0b46830fc38.json) |  | 2026-07-08 | 11KB | `85d5454c` |
| [graphify-out/cache/ast/v0.9.8/7139d012adf8c39a9f1970278ccf0827ce058c8ecf6ccb33d1a3cbdba892775d.json](graphify-out/cache/ast/v0.9.8/7139d012adf8c39a9f1970278ccf0827ce058c8ecf6ccb33d1a3cbdba892775d.json) |  | 2026-07-08 | 11KB | `e7fe5972` |
| [graphify-out/cache/ast/v0.9.8/7144a5177aca58bbac2a1d41fff1a3fad3dfac443167838d5a49f3352e5254fd.json](graphify-out/cache/ast/v0.9.8/7144a5177aca58bbac2a1d41fff1a3fad3dfac443167838d5a49f3352e5254fd.json) |  | 2026-07-30 | 9KB | `330f823f` |
| [graphify-out/cache/ast/v0.9.8/715ccccfc4ec95f4ff48e98d34383fccbfa51a6b0eb780386f2e36352febb588.json](graphify-out/cache/ast/v0.9.8/715ccccfc4ec95f4ff48e98d34383fccbfa51a6b0eb780386f2e36352febb588.json) |  | 2026-07-07 | 20KB | `b0dc2c43` |
| [graphify-out/cache/ast/v0.9.8/7163c77607216b14ff7c88fc4d5ea347a0978892e68748e2ec9480cd01166ad8.json](graphify-out/cache/ast/v0.9.8/7163c77607216b14ff7c88fc4d5ea347a0978892e68748e2ec9480cd01166ad8.json) |  | 2026-07-30 | 3KB | `24885562` |
| [graphify-out/cache/ast/v0.9.8/7168a20fa9e39d4cc108567577e96d20e975952c264eebde2cd6b29dd51ababa.json](graphify-out/cache/ast/v0.9.8/7168a20fa9e39d4cc108567577e96d20e975952c264eebde2cd6b29dd51ababa.json) |  | 2026-07-08 | 4KB | `4f1d2fe1` |
| [graphify-out/cache/ast/v0.9.8/716cf998833baa505070e8a2433b45e018eac13e442bc9ecd9f91dc7f5cdcc93.json](graphify-out/cache/ast/v0.9.8/716cf998833baa505070e8a2433b45e018eac13e442bc9ecd9f91dc7f5cdcc93.json) |  | 2026-07-08 | 13KB | `8ae298b3` |
| [graphify-out/cache/ast/v0.9.8/7176c06e07c93c02d4929347dfb3c710517676cd421dca9f7fa62a7f9b028dfb.json](graphify-out/cache/ast/v0.9.8/7176c06e07c93c02d4929347dfb3c710517676cd421dca9f7fa62a7f9b028dfb.json) |  | 2026-07-07 | 15KB | `e5462cc6` |
| [graphify-out/cache/ast/v0.9.8/71f1c9e976e9874354abacb839829d13e17ba2a25bd1cb8989aeafd72f98f1dd.json](graphify-out/cache/ast/v0.9.8/71f1c9e976e9874354abacb839829d13e17ba2a25bd1cb8989aeafd72f98f1dd.json) |  | 2026-07-08 | 4KB | `e7514427` |
| [graphify-out/cache/ast/v0.9.8/7206a25888ce4171f59d4275c49220c96148c1ab0cb25799e91fa43b7817afa3.json](graphify-out/cache/ast/v0.9.8/7206a25888ce4171f59d4275c49220c96148c1ab0cb25799e91fa43b7817afa3.json) |  | 2026-07-30 | 9KB | `afc0255d` |
| [graphify-out/cache/ast/v0.9.8/72436d23f51c96c5213ed5fb119f2ca4d1bd3efe173a36969046329e247e2b69.json](graphify-out/cache/ast/v0.9.8/72436d23f51c96c5213ed5fb119f2ca4d1bd3efe173a36969046329e247e2b69.json) |  | 2026-07-08 | 8KB | `946fc170` |
| [graphify-out/cache/ast/v0.9.8/72b75a1bfe0dcec4a230f6016d3bef097801c30fb7297dc46cae7da5ccf4729d.json](graphify-out/cache/ast/v0.9.8/72b75a1bfe0dcec4a230f6016d3bef097801c30fb7297dc46cae7da5ccf4729d.json) |  | 2026-07-10 | 16KB | `69b804d4` |
| [graphify-out/cache/ast/v0.9.8/72c1b4bc917ea1c5377dabd783dab51f1a5084b5550c990b55e95e4a8fd9945b.json](graphify-out/cache/ast/v0.9.8/72c1b4bc917ea1c5377dabd783dab51f1a5084b5550c990b55e95e4a8fd9945b.json) |  | 2026-07-27 | 3KB | `07a1906c` |
| [graphify-out/cache/ast/v0.9.8/72d1b33e60c6166e4389356c11c75ba9a86d65f0dcacda5b39ec82b3ecfc0df6.json](graphify-out/cache/ast/v0.9.8/72d1b33e60c6166e4389356c11c75ba9a86d65f0dcacda5b39ec82b3ecfc0df6.json) |  | 2026-07-07 | 17KB | `c07ca273` |
| [graphify-out/cache/ast/v0.9.8/72d435813f90aa48c31d4ab12f3dba33b67b3071ef64cd1d74009bd80a09c4aa.json](graphify-out/cache/ast/v0.9.8/72d435813f90aa48c31d4ab12f3dba33b67b3071ef64cd1d74009bd80a09c4aa.json) |  | 2026-07-08 | 9KB | `1e86592e` |
| [graphify-out/cache/ast/v0.9.8/72d9b8bf0bbe76440a7ef0877576e0d3a28fb1aca3f2f621899c7d1fd821832a.json](graphify-out/cache/ast/v0.9.8/72d9b8bf0bbe76440a7ef0877576e0d3a28fb1aca3f2f621899c7d1fd821832a.json) |  | 2026-07-29 | 5KB | `393a4aba` |
| [graphify-out/cache/ast/v0.9.8/72f9bdb4f57952e3857f261d2ebac6c81801bb425acb66ebcf054d4e5ef04262.json](graphify-out/cache/ast/v0.9.8/72f9bdb4f57952e3857f261d2ebac6c81801bb425acb66ebcf054d4e5ef04262.json) |  | 2026-07-08 | 13KB | `06b87727` |
| [graphify-out/cache/ast/v0.9.8/7306f937d54041a53955e4ee3342eff46bc47b771aa0bba07203172ffec2b012.json](graphify-out/cache/ast/v0.9.8/7306f937d54041a53955e4ee3342eff46bc47b771aa0bba07203172ffec2b012.json) |  | 2026-07-07 | 20KB | `ba4f2e4d` |
| [graphify-out/cache/ast/v0.9.8/73587895287a77d7b7a21ac1b7e7b580c550f7c10ad11fc87514c107f8d6d18f.json](graphify-out/cache/ast/v0.9.8/73587895287a77d7b7a21ac1b7e7b580c550f7c10ad11fc87514c107f8d6d18f.json) |  | 2026-07-08 | 4KB | `48036b11` |
| [graphify-out/cache/ast/v0.9.8/73cc0ccb6e7ef8add0971032fd029c545ab6dc6919038028e578c6523520edac.json](graphify-out/cache/ast/v0.9.8/73cc0ccb6e7ef8add0971032fd029c545ab6dc6919038028e578c6523520edac.json) |  | 2026-07-08 | 41KB | `12d3e270` |
| [graphify-out/cache/ast/v0.9.8/73e5a20ca0b7627f8d3fdd43380ef4022a7194e36a48e46f55ecb823a1b69bff.json](graphify-out/cache/ast/v0.9.8/73e5a20ca0b7627f8d3fdd43380ef4022a7194e36a48e46f55ecb823a1b69bff.json) |  | 2026-07-08 | 4KB | `94cb2eb3` |
| [graphify-out/cache/ast/v0.9.8/7400f69fdb5447edfc66d2979a1c0f794f21827bb1cfdbf0869625c5c9050a71.json](graphify-out/cache/ast/v0.9.8/7400f69fdb5447edfc66d2979a1c0f794f21827bb1cfdbf0869625c5c9050a71.json) |  | 2026-07-07 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/7408c11a29862581f53f3643df2477f559a582a2ac22a1b5126b81569be6888e.json](graphify-out/cache/ast/v0.9.8/7408c11a29862581f53f3643df2477f559a582a2ac22a1b5126b81569be6888e.json) |  | 2026-07-08 | 22KB | `de7b64a4` |
| [graphify-out/cache/ast/v0.9.8/7428a62b11eaeae394a4f719c4dcb13d9fc19be775aa881fdbb77e182779662b.json](graphify-out/cache/ast/v0.9.8/7428a62b11eaeae394a4f719c4dcb13d9fc19be775aa881fdbb77e182779662b.json) |  | 2026-07-08 | 5KB | `15843297` |
| [graphify-out/cache/ast/v0.9.8/742e1196e7120fed081bc39b6a01c4a7c5fbaa4e8b7601a067eb7f75f365d2f5.json](graphify-out/cache/ast/v0.9.8/742e1196e7120fed081bc39b6a01c4a7c5fbaa4e8b7601a067eb7f75f365d2f5.json) |  | 2026-07-08 | 8KB | `6585ac66` |
| [graphify-out/cache/ast/v0.9.8/745c8048275d8c5f36a1d1691afd353a2d08ae23b5cab2d77523946e73713db6.json](graphify-out/cache/ast/v0.9.8/745c8048275d8c5f36a1d1691afd353a2d08ae23b5cab2d77523946e73713db6.json) |  | 2026-07-08 | 22KB | `669d14a0` |
| [graphify-out/cache/ast/v0.9.8/74c0b290cfbbfc5bee9c960398199f4f75a095378a539d3b49a3bb2d2730ca2c.json](graphify-out/cache/ast/v0.9.8/74c0b290cfbbfc5bee9c960398199f4f75a095378a539d3b49a3bb2d2730ca2c.json) |  | 2026-07-08 | 54KB | `f804a5b1` |
| [graphify-out/cache/ast/v0.9.8/74d4a9256343aee1090d80ab7c4a764ad45ce6dc1db11f6700a1aa327e7c1742.json](graphify-out/cache/ast/v0.9.8/74d4a9256343aee1090d80ab7c4a764ad45ce6dc1db11f6700a1aa327e7c1742.json) |  | 2026-07-08 | 5KB | `33531058` |
| [graphify-out/cache/ast/v0.9.8/74ee2bcbcd152d3c3383621e830010c4adeaf2a3512737ca37350bfeb6b33e4c.json](graphify-out/cache/ast/v0.9.8/74ee2bcbcd152d3c3383621e830010c4adeaf2a3512737ca37350bfeb6b33e4c.json) |  | 2026-07-08 | 17KB | `3b66a91c` |
| [graphify-out/cache/ast/v0.9.8/74f8dc5b85b82e15ce283a396ec5a257825bd83870686197d76c50ca0a557378.json](graphify-out/cache/ast/v0.9.8/74f8dc5b85b82e15ce283a396ec5a257825bd83870686197d76c50ca0a557378.json) |  | 2026-07-07 | 21KB | `7a369328` |
| [graphify-out/cache/ast/v0.9.8/7552c835677f900ba4372b535fb7fcd3065b07762b483097e365a8a0e0f1f8d2.json](graphify-out/cache/ast/v0.9.8/7552c835677f900ba4372b535fb7fcd3065b07762b483097e365a8a0e0f1f8d2.json) |  | 2026-07-08 | 3KB | `8593b198` |
| [graphify-out/cache/ast/v0.9.8/7585a1dfb948003eb0f975660ae228ebb01771a12dc6aa9a4d6c37121d11d955.json](graphify-out/cache/ast/v0.9.8/7585a1dfb948003eb0f975660ae228ebb01771a12dc6aa9a4d6c37121d11d955.json) |  | 2026-07-08 | 3KB | `8c9ef53c` |
| [graphify-out/cache/ast/v0.9.8/759f3fa8416cd2605761bba5e054f8a00df64e2e6c00af8d57139e3811d14f6e.json](graphify-out/cache/ast/v0.9.8/759f3fa8416cd2605761bba5e054f8a00df64e2e6c00af8d57139e3811d14f6e.json) |  | 2026-07-07 | 247B | `30045dcd` |
| [graphify-out/cache/ast/v0.9.8/75aa6781e15ca5648b3d5485df5c74710d8c6c46042a0e31a0cedb97ea2ba7a1.json](graphify-out/cache/ast/v0.9.8/75aa6781e15ca5648b3d5485df5c74710d8c6c46042a0e31a0cedb97ea2ba7a1.json) |  | 2026-07-08 | 2KB | `2a03a729` |
| [graphify-out/cache/ast/v0.9.8/75ac675e9e06271ef994be87c00e43e3841dedbcecc3c05e0cd4955a14a3915a.json](graphify-out/cache/ast/v0.9.8/75ac675e9e06271ef994be87c00e43e3841dedbcecc3c05e0cd4955a14a3915a.json) |  | 2026-07-07 | 14KB | `a7838dac` |
| [graphify-out/cache/ast/v0.9.8/760d3bb9eeb4ec6a22a96a3426388cdbda1210685e09324fe543d782a02b6aa7.json](graphify-out/cache/ast/v0.9.8/760d3bb9eeb4ec6a22a96a3426388cdbda1210685e09324fe543d782a02b6aa7.json) |  | 2026-07-08 | 64KB | `0f5c0e88` |
| [graphify-out/cache/ast/v0.9.8/761cde20f620fc4599206c68a35f59fd3472e3f74fc578a8cdf1be497e15ba90.json](graphify-out/cache/ast/v0.9.8/761cde20f620fc4599206c68a35f59fd3472e3f74fc578a8cdf1be497e15ba90.json) |  | 2026-07-08 | 5KB | `cf4d3dc7` |
| [graphify-out/cache/ast/v0.9.8/76702acc18e13068d079bb9c4ea2baf4df532bff312e32637ed688e45077f7b0.json](graphify-out/cache/ast/v0.9.8/76702acc18e13068d079bb9c4ea2baf4df532bff312e32637ed688e45077f7b0.json) |  | 2026-07-08 | 40KB | `df134347` |
| [graphify-out/cache/ast/v0.9.8/767660e7fdecfb6f64edd2e65f4656bceafc0ac2a581a3e3076be83cc388e853.json](graphify-out/cache/ast/v0.9.8/767660e7fdecfb6f64edd2e65f4656bceafc0ac2a581a3e3076be83cc388e853.json) |  | 2026-07-08 | 5KB | `007721d3` |
| [graphify-out/cache/ast/v0.9.8/76dc2834c8c379b37b01c1f913ed466cf8ceacd219d4d1ae775dc1bce5d348e7.json](graphify-out/cache/ast/v0.9.8/76dc2834c8c379b37b01c1f913ed466cf8ceacd219d4d1ae775dc1bce5d348e7.json) |  | 2026-07-08 | 7KB | `7e5293ec` |
| [graphify-out/cache/ast/v0.9.8/76e295a2356dcc32c7a06896c2d93cd0265641319a36ecfa5de172c19f6f6281.json](graphify-out/cache/ast/v0.9.8/76e295a2356dcc32c7a06896c2d93cd0265641319a36ecfa5de172c19f6f6281.json) |  | 2026-07-24 | 11KB | `334dc7b7` |
| [graphify-out/cache/ast/v0.9.8/77bc7c48bfd38293dcf180a9af75a272774f4a995178ce98af2dc110d1e5d190.json](graphify-out/cache/ast/v0.9.8/77bc7c48bfd38293dcf180a9af75a272774f4a995178ce98af2dc110d1e5d190.json) |  | 2026-07-08 | 8KB | `eaf943cb` |
| [graphify-out/cache/ast/v0.9.8/77ec8771a2026fe8f664fe94dffc68a5d46a35ff9af58e341968311318c8404b.json](graphify-out/cache/ast/v0.9.8/77ec8771a2026fe8f664fe94dffc68a5d46a35ff9af58e341968311318c8404b.json) |  | 2026-07-30 | 9KB | `981be656` |
| [graphify-out/cache/ast/v0.9.8/781437cdd70316e041b7aa6f184653fa574419fd4e870735191e210f6c876984.json](graphify-out/cache/ast/v0.9.8/781437cdd70316e041b7aa6f184653fa574419fd4e870735191e210f6c876984.json) |  | 2026-07-29 | 89KB | `6d2de446` |
| [graphify-out/cache/ast/v0.9.8/7852397e7e92981b99f4fb6e9320343a316ee6eac0fb4bf06ae496caeabca558.json](graphify-out/cache/ast/v0.9.8/7852397e7e92981b99f4fb6e9320343a316ee6eac0fb4bf06ae496caeabca558.json) |  | 2026-07-07 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/785270b19a96ab86dcabb8b7522771a27d9479485209883758433eb99231e388.json](graphify-out/cache/ast/v0.9.8/785270b19a96ab86dcabb8b7522771a27d9479485209883758433eb99231e388.json) |  | 2026-07-07 | 11KB | `6d2331be` |
| [graphify-out/cache/ast/v0.9.8/792c0ec314a852c514495ae68fff8569362624bd6b1bce152f51bc43de40d2a9.json](graphify-out/cache/ast/v0.9.8/792c0ec314a852c514495ae68fff8569362624bd6b1bce152f51bc43de40d2a9.json) |  | 2026-07-07 | 35KB | `eb7a7e8d` |
| [graphify-out/cache/ast/v0.9.8/793688e1f4d8f7777dd0081240f60289984572c79577858d10efcf95c5902f0a.json](graphify-out/cache/ast/v0.9.8/793688e1f4d8f7777dd0081240f60289984572c79577858d10efcf95c5902f0a.json) |  | 2026-07-10 | 9KB | `91e8d376` |
| [graphify-out/cache/ast/v0.9.8/79be15457e31f1c64159d8cad9276940c61022b761d5c0785e19704ca5a2d657.json](graphify-out/cache/ast/v0.9.8/79be15457e31f1c64159d8cad9276940c61022b761d5c0785e19704ca5a2d657.json) |  | 2026-07-23 | 7KB | `cb678c2f` |
| [graphify-out/cache/ast/v0.9.8/7a03b53a2b3d5cd5fe0ca8ddf5d742b16ec98f5cfb5cb1e5a31457942ead7d47.json](graphify-out/cache/ast/v0.9.8/7a03b53a2b3d5cd5fe0ca8ddf5d742b16ec98f5cfb5cb1e5a31457942ead7d47.json) |  | 2026-07-08 | 12KB | `4fb55d55` |
| [graphify-out/cache/ast/v0.9.8/7a62b6972598bef4db954eb30f867b1888f8badd87f28de1d46290d8c42ac228.json](graphify-out/cache/ast/v0.9.8/7a62b6972598bef4db954eb30f867b1888f8badd87f28de1d46290d8c42ac228.json) |  | 2026-07-08 | 3KB | `aa4012af` |
| [graphify-out/cache/ast/v0.9.8/7ac73efa5bec489db55c472c27be050446d94723e5fe5bb7213b26e7686e780c.json](graphify-out/cache/ast/v0.9.8/7ac73efa5bec489db55c472c27be050446d94723e5fe5bb7213b26e7686e780c.json) |  | 2026-07-31 | 9KB | `53a74bd2` |
| [graphify-out/cache/ast/v0.9.8/7b4802f9d1a7617a227608d514b1be307d9eaabab967ca766303eb5da7531cc3.json](graphify-out/cache/ast/v0.9.8/7b4802f9d1a7617a227608d514b1be307d9eaabab967ca766303eb5da7531cc3.json) |  | 2026-07-08 | 1KB | `8458e7e8` |
| [graphify-out/cache/ast/v0.9.8/7c0a138520f75361f6235181ccf17f610ab459184341c20bec89badfa2b4a8a2.json](graphify-out/cache/ast/v0.9.8/7c0a138520f75361f6235181ccf17f610ab459184341c20bec89badfa2b4a8a2.json) |  | 2026-07-08 | 8KB | `1461046e` |
| [graphify-out/cache/ast/v0.9.8/7c4d9f20804a816c03bb8c21f22086790dbf2c0cdb03636330a57872b1a95713.json](graphify-out/cache/ast/v0.9.8/7c4d9f20804a816c03bb8c21f22086790dbf2c0cdb03636330a57872b1a95713.json) |  | 2026-07-08 | 13KB | `905f0980` |
| [graphify-out/cache/ast/v0.9.8/7c73f2d308aaf0858d4b119bc04351456aca5250ca49138bd36f06ed14130446.json](graphify-out/cache/ast/v0.9.8/7c73f2d308aaf0858d4b119bc04351456aca5250ca49138bd36f06ed14130446.json) |  | 2026-07-08 | 4KB | `ce3f4660` |
| [graphify-out/cache/ast/v0.9.8/7ca0a0467e818549582e729f038f68678f2c7a3c67f17a5b778f05052e1af2f7.json](graphify-out/cache/ast/v0.9.8/7ca0a0467e818549582e729f038f68678f2c7a3c67f17a5b778f05052e1af2f7.json) |  | 2026-07-08 | 24KB | `666c12d9` |
| [graphify-out/cache/ast/v0.9.8/7ca887e23f47a525c7559c605735843550183ba8d9f962c7309480a17d6c0bf5.json](graphify-out/cache/ast/v0.9.8/7ca887e23f47a525c7559c605735843550183ba8d9f962c7309480a17d6c0bf5.json) |  | 2026-07-08 | 4KB | `135b96a2` |
| [graphify-out/cache/ast/v0.9.8/7ce0aab7c23207cec32402edf8cfa07ad49acce11af3a881022db5d7d17b718b.json](graphify-out/cache/ast/v0.9.8/7ce0aab7c23207cec32402edf8cfa07ad49acce11af3a881022db5d7d17b718b.json) |  | 2026-07-08 | 6KB | `71904a0d` |
| [graphify-out/cache/ast/v0.9.8/7ce7172649fbfcb6bd310f50134a7fbd29589cdbf7c96c6500511eb4a6d09190.json](graphify-out/cache/ast/v0.9.8/7ce7172649fbfcb6bd310f50134a7fbd29589cdbf7c96c6500511eb4a6d09190.json) |  | 2026-07-07 | 59KB | `725ce906` |
| [graphify-out/cache/ast/v0.9.8/7d05ca4f5a8b2e7754c4aa5606e8ee30ecb29727a147e809ba1fec918bb31d16.json](graphify-out/cache/ast/v0.9.8/7d05ca4f5a8b2e7754c4aa5606e8ee30ecb29727a147e809ba1fec918bb31d16.json) |  | 2026-07-09 | 35KB | `ba37c697` |
| [graphify-out/cache/ast/v0.9.8/7d3c91ea3a6dd75223d673ad3bc261f86df343e73250639d5e3eec59bb61b424.json](graphify-out/cache/ast/v0.9.8/7d3c91ea3a6dd75223d673ad3bc261f86df343e73250639d5e3eec59bb61b424.json) |  | 2026-07-08 | 30KB | `bd1dfb9c` |
| [graphify-out/cache/ast/v0.9.8/7d6a22ea335bb656cfaa39687117a9f71156684294bc812c87ec9c4e635f3f8d.json](graphify-out/cache/ast/v0.9.8/7d6a22ea335bb656cfaa39687117a9f71156684294bc812c87ec9c4e635f3f8d.json) |  | 2026-07-07 | 19KB | `89b28857` |
| [graphify-out/cache/ast/v0.9.8/7dd0e53eb528b63d00181d07cedaf84fdd2dc2ee64eb2c7bc376d0bde4d1c2ee.json](graphify-out/cache/ast/v0.9.8/7dd0e53eb528b63d00181d07cedaf84fdd2dc2ee64eb2c7bc376d0bde4d1c2ee.json) |  | 2026-07-07 | 19KB | `bbf7a66c` |
| [graphify-out/cache/ast/v0.9.8/7deff95dfd954615a9707731d09affde3844e2a497c9c2b6c4c085846e62e8cf.json](graphify-out/cache/ast/v0.9.8/7deff95dfd954615a9707731d09affde3844e2a497c9c2b6c4c085846e62e8cf.json) |  | 2026-07-07 | 15KB | `fe915113` |
| [graphify-out/cache/ast/v0.9.8/7e20c1d7de70c6dd0a284fc6aecdb1b3aa611dcdc5a888c46397dac464ddf258.json](graphify-out/cache/ast/v0.9.8/7e20c1d7de70c6dd0a284fc6aecdb1b3aa611dcdc5a888c46397dac464ddf258.json) |  | 2026-07-22 | 6KB | `aaebf8ed` |
| [graphify-out/cache/ast/v0.9.8/7e2143180d89693b120b49889d6aa8a520e276807ce6085749288cc25ab3e455.json](graphify-out/cache/ast/v0.9.8/7e2143180d89693b120b49889d6aa8a520e276807ce6085749288cc25ab3e455.json) |  | 2026-07-08 | 2KB | `fd6b8e86` |
| [graphify-out/cache/ast/v0.9.8/7e2f93cf65b430ad1887352bc1dbab3ca814c0a3964a921bd0b5a495f4c29871.json](graphify-out/cache/ast/v0.9.8/7e2f93cf65b430ad1887352bc1dbab3ca814c0a3964a921bd0b5a495f4c29871.json) |  | 2026-07-08 | 30KB | `018715ac` |
| [graphify-out/cache/ast/v0.9.8/7e52aa3ea264c40ca103f1feeff0b65870cb2e0f37eea7d0bab77e74479ff4d8.json](graphify-out/cache/ast/v0.9.8/7e52aa3ea264c40ca103f1feeff0b65870cb2e0f37eea7d0bab77e74479ff4d8.json) |  | 2026-07-08 | 8KB | `09bc7060` |
| [graphify-out/cache/ast/v0.9.8/7e94e166a9113230d4a85084e6a863ef3e7c25beb55ca3f64f4cc8d77d5c10a9.json](graphify-out/cache/ast/v0.9.8/7e94e166a9113230d4a85084e6a863ef3e7c25beb55ca3f64f4cc8d77d5c10a9.json) |  | 2026-07-08 | 67KB | `ab23fca1` |
| [graphify-out/cache/ast/v0.9.8/7ef6a9b6bb4c5438e132b6eeff468ab764941c8c9bbee4b7aa21d26b46693246.json](graphify-out/cache/ast/v0.9.8/7ef6a9b6bb4c5438e132b6eeff468ab764941c8c9bbee4b7aa21d26b46693246.json) |  | 2026-07-07 | 5KB | `5cf363f8` |
| [graphify-out/cache/ast/v0.9.8/7f5621986543842bb815598b12e18925d0be22951771313cec04f36482bd876d.json](graphify-out/cache/ast/v0.9.8/7f5621986543842bb815598b12e18925d0be22951771313cec04f36482bd876d.json) |  | 2026-07-08 | 6KB | `ff0bc702` |
| [graphify-out/cache/ast/v0.9.8/7f69ed92c9fc18c1c779617ba2620cb6fc3e7993fa1c697e2a52cb932a23ea4c.json](graphify-out/cache/ast/v0.9.8/7f69ed92c9fc18c1c779617ba2620cb6fc3e7993fa1c697e2a52cb932a23ea4c.json) |  | 2026-07-10 | 25KB | `7f845171` |
| [graphify-out/cache/ast/v0.9.8/7f741032f8f5c49ac8edab8ab1e1a683007f79744b8204b87fdfbd60ec90f0d0.json](graphify-out/cache/ast/v0.9.8/7f741032f8f5c49ac8edab8ab1e1a683007f79744b8204b87fdfbd60ec90f0d0.json) |  | 2026-07-08 | 8KB | `4088b3ef` |
| [graphify-out/cache/ast/v0.9.8/7fcedcfb96e79baf9aa3feb5d477af71ec2795a16620a3bceb69214abf13e7cf.json](graphify-out/cache/ast/v0.9.8/7fcedcfb96e79baf9aa3feb5d477af71ec2795a16620a3bceb69214abf13e7cf.json) |  | 2026-07-08 | 2KB | `84003a1f` |
| [graphify-out/cache/ast/v0.9.8/7ff28ca494ad820fd1f93cea3ece4a32fa2ba5e5dfc394e69ac117382d94de60.json](graphify-out/cache/ast/v0.9.8/7ff28ca494ad820fd1f93cea3ece4a32fa2ba5e5dfc394e69ac117382d94de60.json) |  | 2026-07-08 | 11KB | `5d9b19cb` |
| [graphify-out/cache/ast/v0.9.8/80017ee83ef5cb6ac05f834728a27fcc530d030edfb6f7830c431add8436a6b1.json](graphify-out/cache/ast/v0.9.8/80017ee83ef5cb6ac05f834728a27fcc530d030edfb6f7830c431add8436a6b1.json) |  | 2026-07-08 | 60KB | `bf72469c` |
| [graphify-out/cache/ast/v0.9.8/80c95cd3974043fde100a317f713763526d50c4ded8858e2199cc21612bbbe3c.json](graphify-out/cache/ast/v0.9.8/80c95cd3974043fde100a317f713763526d50c4ded8858e2199cc21612bbbe3c.json) |  | 2026-07-08 | 31KB | `e184060b` |
| [graphify-out/cache/ast/v0.9.8/80eba40c991e0712eac5ba427a430f0663fa0229141f570a5cfb1f7588dbe50c.json](graphify-out/cache/ast/v0.9.8/80eba40c991e0712eac5ba427a430f0663fa0229141f570a5cfb1f7588dbe50c.json) |  | 2026-07-07 | 3KB | `6d65ae16` |
| [graphify-out/cache/ast/v0.9.8/814599ac1df60e66659901d8f86293fbe926a4aebcef132ee7a23057e02d5043.json](graphify-out/cache/ast/v0.9.8/814599ac1df60e66659901d8f86293fbe926a4aebcef132ee7a23057e02d5043.json) |  | 2026-07-08 | 6KB | `151d7bfa` |
| [graphify-out/cache/ast/v0.9.8/814c5288f854c180fbdacd5678a2a6b8b7b381f297512ea83ddb3853323b0ff7.json](graphify-out/cache/ast/v0.9.8/814c5288f854c180fbdacd5678a2a6b8b7b381f297512ea83ddb3853323b0ff7.json) |  | 2026-07-08 | 4KB | `d29bc697` |
| [graphify-out/cache/ast/v0.9.8/814eb7628108184909ee79b9924e16c9ad7e7d80663b2a556262d937f5ed0eab.json](graphify-out/cache/ast/v0.9.8/814eb7628108184909ee79b9924e16c9ad7e7d80663b2a556262d937f5ed0eab.json) |  | 2026-07-07 | 11KB | `f02a24ea` |
| [graphify-out/cache/ast/v0.9.8/815cc3805ef02e70b4009381edf6a4340c621a5b19327f38796406a31932dbdd.json](graphify-out/cache/ast/v0.9.8/815cc3805ef02e70b4009381edf6a4340c621a5b19327f38796406a31932dbdd.json) |  | 2026-07-08 | 2KB | `594fbd27` |
| [graphify-out/cache/ast/v0.9.8/818953521b6105ae152520604c0bfd27a6c6b2dd0e94ba66a2aec883a53b42bd.json](graphify-out/cache/ast/v0.9.8/818953521b6105ae152520604c0bfd27a6c6b2dd0e94ba66a2aec883a53b42bd.json) |  | 2026-07-08 | 3KB | `14a57556` |
| [graphify-out/cache/ast/v0.9.8/81bd72ef098c88c68a64ee2d15f68b885fab177171fcb8d8e2be830e6f73012f.json](graphify-out/cache/ast/v0.9.8/81bd72ef098c88c68a64ee2d15f68b885fab177171fcb8d8e2be830e6f73012f.json) |  | 2026-07-07 | 5KB | `39075c2b` |
| [graphify-out/cache/ast/v0.9.8/823f30597f39d35698e9a37fbc795f42ba26664b5e5cde13b18b5bd66e6b3f6a.json](graphify-out/cache/ast/v0.9.8/823f30597f39d35698e9a37fbc795f42ba26664b5e5cde13b18b5bd66e6b3f6a.json) |  | 2026-07-08 | 7KB | `0defc553` |
| [graphify-out/cache/ast/v0.9.8/826832fe489fd72f3eebe0ff30040f9ce521be48861349968608669c9ef0ff29.json](graphify-out/cache/ast/v0.9.8/826832fe489fd72f3eebe0ff30040f9ce521be48861349968608669c9ef0ff29.json) |  | 2026-07-08 | 8KB | `601aebbf` |
| [graphify-out/cache/ast/v0.9.8/826af5ecbade3de44bd6d6cdd8485bd64098f10cc780a3c0cfe71d7c24e8e4aa.json](graphify-out/cache/ast/v0.9.8/826af5ecbade3de44bd6d6cdd8485bd64098f10cc780a3c0cfe71d7c24e8e4aa.json) |  | 2026-07-08 | 11KB | `b068c1bd` |
| [graphify-out/cache/ast/v0.9.8/82b01a43992e79b85191e7fe0eaf96109a010713805fa9bc83d6b541f5bb2be9.json](graphify-out/cache/ast/v0.9.8/82b01a43992e79b85191e7fe0eaf96109a010713805fa9bc83d6b541f5bb2be9.json) |  | 2026-07-07 | 21KB | `e1c4ca64` |
| [graphify-out/cache/ast/v0.9.8/82d555f3be67a8e3e6cec71e819c503b07c39bee417ccbd4e1017df98be82143.json](graphify-out/cache/ast/v0.9.8/82d555f3be67a8e3e6cec71e819c503b07c39bee417ccbd4e1017df98be82143.json) |  | 2026-07-08 | 6KB | `10feff55` |
| [graphify-out/cache/ast/v0.9.8/82e7756eef30a3ed4baf1b70f9c07666cba11891fa19d1eaeb5dda9208ca97c6.json](graphify-out/cache/ast/v0.9.8/82e7756eef30a3ed4baf1b70f9c07666cba11891fa19d1eaeb5dda9208ca97c6.json) |  | 2026-07-08 | 7KB | `14fdf66b` |
| [graphify-out/cache/ast/v0.9.8/82f13ffaf4654a955334e794bd3e8f2c4c856cf3db363aea180eff0b4300367b.json](graphify-out/cache/ast/v0.9.8/82f13ffaf4654a955334e794bd3e8f2c4c856cf3db363aea180eff0b4300367b.json) |  | 2026-07-08 | 69KB | `29529399` |
| [graphify-out/cache/ast/v0.9.8/8307fafdc94f136d7b0c23b97fc1968c513e6c41953abeffc7a3a9fee6520bee.json](graphify-out/cache/ast/v0.9.8/8307fafdc94f136d7b0c23b97fc1968c513e6c41953abeffc7a3a9fee6520bee.json) |  | 2026-07-08 | 47KB | `5c468ce3` |
| [graphify-out/cache/ast/v0.9.8/832d5889e3ef08e62f3780203957d0375fafbaf4bf6e0590d237a4475adf8c33.json](graphify-out/cache/ast/v0.9.8/832d5889e3ef08e62f3780203957d0375fafbaf4bf6e0590d237a4475adf8c33.json) |  | 2026-07-29 | 12KB | `e3f60a69` |
| [graphify-out/cache/ast/v0.9.8/832f7c1a7e3816dcacca62cb6bdaf480b418af7c49f0720ca4144f9f0774f9eb.json](graphify-out/cache/ast/v0.9.8/832f7c1a7e3816dcacca62cb6bdaf480b418af7c49f0720ca4144f9f0774f9eb.json) |  | 2026-07-27 | 6KB | `5796ea69` |
| [graphify-out/cache/ast/v0.9.8/835302ba7517dc74bdffcc9af81df1c6a158dd7b588fe65a1089b9499868fb15.json](graphify-out/cache/ast/v0.9.8/835302ba7517dc74bdffcc9af81df1c6a158dd7b588fe65a1089b9499868fb15.json) |  | 2026-07-07 | 237B | `6210f229` |
| [graphify-out/cache/ast/v0.9.8/836aba627cce6a366910488057748e99df67f8d78547a5dfed75f7d10f338dc6.json](graphify-out/cache/ast/v0.9.8/836aba627cce6a366910488057748e99df67f8d78547a5dfed75f7d10f338dc6.json) |  | 2026-08-01 | 12KB | `d7b9ef36` |
| [graphify-out/cache/ast/v0.9.8/83739a36c382efc75f1c9e5fcc5354b2172470e8be2acd5b74f9a57d99602f47.json](graphify-out/cache/ast/v0.9.8/83739a36c382efc75f1c9e5fcc5354b2172470e8be2acd5b74f9a57d99602f47.json) |  | 2026-07-09 | 12KB | `d90cf55b` |
| [graphify-out/cache/ast/v0.9.8/83bc8533cdd37e324d11a16fa94762f4a655ab8ba29d0bb8a7564ecf13966d26.json](graphify-out/cache/ast/v0.9.8/83bc8533cdd37e324d11a16fa94762f4a655ab8ba29d0bb8a7564ecf13966d26.json) |  | 2026-07-20 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/846639d49fb117fa0d29d7ba0ac0359ae19dc160be2c4a4f4ef6e9d5b186352f.json](graphify-out/cache/ast/v0.9.8/846639d49fb117fa0d29d7ba0ac0359ae19dc160be2c4a4f4ef6e9d5b186352f.json) |  | 2026-07-08 | 102KB | `f0712727` |
| [graphify-out/cache/ast/v0.9.8/84734d75d38e7f9b9ba1e9757d2b0acad41860167524825704f2e3be26cc8572.json](graphify-out/cache/ast/v0.9.8/84734d75d38e7f9b9ba1e9757d2b0acad41860167524825704f2e3be26cc8572.json) |  | 2026-07-08 | 3KB | `30988505` |
| [graphify-out/cache/ast/v0.9.8/84fa2683086e58761eec0f656b51adc0c48e16157eb3901b55eab507149d2fcf.json](graphify-out/cache/ast/v0.9.8/84fa2683086e58761eec0f656b51adc0c48e16157eb3901b55eab507149d2fcf.json) |  | 2026-07-08 | 4KB | `856dfb34` |
| [graphify-out/cache/ast/v0.9.8/85119aad21bbe8dfb8c1770add435b8002c4cf56f59ff34d3a3e4b4f27c956b3.json](graphify-out/cache/ast/v0.9.8/85119aad21bbe8dfb8c1770add435b8002c4cf56f59ff34d3a3e4b4f27c956b3.json) |  | 2026-07-10 | 45KB | `cfa9e6bb` |
| [graphify-out/cache/ast/v0.9.8/851b8f75975d0382d757ef79f41f749e07b7d001ea307bfe3f98fb0fefa81902.json](graphify-out/cache/ast/v0.9.8/851b8f75975d0382d757ef79f41f749e07b7d001ea307bfe3f98fb0fefa81902.json) |  | 2026-07-07 | 14KB | `b26eb93e` |
| [graphify-out/cache/ast/v0.9.8/851c9d626f3649d087d4d26195cd915cf035974a4b798f96fe0dc4e1a54a505e.json](graphify-out/cache/ast/v0.9.8/851c9d626f3649d087d4d26195cd915cf035974a4b798f96fe0dc4e1a54a505e.json) |  | 2026-07-08 | 8KB | `e60a1ee6` |
| [graphify-out/cache/ast/v0.9.8/851e9dd1af9a57f61eeb7c50541098082fe1bfbbbb0d7df2bab9551e543fd25f.json](graphify-out/cache/ast/v0.9.8/851e9dd1af9a57f61eeb7c50541098082fe1bfbbbb0d7df2bab9551e543fd25f.json) |  | 2026-07-20 | 5KB | `d074469a` |
| [graphify-out/cache/ast/v0.9.8/853517802ad560db08b48da4bf5e62c4a5aefa6d9691e06e6b79bb1bb7c5b42f.json](graphify-out/cache/ast/v0.9.8/853517802ad560db08b48da4bf5e62c4a5aefa6d9691e06e6b79bb1bb7c5b42f.json) |  | 2026-07-07 | 29KB | `264697cb` |
| [graphify-out/cache/ast/v0.9.8/854af447a34ded15655aafaebedc70c287a15bed8c7f32170d7cabf88fe27d7f.json](graphify-out/cache/ast/v0.9.8/854af447a34ded15655aafaebedc70c287a15bed8c7f32170d7cabf88fe27d7f.json) |  | 2026-07-07 | 15KB | `cdaeb452` |
| [graphify-out/cache/ast/v0.9.8/85578e618706bb1c3ac24225c7aca13da60f84bf298ee7f4c77291c99bc088dc.json](graphify-out/cache/ast/v0.9.8/85578e618706bb1c3ac24225c7aca13da60f84bf298ee7f4c77291c99bc088dc.json) |  | 2026-07-08 | 20KB | `ed5cb6f9` |
| [graphify-out/cache/ast/v0.9.8/85994d24b76eaa336d09fd78ed9c50129edc76b12f8ac1704606fd13fba342f3.json](graphify-out/cache/ast/v0.9.8/85994d24b76eaa336d09fd78ed9c50129edc76b12f8ac1704606fd13fba342f3.json) |  | 2026-07-27 | 55KB | `5f9dc602` |
| [graphify-out/cache/ast/v0.9.8/862fce5ee92dafb485cf4f68e3464215aea4763a66dcf8a251f006034c56b4ae.json](graphify-out/cache/ast/v0.9.8/862fce5ee92dafb485cf4f68e3464215aea4763a66dcf8a251f006034c56b4ae.json) |  | 2026-07-08 | 48KB | `f6b24acb` |
| [graphify-out/cache/ast/v0.9.8/8630cc49eaf96db801c449400d2104715fc5e39d90bbbb9e6af57991ad77611f.json](graphify-out/cache/ast/v0.9.8/8630cc49eaf96db801c449400d2104715fc5e39d90bbbb9e6af57991ad77611f.json) |  | 2026-07-08 | 17KB | `eea48a9d` |
| [graphify-out/cache/ast/v0.9.8/86697d0f34af8d293a24acdd731edc43b03253efd0ef58db9590e9892ec8632f.json](graphify-out/cache/ast/v0.9.8/86697d0f34af8d293a24acdd731edc43b03253efd0ef58db9590e9892ec8632f.json) |  | 2026-07-07 | 6KB | `444d50da` |
| [graphify-out/cache/ast/v0.9.8/86a14fa76a9d3f4b9e1d190a5c24d3f37ff007b850fb24e580dcb7bec0fc470e.json](graphify-out/cache/ast/v0.9.8/86a14fa76a9d3f4b9e1d190a5c24d3f37ff007b850fb24e580dcb7bec0fc470e.json) |  | 2026-07-08 | 12KB | `84f2ac63` |
| [graphify-out/cache/ast/v0.9.8/86e7c16f45ac1e8d09b9facd1b117f7936570d3adcfe8da89690420f2b988389.json](graphify-out/cache/ast/v0.9.8/86e7c16f45ac1e8d09b9facd1b117f7936570d3adcfe8da89690420f2b988389.json) |  | 2026-07-08 | 8KB | `af957b9c` |
| [graphify-out/cache/ast/v0.9.8/86e934c0acfef37684ab4c502f27e84cb923e2651e5ebb7d1cf2b16afd8bbeb2.json](graphify-out/cache/ast/v0.9.8/86e934c0acfef37684ab4c502f27e84cb923e2651e5ebb7d1cf2b16afd8bbeb2.json) |  | 2026-07-08 | 4KB | `ceec018e` |
| [graphify-out/cache/ast/v0.9.8/877da59d4ae96589e4830585fb52e96ab186b99c749bcfa102d688b643dc628e.json](graphify-out/cache/ast/v0.9.8/877da59d4ae96589e4830585fb52e96ab186b99c749bcfa102d688b643dc628e.json) |  | 2026-07-27 | 3KB | `a988a8a2` |
| [graphify-out/cache/ast/v0.9.8/881803b57e7e2a02ec3c4d167ad82f5d2cc5a59fed34db0963d4ff90611b56b5.json](graphify-out/cache/ast/v0.9.8/881803b57e7e2a02ec3c4d167ad82f5d2cc5a59fed34db0963d4ff90611b56b5.json) |  | 2026-07-08 | 27KB | `9b5de42c` |
| [graphify-out/cache/ast/v0.9.8/887b40c370bcc194a1aa69a2b45522c5241dc02900bd9dafc6b93d24c7502ffb.json](graphify-out/cache/ast/v0.9.8/887b40c370bcc194a1aa69a2b45522c5241dc02900bd9dafc6b93d24c7502ffb.json) |  | 2026-07-08 | 12KB | `58582319` |
| [graphify-out/cache/ast/v0.9.8/8927a41b7b5798d2fc0ab9a522d5acb83d1bda932cc2ba6e735e4beca85d23ef.json](graphify-out/cache/ast/v0.9.8/8927a41b7b5798d2fc0ab9a522d5acb83d1bda932cc2ba6e735e4beca85d23ef.json) |  | 2026-07-08 | 14KB | `0163f271` |
| [graphify-out/cache/ast/v0.9.8/8933a0c4e9f414d4d58bd97b06fa3f83d222488c41540c32845fb584c4962d18.json](graphify-out/cache/ast/v0.9.8/8933a0c4e9f414d4d58bd97b06fa3f83d222488c41540c32845fb584c4962d18.json) |  | 2026-07-08 | 42KB | `2207dad9` |
| [graphify-out/cache/ast/v0.9.8/89685557e0148cc3bb0c3da60399f9cc1282bf3f99199c0f11d808f3fc6dda13.json](graphify-out/cache/ast/v0.9.8/89685557e0148cc3bb0c3da60399f9cc1282bf3f99199c0f11d808f3fc6dda13.json) |  | 2026-07-08 | 9KB | `479d33f8` |
| [graphify-out/cache/ast/v0.9.8/89709fde7917f4861930f695e12cc0a4bb929ea077bd01ca7239fc3133a56149.json](graphify-out/cache/ast/v0.9.8/89709fde7917f4861930f695e12cc0a4bb929ea077bd01ca7239fc3133a56149.json) |  | 2026-07-08 | 2KB | `319172c2` |
| [graphify-out/cache/ast/v0.9.8/89bdbe6e1807a4facaa2addcfddb3311588c47e8bc2bf2d58faf8de3d0e9db92.json](graphify-out/cache/ast/v0.9.8/89bdbe6e1807a4facaa2addcfddb3311588c47e8bc2bf2d58faf8de3d0e9db92.json) |  | 2026-07-08 | 6KB | `b9272fbe` |
| [graphify-out/cache/ast/v0.9.8/89cdf1711b91170a2adc0f7ea9007f7d4215f043ea385dd4763849da87ae1dd4.json](graphify-out/cache/ast/v0.9.8/89cdf1711b91170a2adc0f7ea9007f7d4215f043ea385dd4763849da87ae1dd4.json) |  | 2026-07-22 | 20KB | `e3e17cf7` |
| [graphify-out/cache/ast/v0.9.8/8a27a44c36fd0ce73169ade20fbe429d7f34b6c00845a07f1f7c067e2b4cf477.json](graphify-out/cache/ast/v0.9.8/8a27a44c36fd0ce73169ade20fbe429d7f34b6c00845a07f1f7c067e2b4cf477.json) |  | 2026-07-07 | 17KB | `1c75cc5d` |
| [graphify-out/cache/ast/v0.9.8/8a31ffc022b7ba421653a98a25a27edc8484c64ab696b04cdd333e7dbbdfa32b.json](graphify-out/cache/ast/v0.9.8/8a31ffc022b7ba421653a98a25a27edc8484c64ab696b04cdd333e7dbbdfa32b.json) |  | 2026-07-08 | 32KB | `f0d3210f` |
| [graphify-out/cache/ast/v0.9.8/8aaef477fcdd4a2c62424c9fba67d664c664ad7328e118d9dda1ccc19d50a1d0.json](graphify-out/cache/ast/v0.9.8/8aaef477fcdd4a2c62424c9fba67d664c664ad7328e118d9dda1ccc19d50a1d0.json) |  | 2026-07-08 | 43KB | `e102cc43` |
| [graphify-out/cache/ast/v0.9.8/8ae2881daabb96a8ba72e39563f0276f41f70055836e01f8d2a8991c5160af19.json](graphify-out/cache/ast/v0.9.8/8ae2881daabb96a8ba72e39563f0276f41f70055836e01f8d2a8991c5160af19.json) |  | 2026-07-08 | 2KB | `674f24c3` |
| [graphify-out/cache/ast/v0.9.8/8b02e354cb6d7500a0dfb3242ec6c4061753bdb7daa17ac59a2dad43309d1082.json](graphify-out/cache/ast/v0.9.8/8b02e354cb6d7500a0dfb3242ec6c4061753bdb7daa17ac59a2dad43309d1082.json) |  | 2026-07-08 | 17KB | `73f17541` |
| [graphify-out/cache/ast/v0.9.8/8b083354d68b20e7eb77a697dfa8a455ee4afc1526baebbe44976ff6e31c50ff.json](graphify-out/cache/ast/v0.9.8/8b083354d68b20e7eb77a697dfa8a455ee4afc1526baebbe44976ff6e31c50ff.json) |  | 2026-07-29 | 31KB | `b56c1f9e` |
| [graphify-out/cache/ast/v0.9.8/8b0d76e596f5e471afc58e621779f5500d5050e536aa647f76168769e5037be0.json](graphify-out/cache/ast/v0.9.8/8b0d76e596f5e471afc58e621779f5500d5050e536aa647f76168769e5037be0.json) |  | 2026-07-07 | 23KB | `1eb9c7dc` |
| [graphify-out/cache/ast/v0.9.8/8b4b0e701c9599c7cc9482565b4b803bd477e43105d39acefbe910448661c238.json](graphify-out/cache/ast/v0.9.8/8b4b0e701c9599c7cc9482565b4b803bd477e43105d39acefbe910448661c238.json) |  | 2026-07-08 | 11KB | `a3129bd0` |
| [graphify-out/cache/ast/v0.9.8/8b71bb658c0b3e9d67af17e5dfc09253c9f07e4ea9c0d72fb9a14575719941f6.json](graphify-out/cache/ast/v0.9.8/8b71bb658c0b3e9d67af17e5dfc09253c9f07e4ea9c0d72fb9a14575719941f6.json) |  | 2026-07-07 | 155KB | `3e3f87e6` |
| [graphify-out/cache/ast/v0.9.8/8c1d7d25da7dde50a5f7266fb399aae97c1f213bf0726ccd76e4efa0c9732c29.json](graphify-out/cache/ast/v0.9.8/8c1d7d25da7dde50a5f7266fb399aae97c1f213bf0726ccd76e4efa0c9732c29.json) |  | 2026-07-07 | 15KB | `e5192929` |
| [graphify-out/cache/ast/v0.9.8/8cd9da22d9e223b4d0a140a6a27f3b2982c2b5a106107ee10a72a4d678cb875e.json](graphify-out/cache/ast/v0.9.8/8cd9da22d9e223b4d0a140a6a27f3b2982c2b5a106107ee10a72a4d678cb875e.json) |  | 2026-07-08 | 6KB | `ba8b2438` |
| [graphify-out/cache/ast/v0.9.8/8d71269ad5e3d6fca9f3ab9a2abed3e888c2ee5bae55e33f3f6ff4516520d92b.json](graphify-out/cache/ast/v0.9.8/8d71269ad5e3d6fca9f3ab9a2abed3e888c2ee5bae55e33f3f6ff4516520d92b.json) |  | 2026-07-08 | 40KB | `d1f224e8` |
| [graphify-out/cache/ast/v0.9.8/8d7c13b9e4e1f2635278bec5c4528b6181144f30458db5c66eeb80850dc1dbc8.json](graphify-out/cache/ast/v0.9.8/8d7c13b9e4e1f2635278bec5c4528b6181144f30458db5c66eeb80850dc1dbc8.json) |  | 2026-07-08 | 157KB | `21630ac5` |
| [graphify-out/cache/ast/v0.9.8/8dca267f36313cd9fcfeadfcfb8728edf4953de6c4a214776d55adf71540d6a8.json](graphify-out/cache/ast/v0.9.8/8dca267f36313cd9fcfeadfcfb8728edf4953de6c4a214776d55adf71540d6a8.json) |  | 2026-07-08 | 5KB | `e987ce06` |
| [graphify-out/cache/ast/v0.9.8/8dff27a4534705b8d9143bfbc559f985202d934ccae28b08a67ca3e2f0c6c14d.json](graphify-out/cache/ast/v0.9.8/8dff27a4534705b8d9143bfbc559f985202d934ccae28b08a67ca3e2f0c6c14d.json) |  | 2026-07-08 | 27KB | `756390b8` |
| [graphify-out/cache/ast/v0.9.8/8e3f7f6cf8a3672c537b5fff456d52a3659f2ff67a382f061d1467cceab90764.json](graphify-out/cache/ast/v0.9.8/8e3f7f6cf8a3672c537b5fff456d52a3659f2ff67a382f061d1467cceab90764.json) |  | 2026-07-08 | 4KB | `6c45edad` |
| [graphify-out/cache/ast/v0.9.8/8e54284f20f1284ed644af53c7bfbed1b0f1ce66859e98b6a041a50895b97f04.json](graphify-out/cache/ast/v0.9.8/8e54284f20f1284ed644af53c7bfbed1b0f1ce66859e98b6a041a50895b97f04.json) |  | 2026-07-08 | 8KB | `a04f5fd7` |
| [graphify-out/cache/ast/v0.9.8/8e6cccc235e82f83baa86ca5eef951b6d8283ae92e1fe325c9bf1085f90509a5.json](graphify-out/cache/ast/v0.9.8/8e6cccc235e82f83baa86ca5eef951b6d8283ae92e1fe325c9bf1085f90509a5.json) |  | 2026-07-10 | 9KB | `eda7464a` |
| [graphify-out/cache/ast/v0.9.8/8e86ebe411806efd945d4ce5cedec0ce0f4805ad36f32e14e2a41b5a81c62305.json](graphify-out/cache/ast/v0.9.8/8e86ebe411806efd945d4ce5cedec0ce0f4805ad36f32e14e2a41b5a81c62305.json) |  | 2026-07-08 | 12KB | `13fbe036` |
| [graphify-out/cache/ast/v0.9.8/8e930479ca7ac8819744ee133d3af25363cdb00ceada380a63d7bf5de24a2eb5.json](graphify-out/cache/ast/v0.9.8/8e930479ca7ac8819744ee133d3af25363cdb00ceada380a63d7bf5de24a2eb5.json) |  | 2026-07-30 | 6KB | `b1fbf6bc` |
| [graphify-out/cache/ast/v0.9.8/8f01747530af98bb27ff2d7c6881614850cbdbc6e77d5fc6335866bdf3204253.json](graphify-out/cache/ast/v0.9.8/8f01747530af98bb27ff2d7c6881614850cbdbc6e77d5fc6335866bdf3204253.json) |  | 2026-07-08 | 7KB | `09cd6442` |
| [graphify-out/cache/ast/v0.9.8/8f0c7649e27191cf742328b3b93dfb9fe4ed3834f0e98dded496ca6a1fc575f4.json](graphify-out/cache/ast/v0.9.8/8f0c7649e27191cf742328b3b93dfb9fe4ed3834f0e98dded496ca6a1fc575f4.json) |  | 2026-07-08 | 8KB | `76736d8a` |
| [graphify-out/cache/ast/v0.9.8/8f568f91bdfb40020fbce8ea964c39bbcc7bbe53211d5b113a32bc775d43e2e9.json](graphify-out/cache/ast/v0.9.8/8f568f91bdfb40020fbce8ea964c39bbcc7bbe53211d5b113a32bc775d43e2e9.json) |  | 2026-07-10 | 46KB | `a4707b09` |
| [graphify-out/cache/ast/v0.9.8/8f6adb19dafcd75ed2347f4c2232d7d6d078055aaf6c13895ea52eb7c06359c9.json](graphify-out/cache/ast/v0.9.8/8f6adb19dafcd75ed2347f4c2232d7d6d078055aaf6c13895ea52eb7c06359c9.json) |  | 2026-07-08 | 4KB | `252a9b39` |
| [graphify-out/cache/ast/v0.9.8/8f74cfe0cc5ee40ed8bb947a4c28ce33e0a15c0c5c4fc7d9176cd90212ce5046.json](graphify-out/cache/ast/v0.9.8/8f74cfe0cc5ee40ed8bb947a4c28ce33e0a15c0c5c4fc7d9176cd90212ce5046.json) |  | 2026-07-24 | 9KB | `7112c8af` |
| [graphify-out/cache/ast/v0.9.8/8f95a3ef77156ec0e7b2a8b71911d7d534979978957a256802b583536f77ea8a.json](graphify-out/cache/ast/v0.9.8/8f95a3ef77156ec0e7b2a8b71911d7d534979978957a256802b583536f77ea8a.json) |  | 2026-07-08 | 7KB | `68848dbe` |
| [graphify-out/cache/ast/v0.9.8/8f9fc4e845002ac96188ced2bbb385eda0b830b4d22c7bcd2a4a56c593b07c72.json](graphify-out/cache/ast/v0.9.8/8f9fc4e845002ac96188ced2bbb385eda0b830b4d22c7bcd2a4a56c593b07c72.json) |  | 2026-07-08 | 4KB | `f62ccd47` |
| [graphify-out/cache/ast/v0.9.8/8fbe9bcf16454ee43a7dd6c0dfa40518d29e025a9a57c817c0dab7a5b6c1d0bb.json](graphify-out/cache/ast/v0.9.8/8fbe9bcf16454ee43a7dd6c0dfa40518d29e025a9a57c817c0dab7a5b6c1d0bb.json) |  | 2026-07-08 | 23KB | `2f7ec00c` |
| [graphify-out/cache/ast/v0.9.8/8fc58714b3dba8255f4db4ae4a4a5d9ae8e3525f95252de909144d9fa810885a.json](graphify-out/cache/ast/v0.9.8/8fc58714b3dba8255f4db4ae4a4a5d9ae8e3525f95252de909144d9fa810885a.json) |  | 2026-07-07 | 60KB | `66967256` |
| [graphify-out/cache/ast/v0.9.8/8fe1008a2240ec060899c86ab4dd722e7a3b216193e67d98640e015d4bf1c7f3.json](graphify-out/cache/ast/v0.9.8/8fe1008a2240ec060899c86ab4dd722e7a3b216193e67d98640e015d4bf1c7f3.json) |  | 2026-07-30 | 17KB | `00ed602d` |
| [graphify-out/cache/ast/v0.9.8/8fe845c300d58703f6d3594040ca2320ca9d0859f25571be781428841c5f6968.json](graphify-out/cache/ast/v0.9.8/8fe845c300d58703f6d3594040ca2320ca9d0859f25571be781428841c5f6968.json) |  | 2026-07-07 | 22KB | `d44cf75c` |
| [graphify-out/cache/ast/v0.9.8/8ffc43198df59470d7b0c28ab93a09a79f717c6a08899c6450e66018b5b14f64.json](graphify-out/cache/ast/v0.9.8/8ffc43198df59470d7b0c28ab93a09a79f717c6a08899c6450e66018b5b14f64.json) |  | 2026-07-08 | 6KB | `c260c907` |
| [graphify-out/cache/ast/v0.9.8/904f5f719bd8dff33616eeb67f6ccc12ac84caa084efd8dccdc11c23dd5fd95e.json](graphify-out/cache/ast/v0.9.8/904f5f719bd8dff33616eeb67f6ccc12ac84caa084efd8dccdc11c23dd5fd95e.json) |  | 2026-07-08 | 34KB | `9f08d764` |
| [graphify-out/cache/ast/v0.9.8/90a341c604bb542ad442325f5f2dc55d60f23e22fd08a7cfa9e57b79423867ed.json](graphify-out/cache/ast/v0.9.8/90a341c604bb542ad442325f5f2dc55d60f23e22fd08a7cfa9e57b79423867ed.json) |  | 2026-07-07 | 22KB | `03407b1f` |
| [graphify-out/cache/ast/v0.9.8/90a3ab3530352846c0431174d4186a12fc95e27c5c47ac316f76c859bd150888.json](graphify-out/cache/ast/v0.9.8/90a3ab3530352846c0431174d4186a12fc95e27c5c47ac316f76c859bd150888.json) |  | 2026-07-08 | 20KB | `298d19ec` |
| [graphify-out/cache/ast/v0.9.8/90af4ad04e6ead498a0b35346c4add2071b668b4d03527e5a318ba370024d295.json](graphify-out/cache/ast/v0.9.8/90af4ad04e6ead498a0b35346c4add2071b668b4d03527e5a318ba370024d295.json) |  | 2026-07-08 | 4KB | `7a945308` |
| [graphify-out/cache/ast/v0.9.8/90b7f24c11a5c2186ae4c6f079ee44b6e87334f0552a9d90532f3cd68d64db01.json](graphify-out/cache/ast/v0.9.8/90b7f24c11a5c2186ae4c6f079ee44b6e87334f0552a9d90532f3cd68d64db01.json) |  | 2026-07-31 | 17KB | `61e2f7cf` |
| [graphify-out/cache/ast/v0.9.8/90dfaaad457e938a3289069ca9af10ef919a2371333fd8fe238cb4bffea32196.json](graphify-out/cache/ast/v0.9.8/90dfaaad457e938a3289069ca9af10ef919a2371333fd8fe238cb4bffea32196.json) |  | 2026-07-08 | 6KB | `07b1ec02` |
| [graphify-out/cache/ast/v0.9.8/90e00f3cdb0d49c67231d2b5739f662f12a42aaa217a35896e2c0f597c7dc485.json](graphify-out/cache/ast/v0.9.8/90e00f3cdb0d49c67231d2b5739f662f12a42aaa217a35896e2c0f597c7dc485.json) |  | 2026-07-08 | 2KB | `897dc698` |
| [graphify-out/cache/ast/v0.9.8/90e155cda2ffbead2f9e24f6bac8729f620871a55e93ab721026eb92a32f0d3c.json](graphify-out/cache/ast/v0.9.8/90e155cda2ffbead2f9e24f6bac8729f620871a55e93ab721026eb92a32f0d3c.json) |  | 2026-07-08 | 13KB | `7fed457c` |
| [graphify-out/cache/ast/v0.9.8/91306b430611c721a240550d83423a8b922b828b669e7fd0a418bc7decad255d.json](graphify-out/cache/ast/v0.9.8/91306b430611c721a240550d83423a8b922b828b669e7fd0a418bc7decad255d.json) |  | 2026-07-08 | 10KB | `5b777cf9` |
| [graphify-out/cache/ast/v0.9.8/913f6fae144bc0314c8e718d1ddb82ec2fa75f9df59077ad534b03477d240cc2.json](graphify-out/cache/ast/v0.9.8/913f6fae144bc0314c8e718d1ddb82ec2fa75f9df59077ad534b03477d240cc2.json) |  | 2026-07-30 | 13KB | `28db387e` |
| [graphify-out/cache/ast/v0.9.8/91769cb8903f589f5c32880b0cc58be24a4d802e1e9af6cc2d4ecddc1a7e84de.json](graphify-out/cache/ast/v0.9.8/91769cb8903f589f5c32880b0cc58be24a4d802e1e9af6cc2d4ecddc1a7e84de.json) |  | 2026-07-27 | 54KB | `4bf5ab14` |
| [graphify-out/cache/ast/v0.9.8/91b3f7d5027e905b52df088e3a078125395ea09f8d7a3a52ea91b5e2aa109837.json](graphify-out/cache/ast/v0.9.8/91b3f7d5027e905b52df088e3a078125395ea09f8d7a3a52ea91b5e2aa109837.json) |  | 2026-07-24 | 4KB | `5b0edcfc` |
| [graphify-out/cache/ast/v0.9.8/9228460b4ef6fbecff3970ba92f140b6fb8e1f317c640d0f70d219ed88f3e44a.json](graphify-out/cache/ast/v0.9.8/9228460b4ef6fbecff3970ba92f140b6fb8e1f317c640d0f70d219ed88f3e44a.json) |  | 2026-07-08 | 53KB | `92404385` |
| [graphify-out/cache/ast/v0.9.8/9256d440e257b368aa4acfe0986e86c6f697e50e4d5b3f6d47538e54b8ef97ed.json](graphify-out/cache/ast/v0.9.8/9256d440e257b368aa4acfe0986e86c6f697e50e4d5b3f6d47538e54b8ef97ed.json) |  | 2026-07-08 | 6KB | `85644d8f` |
| [graphify-out/cache/ast/v0.9.8/925a2e6fadee873e9db615355f654a251d5ae6f810219b05c58dce160c7788db.json](graphify-out/cache/ast/v0.9.8/925a2e6fadee873e9db615355f654a251d5ae6f810219b05c58dce160c7788db.json) |  | 2026-07-08 | 50KB | `da49e0bb` |
| [graphify-out/cache/ast/v0.9.8/92f75b7b50608e6e3ed29b25e3a38198222ca7b4d2dd2af88c38698d80e0ae44.json](graphify-out/cache/ast/v0.9.8/92f75b7b50608e6e3ed29b25e3a38198222ca7b4d2dd2af88c38698d80e0ae44.json) |  | 2026-07-08 | 6KB | `00e0d32b` |
| [graphify-out/cache/ast/v0.9.8/930f6bf4c0cd42438c05d16802541140f72d1bc579f3bbba8d99f46952bdf6d1.json](graphify-out/cache/ast/v0.9.8/930f6bf4c0cd42438c05d16802541140f72d1bc579f3bbba8d99f46952bdf6d1.json) |  | 2026-07-08 | 6KB | `ac3faa21` |
| [graphify-out/cache/ast/v0.9.8/9345542a04a50e4f49e5af9273272359c34f083f7ed0de8b762f94fcc8aef4ca.json](graphify-out/cache/ast/v0.9.8/9345542a04a50e4f49e5af9273272359c34f083f7ed0de8b762f94fcc8aef4ca.json) |  | 2026-07-08 | 53KB | `280240ea` |
| [graphify-out/cache/ast/v0.9.8/93473ef60f4a5a7e289ebe63ab2aa21057727591d8eedbb10c6bd6a7bfaae120.json](graphify-out/cache/ast/v0.9.8/93473ef60f4a5a7e289ebe63ab2aa21057727591d8eedbb10c6bd6a7bfaae120.json) |  | 2026-07-24 | 13KB | `b7f08139` |
| [graphify-out/cache/ast/v0.9.8/935a01d351cf42cf1d7a44552f22731ac47ca3badcbe333a43ade5ca35a5c31e.json](graphify-out/cache/ast/v0.9.8/935a01d351cf42cf1d7a44552f22731ac47ca3badcbe333a43ade5ca35a5c31e.json) |  | 2026-07-08 | 30KB | `95ce0192` |
| [graphify-out/cache/ast/v0.9.8/936122822138b12f363fb9b7a8567edaa1f834c835137a4c72d81c17116ce11e.json](graphify-out/cache/ast/v0.9.8/936122822138b12f363fb9b7a8567edaa1f834c835137a4c72d81c17116ce11e.json) |  | 2026-07-07 | 1KB | `cb0cfb98` |
| [graphify-out/cache/ast/v0.9.8/9367efe658cfb1a676f16c36302d006bb7430c10b3379a5345a76ba18f934cfa.json](graphify-out/cache/ast/v0.9.8/9367efe658cfb1a676f16c36302d006bb7430c10b3379a5345a76ba18f934cfa.json) |  | 2026-07-29 | 3KB | `b6a0f67f` |
| [graphify-out/cache/ast/v0.9.8/937a060dee53a1dc104b17f65dec3c647b66718d22e1213e37cf1876bc242453.json](graphify-out/cache/ast/v0.9.8/937a060dee53a1dc104b17f65dec3c647b66718d22e1213e37cf1876bc242453.json) |  | 2026-07-08 | 16KB | `206a2b0c` |
| [graphify-out/cache/ast/v0.9.8/938e2fa37596e3677c6773982a8d7dfdcd7dc4b2f78488bd03b326d7e3b65de8.json](graphify-out/cache/ast/v0.9.8/938e2fa37596e3677c6773982a8d7dfdcd7dc4b2f78488bd03b326d7e3b65de8.json) |  | 2026-07-08 | 42KB | `ea7ed268` |
| [graphify-out/cache/ast/v0.9.8/93b06036c8ab07c2de010db9c42088ad30cee51bf307b6fc74688ec7c676b993.json](graphify-out/cache/ast/v0.9.8/93b06036c8ab07c2de010db9c42088ad30cee51bf307b6fc74688ec7c676b993.json) |  | 2026-07-08 | 1KB | `536ad635` |
| [graphify-out/cache/ast/v0.9.8/93fff49a50d4ee710994b5baa92dd35ac0e2c60c9b926361dfa2820e5f86eee9.json](graphify-out/cache/ast/v0.9.8/93fff49a50d4ee710994b5baa92dd35ac0e2c60c9b926361dfa2820e5f86eee9.json) |  | 2026-07-07 | 19KB | `4e859f77` |
| [graphify-out/cache/ast/v0.9.8/940c508d0acc7b056b0fe353f0d606f0ee59c3ba6cdc0fa6fb2bedd7c7c2a9d3.json](graphify-out/cache/ast/v0.9.8/940c508d0acc7b056b0fe353f0d606f0ee59c3ba6cdc0fa6fb2bedd7c7c2a9d3.json) |  | 2026-07-08 | 7KB | `39cc0d7f` |
| [graphify-out/cache/ast/v0.9.8/94126eadb201eebdf55ee29ba7cec4eafbdfeb7b59f054ed81699ed326bb8dea.json](graphify-out/cache/ast/v0.9.8/94126eadb201eebdf55ee29ba7cec4eafbdfeb7b59f054ed81699ed326bb8dea.json) |  | 2026-07-08 | 14KB | `fadaa0d2` |
| [graphify-out/cache/ast/v0.9.8/9480bd64c2ba2c2d40b9852393e0d0c7781229f8e29b3545d6178553e0543973.json](graphify-out/cache/ast/v0.9.8/9480bd64c2ba2c2d40b9852393e0d0c7781229f8e29b3545d6178553e0543973.json) |  | 2026-07-07 | 97KB | `6c38089e` |
| [graphify-out/cache/ast/v0.9.8/94ac8b015db6f2beaf303bc142c2f43ee3947363ade94c9b97f95aad7ff97f1d.json](graphify-out/cache/ast/v0.9.8/94ac8b015db6f2beaf303bc142c2f43ee3947363ade94c9b97f95aad7ff97f1d.json) |  | 2026-07-10 | 8KB | `055f2444` |
| [graphify-out/cache/ast/v0.9.8/94ea56a8507a289077a226cef72b35244318833cb152b13e457656eabe91e1cc.json](graphify-out/cache/ast/v0.9.8/94ea56a8507a289077a226cef72b35244318833cb152b13e457656eabe91e1cc.json) |  | 2026-07-27 | 31KB | `1c697475` |
| [graphify-out/cache/ast/v0.9.8/94ef631ea54a40a14887974be1778590d3f0e68cfb906984644ee5c5627b7b08.json](graphify-out/cache/ast/v0.9.8/94ef631ea54a40a14887974be1778590d3f0e68cfb906984644ee5c5627b7b08.json) |  | 2026-07-07 | 3KB | `f45a8ef4` |
| [graphify-out/cache/ast/v0.9.8/9503ae3e47228c6c448eb091233fdec0471749ac52a6809f8883317c666f9e9e.json](graphify-out/cache/ast/v0.9.8/9503ae3e47228c6c448eb091233fdec0471749ac52a6809f8883317c666f9e9e.json) |  | 2026-08-01 | 3KB | `c387043c` |
| [graphify-out/cache/ast/v0.9.8/9519084224c236c39152f72b32d42af07053c1b7fe09e6a1ae0ab8aa6070e20f.json](graphify-out/cache/ast/v0.9.8/9519084224c236c39152f72b32d42af07053c1b7fe09e6a1ae0ab8aa6070e20f.json) |  | 2026-07-07 | 25KB | `c2b86fef` |
| [graphify-out/cache/ast/v0.9.8/953fd8fd74cc4d6aaa42140f7be63bb0680396e68304c4432c69199fb29c049a.json](graphify-out/cache/ast/v0.9.8/953fd8fd74cc4d6aaa42140f7be63bb0680396e68304c4432c69199fb29c049a.json) |  | 2026-07-08 | 8KB | `3c2f1487` |
| [graphify-out/cache/ast/v0.9.8/955c7c72b0c0e5ab599497453a297ec3f5b7407d3c8e37907d10736c88046fc7.json](graphify-out/cache/ast/v0.9.8/955c7c72b0c0e5ab599497453a297ec3f5b7407d3c8e37907d10736c88046fc7.json) |  | 2026-07-27 | 11KB | `a1379db8` |
| [graphify-out/cache/ast/v0.9.8/959891838a3bdcbf0f768c1e74e1d4edd2947315d36434b0eb6619d8f64b0c7f.json](graphify-out/cache/ast/v0.9.8/959891838a3bdcbf0f768c1e74e1d4edd2947315d36434b0eb6619d8f64b0c7f.json) |  | 2026-07-23 | 98KB | `f2de6908` |
| [graphify-out/cache/ast/v0.9.8/960cef72044394446ea4f1022890ac9c90b5c3226ebaad7b6643ee6ceb76c1d9.json](graphify-out/cache/ast/v0.9.8/960cef72044394446ea4f1022890ac9c90b5c3226ebaad7b6643ee6ceb76c1d9.json) |  | 2026-07-08 | 58KB | `9c4699fa` |
| [graphify-out/cache/ast/v0.9.8/9612557a4803061367440fe418ad72b901b484158716c3f2f8106839fcd2c353.json](graphify-out/cache/ast/v0.9.8/9612557a4803061367440fe418ad72b901b484158716c3f2f8106839fcd2c353.json) |  | 2026-07-07 | 26KB | `2634bb3a` |
| [graphify-out/cache/ast/v0.9.8/96277739c5da55b999bdc7ecedefdbb584b374c573408a2aebc7e2e8d177dfea.json](graphify-out/cache/ast/v0.9.8/96277739c5da55b999bdc7ecedefdbb584b374c573408a2aebc7e2e8d177dfea.json) |  | 2026-07-08 | 14KB | `5eaad856` |
| [graphify-out/cache/ast/v0.9.8/9628b466d2b0c2113df74882298164147325cd09f13d1e30d3e00d54826cf57d.json](graphify-out/cache/ast/v0.9.8/9628b466d2b0c2113df74882298164147325cd09f13d1e30d3e00d54826cf57d.json) |  | 2026-07-08 | 28KB | `a21b1d01` |
| [graphify-out/cache/ast/v0.9.8/96549d841c6bbc248d07f5a0d78262cdef105f6034d47d8da858039108d9b2b0.json](graphify-out/cache/ast/v0.9.8/96549d841c6bbc248d07f5a0d78262cdef105f6034d47d8da858039108d9b2b0.json) |  | 2026-07-08 | 73KB | `1ac212bd` |
| [graphify-out/cache/ast/v0.9.8/96a310366350ba4d8d15faf0c4ff6f5eaad53d202f6bc4bee2a4f88dbb96d7dc.json](graphify-out/cache/ast/v0.9.8/96a310366350ba4d8d15faf0c4ff6f5eaad53d202f6bc4bee2a4f88dbb96d7dc.json) |  | 2026-07-07 | 21KB | `d4545d0f` |
| [graphify-out/cache/ast/v0.9.8/96ce3ffc615dd69bacc0b91762da04e033298673ad34bf50ad6aebefcb07d5d8.json](graphify-out/cache/ast/v0.9.8/96ce3ffc615dd69bacc0b91762da04e033298673ad34bf50ad6aebefcb07d5d8.json) |  | 2026-07-27 | 9KB | `e935575c` |
| [graphify-out/cache/ast/v0.9.8/972756de038b8e4c933fa348487925c268a897e29432974262aca4ffeed494d6.json](graphify-out/cache/ast/v0.9.8/972756de038b8e4c933fa348487925c268a897e29432974262aca4ffeed494d6.json) |  | 2026-07-07 | 17KB | `52e439f5` |
| [graphify-out/cache/ast/v0.9.8/974a3cfc3c59745d1267387ff54f6cbae77f99d356f5f444429a69de88526137.json](graphify-out/cache/ast/v0.9.8/974a3cfc3c59745d1267387ff54f6cbae77f99d356f5f444429a69de88526137.json) |  | 2026-07-09 | 6KB | `a7a28909` |
| [graphify-out/cache/ast/v0.9.8/97a6712d082fd191344bb3cc728e64864089e9e031193a302780b0a3374b408f.json](graphify-out/cache/ast/v0.9.8/97a6712d082fd191344bb3cc728e64864089e9e031193a302780b0a3374b408f.json) |  | 2026-07-22 | 8KB | `72960df6` |
| [graphify-out/cache/ast/v0.9.8/97f43f1caffe8d00aa33ffc63fefdc89aeb37fa0e2ff7d23368dff5995e595b2.json](graphify-out/cache/ast/v0.9.8/97f43f1caffe8d00aa33ffc63fefdc89aeb37fa0e2ff7d23368dff5995e595b2.json) |  | 2026-07-29 | 9KB | `eb52a9f0` |
| [graphify-out/cache/ast/v0.9.8/9822eaaeb609c0e679f6172608ccd1c1cdd5c35642603c084714ed3d15ee2f96.json](graphify-out/cache/ast/v0.9.8/9822eaaeb609c0e679f6172608ccd1c1cdd5c35642603c084714ed3d15ee2f96.json) |  | 2026-07-07 | 22KB | `e4adf3dc` |
| [graphify-out/cache/ast/v0.9.8/988301b60a14dedf01e918ffde291794e3a7831ab84bcebc3bf2f9046c9c69fe.json](graphify-out/cache/ast/v0.9.8/988301b60a14dedf01e918ffde291794e3a7831ab84bcebc3bf2f9046c9c69fe.json) |  | 2026-07-08 | 11KB | `54aca945` |
| [graphify-out/cache/ast/v0.9.8/98e894c4260a729e97109e043e3fd102a925f172a94c2c45ee03864b4a4615ca.json](graphify-out/cache/ast/v0.9.8/98e894c4260a729e97109e043e3fd102a925f172a94c2c45ee03864b4a4615ca.json) |  | 2026-07-08 | 54KB | `778ee011` |
| [graphify-out/cache/ast/v0.9.8/990b064994413104b2c1d8fec8f341625435e1e448840d6b7e2be136c0ac0e4f.json](graphify-out/cache/ast/v0.9.8/990b064994413104b2c1d8fec8f341625435e1e448840d6b7e2be136c0ac0e4f.json) |  | 2026-07-07 | 13KB | `329a4a83` |
| [graphify-out/cache/ast/v0.9.8/992fd7d199306821c3c97bcc5cd3c4fcc169a2e7906ef565539b89ae3a189ef0.json](graphify-out/cache/ast/v0.9.8/992fd7d199306821c3c97bcc5cd3c4fcc169a2e7906ef565539b89ae3a189ef0.json) |  | 2026-07-08 | 8KB | `7aa4e591` |
| [graphify-out/cache/ast/v0.9.8/9988e66e343a4b8576b61dbceb777ab77e87c31683aae034d44fdbea2cb7c9bd.json](graphify-out/cache/ast/v0.9.8/9988e66e343a4b8576b61dbceb777ab77e87c31683aae034d44fdbea2cb7c9bd.json) |  | 2026-07-08 | 197KB | `88c1798e` |
| [graphify-out/cache/ast/v0.9.8/99c949d937b6a92de3743516ee7c6329c3ef8679f588a9029e2f0bdac026a96a.json](graphify-out/cache/ast/v0.9.8/99c949d937b6a92de3743516ee7c6329c3ef8679f588a9029e2f0bdac026a96a.json) |  | 2026-07-07 | 3KB | `0460c1ae` |
| [graphify-out/cache/ast/v0.9.8/99f645b5b894786494bc07b933922dcd139f85763805f7c19a977fcd20a6a07e.json](graphify-out/cache/ast/v0.9.8/99f645b5b894786494bc07b933922dcd139f85763805f7c19a977fcd20a6a07e.json) |  | 2026-07-08 | 97KB | `6c38089e` |
| [graphify-out/cache/ast/v0.9.8/9a0b5e517792fd9f6c993c6d979687601347016ac503f02a67d26221f6d44fe0.json](graphify-out/cache/ast/v0.9.8/9a0b5e517792fd9f6c993c6d979687601347016ac503f02a67d26221f6d44fe0.json) |  | 2026-07-08 | 23KB | `cf0dba88` |
| [graphify-out/cache/ast/v0.9.8/9a483eb7cd0f0e2865e4c3bd5f68a26b51e6d4c794c98bccadcb19aefca39f3b.json](graphify-out/cache/ast/v0.9.8/9a483eb7cd0f0e2865e4c3bd5f68a26b51e6d4c794c98bccadcb19aefca39f3b.json) |  | 2026-07-08 | 2KB | `3ca537d6` |
| [graphify-out/cache/ast/v0.9.8/9a6fc04710b0bdfba59698bcddb74e87ae22229d45092667c6f1258671b79140.json](graphify-out/cache/ast/v0.9.8/9a6fc04710b0bdfba59698bcddb74e87ae22229d45092667c6f1258671b79140.json) |  | 2026-07-31 | 9KB | `47ef4341` |
| [graphify-out/cache/ast/v0.9.8/9a8078bc3e15c34e09f3d39c8f93039cbf734b7077ead72f8a23a8e9fbb4f3c0.json](graphify-out/cache/ast/v0.9.8/9a8078bc3e15c34e09f3d39c8f93039cbf734b7077ead72f8a23a8e9fbb4f3c0.json) |  | 2026-07-30 | 8KB | `9475d90e` |
| [graphify-out/cache/ast/v0.9.8/9abe8ccebfb2e39d6c586b1534a144c01af39a313344706bfc348e97e0c08c3a.json](graphify-out/cache/ast/v0.9.8/9abe8ccebfb2e39d6c586b1534a144c01af39a313344706bfc348e97e0c08c3a.json) |  | 2026-07-08 | 15KB | `8052be46` |
| [graphify-out/cache/ast/v0.9.8/9aded5bf4335df33a3941bf908f6a13a58956239149a53b4972845a3b22f92f6.json](graphify-out/cache/ast/v0.9.8/9aded5bf4335df33a3941bf908f6a13a58956239149a53b4972845a3b22f92f6.json) |  | 2026-07-08 | 14KB | `37818ed7` |
| [graphify-out/cache/ast/v0.9.8/9b2b37114b60284b82dac1a48275f355eaa9cd939ba32869b0db014077d79ee8.json](graphify-out/cache/ast/v0.9.8/9b2b37114b60284b82dac1a48275f355eaa9cd939ba32869b0db014077d79ee8.json) |  | 2026-07-08 | 27KB | `e577d353` |
| [graphify-out/cache/ast/v0.9.8/9b61cd6fb467a7ca1f5a617a17f897413562ec4f1c7f34838ad6a28198d84442.json](graphify-out/cache/ast/v0.9.8/9b61cd6fb467a7ca1f5a617a17f897413562ec4f1c7f34838ad6a28198d84442.json) |  | 2026-07-07 | 19KB | `f6d640e6` |
| [graphify-out/cache/ast/v0.9.8/9baeb13d5014a49c2abdfdaea0f270f0681389ae6df80ea4298fc98f703978c0.json](graphify-out/cache/ast/v0.9.8/9baeb13d5014a49c2abdfdaea0f270f0681389ae6df80ea4298fc98f703978c0.json) |  | 2026-07-30 | 8KB | `c4c4dc15` |
| [graphify-out/cache/ast/v0.9.8/9bb2db0c227572494a7740e37ba569e3e39d3adfab64f28f53652f01b9269e5d.json](graphify-out/cache/ast/v0.9.8/9bb2db0c227572494a7740e37ba569e3e39d3adfab64f28f53652f01b9269e5d.json) |  | 2026-07-08 | 14KB | `695da6d5` |
| [graphify-out/cache/ast/v0.9.8/9bcd93644af9c654594dae3296de794b7078941e0546307bca03ca212634db7c.json](graphify-out/cache/ast/v0.9.8/9bcd93644af9c654594dae3296de794b7078941e0546307bca03ca212634db7c.json) |  | 2026-07-07 | 15KB | `ed64231f` |
| [graphify-out/cache/ast/v0.9.8/9be770429753625e5a065bf97aab95adb58abd939ba4f36e626d76bef368b90f.json](graphify-out/cache/ast/v0.9.8/9be770429753625e5a065bf97aab95adb58abd939ba4f36e626d76bef368b90f.json) |  | 2026-07-08 | 3KB | `e3c1712e` |
| [graphify-out/cache/ast/v0.9.8/9c1ea40a1f3eba4e5fca9adfb951c29d6ce25b7b2d2ffccf5af9615a9b544579.json](graphify-out/cache/ast/v0.9.8/9c1ea40a1f3eba4e5fca9adfb951c29d6ce25b7b2d2ffccf5af9615a9b544579.json) |  | 2026-07-08 | 17KB | `541f006b` |
| [graphify-out/cache/ast/v0.9.8/9c862ad965581f24d92325ee0dda1a3ce3b84b79c46cb7fbd2d52690c7a3121c.json](graphify-out/cache/ast/v0.9.8/9c862ad965581f24d92325ee0dda1a3ce3b84b79c46cb7fbd2d52690c7a3121c.json) |  | 2026-07-07 | 33KB | `bb68712b` |
| [graphify-out/cache/ast/v0.9.8/9c89dd7f953cb4793d31d6571a566e8618ccea9313730f2711e7e525ec8d54ff.json](graphify-out/cache/ast/v0.9.8/9c89dd7f953cb4793d31d6571a566e8618ccea9313730f2711e7e525ec8d54ff.json) |  | 2026-07-08 | 6KB | `e380ab88` |
| [graphify-out/cache/ast/v0.9.8/9cd3be0072b426fded4b2a48aeb500b9e4b0c368ccc02a115aa5037f6b87f697.json](graphify-out/cache/ast/v0.9.8/9cd3be0072b426fded4b2a48aeb500b9e4b0c368ccc02a115aa5037f6b87f697.json) |  | 2026-07-08 | 4KB | `e7ffb256` |
| [graphify-out/cache/ast/v0.9.8/9cfef2a8961df5968cc7a90c9329684c64b564814b0d98429c2db32739b13ce8.json](graphify-out/cache/ast/v0.9.8/9cfef2a8961df5968cc7a90c9329684c64b564814b0d98429c2db32739b13ce8.json) |  | 2026-07-08 | 9KB | `92aab347` |
| [graphify-out/cache/ast/v0.9.8/9d38a42db78e4384d9c24971a412bd829eff0b50cd10423bd1e9d69919f3fa2c.json](graphify-out/cache/ast/v0.9.8/9d38a42db78e4384d9c24971a412bd829eff0b50cd10423bd1e9d69919f3fa2c.json) |  | 2026-07-30 | 8KB | `8ef96e75` |
| [graphify-out/cache/ast/v0.9.8/9d710fd4aa609a83d326a3234a2cbeddfd9f64c2e71e3aa37b2055d571982988.json](graphify-out/cache/ast/v0.9.8/9d710fd4aa609a83d326a3234a2cbeddfd9f64c2e71e3aa37b2055d571982988.json) |  | 2026-07-31 | 7KB | `cdbc75ed` |
| [graphify-out/cache/ast/v0.9.8/9d947360d0a5b81639d5cbb0fa3ea76082fbadf6aab450386c2947d1847d7aca.json](graphify-out/cache/ast/v0.9.8/9d947360d0a5b81639d5cbb0fa3ea76082fbadf6aab450386c2947d1847d7aca.json) |  | 2026-07-08 | 14KB | `b9ab27b6` |
| [graphify-out/cache/ast/v0.9.8/9db4c87d8b46541c5de9a3b3a2ebb8e2d9f1f7e4d730862be77babb40a610cac.json](graphify-out/cache/ast/v0.9.8/9db4c87d8b46541c5de9a3b3a2ebb8e2d9f1f7e4d730862be77babb40a610cac.json) |  | 2026-07-08 | 47KB | `0a48ecff` |
| [graphify-out/cache/ast/v0.9.8/9de4c0d2dace501fc4525c065472346da85f8b8f0886925df8a6af098a5842bb.json](graphify-out/cache/ast/v0.9.8/9de4c0d2dace501fc4525c065472346da85f8b8f0886925df8a6af098a5842bb.json) |  | 2026-07-08 | 4KB | `d49b93d8` |
| [graphify-out/cache/ast/v0.9.8/9df850c33908200fd190ab9128680e8abf04e9affbffc3c7d8796357c4adc59a.json](graphify-out/cache/ast/v0.9.8/9df850c33908200fd190ab9128680e8abf04e9affbffc3c7d8796357c4adc59a.json) |  | 2026-07-07 | 13KB | `654dd26f` |
| [graphify-out/cache/ast/v0.9.8/9e9b050d66eeae01877ddd5d57d5bcc4151e666a2fdb8dd2df7088d9c07d1f18.json](graphify-out/cache/ast/v0.9.8/9e9b050d66eeae01877ddd5d57d5bcc4151e666a2fdb8dd2df7088d9c07d1f18.json) |  | 2026-07-24 | 57KB | `71354035` |
| [graphify-out/cache/ast/v0.9.8/9eb74370f1506aac15bab4c88de767fb4bb0bb20d2f0e7ee7f6c185271305ae4.json](graphify-out/cache/ast/v0.9.8/9eb74370f1506aac15bab4c88de767fb4bb0bb20d2f0e7ee7f6c185271305ae4.json) |  | 2026-07-07 | 10KB | `3fbe90bf` |
| [graphify-out/cache/ast/v0.9.8/9f529b2f588adaffa0a6b2172a273dfb1573f70cd3995af7b13c9745185e0f53.json](graphify-out/cache/ast/v0.9.8/9f529b2f588adaffa0a6b2172a273dfb1573f70cd3995af7b13c9745185e0f53.json) |  | 2026-07-10 | 12KB | `375cea69` |
| [graphify-out/cache/ast/v0.9.8/9f916c7992cbe4356168669d86a0afa0159fb0c6b23125660e7d3581d326c893.json](graphify-out/cache/ast/v0.9.8/9f916c7992cbe4356168669d86a0afa0159fb0c6b23125660e7d3581d326c893.json) |  | 2026-07-08 | 125KB | `702f9052` |
| [graphify-out/cache/ast/v0.9.8/9fe250540e6d57c160b57ade51347a308be7b3546c1f727f3413d92a6f740278.json](graphify-out/cache/ast/v0.9.8/9fe250540e6d57c160b57ade51347a308be7b3546c1f727f3413d92a6f740278.json) |  | 2026-07-08 | 11KB | `2c3282b1` |
| [graphify-out/cache/ast/v0.9.8/9ffcc17063619cc2a7c4c3cf36fa19345f5d3e45acae2337d25acd3fb1c0a04f.json](graphify-out/cache/ast/v0.9.8/9ffcc17063619cc2a7c4c3cf36fa19345f5d3e45acae2337d25acd3fb1c0a04f.json) |  | 2026-07-07 | 11KB | `36b177d9` |
| [graphify-out/cache/ast/v0.9.8/a006d114fce553764df863267ddcac15f7676983ebf26266aeb173957580a2b9.json](graphify-out/cache/ast/v0.9.8/a006d114fce553764df863267ddcac15f7676983ebf26266aeb173957580a2b9.json) |  | 2026-07-08 | 10KB | `44963761` |
| [graphify-out/cache/ast/v0.9.8/a008382362b1da472352e91146ef36e930c491987e477b6bb18946710bdaca50.json](graphify-out/cache/ast/v0.9.8/a008382362b1da472352e91146ef36e930c491987e477b6bb18946710bdaca50.json) |  | 2026-07-08 | 2KB | `c6dda437` |
| [graphify-out/cache/ast/v0.9.8/a00bb16094d4596cd57f11ec5d2c9a4489940443ee423d861cd72643a6b06da3.json](graphify-out/cache/ast/v0.9.8/a00bb16094d4596cd57f11ec5d2c9a4489940443ee423d861cd72643a6b06da3.json) |  | 2026-07-08 | 6KB | `b7c1006c` |
| [graphify-out/cache/ast/v0.9.8/a04f6a5ddbe7e1114d760191de032d47af5bbe0e3ef27f175309712dc6834646.json](graphify-out/cache/ast/v0.9.8/a04f6a5ddbe7e1114d760191de032d47af5bbe0e3ef27f175309712dc6834646.json) |  | 2026-07-07 | 7KB | `bf6f49d6` |
| [graphify-out/cache/ast/v0.9.8/a0591b58bfa24fdc07d0e5755a51eda5fdf9f6e631efa5d92a2dd4977b1ce5e2.json](graphify-out/cache/ast/v0.9.8/a0591b58bfa24fdc07d0e5755a51eda5fdf9f6e631efa5d92a2dd4977b1ce5e2.json) |  | 2026-07-07 | 2KB | `ec96b780` |
| [graphify-out/cache/ast/v0.9.8/a05f81f678ad4ee3d1ee48e8849ffa8f093ce60794d4d01912066c6eebfc6b4a.json](graphify-out/cache/ast/v0.9.8/a05f81f678ad4ee3d1ee48e8849ffa8f093ce60794d4d01912066c6eebfc6b4a.json) |  | 2026-07-08 | 25KB | `d100186a` |
| [graphify-out/cache/ast/v0.9.8/a11c260624f564cd4dcfb6732822f3b45100be91e4af49d3432269ea31fd495a.json](graphify-out/cache/ast/v0.9.8/a11c260624f564cd4dcfb6732822f3b45100be91e4af49d3432269ea31fd495a.json) |  | 2026-07-08 | 4KB | `9d52d2f8` |
| [graphify-out/cache/ast/v0.9.8/a1255a3b588b2daa9fbe65e8100bed11aa629e957dc27298fb4a69022dfae062.json](graphify-out/cache/ast/v0.9.8/a1255a3b588b2daa9fbe65e8100bed11aa629e957dc27298fb4a69022dfae062.json) |  | 2026-07-08 | 66KB | `b15d64f8` |
| [graphify-out/cache/ast/v0.9.8/a12c984903befc0abf5de574ccc13ece0107aa2e423efabf2d2f4d0e842d4772.json](graphify-out/cache/ast/v0.9.8/a12c984903befc0abf5de574ccc13ece0107aa2e423efabf2d2f4d0e842d4772.json) |  | 2026-07-07 | 5KB | `4a1b90fd` |
| [graphify-out/cache/ast/v0.9.8/a1333970037f3a017cf56241196c29904f845789f51aa33432d68da17f284327.json](graphify-out/cache/ast/v0.9.8/a1333970037f3a017cf56241196c29904f845789f51aa33432d68da17f284327.json) |  | 2026-07-08 | 61KB | `e873e2df` |
| [graphify-out/cache/ast/v0.9.8/a1847d0b25e4c26e8a4b0281ac5ec169d5219e66c50a55b1aad4572a8c01d946.json](graphify-out/cache/ast/v0.9.8/a1847d0b25e4c26e8a4b0281ac5ec169d5219e66c50a55b1aad4572a8c01d946.json) |  | 2026-07-07 | 16KB | `a42b8320` |
| [graphify-out/cache/ast/v0.9.8/a18fa8393dfec91d32e34efd5f8f99aecf299dc41fcf89cf399becb6bbccf5d4.json](graphify-out/cache/ast/v0.9.8/a18fa8393dfec91d32e34efd5f8f99aecf299dc41fcf89cf399becb6bbccf5d4.json) |  | 2026-07-23 | 16KB | `5fa67b54` |
| [graphify-out/cache/ast/v0.9.8/a1e7c21338055a4f6f60a8f9cb6f3e497912c305aece1e4150773af37f22f585.json](graphify-out/cache/ast/v0.9.8/a1e7c21338055a4f6f60a8f9cb6f3e497912c305aece1e4150773af37f22f585.json) |  | 2026-07-08 | 6KB | `575e33ad` |
| [graphify-out/cache/ast/v0.9.8/a21a114d555c1d3a27fbeeec09b09e0d68347405ddbd781d70ca38865767961a.json](graphify-out/cache/ast/v0.9.8/a21a114d555c1d3a27fbeeec09b09e0d68347405ddbd781d70ca38865767961a.json) |  | 2026-07-08 | 15KB | `2277ca50` |
| [graphify-out/cache/ast/v0.9.8/a239b7352b3e2d684db0ffebb5d42a8ee02e3bd1b0c4d48a1bc8e8088ab8c0f6.json](graphify-out/cache/ast/v0.9.8/a239b7352b3e2d684db0ffebb5d42a8ee02e3bd1b0c4d48a1bc8e8088ab8c0f6.json) |  | 2026-07-08 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/a264bdc65f1dfd2f4958886724c5e084994fdc3c07ddc7e81c0c01389a890204.json](graphify-out/cache/ast/v0.9.8/a264bdc65f1dfd2f4958886724c5e084994fdc3c07ddc7e81c0c01389a890204.json) |  | 2026-07-08 | 17KB | `a88795df` |
| [graphify-out/cache/ast/v0.9.8/a27fb1a3178895393613dbc1d493872a0a9422f1fadfb9ddd3a49d367e99f112.json](graphify-out/cache/ast/v0.9.8/a27fb1a3178895393613dbc1d493872a0a9422f1fadfb9ddd3a49d367e99f112.json) |  | 2026-07-07 | 22KB | `7b375b5c` |
| [graphify-out/cache/ast/v0.9.8/a298e86eb8571c16239ce42ecb3fede48b5eeae5473b93e175e751914dfd5675.json](graphify-out/cache/ast/v0.9.8/a298e86eb8571c16239ce42ecb3fede48b5eeae5473b93e175e751914dfd5675.json) |  | 2026-07-08 | 2KB | `4bc7dffb` |
| [graphify-out/cache/ast/v0.9.8/a2aa312a51fe36b1c317d86f427ac957a553344f5783e10879e8ca67a0bb3e41.json](graphify-out/cache/ast/v0.9.8/a2aa312a51fe36b1c317d86f427ac957a553344f5783e10879e8ca67a0bb3e41.json) |  | 2026-07-08 | 6KB | `3d7faa7d` |
| [graphify-out/cache/ast/v0.9.8/a2b3575bc6f0cf67a374804c8569d0efdd4b44ac032b54b847a31b42095cc222.json](graphify-out/cache/ast/v0.9.8/a2b3575bc6f0cf67a374804c8569d0efdd4b44ac032b54b847a31b42095cc222.json) |  | 2026-07-08 | 45KB | `ed6992da` |
| [graphify-out/cache/ast/v0.9.8/a2bdaf6cf52fdf6ee28b576ebe2c2a4f61059b8481cce3f84b5213b08627290c.json](graphify-out/cache/ast/v0.9.8/a2bdaf6cf52fdf6ee28b576ebe2c2a4f61059b8481cce3f84b5213b08627290c.json) |  | 2026-07-07 | 5KB | `e840a600` |
| [graphify-out/cache/ast/v0.9.8/a2d135d23cea989c9f43db2d5d5fcf6f347f70666cb40679cc6ba4707302c239.json](graphify-out/cache/ast/v0.9.8/a2d135d23cea989c9f43db2d5d5fcf6f347f70666cb40679cc6ba4707302c239.json) |  | 2026-07-07 | 22KB | `32b2a429` |
| [graphify-out/cache/ast/v0.9.8/a30d0c590d763ed0bb6426d0c76f5ca4767e137d31a5ac7b08f51b9d476fe928.json](graphify-out/cache/ast/v0.9.8/a30d0c590d763ed0bb6426d0c76f5ca4767e137d31a5ac7b08f51b9d476fe928.json) |  | 2026-07-30 | 11KB | `5dccad8a` |
| [graphify-out/cache/ast/v0.9.8/a4027aafd61861c100aa90ebe9f10afb604cb8d38f93244d446440c2141a3e8e.json](graphify-out/cache/ast/v0.9.8/a4027aafd61861c100aa90ebe9f10afb604cb8d38f93244d446440c2141a3e8e.json) |  | 2026-07-08 | 4KB | `4942af5c` |
| [graphify-out/cache/ast/v0.9.8/a404ab1087448f888bbbf85c0fdbee00e9ef72378155dbb7ea3456a807d00dae.json](graphify-out/cache/ast/v0.9.8/a404ab1087448f888bbbf85c0fdbee00e9ef72378155dbb7ea3456a807d00dae.json) |  | 2026-07-29 | 9KB | `645eb8fe` |
| [graphify-out/cache/ast/v0.9.8/a41afbe6dc0224d48dfb3178271e2e20322b66628dc782f654602e088689022c.json](graphify-out/cache/ast/v0.9.8/a41afbe6dc0224d48dfb3178271e2e20322b66628dc782f654602e088689022c.json) |  | 2026-07-08 | 49KB | `1449122d` |
| [graphify-out/cache/ast/v0.9.8/a42e35ad214b62b9d2f4207e951ed213cc10f8ced90558298d3ab29bf9431d20.json](graphify-out/cache/ast/v0.9.8/a42e35ad214b62b9d2f4207e951ed213cc10f8ced90558298d3ab29bf9431d20.json) |  | 2026-07-07 | 19KB | `c8283d8a` |
| [graphify-out/cache/ast/v0.9.8/a47c434cf0e956fe56f733cd032980677cf8ac278ef2fab38c4f3b93b186da61.json](graphify-out/cache/ast/v0.9.8/a47c434cf0e956fe56f733cd032980677cf8ac278ef2fab38c4f3b93b186da61.json) |  | 2026-07-20 | 9KB | `e6f42dcc` |
| [graphify-out/cache/ast/v0.9.8/a4b417464e1d490893f6c712963b90412d5d02f3f85189e324b4c947892401e4.json](graphify-out/cache/ast/v0.9.8/a4b417464e1d490893f6c712963b90412d5d02f3f85189e324b4c947892401e4.json) |  | 2026-07-07 | 15KB | `d89f7c20` |
| [graphify-out/cache/ast/v0.9.8/a4e57b554ef81cbfaf8eabfc598d1eeb67d6c3720f8a86821c0de9bb2740ad5b.json](graphify-out/cache/ast/v0.9.8/a4e57b554ef81cbfaf8eabfc598d1eeb67d6c3720f8a86821c0de9bb2740ad5b.json) |  | 2026-07-24 | 54KB | `fb7f8c70` |
| [graphify-out/cache/ast/v0.9.8/a536969a05ec8c2f63092be767a13864737bfd0a004259703b04cfe1e33cb5c6.json](graphify-out/cache/ast/v0.9.8/a536969a05ec8c2f63092be767a13864737bfd0a004259703b04cfe1e33cb5c6.json) |  | 2026-07-07 | 16KB | `b3ac3ee9` |
| [graphify-out/cache/ast/v0.9.8/a59ea3dd521155cef11f48247d36f7d75c47dec78e8eda7cc86ce5b9388fc325.json](graphify-out/cache/ast/v0.9.8/a59ea3dd521155cef11f48247d36f7d75c47dec78e8eda7cc86ce5b9388fc325.json) |  | 2026-07-29 | 56KB | `efeccd9d` |
| [graphify-out/cache/ast/v0.9.8/a5d16e94efd764ebab19b2918b9f6ffc61451109ae6015245000d820f2df1e66.json](graphify-out/cache/ast/v0.9.8/a5d16e94efd764ebab19b2918b9f6ffc61451109ae6015245000d820f2df1e66.json) |  | 2026-07-08 | 19KB | `2d650633` |
| [graphify-out/cache/ast/v0.9.8/a5db4aa0a1fcfd03fc92577e0240ae3f0d9161d6288db5b10143cffd01bd22f9.json](graphify-out/cache/ast/v0.9.8/a5db4aa0a1fcfd03fc92577e0240ae3f0d9161d6288db5b10143cffd01bd22f9.json) |  | 2026-07-08 | 16KB | `f5387239` |
| [graphify-out/cache/ast/v0.9.8/a5f063dbf051a316de990c9d754da6d401e9600d028c96adbd1b1bf2f58e2b11.json](graphify-out/cache/ast/v0.9.8/a5f063dbf051a316de990c9d754da6d401e9600d028c96adbd1b1bf2f58e2b11.json) |  | 2026-07-08 | 17KB | `efe593ac` |
| [graphify-out/cache/ast/v0.9.8/a5ff158c9dec02fa7c58c020676839f81f86d633b2cfdb0d64c507420d753305.json](graphify-out/cache/ast/v0.9.8/a5ff158c9dec02fa7c58c020676839f81f86d633b2cfdb0d64c507420d753305.json) |  | 2026-07-08 | 37KB | `b4f947b5` |
| [graphify-out/cache/ast/v0.9.8/a63be16d6223f623cefe9331b35043bf6e92e9f37e9c02eb10674f40abf8fd71.json](graphify-out/cache/ast/v0.9.8/a63be16d6223f623cefe9331b35043bf6e92e9f37e9c02eb10674f40abf8fd71.json) |  | 2026-07-08 | 13KB | `fc1dde50` |
| [graphify-out/cache/ast/v0.9.8/a6a72d98b5392da5e89c993d40cea93ae1f88c56ffa82b1a850cad3819cf7388.json](graphify-out/cache/ast/v0.9.8/a6a72d98b5392da5e89c993d40cea93ae1f88c56ffa82b1a850cad3819cf7388.json) |  | 2026-07-23 | 7KB | `ea3eb173` |
| [graphify-out/cache/ast/v0.9.8/a6a9a842009cfccb966482b49653fc3eb844343b30b15b38e9d8b06dc1de5e47.json](graphify-out/cache/ast/v0.9.8/a6a9a842009cfccb966482b49653fc3eb844343b30b15b38e9d8b06dc1de5e47.json) |  | 2026-07-07 | 16KB | `f7808b20` |
| [graphify-out/cache/ast/v0.9.8/a6daad232ce9ef112c35637cdca69da3d4fac309adc0f203f87d7acdfa91eb10.json](graphify-out/cache/ast/v0.9.8/a6daad232ce9ef112c35637cdca69da3d4fac309adc0f203f87d7acdfa91eb10.json) |  | 2026-07-08 | 6KB | `7f03108f` |
| [graphify-out/cache/ast/v0.9.8/a6e09565398ee5640cfe0c40f0e88506523f5ea2d730b16a8a572cad96cce742.json](graphify-out/cache/ast/v0.9.8/a6e09565398ee5640cfe0c40f0e88506523f5ea2d730b16a8a572cad96cce742.json) |  | 2026-07-08 | 41KB | `5b02d655` |
| [graphify-out/cache/ast/v0.9.8/a7b2e4e2a6f138e3e48942c1c828349d578e9398ac2f088d1260ba13f807eeb1.json](graphify-out/cache/ast/v0.9.8/a7b2e4e2a6f138e3e48942c1c828349d578e9398ac2f088d1260ba13f807eeb1.json) |  | 2026-07-08 | 8KB | `16710a0d` |
| [graphify-out/cache/ast/v0.9.8/a7d4e0b0d378c1cc9d3013d43205346d817f8a6de4d03866b02789744a676df4.json](graphify-out/cache/ast/v0.9.8/a7d4e0b0d378c1cc9d3013d43205346d817f8a6de4d03866b02789744a676df4.json) |  | 2026-07-08 | 65KB | `7d6b9889` |
| [graphify-out/cache/ast/v0.9.8/a8206b8e21ecb51f6b376398dbd79fabce539c6d8ae5f536986da4d61b5002a7.json](graphify-out/cache/ast/v0.9.8/a8206b8e21ecb51f6b376398dbd79fabce539c6d8ae5f536986da4d61b5002a7.json) |  | 2026-07-29 | 3KB | `2211f62e` |
| [graphify-out/cache/ast/v0.9.8/a86b7035ee0b4077f3ba5e6e8861f2286abe6404971ed336c1f170dab80def68.json](graphify-out/cache/ast/v0.9.8/a86b7035ee0b4077f3ba5e6e8861f2286abe6404971ed336c1f170dab80def68.json) |  | 2026-07-08 | 31KB | `89b561ae` |
| [graphify-out/cache/ast/v0.9.8/a891bb5de614fffba4be1c4a7a06f4b1e04bd3f36340c754737e8e2df05b8a94.json](graphify-out/cache/ast/v0.9.8/a891bb5de614fffba4be1c4a7a06f4b1e04bd3f36340c754737e8e2df05b8a94.json) |  | 2026-07-08 | 6KB | `90016b03` |
| [graphify-out/cache/ast/v0.9.8/a8b34029a5cafa149ebbc357c9e23dd94f803b5e426ae650202c9e060be171f7.json](graphify-out/cache/ast/v0.9.8/a8b34029a5cafa149ebbc357c9e23dd94f803b5e426ae650202c9e060be171f7.json) |  | 2026-07-09 | 4KB | `3b330bfd` |
| [graphify-out/cache/ast/v0.9.8/a9330cd12d806432d444c0cff54cea2433750c23c913dc4f302780343af88d93.json](graphify-out/cache/ast/v0.9.8/a9330cd12d806432d444c0cff54cea2433750c23c913dc4f302780343af88d93.json) |  | 2026-07-08 | 7KB | `549a7f81` |
| [graphify-out/cache/ast/v0.9.8/a9579435b6c2f5a40f4fe95e83fd4cb2a518af0a0aad7f769f5491b6785cc79b.json](graphify-out/cache/ast/v0.9.8/a9579435b6c2f5a40f4fe95e83fd4cb2a518af0a0aad7f769f5491b6785cc79b.json) |  | 2026-07-08 | 7KB | `c2ddc190` |
| [graphify-out/cache/ast/v0.9.8/a971c550eb4d37b1ca047efaeaf0f824b3e744b931c560f1910b8750a33dac03.json](graphify-out/cache/ast/v0.9.8/a971c550eb4d37b1ca047efaeaf0f824b3e744b931c560f1910b8750a33dac03.json) |  | 2026-07-08 | 111KB | `b316354e` |
| [graphify-out/cache/ast/v0.9.8/a9c92727a0f2cb84bafa242dacea9823f1bc334250b98ccf79e1f47ecbb974b7.json](graphify-out/cache/ast/v0.9.8/a9c92727a0f2cb84bafa242dacea9823f1bc334250b98ccf79e1f47ecbb974b7.json) |  | 2026-07-08 | 6KB | `b249a1a2` |
| [graphify-out/cache/ast/v0.9.8/aa0896cf86f337ddae55f99575c92a308e99e03b36fdc8af28d1e54beb6649f8.json](graphify-out/cache/ast/v0.9.8/aa0896cf86f337ddae55f99575c92a308e99e03b36fdc8af28d1e54beb6649f8.json) |  | 2026-07-08 | 7KB | `2d681ccb` |
| [graphify-out/cache/ast/v0.9.8/aa14236f6c5d9bea81fc6f44e1819ddfee3509b010f53285fb01eef24c0a0638.json](graphify-out/cache/ast/v0.9.8/aa14236f6c5d9bea81fc6f44e1819ddfee3509b010f53285fb01eef24c0a0638.json) |  | 2026-07-08 | 4KB | `6b4f58cb` |
| [graphify-out/cache/ast/v0.9.8/aa2f65da384867ed29f223ab1689e7cabe1c238885082f0634f99e1cd7bf9c61.json](graphify-out/cache/ast/v0.9.8/aa2f65da384867ed29f223ab1689e7cabe1c238885082f0634f99e1cd7bf9c61.json) |  | 2026-07-08 | 20KB | `c37cb7a1` |
| [graphify-out/cache/ast/v0.9.8/aa32ce306909fa22f8c3a0950d8a30124e2d04c801d117b99965c8a444c14e1e.json](graphify-out/cache/ast/v0.9.8/aa32ce306909fa22f8c3a0950d8a30124e2d04c801d117b99965c8a444c14e1e.json) |  | 2026-07-08 | 2KB | `4483ed1a` |
| [graphify-out/cache/ast/v0.9.8/aa6b63c975decaa98821410d7bec80fa55c1c0dd153e4d79259c38b27906d3f5.json](graphify-out/cache/ast/v0.9.8/aa6b63c975decaa98821410d7bec80fa55c1c0dd153e4d79259c38b27906d3f5.json) |  | 2026-07-30 | 841B | `7bb666ef` |
| [graphify-out/cache/ast/v0.9.8/aae0d01819c844e26ce7c0fae694bd13efc37279a3429aa013e4fc58b1f7db67.json](graphify-out/cache/ast/v0.9.8/aae0d01819c844e26ce7c0fae694bd13efc37279a3429aa013e4fc58b1f7db67.json) |  | 2026-07-10 | 8KB | `4a1179f9` |
| [graphify-out/cache/ast/v0.9.8/abc49f5ab9f30f5f88de4f94803efa2c72106a1f2df135afd1c99ebf60c2957e.json](graphify-out/cache/ast/v0.9.8/abc49f5ab9f30f5f88de4f94803efa2c72106a1f2df135afd1c99ebf60c2957e.json) |  | 2026-07-08 | 25KB | `28e7ef3a` |
| [graphify-out/cache/ast/v0.9.8/ac025551ad4fde68c75967d401491df8694e7a5471cac8b6ec5448c198e986e5.json](graphify-out/cache/ast/v0.9.8/ac025551ad4fde68c75967d401491df8694e7a5471cac8b6ec5448c198e986e5.json) |  | 2026-07-08 | 9KB | `6caea5d4` |
| [graphify-out/cache/ast/v0.9.8/ac13aa6c4a09f91d5f8b95cbff59c710be54a0cb38730244201702d7547ba3a0.json](graphify-out/cache/ast/v0.9.8/ac13aa6c4a09f91d5f8b95cbff59c710be54a0cb38730244201702d7547ba3a0.json) |  | 2026-07-07 | 864B | `f590c59f` |
| [graphify-out/cache/ast/v0.9.8/ac2d5360b0de17ff3b1a35f0627df4b1e1d84b0dc4488543e936e3a8cd3a4f6f.json](graphify-out/cache/ast/v0.9.8/ac2d5360b0de17ff3b1a35f0627df4b1e1d84b0dc4488543e936e3a8cd3a4f6f.json) |  | 2026-07-08 | 9KB | `3ed829d8` |
| [graphify-out/cache/ast/v0.9.8/ac40f45aab5976f4759dc5cd79ba3a8c2931b78fd42ac84ee2d0339b72964b49.json](graphify-out/cache/ast/v0.9.8/ac40f45aab5976f4759dc5cd79ba3a8c2931b78fd42ac84ee2d0339b72964b49.json) |  | 2026-07-08 | 9KB | `8f6bdb99` |
| [graphify-out/cache/ast/v0.9.8/ac50e8519fc1498ebba345b72f1f8749157196fddbbec4b24efc6c520842a5d3.json](graphify-out/cache/ast/v0.9.8/ac50e8519fc1498ebba345b72f1f8749157196fddbbec4b24efc6c520842a5d3.json) |  | 2026-07-09 | 4KB | `ad05c38b` |
| [graphify-out/cache/ast/v0.9.8/ac61499103f18f5bf9241312c8e4c50d0c0f7f07e2c3cc5783ae88e4376ad2b2.json](graphify-out/cache/ast/v0.9.8/ac61499103f18f5bf9241312c8e4c50d0c0f7f07e2c3cc5783ae88e4376ad2b2.json) |  | 2026-07-08 | 188KB | `c008109d` |
| [graphify-out/cache/ast/v0.9.8/ac85d76c2d22a6ed1b460b1b0aeb581b14c6bbb564267b1856ae31c21641e1cc.json](graphify-out/cache/ast/v0.9.8/ac85d76c2d22a6ed1b460b1b0aeb581b14c6bbb564267b1856ae31c21641e1cc.json) |  | 2026-07-08 | 6KB | `309bbf69` |
| [graphify-out/cache/ast/v0.9.8/ac8ee54ebacd7912dd3157dd784bf021de44a86f802cb0894210fbe5f283d5ad.json](graphify-out/cache/ast/v0.9.8/ac8ee54ebacd7912dd3157dd784bf021de44a86f802cb0894210fbe5f283d5ad.json) |  | 2026-07-10 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/acd1c113d837fd688106744379e00734762fa9a2e30b56538379387c23a1a6c6.json](graphify-out/cache/ast/v0.9.8/acd1c113d837fd688106744379e00734762fa9a2e30b56538379387c23a1a6c6.json) |  | 2026-07-29 | 10KB | `804130cb` |
| [graphify-out/cache/ast/v0.9.8/ad0246ef07f80dfba5c8551b498935aecd2a684d13497426d023b20fd69add17.json](graphify-out/cache/ast/v0.9.8/ad0246ef07f80dfba5c8551b498935aecd2a684d13497426d023b20fd69add17.json) |  | 2026-07-08 | 8KB | `89ee3aeb` |
| [graphify-out/cache/ast/v0.9.8/ad0a16db1fbd0e0fe4e831cc4914cd4a7d9fc20e01c2525cdf5a6e9916e20b5b.json](graphify-out/cache/ast/v0.9.8/ad0a16db1fbd0e0fe4e831cc4914cd4a7d9fc20e01c2525cdf5a6e9916e20b5b.json) |  | 2026-07-08 | 2KB | `692cd2fd` |
| [graphify-out/cache/ast/v0.9.8/ad5ad52de93d6f27306125797daa092c86fe9e62a0bf4fe58e2e200fcb05acbd.json](graphify-out/cache/ast/v0.9.8/ad5ad52de93d6f27306125797daa092c86fe9e62a0bf4fe58e2e200fcb05acbd.json) |  | 2026-07-31 | 10KB | `2c3a492c` |
| [graphify-out/cache/ast/v0.9.8/ade69c1ec2fc4778fffff1c25f8f3861c6737b80f7a38fda31b969e246248ff2.json](graphify-out/cache/ast/v0.9.8/ade69c1ec2fc4778fffff1c25f8f3861c6737b80f7a38fda31b969e246248ff2.json) |  | 2026-07-30 | 10KB | `a335d165` |
| [graphify-out/cache/ast/v0.9.8/ade7d1955a6e03ddf2b8006bcfbef0db96d7ff1ba58b9a288f7b6d4754eebb8f.json](graphify-out/cache/ast/v0.9.8/ade7d1955a6e03ddf2b8006bcfbef0db96d7ff1ba58b9a288f7b6d4754eebb8f.json) |  | 2026-07-08 | 6KB | `ecf69e42` |
| [graphify-out/cache/ast/v0.9.8/ae0f138ea4308814aede6739d83333eab023a6a35b64369573af9210bde59747.json](graphify-out/cache/ast/v0.9.8/ae0f138ea4308814aede6739d83333eab023a6a35b64369573af9210bde59747.json) |  | 2026-07-08 | 8KB | `4fca3f7d` |
| [graphify-out/cache/ast/v0.9.8/ae1c655d73c2aaf260bd7fb76e03abea70f8ee2f0d470dcd239137858e038858.json](graphify-out/cache/ast/v0.9.8/ae1c655d73c2aaf260bd7fb76e03abea70f8ee2f0d470dcd239137858e038858.json) |  | 2026-07-27 | 8KB | `65a5024e` |
| [graphify-out/cache/ast/v0.9.8/ae4dd90d6ba47d92a14627c06e2a349fe79936beb1735c6bc7a4c8cfd3eb8f2e.json](graphify-out/cache/ast/v0.9.8/ae4dd90d6ba47d92a14627c06e2a349fe79936beb1735c6bc7a4c8cfd3eb8f2e.json) |  | 2026-07-08 | 15KB | `b684cc88` |
| [graphify-out/cache/ast/v0.9.8/ae675b0cff7a4e7933a00b843455060bc590b619c7516dd6a118ee7b915c7d90.json](graphify-out/cache/ast/v0.9.8/ae675b0cff7a4e7933a00b843455060bc590b619c7516dd6a118ee7b915c7d90.json) |  | 2026-07-08 | 45KB | `a20e37b6` |
| [graphify-out/cache/ast/v0.9.8/ae810c830d489c6388a848d66fbcbb6b3e202c5267dc0eda083b1bb474627a9c.json](graphify-out/cache/ast/v0.9.8/ae810c830d489c6388a848d66fbcbb6b3e202c5267dc0eda083b1bb474627a9c.json) |  | 2026-07-08 | 47KB | `1f6b7919` |
| [graphify-out/cache/ast/v0.9.8/aeebeabb63c69de8c72a78cb54366900e5cef271237d55dba82d16e04e9b4357.json](graphify-out/cache/ast/v0.9.8/aeebeabb63c69de8c72a78cb54366900e5cef271237d55dba82d16e04e9b4357.json) |  | 2026-07-08 | 58KB | `68144932` |
| [graphify-out/cache/ast/v0.9.8/af0cb3f7dfba65a3ad604eb98d682c69720b5e8055fa041caf3eabedf137d0e2.json](graphify-out/cache/ast/v0.9.8/af0cb3f7dfba65a3ad604eb98d682c69720b5e8055fa041caf3eabedf137d0e2.json) |  | 2026-07-08 | 17KB | `b29846b7` |
| [graphify-out/cache/ast/v0.9.8/af32687d0b85782a8ea7844c474ef3a7ef7e2bc1ef175623ccd80206647bb0e1.json](graphify-out/cache/ast/v0.9.8/af32687d0b85782a8ea7844c474ef3a7ef7e2bc1ef175623ccd80206647bb0e1.json) |  | 2026-07-08 | 1KB | `2ce254a2` |
| [graphify-out/cache/ast/v0.9.8/af56c61bfe4706fcfe4dc219db50b8b23c16f2d6517a06fd498c8be2afe81061.json](graphify-out/cache/ast/v0.9.8/af56c61bfe4706fcfe4dc219db50b8b23c16f2d6517a06fd498c8be2afe81061.json) |  | 2026-07-08 | 6KB | `2f3480c4` |
| [graphify-out/cache/ast/v0.9.8/af64a0976d77a2cfe285aebeb5cde81b15dc4d6a3042caeb2a04047d2fefde09.json](graphify-out/cache/ast/v0.9.8/af64a0976d77a2cfe285aebeb5cde81b15dc4d6a3042caeb2a04047d2fefde09.json) |  | 2026-07-08 | 10KB | `a94c60b2` |
| [graphify-out/cache/ast/v0.9.8/af740deaa9ddf5b369f88e46d1643dc5b47ea90535bfb14c85e768c10f594ba8.json](graphify-out/cache/ast/v0.9.8/af740deaa9ddf5b369f88e46d1643dc5b47ea90535bfb14c85e768c10f594ba8.json) |  | 2026-07-08 | 3KB | `1d65b75d` |
| [graphify-out/cache/ast/v0.9.8/af7727d5672fcf8ab0dbf954370a3bf3318b887407ce30e29216dc9dd87c74a1.json](graphify-out/cache/ast/v0.9.8/af7727d5672fcf8ab0dbf954370a3bf3318b887407ce30e29216dc9dd87c74a1.json) |  | 2026-07-08 | 29KB | `67e08a00` |
| [graphify-out/cache/ast/v0.9.8/af8fec96a13ef975f19cec05715c01e8cf6398f6c2e049ef46085f42bd2d640a.json](graphify-out/cache/ast/v0.9.8/af8fec96a13ef975f19cec05715c01e8cf6398f6c2e049ef46085f42bd2d640a.json) |  | 2026-07-30 | 3KB | `fb62d941` |
| [graphify-out/cache/ast/v0.9.8/af94862dd1bf28b29bf68f06783d15991e64a36b4e364ab7a829fdeda361b321.json](graphify-out/cache/ast/v0.9.8/af94862dd1bf28b29bf68f06783d15991e64a36b4e364ab7a829fdeda361b321.json) |  | 2026-07-10 | 8KB | `1dce174b` |
| [graphify-out/cache/ast/v0.9.8/afbfc9ac9947e1736753df22adba4fb45e9b9da3a77f74527caa55dc90785a67.json](graphify-out/cache/ast/v0.9.8/afbfc9ac9947e1736753df22adba4fb45e9b9da3a77f74527caa55dc90785a67.json) |  | 2026-07-08 | 33KB | `d6c49f1c` |
| [graphify-out/cache/ast/v0.9.8/afd1b98a4b501e29b4c95cf84a28bb216e5d73d9f119d98f7595a6b986d74961.json](graphify-out/cache/ast/v0.9.8/afd1b98a4b501e29b4c95cf84a28bb216e5d73d9f119d98f7595a6b986d74961.json) |  | 2026-07-07 | 1KB | `5ea94bba` |
| [graphify-out/cache/ast/v0.9.8/b030df7ee4cdc6f408bc6edea6272f382e7adea05d2af0e5eb509274bb3845c7.json](graphify-out/cache/ast/v0.9.8/b030df7ee4cdc6f408bc6edea6272f382e7adea05d2af0e5eb509274bb3845c7.json) |  | 2026-07-24 | 7KB | `a2ff798e` |
| [graphify-out/cache/ast/v0.9.8/b048c611803ff678d37e13ba0f04ea60a9d1c7a9335dcf7a4c2635c299a16846.json](graphify-out/cache/ast/v0.9.8/b048c611803ff678d37e13ba0f04ea60a9d1c7a9335dcf7a4c2635c299a16846.json) |  | 2026-07-29 | 9KB | `bb817cfa` |
| [graphify-out/cache/ast/v0.9.8/b09e5bfdd8a7b8837b339b7d23eade42d885aa0f13a1b20e52bb7362188f6af4.json](graphify-out/cache/ast/v0.9.8/b09e5bfdd8a7b8837b339b7d23eade42d885aa0f13a1b20e52bb7362188f6af4.json) |  | 2026-07-08 | 2KB | `8d66c012` |
| [graphify-out/cache/ast/v0.9.8/b0a07aaa139bb7667e9643b05bff7e358adcd3f1b0880f18733aa698de7d248e.json](graphify-out/cache/ast/v0.9.8/b0a07aaa139bb7667e9643b05bff7e358adcd3f1b0880f18733aa698de7d248e.json) |  | 2026-07-08 | 4KB | `bdefba6d` |
| [graphify-out/cache/ast/v0.9.8/b0af50596b361ca9d3315862bcd82e096a9bb4b2b8b90cf4375ddcd9963d0648.json](graphify-out/cache/ast/v0.9.8/b0af50596b361ca9d3315862bcd82e096a9bb4b2b8b90cf4375ddcd9963d0648.json) |  | 2026-07-31 | 8KB | `42162a94` |
| [graphify-out/cache/ast/v0.9.8/b0d09534d921f0fbe497c83054aeff0c853acc7662241c793b96cf8fd0ad7011.json](graphify-out/cache/ast/v0.9.8/b0d09534d921f0fbe497c83054aeff0c853acc7662241c793b96cf8fd0ad7011.json) |  | 2026-07-27 | 13KB | `5ea0eccb` |
| [graphify-out/cache/ast/v0.9.8/b0faa75c86e79d3dac151228208d0ca97df772246e78c445552ac24bb946808f.json](graphify-out/cache/ast/v0.9.8/b0faa75c86e79d3dac151228208d0ca97df772246e78c445552ac24bb946808f.json) |  | 2026-07-08 | 11KB | `b9c98e0f` |
| [graphify-out/cache/ast/v0.9.8/b11b333434b961f6a898de9e3ad7f208b9041d1e53ac108995878e2b718c11b4.json](graphify-out/cache/ast/v0.9.8/b11b333434b961f6a898de9e3ad7f208b9041d1e53ac108995878e2b718c11b4.json) |  | 2026-07-27 | 13KB | `25553db4` |
| [graphify-out/cache/ast/v0.9.8/b1865470bf158b6e3e84a5c8f9d8b58b31297441c549057e6ab542ce5f1e8f79.json](graphify-out/cache/ast/v0.9.8/b1865470bf158b6e3e84a5c8f9d8b58b31297441c549057e6ab542ce5f1e8f79.json) |  | 2026-07-08 | 8KB | `e15081a1` |
| [graphify-out/cache/ast/v0.9.8/b1ac2b1c08ba024b8b02d1750c2c963179132aeef7c1991ef20c858bc9319c74.json](graphify-out/cache/ast/v0.9.8/b1ac2b1c08ba024b8b02d1750c2c963179132aeef7c1991ef20c858bc9319c74.json) |  | 2026-07-27 | 3KB | `7d9237cc` |
| [graphify-out/cache/ast/v0.9.8/b1b99371b6f8bd32b1a7e6be3f7e0fe3ee5e466fea52087832fcc94dcca85a32.json](graphify-out/cache/ast/v0.9.8/b1b99371b6f8bd32b1a7e6be3f7e0fe3ee5e466fea52087832fcc94dcca85a32.json) |  | 2026-07-08 | 31KB | `3273d7de` |
| [graphify-out/cache/ast/v0.9.8/b1e707b90e8d27017148cb93d62ed056263bc869337770c308c76306d0994c35.json](graphify-out/cache/ast/v0.9.8/b1e707b90e8d27017148cb93d62ed056263bc869337770c308c76306d0994c35.json) |  | 2026-07-30 | 19KB | `370b7272` |
| [graphify-out/cache/ast/v0.9.8/b20488a83f5fed43652a9e43dc63b4ef8a2513ede797bd9a6ca8791cf60d3d34.json](graphify-out/cache/ast/v0.9.8/b20488a83f5fed43652a9e43dc63b4ef8a2513ede797bd9a6ca8791cf60d3d34.json) |  | 2026-07-07 | 816B | `2161f1c7` |
| [graphify-out/cache/ast/v0.9.8/b21a9502704a4189038ade35ced6cc31254eecf8635347914f83f0a343fe18a5.json](graphify-out/cache/ast/v0.9.8/b21a9502704a4189038ade35ced6cc31254eecf8635347914f83f0a343fe18a5.json) |  | 2026-07-08 | 2KB | `178678cb` |
| [graphify-out/cache/ast/v0.9.8/b24664520dc4225c96b6aad1be45bb9a692b5fb75c69d722475150b76282514c.json](graphify-out/cache/ast/v0.9.8/b24664520dc4225c96b6aad1be45bb9a692b5fb75c69d722475150b76282514c.json) |  | 2026-07-07 | 17KB | `afc74bd9` |
| [graphify-out/cache/ast/v0.9.8/b2581e7942ef3b965358bf8d0a0669b9fd8e862c9257d9633bd5e86e22a3249d.json](graphify-out/cache/ast/v0.9.8/b2581e7942ef3b965358bf8d0a0669b9fd8e862c9257d9633bd5e86e22a3249d.json) |  | 2026-07-08 | 12KB | `78fd9a7d` |
| [graphify-out/cache/ast/v0.9.8/b270a74c320994d0459045bc4b3097ffbeda3a5238559741b04d1e62b39ccc83.json](graphify-out/cache/ast/v0.9.8/b270a74c320994d0459045bc4b3097ffbeda3a5238559741b04d1e62b39ccc83.json) |  | 2026-07-08 | 47KB | `e2a043f5` |
| [graphify-out/cache/ast/v0.9.8/b279f845319641295761efc34699c505b9df54d42f3bfe040f6f35b1fbb7dec8.json](graphify-out/cache/ast/v0.9.8/b279f845319641295761efc34699c505b9df54d42f3bfe040f6f35b1fbb7dec8.json) |  | 2026-07-08 | 5KB | `45f9363a` |
| [graphify-out/cache/ast/v0.9.8/b28a8277f2b5f5361ce5418fc8219baa92f47c8477dc78592654e788af3431df.json](graphify-out/cache/ast/v0.9.8/b28a8277f2b5f5361ce5418fc8219baa92f47c8477dc78592654e788af3431df.json) |  | 2026-07-08 | 18KB | `61acf053` |
| [graphify-out/cache/ast/v0.9.8/b28cf50873b8bb31dbd2bb43c27b18043341734abaa833ff36ecdbca36d38f6b.json](graphify-out/cache/ast/v0.9.8/b28cf50873b8bb31dbd2bb43c27b18043341734abaa833ff36ecdbca36d38f6b.json) |  | 2026-07-08 | 57KB | `ef6dbdca` |
| [graphify-out/cache/ast/v0.9.8/b2db1c32928bd1e0c95e824856ed278dc8d69da8e95d2eb25e46fc8a5340180b.json](graphify-out/cache/ast/v0.9.8/b2db1c32928bd1e0c95e824856ed278dc8d69da8e95d2eb25e46fc8a5340180b.json) |  | 2026-07-07 | 18KB | `db36523f` |
| [graphify-out/cache/ast/v0.9.8/b2f47d3ab07db12d6d5821bce1bcc3ccca95dc255a16b24543bb569f33ae11e8.json](graphify-out/cache/ast/v0.9.8/b2f47d3ab07db12d6d5821bce1bcc3ccca95dc255a16b24543bb569f33ae11e8.json) |  | 2026-07-08 | 7KB | `e7533e6f` |
| [graphify-out/cache/ast/v0.9.8/b307c1a8f9eeff2f7fa86c70c4638d4c26e255dae155478f886a8aed17c69233.json](graphify-out/cache/ast/v0.9.8/b307c1a8f9eeff2f7fa86c70c4638d4c26e255dae155478f886a8aed17c69233.json) |  | 2026-07-07 | 19KB | `b36d088f` |
| [graphify-out/cache/ast/v0.9.8/b31bc3d76b503e4ee923d0b2b0db1f29073339e736e611f8efb901c8daae11a3.json](graphify-out/cache/ast/v0.9.8/b31bc3d76b503e4ee923d0b2b0db1f29073339e736e611f8efb901c8daae11a3.json) |  | 2026-07-08 | 8KB | `4b9c8e4a` |
| [graphify-out/cache/ast/v0.9.8/b33f0063f0897641f1e83bfc4e745e8255b86c2bcbffa27725c5d6bec0e46b7d.json](graphify-out/cache/ast/v0.9.8/b33f0063f0897641f1e83bfc4e745e8255b86c2bcbffa27725c5d6bec0e46b7d.json) |  | 2026-07-08 | 6KB | `68be55eb` |
| [graphify-out/cache/ast/v0.9.8/b38d42f0d9b32951eabb816ed3b9488997d89a83758939f001f58d4d537bbc9b.json](graphify-out/cache/ast/v0.9.8/b38d42f0d9b32951eabb816ed3b9488997d89a83758939f001f58d4d537bbc9b.json) |  | 2026-07-08 | 10KB | `70b83ce7` |
| [graphify-out/cache/ast/v0.9.8/b394f25c2c87fa4d37a1ec3b9537db8ac356d45d3977669daad664f206f1ca39.json](graphify-out/cache/ast/v0.9.8/b394f25c2c87fa4d37a1ec3b9537db8ac356d45d3977669daad664f206f1ca39.json) |  | 2026-07-08 | 52KB | `3264bf1b` |
| [graphify-out/cache/ast/v0.9.8/b3969c66a3f93167bdb3a2cb775f08e7601501d044bab03d201f05fa3cd6e110.json](graphify-out/cache/ast/v0.9.8/b3969c66a3f93167bdb3a2cb775f08e7601501d044bab03d201f05fa3cd6e110.json) |  | 2026-07-08 | 2KB | `2a1dbc0e` |
| [graphify-out/cache/ast/v0.9.8/b3edadd4d0c531394ee94a9bd8cc2d4d935815ffbd66549b5d328030a7c91ad2.json](graphify-out/cache/ast/v0.9.8/b3edadd4d0c531394ee94a9bd8cc2d4d935815ffbd66549b5d328030a7c91ad2.json) |  | 2026-07-08 | 12KB | `9730a3c7` |
| [graphify-out/cache/ast/v0.9.8/b40037f818bce026b89d3e392decb8b8910d0b20d3f7caac718c94ab7c7b9279.json](graphify-out/cache/ast/v0.9.8/b40037f818bce026b89d3e392decb8b8910d0b20d3f7caac718c94ab7c7b9279.json) |  | 2026-07-08 | 15KB | `8190f3bf` |
| [graphify-out/cache/ast/v0.9.8/b40c5968f2285afeb2dfb7e8993ebe3eeeaeb4798077b8b5fdfe27473644f66b.json](graphify-out/cache/ast/v0.9.8/b40c5968f2285afeb2dfb7e8993ebe3eeeaeb4798077b8b5fdfe27473644f66b.json) |  | 2026-07-08 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/b4112fa8df11d7d3fc5272b7238791e2109d07dfda027bc8b7f3a98c6164abc1.json](graphify-out/cache/ast/v0.9.8/b4112fa8df11d7d3fc5272b7238791e2109d07dfda027bc8b7f3a98c6164abc1.json) |  | 2026-07-08 | 7KB | `8050f519` |
| [graphify-out/cache/ast/v0.9.8/b43fecd9154db72e86bea0480d8dfec6687a67ffef7f79d7e40d8c8aad395404.json](graphify-out/cache/ast/v0.9.8/b43fecd9154db72e86bea0480d8dfec6687a67ffef7f79d7e40d8c8aad395404.json) |  | 2026-07-08 | 18KB | `5760d4b4` |
| [graphify-out/cache/ast/v0.9.8/b4516f9c5c6fbfb3c81e8076ecb8b9ef1cc9f059c15b121036d43dae9f88de36.json](graphify-out/cache/ast/v0.9.8/b4516f9c5c6fbfb3c81e8076ecb8b9ef1cc9f059c15b121036d43dae9f88de36.json) |  | 2026-07-23 | 23KB | `fab1524b` |
| [graphify-out/cache/ast/v0.9.8/b4880edb449b002c587fef71b88d7044f9a917b4fad9bfc3d9bf433a7d6ae44b.json](graphify-out/cache/ast/v0.9.8/b4880edb449b002c587fef71b88d7044f9a917b4fad9bfc3d9bf433a7d6ae44b.json) |  | 2026-07-08 | 9KB | `75a087a6` |
| [graphify-out/cache/ast/v0.9.8/b4b01f8d29f1c42d877e389901770bc905cf3f10f9de5a2a8953d760ae8eb24e.json](graphify-out/cache/ast/v0.9.8/b4b01f8d29f1c42d877e389901770bc905cf3f10f9de5a2a8953d760ae8eb24e.json) |  | 2026-07-08 | 4KB | `5a38ecc0` |
| [graphify-out/cache/ast/v0.9.8/b4b5d88b7be8bbde190d80a657f19595e1362266ca022550a4618a7b87d655cd.json](graphify-out/cache/ast/v0.9.8/b4b5d88b7be8bbde190d80a657f19595e1362266ca022550a4618a7b87d655cd.json) |  | 2026-07-08 | 9KB | `fd237a14` |
| [graphify-out/cache/ast/v0.9.8/b4b6dfd4c5eefb069fe35cefd0c43c5df86260568ef7b92375b1ceafad8e28e1.json](graphify-out/cache/ast/v0.9.8/b4b6dfd4c5eefb069fe35cefd0c43c5df86260568ef7b92375b1ceafad8e28e1.json) |  | 2026-07-27 | 9KB | `a5f6f403` |
| [graphify-out/cache/ast/v0.9.8/b4be44a68cb08e6e164b01d3afde010ae3bdb71357c311e52722fde23889ebb2.json](graphify-out/cache/ast/v0.9.8/b4be44a68cb08e6e164b01d3afde010ae3bdb71357c311e52722fde23889ebb2.json) |  | 2026-07-08 | 11KB | `1d0a80c2` |
| [graphify-out/cache/ast/v0.9.8/b51082ca008dbbd7d8ec14e95b921ce8b37a3492114d5e365dd1fdd8a28ef406.json](graphify-out/cache/ast/v0.9.8/b51082ca008dbbd7d8ec14e95b921ce8b37a3492114d5e365dd1fdd8a28ef406.json) |  | 2026-07-08 | 25KB | `f5724e7c` |
| [graphify-out/cache/ast/v0.9.8/b525b66d3f28e140f5ddb7414cf418a54233677be5cae85cf6f7e2fce9d018a7.json](graphify-out/cache/ast/v0.9.8/b525b66d3f28e140f5ddb7414cf418a54233677be5cae85cf6f7e2fce9d018a7.json) |  | 2026-07-08 | 13KB | `6ca0d131` |
| [graphify-out/cache/ast/v0.9.8/b64386aaed2bc009bed9d7f3f831f9bb7c3be7131d9388a92b72036682e8b47a.json](graphify-out/cache/ast/v0.9.8/b64386aaed2bc009bed9d7f3f831f9bb7c3be7131d9388a92b72036682e8b47a.json) |  | 2026-07-08 | 5KB | `002f32a0` |
| [graphify-out/cache/ast/v0.9.8/b66dd66d34438268b8f9803883dab91223a018da239887e57ce7235c21c43306.json](graphify-out/cache/ast/v0.9.8/b66dd66d34438268b8f9803883dab91223a018da239887e57ce7235c21c43306.json) |  | 2026-07-08 | 4KB | `08ae6036` |
| [graphify-out/cache/ast/v0.9.8/b6a7276583b7d0527ff215e2ab36e905f573033844736daea69f5ee325b17e73.json](graphify-out/cache/ast/v0.9.8/b6a7276583b7d0527ff215e2ab36e905f573033844736daea69f5ee325b17e73.json) |  | 2026-07-08 | 3KB | `5327c915` |
| [graphify-out/cache/ast/v0.9.8/b6cf52f1289723c52025b2f38f8dfc76fa3df626b1061894d01ad3eefafea495.json](graphify-out/cache/ast/v0.9.8/b6cf52f1289723c52025b2f38f8dfc76fa3df626b1061894d01ad3eefafea495.json) |  | 2026-07-08 | 7KB | `a5a15403` |
| [graphify-out/cache/ast/v0.9.8/b6d43c123903c50e693e949b552345a5e528cedbad6d47436ff44d521eab0642.json](graphify-out/cache/ast/v0.9.8/b6d43c123903c50e693e949b552345a5e528cedbad6d47436ff44d521eab0642.json) |  | 2026-07-08 | 7KB | `350bab9c` |
| [graphify-out/cache/ast/v0.9.8/b7440e5231c1818c76c67b28a2898950dab56790904ff92d835adc972b9d6c8d.json](graphify-out/cache/ast/v0.9.8/b7440e5231c1818c76c67b28a2898950dab56790904ff92d835adc972b9d6c8d.json) |  | 2026-07-07 | 26KB | `a766cd3b` |
| [graphify-out/cache/ast/v0.9.8/b75c5cca2b36c21aeb9c1f636d8e6280a8d68307579f23b038f1d0655bda40c9.json](graphify-out/cache/ast/v0.9.8/b75c5cca2b36c21aeb9c1f636d8e6280a8d68307579f23b038f1d0655bda40c9.json) |  | 2026-07-07 | 7KB | `361a6e3a` |
| [graphify-out/cache/ast/v0.9.8/b768104a955fcc80cbb7c184dbd7bead1c248d591494212f37f788dc5c845511.json](graphify-out/cache/ast/v0.9.8/b768104a955fcc80cbb7c184dbd7bead1c248d591494212f37f788dc5c845511.json) |  | 2026-07-23 | 51KB | `1e360500` |
| [graphify-out/cache/ast/v0.9.8/b7a12eb94aa5be0dc4e13d0ccce3a55b24ff7c35fca6d4f6475bcd7cc9ad4c59.json](graphify-out/cache/ast/v0.9.8/b7a12eb94aa5be0dc4e13d0ccce3a55b24ff7c35fca6d4f6475bcd7cc9ad4c59.json) |  | 2026-07-08 | 8KB | `afaa8a33` |
| [graphify-out/cache/ast/v0.9.8/b7b8109c416748e15970cfebe9bbf7d85cf2a03234d9a75da074d1e710652ef4.json](graphify-out/cache/ast/v0.9.8/b7b8109c416748e15970cfebe9bbf7d85cf2a03234d9a75da074d1e710652ef4.json) |  | 2026-07-30 | 3KB | `4bc3500d` |
| [graphify-out/cache/ast/v0.9.8/b7f871b71d6ef213495145fc5bbfdb82c369d44eb2508c209cd22403dff70d03.json](graphify-out/cache/ast/v0.9.8/b7f871b71d6ef213495145fc5bbfdb82c369d44eb2508c209cd22403dff70d03.json) |  | 2026-07-31 | 30KB | `c7d27b9b` |
| [graphify-out/cache/ast/v0.9.8/b8297ccdae757273b9fa5c319640f03f2d65b40c543ffbe599b41b9d8667bb6a.json](graphify-out/cache/ast/v0.9.8/b8297ccdae757273b9fa5c319640f03f2d65b40c543ffbe599b41b9d8667bb6a.json) |  | 2026-07-08 | 2KB | `e835f97a` |
| [graphify-out/cache/ast/v0.9.8/b82bc2eec6ee63c461629d34179760772a2b0ba4d6c8107e02966c3279fd34fc.json](graphify-out/cache/ast/v0.9.8/b82bc2eec6ee63c461629d34179760772a2b0ba4d6c8107e02966c3279fd34fc.json) |  | 2026-07-08 | 5KB | `0a96598e` |
| [graphify-out/cache/ast/v0.9.8/b83dc799e4c17a9ea4b26c8978ee843f2430c6f3b1518813250a36213e7132e2.json](graphify-out/cache/ast/v0.9.8/b83dc799e4c17a9ea4b26c8978ee843f2430c6f3b1518813250a36213e7132e2.json) |  | 2026-07-29 | 9KB | `bb817cfa` |
| [graphify-out/cache/ast/v0.9.8/b89f52016d477ab8e05fa62cb5cfcbbf874f6f33f0248d854530f9e789304534.json](graphify-out/cache/ast/v0.9.8/b89f52016d477ab8e05fa62cb5cfcbbf874f6f33f0248d854530f9e789304534.json) |  | 2026-07-08 | 4KB | `4905783d` |
| [graphify-out/cache/ast/v0.9.8/b8f46aa111167cd9236ef3ffd46c464f635b9aaf6611b5f50d2bbed7506d5b1a.json](graphify-out/cache/ast/v0.9.8/b8f46aa111167cd9236ef3ffd46c464f635b9aaf6611b5f50d2bbed7506d5b1a.json) |  | 2026-07-08 | 5KB | `a00a4bdf` |
| [graphify-out/cache/ast/v0.9.8/b97858c00d6d3937e1f9487d9f7d1328e6f3a453d6af02603739d75f72807874.json](graphify-out/cache/ast/v0.9.8/b97858c00d6d3937e1f9487d9f7d1328e6f3a453d6af02603739d75f72807874.json) |  | 2026-07-24 | 2KB | `309beb10` |
| [graphify-out/cache/ast/v0.9.8/b9c40fe7d5a8f6ca3ce7e2987398a05ae740f03fb21d32059f9eed1d2722810f.json](graphify-out/cache/ast/v0.9.8/b9c40fe7d5a8f6ca3ce7e2987398a05ae740f03fb21d32059f9eed1d2722810f.json) |  | 2026-07-23 | 8KB | `be1195e7` |
| [graphify-out/cache/ast/v0.9.8/ba3cc6578575460c3810ed012053d238d2dd304791052186b553926bf7fb8224.json](graphify-out/cache/ast/v0.9.8/ba3cc6578575460c3810ed012053d238d2dd304791052186b553926bf7fb8224.json) |  | 2026-07-08 | 25KB | `da351983` |
| [graphify-out/cache/ast/v0.9.8/ba6907f9012935338240ee7f43ea1ec59829c217d5e8e85c486ec18053da177b.json](graphify-out/cache/ast/v0.9.8/ba6907f9012935338240ee7f43ea1ec59829c217d5e8e85c486ec18053da177b.json) |  | 2026-07-27 | 7KB | `e1a83fd6` |
| [graphify-out/cache/ast/v0.9.8/ba8ac42609755a8ef04b97a94f28e85cbaf6ab5b7d50dae94526d9d549f0c307.json](graphify-out/cache/ast/v0.9.8/ba8ac42609755a8ef04b97a94f28e85cbaf6ab5b7d50dae94526d9d549f0c307.json) |  | 2026-07-08 | 7KB | `92f1ce90` |
| [graphify-out/cache/ast/v0.9.8/ba9f72d9081dcffe4c390b8e65e9708b002f315dfd580e717629880b000804c2.json](graphify-out/cache/ast/v0.9.8/ba9f72d9081dcffe4c390b8e65e9708b002f315dfd580e717629880b000804c2.json) |  | 2026-07-08 | 44KB | `2d80ea50` |
| [graphify-out/cache/ast/v0.9.8/bb15b2706b4bb0fc89ff4fb600f5b3fe14cb075cb494cd1414f5abda041a49c5.json](graphify-out/cache/ast/v0.9.8/bb15b2706b4bb0fc89ff4fb600f5b3fe14cb075cb494cd1414f5abda041a49c5.json) |  | 2026-07-08 | 26KB | `b7e37561` |
| [graphify-out/cache/ast/v0.9.8/bb5741faeed2e6a65e913f8bc548d775370861011482e5e5f905300d74862fc9.json](graphify-out/cache/ast/v0.9.8/bb5741faeed2e6a65e913f8bc548d775370861011482e5e5f905300d74862fc9.json) |  | 2026-07-08 | 26KB | `9fb17fa9` |
| [graphify-out/cache/ast/v0.9.8/bbb1b11e29dc79a86e5eb049da3401e34066ae3f6eb593c581aca847bf0552f6.json](graphify-out/cache/ast/v0.9.8/bbb1b11e29dc79a86e5eb049da3401e34066ae3f6eb593c581aca847bf0552f6.json) |  | 2026-07-07 | 12KB | `3c69c2f4` |
| [graphify-out/cache/ast/v0.9.8/bbb34bf710beef9a4c3e1020dc66be193011a916ec9bbf89e83ac36d1d510c32.json](graphify-out/cache/ast/v0.9.8/bbb34bf710beef9a4c3e1020dc66be193011a916ec9bbf89e83ac36d1d510c32.json) |  | 2026-07-08 | 93KB | `7e03730e` |
| [graphify-out/cache/ast/v0.9.8/bc83681db797f04105aac3876295e0eb650444ce4d2d6efd7d33d3a7d4ea2d98.json](graphify-out/cache/ast/v0.9.8/bc83681db797f04105aac3876295e0eb650444ce4d2d6efd7d33d3a7d4ea2d98.json) |  | 2026-07-08 | 15KB | `d25a0e66` |
| [graphify-out/cache/ast/v0.9.8/bcab157b2b3850502fcb9706a877f06d30e8c6d344fcdcab4e30f85b3a98c74f.json](graphify-out/cache/ast/v0.9.8/bcab157b2b3850502fcb9706a877f06d30e8c6d344fcdcab4e30f85b3a98c74f.json) |  | 2026-07-08 | 7KB | `5d0d7704` |
| [graphify-out/cache/ast/v0.9.8/bd03faddddc1b4b597bf608dbf70fb7e18bd007b601bcc186f9efa232bf68a01.json](graphify-out/cache/ast/v0.9.8/bd03faddddc1b4b597bf608dbf70fb7e18bd007b601bcc186f9efa232bf68a01.json) |  | 2026-07-07 | 16KB | `c7d44213` |
| [graphify-out/cache/ast/v0.9.8/bd619c664da57b057719e398e97aa4cc1fcee24785221c90a3aef4de31bc1aa7.json](graphify-out/cache/ast/v0.9.8/bd619c664da57b057719e398e97aa4cc1fcee24785221c90a3aef4de31bc1aa7.json) |  | 2026-07-08 | 9KB | `d87d72ae` |
| [graphify-out/cache/ast/v0.9.8/bd6b25e0e1d2c0912dcbe6a7bf127c1c48f21625dae6caa4734b5c9ab885e2c3.json](graphify-out/cache/ast/v0.9.8/bd6b25e0e1d2c0912dcbe6a7bf127c1c48f21625dae6caa4734b5c9ab885e2c3.json) |  | 2026-07-07 | 18KB | `79063940` |
| [graphify-out/cache/ast/v0.9.8/bd9391b1b3f7acc0129489b0d49d1b5809ccd7f8a6b544c7f6de722b508b397a.json](graphify-out/cache/ast/v0.9.8/bd9391b1b3f7acc0129489b0d49d1b5809ccd7f8a6b544c7f6de722b508b397a.json) |  | 2026-07-07 | 23KB | `a5502ae3` |
| [graphify-out/cache/ast/v0.9.8/be9546814d49cd726cbd397251f659ac33d59661422f7d04dbe031a0e8d66cb2.json](graphify-out/cache/ast/v0.9.8/be9546814d49cd726cbd397251f659ac33d59661422f7d04dbe031a0e8d66cb2.json) |  | 2026-07-08 | 8KB | `97b66047` |
| [graphify-out/cache/ast/v0.9.8/bec4e559877963fa21b701867e185e46e42cb050310f66b7aa66706d532202d1.json](graphify-out/cache/ast/v0.9.8/bec4e559877963fa21b701867e185e46e42cb050310f66b7aa66706d532202d1.json) |  | 2026-07-24 | 107KB | `8ce1cae5` |
| [graphify-out/cache/ast/v0.9.8/bf12e1fcac0b85bf73aa37e9702c278ce52ac4c73fa89632730a688a677c4181.json](graphify-out/cache/ast/v0.9.8/bf12e1fcac0b85bf73aa37e9702c278ce52ac4c73fa89632730a688a677c4181.json) |  | 2026-07-27 | 3KB | `13ffb184` |
| [graphify-out/cache/ast/v0.9.8/bf2bc06cad10b87225904ae1cfab7cc57f5a3eb1f0bb387890d619f81e7c157d.json](graphify-out/cache/ast/v0.9.8/bf2bc06cad10b87225904ae1cfab7cc57f5a3eb1f0bb387890d619f81e7c157d.json) |  | 2026-07-29 | 9KB | `cc4f853f` |
| [graphify-out/cache/ast/v0.9.8/bf4763cd6c0bae7373325a81f43233fe3f13c95691f9a15e6b5893bf486afad1.json](graphify-out/cache/ast/v0.9.8/bf4763cd6c0bae7373325a81f43233fe3f13c95691f9a15e6b5893bf486afad1.json) |  | 2026-07-08 | 136KB | `3fa101a4` |
| [graphify-out/cache/ast/v0.9.8/bf959e84e1b505dca449324d8cecc6ce0c26b256caeb5db47d1ad818acc5072a.json](graphify-out/cache/ast/v0.9.8/bf959e84e1b505dca449324d8cecc6ce0c26b256caeb5db47d1ad818acc5072a.json) |  | 2026-07-08 | 5KB | `942865d8` |
| [graphify-out/cache/ast/v0.9.8/bfb866d646b4061024f4d6f408d0594865f1127edde458cd9d65b663a84e0c77.json](graphify-out/cache/ast/v0.9.8/bfb866d646b4061024f4d6f408d0594865f1127edde458cd9d65b663a84e0c77.json) |  | 2026-07-07 | 13KB | `aa169424` |
| [graphify-out/cache/ast/v0.9.8/bfc22b5278a3c78b4d65a8b6c0f47cba58963a8dd732af400e012264aeb0a40c.json](graphify-out/cache/ast/v0.9.8/bfc22b5278a3c78b4d65a8b6c0f47cba58963a8dd732af400e012264aeb0a40c.json) |  | 2026-07-08 | 6KB | `7d0cd07f` |
| [graphify-out/cache/ast/v0.9.8/c00199e604a457cf41bc2bc372f6770abddce82a38cd42240fdaf9aff6babfed.json](graphify-out/cache/ast/v0.9.8/c00199e604a457cf41bc2bc372f6770abddce82a38cd42240fdaf9aff6babfed.json) |  | 2026-07-08 | 7KB | `ac4d86e6` |
| [graphify-out/cache/ast/v0.9.8/c050a0b63bdde1ae1fc4316f32299cee534b567e36b39d7fe79359285d239886.json](graphify-out/cache/ast/v0.9.8/c050a0b63bdde1ae1fc4316f32299cee534b567e36b39d7fe79359285d239886.json) |  | 2026-07-29 | 13KB | `3244f4e6` |
| [graphify-out/cache/ast/v0.9.8/c0579c4cc8a2c51ba068a5f13dca0638d6d821c77cf7b18ab5c822339c272182.json](graphify-out/cache/ast/v0.9.8/c0579c4cc8a2c51ba068a5f13dca0638d6d821c77cf7b18ab5c822339c272182.json) |  | 2026-07-07 | 96KB | `8f3e17f5` |
| [graphify-out/cache/ast/v0.9.8/c05f2c62e7a5c974e11b3b78fd0f71186f03a15e6bb45653c33bf79b7cd4016a.json](graphify-out/cache/ast/v0.9.8/c05f2c62e7a5c974e11b3b78fd0f71186f03a15e6bb45653c33bf79b7cd4016a.json) |  | 2026-07-07 | 18KB | `b06c8e0d` |
| [graphify-out/cache/ast/v0.9.8/c0b7d4e9ed294e1aac7f5cb16ba7785d8762ae334de7231be926a4ec32b39290.json](graphify-out/cache/ast/v0.9.8/c0b7d4e9ed294e1aac7f5cb16ba7785d8762ae334de7231be926a4ec32b39290.json) |  | 2026-07-08 | 4KB | `4ff73f04` |
| [graphify-out/cache/ast/v0.9.8/c0fd458af4f9ccc13383aa5ac9ad3289eaa941bb4ad381d03a050217eedfee0e.json](graphify-out/cache/ast/v0.9.8/c0fd458af4f9ccc13383aa5ac9ad3289eaa941bb4ad381d03a050217eedfee0e.json) |  | 2026-07-07 | 18KB | `17840901` |
| [graphify-out/cache/ast/v0.9.8/c11d85c73e8b4558e8833654204a4a9026a8814e27c6e763c027dd36714bfd04.json](graphify-out/cache/ast/v0.9.8/c11d85c73e8b4558e8833654204a4a9026a8814e27c6e763c027dd36714bfd04.json) |  | 2026-07-08 | 1KB | `9a84efe6` |
| [graphify-out/cache/ast/v0.9.8/c12843e84d94bbad8a8e8e60aca0afd0b9615408c7d5e56c03d97edc0d750ca8.json](graphify-out/cache/ast/v0.9.8/c12843e84d94bbad8a8e8e60aca0afd0b9615408c7d5e56c03d97edc0d750ca8.json) |  | 2026-07-08 | 8KB | `1751d5f2` |
| [graphify-out/cache/ast/v0.9.8/c13645c00a0810ff93aaee27e8c004f22d8ca23354d139bfedac2c0a46d0719f.json](graphify-out/cache/ast/v0.9.8/c13645c00a0810ff93aaee27e8c004f22d8ca23354d139bfedac2c0a46d0719f.json) |  | 2026-07-27 | 8KB | `49a4902e` |
| [graphify-out/cache/ast/v0.9.8/c144191b3e850c66e76caa863dd17f31982e691a54f34cb0073330974a297650.json](graphify-out/cache/ast/v0.9.8/c144191b3e850c66e76caa863dd17f31982e691a54f34cb0073330974a297650.json) |  | 2026-07-31 | 25KB | `0280a778` |
| [graphify-out/cache/ast/v0.9.8/c156404114b062a780c2a9cb2da9e2d4b307c3d26284aad2159b7729ca5e3ee4.json](graphify-out/cache/ast/v0.9.8/c156404114b062a780c2a9cb2da9e2d4b307c3d26284aad2159b7729ca5e3ee4.json) |  | 2026-07-08 | 6KB | `db75fca7` |
| [graphify-out/cache/ast/v0.9.8/c1f601f280d0d92a8a09b96f1b723e6badfb3112c8ef2aba1edca148d69ae3d1.json](graphify-out/cache/ast/v0.9.8/c1f601f280d0d92a8a09b96f1b723e6badfb3112c8ef2aba1edca148d69ae3d1.json) |  | 2026-07-07 | 21KB | `5a72e439` |
| [graphify-out/cache/ast/v0.9.8/c25dbfe926bee5ef6287c740c790ef40c0e6747ef34b5b179fe2cded3b776b8b.json](graphify-out/cache/ast/v0.9.8/c25dbfe926bee5ef6287c740c790ef40c0e6747ef34b5b179fe2cded3b776b8b.json) |  | 2026-07-08 | 2KB | `1fa02835` |
| [graphify-out/cache/ast/v0.9.8/c280e0791591d16fc14c0d0effa682a454bb49c7bd7f28ee6a18b82fe079650e.json](graphify-out/cache/ast/v0.9.8/c280e0791591d16fc14c0d0effa682a454bb49c7bd7f28ee6a18b82fe079650e.json) |  | 2026-07-08 | 145KB | `2fce072c` |
| [graphify-out/cache/ast/v0.9.8/c2ea788e6c182d6862d94922885ea0dfa4e6a7017c59b26e501be30797b646e4.json](graphify-out/cache/ast/v0.9.8/c2ea788e6c182d6862d94922885ea0dfa4e6a7017c59b26e501be30797b646e4.json) |  | 2026-07-08 | 11KB | `ffc61a9a` |
| [graphify-out/cache/ast/v0.9.8/c349a774b749129d6c5228e99110cee08d5446ae4cdca7bf269a0ac13ce689eb.json](graphify-out/cache/ast/v0.9.8/c349a774b749129d6c5228e99110cee08d5446ae4cdca7bf269a0ac13ce689eb.json) |  | 2026-07-08 | 30KB | `d3be285a` |
| [graphify-out/cache/ast/v0.9.8/c3612b6a2eeb9c9bc242e717031575f47f5839dd62240f1283565d237f91555f.json](graphify-out/cache/ast/v0.9.8/c3612b6a2eeb9c9bc242e717031575f47f5839dd62240f1283565d237f91555f.json) |  | 2026-07-23 | 18KB | `2bb95e05` |
| [graphify-out/cache/ast/v0.9.8/c492731516e5bfb10276347c7b6b846aaa8ab266ed819d504f50a85620492e7c.json](graphify-out/cache/ast/v0.9.8/c492731516e5bfb10276347c7b6b846aaa8ab266ed819d504f50a85620492e7c.json) |  | 2026-07-22 | 9KB | `a7476293` |
| [graphify-out/cache/ast/v0.9.8/c4a5ce7f810bdc4be399f752481cd5210855657f659e72dc79cb31d8f1d5bd13.json](graphify-out/cache/ast/v0.9.8/c4a5ce7f810bdc4be399f752481cd5210855657f659e72dc79cb31d8f1d5bd13.json) |  | 2026-07-29 | 8KB | `2ba02d33` |
| [graphify-out/cache/ast/v0.9.8/c4a6d325b610018dfe2e5b888de24daed5e156505f64dbf0b529d09707f2571f.json](graphify-out/cache/ast/v0.9.8/c4a6d325b610018dfe2e5b888de24daed5e156505f64dbf0b529d09707f2571f.json) |  | 2026-07-25 | 15KB | `7bea32cf` |
| [graphify-out/cache/ast/v0.9.8/c4bc6ccd49090ed7f0b4f4365d3e565bd7121a1ae5d42a1d75177e015c39a716.json](graphify-out/cache/ast/v0.9.8/c4bc6ccd49090ed7f0b4f4365d3e565bd7121a1ae5d42a1d75177e015c39a716.json) |  | 2026-07-29 | 56KB | `15360e42` |
| [graphify-out/cache/ast/v0.9.8/c4def0769fa7b12a927fde991141b10f5a14b32a42c4e9291355e6748962cc4d.json](graphify-out/cache/ast/v0.9.8/c4def0769fa7b12a927fde991141b10f5a14b32a42c4e9291355e6748962cc4d.json) |  | 2026-07-08 | 12KB | `e2bdad62` |
| [graphify-out/cache/ast/v0.9.8/c4f7cef1ff3319c4cb9ec2b2fac63c08d92e938f090eb93b15ab1c4670feffc4.json](graphify-out/cache/ast/v0.9.8/c4f7cef1ff3319c4cb9ec2b2fac63c08d92e938f090eb93b15ab1c4670feffc4.json) |  | 2026-07-07 | 6KB | `13484135` |
| [graphify-out/cache/ast/v0.9.8/c51619a80bbb4598e62a0b571fe06c31040338ce34c2817041be6dc5d44d256e.json](graphify-out/cache/ast/v0.9.8/c51619a80bbb4598e62a0b571fe06c31040338ce34c2817041be6dc5d44d256e.json) |  | 2026-07-08 | 768B | `8c90fa78` |
| [graphify-out/cache/ast/v0.9.8/c53f035afa5dab19e072e42f7f035232e14b9e9e0b89d0317f4e87680faf7bd3.json](graphify-out/cache/ast/v0.9.8/c53f035afa5dab19e072e42f7f035232e14b9e9e0b89d0317f4e87680faf7bd3.json) |  | 2026-07-08 | 23KB | `44ab1305` |
| [graphify-out/cache/ast/v0.9.8/c54d64c997724cbb9f47e0a15fcbb81f3c2b1022f06e32a8a2a2e82b8d19f921.json](graphify-out/cache/ast/v0.9.8/c54d64c997724cbb9f47e0a15fcbb81f3c2b1022f06e32a8a2a2e82b8d19f921.json) |  | 2026-07-08 | 13KB | `7e99f261` |
| [graphify-out/cache/ast/v0.9.8/c55487ff05ae632311ab6132a46e7e7bb3de85831896e23a6173ef36e526195d.json](graphify-out/cache/ast/v0.9.8/c55487ff05ae632311ab6132a46e7e7bb3de85831896e23a6173ef36e526195d.json) |  | 2026-07-08 | 3KB | `75290093` |
| [graphify-out/cache/ast/v0.9.8/c56ab47aec8305f92e12a534359bd61b89500ff5a01d89e37fcfa82ffa4015b2.json](graphify-out/cache/ast/v0.9.8/c56ab47aec8305f92e12a534359bd61b89500ff5a01d89e37fcfa82ffa4015b2.json) |  | 2026-07-09 | 134KB | `78bef1d3` |
| [graphify-out/cache/ast/v0.9.8/c58c2f723fbc04bdb1e36808dd80fb1f6b0a71d197d69c8ccaff1596ed06341e.json](graphify-out/cache/ast/v0.9.8/c58c2f723fbc04bdb1e36808dd80fb1f6b0a71d197d69c8ccaff1596ed06341e.json) |  | 2026-07-08 | 22KB | `ca2c83dc` |
| [graphify-out/cache/ast/v0.9.8/c5bb084ac33209d2d5241896705c13124974b42fbba08f2cad6005794d6726b8.json](graphify-out/cache/ast/v0.9.8/c5bb084ac33209d2d5241896705c13124974b42fbba08f2cad6005794d6726b8.json) |  | 2026-07-07 | 21KB | `ba225412` |
| [graphify-out/cache/ast/v0.9.8/c5cad5748e0b58dbc9792d57510c04e5e8af796521dbd7060e8030da294c50df.json](graphify-out/cache/ast/v0.9.8/c5cad5748e0b58dbc9792d57510c04e5e8af796521dbd7060e8030da294c50df.json) |  | 2026-07-08 | 8KB | `6af0bf74` |
| [graphify-out/cache/ast/v0.9.8/c5e0c4f7530e279e19cc588725469d872aca686144989a177169b961736f7c0f.json](graphify-out/cache/ast/v0.9.8/c5e0c4f7530e279e19cc588725469d872aca686144989a177169b961736f7c0f.json) |  | 2026-07-08 | 32KB | `4c4df358` |
| [graphify-out/cache/ast/v0.9.8/c63ec1346eacfa262dce8831f79d52288490770438eb84ccc420dcd74ed603b0.json](graphify-out/cache/ast/v0.9.8/c63ec1346eacfa262dce8831f79d52288490770438eb84ccc420dcd74ed603b0.json) |  | 2026-07-08 | 9KB | `201243be` |
| [graphify-out/cache/ast/v0.9.8/c668c365dc0e855950d625f8fada8691c4c4b1912a705fe3afae2e330fb4cee3.json](graphify-out/cache/ast/v0.9.8/c668c365dc0e855950d625f8fada8691c4c4b1912a705fe3afae2e330fb4cee3.json) |  | 2026-07-07 | 68KB | `cae0e645` |
| [graphify-out/cache/ast/v0.9.8/c6bf81d727ed0672053f0c82b9fa08ef495c66b7e6bf2c18ea5f8b5f2b448676.json](graphify-out/cache/ast/v0.9.8/c6bf81d727ed0672053f0c82b9fa08ef495c66b7e6bf2c18ea5f8b5f2b448676.json) |  | 2026-07-07 | 40KB | `902c7d87` |
| [graphify-out/cache/ast/v0.9.8/c712d3a7fa2e4b134fc92f6b17a98ea1eccee97110cef040e3eb932c1ff1755c.json](graphify-out/cache/ast/v0.9.8/c712d3a7fa2e4b134fc92f6b17a98ea1eccee97110cef040e3eb932c1ff1755c.json) |  | 2026-07-08 | 6KB | `87f37aa1` |
| [graphify-out/cache/ast/v0.9.8/c7275d0d5c46d6501c309aae85dc71d30352e6557fb5a68e8e424ca67a5d9f67.json](graphify-out/cache/ast/v0.9.8/c7275d0d5c46d6501c309aae85dc71d30352e6557fb5a68e8e424ca67a5d9f67.json) |  | 2026-07-08 | 20KB | `da620421` |
| [graphify-out/cache/ast/v0.9.8/c72f94058bc626f611270f168be334e1808441884221ffed707502014e4626f0.json](graphify-out/cache/ast/v0.9.8/c72f94058bc626f611270f168be334e1808441884221ffed707502014e4626f0.json) |  | 2026-07-08 | 13KB | `4ebfed8d` |
| [graphify-out/cache/ast/v0.9.8/c75f63ec2b7db360a12cb7d155713fe16341956403c3779c248504497f653d96.json](graphify-out/cache/ast/v0.9.8/c75f63ec2b7db360a12cb7d155713fe16341956403c3779c248504497f653d96.json) |  | 2026-07-08 | 32KB | `af1dfa81` |
| [graphify-out/cache/ast/v0.9.8/c7649d0c989a175c9da2b4ecc01cf58e7a8e03cc0752b68e49ed14418747b059.json](graphify-out/cache/ast/v0.9.8/c7649d0c989a175c9da2b4ecc01cf58e7a8e03cc0752b68e49ed14418747b059.json) |  | 2026-07-31 | 14KB | `4cb92e03` |
| [graphify-out/cache/ast/v0.9.8/c7e97ee92c1b2354a096aeaa24857056f2c870640ada0ad4235661f79844a2c5.json](graphify-out/cache/ast/v0.9.8/c7e97ee92c1b2354a096aeaa24857056f2c870640ada0ad4235661f79844a2c5.json) |  | 2026-07-10 | 4KB | `eafc66bd` |
| [graphify-out/cache/ast/v0.9.8/c7f22e64abdcec192ff757c48cb314ed7d9e81158de1bf5a7ca84f00d54d8fb8.json](graphify-out/cache/ast/v0.9.8/c7f22e64abdcec192ff757c48cb314ed7d9e81158de1bf5a7ca84f00d54d8fb8.json) |  | 2026-07-08 | 30KB | `a71b65d5` |
| [graphify-out/cache/ast/v0.9.8/c7f987844ca369b63a948c6be30d2cafb077b7979f09ff0e324c4262d134bdfe.json](graphify-out/cache/ast/v0.9.8/c7f987844ca369b63a948c6be30d2cafb077b7979f09ff0e324c4262d134bdfe.json) |  | 2026-07-08 | 1KB | `7cd06900` |
| [graphify-out/cache/ast/v0.9.8/c815505acdfb4ad6190ec5d5ad934895b89d3610b079722dd2254d1f3ef9f7dc.json](graphify-out/cache/ast/v0.9.8/c815505acdfb4ad6190ec5d5ad934895b89d3610b079722dd2254d1f3ef9f7dc.json) |  | 2026-07-07 | 4KB | `44c589c4` |
| [graphify-out/cache/ast/v0.9.8/c821b181f49c8926367085a1a8b580d68454321325dd195c340c18777986a1c0.json](graphify-out/cache/ast/v0.9.8/c821b181f49c8926367085a1a8b580d68454321325dd195c340c18777986a1c0.json) |  | 2026-07-30 | 10KB | `522d52fa` |
| [graphify-out/cache/ast/v0.9.8/c8278831535826b663d7f98efd09857722903aa2ed35bc9f00d13f91ec97067b.json](graphify-out/cache/ast/v0.9.8/c8278831535826b663d7f98efd09857722903aa2ed35bc9f00d13f91ec97067b.json) |  | 2026-07-08 | 9KB | `4a9591ec` |
| [graphify-out/cache/ast/v0.9.8/c8922ed84e8205496f6ff42034f4f0803227379193b417ab0b446ba3ad41952e.json](graphify-out/cache/ast/v0.9.8/c8922ed84e8205496f6ff42034f4f0803227379193b417ab0b446ba3ad41952e.json) |  | 2026-07-31 | 3KB | `0156a213` |
| [graphify-out/cache/ast/v0.9.8/c8ee3202692623ce9e2f78797e4fac66a87f4efe998b3db96dc7a6f879f9988b.json](graphify-out/cache/ast/v0.9.8/c8ee3202692623ce9e2f78797e4fac66a87f4efe998b3db96dc7a6f879f9988b.json) |  | 2026-07-08 | 6KB | `94e30b5e` |
| [graphify-out/cache/ast/v0.9.8/c991a303daa31e10938b804fae9b3774cb79ddfb811eafa35612e4b972a8cefa.json](graphify-out/cache/ast/v0.9.8/c991a303daa31e10938b804fae9b3774cb79ddfb811eafa35612e4b972a8cefa.json) |  | 2026-07-08 | 3KB | `a9c5775d` |
| [graphify-out/cache/ast/v0.9.8/c9cac7d22690fa677bcf06b2549be6814e36f10d9ca5884c4047b351dfe0ccc0.json](graphify-out/cache/ast/v0.9.8/c9cac7d22690fa677bcf06b2549be6814e36f10d9ca5884c4047b351dfe0ccc0.json) |  | 2026-07-08 | 8KB | `062e84ad` |
| [graphify-out/cache/ast/v0.9.8/ca025357b8e8ec6d7170b94ddf4e377a1054901ea63cff0ad0fbd2135ecfd5da.json](graphify-out/cache/ast/v0.9.8/ca025357b8e8ec6d7170b94ddf4e377a1054901ea63cff0ad0fbd2135ecfd5da.json) |  | 2026-07-08 | 4KB | `0f439882` |
| [graphify-out/cache/ast/v0.9.8/ca544c6ac9dd4051d0e08afafa204cb253c10ed39aa32d2fcbb904602218418b.json](graphify-out/cache/ast/v0.9.8/ca544c6ac9dd4051d0e08afafa204cb253c10ed39aa32d2fcbb904602218418b.json) |  | 2026-08-01 | 25KB | `0280a778` |
| [graphify-out/cache/ast/v0.9.8/cac6b5b92b299f43dec79e423e35e081fc93e5e3847df0c39c59f2d22b10d87e.json](graphify-out/cache/ast/v0.9.8/cac6b5b92b299f43dec79e423e35e081fc93e5e3847df0c39c59f2d22b10d87e.json) |  | 2026-07-08 | 8KB | `0221d441` |
| [graphify-out/cache/ast/v0.9.8/caf1d7caee8e5cd28fc8233165867111cb8af092af6dc70ea5ba3d1257bde4c4.json](graphify-out/cache/ast/v0.9.8/caf1d7caee8e5cd28fc8233165867111cb8af092af6dc70ea5ba3d1257bde4c4.json) |  | 2026-07-08 | 14KB | `c83b6ec7` |
| [graphify-out/cache/ast/v0.9.8/cb1847459f380c6a48571c94865f66569925aed2f293e49ae4ad2c4509b7c235.json](graphify-out/cache/ast/v0.9.8/cb1847459f380c6a48571c94865f66569925aed2f293e49ae4ad2c4509b7c235.json) |  | 2026-07-08 | 43KB | `4b07f8a4` |
| [graphify-out/cache/ast/v0.9.8/cbd3f57ab5d37d3a1cf3e240f65d880bd0bc39a0a2fae30764631a29ae5b9a6e.json](graphify-out/cache/ast/v0.9.8/cbd3f57ab5d37d3a1cf3e240f65d880bd0bc39a0a2fae30764631a29ae5b9a6e.json) |  | 2026-07-31 | 8KB | `a249905a` |
| [graphify-out/cache/ast/v0.9.8/cc471eb69bb26e3ab22a978288bf5b593b5d39fa3f9e248a48508cdfd801f87b.json](graphify-out/cache/ast/v0.9.8/cc471eb69bb26e3ab22a978288bf5b593b5d39fa3f9e248a48508cdfd801f87b.json) |  | 2026-07-08 | 58KB | `c5f62f15` |
| [graphify-out/cache/ast/v0.9.8/cc75d2e7aefe4c24bf80c2a85c5d77e38d6f4e5ddbdf0788ef89ba14a04a57ca.json](graphify-out/cache/ast/v0.9.8/cc75d2e7aefe4c24bf80c2a85c5d77e38d6f4e5ddbdf0788ef89ba14a04a57ca.json) |  | 2026-07-08 | 8KB | `c77bcb54` |
| [graphify-out/cache/ast/v0.9.8/cc7fdb6d72ff497f457de93c24868211f64690ebcfc1d7b5f5173bf222782cfd.json](graphify-out/cache/ast/v0.9.8/cc7fdb6d72ff497f457de93c24868211f64690ebcfc1d7b5f5173bf222782cfd.json) |  | 2026-07-29 | 6KB | `36629109` |
| [graphify-out/cache/ast/v0.9.8/ccc3206bac60b95966efa7b19322173c73114108a0cff271df0f7efb5fb76b42.json](graphify-out/cache/ast/v0.9.8/ccc3206bac60b95966efa7b19322173c73114108a0cff271df0f7efb5fb76b42.json) |  | 2026-07-07 | 14KB | `e01c0f2c` |
| [graphify-out/cache/ast/v0.9.8/ccc7599dcde3b3b0a5e0cbe09662dee9ace5a25e5ee5ce5ef2e90721514d301c.json](graphify-out/cache/ast/v0.9.8/ccc7599dcde3b3b0a5e0cbe09662dee9ace5a25e5ee5ce5ef2e90721514d301c.json) |  | 2026-07-30 | 8KB | `c4c4dc15` |
| [graphify-out/cache/ast/v0.9.8/cd4733dfc82d9dd7a5ccda5abcc88dd9ee0905f1014b2145418d6ace640c6263.json](graphify-out/cache/ast/v0.9.8/cd4733dfc82d9dd7a5ccda5abcc88dd9ee0905f1014b2145418d6ace640c6263.json) |  | 2026-07-08 | 123KB | `03ef1fb8` |
| [graphify-out/cache/ast/v0.9.8/cd9d038cb71cd17dd69aa5571a7ce3b2f51b337a89c7c1aaee417b80bb56105b.json](graphify-out/cache/ast/v0.9.8/cd9d038cb71cd17dd69aa5571a7ce3b2f51b337a89c7c1aaee417b80bb56105b.json) |  | 2026-07-08 | 43KB | `ce310a16` |
| [graphify-out/cache/ast/v0.9.8/ce07ec9ea3c8af2565338b2fde2d2bcdb017e7518fdfc16c6f131f2e5259d513.json](graphify-out/cache/ast/v0.9.8/ce07ec9ea3c8af2565338b2fde2d2bcdb017e7518fdfc16c6f131f2e5259d513.json) |  | 2026-07-08 | 36KB | `601bab7d` |
| [graphify-out/cache/ast/v0.9.8/ce3dc560212a7c006ab267865997dbf9c68c38e673eab60931032f6a372f4207.json](graphify-out/cache/ast/v0.9.8/ce3dc560212a7c006ab267865997dbf9c68c38e673eab60931032f6a372f4207.json) |  | 2026-07-09 | 8KB | `8155ea7f` |
| [graphify-out/cache/ast/v0.9.8/ce5dc372710b1e3313e142acefa4cc658632ea9e827433f5fba73ac27cefb9e6.json](graphify-out/cache/ast/v0.9.8/ce5dc372710b1e3313e142acefa4cc658632ea9e827433f5fba73ac27cefb9e6.json) |  | 2026-07-24 | 25KB | `bb5381e7` |
| [graphify-out/cache/ast/v0.9.8/ce60ec8b10fd36f79405a4e81303d93e143e555a6232790b1ebb08710b7d2e6a.json](graphify-out/cache/ast/v0.9.8/ce60ec8b10fd36f79405a4e81303d93e143e555a6232790b1ebb08710b7d2e6a.json) |  | 2026-07-08 | 6KB | `08e9c4bc` |
| [graphify-out/cache/ast/v0.9.8/cf127b45cef2828e4224a3f51291188e701f522b13e2e00d94d5fdda38a2b0f7.json](graphify-out/cache/ast/v0.9.8/cf127b45cef2828e4224a3f51291188e701f522b13e2e00d94d5fdda38a2b0f7.json) |  | 2026-07-07 | 21KB | `0b696e03` |
| [graphify-out/cache/ast/v0.9.8/cf2ef6069be6d8305cd761727e35a4f89f213321c0c2f3d5cd8978e7eab269b3.json](graphify-out/cache/ast/v0.9.8/cf2ef6069be6d8305cd761727e35a4f89f213321c0c2f3d5cd8978e7eab269b3.json) |  | 2026-07-08 | 6KB | `4c43170d` |
| [graphify-out/cache/ast/v0.9.8/cf3148aa3890639ff1138c7d08f42ab2c8b22c17d37bf066e60a40cf9c939c04.json](graphify-out/cache/ast/v0.9.8/cf3148aa3890639ff1138c7d08f42ab2c8b22c17d37bf066e60a40cf9c939c04.json) |  | 2026-07-08 | 50KB | `d6ac3fb5` |
| [graphify-out/cache/ast/v0.9.8/cf3adaa9d0d00182f9f0cc588208c1ff231fdd1643a0d1a0822f01ed6c272a4b.json](graphify-out/cache/ast/v0.9.8/cf3adaa9d0d00182f9f0cc588208c1ff231fdd1643a0d1a0822f01ed6c272a4b.json) |  | 2026-07-08 | 52KB | `d0e78a74` |
| [graphify-out/cache/ast/v0.9.8/cfb53e66fb1329d5f1631dc1a715925efcaa998393aed1d22849d6adf4168db2.json](graphify-out/cache/ast/v0.9.8/cfb53e66fb1329d5f1631dc1a715925efcaa998393aed1d22849d6adf4168db2.json) |  | 2026-07-08 | 6KB | `23473b7a` |
| [graphify-out/cache/ast/v0.9.8/cff840840724cac79c603cf0396512e8333df3acfec3d768fc772b16052ca755.json](graphify-out/cache/ast/v0.9.8/cff840840724cac79c603cf0396512e8333df3acfec3d768fc772b16052ca755.json) |  | 2026-07-30 | 6KB | `755660b7` |
| [graphify-out/cache/ast/v0.9.8/d0149b19d424b2d542d17dc4033a5cbc7a004d299d50826968a42ee106ccaab2.json](graphify-out/cache/ast/v0.9.8/d0149b19d424b2d542d17dc4033a5cbc7a004d299d50826968a42ee106ccaab2.json) |  | 2026-07-07 | 838B | `87232e73` |
| [graphify-out/cache/ast/v0.9.8/d025e3088bace638f0007a2e45a58df498c07de50ef61cca5cc48cb47cfd3313.json](graphify-out/cache/ast/v0.9.8/d025e3088bace638f0007a2e45a58df498c07de50ef61cca5cc48cb47cfd3313.json) |  | 2026-07-08 | 46KB | `5e777931` |
| [graphify-out/cache/ast/v0.9.8/d0e824a844e5ec7229f11588808b0de6909eaaf9e06e51ec57e936c2b57dd345.json](graphify-out/cache/ast/v0.9.8/d0e824a844e5ec7229f11588808b0de6909eaaf9e06e51ec57e936c2b57dd345.json) |  | 2026-07-08 | 9KB | `b407c096` |
| [graphify-out/cache/ast/v0.9.8/d13613be343e85f1cf67d13eee8fe206e9b5fd2e3d5dd354e4fc226bc089a2d7.json](graphify-out/cache/ast/v0.9.8/d13613be343e85f1cf67d13eee8fe206e9b5fd2e3d5dd354e4fc226bc089a2d7.json) |  | 2026-07-08 | 4KB | `a5c3b0ff` |
| [graphify-out/cache/ast/v0.9.8/d13ffde02ca1e8fb8e317ac281595d6de5d1a219a037f8fb62d45552cd45b52a.json](graphify-out/cache/ast/v0.9.8/d13ffde02ca1e8fb8e317ac281595d6de5d1a219a037f8fb62d45552cd45b52a.json) |  | 2026-07-08 | 78KB | `2b2c4b49` |
| [graphify-out/cache/ast/v0.9.8/d14963ab48dcde5c4feec065c27e8f3fe8519a6103839800faf0a721c18ba7eb.json](graphify-out/cache/ast/v0.9.8/d14963ab48dcde5c4feec065c27e8f3fe8519a6103839800faf0a721c18ba7eb.json) |  | 2026-07-31 | 21KB | `a59eb842` |
| [graphify-out/cache/ast/v0.9.8/d14968f967ccaab758562caffd234aca4580a3996126f5141229c838d8b3a044.json](graphify-out/cache/ast/v0.9.8/d14968f967ccaab758562caffd234aca4580a3996126f5141229c838d8b3a044.json) |  | 2026-07-08 | 6KB | `a6aa4bad` |
| [graphify-out/cache/ast/v0.9.8/d17624fe38cf01f9787b5844e04fc4ed112d30257696e6db4e4c43031a73de73.json](graphify-out/cache/ast/v0.9.8/d17624fe38cf01f9787b5844e04fc4ed112d30257696e6db4e4c43031a73de73.json) |  | 2026-07-27 | 9KB | `26eaeecf` |
| [graphify-out/cache/ast/v0.9.8/d19ad59768e18c545fb5e62ef453ac4d39a203511e7133a1ef016665dfd3a997.json](graphify-out/cache/ast/v0.9.8/d19ad59768e18c545fb5e62ef453ac4d39a203511e7133a1ef016665dfd3a997.json) |  | 2026-07-08 | 979B | `b3a48f7c` |
| [graphify-out/cache/ast/v0.9.8/d1a29da8294bfcf9bf8c332ad50204a994630bcc080f9a8f3ac406e7732686c1.json](graphify-out/cache/ast/v0.9.8/d1a29da8294bfcf9bf8c332ad50204a994630bcc080f9a8f3ac406e7732686c1.json) |  | 2026-07-08 | 10KB | `38aa9213` |
| [graphify-out/cache/ast/v0.9.8/d1c21ddcffdf89a95fe939f78dd73f769d8e7341850af71ad61fdabee1187427.json](graphify-out/cache/ast/v0.9.8/d1c21ddcffdf89a95fe939f78dd73f769d8e7341850af71ad61fdabee1187427.json) |  | 2026-07-07 | 19KB | `5ddab5f1` |
| [graphify-out/cache/ast/v0.9.8/d2180c237e31bd8eb7d7f11a623a7c76b3197c679469f6a17a3f1bd5f333d884.json](graphify-out/cache/ast/v0.9.8/d2180c237e31bd8eb7d7f11a623a7c76b3197c679469f6a17a3f1bd5f333d884.json) |  | 2026-07-08 | 8KB | `a733534a` |
| [graphify-out/cache/ast/v0.9.8/d21eeb2e301bd514d6c391d698e1fb6aa6f1550729b46487b4e690a67525e914.json](graphify-out/cache/ast/v0.9.8/d21eeb2e301bd514d6c391d698e1fb6aa6f1550729b46487b4e690a67525e914.json) |  | 2026-07-08 | 14KB | `4afc550c` |
| [graphify-out/cache/ast/v0.9.8/d29b0e6cdd1c0d4d517d17bbf9cf77e0da74cf07e28383958f0e8fd9630e038b.json](graphify-out/cache/ast/v0.9.8/d29b0e6cdd1c0d4d517d17bbf9cf77e0da74cf07e28383958f0e8fd9630e038b.json) |  | 2026-07-08 | 4KB | `bc80a95b` |
| [graphify-out/cache/ast/v0.9.8/d2a8a5d1a9c5de3a6d0e463980e440fd9f0e0b758f53b92a060754688285de59.json](graphify-out/cache/ast/v0.9.8/d2a8a5d1a9c5de3a6d0e463980e440fd9f0e0b758f53b92a060754688285de59.json) |  | 2026-07-08 | 7KB | `765edf3a` |
| [graphify-out/cache/ast/v0.9.8/d303e92e0386c886e78c05f60f61471e1581981d8a197078919cd8133093a668.json](graphify-out/cache/ast/v0.9.8/d303e92e0386c886e78c05f60f61471e1581981d8a197078919cd8133093a668.json) |  | 2026-07-07 | 23KB | `4d0496a6` |
| [graphify-out/cache/ast/v0.9.8/d35ba4033b8a7c70e6ec80dbeb1bde4394fdc8a3ad038e4577b545a824413edc.json](graphify-out/cache/ast/v0.9.8/d35ba4033b8a7c70e6ec80dbeb1bde4394fdc8a3ad038e4577b545a824413edc.json) |  | 2026-07-07 | 18KB | `3a7cfea5` |
| [graphify-out/cache/ast/v0.9.8/d3611eefab80209450659006a3dcd7218e6bd10844888be9a1bb3d8dfabf4192.json](graphify-out/cache/ast/v0.9.8/d3611eefab80209450659006a3dcd7218e6bd10844888be9a1bb3d8dfabf4192.json) |  | 2026-07-08 | 42KB | `b5d93ab4` |
| [graphify-out/cache/ast/v0.9.8/d371d7ffcf3ba3d82c342353b227dc0aa6848337dc2272d3d5b88be27588fa8c.json](graphify-out/cache/ast/v0.9.8/d371d7ffcf3ba3d82c342353b227dc0aa6848337dc2272d3d5b88be27588fa8c.json) |  | 2026-07-08 | 11KB | `ea254756` |
| [graphify-out/cache/ast/v0.9.8/d38043b95a66d8d957a60954fffdee3c8b0a277b3279f012b0f77a43bfa2f71b.json](graphify-out/cache/ast/v0.9.8/d38043b95a66d8d957a60954fffdee3c8b0a277b3279f012b0f77a43bfa2f71b.json) |  | 2026-07-07 | 18KB | `6ee234e1` |
| [graphify-out/cache/ast/v0.9.8/d39509a657b95c90b450514f5b1ab09bf1901f2cae1ab68b00d756106632fcd8.json](graphify-out/cache/ast/v0.9.8/d39509a657b95c90b450514f5b1ab09bf1901f2cae1ab68b00d756106632fcd8.json) |  | 2026-07-07 | 16KB | `1e44d34f` |
| [graphify-out/cache/ast/v0.9.8/d39d61b80611c94071c63272c79e4871049a1e804264909e58b472362d49aa23.json](graphify-out/cache/ast/v0.9.8/d39d61b80611c94071c63272c79e4871049a1e804264909e58b472362d49aa23.json) |  | 2026-07-22 | 8KB | `43d15480` |
| [graphify-out/cache/ast/v0.9.8/d3d095568388244995310ee1672bc859e5375890a1a9c38e98dbde75c71456f8.json](graphify-out/cache/ast/v0.9.8/d3d095568388244995310ee1672bc859e5375890a1a9c38e98dbde75c71456f8.json) |  | 2026-07-31 | 27KB | `e4546852` |
| [graphify-out/cache/ast/v0.9.8/d3f1968fb69ee4183075ce5f14730b37c9304d84b7cce7d67907619e4667ac27.json](graphify-out/cache/ast/v0.9.8/d3f1968fb69ee4183075ce5f14730b37c9304d84b7cce7d67907619e4667ac27.json) |  | 2026-07-10 | 8KB | `0101e9bb` |
| [graphify-out/cache/ast/v0.9.8/d425703fd8a83f3e665cc08b6ab60dc2d6c9ffce6c10ac0874a4bcc8b64e93ff.json](graphify-out/cache/ast/v0.9.8/d425703fd8a83f3e665cc08b6ab60dc2d6c9ffce6c10ac0874a4bcc8b64e93ff.json) |  | 2026-07-07 | 789B | `869c1eda` |
| [graphify-out/cache/ast/v0.9.8/d43c521f8625b4b250fff3bd72acd037bed1a5876b1e2ba441b26319134c8b84.json](graphify-out/cache/ast/v0.9.8/d43c521f8625b4b250fff3bd72acd037bed1a5876b1e2ba441b26319134c8b84.json) |  | 2026-07-08 | 6KB | `f6208b09` |
| [graphify-out/cache/ast/v0.9.8/d61b8f62cf02b89101c6c7edf4e0eeda3481a6a8d510b551468a15feb757ff7d.json](graphify-out/cache/ast/v0.9.8/d61b8f62cf02b89101c6c7edf4e0eeda3481a6a8d510b551468a15feb757ff7d.json) |  | 2026-07-08 | 3KB | `d32b4063` |
| [graphify-out/cache/ast/v0.9.8/d62cc2b53e07d6f0dcd12857bf5ec5eded7f8b357fadb94f7383973d94b75a15.json](graphify-out/cache/ast/v0.9.8/d62cc2b53e07d6f0dcd12857bf5ec5eded7f8b357fadb94f7383973d94b75a15.json) |  | 2026-07-08 | 23KB | `3feaf91d` |
| [graphify-out/cache/ast/v0.9.8/d66233e55731f23bcb5e5f6fbe047f9f3fc75d0b49d3300430fde394b8df3272.json](graphify-out/cache/ast/v0.9.8/d66233e55731f23bcb5e5f6fbe047f9f3fc75d0b49d3300430fde394b8df3272.json) |  | 2026-07-08 | 14KB | `77a0cc40` |
| [graphify-out/cache/ast/v0.9.8/d666b6c6e0f9d4972a624e2e5eb81db225238499fd1b4b7bd5fb5896f34d286f.json](graphify-out/cache/ast/v0.9.8/d666b6c6e0f9d4972a624e2e5eb81db225238499fd1b4b7bd5fb5896f34d286f.json) |  | 2026-07-08 | 6KB | `7f260945` |
| [graphify-out/cache/ast/v0.9.8/d68a46b3bf77648842a8a67fd3973ae7d052c1c568e10b038fd95be92169730c.json](graphify-out/cache/ast/v0.9.8/d68a46b3bf77648842a8a67fd3973ae7d052c1c568e10b038fd95be92169730c.json) |  | 2026-07-08 | 62KB | `b1eb2375` |
| [graphify-out/cache/ast/v0.9.8/d6ad672122aec5e0ebc32fbe2965d2806a757bfa18c35e8e58b07f028c5f0258.json](graphify-out/cache/ast/v0.9.8/d6ad672122aec5e0ebc32fbe2965d2806a757bfa18c35e8e58b07f028c5f0258.json) |  | 2026-07-08 | 3KB | `7b4bed32` |
| [graphify-out/cache/ast/v0.9.8/d75ea0ce6d81a3533015a2a6262b8e2129ed78cd6e9b8ab20d1b70b982bae492.json](graphify-out/cache/ast/v0.9.8/d75ea0ce6d81a3533015a2a6262b8e2129ed78cd6e9b8ab20d1b70b982bae492.json) |  | 2026-07-08 | 5KB | `c9f8791a` |
| [graphify-out/cache/ast/v0.9.8/d7af9ce9b25172f688d9b0b6ed6ba73b2132dfe0fd823d05ecb22aa66fe3a971.json](graphify-out/cache/ast/v0.9.8/d7af9ce9b25172f688d9b0b6ed6ba73b2132dfe0fd823d05ecb22aa66fe3a971.json) |  | 2026-07-08 | 1KB | `441d7298` |
| [graphify-out/cache/ast/v0.9.8/d7ecbcbaa534939ca868b6436ac0a1358a865efaafab8a5126768eced02cd116.json](graphify-out/cache/ast/v0.9.8/d7ecbcbaa534939ca868b6436ac0a1358a865efaafab8a5126768eced02cd116.json) |  | 2026-07-08 | 14KB | `40b4aaae` |
| [graphify-out/cache/ast/v0.9.8/d7f6ff36d5c1abe2cc558096badc3914a76cb43e7b4148d77e1da67808adae81.json](graphify-out/cache/ast/v0.9.8/d7f6ff36d5c1abe2cc558096badc3914a76cb43e7b4148d77e1da67808adae81.json) |  | 2026-07-08 | 3KB | `82b1ca2c` |
| [graphify-out/cache/ast/v0.9.8/d816b5cbf090b90e1e2e9137db12124035b6d3d48d9e4340894bb5b472a27084.json](graphify-out/cache/ast/v0.9.8/d816b5cbf090b90e1e2e9137db12124035b6d3d48d9e4340894bb5b472a27084.json) |  | 2026-07-07 | 11KB | `3973528e` |
| [graphify-out/cache/ast/v0.9.8/d8367de04fbc1e6376c8414b2f1774398c0248803b67fa9bac451642cd32397a.json](graphify-out/cache/ast/v0.9.8/d8367de04fbc1e6376c8414b2f1774398c0248803b67fa9bac451642cd32397a.json) |  | 2026-07-24 | 25KB | `46997219` |
| [graphify-out/cache/ast/v0.9.8/d8420d735aea05633c9ded080ec0119e5fce75868ad1343434cea0f22762d9c8.json](graphify-out/cache/ast/v0.9.8/d8420d735aea05633c9ded080ec0119e5fce75868ad1343434cea0f22762d9c8.json) |  | 2026-07-08 | 867B | `729ec6db` |
| [graphify-out/cache/ast/v0.9.8/d8c8c5aa60df24a1dac37b4d2c97386ffd67118cd2e3587489a0cb20e52b2950.json](graphify-out/cache/ast/v0.9.8/d8c8c5aa60df24a1dac37b4d2c97386ffd67118cd2e3587489a0cb20e52b2950.json) |  | 2026-07-08 | 14KB | `bec795f6` |
| [graphify-out/cache/ast/v0.9.8/d9251d638957cea5676528af94ec088869fefb359eb2cc33ebeee34adce29d85.json](graphify-out/cache/ast/v0.9.8/d9251d638957cea5676528af94ec088869fefb359eb2cc33ebeee34adce29d85.json) |  | 2026-07-23 | 7KB | `9bcdf11a` |
| [graphify-out/cache/ast/v0.9.8/d93ae2adbb230e8a5996a202ad04f48b12b5a3ba1f5cd217e66fe1c34145fd38.json](graphify-out/cache/ast/v0.9.8/d93ae2adbb230e8a5996a202ad04f48b12b5a3ba1f5cd217e66fe1c34145fd38.json) |  | 2026-07-24 | 4KB | `1ef0995b` |
| [graphify-out/cache/ast/v0.9.8/d9754ce50772383721da317062494a248160c4716046f060439fce274218ede3.json](graphify-out/cache/ast/v0.9.8/d9754ce50772383721da317062494a248160c4716046f060439fce274218ede3.json) |  | 2026-07-07 | 19KB | `765aa7fc` |
| [graphify-out/cache/ast/v0.9.8/d9fc1400deb049c2d94ba8bb4b718d201b67af875576e001c5d5cbb7a6c1af0c.json](graphify-out/cache/ast/v0.9.8/d9fc1400deb049c2d94ba8bb4b718d201b67af875576e001c5d5cbb7a6c1af0c.json) |  | 2026-07-07 | 101KB | `ea31e5af` |
| [graphify-out/cache/ast/v0.9.8/da52e1beb24087c62536cee313862737e7f6d1ddf47f0fefc1be28905a2121bc.json](graphify-out/cache/ast/v0.9.8/da52e1beb24087c62536cee313862737e7f6d1ddf47f0fefc1be28905a2121bc.json) |  | 2026-07-29 | 13KB | `1a755433` |
| [graphify-out/cache/ast/v0.9.8/da713305e9e0c790a4b1cb33cd933e6de84ce1958adbb41ee6ec980bcb506dfc.json](graphify-out/cache/ast/v0.9.8/da713305e9e0c790a4b1cb33cd933e6de84ce1958adbb41ee6ec980bcb506dfc.json) |  | 2026-07-08 | 8KB | `afadfb99` |
| [graphify-out/cache/ast/v0.9.8/da840d5cedbbeee70315269d66914337213a6d68fd229a327621a975aaf9d77e.json](graphify-out/cache/ast/v0.9.8/da840d5cedbbeee70315269d66914337213a6d68fd229a327621a975aaf9d77e.json) |  | 2026-07-08 | 12KB | `9077a6fc` |
| [graphify-out/cache/ast/v0.9.8/dab18286146036b63418dd8ba17da3d5b3bd8cc60a0f1c557ab410ee0ad34c7c.json](graphify-out/cache/ast/v0.9.8/dab18286146036b63418dd8ba17da3d5b3bd8cc60a0f1c557ab410ee0ad34c7c.json) |  | 2026-07-08 | 22KB | `7752d266` |
| [graphify-out/cache/ast/v0.9.8/dab797a924c188ace0e7a8a700ef9435f791638fc0fb66b2e142284aa39bd5d9.json](graphify-out/cache/ast/v0.9.8/dab797a924c188ace0e7a8a700ef9435f791638fc0fb66b2e142284aa39bd5d9.json) |  | 2026-07-08 | 23KB | `93977e82` |
| [graphify-out/cache/ast/v0.9.8/db1114b95b45c682ed359134526a7be6c6fe4bad9b7aba19efa64efda5e774f2.json](graphify-out/cache/ast/v0.9.8/db1114b95b45c682ed359134526a7be6c6fe4bad9b7aba19efa64efda5e774f2.json) |  | 2026-07-08 | 17KB | `68cf0da7` |
| [graphify-out/cache/ast/v0.9.8/db83917707a86b88e92989d17c5dc540675967ee9496d9fe39e085b795f18d2b.json](graphify-out/cache/ast/v0.9.8/db83917707a86b88e92989d17c5dc540675967ee9496d9fe39e085b795f18d2b.json) |  | 2026-07-30 | 45KB | `170ae11f` |
| [graphify-out/cache/ast/v0.9.8/dc23852ce2406046df4da275c36e8da94e6a030c42baf273136a1b93eebd18df.json](graphify-out/cache/ast/v0.9.8/dc23852ce2406046df4da275c36e8da94e6a030c42baf273136a1b93eebd18df.json) |  | 2026-07-08 | 1KB | `4b6bfa24` |
| [graphify-out/cache/ast/v0.9.8/dc30e1bffc18af43b422f5208593addf4e1f0c8966d630ad8d2a8eaa6de50127.json](graphify-out/cache/ast/v0.9.8/dc30e1bffc18af43b422f5208593addf4e1f0c8966d630ad8d2a8eaa6de50127.json) |  | 2026-07-08 | 34KB | `dd1b662f` |
| [graphify-out/cache/ast/v0.9.8/dc3d63281792d758c02bb533ef343fe9afc4bb07bb53f5b4351ca91068bc9663.json](graphify-out/cache/ast/v0.9.8/dc3d63281792d758c02bb533ef343fe9afc4bb07bb53f5b4351ca91068bc9663.json) |  | 2026-07-08 | 22KB | `fff70a50` |
| [graphify-out/cache/ast/v0.9.8/dc64e0c6b84f3714f1877a7a4287553767903ff71539564fb9d3a83b06ed0fbf.json](graphify-out/cache/ast/v0.9.8/dc64e0c6b84f3714f1877a7a4287553767903ff71539564fb9d3a83b06ed0fbf.json) |  | 2026-07-29 | 10KB | `9f9d2cd9` |
| [graphify-out/cache/ast/v0.9.8/dcb08c5dc0e1ecaef5886d4a490c69e176c27df6c2bc68d391bc90a0b6858f76.json](graphify-out/cache/ast/v0.9.8/dcb08c5dc0e1ecaef5886d4a490c69e176c27df6c2bc68d391bc90a0b6858f76.json) |  | 2026-07-08 | 18KB | `67e75cfb` |
| [graphify-out/cache/ast/v0.9.8/dd706e0f16fc334567a16b5563bdb81a9b574635059bc718d98264868ff84b5d.json](graphify-out/cache/ast/v0.9.8/dd706e0f16fc334567a16b5563bdb81a9b574635059bc718d98264868ff84b5d.json) |  | 2026-07-22 | 11KB | `7de9b46b` |
| [graphify-out/cache/ast/v0.9.8/dd8c7c05a26065785195b02e4c515cada1c85affe4805ecbb5032db88be8a95a.json](graphify-out/cache/ast/v0.9.8/dd8c7c05a26065785195b02e4c515cada1c85affe4805ecbb5032db88be8a95a.json) |  | 2026-07-08 | 1KB | `9c3ae84f` |
| [graphify-out/cache/ast/v0.9.8/de54e3f6940ef11d0eb140e3d6e3aaf8c94e7f7917cc8a7d1e1c84c430fddf23.json](graphify-out/cache/ast/v0.9.8/de54e3f6940ef11d0eb140e3d6e3aaf8c94e7f7917cc8a7d1e1c84c430fddf23.json) |  | 2026-07-08 | 44KB | `e221543d` |
| [graphify-out/cache/ast/v0.9.8/de8eb9a98668f8f049e8d21b7748b23e3fde8e021e1d321f54876557e24329d0.json](graphify-out/cache/ast/v0.9.8/de8eb9a98668f8f049e8d21b7748b23e3fde8e021e1d321f54876557e24329d0.json) |  | 2026-07-08 | 91KB | `45c3180c` |
| [graphify-out/cache/ast/v0.9.8/de90183da185712c330560eda3e7c2a2181031033a698e20626619765da94e31.json](graphify-out/cache/ast/v0.9.8/de90183da185712c330560eda3e7c2a2181031033a698e20626619765da94e31.json) |  | 2026-07-08 | 11KB | `97cd1f8b` |
| [graphify-out/cache/ast/v0.9.8/dedc0d9601ae85f1147eb3ab0cb29e780e5b4af7fd437ee912977b28992ce20b.json](graphify-out/cache/ast/v0.9.8/dedc0d9601ae85f1147eb3ab0cb29e780e5b4af7fd437ee912977b28992ce20b.json) |  | 2026-07-08 | 27KB | `55ad75b9` |
| [graphify-out/cache/ast/v0.9.8/def9ae6b4f5bd89995f031a99e51b6b38f966624bde799ed87d0df04320205f5.json](graphify-out/cache/ast/v0.9.8/def9ae6b4f5bd89995f031a99e51b6b38f966624bde799ed87d0df04320205f5.json) |  | 2026-07-08 | 19KB | `78e95c8f` |
| [graphify-out/cache/ast/v0.9.8/defa5dd58d995e18aa2ee7bffd3bdca593d4c453b86226dea8477e13e96ca906.json](graphify-out/cache/ast/v0.9.8/defa5dd58d995e18aa2ee7bffd3bdca593d4c453b86226dea8477e13e96ca906.json) |  | 2026-07-08 | 8KB | `787014ba` |
| [graphify-out/cache/ast/v0.9.8/df705335cae4c8b4f00d856f7bd31b88cb01b127fdf3a9e79f602a753c763226.json](graphify-out/cache/ast/v0.9.8/df705335cae4c8b4f00d856f7bd31b88cb01b127fdf3a9e79f602a753c763226.json) |  | 2026-07-07 | 14KB | `0be60527` |
| [graphify-out/cache/ast/v0.9.8/df726ad9ade81a487a9b5b6b16e9e4302b12c8dcb0d173799bcc32600a4815e5.json](graphify-out/cache/ast/v0.9.8/df726ad9ade81a487a9b5b6b16e9e4302b12c8dcb0d173799bcc32600a4815e5.json) |  | 2026-07-08 | 6KB | `e6af49d3` |
| [graphify-out/cache/ast/v0.9.8/dfacd77458134c8c7d00529c358abb86db3b6eb5baa6edd9b7fa432c9f20e650.json](graphify-out/cache/ast/v0.9.8/dfacd77458134c8c7d00529c358abb86db3b6eb5baa6edd9b7fa432c9f20e650.json) |  | 2026-07-08 | 6KB | `84402edc` |
| [graphify-out/cache/ast/v0.9.8/dfada9efc7d5f2eda5389d2eeccb1f97d8e190c490090308ae311844336db000.json](graphify-out/cache/ast/v0.9.8/dfada9efc7d5f2eda5389d2eeccb1f97d8e190c490090308ae311844336db000.json) |  | 2026-07-08 | 4KB | `8604105a` |
| [graphify-out/cache/ast/v0.9.8/dfe2ce5761497a1183793c0b53f077d4614156d4c762b4f15cd6d10cb3aa2e36.json](graphify-out/cache/ast/v0.9.8/dfe2ce5761497a1183793c0b53f077d4614156d4c762b4f15cd6d10cb3aa2e36.json) |  | 2026-07-08 | 24KB | `489750a7` |
| [graphify-out/cache/ast/v0.9.8/e0460ffd40c3d9b57e7721db458c0162bf4e1c0e784452c3b8d200ecd2e9cf12.json](graphify-out/cache/ast/v0.9.8/e0460ffd40c3d9b57e7721db458c0162bf4e1c0e784452c3b8d200ecd2e9cf12.json) |  | 2026-07-08 | 38KB | `392eb4a3` |
| [graphify-out/cache/ast/v0.9.8/e06d6844cd1dd383308e875f6cd2cb2c27dec7c416e5e81e133421a995dac802.json](graphify-out/cache/ast/v0.9.8/e06d6844cd1dd383308e875f6cd2cb2c27dec7c416e5e81e133421a995dac802.json) |  | 2026-07-27 | 3KB | `ae139e6d` |
| [graphify-out/cache/ast/v0.9.8/e08d45629426a0ed329267cf0eaf6322b09526fd3ea77605badc0ccd6a318921.json](graphify-out/cache/ast/v0.9.8/e08d45629426a0ed329267cf0eaf6322b09526fd3ea77605badc0ccd6a318921.json) |  | 2026-07-07 | 1KB | `a5b609ef` |
| [graphify-out/cache/ast/v0.9.8/e0a9c15b4dc349c1b6f6cfe99f610332d2ffb2045c4a54441146bb860c98cf9d.json](graphify-out/cache/ast/v0.9.8/e0a9c15b4dc349c1b6f6cfe99f610332d2ffb2045c4a54441146bb860c98cf9d.json) |  | 2026-07-10 | 4KB | `2fd6d09c` |
| [graphify-out/cache/ast/v0.9.8/e0c9e0d56155f80e586bc7ef04876642f8025fd15ae69b545fac196e87e4db38.json](graphify-out/cache/ast/v0.9.8/e0c9e0d56155f80e586bc7ef04876642f8025fd15ae69b545fac196e87e4db38.json) |  | 2026-07-07 | 3KB | `6cd2e51c` |
| [graphify-out/cache/ast/v0.9.8/e0cd4f6d719d1709bb7344ebe0a5b9a43af5b36f1d8fd5ceb9e635743715e1b5.json](graphify-out/cache/ast/v0.9.8/e0cd4f6d719d1709bb7344ebe0a5b9a43af5b36f1d8fd5ceb9e635743715e1b5.json) |  | 2026-07-08 | 7KB | `6853408d` |
| [graphify-out/cache/ast/v0.9.8/e0e97ce0eda660427e77d322bc48d8d02c0f708dc9300050f13951e2babe2c5a.json](graphify-out/cache/ast/v0.9.8/e0e97ce0eda660427e77d322bc48d8d02c0f708dc9300050f13951e2babe2c5a.json) |  | 2026-07-08 | 26KB | `c8cb44bb` |
| [graphify-out/cache/ast/v0.9.8/e124a2a7512d3bcf2953993fc5146ec830b958a77f3c6bd9bdd8c7e3a323ab2d.json](graphify-out/cache/ast/v0.9.8/e124a2a7512d3bcf2953993fc5146ec830b958a77f3c6bd9bdd8c7e3a323ab2d.json) |  | 2026-07-08 | 5KB | `4c22f156` |
| [graphify-out/cache/ast/v0.9.8/e155214aa15040b0ed4d5779b29b55570cf9fb4bb2b935f1ddabc6cb86edc0ba.json](graphify-out/cache/ast/v0.9.8/e155214aa15040b0ed4d5779b29b55570cf9fb4bb2b935f1ddabc6cb86edc0ba.json) |  | 2026-07-08 | 38KB | `8bfa8bcd` |
| [graphify-out/cache/ast/v0.9.8/e18a11c6a26bfb612910581ab9887499dd3d423ba4191ebe01553f838f21f78b.json](graphify-out/cache/ast/v0.9.8/e18a11c6a26bfb612910581ab9887499dd3d423ba4191ebe01553f838f21f78b.json) |  | 2026-07-08 | 62KB | `0eb9d0c2` |
| [graphify-out/cache/ast/v0.9.8/e19ea4253f4b4ce08ae32511eb791d3961775a85e3bbf13937dd7e6bcf122729.json](graphify-out/cache/ast/v0.9.8/e19ea4253f4b4ce08ae32511eb791d3961775a85e3bbf13937dd7e6bcf122729.json) |  | 2026-07-07 | 11KB | `4ac431bb` |
| [graphify-out/cache/ast/v0.9.8/e2001f312eea7746af959f99fc5e8e46e8860a6e72846eeada14accc251592a3.json](graphify-out/cache/ast/v0.9.8/e2001f312eea7746af959f99fc5e8e46e8860a6e72846eeada14accc251592a3.json) |  | 2026-07-08 | 8KB | `74e551fc` |
| [graphify-out/cache/ast/v0.9.8/e22d17a9f78d6c9e756ac1720e6f6e1f2b0434648fcf8cace8357a78a832482b.json](graphify-out/cache/ast/v0.9.8/e22d17a9f78d6c9e756ac1720e6f6e1f2b0434648fcf8cace8357a78a832482b.json) |  | 2026-07-08 | 11KB | `1b20368c` |
| [graphify-out/cache/ast/v0.9.8/e23c017e4d61561f8051a9a077e8faf33a779833f4fee2966682c712577867a7.json](graphify-out/cache/ast/v0.9.8/e23c017e4d61561f8051a9a077e8faf33a779833f4fee2966682c712577867a7.json) |  | 2026-07-08 | 128KB | `856745f1` |
| [graphify-out/cache/ast/v0.9.8/e2e575f9220f300abc51c230bd2ad2971697dfe35a3a0a05f4405eee144452f0.json](graphify-out/cache/ast/v0.9.8/e2e575f9220f300abc51c230bd2ad2971697dfe35a3a0a05f4405eee144452f0.json) |  | 2026-07-31 | 8KB | `f91e7e02` |
| [graphify-out/cache/ast/v0.9.8/e3235f17922851e4f2c963f83a26101b9a764990bafc31e23c4aad1de53c62e1.json](graphify-out/cache/ast/v0.9.8/e3235f17922851e4f2c963f83a26101b9a764990bafc31e23c4aad1de53c62e1.json) |  | 2026-07-08 | 16KB | `c11839b1` |
| [graphify-out/cache/ast/v0.9.8/e329da8903930c9c56ebcf25db90bc203c0ae96e63d465ae06c99ccb0df1ecaf.json](graphify-out/cache/ast/v0.9.8/e329da8903930c9c56ebcf25db90bc203c0ae96e63d465ae06c99ccb0df1ecaf.json) |  | 2026-07-08 | 30KB | `28fefff7` |
| [graphify-out/cache/ast/v0.9.8/e334a0045a1532914d6943c6f29a376c07f42bdb6dcaacf9a1cb24af824e290a.json](graphify-out/cache/ast/v0.9.8/e334a0045a1532914d6943c6f29a376c07f42bdb6dcaacf9a1cb24af824e290a.json) |  | 2026-07-08 | 13KB | `2dfd3dc1` |
| [graphify-out/cache/ast/v0.9.8/e370f88db659865ffd3c98b222f12561537b19db79db8450219d5f4e3297a446.json](graphify-out/cache/ast/v0.9.8/e370f88db659865ffd3c98b222f12561537b19db79db8450219d5f4e3297a446.json) |  | 2026-07-07 | 18KB | `b7c0c74f` |
| [graphify-out/cache/ast/v0.9.8/e3c10eec267a842de4d0fa780d24572be5d446420362a73930364bcd50b760c3.json](graphify-out/cache/ast/v0.9.8/e3c10eec267a842de4d0fa780d24572be5d446420362a73930364bcd50b760c3.json) |  | 2026-07-08 | 12KB | `c0662b2e` |
| [graphify-out/cache/ast/v0.9.8/e423b0d6e831d1ff0a5dffa530fbaa203dc9bf4a593257c51e82966a38f841c1.json](graphify-out/cache/ast/v0.9.8/e423b0d6e831d1ff0a5dffa530fbaa203dc9bf4a593257c51e82966a38f841c1.json) |  | 2026-07-08 | 49KB | `e38e14df` |
| [graphify-out/cache/ast/v0.9.8/e49cf0ebf98559423ac2386b6007e45fe5de39e2841de076fd403b27ca279514.json](graphify-out/cache/ast/v0.9.8/e49cf0ebf98559423ac2386b6007e45fe5de39e2841de076fd403b27ca279514.json) |  | 2026-07-08 | 120KB | `66f0b554` |
| [graphify-out/cache/ast/v0.9.8/e4a2604b01fe34db93edb71f91c4ae0b9d05fffa081fb20c57c5be26ac67ec38.json](graphify-out/cache/ast/v0.9.8/e4a2604b01fe34db93edb71f91c4ae0b9d05fffa081fb20c57c5be26ac67ec38.json) |  | 2026-07-08 | 85KB | `cfce45e6` |
| [graphify-out/cache/ast/v0.9.8/e4ba8bc935a3115837857edfca43d46aef4d50c54d6b46e5e1bae8f30d01ac74.json](graphify-out/cache/ast/v0.9.8/e4ba8bc935a3115837857edfca43d46aef4d50c54d6b46e5e1bae8f30d01ac74.json) |  | 2026-07-27 | 12KB | `3dae843a` |
| [graphify-out/cache/ast/v0.9.8/e517a2d19f24272cf5ed8220f16b3eed298cb3f3829f64a845f479b4b3ef3079.json](graphify-out/cache/ast/v0.9.8/e517a2d19f24272cf5ed8220f16b3eed298cb3f3829f64a845f479b4b3ef3079.json) |  | 2026-07-08 | 13KB | `14813f3d` |
| [graphify-out/cache/ast/v0.9.8/e547758831a58739412bdd6f160e72c057dc0bb404be7c522e466b299f10ef4f.json](graphify-out/cache/ast/v0.9.8/e547758831a58739412bdd6f160e72c057dc0bb404be7c522e466b299f10ef4f.json) |  | 2026-07-07 | 13KB | `e065e932` |
| [graphify-out/cache/ast/v0.9.8/e54d4a4ee4dd584f7565c569ef9883dffb0e1417bd405de382ad16513ab905ae.json](graphify-out/cache/ast/v0.9.8/e54d4a4ee4dd584f7565c569ef9883dffb0e1417bd405de382ad16513ab905ae.json) |  | 2026-07-08 | 7KB | `be50880a` |
| [graphify-out/cache/ast/v0.9.8/e59707f957c26d47b605d1a0fba69b2cc7175791c696ffad2bf38a6a11f1e933.json](graphify-out/cache/ast/v0.9.8/e59707f957c26d47b605d1a0fba69b2cc7175791c696ffad2bf38a6a11f1e933.json) |  | 2026-07-22 | 8KB | `724ede04` |
| [graphify-out/cache/ast/v0.9.8/e5f3888a98098aface21b445edd038b9c62737910799c51af8f8bb33c5518ab1.json](graphify-out/cache/ast/v0.9.8/e5f3888a98098aface21b445edd038b9c62737910799c51af8f8bb33c5518ab1.json) |  | 2026-07-08 | 70KB | `7a403ab6` |
| [graphify-out/cache/ast/v0.9.8/e5fb9598c8733bb5bc5ea4fbeea435903e743f6044ffec182b561deafe41095a.json](graphify-out/cache/ast/v0.9.8/e5fb9598c8733bb5bc5ea4fbeea435903e743f6044ffec182b561deafe41095a.json) |  | 2026-07-08 | 5KB | `444731db` |
| [graphify-out/cache/ast/v0.9.8/e61cbf01aeb5b6fb6e7270686525f352a53d4820335fee72429954109ad51cd4.json](graphify-out/cache/ast/v0.9.8/e61cbf01aeb5b6fb6e7270686525f352a53d4820335fee72429954109ad51cd4.json) |  | 2026-07-08 | 4KB | `f4ce9cfc` |
| [graphify-out/cache/ast/v0.9.8/e652fede0dedb6bd293b752dbc6624a62d566abece97f161973c5b99e4b805a5.json](graphify-out/cache/ast/v0.9.8/e652fede0dedb6bd293b752dbc6624a62d566abece97f161973c5b99e4b805a5.json) |  | 2026-07-08 | 8KB | `90efb966` |
| [graphify-out/cache/ast/v0.9.8/e6633b165de4949a29345179bbe2219b976f801ed2636747deaf7c67e8e189b3.json](graphify-out/cache/ast/v0.9.8/e6633b165de4949a29345179bbe2219b976f801ed2636747deaf7c67e8e189b3.json) |  | 2026-07-08 | 32KB | `f5859099` |
| [graphify-out/cache/ast/v0.9.8/e6741b7059b2986dfca29b73833bcb69af53dd25db3d98cf2b724829cfd22d73.json](graphify-out/cache/ast/v0.9.8/e6741b7059b2986dfca29b73833bcb69af53dd25db3d98cf2b724829cfd22d73.json) |  | 2026-07-08 | 36KB | `3590e541` |
| [graphify-out/cache/ast/v0.9.8/e677a054aa07da8619eb2909469ce9290bf4e7663ddda00443beeb8d637f79bb.json](graphify-out/cache/ast/v0.9.8/e677a054aa07da8619eb2909469ce9290bf4e7663ddda00443beeb8d637f79bb.json) |  | 2026-07-08 | 12KB | `9c4a049f` |
| [graphify-out/cache/ast/v0.9.8/e68057c586a972c74c3c04ecdcb7e9289faf00eb60c67b86715815decdccac17.json](graphify-out/cache/ast/v0.9.8/e68057c586a972c74c3c04ecdcb7e9289faf00eb60c67b86715815decdccac17.json) |  | 2026-07-08 | 38KB | `0a163a91` |
| [graphify-out/cache/ast/v0.9.8/e6bf3b340e83fdfccf9e61f71a64aea1b1764c2755a8f45be87931c3bbf57dce.json](graphify-out/cache/ast/v0.9.8/e6bf3b340e83fdfccf9e61f71a64aea1b1764c2755a8f45be87931c3bbf57dce.json) |  | 2026-07-31 | 9KB | `044ed4a7` |
| [graphify-out/cache/ast/v0.9.8/e713c51d82f16723f24fae81dfb9a0666d89b69579d711659df53fc58bb2138e.json](graphify-out/cache/ast/v0.9.8/e713c51d82f16723f24fae81dfb9a0666d89b69579d711659df53fc58bb2138e.json) |  | 2026-07-08 | 1KB | `d7781de1` |
| [graphify-out/cache/ast/v0.9.8/e7169140383099d51178ed0d5f98e5e8be4667b3239e3cdd24f031418631d476.json](graphify-out/cache/ast/v0.9.8/e7169140383099d51178ed0d5f98e5e8be4667b3239e3cdd24f031418631d476.json) |  | 2026-07-24 | 23KB | `f957390e` |
| [graphify-out/cache/ast/v0.9.8/e74c1130e72cccc1737348b8bce21c356a8abeba28daa637da38574765093338.json](graphify-out/cache/ast/v0.9.8/e74c1130e72cccc1737348b8bce21c356a8abeba28daa637da38574765093338.json) |  | 2026-07-29 | 13KB | `dd464593` |
| [graphify-out/cache/ast/v0.9.8/e79b56599699d9c1fa18e085fdd6996fc999011b952b746e75bd5bc5c0eb7461.json](graphify-out/cache/ast/v0.9.8/e79b56599699d9c1fa18e085fdd6996fc999011b952b746e75bd5bc5c0eb7461.json) |  | 2026-07-08 | 55KB | `2ea8671e` |
| [graphify-out/cache/ast/v0.9.8/e79ef12cfe098c8fd653fdd716d6603f8f56546c5f428eef5604d8ab834e5dfc.json](graphify-out/cache/ast/v0.9.8/e79ef12cfe098c8fd653fdd716d6603f8f56546c5f428eef5604d8ab834e5dfc.json) |  | 2026-07-31 | 3KB | `00c5cdd2` |
| [graphify-out/cache/ast/v0.9.8/e7ab2f0a806664a3ba9e7bc2eb1060e94b7911067289868bf99430dc5c2f78e0.json](graphify-out/cache/ast/v0.9.8/e7ab2f0a806664a3ba9e7bc2eb1060e94b7911067289868bf99430dc5c2f78e0.json) |  | 2026-07-27 | 31KB | `1a965a7a` |
| [graphify-out/cache/ast/v0.9.8/e7b0430bd535735d1ac45c010658f52e9fd3c6d67e16c4d5a961123891444055.json](graphify-out/cache/ast/v0.9.8/e7b0430bd535735d1ac45c010658f52e9fd3c6d67e16c4d5a961123891444055.json) |  | 2026-07-08 | 21KB | `9f0eb25b` |
| [graphify-out/cache/ast/v0.9.8/e7d96263fc36c8aa9c8f21ee7f2d2a6c75d4fe25f31ecced87dd8e6d5e069f0d.json](graphify-out/cache/ast/v0.9.8/e7d96263fc36c8aa9c8f21ee7f2d2a6c75d4fe25f31ecced87dd8e6d5e069f0d.json) |  | 2026-07-07 | 10KB | `7df29ef4` |
| [graphify-out/cache/ast/v0.9.8/e8149c4e2782362c3173a38c09ccd7c8f81fd6f212cb8bccb588998f9284e714.json](graphify-out/cache/ast/v0.9.8/e8149c4e2782362c3173a38c09ccd7c8f81fd6f212cb8bccb588998f9284e714.json) |  | 2026-07-08 | 15KB | `a5a270de` |
| [graphify-out/cache/ast/v0.9.8/e8714f3cedd34d12b56aa1cf98e9bee9ccf9bb3653367b2c648997df46f313af.json](graphify-out/cache/ast/v0.9.8/e8714f3cedd34d12b56aa1cf98e9bee9ccf9bb3653367b2c648997df46f313af.json) |  | 2026-07-07 | 20KB | `88b03048` |
| [graphify-out/cache/ast/v0.9.8/e89f8760b2fe2bc0fa18b1c20c3c5178de15cb63d603087e3d4ac066bbf0b1e6.json](graphify-out/cache/ast/v0.9.8/e89f8760b2fe2bc0fa18b1c20c3c5178de15cb63d603087e3d4ac066bbf0b1e6.json) |  | 2026-07-07 | 97KB | `a49f8e84` |
| [graphify-out/cache/ast/v0.9.8/e8a8c3d7f18facd884f1ff4450017a0982f5dfafe7c9f8f642cd1985e55dee1c.json](graphify-out/cache/ast/v0.9.8/e8a8c3d7f18facd884f1ff4450017a0982f5dfafe7c9f8f642cd1985e55dee1c.json) |  | 2026-07-31 | 22KB | `ff41f0da` |
| [graphify-out/cache/ast/v0.9.8/e8e0b9188cf96cbd24e790d7fc9d38f99e590ca80a773194c5d7d398544ea958.json](graphify-out/cache/ast/v0.9.8/e8e0b9188cf96cbd24e790d7fc9d38f99e590ca80a773194c5d7d398544ea958.json) |  | 2026-07-07 | 13KB | `ac1a9c8a` |
| [graphify-out/cache/ast/v0.9.8/e936b54a412d8e9c0286d8e2cf61e3dd5f5783b742edf36eedcf976d5a3080c2.json](graphify-out/cache/ast/v0.9.8/e936b54a412d8e9c0286d8e2cf61e3dd5f5783b742edf36eedcf976d5a3080c2.json) |  | 2026-07-08 | 45KB | `a5489ede` |
| [graphify-out/cache/ast/v0.9.8/e94d5d7cf1eb2a9143189ce43211ec2ff9693af544df8a3ee2dcef2e304ee498.json](graphify-out/cache/ast/v0.9.8/e94d5d7cf1eb2a9143189ce43211ec2ff9693af544df8a3ee2dcef2e304ee498.json) |  | 2026-07-07 | 19KB | `9cca6de7` |
| [graphify-out/cache/ast/v0.9.8/e9857cb3be82f8126555e77b7e081f63c682d782306e23f61a25849efaf9acb1.json](graphify-out/cache/ast/v0.9.8/e9857cb3be82f8126555e77b7e081f63c682d782306e23f61a25849efaf9acb1.json) |  | 2026-07-08 | 2KB | `a5fdfa56` |
| [graphify-out/cache/ast/v0.9.8/e9b71808f0b19b5a0afc730479d014fb6fe084ff631288274bfc411bd2a529f6.json](graphify-out/cache/ast/v0.9.8/e9b71808f0b19b5a0afc730479d014fb6fe084ff631288274bfc411bd2a529f6.json) |  | 2026-07-08 | 5KB | `787f1090` |
| [graphify-out/cache/ast/v0.9.8/e9c7e7efd5123dfb77dafb69ad1d75a1ed236cf5e092b3f55c42c7fab09e759f.json](graphify-out/cache/ast/v0.9.8/e9c7e7efd5123dfb77dafb69ad1d75a1ed236cf5e092b3f55c42c7fab09e759f.json) |  | 2026-07-08 | 13KB | `c96eb7ce` |
| [graphify-out/cache/ast/v0.9.8/e9e7f0c45821233971895371fd7c7f63cf5851329ecb8e7640f9e3736939c6c4.json](graphify-out/cache/ast/v0.9.8/e9e7f0c45821233971895371fd7c7f63cf5851329ecb8e7640f9e3736939c6c4.json) |  | 2026-07-07 | 18KB | `fbe5d67d` |
| [graphify-out/cache/ast/v0.9.8/ea07f2f163d3405507f072a04d10adfa8c149f015a1122abfd4d9388498d8263.json](graphify-out/cache/ast/v0.9.8/ea07f2f163d3405507f072a04d10adfa8c149f015a1122abfd4d9388498d8263.json) |  | 2026-07-08 | 3KB | `cc1d1250` |
| [graphify-out/cache/ast/v0.9.8/ea0ef3612d7481bf2119ed17bd429538e878ec09b0d50f5d4c4a3c4852cb4d72.json](graphify-out/cache/ast/v0.9.8/ea0ef3612d7481bf2119ed17bd429538e878ec09b0d50f5d4c4a3c4852cb4d72.json) |  | 2026-07-27 | 135KB | `4b98ef9c` |
| [graphify-out/cache/ast/v0.9.8/ea3985d54e60995524c40f11ac2db0b088c08a1a64295dbd270a9b50c2d07abc.json](graphify-out/cache/ast/v0.9.8/ea3985d54e60995524c40f11ac2db0b088c08a1a64295dbd270a9b50c2d07abc.json) |  | 2026-07-08 | 108KB | `dd8f338e` |
| [graphify-out/cache/ast/v0.9.8/ea4a9f5930d10c330e62948b8001690bd8a3b39d7442c63790386419da322779.json](graphify-out/cache/ast/v0.9.8/ea4a9f5930d10c330e62948b8001690bd8a3b39d7442c63790386419da322779.json) |  | 2026-07-29 | 7KB | `d09b1dc6` |
| [graphify-out/cache/ast/v0.9.8/ea59e2d3d463e17fd8db346e1f24a73be19b086d47e6bf365aa13baff0f624a5.json](graphify-out/cache/ast/v0.9.8/ea59e2d3d463e17fd8db346e1f24a73be19b086d47e6bf365aa13baff0f624a5.json) |  | 2026-07-08 | 10KB | `9ae160dd` |
| [graphify-out/cache/ast/v0.9.8/ea716e5082a551d5c8fe23201c28c7b2fe21d2291ff4170a299a23b7f0ea2c8a.json](graphify-out/cache/ast/v0.9.8/ea716e5082a551d5c8fe23201c28c7b2fe21d2291ff4170a299a23b7f0ea2c8a.json) |  | 2026-07-08 | 9KB | `15228566` |
| [graphify-out/cache/ast/v0.9.8/eaefab7a894c95bd29aa9315a758d85b358620ceb3a1c4d1f92ef206022f4779.json](graphify-out/cache/ast/v0.9.8/eaefab7a894c95bd29aa9315a758d85b358620ceb3a1c4d1f92ef206022f4779.json) |  | 2026-07-07 | 14KB | `d9991119` |
| [graphify-out/cache/ast/v0.9.8/eb1c38413fd7d81cf4edfe09bcdf5cc5464e4818176ca508a8bcb00da0ad76e9.json](graphify-out/cache/ast/v0.9.8/eb1c38413fd7d81cf4edfe09bcdf5cc5464e4818176ca508a8bcb00da0ad76e9.json) |  | 2026-07-08 | 8KB | `6d78cbb0` |
| [graphify-out/cache/ast/v0.9.8/eb82742619edb84536eb2d8f7796a2306a14a9698a13d3a1b601966393aede1a.json](graphify-out/cache/ast/v0.9.8/eb82742619edb84536eb2d8f7796a2306a14a9698a13d3a1b601966393aede1a.json) |  | 2026-07-07 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/eb8da9af2fd1409473d975dbbffc429f260c029de91450d6f133c3e43a452b8a.json](graphify-out/cache/ast/v0.9.8/eb8da9af2fd1409473d975dbbffc429f260c029de91450d6f133c3e43a452b8a.json) |  | 2026-07-08 | 6KB | `3d0f5ad7` |
| [graphify-out/cache/ast/v0.9.8/eb9afd2cc02c2ddcb7ed3654056bb2878a3ec7a2111fbe2f70d42976af14fd83.json](graphify-out/cache/ast/v0.9.8/eb9afd2cc02c2ddcb7ed3654056bb2878a3ec7a2111fbe2f70d42976af14fd83.json) |  | 2026-07-08 | 8KB | `d9441307` |
| [graphify-out/cache/ast/v0.9.8/eba24ba840078feeefe019b5d86efbdbb8c0480d38f7ce75c93f29912c74b9d6.json](graphify-out/cache/ast/v0.9.8/eba24ba840078feeefe019b5d86efbdbb8c0480d38f7ce75c93f29912c74b9d6.json) |  | 2026-07-30 | 13KB | `3316dabd` |
| [graphify-out/cache/ast/v0.9.8/ebec9554d3f122cd91486dd6ee9d5b3792d72085503ff9e7e7636bf9d8c4763e.json](graphify-out/cache/ast/v0.9.8/ebec9554d3f122cd91486dd6ee9d5b3792d72085503ff9e7e7636bf9d8c4763e.json) |  | 2026-07-08 | 19KB | `a0c1a653` |
| [graphify-out/cache/ast/v0.9.8/ed1596a29c93ef5f8c76785e0fbf56aa4adc08acdd4e897365c1b6a6d9d270a7.json](graphify-out/cache/ast/v0.9.8/ed1596a29c93ef5f8c76785e0fbf56aa4adc08acdd4e897365c1b6a6d9d270a7.json) |  | 2026-07-10 | 22KB | `e37175ba` |
| [graphify-out/cache/ast/v0.9.8/ed287c78382f5fa8047f2bd49d4b548c63af6b27435e8b0c981ea91c1ed8b0af.json](graphify-out/cache/ast/v0.9.8/ed287c78382f5fa8047f2bd49d4b548c63af6b27435e8b0c981ea91c1ed8b0af.json) |  | 2026-07-08 | 4KB | `c53736eb` |
| [graphify-out/cache/ast/v0.9.8/ed54c06a43b05c931fa9999bb510e355c4d847db5896c8b5ae730a9b9e116b8c.json](graphify-out/cache/ast/v0.9.8/ed54c06a43b05c931fa9999bb510e355c4d847db5896c8b5ae730a9b9e116b8c.json) |  | 2026-07-31 | 9KB | `5647c2dc` |
| [graphify-out/cache/ast/v0.9.8/ed6f1639a65c3d20ebb7035ea1182abf37fa418c65f0764de74779ab324a966a.json](graphify-out/cache/ast/v0.9.8/ed6f1639a65c3d20ebb7035ea1182abf37fa418c65f0764de74779ab324a966a.json) |  | 2026-07-08 | 9KB | `f5b0da0d` |
| [graphify-out/cache/ast/v0.9.8/ed7b3b4e78f500ffec45813d8043dc1529204e584bffe620bda55f2bd6434659.json](graphify-out/cache/ast/v0.9.8/ed7b3b4e78f500ffec45813d8043dc1529204e584bffe620bda55f2bd6434659.json) |  | 2026-07-08 | 4KB | `8e8add55` |
| [graphify-out/cache/ast/v0.9.8/edadad53b1999148660638468768e8549ff01fdb81fcce1dfa9ba1a7e3543b43.json](graphify-out/cache/ast/v0.9.8/edadad53b1999148660638468768e8549ff01fdb81fcce1dfa9ba1a7e3543b43.json) |  | 2026-07-08 | 19KB | `c8fa66f0` |
| [graphify-out/cache/ast/v0.9.8/edb2005f33cdb4c2fb64ba074ee1217fd2b65d1fa85e0d4d806b4ae2d378ea29.json](graphify-out/cache/ast/v0.9.8/edb2005f33cdb4c2fb64ba074ee1217fd2b65d1fa85e0d4d806b4ae2d378ea29.json) |  | 2026-07-08 | 44KB | `85fdf15d` |
| [graphify-out/cache/ast/v0.9.8/ee300e9631c3cb7cdae200e31919529495a09f87ae09309ff50dd0b2335ccef9.json](graphify-out/cache/ast/v0.9.8/ee300e9631c3cb7cdae200e31919529495a09f87ae09309ff50dd0b2335ccef9.json) |  | 2026-07-08 | 17KB | `c3a807ef` |
| [graphify-out/cache/ast/v0.9.8/ee66da9f6a26bf3cf949549b0ed774bbb6c273ed6a7bc2099f008a749d346198.json](graphify-out/cache/ast/v0.9.8/ee66da9f6a26bf3cf949549b0ed774bbb6c273ed6a7bc2099f008a749d346198.json) |  | 2026-07-27 | 9KB | `f015fb73` |
| [graphify-out/cache/ast/v0.9.8/ee7a4d2be4f6018b6819a8d0c7311265f1813a20cb6919886ea75b2b57eae355.json](graphify-out/cache/ast/v0.9.8/ee7a4d2be4f6018b6819a8d0c7311265f1813a20cb6919886ea75b2b57eae355.json) |  | 2026-07-08 | 6KB | `54a1f0f5` |
| [graphify-out/cache/ast/v0.9.8/eeb27b936fee65178a3e7ad18a56240f49d5193116f1e58f7f82038fbe19c670.json](graphify-out/cache/ast/v0.9.8/eeb27b936fee65178a3e7ad18a56240f49d5193116f1e58f7f82038fbe19c670.json) |  | 2026-07-08 | 18KB | `532d3350` |
| [graphify-out/cache/ast/v0.9.8/eebd8b17a1528bebeb50bf75a322069027f4fa9d87308233f4b88950ceb77ae4.json](graphify-out/cache/ast/v0.9.8/eebd8b17a1528bebeb50bf75a322069027f4fa9d87308233f4b88950ceb77ae4.json) |  | 2026-07-08 | 7KB | `44cd1237` |
| [graphify-out/cache/ast/v0.9.8/eecc26a49479b706c83a965e9179455762c14b279effa86b84b4a3492d126231.json](graphify-out/cache/ast/v0.9.8/eecc26a49479b706c83a965e9179455762c14b279effa86b84b4a3492d126231.json) |  | 2026-07-08 | 59KB | `202d11f4` |
| [graphify-out/cache/ast/v0.9.8/eed88e335edc437f20dfed65986a4023bcd35544b7eb5aec2179386dc63120b8.json](graphify-out/cache/ast/v0.9.8/eed88e335edc437f20dfed65986a4023bcd35544b7eb5aec2179386dc63120b8.json) |  | 2026-07-07 | 17KB | `1bf0c20f` |
| [graphify-out/cache/ast/v0.9.8/ef128382f31ccfac0ed73dde0003be282863cbd3a23b432b034c569a80a3970a.json](graphify-out/cache/ast/v0.9.8/ef128382f31ccfac0ed73dde0003be282863cbd3a23b432b034c569a80a3970a.json) |  | 2026-07-24 | 13KB | `e402d0e7` |
| [graphify-out/cache/ast/v0.9.8/ef1a8a0d330520d0b27a72263e557b9252d72f981e2766a00f946a0dedc13548.json](graphify-out/cache/ast/v0.9.8/ef1a8a0d330520d0b27a72263e557b9252d72f981e2766a00f946a0dedc13548.json) |  | 2026-07-08 | 12KB | `6eff30b9` |
| [graphify-out/cache/ast/v0.9.8/ef3d821f05430094ff3dc53acfaa299ba002cccfe07168bf1377b6091f96a5c7.json](graphify-out/cache/ast/v0.9.8/ef3d821f05430094ff3dc53acfaa299ba002cccfe07168bf1377b6091f96a5c7.json) |  | 2026-07-08 | 6KB | `c7d36383` |
| [graphify-out/cache/ast/v0.9.8/ef5e51443530e94c966cc48288ad33926aaa7884da511e39428f85af1a870ede.json](graphify-out/cache/ast/v0.9.8/ef5e51443530e94c966cc48288ad33926aaa7884da511e39428f85af1a870ede.json) |  | 2026-07-08 | 3KB | `e00340b0` |
| [graphify-out/cache/ast/v0.9.8/ef77100490f6dd423aa5739fa0e2cd62d64e2652f6641d37492edb1e650a00ba.json](graphify-out/cache/ast/v0.9.8/ef77100490f6dd423aa5739fa0e2cd62d64e2652f6641d37492edb1e650a00ba.json) |  | 2026-07-08 | 10KB | `bd6bd5e8` |
| [graphify-out/cache/ast/v0.9.8/ef7f7171b5b71e8c1eaa24512e890071d0590210e2c2a58a2b4d2084df4236e1.json](graphify-out/cache/ast/v0.9.8/ef7f7171b5b71e8c1eaa24512e890071d0590210e2c2a58a2b4d2084df4236e1.json) |  | 2026-07-08 | 12KB | `123ca244` |
| [graphify-out/cache/ast/v0.9.8/ef9da43571de2e52a9a39c62085628352f0d133c1e76b33c14b7b0c827e7e101.json](graphify-out/cache/ast/v0.9.8/ef9da43571de2e52a9a39c62085628352f0d133c1e76b33c14b7b0c827e7e101.json) |  | 2026-07-08 | 7KB | `6dc2fe99` |
| [graphify-out/cache/ast/v0.9.8/efc9d440ed97ed0410946ba8d57540bf7c97dfce02eae7f585c68a705cb3c741.json](graphify-out/cache/ast/v0.9.8/efc9d440ed97ed0410946ba8d57540bf7c97dfce02eae7f585c68a705cb3c741.json) |  | 2026-07-07 | 17KB | `21be742c` |
| [graphify-out/cache/ast/v0.9.8/efccbf25b4bc6f0aadccba411de99e877d4fa89d4da7f1392a387c34de30051c.json](graphify-out/cache/ast/v0.9.8/efccbf25b4bc6f0aadccba411de99e877d4fa89d4da7f1392a387c34de30051c.json) |  | 2026-07-08 | 26KB | `2875427b` |
| [graphify-out/cache/ast/v0.9.8/effc64f78dbf4b228cfa1588ea191fd16c02f958bdfc19bd2bd58e90dfb3197f.json](graphify-out/cache/ast/v0.9.8/effc64f78dbf4b228cfa1588ea191fd16c02f958bdfc19bd2bd58e90dfb3197f.json) |  | 2026-07-08 | 15KB | `3260198d` |
| [graphify-out/cache/ast/v0.9.8/f000c89ef2ebc9438cd36a0cad78847bf4c8edd59612a14966bbace1f63de647.json](graphify-out/cache/ast/v0.9.8/f000c89ef2ebc9438cd36a0cad78847bf4c8edd59612a14966bbace1f63de647.json) |  | 2026-07-08 | 18KB | `aeccad0d` |
| [graphify-out/cache/ast/v0.9.8/f0503202b9242d2a2e44505ab3ea6a6b5ce4522a385a3fc1fccd7fe7ffa1214b.json](graphify-out/cache/ast/v0.9.8/f0503202b9242d2a2e44505ab3ea6a6b5ce4522a385a3fc1fccd7fe7ffa1214b.json) |  | 2026-07-08 | 2KB | `85159268` |
| [graphify-out/cache/ast/v0.9.8/f0744dd148ae8f7df78fd656d36f80ee29dfbcd639dd807f6040739e431963ff.json](graphify-out/cache/ast/v0.9.8/f0744dd148ae8f7df78fd656d36f80ee29dfbcd639dd807f6040739e431963ff.json) |  | 2026-07-08 | 19KB | `66774938` |
| [graphify-out/cache/ast/v0.9.8/f0af98641a7966b7c82d97fc45efe57398a458059849dcf010d0316c8740f231.json](graphify-out/cache/ast/v0.9.8/f0af98641a7966b7c82d97fc45efe57398a458059849dcf010d0316c8740f231.json) |  | 2026-07-08 | 15KB | `845e3276` |
| [graphify-out/cache/ast/v0.9.8/f0d2d25b3d9c60661da910870cfcdd5d5962d305fb629e152fb37e497466a553.json](graphify-out/cache/ast/v0.9.8/f0d2d25b3d9c60661da910870cfcdd5d5962d305fb629e152fb37e497466a553.json) |  | 2026-07-08 | 18KB | `5b6c426a` |
| [graphify-out/cache/ast/v0.9.8/f0d58f48389ed161c25e8ac199c9dc407b2ca0ce498cf9f6f6e7be39b74f6ec6.json](graphify-out/cache/ast/v0.9.8/f0d58f48389ed161c25e8ac199c9dc407b2ca0ce498cf9f6f6e7be39b74f6ec6.json) |  | 2026-07-08 | 34KB | `dae057c1` |
| [graphify-out/cache/ast/v0.9.8/f14b1c7faba6cc0f38c13c66d7e643efc8df2bd0ae75c27d0241bd52211e9955.json](graphify-out/cache/ast/v0.9.8/f14b1c7faba6cc0f38c13c66d7e643efc8df2bd0ae75c27d0241bd52211e9955.json) |  | 2026-07-08 | 66KB | `bc8dc07e` |
| [graphify-out/cache/ast/v0.9.8/f162543aecafd43db720ce7d7e53e584f77c8e4596507ab5d095c5b24e19f663.json](graphify-out/cache/ast/v0.9.8/f162543aecafd43db720ce7d7e53e584f77c8e4596507ab5d095c5b24e19f663.json) |  | 2026-07-08 | 43KB | `7c05fe38` |
| [graphify-out/cache/ast/v0.9.8/f180ad8728230b405cb081f723ced12676161d67b843df2a7c52b18cfce3e416.json](graphify-out/cache/ast/v0.9.8/f180ad8728230b405cb081f723ced12676161d67b843df2a7c52b18cfce3e416.json) |  | 2026-07-24 | 12KB | `8eceb6d4` |
| [graphify-out/cache/ast/v0.9.8/f1cb339e02a483367c6c1d7034d2d26fdf95132f860bcc17a97a579ebbc6a01d.json](graphify-out/cache/ast/v0.9.8/f1cb339e02a483367c6c1d7034d2d26fdf95132f860bcc17a97a579ebbc6a01d.json) |  | 2026-07-08 | 8KB | `acd454a4` |
| [graphify-out/cache/ast/v0.9.8/f21bde304aac10c612c1ce0ba1f3f7caeee2467c5bc4213919e60741ef640ca1.json](graphify-out/cache/ast/v0.9.8/f21bde304aac10c612c1ce0ba1f3f7caeee2467c5bc4213919e60741ef640ca1.json) |  | 2026-07-08 | 4KB | `1f2dd1f8` |
| [graphify-out/cache/ast/v0.9.8/f22d6556f968a6a1d6dd9d19c9d3a4bfe9bc70647d3e432af59ce5c873a553d7.json](graphify-out/cache/ast/v0.9.8/f22d6556f968a6a1d6dd9d19c9d3a4bfe9bc70647d3e432af59ce5c873a553d7.json) |  | 2026-07-07 | 247B | `30045dcd` |
| [graphify-out/cache/ast/v0.9.8/f2d96f07c580dff86252cb9300bd3cb5f945ad87b9ed0370683ef8a67cf0c504.json](graphify-out/cache/ast/v0.9.8/f2d96f07c580dff86252cb9300bd3cb5f945ad87b9ed0370683ef8a67cf0c504.json) |  | 2026-07-08 | 10KB | `2074d264` |
| [graphify-out/cache/ast/v0.9.8/f2f408d0de2feb49f1fa8d04bd24cff288aa955e63f0e53fe06d2c570f7da10e.json](graphify-out/cache/ast/v0.9.8/f2f408d0de2feb49f1fa8d04bd24cff288aa955e63f0e53fe06d2c570f7da10e.json) |  | 2026-07-08 | 8KB | `116bfd0c` |
| [graphify-out/cache/ast/v0.9.8/f304a4a5fe86bf60e31b3c7bfbff2b83236d4729429aa2b1eda3168c50e73688.json](graphify-out/cache/ast/v0.9.8/f304a4a5fe86bf60e31b3c7bfbff2b83236d4729429aa2b1eda3168c50e73688.json) |  | 2026-07-29 | 41KB | `c66e3f6d` |
| [graphify-out/cache/ast/v0.9.8/f33009af14accaa3b6488cf7e5018053b03d52e2f7b4b55f2e6b969a8596deb1.json](graphify-out/cache/ast/v0.9.8/f33009af14accaa3b6488cf7e5018053b03d52e2f7b4b55f2e6b969a8596deb1.json) |  | 2026-07-07 | 9KB | `bb328e77` |
| [graphify-out/cache/ast/v0.9.8/f3326a7d01bd1b69f188ceb65d637a876779c2c2953b05a50ffe7868d052712c.json](graphify-out/cache/ast/v0.9.8/f3326a7d01bd1b69f188ceb65d637a876779c2c2953b05a50ffe7868d052712c.json) |  | 2026-07-08 | 20KB | `d3df2959` |
| [graphify-out/cache/ast/v0.9.8/f3a7112d82fd5e950f9f1359a9740f1bb9cf3b557bc6d38a00c90f8526f3fa5b.json](graphify-out/cache/ast/v0.9.8/f3a7112d82fd5e950f9f1359a9740f1bb9cf3b557bc6d38a00c90f8526f3fa5b.json) |  | 2026-07-08 | 22KB | `ced2773f` |
| [graphify-out/cache/ast/v0.9.8/f3acd43cb9086f09706068121398a3737f9d4f4c33262af801b70631128c01a0.json](graphify-out/cache/ast/v0.9.8/f3acd43cb9086f09706068121398a3737f9d4f4c33262af801b70631128c01a0.json) |  | 2026-07-08 | 1KB | `3b28b2ef` |
| [graphify-out/cache/ast/v0.9.8/f3bcbc962e81cc0be4c166ef60097b239dfb6ec9b2a8fd2b16ca77ddc16b6a33.json](graphify-out/cache/ast/v0.9.8/f3bcbc962e81cc0be4c166ef60097b239dfb6ec9b2a8fd2b16ca77ddc16b6a33.json) |  | 2026-07-08 | 2KB | `fa2274ac` |
| [graphify-out/cache/ast/v0.9.8/f3cc5eaeca5e050efafdf3b72b09fe8abdab4f0d662c830586f69f7111a7b55f.json](graphify-out/cache/ast/v0.9.8/f3cc5eaeca5e050efafdf3b72b09fe8abdab4f0d662c830586f69f7111a7b55f.json) |  | 2026-07-07 | 16KB | `a49e5267` |
| [graphify-out/cache/ast/v0.9.8/f3d3611c08f2680b6a86c2c2ea02fa99f8422ca740d07fb1c003eb5a3643fd0d.json](graphify-out/cache/ast/v0.9.8/f3d3611c08f2680b6a86c2c2ea02fa99f8422ca740d07fb1c003eb5a3643fd0d.json) |  | 2026-07-07 | 18KB | `b54469bd` |
| [graphify-out/cache/ast/v0.9.8/f46f5a7ce50bc21127a5b67d354a7232fd030965e7d57695ac0ea4bf21474f2b.json](graphify-out/cache/ast/v0.9.8/f46f5a7ce50bc21127a5b67d354a7232fd030965e7d57695ac0ea4bf21474f2b.json) |  | 2026-07-08 | 4KB | `aa8d2ad2` |
| [graphify-out/cache/ast/v0.9.8/f4a0403027b3e9af912f56253416cc15f67233fa45169ed536cb6f64312e7f8a.json](graphify-out/cache/ast/v0.9.8/f4a0403027b3e9af912f56253416cc15f67233fa45169ed536cb6f64312e7f8a.json) |  | 2026-07-08 | 87KB | `b468d033` |
| [graphify-out/cache/ast/v0.9.8/f4a1728b856753116008e79356447a6fcb73f8b9ccd52db820f39047cb1f7aad.json](graphify-out/cache/ast/v0.9.8/f4a1728b856753116008e79356447a6fcb73f8b9ccd52db820f39047cb1f7aad.json) |  | 2026-07-08 | 9KB | `2258a570` |
| [graphify-out/cache/ast/v0.9.8/f4a73cfe61bae57f5315668e6b0c79b1eecff7c0800a4e730a1bd0e3609bba0d.json](graphify-out/cache/ast/v0.9.8/f4a73cfe61bae57f5315668e6b0c79b1eecff7c0800a4e730a1bd0e3609bba0d.json) |  | 2026-07-07 | 21KB | `1bf2fa9d` |
| [graphify-out/cache/ast/v0.9.8/f4d72959474867140b9775544f455cbcde70ee9d0eb723d731f40436ce6f8335.json](graphify-out/cache/ast/v0.9.8/f4d72959474867140b9775544f455cbcde70ee9d0eb723d731f40436ce6f8335.json) |  | 2026-07-08 | 17KB | `f98e7f62` |
| [graphify-out/cache/ast/v0.9.8/f4fff66661ca240d2cdfc9840b0db4a44f955f2ded08cfcf27f1336bce665002.json](graphify-out/cache/ast/v0.9.8/f4fff66661ca240d2cdfc9840b0db4a44f955f2ded08cfcf27f1336bce665002.json) |  | 2026-07-08 | 4KB | `ac5b783c` |
| [graphify-out/cache/ast/v0.9.8/f52c959429802080e873040c7da8abcbb5db8585f115ecaf0dd1c61fcf7091da.json](graphify-out/cache/ast/v0.9.8/f52c959429802080e873040c7da8abcbb5db8585f115ecaf0dd1c61fcf7091da.json) |  | 2026-07-08 | 7KB | `9ccd7c1a` |
| [graphify-out/cache/ast/v0.9.8/f58a2ad00c638de3ac5f4149f3d910f944d7797f5cc7c7f75363339ec4a12fd7.json](graphify-out/cache/ast/v0.9.8/f58a2ad00c638de3ac5f4149f3d910f944d7797f5cc7c7f75363339ec4a12fd7.json) |  | 2026-07-08 | 11KB | `169593ed` |
| [graphify-out/cache/ast/v0.9.8/f5b9504e91fcfa91f8394ed58c5bd88fc1c8c689f9aca455555344d2e2fe93f1.json](graphify-out/cache/ast/v0.9.8/f5b9504e91fcfa91f8394ed58c5bd88fc1c8c689f9aca455555344d2e2fe93f1.json) |  | 2026-07-07 | 19KB | `b11536a6` |
| [graphify-out/cache/ast/v0.9.8/f5c47dada724f4529d32e9a5192eb5b0b926a33398e4e917a333db31493d2fb1.json](graphify-out/cache/ast/v0.9.8/f5c47dada724f4529d32e9a5192eb5b0b926a33398e4e917a333db31493d2fb1.json) |  | 2026-07-08 | 16KB | `41b7c47e` |
| [graphify-out/cache/ast/v0.9.8/f5d64a3cb5b7a3f9075d33538142540ca532a627fd20cccc3dc056498673e203.json](graphify-out/cache/ast/v0.9.8/f5d64a3cb5b7a3f9075d33538142540ca532a627fd20cccc3dc056498673e203.json) |  | 2026-07-24 | 87KB | `76303f22` |
| [graphify-out/cache/ast/v0.9.8/f603536cf6bd3d3fc8b62f3e06b64fab3b74c4f4cbacacaf06eebe58a04d43bd.json](graphify-out/cache/ast/v0.9.8/f603536cf6bd3d3fc8b62f3e06b64fab3b74c4f4cbacacaf06eebe58a04d43bd.json) |  | 2026-07-08 | 5KB | `b2f8c28c` |
| [graphify-out/cache/ast/v0.9.8/f60d4259d1dba63a77d96b4993ba8584f11d9bebee995a165aa3b94d27ec3a0d.json](graphify-out/cache/ast/v0.9.8/f60d4259d1dba63a77d96b4993ba8584f11d9bebee995a165aa3b94d27ec3a0d.json) |  | 2026-07-22 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/f6864b7578007ac816b86164caa349eba15ceb2353e8d2309476181786366fb3.json](graphify-out/cache/ast/v0.9.8/f6864b7578007ac816b86164caa349eba15ceb2353e8d2309476181786366fb3.json) |  | 2026-07-29 | 6KB | `a42cacfa` |
| [graphify-out/cache/ast/v0.9.8/f6ea77008a1846e3ba130ad387b8ec542b0fbbe387078a34e6642e6f72d95101.json](graphify-out/cache/ast/v0.9.8/f6ea77008a1846e3ba130ad387b8ec542b0fbbe387078a34e6642e6f72d95101.json) |  | 2026-07-07 | 847B | `07702ade` |
| [graphify-out/cache/ast/v0.9.8/f6fe8b800c12c536efc1c2bfb1e049f6caf72cf42d7791e3687f332762d94348.json](graphify-out/cache/ast/v0.9.8/f6fe8b800c12c536efc1c2bfb1e049f6caf72cf42d7791e3687f332762d94348.json) |  | 2026-07-08 | 8KB | `9287a8c2` |
| [graphify-out/cache/ast/v0.9.8/f7809745b98e6eef8cc5a51a9d6379a8663aef99563a6ba315b87b7bec53eb90.json](graphify-out/cache/ast/v0.9.8/f7809745b98e6eef8cc5a51a9d6379a8663aef99563a6ba315b87b7bec53eb90.json) |  | 2026-07-08 | 21KB | `1fffae22` |
| [graphify-out/cache/ast/v0.9.8/f7a29b8d0e8bd82eddcc1c6ff08eec7d4a567894ba65c254aca570c058f8e74b.json](graphify-out/cache/ast/v0.9.8/f7a29b8d0e8bd82eddcc1c6ff08eec7d4a567894ba65c254aca570c058f8e74b.json) |  | 2026-07-08 | 101KB | `90a50292` |
| [graphify-out/cache/ast/v0.9.8/f7b041e54cb1ca7b1afb5073c77d099c36c36bff96cd65562aa1266e33d4b272.json](graphify-out/cache/ast/v0.9.8/f7b041e54cb1ca7b1afb5073c77d099c36c36bff96cd65562aa1266e33d4b272.json) |  | 2026-07-08 | 18KB | `634c6a34` |
| [graphify-out/cache/ast/v0.9.8/f7d9291505896f3eead888570af24b93884f26e0708be718341a2ff4d508f3a0.json](graphify-out/cache/ast/v0.9.8/f7d9291505896f3eead888570af24b93884f26e0708be718341a2ff4d508f3a0.json) |  | 2026-07-07 | 43KB | `65338ae5` |
| [graphify-out/cache/ast/v0.9.8/f834ae4a19a993bbcfb64ce4ce5b833f9c66b4b7376678d5fe00d698d94161d5.json](graphify-out/cache/ast/v0.9.8/f834ae4a19a993bbcfb64ce4ce5b833f9c66b4b7376678d5fe00d698d94161d5.json) |  | 2026-07-10 | 97KB | `f27148db` |
| [graphify-out/cache/ast/v0.9.8/f899f6ce4651dd6c9880d682202016dbef15efd8d8ac430117b02d4f204279cc.json](graphify-out/cache/ast/v0.9.8/f899f6ce4651dd6c9880d682202016dbef15efd8d8ac430117b02d4f204279cc.json) |  | 2026-07-08 | 5KB | `cbf05b57` |
| [graphify-out/cache/ast/v0.9.8/f91407f5cfa686da461b4559b4f8c4de75fdf99e38f1ba2b68c8680a6bda193e.json](graphify-out/cache/ast/v0.9.8/f91407f5cfa686da461b4559b4f8c4de75fdf99e38f1ba2b68c8680a6bda193e.json) |  | 2026-07-10 | 4KB | `a66f27d0` |
| [graphify-out/cache/ast/v0.9.8/f9193906585a3e84934d0a1700e5478544708c07d5ea31b44671c5e5a3c8aaa5.json](graphify-out/cache/ast/v0.9.8/f9193906585a3e84934d0a1700e5478544708c07d5ea31b44671c5e5a3c8aaa5.json) |  | 2026-07-08 | 10KB | `ff667311` |
| [graphify-out/cache/ast/v0.9.8/f93954fa8203ffee5ff8c93d2021f9907e96b145d23fdf75f609ca9302cbabf7.json](graphify-out/cache/ast/v0.9.8/f93954fa8203ffee5ff8c93d2021f9907e96b145d23fdf75f609ca9302cbabf7.json) |  | 2026-07-08 | 12KB | `321b363a` |
| [graphify-out/cache/ast/v0.9.8/f9b6a33a8f1dad335fcbe9f10637c88e6514d2ad87814efab71f6f89c6a4a37d.json](graphify-out/cache/ast/v0.9.8/f9b6a33a8f1dad335fcbe9f10637c88e6514d2ad87814efab71f6f89c6a4a37d.json) |  | 2026-07-08 | 47KB | `80736a7f` |
| [graphify-out/cache/ast/v0.9.8/fa0c0ea916ad5d4b1759f7de9f38c76f907e83f2564d50a10c534348759cde4a.json](graphify-out/cache/ast/v0.9.8/fa0c0ea916ad5d4b1759f7de9f38c76f907e83f2564d50a10c534348759cde4a.json) |  | 2026-07-07 | 15KB | `ba078f44` |
| [graphify-out/cache/ast/v0.9.8/fa1be4d2ca4054426a1884b70cb5ff52c6e5ac6bdb7ff9c4f131708a7a412677.json](graphify-out/cache/ast/v0.9.8/fa1be4d2ca4054426a1884b70cb5ff52c6e5ac6bdb7ff9c4f131708a7a412677.json) |  | 2026-07-08 | 5KB | `0b1f33e6` |
| [graphify-out/cache/ast/v0.9.8/fa33f08af0dd181d9d45d2f35bd9cea57d358f578efd3bb4aa8a645c3985fab6.json](graphify-out/cache/ast/v0.9.8/fa33f08af0dd181d9d45d2f35bd9cea57d358f578efd3bb4aa8a645c3985fab6.json) |  | 2026-07-10 | 6KB | `2cfbcc3e` |
| [graphify-out/cache/ast/v0.9.8/fa35ae103eabbb6a798f1d4f8b4794939b6d77efc391f6f285f84dc50a3be9e4.json](graphify-out/cache/ast/v0.9.8/fa35ae103eabbb6a798f1d4f8b4794939b6d77efc391f6f285f84dc50a3be9e4.json) |  | 2026-07-08 | 10KB | `ec71c6e8` |
| [graphify-out/cache/ast/v0.9.8/fa72d341871d8c52f3abfe9c82488983558280f22b0ec405eb8ad6a2395083e9.json](graphify-out/cache/ast/v0.9.8/fa72d341871d8c52f3abfe9c82488983558280f22b0ec405eb8ad6a2395083e9.json) |  | 2026-07-07 | 6KB | `94dc19f0` |
| [graphify-out/cache/ast/v0.9.8/fa85f13fa8da24ae5e6b9643f41fda9e2d6ca25ace5800cf4c2fec0f3c53e345.json](graphify-out/cache/ast/v0.9.8/fa85f13fa8da24ae5e6b9643f41fda9e2d6ca25ace5800cf4c2fec0f3c53e345.json) |  | 2026-07-08 | 15KB | `1a7b68ba` |
| [graphify-out/cache/ast/v0.9.8/faa2d7795ffa94d2c81d9b44ef82f41bae49d454ed4e7e768d1983939e369ed9.json](graphify-out/cache/ast/v0.9.8/faa2d7795ffa94d2c81d9b44ef82f41bae49d454ed4e7e768d1983939e369ed9.json) |  | 2026-07-08 | 6KB | `b29bdcc4` |
| [graphify-out/cache/ast/v0.9.8/fab5b0811d7423af27be19da8a27a7d0f8832b442ff1b8552cba5f94d8fd3f6e.json](graphify-out/cache/ast/v0.9.8/fab5b0811d7423af27be19da8a27a7d0f8832b442ff1b8552cba5f94d8fd3f6e.json) |  | 2026-07-08 | 3KB | `5009eff0` |
| [graphify-out/cache/ast/v0.9.8/fafc7820b81705184a08230003e6c2881aaedf343c5dd06fd8e49c0d9bd6b19e.json](graphify-out/cache/ast/v0.9.8/fafc7820b81705184a08230003e6c2881aaedf343c5dd06fd8e49c0d9bd6b19e.json) |  | 2026-07-10 | 7KB | `00223d89` |
| [graphify-out/cache/ast/v0.9.8/fb2b9ef9dbb26dc8c01d9899cc8c469b97699938109a3fdc16f30389cbe16f77.json](graphify-out/cache/ast/v0.9.8/fb2b9ef9dbb26dc8c01d9899cc8c469b97699938109a3fdc16f30389cbe16f77.json) |  | 2026-07-24 | 20KB | `21dcbad4` |
| [graphify-out/cache/ast/v0.9.8/fb4de50515541a9a506ce3200b95028835e3377e47843f8cfbe8b0f21cd826e8.json](graphify-out/cache/ast/v0.9.8/fb4de50515541a9a506ce3200b95028835e3377e47843f8cfbe8b0f21cd826e8.json) |  | 2026-07-27 | 40KB | `ce6f6baa` |
| [graphify-out/cache/ast/v0.9.8/fb63ac57a1688be02ab696f1edab4926a746e6dea4a16ce0f8831a59885f9843.json](graphify-out/cache/ast/v0.9.8/fb63ac57a1688be02ab696f1edab4926a746e6dea4a16ce0f8831a59885f9843.json) |  | 2026-07-07 | 1KB | `6f416035` |
| [graphify-out/cache/ast/v0.9.8/fb9b8c64a4188ac50355ea155dfddb591d5140d91532196cd5f9dba506c1a0e8.json](graphify-out/cache/ast/v0.9.8/fb9b8c64a4188ac50355ea155dfddb591d5140d91532196cd5f9dba506c1a0e8.json) |  | 2026-07-08 | 25KB | `35cf5b54` |
| [graphify-out/cache/ast/v0.9.8/fc2888b605b45bfa25766f7f7872a8501b427da66326672bb93ad8c484381da7.json](graphify-out/cache/ast/v0.9.8/fc2888b605b45bfa25766f7f7872a8501b427da66326672bb93ad8c484381da7.json) |  | 2026-07-08 | 10KB | `52d1f7b7` |
| [graphify-out/cache/ast/v0.9.8/fc3428ec8778d4f8dbc5bd512a27e13fb5c72b49b98a8286caae3be07f326d4f.json](graphify-out/cache/ast/v0.9.8/fc3428ec8778d4f8dbc5bd512a27e13fb5c72b49b98a8286caae3be07f326d4f.json) |  | 2026-07-07 | 17KB | `c85bf212` |
| [graphify-out/cache/ast/v0.9.8/fd34c4620392d235854c4c1f24283f846f0d984cabf5aa4e814405feec1e19fe.json](graphify-out/cache/ast/v0.9.8/fd34c4620392d235854c4c1f24283f846f0d984cabf5aa4e814405feec1e19fe.json) |  | 2026-07-09 | 57KB | `665245fc` |
| [graphify-out/cache/ast/v0.9.8/fd42d0b31dbbb5d35560cf7388c8f06aa15813b13c08a30b7398029e635f24f6.json](graphify-out/cache/ast/v0.9.8/fd42d0b31dbbb5d35560cf7388c8f06aa15813b13c08a30b7398029e635f24f6.json) |  | 2026-07-07 | 20KB | `1b2b7bae` |
| [graphify-out/cache/ast/v0.9.8/fd4cfa02691dac99b6b1e2034bb7bac1454f95a34c55f2cc94301f7409c234a3.json](graphify-out/cache/ast/v0.9.8/fd4cfa02691dac99b6b1e2034bb7bac1454f95a34c55f2cc94301f7409c234a3.json) |  | 2026-07-24 | 10KB | `45b0ab88` |
| [graphify-out/cache/ast/v0.9.8/fd617802363b74f51d011d3e7b5e4d109fecc0901484fae1b7fce93dd76717ed.json](graphify-out/cache/ast/v0.9.8/fd617802363b74f51d011d3e7b5e4d109fecc0901484fae1b7fce93dd76717ed.json) |  | 2026-07-08 | 63KB | `62fabfe7` |
| [graphify-out/cache/ast/v0.9.8/fd82b980b1981441ce8de412bad5b33f7e1417de9e5aba598366d2a42bb47013.json](graphify-out/cache/ast/v0.9.8/fd82b980b1981441ce8de412bad5b33f7e1417de9e5aba598366d2a42bb47013.json) |  | 2026-07-08 | 6KB | `2a859c60` |
| [graphify-out/cache/ast/v0.9.8/fda6dd1e848de0105792aa224da56ceeceef790c0ee73eeb0bc0e361c9108172.json](graphify-out/cache/ast/v0.9.8/fda6dd1e848de0105792aa224da56ceeceef790c0ee73eeb0bc0e361c9108172.json) |  | 2026-07-07 | 14KB | `5ec98104` |
| [graphify-out/cache/ast/v0.9.8/fdc2ffe88307f7b92f00e4e2683f5390dcafb66d2d69e1fa7eef0009e85c9f87.json](graphify-out/cache/ast/v0.9.8/fdc2ffe88307f7b92f00e4e2683f5390dcafb66d2d69e1fa7eef0009e85c9f87.json) |  | 2026-07-27 | 47KB | `e40ff248` |
| [graphify-out/cache/ast/v0.9.8/fdd02886a3a56f3ef712168c41c7b86451f7ee59ee399a76d418ca95c682498b.json](graphify-out/cache/ast/v0.9.8/fdd02886a3a56f3ef712168c41c7b86451f7ee59ee399a76d418ca95c682498b.json) |  | 2026-07-08 | 42KB | `78147f4c` |
| [graphify-out/cache/ast/v0.9.8/fe00a7da307a191424bc3b4131c6fd5cc30746b734cce55a5f05f173ad9d8c9b.json](graphify-out/cache/ast/v0.9.8/fe00a7da307a191424bc3b4131c6fd5cc30746b734cce55a5f05f173ad9d8c9b.json) |  | 2026-07-08 | 10KB | `e7aed101` |
| [graphify-out/cache/ast/v0.9.8/fe102a1b0713a5cd9caaab32e07003b1691d47cd9ac49508d64b1f2fdddf20d1.json](graphify-out/cache/ast/v0.9.8/fe102a1b0713a5cd9caaab32e07003b1691d47cd9ac49508d64b1f2fdddf20d1.json) |  | 2026-07-08 | 10KB | `a90445a3` |
| [graphify-out/cache/ast/v0.9.8/fe37088c2ae5a1ae74d59873c317ecb36cce2c5b252b8c50a0833b5b3a068e90.json](graphify-out/cache/ast/v0.9.8/fe37088c2ae5a1ae74d59873c317ecb36cce2c5b252b8c50a0833b5b3a068e90.json) |  | 2026-07-08 | 6KB | `8e09e232` |
| [graphify-out/cache/ast/v0.9.8/fe3d92409531b4b292d611353bdfab0636930c49697a915655744d310f7a098a.json](graphify-out/cache/ast/v0.9.8/fe3d92409531b4b292d611353bdfab0636930c49697a915655744d310f7a098a.json) |  | 2026-07-08 | 5KB | `ccba2c6e` |
| [graphify-out/cache/ast/v0.9.8/fe512b2cdf8c83553f272553866e210b108843dc82d0576a627e46b5da24a46e.json](graphify-out/cache/ast/v0.9.8/fe512b2cdf8c83553f272553866e210b108843dc82d0576a627e46b5da24a46e.json) |  | 2026-07-08 | 18KB | `a0bc4b84` |
| [graphify-out/cache/ast/v0.9.8/fe5f194e8c8ce5f3e6e10a664628245660c9e23ae12df2e2d8055eb5a519e693.json](graphify-out/cache/ast/v0.9.8/fe5f194e8c8ce5f3e6e10a664628245660c9e23ae12df2e2d8055eb5a519e693.json) |  | 2026-07-07 | 8KB | `628e8b8a` |
| [graphify-out/cache/ast/v0.9.8/feeb9782c9d464502ee3ad7c896856bfb21fca5774b632db3f5ddcf9a2397e2a.json](graphify-out/cache/ast/v0.9.8/feeb9782c9d464502ee3ad7c896856bfb21fca5774b632db3f5ddcf9a2397e2a.json) |  | 2026-07-07 | 17KB | `c8533e30` |
| [graphify-out/cache/ast/v0.9.8/feef455b6ec55286be781e0d24941054560341062043d78d60d9f74138ffb961.json](graphify-out/cache/ast/v0.9.8/feef455b6ec55286be781e0d24941054560341062043d78d60d9f74138ffb961.json) |  | 2026-07-08 | 9KB | `175676a3` |
| [graphify-out/cache/ast/v0.9.8/fef6d393a09088b39c29bed009430effef972f548df7d88621763a858eaa0ba4.json](graphify-out/cache/ast/v0.9.8/fef6d393a09088b39c29bed009430effef972f548df7d88621763a858eaa0ba4.json) |  | 2026-07-08 | 51KB | `0e72a21a` |
| [graphify-out/cache/ast/v0.9.8/ff643256156503424bbdf68ec15593ba63268f4411028cba198cdebe55dd3a2b.json](graphify-out/cache/ast/v0.9.8/ff643256156503424bbdf68ec15593ba63268f4411028cba198cdebe55dd3a2b.json) |  | 2026-07-07 | 15KB | `e663b361` |
| [graphify-out/cache/ast/v0.9.8/ffab892cca599aab64f9017529f1fbf09d183ff2bfb40cf6952e827231c66395.json](graphify-out/cache/ast/v0.9.8/ffab892cca599aab64f9017529f1fbf09d183ff2bfb40cf6952e827231c66395.json) |  | 2026-07-08 | 17KB | `6b635e31` |
| [graphify-out/cache/ast/v0.9.8/ffc0013009bda95d2ae73888908e50b640c9fc90a76b4415620853ed29333eee.json](graphify-out/cache/ast/v0.9.8/ffc0013009bda95d2ae73888908e50b640c9fc90a76b4415620853ed29333eee.json) |  | 2026-07-08 | 28KB | `801a029c` |
| [graphify-out/cache/ast/v0.9.8/ffd538e4bd8f1ba48e58f835bb5fbb94470d4bf6226fc1ddf5518a091dd4de63.json](graphify-out/cache/ast/v0.9.8/ffd538e4bd8f1ba48e58f835bb5fbb94470d4bf6226fc1ddf5518a091dd4de63.json) |  | 2026-07-08 | 28KB | `c6b4cf8f` |
| [graphify-out/cache/ast/v0.9.8/fffc31365682623c008dc63a713c90b70b287375ab63e0647636cca578648734.json](graphify-out/cache/ast/v0.9.8/fffc31365682623c008dc63a713c90b70b287375ab63e0647636cca578648734.json) |  | 2026-07-08 | 16KB | `db519fc2` |
| [graphify-out/cache/semantic/0031b7e4444bb7d47f5f5f0a8c8e52794bdd75c255d786a67d66c7ff83723529.json](graphify-out/cache/semantic/0031b7e4444bb7d47f5f5f0a8c8e52794bdd75c255d786a67d66c7ff83723529.json) |  | 2026-07-08 | 389B | `f5491aa3` |
| [graphify-out/cache/semantic/010ee2192d71f1ebfd02b5d820b585663c7cc887a2fb747e841234c95cd67b44.json](graphify-out/cache/semantic/010ee2192d71f1ebfd02b5d820b585663c7cc887a2fb747e841234c95cd67b44.json) |  | 2026-07-08 | 869B | `dad26ce4` |
| [graphify-out/cache/semantic/01148ed0ccdd549a92c8adb1bf5cb21f5aa7eab3af82b9ced25fdb664563485b.json](graphify-out/cache/semantic/01148ed0ccdd549a92c8adb1bf5cb21f5aa7eab3af82b9ced25fdb664563485b.json) |  | 2026-07-08 | 327B | `8b8693d2` |
| [graphify-out/cache/semantic/02533d11a6bc39bef65990f12e34269fc67549b8d1963eb46c5e490be809ead6.json](graphify-out/cache/semantic/02533d11a6bc39bef65990f12e34269fc67549b8d1963eb46c5e490be809ead6.json) |  | 2026-07-08 | 745B | `7c8ee816` |
| [graphify-out/cache/semantic/0415081efc220fba5056bf7b75924827950beb59d9835a3263380dfe3bb8c638.json](graphify-out/cache/semantic/0415081efc220fba5056bf7b75924827950beb59d9835a3263380dfe3bb8c638.json) |  | 2026-07-08 | 326B | `53c9c912` |
| [graphify-out/cache/semantic/052d560adf40e09bfecf7fae97e77c37df3bf744831fd31c203818e97a859346.json](graphify-out/cache/semantic/052d560adf40e09bfecf7fae97e77c37df3bf744831fd31c203818e97a859346.json) |  | 2026-07-08 | 949B | `988cd9f3` |
| [graphify-out/cache/semantic/06188963189a2757bd4bc2401effd13008afef7bd25c98f7eb64303a0493c735.json](graphify-out/cache/semantic/06188963189a2757bd4bc2401effd13008afef7bd25c98f7eb64303a0493c735.json) |  | 2026-07-08 | 800B | `d64fd380` |
| [graphify-out/cache/semantic/06e0226b2a8b3fc0ce61d6ddfbf4c7eafa69bc67079b1635263ea141fff14fb0.json](graphify-out/cache/semantic/06e0226b2a8b3fc0ce61d6ddfbf4c7eafa69bc67079b1635263ea141fff14fb0.json) |  | 2026-07-08 | 917B | `68b8232e` |
| [graphify-out/cache/semantic/06f2984c00af0ebcfface89b4ba47ab22037614ee8fe661b108d36a867b85593.json](graphify-out/cache/semantic/06f2984c00af0ebcfface89b4ba47ab22037614ee8fe661b108d36a867b85593.json) |  | 2026-07-08 | 815B | `e3c777ad` |
| [graphify-out/cache/semantic/0738bef7fb891288545e9930cf6111b8fe186c433c3abb78ebd0f893d50fcc98.json](graphify-out/cache/semantic/0738bef7fb891288545e9930cf6111b8fe186c433c3abb78ebd0f893d50fcc98.json) |  | 2026-07-08 | 927B | `f23a7255` |
| [graphify-out/cache/semantic/0769b2ad2a0e4d20814459a4bf408e4aa2b334051856e16f8dfe7edda04e10bb.json](graphify-out/cache/semantic/0769b2ad2a0e4d20814459a4bf408e4aa2b334051856e16f8dfe7edda04e10bb.json) |  | 2026-07-08 | 700B | `b933f2f5` |
| [graphify-out/cache/semantic/079a0a120a9d99bb5b71a944b7446ca7bd8b3f75cdf953671be030ac60c27366.json](graphify-out/cache/semantic/079a0a120a9d99bb5b71a944b7446ca7bd8b3f75cdf953671be030ac60c27366.json) |  | 2026-07-08 | 2KB | `5d2f6a27` |
| [graphify-out/cache/semantic/08c9f950c423096f9947baad20e5e188e7a9be054bedda5a4206d0801f035ff6.json](graphify-out/cache/semantic/08c9f950c423096f9947baad20e5e188e7a9be054bedda5a4206d0801f035ff6.json) |  | 2026-07-08 | 1KB | `ac1a2737` |
| [graphify-out/cache/semantic/090224d1f1c9ab940121360104d78c6fdf32eafa9a9a0e9c5e316d4d685876a8.json](graphify-out/cache/semantic/090224d1f1c9ab940121360104d78c6fdf32eafa9a9a0e9c5e316d4d685876a8.json) |  | 2026-07-08 | 356B | `b94eb559` |
| [graphify-out/cache/semantic/091c0e9c283d2efc5a8ae15089c9cd7c9fa22afce3f565d0728d30f07c494a29.json](graphify-out/cache/semantic/091c0e9c283d2efc5a8ae15089c9cd7c9fa22afce3f565d0728d30f07c494a29.json) |  | 2026-07-08 | 839B | `5f6cdf10` |
| [graphify-out/cache/semantic/09381c5735f971f0f9f69d1be863025ad2243f37c66a7665d2aabea77039c5e3.json](graphify-out/cache/semantic/09381c5735f971f0f9f69d1be863025ad2243f37c66a7665d2aabea77039c5e3.json) |  | 2026-07-08 | 588B | `48f9c346` |
| [graphify-out/cache/semantic/0ac762f3547e69f705084a672d417df863d73d1c2c45a057d3f5f594770bbdf1.json](graphify-out/cache/semantic/0ac762f3547e69f705084a672d417df863d73d1c2c45a057d3f5f594770bbdf1.json) |  | 2026-07-08 | 452B | `9ffb8b6f` |
| [graphify-out/cache/semantic/0c49df0a9defad6c3c78a3c61cc9e246e25e7a2a1b1062b851ac70cdc3234750.json](graphify-out/cache/semantic/0c49df0a9defad6c3c78a3c61cc9e246e25e7a2a1b1062b851ac70cdc3234750.json) |  | 2026-07-08 | 2KB | `cf75c64f` |
| [graphify-out/cache/semantic/0dc4946b78c355c2c6b10ddd683e698e23a813774d27b1cab506edb6394092c6.json](graphify-out/cache/semantic/0dc4946b78c355c2c6b10ddd683e698e23a813774d27b1cab506edb6394092c6.json) |  | 2026-07-08 | 1KB | `5c5815a7` |
| [graphify-out/cache/semantic/0dd2f03f9f0d83aa6a5496c21bcbafdaec5e06fc823aaef73441980117a265c4.json](graphify-out/cache/semantic/0dd2f03f9f0d83aa6a5496c21bcbafdaec5e06fc823aaef73441980117a265c4.json) |  | 2026-07-08 | 343B | `25bb38be` |
| [graphify-out/cache/semantic/0e7fb3b6ec55617be9083b7870b8caf22aea200cb9cf10255449a1501004ea0e.json](graphify-out/cache/semantic/0e7fb3b6ec55617be9083b7870b8caf22aea200cb9cf10255449a1501004ea0e.json) |  | 2026-07-08 | 387B | `067f4d33` |
| [graphify-out/cache/semantic/0edd9f39418a12ffda12c17ad9e6ab71ae1835d69e76e3bedfbb34cec7a0056a.json](graphify-out/cache/semantic/0edd9f39418a12ffda12c17ad9e6ab71ae1835d69e76e3bedfbb34cec7a0056a.json) |  | 2026-07-08 | 284B | `6edc1ca4` |
| [graphify-out/cache/semantic/0f4a4537dd2a0125eaf60e9f9ac0fd2bf371599b60c0a036b618c6032bc4e80e.json](graphify-out/cache/semantic/0f4a4537dd2a0125eaf60e9f9ac0fd2bf371599b60c0a036b618c6032bc4e80e.json) |  | 2026-07-08 | 4KB | `16cf3b66` |
| [graphify-out/cache/semantic/0f714776c03b8484404723a725aead337dfdeb01584663f764dd706044507304.json](graphify-out/cache/semantic/0f714776c03b8484404723a725aead337dfdeb01584663f764dd706044507304.json) |  | 2026-07-08 | 3KB | `1690b301` |
| [graphify-out/cache/semantic/0fc96f785699687c5d8ea014b9cb6de0917d5e377e2d72f4fa655304c627a59a.json](graphify-out/cache/semantic/0fc96f785699687c5d8ea014b9cb6de0917d5e377e2d72f4fa655304c627a59a.json) |  | 2026-07-08 | 2KB | `a0843fcd` |
| [graphify-out/cache/semantic/101b2b31666d4f15e61445129d7620e9cfc254778a7d4582369d29f336d00713.json](graphify-out/cache/semantic/101b2b31666d4f15e61445129d7620e9cfc254778a7d4582369d29f336d00713.json) |  | 2026-07-08 | 265B | `7950d234` |
| [graphify-out/cache/semantic/10ebb1371a90f903d08fcd6398060742e2a4c85dbde86690fd9ee4d519c499f9.json](graphify-out/cache/semantic/10ebb1371a90f903d08fcd6398060742e2a4c85dbde86690fd9ee4d519c499f9.json) |  | 2026-07-08 | 583B | `92244097` |
| [graphify-out/cache/semantic/11ccb1abf86d3867c5440690f44a0b4f96678d5567b9fa5e3bf4c338d0733579.json](graphify-out/cache/semantic/11ccb1abf86d3867c5440690f44a0b4f96678d5567b9fa5e3bf4c338d0733579.json) |  | 2026-07-08 | 1KB | `ab1c465f` |
| [graphify-out/cache/semantic/12c9484b2a3478636f0553c3fdeaa45475bf568f6f9fb2b64955c432fe71f3f0.json](graphify-out/cache/semantic/12c9484b2a3478636f0553c3fdeaa45475bf568f6f9fb2b64955c432fe71f3f0.json) |  | 2026-07-08 | 6KB | `3ae31c85` |
| [graphify-out/cache/semantic/136dca00217ac832f39b3318b0f51dd3236e2440eb0b5bb04aba58dcc6d5b0b2.json](graphify-out/cache/semantic/136dca00217ac832f39b3318b0f51dd3236e2440eb0b5bb04aba58dcc6d5b0b2.json) |  | 2026-07-08 | 344B | `308d7fcf` |
| [graphify-out/cache/semantic/14036bfdedaeffbd8e81caab79e1ee8331c5eb02522b9a49aeecb1c2471250c8.json](graphify-out/cache/semantic/14036bfdedaeffbd8e81caab79e1ee8331c5eb02522b9a49aeecb1c2471250c8.json) |  | 2026-07-08 | 436B | `ad8f6e4d` |
| [graphify-out/cache/semantic/147fc9a743b71244a94a2a5acac1a804f462abe8d64f913e8758a57cca8f02be.json](graphify-out/cache/semantic/147fc9a743b71244a94a2a5acac1a804f462abe8d64f913e8758a57cca8f02be.json) |  | 2026-07-08 | 909B | `ff14b84a` |
| [graphify-out/cache/semantic/150f4feb73e1f2dffb37211a058f4b113e975e116e61ef72ff917714fa689fa6.json](graphify-out/cache/semantic/150f4feb73e1f2dffb37211a058f4b113e975e116e61ef72ff917714fa689fa6.json) |  | 2026-07-08 | 1KB | `7bcd406c` |
| [graphify-out/cache/semantic/16060a25505a5ee1158574107c3344640e53fae3643c620ebaaac3ef7e5e1d35.json](graphify-out/cache/semantic/16060a25505a5ee1158574107c3344640e53fae3643c620ebaaac3ef7e5e1d35.json) |  | 2026-07-08 | 353B | `62a21091` |
| [graphify-out/cache/semantic/1663ee67f769af35949d60821aa97c24830338e85637ae3dc200a902184b99c7.json](graphify-out/cache/semantic/1663ee67f769af35949d60821aa97c24830338e85637ae3dc200a902184b99c7.json) |  | 2026-07-08 | 6KB | `7fc028ee` |
| [graphify-out/cache/semantic/179cb0793000f6a9c4972600dee47016813b7a99733e979b1f3d82afe93f70be.json](graphify-out/cache/semantic/179cb0793000f6a9c4972600dee47016813b7a99733e979b1f3d82afe93f70be.json) |  | 2026-07-08 | 296B | `77d67d74` |
| [graphify-out/cache/semantic/18a5d711c8005c185c67716e5e42e4ddaba49d81fe66339af1a626b2b47948c6.json](graphify-out/cache/semantic/18a5d711c8005c185c67716e5e42e4ddaba49d81fe66339af1a626b2b47948c6.json) |  | 2026-07-08 | 2KB | `d18d8ef6` |
| [graphify-out/cache/semantic/194f53c7557967d5acd10d16e846a4c4108e0e78883cb1108bd6c1bf012124d3.json](graphify-out/cache/semantic/194f53c7557967d5acd10d16e846a4c4108e0e78883cb1108bd6c1bf012124d3.json) |  | 2026-07-08 | 2KB | `ba94edb6` |
| [graphify-out/cache/semantic/1994dd52985fdc653c5842ff85a796ad0418254dc7ceae2f4739a9e54bd7f477.json](graphify-out/cache/semantic/1994dd52985fdc653c5842ff85a796ad0418254dc7ceae2f4739a9e54bd7f477.json) |  | 2026-07-08 | 1KB | `bd2f3f80` |
| [graphify-out/cache/semantic/1b0fa91aa4af4f0e5a608c01918c42b6a4d1785ab4ceb511cd44a078a5d33799.json](graphify-out/cache/semantic/1b0fa91aa4af4f0e5a608c01918c42b6a4d1785ab4ceb511cd44a078a5d33799.json) |  | 2026-07-08 | 948B | `0969d5be` |
| [graphify-out/cache/semantic/1b8419e6a1ca1dca54710868658644554cc2c91a8fe43ccac66018fb0813a6ae.json](graphify-out/cache/semantic/1b8419e6a1ca1dca54710868658644554cc2c91a8fe43ccac66018fb0813a6ae.json) |  | 2026-07-08 | 1KB | `f1fd9fd0` |
| [graphify-out/cache/semantic/1bd6d34a1dd3a0e0448707b90d2ebb525f3276f68f436f186b78f6da5d75f6cf.json](graphify-out/cache/semantic/1bd6d34a1dd3a0e0448707b90d2ebb525f3276f68f436f186b78f6da5d75f6cf.json) |  | 2026-07-08 | 1KB | `6c32e679` |
| [graphify-out/cache/semantic/1bf48dc5d126c8c4afdd1517ef6df5a64ce9839da04d58ef6dec23c2012031d2.json](graphify-out/cache/semantic/1bf48dc5d126c8c4afdd1517ef6df5a64ce9839da04d58ef6dec23c2012031d2.json) |  | 2026-07-08 | 805B | `e7b2adda` |
| [graphify-out/cache/semantic/1cca50e9a90db4b806736bc4c7cad9dddacf963da47692727220bc8f6c77f9ab.json](graphify-out/cache/semantic/1cca50e9a90db4b806736bc4c7cad9dddacf963da47692727220bc8f6c77f9ab.json) |  | 2026-07-08 | 933B | `497a75ff` |
| [graphify-out/cache/semantic/1dd8ece4982e5f098ec3843d41c8d602b375c62da68008e14cd6858111ff1400.json](graphify-out/cache/semantic/1dd8ece4982e5f098ec3843d41c8d602b375c62da68008e14cd6858111ff1400.json) |  | 2026-07-08 | 2KB | `7d3d4a22` |
| [graphify-out/cache/semantic/1e0b3258f0a89600fca06e1d6078070f358e772c50573a2deedd825490d0821e.json](graphify-out/cache/semantic/1e0b3258f0a89600fca06e1d6078070f358e772c50573a2deedd825490d0821e.json) |  | 2026-07-08 | 746B | `2f167a18` |
| [graphify-out/cache/semantic/1ef8f14e120488c1347eaa4e149f4d1e28003c381c088799a217d8804a091638.json](graphify-out/cache/semantic/1ef8f14e120488c1347eaa4e149f4d1e28003c381c088799a217d8804a091638.json) |  | 2026-07-08 | 800B | `b6044625` |
| [graphify-out/cache/semantic/1f28fa0ac130ff4adf3707180b327597ebfe044b0424cf7c9bfcabf1f748be3a.json](graphify-out/cache/semantic/1f28fa0ac130ff4adf3707180b327597ebfe044b0424cf7c9bfcabf1f748be3a.json) |  | 2026-07-08 | 926B | `0d07af74` |
| [graphify-out/cache/semantic/1f38972804d6512fd010fb0915571d1b01cb4ff3e604acbbe6659a05c808f4e1.json](graphify-out/cache/semantic/1f38972804d6512fd010fb0915571d1b01cb4ff3e604acbbe6659a05c808f4e1.json) |  | 2026-07-08 | 298B | `a3127154` |
| [graphify-out/cache/semantic/1f94e8bceefaad39dd4e47fcd12293144b5c812ece98d491679b32284340931d.json](graphify-out/cache/semantic/1f94e8bceefaad39dd4e47fcd12293144b5c812ece98d491679b32284340931d.json) |  | 2026-07-08 | 873B | `c99b9ab8` |
| [graphify-out/cache/semantic/20c7321b4c865e9a4a6ec65bf6cfcd07d0188ccc30492689e8873a74ec590ad5.json](graphify-out/cache/semantic/20c7321b4c865e9a4a6ec65bf6cfcd07d0188ccc30492689e8873a74ec590ad5.json) |  | 2026-07-08 | 440B | `23e2574e` |
| [graphify-out/cache/semantic/216c1d511248b35211d21f2da0296f1c60d7ac5ad87dd7a13d5c47e362c7cb1f.json](graphify-out/cache/semantic/216c1d511248b35211d21f2da0296f1c60d7ac5ad87dd7a13d5c47e362c7cb1f.json) |  | 2026-07-08 | 2KB | `ec2bdd99` |
| [graphify-out/cache/semantic/22041781269c8e6b8e27785c41d49a9500a7f22a11060f3582aecaa821d652b9.json](graphify-out/cache/semantic/22041781269c8e6b8e27785c41d49a9500a7f22a11060f3582aecaa821d652b9.json) |  | 2026-07-08 | 768B | `dad4a9ba` |
| [graphify-out/cache/semantic/22570e30ef650480a9c80b8f854895e863acb2633c519a60375d7a8dbb80a7f6.json](graphify-out/cache/semantic/22570e30ef650480a9c80b8f854895e863acb2633c519a60375d7a8dbb80a7f6.json) |  | 2026-07-08 | 2KB | `4b5dd786` |
| [graphify-out/cache/semantic/227297cdcaf877b5ed4ca60662ddd08ae690542fee98a2b2806e83b598731d79.json](graphify-out/cache/semantic/227297cdcaf877b5ed4ca60662ddd08ae690542fee98a2b2806e83b598731d79.json) |  | 2026-07-08 | 1KB | `c1314825` |
| [graphify-out/cache/semantic/22c8e88c4b579fc248d57254c7ccc51a3cabf2f39a0f5078a2ffed78ceb58b21.json](graphify-out/cache/semantic/22c8e88c4b579fc248d57254c7ccc51a3cabf2f39a0f5078a2ffed78ceb58b21.json) |  | 2026-07-08 | 3KB | `2d57fd1c` |
| [graphify-out/cache/semantic/23640e7c1a703000ffb1839f02365b6600ed9a07805bce84addd4a65cf7b6515.json](graphify-out/cache/semantic/23640e7c1a703000ffb1839f02365b6600ed9a07805bce84addd4a65cf7b6515.json) |  | 2026-07-08 | 390B | `def230a9` |
| [graphify-out/cache/semantic/238fab9bc9109f3583b1a92da45bad163ab0614e4c376e8e1acc75ae4e771ad1.json](graphify-out/cache/semantic/238fab9bc9109f3583b1a92da45bad163ab0614e4c376e8e1acc75ae4e771ad1.json) |  | 2026-07-08 | 1KB | `6e342a1c` |
| [graphify-out/cache/semantic/24a0d508a77219d34d2f52afff922dfdc497063350dae50b6ea747fd87ab8db6.json](graphify-out/cache/semantic/24a0d508a77219d34d2f52afff922dfdc497063350dae50b6ea747fd87ab8db6.json) |  | 2026-07-08 | 322B | `db93f19c` |
| [graphify-out/cache/semantic/26dc3db48b80e52e0eba1f9ba0092c3b1e88067366e8acc331d5983ba7d2bb5d.json](graphify-out/cache/semantic/26dc3db48b80e52e0eba1f9ba0092c3b1e88067366e8acc331d5983ba7d2bb5d.json) |  | 2026-07-08 | 1KB | `43b5e6ff` |
| [graphify-out/cache/semantic/2723d53508f4d49d209907e8cd0aaa4f2840a583ac0e43aabc68a5cdc0667449.json](graphify-out/cache/semantic/2723d53508f4d49d209907e8cd0aaa4f2840a583ac0e43aabc68a5cdc0667449.json) |  | 2026-07-08 | 717B | `c557e8f0` |
| [graphify-out/cache/semantic/27c54167b13ea8e08c48eb78a5eac77057930d74590b0bb10217768d4d0af2bd.json](graphify-out/cache/semantic/27c54167b13ea8e08c48eb78a5eac77057930d74590b0bb10217768d4d0af2bd.json) |  | 2026-07-08 | 3KB | `fbcfd34e` |
| [graphify-out/cache/semantic/2807b41337fbdf586ab9cb1d418c0edfa2b0f26fb1835885f42c848b9b5a40a6.json](graphify-out/cache/semantic/2807b41337fbdf586ab9cb1d418c0edfa2b0f26fb1835885f42c848b9b5a40a6.json) |  | 2026-07-08 | 1KB | `6b04d4ff` |
| [graphify-out/cache/semantic/2a4e918eed719ca273ee48052f9a6830b033e2366884edbf6c0a775725730b33.json](graphify-out/cache/semantic/2a4e918eed719ca273ee48052f9a6830b033e2366884edbf6c0a775725730b33.json) |  | 2026-07-08 | 2KB | `c11cd18a` |
| [graphify-out/cache/semantic/2afcb96eb918eea8bfb933e8cbd089e496f5ea262dddaa4558260c0b180656fe.json](graphify-out/cache/semantic/2afcb96eb918eea8bfb933e8cbd089e496f5ea262dddaa4558260c0b180656fe.json) |  | 2026-07-08 | 1012B | `095bba90` |
| [graphify-out/cache/semantic/2b45422a8e21c77a5c8c61864d0e449018b977f5c92c830a18264fd7f49d55ab.json](graphify-out/cache/semantic/2b45422a8e21c77a5c8c61864d0e449018b977f5c92c830a18264fd7f49d55ab.json) |  | 2026-07-08 | 5KB | `13ae50ed` |
| [graphify-out/cache/semantic/2cb57d10e366526865d22e949897164bf22f7cc67988466bc5d9f15a7a136cb1.json](graphify-out/cache/semantic/2cb57d10e366526865d22e949897164bf22f7cc67988466bc5d9f15a7a136cb1.json) |  | 2026-07-08 | 2KB | `d8f8dbbb` |
| [graphify-out/cache/semantic/2cbccae9e25a1ee76c5a1af041bfc624a387ae3ab8a851e17928c07844a70061.json](graphify-out/cache/semantic/2cbccae9e25a1ee76c5a1af041bfc624a387ae3ab8a851e17928c07844a70061.json) |  | 2026-07-08 | 859B | `e3044b1e` |
| [graphify-out/cache/semantic/2d188a71baf735f090345a5cfc55d8e6111035cfbf4568a98f683f7870495f5f.json](graphify-out/cache/semantic/2d188a71baf735f090345a5cfc55d8e6111035cfbf4568a98f683f7870495f5f.json) |  | 2026-07-08 | 2KB | `d425d5f5` |
| [graphify-out/cache/semantic/2e25d93476591f9488aaa2b2540e59da29b5a4a60ce194957984de7ad3e21760.json](graphify-out/cache/semantic/2e25d93476591f9488aaa2b2540e59da29b5a4a60ce194957984de7ad3e21760.json) |  | 2026-07-08 | 3KB | `3c5d6042` |
| [graphify-out/cache/semantic/2f8ac8401a17b34afdf3cf327efec67738e436b124a1fcfa45932aec38bd1002.json](graphify-out/cache/semantic/2f8ac8401a17b34afdf3cf327efec67738e436b124a1fcfa45932aec38bd1002.json) |  | 2026-07-08 | 335B | `f42b2543` |
| [graphify-out/cache/semantic/30274d269b8cfbd194c5a305e48897901f962a710e0ed86fcecbe631df38a5c9.json](graphify-out/cache/semantic/30274d269b8cfbd194c5a305e48897901f962a710e0ed86fcecbe631df38a5c9.json) |  | 2026-07-08 | 1KB | `fc422a3e` |
| [graphify-out/cache/semantic/31726c3485f8e38bceb513de8e1837febc053b5ab810cb11af58617423f7bbd3.json](graphify-out/cache/semantic/31726c3485f8e38bceb513de8e1837febc053b5ab810cb11af58617423f7bbd3.json) |  | 2026-07-08 | 901B | `a2acf6cb` |
| [graphify-out/cache/semantic/31ccf58e04c3339ae7f3485220861e403880aaea525281381a68bb69b1e6134b.json](graphify-out/cache/semantic/31ccf58e04c3339ae7f3485220861e403880aaea525281381a68bb69b1e6134b.json) |  | 2026-07-08 | 374B | `a7603375` |
| [graphify-out/cache/semantic/31ddc60107b129f3781169d2ee3d7d70306afc7b6c1aee2cd7d3cc70034290dc.json](graphify-out/cache/semantic/31ddc60107b129f3781169d2ee3d7d70306afc7b6c1aee2cd7d3cc70034290dc.json) |  | 2026-07-08 | 1KB | `ca8b612b` |
| [graphify-out/cache/semantic/32f48b7a0d301edb9bacb96f364b3f2883569bb0bf36e282424be62f527700bf.json](graphify-out/cache/semantic/32f48b7a0d301edb9bacb96f364b3f2883569bb0bf36e282424be62f527700bf.json) |  | 2026-07-08 | 1KB | `2d31337c` |
| [graphify-out/cache/semantic/33246f1e12de6f986df84c46aafd792956fd0f93ef6032a1187d4d2a02fcbc34.json](graphify-out/cache/semantic/33246f1e12de6f986df84c46aafd792956fd0f93ef6032a1187d4d2a02fcbc34.json) |  | 2026-07-08 | 2KB | `9516a648` |
| [graphify-out/cache/semantic/335f2ab2e6d09f6f9ae7c17afc2e2e6e59e4fdea468d1b1ed89372cf6a7f610f.json](graphify-out/cache/semantic/335f2ab2e6d09f6f9ae7c17afc2e2e6e59e4fdea468d1b1ed89372cf6a7f610f.json) |  | 2026-07-08 | 492B | `43772f87` |
| [graphify-out/cache/semantic/33c86aa7a68f6dbdda6406b3d5934498a9a7265b4d97a8033b420fc6e960007b.json](graphify-out/cache/semantic/33c86aa7a68f6dbdda6406b3d5934498a9a7265b4d97a8033b420fc6e960007b.json) |  | 2026-07-08 | 652B | `c7d12934` |
| [graphify-out/cache/semantic/3525e1167e76af103522cfe7fe6118d3b022fabacd6eb15409705489a90be79a.json](graphify-out/cache/semantic/3525e1167e76af103522cfe7fe6118d3b022fabacd6eb15409705489a90be79a.json) |  | 2026-07-08 | 637B | `afd04361` |
| [graphify-out/cache/semantic/36a1cc4781db9bc84a18ea083681d0bdda12abf4ed62fc9ca7f5e8d7e69e0d34.json](graphify-out/cache/semantic/36a1cc4781db9bc84a18ea083681d0bdda12abf4ed62fc9ca7f5e8d7e69e0d34.json) |  | 2026-07-08 | 4KB | `75677ffe` |
| [graphify-out/cache/semantic/376b2d25d459655cc55d44d7112b33fb012abe48cc4c97ab953aa05f38242100.json](graphify-out/cache/semantic/376b2d25d459655cc55d44d7112b33fb012abe48cc4c97ab953aa05f38242100.json) |  | 2026-07-08 | 634B | `82940ca6` |
| [graphify-out/cache/semantic/38c09bf86ba84aae4cd6d301633dc880185eacdf814f5765a6f5fa76ac7b5bd2.json](graphify-out/cache/semantic/38c09bf86ba84aae4cd6d301633dc880185eacdf814f5765a6f5fa76ac7b5bd2.json) |  | 2026-07-08 | 486B | `9fee8fb9` |
| [graphify-out/cache/semantic/39b57efda4f474d72db9be9f4cdf6e3e0dc7f216c152453d0b6de49055374de3.json](graphify-out/cache/semantic/39b57efda4f474d72db9be9f4cdf6e3e0dc7f216c152453d0b6de49055374de3.json) |  | 2026-07-08 | 284B | `3250cf4d` |
| [graphify-out/cache/semantic/3b33004c1b5a26e1325a683996c55856877faf1c11155639fbfc2a1aec01144b.json](graphify-out/cache/semantic/3b33004c1b5a26e1325a683996c55856877faf1c11155639fbfc2a1aec01144b.json) |  | 2026-07-08 | 317B | `2285a275` |
| [graphify-out/cache/semantic/3b49fba84cce5f047706f25fc011ca55f7c519e57d901e3a9001464ac21df805.json](graphify-out/cache/semantic/3b49fba84cce5f047706f25fc011ca55f7c519e57d901e3a9001464ac21df805.json) |  | 2026-07-08 | 703B | `b0e87d19` |
| [graphify-out/cache/semantic/3b9230088999f11e702ee71d6ed636a96502bef7d2eaf9901ee8606b88776c05.json](graphify-out/cache/semantic/3b9230088999f11e702ee71d6ed636a96502bef7d2eaf9901ee8606b88776c05.json) |  | 2026-07-08 | 291B | `e299f932` |
| [graphify-out/cache/semantic/3ba5c03eafe8ae6aae80dc7d071b6a4d239cd51fe41c1c601ea34ad88cb1a1f4.json](graphify-out/cache/semantic/3ba5c03eafe8ae6aae80dc7d071b6a4d239cd51fe41c1c601ea34ad88cb1a1f4.json) |  | 2026-07-08 | 750B | `aa2a8f98` |
| [graphify-out/cache/semantic/3c08615b2d80aaf472346912931bd635cf2ac7135cfc85599b4be3eaf747b2bd.json](graphify-out/cache/semantic/3c08615b2d80aaf472346912931bd635cf2ac7135cfc85599b4be3eaf747b2bd.json) |  | 2026-07-08 | 353B | `69e30438` |
| [graphify-out/cache/semantic/3c3bf57cffff7d8e260bf4c294b3790b4f08a4a060e856b01d0b9cda43c68882.json](graphify-out/cache/semantic/3c3bf57cffff7d8e260bf4c294b3790b4f08a4a060e856b01d0b9cda43c68882.json) |  | 2026-07-08 | 1KB | `ce8dbaa8` |
| [graphify-out/cache/semantic/3d11e91324a942e79dd74ed17e95e5ca0ec80bf213281e885866e683a2b95a5b.json](graphify-out/cache/semantic/3d11e91324a942e79dd74ed17e95e5ca0ec80bf213281e885866e683a2b95a5b.json) |  | 2026-07-08 | 588B | `671cbf95` |
| [graphify-out/cache/semantic/3d60227a95909d9c000b702e66431794c4c92baceafe0dff3bdeb2d0edca3768.json](graphify-out/cache/semantic/3d60227a95909d9c000b702e66431794c4c92baceafe0dff3bdeb2d0edca3768.json) |  | 2026-07-08 | 993B | `1bb15148` |
| [graphify-out/cache/semantic/3da5ecd5d72d6cef337dc28481801e1e69b32b5c09e7792ef1cd30b8c0aa6def.json](graphify-out/cache/semantic/3da5ecd5d72d6cef337dc28481801e1e69b32b5c09e7792ef1cd30b8c0aa6def.json) |  | 2026-07-08 | 766B | `5f8f9dbb` |
| [graphify-out/cache/semantic/3f588af826bfc5e9b87ee39edacc90a8f01d6622ef8465a714e98ca326befa03.json](graphify-out/cache/semantic/3f588af826bfc5e9b87ee39edacc90a8f01d6622ef8465a714e98ca326befa03.json) |  | 2026-07-08 | 717B | `5a43574d` |
| [graphify-out/cache/semantic/401b71fd3dbe8aa044a60462b3699b1dc9f902f0e12157bf2957097e77ff437e.json](graphify-out/cache/semantic/401b71fd3dbe8aa044a60462b3699b1dc9f902f0e12157bf2957097e77ff437e.json) |  | 2026-07-08 | 344B | `9235085b` |
| [graphify-out/cache/semantic/40707394dc7b4887ce92985548b9634d241bb48b43f333c5be0d44aacb6b1547.json](graphify-out/cache/semantic/40707394dc7b4887ce92985548b9634d241bb48b43f333c5be0d44aacb6b1547.json) |  | 2026-07-08 | 1KB | `0da0725e` |
| [graphify-out/cache/semantic/409542d95910afbc07eaaba8aba21f782e71e89c16702e758e2d01ea71cc6617.json](graphify-out/cache/semantic/409542d95910afbc07eaaba8aba21f782e71e89c16702e758e2d01ea71cc6617.json) |  | 2026-07-08 | 357B | `3d8013e8` |
| [graphify-out/cache/semantic/40a092641d5b7c0b0bdcdd7ca6e3db8ebff5cd52652145f8bfe3121e8b60cf89.json](graphify-out/cache/semantic/40a092641d5b7c0b0bdcdd7ca6e3db8ebff5cd52652145f8bfe3121e8b60cf89.json) |  | 2026-07-08 | 739B | `621cb6b0` |
| [graphify-out/cache/semantic/40c4ebc5f978b7a50691d192585a3e23f3f577c39c940244221d608035c5d9fa.json](graphify-out/cache/semantic/40c4ebc5f978b7a50691d192585a3e23f3f577c39c940244221d608035c5d9fa.json) |  | 2026-07-08 | 347B | `f16cd8ab` |
| [graphify-out/cache/semantic/41c7c383511a28eced007887b87a2dc0494666f1a2a32e3c95abb6f3d583ef05.json](graphify-out/cache/semantic/41c7c383511a28eced007887b87a2dc0494666f1a2a32e3c95abb6f3d583ef05.json) |  | 2026-07-08 | 353B | `2fa6f7af` |
| [graphify-out/cache/semantic/42a9637ede11b982035718d1f9e5076a39228469ee4e772b7a3972e4d21f8c8e.json](graphify-out/cache/semantic/42a9637ede11b982035718d1f9e5076a39228469ee4e772b7a3972e4d21f8c8e.json) |  | 2026-07-08 | 2KB | `079e35f0` |
| [graphify-out/cache/semantic/4306875d997f18f91891f35ba8eb86c685eb9c33c834ccefd29b341eacc39424.json](graphify-out/cache/semantic/4306875d997f18f91891f35ba8eb86c685eb9c33c834ccefd29b341eacc39424.json) |  | 2026-07-08 | 312B | `eed75be9` |
| [graphify-out/cache/semantic/4371236530f458982759109a9129d637e1fe02f50f77195198c1049564e06ec1.json](graphify-out/cache/semantic/4371236530f458982759109a9129d637e1fe02f50f77195198c1049564e06ec1.json) |  | 2026-07-08 | 7KB | `9d90c87e` |
| [graphify-out/cache/semantic/448a9ff0753ba2ede7635d0252d08a01db4bc5fe08d592b7ab4d525eb20eab30.json](graphify-out/cache/semantic/448a9ff0753ba2ede7635d0252d08a01db4bc5fe08d592b7ab4d525eb20eab30.json) |  | 2026-07-08 | 362B | `911520b5` |
| [graphify-out/cache/semantic/449205f79a3a738af46f17ac15d43ced52d5e38405cb20c3686662ef487b9734.json](graphify-out/cache/semantic/449205f79a3a738af46f17ac15d43ced52d5e38405cb20c3686662ef487b9734.json) |  | 2026-07-08 | 1KB | `7ed17c03` |
| [graphify-out/cache/semantic/44e7287ebfd615d6857cc475707232a602e113545146a6b6fcdf0fdcf93ae5a7.json](graphify-out/cache/semantic/44e7287ebfd615d6857cc475707232a602e113545146a6b6fcdf0fdcf93ae5a7.json) |  | 2026-07-08 | 312B | `10e018c5` |
| [graphify-out/cache/semantic/456415b50a5ecdd44d98338f4fa3bc7cdc9247ab5ad4bbbc7a751a46fd581665.json](graphify-out/cache/semantic/456415b50a5ecdd44d98338f4fa3bc7cdc9247ab5ad4bbbc7a751a46fd581665.json) |  | 2026-07-08 | 1KB | `c271e011` |
| [graphify-out/cache/semantic/45dbdf7ef5f77edb0624e3b58fecd5660a28cc16d80993f34c355aa0dfe5b8a3.json](graphify-out/cache/semantic/45dbdf7ef5f77edb0624e3b58fecd5660a28cc16d80993f34c355aa0dfe5b8a3.json) |  | 2026-07-08 | 674B | `decd564f` |
| [graphify-out/cache/semantic/45f0d01ebdccaa2d60f349f493f34b494a9aab33a078896a23be880bb1582d79.json](graphify-out/cache/semantic/45f0d01ebdccaa2d60f349f493f34b494a9aab33a078896a23be880bb1582d79.json) |  | 2026-07-08 | 1KB | `6eb415fe` |
| [graphify-out/cache/semantic/46661ff32d8e70739bf55b31aab0c1736a977a4aa637f667cb16b4a528c3aa25.json](graphify-out/cache/semantic/46661ff32d8e70739bf55b31aab0c1736a977a4aa637f667cb16b4a528c3aa25.json) |  | 2026-07-08 | 855B | `4c399e89` |
| [graphify-out/cache/semantic/46821a0db4ce6627e98443d023733a60e61dc8bf5b1b0c1c6468486c6848cc11.json](graphify-out/cache/semantic/46821a0db4ce6627e98443d023733a60e61dc8bf5b1b0c1c6468486c6848cc11.json) |  | 2026-07-08 | 704B | `1a99b260` |
| [graphify-out/cache/semantic/48360a9a2d5daad51e8b13c2cea763416dfd6ffefe328732621980e8012f87c9.json](graphify-out/cache/semantic/48360a9a2d5daad51e8b13c2cea763416dfd6ffefe328732621980e8012f87c9.json) |  | 2026-07-08 | 859B | `d64c35cf` |
| [graphify-out/cache/semantic/487f4addaed7b1ff55d0d706c33aa95cc48ebc861d11b01d68ca60cbd160b97b.json](graphify-out/cache/semantic/487f4addaed7b1ff55d0d706c33aa95cc48ebc861d11b01d68ca60cbd160b97b.json) |  | 2026-07-08 | 708B | `900c3da1` |
| [graphify-out/cache/semantic/498cf6819f649314e8cb056d33c849996903d1151888140d7bc4b568c5202a33.json](graphify-out/cache/semantic/498cf6819f649314e8cb056d33c849996903d1151888140d7bc4b568c5202a33.json) |  | 2026-07-08 | 404B | `0c52c54d` |
| [graphify-out/cache/semantic/4a17cdc92c80e0826158648b222de8df7ad3c31f0c8f6a1832bbe725adedba7e.json](graphify-out/cache/semantic/4a17cdc92c80e0826158648b222de8df7ad3c31f0c8f6a1832bbe725adedba7e.json) |  | 2026-07-08 | 1KB | `fcb8310c` |
| [graphify-out/cache/semantic/4a51e097c6557cc5b8a190aaeeb1cf467fc8ba540ee20f19a48f07d32194e79e.json](graphify-out/cache/semantic/4a51e097c6557cc5b8a190aaeeb1cf467fc8ba540ee20f19a48f07d32194e79e.json) |  | 2026-07-08 | 365B | `b0c4ad30` |
| [graphify-out/cache/semantic/4b1fc24593120b13c7870f68e04a05cc09e2e5eecce9d870b60b5552a81e7a92.json](graphify-out/cache/semantic/4b1fc24593120b13c7870f68e04a05cc09e2e5eecce9d870b60b5552a81e7a92.json) |  | 2026-07-08 | 1KB | `b1aab013` |
| [graphify-out/cache/semantic/4b937953b2304fdc4fff05af307b498f4aa258c2d5d937be53f1054c074b3af0.json](graphify-out/cache/semantic/4b937953b2304fdc4fff05af307b498f4aa258c2d5d937be53f1054c074b3af0.json) |  | 2026-07-08 | 1KB | `68ceb09f` |
| [graphify-out/cache/semantic/4cb700074adedbebfe9ddb0be1a5a679eb4962e4b64172a5afbc66aead593bbe.json](graphify-out/cache/semantic/4cb700074adedbebfe9ddb0be1a5a679eb4962e4b64172a5afbc66aead593bbe.json) |  | 2026-07-08 | 2KB | `d3babf7e` |
| [graphify-out/cache/semantic/4dbe791935fa03cc86d3105e32fed3ae58cc9f41306922d9e190e345ab617ee4.json](graphify-out/cache/semantic/4dbe791935fa03cc86d3105e32fed3ae58cc9f41306922d9e190e345ab617ee4.json) |  | 2026-07-08 | 2KB | `8dab2808` |
| [graphify-out/cache/semantic/4e245130721d864df834f48c7e88adc503ab4f7c7e9c572c684b461bb76d260d.json](graphify-out/cache/semantic/4e245130721d864df834f48c7e88adc503ab4f7c7e9c572c684b461bb76d260d.json) |  | 2026-07-08 | 401B | `e6a1c841` |
| [graphify-out/cache/semantic/4f9e014737e58d766c706313fd53ac5d510d3896c25dd119a3b2b568df9e3038.json](graphify-out/cache/semantic/4f9e014737e58d766c706313fd53ac5d510d3896c25dd119a3b2b568df9e3038.json) |  | 2026-07-08 | 834B | `41b204d1` |
| [graphify-out/cache/semantic/4fcaff4c57cc8305d02f3f9b412eae447afbcbc58beabf01013bac28cce64727.json](graphify-out/cache/semantic/4fcaff4c57cc8305d02f3f9b412eae447afbcbc58beabf01013bac28cce64727.json) |  | 2026-07-08 | 329B | `3d6b6ea4` |
| [graphify-out/cache/semantic/50d6d62265aceeac5dc866018f5cd1bc93ce97854fa2264ce9da93f395cb244f.json](graphify-out/cache/semantic/50d6d62265aceeac5dc866018f5cd1bc93ce97854fa2264ce9da93f395cb244f.json) |  | 2026-07-08 | 375B | `9f26c354` |
| [graphify-out/cache/semantic/50f5c1bc813215c4de23cbbeb4a4d0ca71d872406d1e271996c12f079ddab7e6.json](graphify-out/cache/semantic/50f5c1bc813215c4de23cbbeb4a4d0ca71d872406d1e271996c12f079ddab7e6.json) |  | 2026-07-08 | 794B | `ce93d2c6` |
| [graphify-out/cache/semantic/523d11271cdb44b02a37ac076cf600d4d1bc6993df8dfecfea6182b1044a01a9.json](graphify-out/cache/semantic/523d11271cdb44b02a37ac076cf600d4d1bc6993df8dfecfea6182b1044a01a9.json) |  | 2026-07-08 | 1KB | `c75eb405` |
| [graphify-out/cache/semantic/52a779c598464b0fcbf2cfe08d7fd474bc4ee50892c69add5ab7026265048f27.json](graphify-out/cache/semantic/52a779c598464b0fcbf2cfe08d7fd474bc4ee50892c69add5ab7026265048f27.json) |  | 2026-07-08 | 637B | `5ff880be` |
| [graphify-out/cache/semantic/5397ee5c5e87a877778d006b261c21120a018f92ce35e98e226996039ad06cc3.json](graphify-out/cache/semantic/5397ee5c5e87a877778d006b261c21120a018f92ce35e98e226996039ad06cc3.json) |  | 2026-07-08 | 1KB | `7f14b8b7` |
| [graphify-out/cache/semantic/53acd0afc1d0efc18ead95904ba914f480641dad5c10316aeb8917bc502048c3.json](graphify-out/cache/semantic/53acd0afc1d0efc18ead95904ba914f480641dad5c10316aeb8917bc502048c3.json) |  | 2026-07-08 | 1KB | `2068dc17` |
| [graphify-out/cache/semantic/54e15a9e328b88a8a85d08433685141bad2c2cd6e58bdf9746d77f9399bf7476.json](graphify-out/cache/semantic/54e15a9e328b88a8a85d08433685141bad2c2cd6e58bdf9746d77f9399bf7476.json) |  | 2026-07-08 | 2KB | `2ef58719` |
| [graphify-out/cache/semantic/55950d7cb4960d37fc48d0c96dce7529e484a0c7d6e193c3f214737394e9dbd8.json](graphify-out/cache/semantic/55950d7cb4960d37fc48d0c96dce7529e484a0c7d6e193c3f214737394e9dbd8.json) |  | 2026-07-08 | 613B | `70218e8b` |
| [graphify-out/cache/semantic/5617c4163e39cc32ef723d7d56ea536bb40f823587d7fda1a55549720b83ed29.json](graphify-out/cache/semantic/5617c4163e39cc32ef723d7d56ea536bb40f823587d7fda1a55549720b83ed29.json) |  | 2026-07-08 | 909B | `8e50dbff` |
| [graphify-out/cache/semantic/56ac3eaf6ec26c38e442a75afae91ad2e6f6d9f84187a36f4cc4e879bebfb38b.json](graphify-out/cache/semantic/56ac3eaf6ec26c38e442a75afae91ad2e6f6d9f84187a36f4cc4e879bebfb38b.json) |  | 2026-07-08 | 862B | `659ebce2` |
| [graphify-out/cache/semantic/56d406ea5801e4db4da447bf6b17ffc9030211a67c16293acfd7e0e2b56c3b6a.json](graphify-out/cache/semantic/56d406ea5801e4db4da447bf6b17ffc9030211a67c16293acfd7e0e2b56c3b6a.json) |  | 2026-07-08 | 1KB | `1f498371` |
| [graphify-out/cache/semantic/56dff6e3d62cbd54e11e90cf883404e45d2536fd5b7cd1bec9b0f8a563ba7c7b.json](graphify-out/cache/semantic/56dff6e3d62cbd54e11e90cf883404e45d2536fd5b7cd1bec9b0f8a563ba7c7b.json) |  | 2026-07-08 | 991B | `2581c16f` |
| [graphify-out/cache/semantic/5801dd603326e0386a55f151a97a32b9e1a9d507cb45f931ca1f4947dadb450b.json](graphify-out/cache/semantic/5801dd603326e0386a55f151a97a32b9e1a9d507cb45f931ca1f4947dadb450b.json) |  | 2026-07-08 | 775B | `9c963534` |
| [graphify-out/cache/semantic/58437c093902a91b29bc8b06c06a2a0ec8bf1d274a02dd517a75043234b4379f.json](graphify-out/cache/semantic/58437c093902a91b29bc8b06c06a2a0ec8bf1d274a02dd517a75043234b4379f.json) |  | 2026-07-08 | 1017B | `44fcd1ee` |
| [graphify-out/cache/semantic/5846667bbee654d6fa0faa19a5ecb52d44b7bbb2af61ec02e19f42de8c662643.json](graphify-out/cache/semantic/5846667bbee654d6fa0faa19a5ecb52d44b7bbb2af61ec02e19f42de8c662643.json) |  | 2026-07-08 | 1KB | `46d57d32` |
| [graphify-out/cache/semantic/585e3475707dff921e1ffeb9f9446e7e104c8ca191d88aa590ca45e634ac28e0.json](graphify-out/cache/semantic/585e3475707dff921e1ffeb9f9446e7e104c8ca191d88aa590ca45e634ac28e0.json) |  | 2026-07-08 | 1KB | `2496eb7b` |
| [graphify-out/cache/semantic/585ed3079e593ff0d71553848c76de5508b032010ce90dcd08609f670bd68763.json](graphify-out/cache/semantic/585ed3079e593ff0d71553848c76de5508b032010ce90dcd08609f670bd68763.json) |  | 2026-07-08 | 525B | `64d852d2` |
| [graphify-out/cache/semantic/5b2cca1ba0dce2f2044d8043eb264155bbc2f36f54b97f5ce85d994c6dd66d00.json](graphify-out/cache/semantic/5b2cca1ba0dce2f2044d8043eb264155bbc2f36f54b97f5ce85d994c6dd66d00.json) |  | 2026-07-08 | 3KB | `d3389686` |
| [graphify-out/cache/semantic/5b72acd11e9926d8aa52b79ea10b3cc51ccaff10fb649af27cd54ff5b37a0649.json](graphify-out/cache/semantic/5b72acd11e9926d8aa52b79ea10b3cc51ccaff10fb649af27cd54ff5b37a0649.json) |  | 2026-07-08 | 927B | `15316820` |
| [graphify-out/cache/semantic/5bb46c3dbc51d32468d3b44ae24f597c45527b6f40772117011b8e66f043d2ca.json](graphify-out/cache/semantic/5bb46c3dbc51d32468d3b44ae24f597c45527b6f40772117011b8e66f043d2ca.json) |  | 2026-07-08 | 1KB | `6b6b2bbf` |
| [graphify-out/cache/semantic/5c2fa6a5da873a9dc3affb85d3e5d280d0093f5b7199e2e79457b25d2dce7e16.json](graphify-out/cache/semantic/5c2fa6a5da873a9dc3affb85d3e5d280d0093f5b7199e2e79457b25d2dce7e16.json) |  | 2026-07-08 | 527B | `9ed6c909` |
| [graphify-out/cache/semantic/5cc188cdb378380cbd30dc99729a6d14b6210cef7568795d0cc2ed524fccc1fe.json](graphify-out/cache/semantic/5cc188cdb378380cbd30dc99729a6d14b6210cef7568795d0cc2ed524fccc1fe.json) |  | 2026-07-08 | 609B | `7a8dbab1` |
| [graphify-out/cache/semantic/5ce6b633e69c50faaa48241b82db9e89fc416ba77f67f8b33c41f4479fa1036a.json](graphify-out/cache/semantic/5ce6b633e69c50faaa48241b82db9e89fc416ba77f67f8b33c41f4479fa1036a.json) |  | 2026-07-08 | 1KB | `6778feb8` |
| [graphify-out/cache/semantic/5d105bdb543c3dbd537460d0e097d5488517ab0a21e0e1e520513f43670b95f1.json](graphify-out/cache/semantic/5d105bdb543c3dbd537460d0e097d5488517ab0a21e0e1e520513f43670b95f1.json) |  | 2026-07-08 | 414B | `8a101bad` |
| [graphify-out/cache/semantic/5df11efcf8155016a490d81626e8f203c1bc586d3b817920bde7c7980e94f8c1.json](graphify-out/cache/semantic/5df11efcf8155016a490d81626e8f203c1bc586d3b817920bde7c7980e94f8c1.json) |  | 2026-07-08 | 344B | `993979d8` |
| [graphify-out/cache/semantic/608d8b06105945f65f29048fbabf9682e2a7684cd402d79a5834900efbb49f67.json](graphify-out/cache/semantic/608d8b06105945f65f29048fbabf9682e2a7684cd402d79a5834900efbb49f67.json) |  | 2026-07-08 | 253B | `56fddc2f` |
| [graphify-out/cache/semantic/616adb19748f0341339920c9d03b0eca9df6332fd354f4acd7661b7e15ac67b4.json](graphify-out/cache/semantic/616adb19748f0341339920c9d03b0eca9df6332fd354f4acd7661b7e15ac67b4.json) |  | 2026-07-08 | 1KB | `7ea3533b` |
| [graphify-out/cache/semantic/61c2fe4c1400f452ae556c26cbd3676432d47b2ce77f0ad57a09cd2144ad61a3.json](graphify-out/cache/semantic/61c2fe4c1400f452ae556c26cbd3676432d47b2ce77f0ad57a09cd2144ad61a3.json) |  | 2026-07-08 | 353B | `69b8655b` |
| [graphify-out/cache/semantic/61e77ce7f62d7a73fc62e40338ed026706c732e8503d82d72e14cc01e0e8b47d.json](graphify-out/cache/semantic/61e77ce7f62d7a73fc62e40338ed026706c732e8503d82d72e14cc01e0e8b47d.json) |  | 2026-07-08 | 1KB | `4eb5a1bf` |
| [graphify-out/cache/semantic/6214ae76a414f3f30e1d7fe60ef275c13c6cd245d40f1f9f4d836723fa4c1139.json](graphify-out/cache/semantic/6214ae76a414f3f30e1d7fe60ef275c13c6cd245d40f1f9f4d836723fa4c1139.json) |  | 2026-07-08 | 619B | `5c767a1b` |
| [graphify-out/cache/semantic/6275e90b2d5bc964eca193312233a9aaadc4d6d32a83d7caeb3bf35bf362817d.json](graphify-out/cache/semantic/6275e90b2d5bc964eca193312233a9aaadc4d6d32a83d7caeb3bf35bf362817d.json) |  | 2026-07-08 | 642B | `a90c09f8` |
| [graphify-out/cache/semantic/62c3cf8c7038a6b3653baa63a71d47b5fdbf7e15b002e876247faebd6ace4270.json](graphify-out/cache/semantic/62c3cf8c7038a6b3653baa63a71d47b5fdbf7e15b002e876247faebd6ace4270.json) |  | 2026-07-08 | 705B | `cd951f81` |
| [graphify-out/cache/semantic/64063edb67184b66002b946d216d1e3f2a6417231d0514e4134cbc9a83173a7f.json](graphify-out/cache/semantic/64063edb67184b66002b946d216d1e3f2a6417231d0514e4134cbc9a83173a7f.json) |  | 2026-07-08 | 772B | `a00561d6` |
| [graphify-out/cache/semantic/6416c59e93774dcd2dc49e6360444599d737ee6c092d79c635a5c65ded064ea9.json](graphify-out/cache/semantic/6416c59e93774dcd2dc49e6360444599d737ee6c092d79c635a5c65ded064ea9.json) |  | 2026-07-08 | 1KB | `481c6a1b` |
| [graphify-out/cache/semantic/643cc4ffe27c6856de2fd41f7326872a3232fcf6c21708efd2b078ae2ba410e9.json](graphify-out/cache/semantic/643cc4ffe27c6856de2fd41f7326872a3232fcf6c21708efd2b078ae2ba410e9.json) |  | 2026-07-08 | 527B | `7fa6da59` |
| [graphify-out/cache/semantic/64d0c76070200c467b7c5adb850f509e00c75c1a3f69fb12556d92015b403db6.json](graphify-out/cache/semantic/64d0c76070200c467b7c5adb850f509e00c75c1a3f69fb12556d92015b403db6.json) |  | 2026-07-08 | 1KB | `c3dfe696` |
| [graphify-out/cache/semantic/655da4a54f3e8e565e841df59e9c0e1f956f50d15974baf8a4a6319918216ced.json](graphify-out/cache/semantic/655da4a54f3e8e565e841df59e9c0e1f956f50d15974baf8a4a6319918216ced.json) |  | 2026-07-08 | 1KB | `3c0e87eb` |
| [graphify-out/cache/semantic/65d507b234fc41a165f04499e95d2fbe3312e821a85b60ebaaded384eb12f02c.json](graphify-out/cache/semantic/65d507b234fc41a165f04499e95d2fbe3312e821a85b60ebaaded384eb12f02c.json) |  | 2026-07-08 | 1KB | `68abf892` |
| [graphify-out/cache/semantic/66375d86e06b5aff6c3e80aeb9dc0ba68a2b86ad7e37417c83fa56b9e55f17c8.json](graphify-out/cache/semantic/66375d86e06b5aff6c3e80aeb9dc0ba68a2b86ad7e37417c83fa56b9e55f17c8.json) |  | 2026-07-08 | 626B | `37c660e8` |
| [graphify-out/cache/semantic/66e30844e1693ae1a4a826e79ac67b77f8fe6d77d12fbf030a679e480b1cbed5.json](graphify-out/cache/semantic/66e30844e1693ae1a4a826e79ac67b77f8fe6d77d12fbf030a679e480b1cbed5.json) |  | 2026-07-08 | 451B | `ae35a6b0` |
| [graphify-out/cache/semantic/677d62db8f0cbb5175598707950ffff428483c73c1e21b0ffb77e378d51f9d8c.json](graphify-out/cache/semantic/677d62db8f0cbb5175598707950ffff428483c73c1e21b0ffb77e378d51f9d8c.json) |  | 2026-07-08 | 380B | `f18f4fca` |
| [graphify-out/cache/semantic/67be740985d7b214d2a4164130dff4b31cd8640f9b2776f5c09e9bad18221e72.json](graphify-out/cache/semantic/67be740985d7b214d2a4164130dff4b31cd8640f9b2776f5c09e9bad18221e72.json) |  | 2026-07-08 | 1KB | `a00c8fd7` |
| [graphify-out/cache/semantic/68f0a5e9d11a5051fc9da33403f949c012f94af60071ec76ddbf9ca69d88d033.json](graphify-out/cache/semantic/68f0a5e9d11a5051fc9da33403f949c012f94af60071ec76ddbf9ca69d88d033.json) |  | 2026-07-08 | 3KB | `7e882998` |
| [graphify-out/cache/semantic/68ff5ac03917dc11a70ddf09b0b8ed2b73fc566163859162f0f4490a7bcc414f.json](graphify-out/cache/semantic/68ff5ac03917dc11a70ddf09b0b8ed2b73fc566163859162f0f4490a7bcc414f.json) |  | 2026-07-08 | 344B | `3a83f21e` |
| [graphify-out/cache/semantic/69564116aa39838dd9a59dc1edb637c2e1d2abfdfcbd62687c9dae6fe6ac31ed.json](graphify-out/cache/semantic/69564116aa39838dd9a59dc1edb637c2e1d2abfdfcbd62687c9dae6fe6ac31ed.json) |  | 2026-07-08 | 781B | `04864607` |
| [graphify-out/cache/semantic/6addd8690b5536652c48185a5af6676e17b806722c7c8601f44fb8c515c2b60c.json](graphify-out/cache/semantic/6addd8690b5536652c48185a5af6676e17b806722c7c8601f44fb8c515c2b60c.json) |  | 2026-07-08 | 326B | `d6f9349c` |
| [graphify-out/cache/semantic/6b1d2f3f6f0f7149e0627a874c47f0cfe4817d489a19e362ff99e899a5209587.json](graphify-out/cache/semantic/6b1d2f3f6f0f7149e0627a874c47f0cfe4817d489a19e362ff99e899a5209587.json) |  | 2026-07-08 | 1KB | `f109a6d1` |
| [graphify-out/cache/semantic/6c42954c70832804591708bdc80fb56d1ea62cec299824f62ec8ef613506a430.json](graphify-out/cache/semantic/6c42954c70832804591708bdc80fb56d1ea62cec299824f62ec8ef613506a430.json) |  | 2026-07-08 | 1KB | `c684cd8a` |
| [graphify-out/cache/semantic/6d3ea2a20ff35c5b15c4e288ed7b21c1ac84cd4615f006fce440297503e74714.json](graphify-out/cache/semantic/6d3ea2a20ff35c5b15c4e288ed7b21c1ac84cd4615f006fce440297503e74714.json) |  | 2026-07-08 | 713B | `58900289` |
| [graphify-out/cache/semantic/6e5588b5ed974d05d9308594fc162fad11bcf47165c190380f3d4a21ddf6ba08.json](graphify-out/cache/semantic/6e5588b5ed974d05d9308594fc162fad11bcf47165c190380f3d4a21ddf6ba08.json) |  | 2026-07-08 | 1KB | `051269eb` |
| [graphify-out/cache/semantic/6fd8a07078fdf93f11abcb2513e16dcc725d049fc8d0bad63bf90c42c5bf682f.json](graphify-out/cache/semantic/6fd8a07078fdf93f11abcb2513e16dcc725d049fc8d0bad63bf90c42c5bf682f.json) |  | 2026-07-08 | 340B | `4bb8abeb` |
| [graphify-out/cache/semantic/70dbab2b1670c39d1be5ce14addf50dafc951b1a7990b2a727713ebd93ccdcb9.json](graphify-out/cache/semantic/70dbab2b1670c39d1be5ce14addf50dafc951b1a7990b2a727713ebd93ccdcb9.json) |  | 2026-07-08 | 2KB | `20345a30` |
| [graphify-out/cache/semantic/70fd302152490fdf9f412dd777b20563d31fd3468814a549f1e2fdd1c8e346d3.json](graphify-out/cache/semantic/70fd302152490fdf9f412dd777b20563d31fd3468814a549f1e2fdd1c8e346d3.json) |  | 2026-07-08 | 649B | `ee6710c8` |
| [graphify-out/cache/semantic/7124c3e16b510c848773846f0ce4aa59432fae68450bf8677816e0b46830fc38.json](graphify-out/cache/semantic/7124c3e16b510c848773846f0ce4aa59432fae68450bf8677816e0b46830fc38.json) |  | 2026-07-08 | 879B | `b800aea2` |
| [graphify-out/cache/semantic/7168a20fa9e39d4cc108567577e96d20e975952c264eebde2cd6b29dd51ababa.json](graphify-out/cache/semantic/7168a20fa9e39d4cc108567577e96d20e975952c264eebde2cd6b29dd51ababa.json) |  | 2026-07-08 | 1KB | `c2df11b7` |
| [graphify-out/cache/semantic/71f1c9e976e9874354abacb839829d13e17ba2a25bd1cb8989aeafd72f98f1dd.json](graphify-out/cache/semantic/71f1c9e976e9874354abacb839829d13e17ba2a25bd1cb8989aeafd72f98f1dd.json) |  | 2026-07-08 | 395B | `cb3bbe01` |
| [graphify-out/cache/semantic/72436d23f51c96c5213ed5fb119f2ca4d1bd3efe173a36969046329e247e2b69.json](graphify-out/cache/semantic/72436d23f51c96c5213ed5fb119f2ca4d1bd3efe173a36969046329e247e2b69.json) |  | 2026-07-08 | 607B | `8978f653` |
| [graphify-out/cache/semantic/72f9bdb4f57952e3857f261d2ebac6c81801bb425acb66ebcf054d4e5ef04262.json](graphify-out/cache/semantic/72f9bdb4f57952e3857f261d2ebac6c81801bb425acb66ebcf054d4e5ef04262.json) |  | 2026-07-08 | 1KB | `eca8eebd` |
| [graphify-out/cache/semantic/73587895287a77d7b7a21ac1b7e7b580c550f7c10ad11fc87514c107f8d6d18f.json](graphify-out/cache/semantic/73587895287a77d7b7a21ac1b7e7b580c550f7c10ad11fc87514c107f8d6d18f.json) |  | 2026-07-08 | 1KB | `6736485c` |
| [graphify-out/cache/semantic/73e5a20ca0b7627f8d3fdd43380ef4022a7194e36a48e46f55ecb823a1b69bff.json](graphify-out/cache/semantic/73e5a20ca0b7627f8d3fdd43380ef4022a7194e36a48e46f55ecb823a1b69bff.json) |  | 2026-07-08 | 344B | `0051f487` |
| [graphify-out/cache/semantic/7428a62b11eaeae394a4f719c4dcb13d9fc19be775aa881fdbb77e182779662b.json](graphify-out/cache/semantic/7428a62b11eaeae394a4f719c4dcb13d9fc19be775aa881fdbb77e182779662b.json) |  | 2026-07-08 | 356B | `cc0f9acd` |
| [graphify-out/cache/semantic/742e1196e7120fed081bc39b6a01c4a7c5fbaa4e8b7601a067eb7f75f365d2f5.json](graphify-out/cache/semantic/742e1196e7120fed081bc39b6a01c4a7c5fbaa4e8b7601a067eb7f75f365d2f5.json) |  | 2026-07-08 | 326B | `1999a361` |
| [graphify-out/cache/semantic/7552c835677f900ba4372b535fb7fcd3065b07762b483097e365a8a0e0f1f8d2.json](graphify-out/cache/semantic/7552c835677f900ba4372b535fb7fcd3065b07762b483097e365a8a0e0f1f8d2.json) |  | 2026-07-08 | 329B | `4f08b95f` |
| [graphify-out/cache/semantic/75aa6781e15ca5648b3d5485df5c74710d8c6c46042a0e31a0cedb97ea2ba7a1.json](graphify-out/cache/semantic/75aa6781e15ca5648b3d5485df5c74710d8c6c46042a0e31a0cedb97ea2ba7a1.json) |  | 2026-07-08 | 265B | `ee22f5ec` |
| [graphify-out/cache/semantic/761cde20f620fc4599206c68a35f59fd3472e3f74fc578a8cdf1be497e15ba90.json](graphify-out/cache/semantic/761cde20f620fc4599206c68a35f59fd3472e3f74fc578a8cdf1be497e15ba90.json) |  | 2026-07-08 | 785B | `62b03dbd` |
| [graphify-out/cache/semantic/767660e7fdecfb6f64edd2e65f4656bceafc0ac2a581a3e3076be83cc388e853.json](graphify-out/cache/semantic/767660e7fdecfb6f64edd2e65f4656bceafc0ac2a581a3e3076be83cc388e853.json) |  | 2026-07-08 | 323B | `d37384e3` |
| [graphify-out/cache/semantic/76dc2834c8c379b37b01c1f913ed466cf8ceacd219d4d1ae775dc1bce5d348e7.json](graphify-out/cache/semantic/76dc2834c8c379b37b01c1f913ed466cf8ceacd219d4d1ae775dc1bce5d348e7.json) |  | 2026-07-08 | 394B | `39c22b12` |
| [graphify-out/cache/semantic/77bc7c48bfd38293dcf180a9af75a272774f4a995178ce98af2dc110d1e5d190.json](graphify-out/cache/semantic/77bc7c48bfd38293dcf180a9af75a272774f4a995178ce98af2dc110d1e5d190.json) |  | 2026-07-08 | 1KB | `ad2519f8` |
| [graphify-out/cache/semantic/7a62b6972598bef4db954eb30f867b1888f8badd87f28de1d46290d8c42ac228.json](graphify-out/cache/semantic/7a62b6972598bef4db954eb30f867b1888f8badd87f28de1d46290d8c42ac228.json) |  | 2026-07-08 | 308B | `2a8cc2e2` |
| [graphify-out/cache/semantic/7b4802f9d1a7617a227608d514b1be307d9eaabab967ca766303eb5da7531cc3.json](graphify-out/cache/semantic/7b4802f9d1a7617a227608d514b1be307d9eaabab967ca766303eb5da7531cc3.json) |  | 2026-07-08 | 358B | `a0645179` |
| [graphify-out/cache/semantic/7c0a138520f75361f6235181ccf17f610ab459184341c20bec89badfa2b4a8a2.json](graphify-out/cache/semantic/7c0a138520f75361f6235181ccf17f610ab459184341c20bec89badfa2b4a8a2.json) |  | 2026-07-08 | 824B | `c168a772` |
| [graphify-out/cache/semantic/7c73f2d308aaf0858d4b119bc04351456aca5250ca49138bd36f06ed14130446.json](graphify-out/cache/semantic/7c73f2d308aaf0858d4b119bc04351456aca5250ca49138bd36f06ed14130446.json) |  | 2026-07-08 | 344B | `b557f1e3` |
| [graphify-out/cache/semantic/7ca887e23f47a525c7559c605735843550183ba8d9f962c7309480a17d6c0bf5.json](graphify-out/cache/semantic/7ca887e23f47a525c7559c605735843550183ba8d9f962c7309480a17d6c0bf5.json) |  | 2026-07-08 | 1KB | `ddb77ba7` |
| [graphify-out/cache/semantic/7ce0aab7c23207cec32402edf8cfa07ad49acce11af3a881022db5d7d17b718b.json](graphify-out/cache/semantic/7ce0aab7c23207cec32402edf8cfa07ad49acce11af3a881022db5d7d17b718b.json) |  | 2026-07-08 | 392B | `f67c3e19` |
| [graphify-out/cache/semantic/7e2f93cf65b430ad1887352bc1dbab3ca814c0a3964a921bd0b5a495f4c29871.json](graphify-out/cache/semantic/7e2f93cf65b430ad1887352bc1dbab3ca814c0a3964a921bd0b5a495f4c29871.json) |  | 2026-07-08 | 1KB | `30703685` |
| [graphify-out/cache/semantic/7f5621986543842bb815598b12e18925d0be22951771313cec04f36482bd876d.json](graphify-out/cache/semantic/7f5621986543842bb815598b12e18925d0be22951771313cec04f36482bd876d.json) |  | 2026-07-08 | 1KB | `9c3be863` |
| [graphify-out/cache/semantic/7fcedcfb96e79baf9aa3feb5d477af71ec2795a16620a3bceb69214abf13e7cf.json](graphify-out/cache/semantic/7fcedcfb96e79baf9aa3feb5d477af71ec2795a16620a3bceb69214abf13e7cf.json) |  | 2026-07-08 | 246B | `ce6ef6db` |
| [graphify-out/cache/semantic/814599ac1df60e66659901d8f86293fbe926a4aebcef132ee7a23057e02d5043.json](graphify-out/cache/semantic/814599ac1df60e66659901d8f86293fbe926a4aebcef132ee7a23057e02d5043.json) |  | 2026-07-08 | 397B | `8501ca3e` |
| [graphify-out/cache/semantic/818953521b6105ae152520604c0bfd27a6c6b2dd0e94ba66a2aec883a53b42bd.json](graphify-out/cache/semantic/818953521b6105ae152520604c0bfd27a6c6b2dd0e94ba66a2aec883a53b42bd.json) |  | 2026-07-08 | 326B | `3c0ddc3b` |
| [graphify-out/cache/semantic/82d555f3be67a8e3e6cec71e819c503b07c39bee417ccbd4e1017df98be82143.json](graphify-out/cache/semantic/82d555f3be67a8e3e6cec71e819c503b07c39bee417ccbd4e1017df98be82143.json) |  | 2026-07-08 | 369B | `27a88039` |
| [graphify-out/cache/semantic/82e7756eef30a3ed4baf1b70f9c07666cba11891fa19d1eaeb5dda9208ca97c6.json](graphify-out/cache/semantic/82e7756eef30a3ed4baf1b70f9c07666cba11891fa19d1eaeb5dda9208ca97c6.json) |  | 2026-07-08 | 418B | `845903df` |
| [graphify-out/cache/semantic/84fa2683086e58761eec0f656b51adc0c48e16157eb3901b55eab507149d2fcf.json](graphify-out/cache/semantic/84fa2683086e58761eec0f656b51adc0c48e16157eb3901b55eab507149d2fcf.json) |  | 2026-07-08 | 329B | `b8a03c87` |
| [graphify-out/cache/semantic/85578e618706bb1c3ac24225c7aca13da60f84bf298ee7f4c77291c99bc088dc.json](graphify-out/cache/semantic/85578e618706bb1c3ac24225c7aca13da60f84bf298ee7f4c77291c99bc088dc.json) |  | 2026-07-08 | 1KB | `01c9356d` |
| [graphify-out/cache/semantic/86e7c16f45ac1e8d09b9facd1b117f7936570d3adcfe8da89690420f2b988389.json](graphify-out/cache/semantic/86e7c16f45ac1e8d09b9facd1b117f7936570d3adcfe8da89690420f2b988389.json) |  | 2026-07-08 | 849B | `c152a03b` |
| [graphify-out/cache/semantic/887b40c370bcc194a1aa69a2b45522c5241dc02900bd9dafc6b93d24c7502ffb.json](graphify-out/cache/semantic/887b40c370bcc194a1aa69a2b45522c5241dc02900bd9dafc6b93d24c7502ffb.json) |  | 2026-07-08 | 653B | `97cd9635` |
| [graphify-out/cache/semantic/8927a41b7b5798d2fc0ab9a522d5acb83d1bda932cc2ba6e735e4beca85d23ef.json](graphify-out/cache/semantic/8927a41b7b5798d2fc0ab9a522d5acb83d1bda932cc2ba6e735e4beca85d23ef.json) |  | 2026-07-08 | 751B | `e2cbece2` |
| [graphify-out/cache/semantic/89685557e0148cc3bb0c3da60399f9cc1282bf3f99199c0f11d808f3fc6dda13.json](graphify-out/cache/semantic/89685557e0148cc3bb0c3da60399f9cc1282bf3f99199c0f11d808f3fc6dda13.json) |  | 2026-07-08 | 761B | `e48f8625` |
| [graphify-out/cache/semantic/89709fde7917f4861930f695e12cc0a4bb929ea077bd01ca7239fc3133a56149.json](graphify-out/cache/semantic/89709fde7917f4861930f695e12cc0a4bb929ea077bd01ca7239fc3133a56149.json) |  | 2026-07-08 | 816B | `900cec67` |
| [graphify-out/cache/semantic/89bdbe6e1807a4facaa2addcfddb3311588c47e8bc2bf2d58faf8de3d0e9db92.json](graphify-out/cache/semantic/89bdbe6e1807a4facaa2addcfddb3311588c47e8bc2bf2d58faf8de3d0e9db92.json) |  | 2026-07-08 | 361B | `8fe9d331` |
| [graphify-out/cache/semantic/8ae2881daabb96a8ba72e39563f0276f41f70055836e01f8d2a8991c5160af19.json](graphify-out/cache/semantic/8ae2881daabb96a8ba72e39563f0276f41f70055836e01f8d2a8991c5160af19.json) |  | 2026-07-08 | 344B | `02fa4f0c` |
| [graphify-out/cache/semantic/8cd9da22d9e223b4d0a140a6a27f3b2982c2b5a106107ee10a72a4d678cb875e.json](graphify-out/cache/semantic/8cd9da22d9e223b4d0a140a6a27f3b2982c2b5a106107ee10a72a4d678cb875e.json) |  | 2026-07-08 | 611B | `21b45581` |
| [graphify-out/cache/semantic/8dca267f36313cd9fcfeadfcfb8728edf4953de6c4a214776d55adf71540d6a8.json](graphify-out/cache/semantic/8dca267f36313cd9fcfeadfcfb8728edf4953de6c4a214776d55adf71540d6a8.json) |  | 2026-07-08 | 655B | `580324b8` |
| [graphify-out/cache/semantic/8e3f7f6cf8a3672c537b5fff456d52a3659f2ff67a382f061d1467cceab90764.json](graphify-out/cache/semantic/8e3f7f6cf8a3672c537b5fff456d52a3659f2ff67a382f061d1467cceab90764.json) |  | 2026-07-08 | 797B | `27cd80ad` |
| [graphify-out/cache/semantic/8e54284f20f1284ed644af53c7bfbed1b0f1ce66859e98b6a041a50895b97f04.json](graphify-out/cache/semantic/8e54284f20f1284ed644af53c7bfbed1b0f1ce66859e98b6a041a50895b97f04.json) |  | 2026-07-08 | 824B | `796ea507` |
| [graphify-out/cache/semantic/8e86ebe411806efd945d4ce5cedec0ce0f4805ad36f32e14e2a41b5a81c62305.json](graphify-out/cache/semantic/8e86ebe411806efd945d4ce5cedec0ce0f4805ad36f32e14e2a41b5a81c62305.json) |  | 2026-07-08 | 2KB | `bf4e5f53` |
| [graphify-out/cache/semantic/8f01747530af98bb27ff2d7c6881614850cbdbc6e77d5fc6335866bdf3204253.json](graphify-out/cache/semantic/8f01747530af98bb27ff2d7c6881614850cbdbc6e77d5fc6335866bdf3204253.json) |  | 2026-07-08 | 1KB | `9d62d204` |
| [graphify-out/cache/semantic/8f0c7649e27191cf742328b3b93dfb9fe4ed3834f0e98dded496ca6a1fc575f4.json](graphify-out/cache/semantic/8f0c7649e27191cf742328b3b93dfb9fe4ed3834f0e98dded496ca6a1fc575f4.json) |  | 2026-07-08 | 2KB | `75a10a2a` |
| [graphify-out/cache/semantic/8f6adb19dafcd75ed2347f4c2232d7d6d078055aaf6c13895ea52eb7c06359c9.json](graphify-out/cache/semantic/8f6adb19dafcd75ed2347f4c2232d7d6d078055aaf6c13895ea52eb7c06359c9.json) |  | 2026-07-08 | 419B | `52ec2cf8` |
| [graphify-out/cache/semantic/8f95a3ef77156ec0e7b2a8b71911d7d534979978957a256802b583536f77ea8a.json](graphify-out/cache/semantic/8f95a3ef77156ec0e7b2a8b71911d7d534979978957a256802b583536f77ea8a.json) |  | 2026-07-08 | 1KB | `d3c466b4` |
| [graphify-out/cache/semantic/8f9fc4e845002ac96188ced2bbb385eda0b830b4d22c7bcd2a4a56c593b07c72.json](graphify-out/cache/semantic/8f9fc4e845002ac96188ced2bbb385eda0b830b4d22c7bcd2a4a56c593b07c72.json) |  | 2026-07-08 | 293B | `e889f041` |
| [graphify-out/cache/semantic/8fbe9bcf16454ee43a7dd6c0dfa40518d29e025a9a57c817c0dab7a5b6c1d0bb.json](graphify-out/cache/semantic/8fbe9bcf16454ee43a7dd6c0dfa40518d29e025a9a57c817c0dab7a5b6c1d0bb.json) |  | 2026-07-08 | 3KB | `5a2c687a` |
| [graphify-out/cache/semantic/8ffc43198df59470d7b0c28ab93a09a79f717c6a08899c6450e66018b5b14f64.json](graphify-out/cache/semantic/8ffc43198df59470d7b0c28ab93a09a79f717c6a08899c6450e66018b5b14f64.json) |  | 2026-07-08 | 365B | `7c4db2e2` |
| [graphify-out/cache/semantic/90a3ab3530352846c0431174d4186a12fc95e27c5c47ac316f76c859bd150888.json](graphify-out/cache/semantic/90a3ab3530352846c0431174d4186a12fc95e27c5c47ac316f76c859bd150888.json) |  | 2026-07-08 | 1KB | `e522bddd` |
| [graphify-out/cache/semantic/90af4ad04e6ead498a0b35346c4add2071b668b4d03527e5a318ba370024d295.json](graphify-out/cache/semantic/90af4ad04e6ead498a0b35346c4add2071b668b4d03527e5a318ba370024d295.json) |  | 2026-07-08 | 290B | `48e9b1f4` |
| [graphify-out/cache/semantic/90dfaaad457e938a3289069ca9af10ef919a2371333fd8fe238cb4bffea32196.json](graphify-out/cache/semantic/90dfaaad457e938a3289069ca9af10ef919a2371333fd8fe238cb4bffea32196.json) |  | 2026-07-08 | 494B | `b36e5019` |
| [graphify-out/cache/semantic/90e00f3cdb0d49c67231d2b5739f662f12a42aaa217a35896e2c0f597c7dc485.json](graphify-out/cache/semantic/90e00f3cdb0d49c67231d2b5739f662f12a42aaa217a35896e2c0f597c7dc485.json) |  | 2026-07-08 | 365B | `76d95f0e` |
| [graphify-out/cache/semantic/90e155cda2ffbead2f9e24f6bac8729f620871a55e93ab721026eb92a32f0d3c.json](graphify-out/cache/semantic/90e155cda2ffbead2f9e24f6bac8729f620871a55e93ab721026eb92a32f0d3c.json) |  | 2026-07-08 | 428B | `b7c80a16` |
| [graphify-out/cache/semantic/91306b430611c721a240550d83423a8b922b828b669e7fd0a418bc7decad255d.json](graphify-out/cache/semantic/91306b430611c721a240550d83423a8b922b828b669e7fd0a418bc7decad255d.json) |  | 2026-07-08 | 311B | `ffa6f69d` |
| [graphify-out/cache/semantic/930f6bf4c0cd42438c05d16802541140f72d1bc579f3bbba8d99f46952bdf6d1.json](graphify-out/cache/semantic/930f6bf4c0cd42438c05d16802541140f72d1bc579f3bbba8d99f46952bdf6d1.json) |  | 2026-07-08 | 698B | `5c8f1b81` |
| [graphify-out/cache/semantic/935a01d351cf42cf1d7a44552f22731ac47ca3badcbe333a43ade5ca35a5c31e.json](graphify-out/cache/semantic/935a01d351cf42cf1d7a44552f22731ac47ca3badcbe333a43ade5ca35a5c31e.json) |  | 2026-07-08 | 402B | `6dab8b60` |
| [graphify-out/cache/semantic/93b06036c8ab07c2de010db9c42088ad30cee51bf307b6fc74688ec7c676b993.json](graphify-out/cache/semantic/93b06036c8ab07c2de010db9c42088ad30cee51bf307b6fc74688ec7c676b993.json) |  | 2026-07-08 | 318B | `177f68d3` |
| [graphify-out/cache/semantic/940c508d0acc7b056b0fe353f0d606f0ee59c3ba6cdc0fa6fb2bedd7c7c2a9d3.json](graphify-out/cache/semantic/940c508d0acc7b056b0fe353f0d606f0ee59c3ba6cdc0fa6fb2bedd7c7c2a9d3.json) |  | 2026-07-08 | 415B | `1ccf541d` |
| [graphify-out/cache/semantic/94126eadb201eebdf55ee29ba7cec4eafbdfeb7b59f054ed81699ed326bb8dea.json](graphify-out/cache/semantic/94126eadb201eebdf55ee29ba7cec4eafbdfeb7b59f054ed81699ed326bb8dea.json) |  | 2026-07-08 | 729B | `cf83622f` |
| [graphify-out/cache/semantic/9628b466d2b0c2113df74882298164147325cd09f13d1e30d3e00d54826cf57d.json](graphify-out/cache/semantic/9628b466d2b0c2113df74882298164147325cd09f13d1e30d3e00d54826cf57d.json) |  | 2026-07-08 | 384B | `141569ab` |
| [graphify-out/cache/semantic/988301b60a14dedf01e918ffde291794e3a7831ab84bcebc3bf2f9046c9c69fe.json](graphify-out/cache/semantic/988301b60a14dedf01e918ffde291794e3a7831ab84bcebc3bf2f9046c9c69fe.json) |  | 2026-07-08 | 585B | `f380b511` |
| [graphify-out/cache/semantic/992fd7d199306821c3c97bcc5cd3c4fcc169a2e7906ef565539b89ae3a189ef0.json](graphify-out/cache/semantic/992fd7d199306821c3c97bcc5cd3c4fcc169a2e7906ef565539b89ae3a189ef0.json) |  | 2026-07-08 | 794B | `cc45ecbf` |
| [graphify-out/cache/semantic/9a0b5e517792fd9f6c993c6d979687601347016ac503f02a67d26221f6d44fe0.json](graphify-out/cache/semantic/9a0b5e517792fd9f6c993c6d979687601347016ac503f02a67d26221f6d44fe0.json) |  | 2026-07-08 | 804B | `a75ba0ae` |
| [graphify-out/cache/semantic/9abe8ccebfb2e39d6c586b1534a144c01af39a313344706bfc348e97e0c08c3a.json](graphify-out/cache/semantic/9abe8ccebfb2e39d6c586b1534a144c01af39a313344706bfc348e97e0c08c3a.json) |  | 2026-07-08 | 355B | `a71f72dd` |
| [graphify-out/cache/semantic/9bb2db0c227572494a7740e37ba569e3e39d3adfab64f28f53652f01b9269e5d.json](graphify-out/cache/semantic/9bb2db0c227572494a7740e37ba569e3e39d3adfab64f28f53652f01b9269e5d.json) |  | 2026-07-08 | 1KB | `590649d4` |
| [graphify-out/cache/semantic/9be770429753625e5a065bf97aab95adb58abd939ba4f36e626d76bef368b90f.json](graphify-out/cache/semantic/9be770429753625e5a065bf97aab95adb58abd939ba4f36e626d76bef368b90f.json) |  | 2026-07-08 | 763B | `36ed8dde` |
| [graphify-out/cache/semantic/9c1ea40a1f3eba4e5fca9adfb951c29d6ce25b7b2d2ffccf5af9615a9b544579.json](graphify-out/cache/semantic/9c1ea40a1f3eba4e5fca9adfb951c29d6ce25b7b2d2ffccf5af9615a9b544579.json) |  | 2026-07-08 | 763B | `0ab85987` |
| [graphify-out/cache/semantic/9c89dd7f953cb4793d31d6571a566e8618ccea9313730f2711e7e525ec8d54ff.json](graphify-out/cache/semantic/9c89dd7f953cb4793d31d6571a566e8618ccea9313730f2711e7e525ec8d54ff.json) |  | 2026-07-08 | 1KB | `11a03352` |
| [graphify-out/cache/semantic/9cd3be0072b426fded4b2a48aeb500b9e4b0c368ccc02a115aa5037f6b87f697.json](graphify-out/cache/semantic/9cd3be0072b426fded4b2a48aeb500b9e4b0c368ccc02a115aa5037f6b87f697.json) |  | 2026-07-08 | 284B | `e61cc70e` |
| [graphify-out/cache/semantic/9cfef2a8961df5968cc7a90c9329684c64b564814b0d98429c2db32739b13ce8.json](graphify-out/cache/semantic/9cfef2a8961df5968cc7a90c9329684c64b564814b0d98429c2db32739b13ce8.json) |  | 2026-07-08 | 3KB | `40c244c2` |
| [graphify-out/cache/semantic/9d947360d0a5b81639d5cbb0fa3ea76082fbadf6aab450386c2947d1847d7aca.json](graphify-out/cache/semantic/9d947360d0a5b81639d5cbb0fa3ea76082fbadf6aab450386c2947d1847d7aca.json) |  | 2026-07-08 | 5KB | `3e914533` |
| [graphify-out/cache/semantic/9de4c0d2dace501fc4525c065472346da85f8b8f0886925df8a6af098a5842bb.json](graphify-out/cache/semantic/9de4c0d2dace501fc4525c065472346da85f8b8f0886925df8a6af098a5842bb.json) |  | 2026-07-08 | 766B | `4cd387ff` |
| [graphify-out/cache/semantic/a006d114fce553764df863267ddcac15f7676983ebf26266aeb173957580a2b9.json](graphify-out/cache/semantic/a006d114fce553764df863267ddcac15f7676983ebf26266aeb173957580a2b9.json) |  | 2026-07-08 | 6KB | `f32bfacd` |
| [graphify-out/cache/semantic/a008382362b1da472352e91146ef36e930c491987e477b6bb18946710bdaca50.json](graphify-out/cache/semantic/a008382362b1da472352e91146ef36e930c491987e477b6bb18946710bdaca50.json) |  | 2026-07-08 | 380B | `7b6655dd` |
| [graphify-out/cache/semantic/a00bb16094d4596cd57f11ec5d2c9a4489940443ee423d861cd72643a6b06da3.json](graphify-out/cache/semantic/a00bb16094d4596cd57f11ec5d2c9a4489940443ee423d861cd72643a6b06da3.json) |  | 2026-07-08 | 729B | `f2ac542c` |
| [graphify-out/cache/semantic/a05f81f678ad4ee3d1ee48e8849ffa8f093ce60794d4d01912066c6eebfc6b4a.json](graphify-out/cache/semantic/a05f81f678ad4ee3d1ee48e8849ffa8f093ce60794d4d01912066c6eebfc6b4a.json) |  | 2026-07-08 | 9KB | `4a72d3fe` |
| [graphify-out/cache/semantic/a11c260624f564cd4dcfb6732822f3b45100be91e4af49d3432269ea31fd495a.json](graphify-out/cache/semantic/a11c260624f564cd4dcfb6732822f3b45100be91e4af49d3432269ea31fd495a.json) |  | 2026-07-08 | 344B | `5a2fd013` |
| [graphify-out/cache/semantic/a1e7c21338055a4f6f60a8f9cb6f3e497912c305aece1e4150773af37f22f585.json](graphify-out/cache/semantic/a1e7c21338055a4f6f60a8f9cb6f3e497912c305aece1e4150773af37f22f585.json) |  | 2026-07-08 | 750B | `e54ac548` |
| [graphify-out/cache/semantic/a239b7352b3e2d684db0ffebb5d42a8ee02e3bd1b0c4d48a1bc8e8088ab8c0f6.json](graphify-out/cache/semantic/a239b7352b3e2d684db0ffebb5d42a8ee02e3bd1b0c4d48a1bc8e8088ab8c0f6.json) |  | 2026-07-08 | 495B | `e0d391b1` |
| [graphify-out/cache/semantic/a264bdc65f1dfd2f4958886724c5e084994fdc3c07ddc7e81c0c01389a890204.json](graphify-out/cache/semantic/a264bdc65f1dfd2f4958886724c5e084994fdc3c07ddc7e81c0c01389a890204.json) |  | 2026-07-08 | 2KB | `530db6e4` |
| [graphify-out/cache/semantic/a2aa312a51fe36b1c317d86f427ac957a553344f5783e10879e8ca67a0bb3e41.json](graphify-out/cache/semantic/a2aa312a51fe36b1c317d86f427ac957a553344f5783e10879e8ca67a0bb3e41.json) |  | 2026-07-08 | 320B | `bd774920` |
| [graphify-out/cache/semantic/a4027aafd61861c100aa90ebe9f10afb604cb8d38f93244d446440c2141a3e8e.json](graphify-out/cache/semantic/a4027aafd61861c100aa90ebe9f10afb604cb8d38f93244d446440c2141a3e8e.json) |  | 2026-07-08 | 314B | `a656aa60` |
| [graphify-out/cache/semantic/a4b417464e1d490893f6c712963b90412d5d02f3f85189e324b4c947892401e4.json](graphify-out/cache/semantic/a4b417464e1d490893f6c712963b90412d5d02f3f85189e324b4c947892401e4.json) |  | 2026-07-08 | 2KB | `12090d19` |
| [graphify-out/cache/semantic/a5db4aa0a1fcfd03fc92577e0240ae3f0d9161d6288db5b10143cffd01bd22f9.json](graphify-out/cache/semantic/a5db4aa0a1fcfd03fc92577e0240ae3f0d9161d6288db5b10143cffd01bd22f9.json) |  | 2026-07-08 | 1KB | `bd62e79a` |
| [graphify-out/cache/semantic/a63be16d6223f623cefe9331b35043bf6e92e9f37e9c02eb10674f40abf8fd71.json](graphify-out/cache/semantic/a63be16d6223f623cefe9331b35043bf6e92e9f37e9c02eb10674f40abf8fd71.json) |  | 2026-07-08 | 1KB | `231ade3d` |
| [graphify-out/cache/semantic/a6daad232ce9ef112c35637cdca69da3d4fac309adc0f203f87d7acdfa91eb10.json](graphify-out/cache/semantic/a6daad232ce9ef112c35637cdca69da3d4fac309adc0f203f87d7acdfa91eb10.json) |  | 2026-07-08 | 825B | `9b6c7628` |
| [graphify-out/cache/semantic/a7b2e4e2a6f138e3e48942c1c828349d578e9398ac2f088d1260ba13f807eeb1.json](graphify-out/cache/semantic/a7b2e4e2a6f138e3e48942c1c828349d578e9398ac2f088d1260ba13f807eeb1.json) |  | 2026-07-08 | 1KB | `25734dc7` |
| [graphify-out/cache/semantic/a891bb5de614fffba4be1c4a7a06f4b1e04bd3f36340c754737e8e2df05b8a94.json](graphify-out/cache/semantic/a891bb5de614fffba4be1c4a7a06f4b1e04bd3f36340c754737e8e2df05b8a94.json) |  | 2026-07-08 | 336B | `3e9e452a` |
| [graphify-out/cache/semantic/a9330cd12d806432d444c0cff54cea2433750c23c913dc4f302780343af88d93.json](graphify-out/cache/semantic/a9330cd12d806432d444c0cff54cea2433750c23c913dc4f302780343af88d93.json) |  | 2026-07-08 | 666B | `a02fb740` |
| [graphify-out/cache/semantic/a9579435b6c2f5a40f4fe95e83fd4cb2a518af0a0aad7f769f5491b6785cc79b.json](graphify-out/cache/semantic/a9579435b6c2f5a40f4fe95e83fd4cb2a518af0a0aad7f769f5491b6785cc79b.json) |  | 2026-07-08 | 342B | `6ca1ed60` |
| [graphify-out/cache/semantic/aa0896cf86f337ddae55f99575c92a308e99e03b36fdc8af28d1e54beb6649f8.json](graphify-out/cache/semantic/aa0896cf86f337ddae55f99575c92a308e99e03b36fdc8af28d1e54beb6649f8.json) |  | 2026-07-08 | 9KB | `c7983960` |
| [graphify-out/cache/semantic/aa14236f6c5d9bea81fc6f44e1819ddfee3509b010f53285fb01eef24c0a0638.json](graphify-out/cache/semantic/aa14236f6c5d9bea81fc6f44e1819ddfee3509b010f53285fb01eef24c0a0638.json) |  | 2026-07-08 | 654B | `b82b263a` |
| [graphify-out/cache/semantic/aa2f65da384867ed29f223ab1689e7cabe1c238885082f0634f99e1cd7bf9c61.json](graphify-out/cache/semantic/aa2f65da384867ed29f223ab1689e7cabe1c238885082f0634f99e1cd7bf9c61.json) |  | 2026-07-08 | 1KB | `7586ff9b` |
| [graphify-out/cache/semantic/ac025551ad4fde68c75967d401491df8694e7a5471cac8b6ec5448c198e986e5.json](graphify-out/cache/semantic/ac025551ad4fde68c75967d401491df8694e7a5471cac8b6ec5448c198e986e5.json) |  | 2026-07-08 | 363B | `4b978312` |
| [graphify-out/cache/semantic/ac85d76c2d22a6ed1b460b1b0aeb581b14c6bbb564267b1856ae31c21641e1cc.json](graphify-out/cache/semantic/ac85d76c2d22a6ed1b460b1b0aeb581b14c6bbb564267b1856ae31c21641e1cc.json) |  | 2026-07-08 | 823B | `b8ac833f` |
| [graphify-out/cache/semantic/ad0246ef07f80dfba5c8551b498935aecd2a684d13497426d023b20fd69add17.json](graphify-out/cache/semantic/ad0246ef07f80dfba5c8551b498935aecd2a684d13497426d023b20fd69add17.json) |  | 2026-07-08 | 598B | `10e820a5` |
| [graphify-out/cache/semantic/ad0a16db1fbd0e0fe4e831cc4914cd4a7d9fc20e01c2525cdf5a6e9916e20b5b.json](graphify-out/cache/semantic/ad0a16db1fbd0e0fe4e831cc4914cd4a7d9fc20e01c2525cdf5a6e9916e20b5b.json) |  | 2026-07-08 | 353B | `354637d3` |
| [graphify-out/cache/semantic/ade7d1955a6e03ddf2b8006bcfbef0db96d7ff1ba58b9a288f7b6d4754eebb8f.json](graphify-out/cache/semantic/ade7d1955a6e03ddf2b8006bcfbef0db96d7ff1ba58b9a288f7b6d4754eebb8f.json) |  | 2026-07-08 | 344B | `d4a8932d` |
| [graphify-out/cache/semantic/ae0f138ea4308814aede6739d83333eab023a6a35b64369573af9210bde59747.json](graphify-out/cache/semantic/ae0f138ea4308814aede6739d83333eab023a6a35b64369573af9210bde59747.json) |  | 2026-07-08 | 688B | `4206c5f7` |
| [graphify-out/cache/semantic/ae4dd90d6ba47d92a14627c06e2a349fe79936beb1735c6bc7a4c8cfd3eb8f2e.json](graphify-out/cache/semantic/ae4dd90d6ba47d92a14627c06e2a349fe79936beb1735c6bc7a4c8cfd3eb8f2e.json) |  | 2026-07-08 | 2KB | `0f6fa758` |
| [graphify-out/cache/semantic/af32687d0b85782a8ea7844c474ef3a7ef7e2bc1ef175623ccd80206647bb0e1.json](graphify-out/cache/semantic/af32687d0b85782a8ea7844c474ef3a7ef7e2bc1ef175623ccd80206647bb0e1.json) |  | 2026-07-08 | 1KB | `c241a4f5` |
| [graphify-out/cache/semantic/af56c61bfe4706fcfe4dc219db50b8b23c16f2d6517a06fd498c8be2afe81061.json](graphify-out/cache/semantic/af56c61bfe4706fcfe4dc219db50b8b23c16f2d6517a06fd498c8be2afe81061.json) |  | 2026-07-08 | 1KB | `82cffbb6` |
| [graphify-out/cache/semantic/af64a0976d77a2cfe285aebeb5cde81b15dc4d6a3042caeb2a04047d2fefde09.json](graphify-out/cache/semantic/af64a0976d77a2cfe285aebeb5cde81b15dc4d6a3042caeb2a04047d2fefde09.json) |  | 2026-07-08 | 1KB | `c3e281a3` |
| [graphify-out/cache/semantic/af740deaa9ddf5b369f88e46d1643dc5b47ea90535bfb14c85e768c10f594ba8.json](graphify-out/cache/semantic/af740deaa9ddf5b369f88e46d1643dc5b47ea90535bfb14c85e768c10f594ba8.json) |  | 2026-07-08 | 329B | `1162db9b` |
| [graphify-out/cache/semantic/af7727d5672fcf8ab0dbf954370a3bf3318b887407ce30e29216dc9dd87c74a1.json](graphify-out/cache/semantic/af7727d5672fcf8ab0dbf954370a3bf3318b887407ce30e29216dc9dd87c74a1.json) |  | 2026-07-08 | 709B | `1c53bbfe` |
| [graphify-out/cache/semantic/afbfc9ac9947e1736753df22adba4fb45e9b9da3a77f74527caa55dc90785a67.json](graphify-out/cache/semantic/afbfc9ac9947e1736753df22adba4fb45e9b9da3a77f74527caa55dc90785a67.json) |  | 2026-07-08 | 4KB | `618592b6` |
| [graphify-out/cache/semantic/b09e5bfdd8a7b8837b339b7d23eade42d885aa0f13a1b20e52bb7362188f6af4.json](graphify-out/cache/semantic/b09e5bfdd8a7b8837b339b7d23eade42d885aa0f13a1b20e52bb7362188f6af4.json) |  | 2026-07-08 | 876B | `b4cc0a02` |
| [graphify-out/cache/semantic/b0a07aaa139bb7667e9643b05bff7e358adcd3f1b0880f18733aa698de7d248e.json](graphify-out/cache/semantic/b0a07aaa139bb7667e9643b05bff7e358adcd3f1b0880f18733aa698de7d248e.json) |  | 2026-07-08 | 422B | `c1a3c435` |
| [graphify-out/cache/semantic/b1865470bf158b6e3e84a5c8f9d8b58b31297441c549057e6ab542ce5f1e8f79.json](graphify-out/cache/semantic/b1865470bf158b6e3e84a5c8f9d8b58b31297441c549057e6ab542ce5f1e8f79.json) |  | 2026-07-08 | 5KB | `106122de` |
| [graphify-out/cache/semantic/b1b99371b6f8bd32b1a7e6be3f7e0fe3ee5e466fea52087832fcc94dcca85a32.json](graphify-out/cache/semantic/b1b99371b6f8bd32b1a7e6be3f7e0fe3ee5e466fea52087832fcc94dcca85a32.json) |  | 2026-07-08 | 525B | `8532eb64` |
| [graphify-out/cache/semantic/b21a9502704a4189038ade35ced6cc31254eecf8635347914f83f0a343fe18a5.json](graphify-out/cache/semantic/b21a9502704a4189038ade35ced6cc31254eecf8635347914f83f0a343fe18a5.json) |  | 2026-07-08 | 882B | `a8674518` |
| [graphify-out/cache/semantic/b2581e7942ef3b965358bf8d0a0669b9fd8e862c9257d9633bd5e86e22a3249d.json](graphify-out/cache/semantic/b2581e7942ef3b965358bf8d0a0669b9fd8e862c9257d9633bd5e86e22a3249d.json) |  | 2026-07-08 | 1KB | `52fe55fe` |
| [graphify-out/cache/semantic/b270a74c320994d0459045bc4b3097ffbeda3a5238559741b04d1e62b39ccc83.json](graphify-out/cache/semantic/b270a74c320994d0459045bc4b3097ffbeda3a5238559741b04d1e62b39ccc83.json) |  | 2026-07-08 | 2KB | `1bcb81c6` |
| [graphify-out/cache/semantic/b279f845319641295761efc34699c505b9df54d42f3bfe040f6f35b1fbb7dec8.json](graphify-out/cache/semantic/b279f845319641295761efc34699c505b9df54d42f3bfe040f6f35b1fbb7dec8.json) |  | 2026-07-08 | 962B | `7907aff9` |
| [graphify-out/cache/semantic/b28a8277f2b5f5361ce5418fc8219baa92f47c8477dc78592654e788af3431df.json](graphify-out/cache/semantic/b28a8277f2b5f5361ce5418fc8219baa92f47c8477dc78592654e788af3431df.json) |  | 2026-07-08 | 1KB | `8ff9eab9` |
| [graphify-out/cache/semantic/b2f47d3ab07db12d6d5821bce1bcc3ccca95dc255a16b24543bb569f33ae11e8.json](graphify-out/cache/semantic/b2f47d3ab07db12d6d5821bce1bcc3ccca95dc255a16b24543bb569f33ae11e8.json) |  | 2026-07-08 | 642B | `0a83a849` |
| [graphify-out/cache/semantic/b33f0063f0897641f1e83bfc4e745e8255b86c2bcbffa27725c5d6bec0e46b7d.json](graphify-out/cache/semantic/b33f0063f0897641f1e83bfc4e745e8255b86c2bcbffa27725c5d6bec0e46b7d.json) |  | 2026-07-08 | 808B | `c785143e` |
| [graphify-out/cache/semantic/b38d42f0d9b32951eabb816ed3b9488997d89a83758939f001f58d4d537bbc9b.json](graphify-out/cache/semantic/b38d42f0d9b32951eabb816ed3b9488997d89a83758939f001f58d4d537bbc9b.json) |  | 2026-07-08 | 1KB | `16a8376d` |
| [graphify-out/cache/semantic/b394f25c2c87fa4d37a1ec3b9537db8ac356d45d3977669daad664f206f1ca39.json](graphify-out/cache/semantic/b394f25c2c87fa4d37a1ec3b9537db8ac356d45d3977669daad664f206f1ca39.json) |  | 2026-07-08 | 2KB | `973a8e1c` |
| [graphify-out/cache/semantic/b3969c66a3f93167bdb3a2cb775f08e7601501d044bab03d201f05fa3cd6e110.json](graphify-out/cache/semantic/b3969c66a3f93167bdb3a2cb775f08e7601501d044bab03d201f05fa3cd6e110.json) |  | 2026-07-08 | 826B | `9282ea39` |
| [graphify-out/cache/semantic/b43fecd9154db72e86bea0480d8dfec6687a67ffef7f79d7e40d8c8aad395404.json](graphify-out/cache/semantic/b43fecd9154db72e86bea0480d8dfec6687a67ffef7f79d7e40d8c8aad395404.json) |  | 2026-07-08 | 2KB | `e107ccb8` |
| [graphify-out/cache/semantic/b4b01f8d29f1c42d877e389901770bc905cf3f10f9de5a2a8953d760ae8eb24e.json](graphify-out/cache/semantic/b4b01f8d29f1c42d877e389901770bc905cf3f10f9de5a2a8953d760ae8eb24e.json) |  | 2026-07-08 | 859B | `028e2dfb` |
| [graphify-out/cache/semantic/b4b5d88b7be8bbde190d80a657f19595e1362266ca022550a4618a7b87d655cd.json](graphify-out/cache/semantic/b4b5d88b7be8bbde190d80a657f19595e1362266ca022550a4618a7b87d655cd.json) |  | 2026-07-08 | 353B | `0110308a` |
| [graphify-out/cache/semantic/b64386aaed2bc009bed9d7f3f831f9bb7c3be7131d9388a92b72036682e8b47a.json](graphify-out/cache/semantic/b64386aaed2bc009bed9d7f3f831f9bb7c3be7131d9388a92b72036682e8b47a.json) |  | 2026-07-08 | 840B | `7b5c6ef7` |
| [graphify-out/cache/semantic/b6a7276583b7d0527ff215e2ab36e905f573033844736daea69f5ee325b17e73.json](graphify-out/cache/semantic/b6a7276583b7d0527ff215e2ab36e905f573033844736daea69f5ee325b17e73.json) |  | 2026-07-08 | 618B | `e6393edf` |
| [graphify-out/cache/semantic/b7a12eb94aa5be0dc4e13d0ccce3a55b24ff7c35fca6d4f6475bcd7cc9ad4c59.json](graphify-out/cache/semantic/b7a12eb94aa5be0dc4e13d0ccce3a55b24ff7c35fca6d4f6475bcd7cc9ad4c59.json) |  | 2026-07-08 | 619B | `023f9599` |
| [graphify-out/cache/semantic/b8f46aa111167cd9236ef3ffd46c464f635b9aaf6611b5f50d2bbed7506d5b1a.json](graphify-out/cache/semantic/b8f46aa111167cd9236ef3ffd46c464f635b9aaf6611b5f50d2bbed7506d5b1a.json) |  | 2026-07-08 | 583B | `98ea8137` |
| [graphify-out/cache/semantic/ba8ac42609755a8ef04b97a94f28e85cbaf6ab5b7d50dae94526d9d549f0c307.json](graphify-out/cache/semantic/ba8ac42609755a8ef04b97a94f28e85cbaf6ab5b7d50dae94526d9d549f0c307.json) |  | 2026-07-08 | 1KB | `b0be40f6` |
| [graphify-out/cache/semantic/ba9f72d9081dcffe4c390b8e65e9708b002f315dfd580e717629880b000804c2.json](graphify-out/cache/semantic/ba9f72d9081dcffe4c390b8e65e9708b002f315dfd580e717629880b000804c2.json) |  | 2026-07-08 | 3KB | `86c4c32f` |
| [graphify-out/cache/semantic/bcab157b2b3850502fcb9706a877f06d30e8c6d344fcdcab4e30f85b3a98c74f.json](graphify-out/cache/semantic/bcab157b2b3850502fcb9706a877f06d30e8c6d344fcdcab4e30f85b3a98c74f.json) |  | 2026-07-08 | 800B | `c30c0458` |
| [graphify-out/cache/semantic/bd619c664da57b057719e398e97aa4cc1fcee24785221c90a3aef4de31bc1aa7.json](graphify-out/cache/semantic/bd619c664da57b057719e398e97aa4cc1fcee24785221c90a3aef4de31bc1aa7.json) |  | 2026-07-08 | 9KB | `9a08830e` |
| [graphify-out/cache/semantic/be9546814d49cd726cbd397251f659ac33d59661422f7d04dbe031a0e8d66cb2.json](graphify-out/cache/semantic/be9546814d49cd726cbd397251f659ac33d59661422f7d04dbe031a0e8d66cb2.json) |  | 2026-07-08 | 830B | `411be5b0` |
| [graphify-out/cache/semantic/bf959e84e1b505dca449324d8cecc6ce0c26b256caeb5db47d1ad818acc5072a.json](graphify-out/cache/semantic/bf959e84e1b505dca449324d8cecc6ce0c26b256caeb5db47d1ad818acc5072a.json) |  | 2026-07-08 | 279B | `c339cbf0` |
| [graphify-out/cache/semantic/bfc22b5278a3c78b4d65a8b6c0f47cba58963a8dd732af400e012264aeb0a40c.json](graphify-out/cache/semantic/bfc22b5278a3c78b4d65a8b6c0f47cba58963a8dd732af400e012264aeb0a40c.json) |  | 2026-07-08 | 305B | `3ab22b99` |
| [graphify-out/cache/semantic/c0b7d4e9ed294e1aac7f5cb16ba7785d8762ae334de7231be926a4ec32b39290.json](graphify-out/cache/semantic/c0b7d4e9ed294e1aac7f5cb16ba7785d8762ae334de7231be926a4ec32b39290.json) |  | 2026-07-08 | 366B | `cd1c0161` |
| [graphify-out/cache/semantic/c11d85c73e8b4558e8833654204a4a9026a8814e27c6e763c027dd36714bfd04.json](graphify-out/cache/semantic/c11d85c73e8b4558e8833654204a4a9026a8814e27c6e763c027dd36714bfd04.json) |  | 2026-07-08 | 817B | `52240ae1` |
| [graphify-out/cache/semantic/c12843e84d94bbad8a8e8e60aca0afd0b9615408c7d5e56c03d97edc0d750ca8.json](graphify-out/cache/semantic/c12843e84d94bbad8a8e8e60aca0afd0b9615408c7d5e56c03d97edc0d750ca8.json) |  | 2026-07-08 | 1KB | `c3c5f33c` |
| [graphify-out/cache/semantic/c156404114b062a780c2a9cb2da9e2d4b307c3d26284aad2159b7729ca5e3ee4.json](graphify-out/cache/semantic/c156404114b062a780c2a9cb2da9e2d4b307c3d26284aad2159b7729ca5e3ee4.json) |  | 2026-07-08 | 326B | `1bd95ecc` |
| [graphify-out/cache/semantic/c25dbfe926bee5ef6287c740c790ef40c0e6747ef34b5b179fe2cded3b776b8b.json](graphify-out/cache/semantic/c25dbfe926bee5ef6287c740c790ef40c0e6747ef34b5b179fe2cded3b776b8b.json) |  | 2026-07-08 | 318B | `c3eaed28` |
| [graphify-out/cache/semantic/c4def0769fa7b12a927fde991141b10f5a14b32a42c4e9291355e6748962cc4d.json](graphify-out/cache/semantic/c4def0769fa7b12a927fde991141b10f5a14b32a42c4e9291355e6748962cc4d.json) |  | 2026-07-08 | 3KB | `f5964c2c` |
| [graphify-out/cache/semantic/c51619a80bbb4598e62a0b571fe06c31040338ce34c2817041be6dc5d44d256e.json](graphify-out/cache/semantic/c51619a80bbb4598e62a0b571fe06c31040338ce34c2817041be6dc5d44d256e.json) |  | 2026-07-08 | 287B | `7ebf30cd` |
| [graphify-out/cache/semantic/c54d64c997724cbb9f47e0a15fcbb81f3c2b1022f06e32a8a2a2e82b8d19f921.json](graphify-out/cache/semantic/c54d64c997724cbb9f47e0a15fcbb81f3c2b1022f06e32a8a2a2e82b8d19f921.json) |  | 2026-07-08 | 834B | `d83e6d8c` |
| [graphify-out/cache/semantic/c5cad5748e0b58dbc9792d57510c04e5e8af796521dbd7060e8030da294c50df.json](graphify-out/cache/semantic/c5cad5748e0b58dbc9792d57510c04e5e8af796521dbd7060e8030da294c50df.json) |  | 2026-07-08 | 1KB | `d4f16663` |
| [graphify-out/cache/semantic/c63ec1346eacfa262dce8831f79d52288490770438eb84ccc420dcd74ed603b0.json](graphify-out/cache/semantic/c63ec1346eacfa262dce8831f79d52288490770438eb84ccc420dcd74ed603b0.json) |  | 2026-07-08 | 1KB | `8d09af7a` |
| [graphify-out/cache/semantic/c712d3a7fa2e4b134fc92f6b17a98ea1eccee97110cef040e3eb932c1ff1755c.json](graphify-out/cache/semantic/c712d3a7fa2e4b134fc92f6b17a98ea1eccee97110cef040e3eb932c1ff1755c.json) |  | 2026-07-08 | 400B | `8d4be091` |
| [graphify-out/cache/semantic/c72f94058bc626f611270f168be334e1808441884221ffed707502014e4626f0.json](graphify-out/cache/semantic/c72f94058bc626f611270f168be334e1808441884221ffed707502014e4626f0.json) |  | 2026-07-08 | 2KB | `b78b9628` |
| [graphify-out/cache/semantic/c7f987844ca369b63a948c6be30d2cafb077b7979f09ff0e324c4262d134bdfe.json](graphify-out/cache/semantic/c7f987844ca369b63a948c6be30d2cafb077b7979f09ff0e324c4262d134bdfe.json) |  | 2026-07-08 | 299B | `479f9e92` |
| [graphify-out/cache/semantic/c8278831535826b663d7f98efd09857722903aa2ed35bc9f00d13f91ec97067b.json](graphify-out/cache/semantic/c8278831535826b663d7f98efd09857722903aa2ed35bc9f00d13f91ec97067b.json) |  | 2026-07-08 | 1KB | `ddd97a7e` |
| [graphify-out/cache/semantic/c8ee3202692623ce9e2f78797e4fac66a87f4efe998b3db96dc7a6f879f9988b.json](graphify-out/cache/semantic/c8ee3202692623ce9e2f78797e4fac66a87f4efe998b3db96dc7a6f879f9988b.json) |  | 2026-07-08 | 350B | `e8d55e01` |
| [graphify-out/cache/semantic/c9cac7d22690fa677bcf06b2549be6814e36f10d9ca5884c4047b351dfe0ccc0.json](graphify-out/cache/semantic/c9cac7d22690fa677bcf06b2549be6814e36f10d9ca5884c4047b351dfe0ccc0.json) |  | 2026-07-08 | 849B | `2ebf4034` |
| [graphify-out/cache/semantic/ca025357b8e8ec6d7170b94ddf4e377a1054901ea63cff0ad0fbd2135ecfd5da.json](graphify-out/cache/semantic/ca025357b8e8ec6d7170b94ddf4e377a1054901ea63cff0ad0fbd2135ecfd5da.json) |  | 2026-07-08 | 323B | `fa098d49` |
| [graphify-out/cache/semantic/caf1d7caee8e5cd28fc8233165867111cb8af092af6dc70ea5ba3d1257bde4c4.json](graphify-out/cache/semantic/caf1d7caee8e5cd28fc8233165867111cb8af092af6dc70ea5ba3d1257bde4c4.json) |  | 2026-07-08 | 847B | `ba66a9e4` |
| [graphify-out/cache/semantic/cb1847459f380c6a48571c94865f66569925aed2f293e49ae4ad2c4509b7c235.json](graphify-out/cache/semantic/cb1847459f380c6a48571c94865f66569925aed2f293e49ae4ad2c4509b7c235.json) |  | 2026-07-08 | 524B | `341cb3f7` |
| [graphify-out/cache/semantic/cc75d2e7aefe4c24bf80c2a85c5d77e38d6f4e5ddbdf0788ef89ba14a04a57ca.json](graphify-out/cache/semantic/cc75d2e7aefe4c24bf80c2a85c5d77e38d6f4e5ddbdf0788ef89ba14a04a57ca.json) |  | 2026-07-08 | 389B | `9faf82a0` |
| [graphify-out/cache/semantic/ce60ec8b10fd36f79405a4e81303d93e143e555a6232790b1ebb08710b7d2e6a.json](graphify-out/cache/semantic/ce60ec8b10fd36f79405a4e81303d93e143e555a6232790b1ebb08710b7d2e6a.json) |  | 2026-07-08 | 1KB | `62c5197c` |
| [graphify-out/cache/semantic/cf2ef6069be6d8305cd761727e35a4f89f213321c0c2f3d5cd8978e7eab269b3.json](graphify-out/cache/semantic/cf2ef6069be6d8305cd761727e35a4f89f213321c0c2f3d5cd8978e7eab269b3.json) |  | 2026-07-08 | 346B | `ac2dbb49` |
| [graphify-out/cache/semantic/d0e824a844e5ec7229f11588808b0de6909eaaf9e06e51ec57e936c2b57dd345.json](graphify-out/cache/semantic/d0e824a844e5ec7229f11588808b0de6909eaaf9e06e51ec57e936c2b57dd345.json) |  | 2026-07-08 | 466B | `daff1cf8` |
| [graphify-out/cache/semantic/d13613be343e85f1cf67d13eee8fe206e9b5fd2e3d5dd354e4fc226bc089a2d7.json](graphify-out/cache/semantic/d13613be343e85f1cf67d13eee8fe206e9b5fd2e3d5dd354e4fc226bc089a2d7.json) |  | 2026-07-08 | 353B | `35ea4f52` |
| [graphify-out/cache/semantic/d19ad59768e18c545fb5e62ef453ac4d39a203511e7133a1ef016665dfd3a997.json](graphify-out/cache/semantic/d19ad59768e18c545fb5e62ef453ac4d39a203511e7133a1ef016665dfd3a997.json) |  | 2026-07-08 | 338B | `7259f080` |
| [graphify-out/cache/semantic/d1a29da8294bfcf9bf8c332ad50204a994630bcc080f9a8f3ac406e7732686c1.json](graphify-out/cache/semantic/d1a29da8294bfcf9bf8c332ad50204a994630bcc080f9a8f3ac406e7732686c1.json) |  | 2026-07-08 | 309B | `0b2e0801` |
| [graphify-out/cache/semantic/d29b0e6cdd1c0d4d517d17bbf9cf77e0da74cf07e28383958f0e8fd9630e038b.json](graphify-out/cache/semantic/d29b0e6cdd1c0d4d517d17bbf9cf77e0da74cf07e28383958f0e8fd9630e038b.json) |  | 2026-07-08 | 663B | `804a2e84` |
| [graphify-out/cache/semantic/d371d7ffcf3ba3d82c342353b227dc0aa6848337dc2272d3d5b88be27588fa8c.json](graphify-out/cache/semantic/d371d7ffcf3ba3d82c342353b227dc0aa6848337dc2272d3d5b88be27588fa8c.json) |  | 2026-07-08 | 771B | `aa5b4a0a` |
| [graphify-out/cache/semantic/d43c521f8625b4b250fff3bd72acd037bed1a5876b1e2ba441b26319134c8b84.json](graphify-out/cache/semantic/d43c521f8625b4b250fff3bd72acd037bed1a5876b1e2ba441b26319134c8b84.json) |  | 2026-07-08 | 353B | `a9add80c` |
| [graphify-out/cache/semantic/d61b8f62cf02b89101c6c7edf4e0eeda3481a6a8d510b551468a15feb757ff7d.json](graphify-out/cache/semantic/d61b8f62cf02b89101c6c7edf4e0eeda3481a6a8d510b551468a15feb757ff7d.json) |  | 2026-07-08 | 955B | `0fa91ef7` |
| [graphify-out/cache/semantic/d666b6c6e0f9d4972a624e2e5eb81db225238499fd1b4b7bd5fb5896f34d286f.json](graphify-out/cache/semantic/d666b6c6e0f9d4972a624e2e5eb81db225238499fd1b4b7bd5fb5896f34d286f.json) |  | 2026-07-08 | 315B | `5460ace7` |
| [graphify-out/cache/semantic/d6ad672122aec5e0ebc32fbe2965d2806a757bfa18c35e8e58b07f028c5f0258.json](graphify-out/cache/semantic/d6ad672122aec5e0ebc32fbe2965d2806a757bfa18c35e8e58b07f028c5f0258.json) |  | 2026-07-08 | 314B | `bcdc9a35` |
| [graphify-out/cache/semantic/d75ea0ce6d81a3533015a2a6262b8e2129ed78cd6e9b8ab20d1b70b982bae492.json](graphify-out/cache/semantic/d75ea0ce6d81a3533015a2a6262b8e2129ed78cd6e9b8ab20d1b70b982bae492.json) |  | 2026-07-08 | 278B | `4aefd86b` |
| [graphify-out/cache/semantic/d7ecbcbaa534939ca868b6436ac0a1358a865efaafab8a5126768eced02cd116.json](graphify-out/cache/semantic/d7ecbcbaa534939ca868b6436ac0a1358a865efaafab8a5126768eced02cd116.json) |  | 2026-07-08 | 284B | `fadd7ab0` |
| [graphify-out/cache/semantic/d7f6ff36d5c1abe2cc558096badc3914a76cb43e7b4148d77e1da67808adae81.json](graphify-out/cache/semantic/d7f6ff36d5c1abe2cc558096badc3914a76cb43e7b4148d77e1da67808adae81.json) |  | 2026-07-08 | 709B | `82720e4c` |
| [graphify-out/cache/semantic/d8420d735aea05633c9ded080ec0119e5fce75868ad1343434cea0f22762d9c8.json](graphify-out/cache/semantic/d8420d735aea05633c9ded080ec0119e5fce75868ad1343434cea0f22762d9c8.json) |  | 2026-07-08 | 314B | `cc58dc2f` |
| [graphify-out/cache/semantic/d8c8c5aa60df24a1dac37b4d2c97386ffd67118cd2e3587489a0cb20e52b2950.json](graphify-out/cache/semantic/d8c8c5aa60df24a1dac37b4d2c97386ffd67118cd2e3587489a0cb20e52b2950.json) |  | 2026-07-08 | 1KB | `ecc8ce28` |
| [graphify-out/cache/semantic/da713305e9e0c790a4b1cb33cd933e6de84ce1958adbb41ee6ec980bcb506dfc.json](graphify-out/cache/semantic/da713305e9e0c790a4b1cb33cd933e6de84ce1958adbb41ee6ec980bcb506dfc.json) |  | 2026-07-08 | 266B | `8023d6de` |
| [graphify-out/cache/semantic/db1114b95b45c682ed359134526a7be6c6fe4bad9b7aba19efa64efda5e774f2.json](graphify-out/cache/semantic/db1114b95b45c682ed359134526a7be6c6fe4bad9b7aba19efa64efda5e774f2.json) |  | 2026-07-08 | 1KB | `30bd4c33` |
| [graphify-out/cache/semantic/dc23852ce2406046df4da275c36e8da94e6a030c42baf273136a1b93eebd18df.json](graphify-out/cache/semantic/dc23852ce2406046df4da275c36e8da94e6a030c42baf273136a1b93eebd18df.json) |  | 2026-07-08 | 739B | `23fd4604` |
| [graphify-out/cache/semantic/dd8c7c05a26065785195b02e4c515cada1c85affe4805ecbb5032db88be8a95a.json](graphify-out/cache/semantic/dd8c7c05a26065785195b02e4c515cada1c85affe4805ecbb5032db88be8a95a.json) |  | 2026-07-08 | 853B | `fff7cbf3` |
| [graphify-out/cache/semantic/de90183da185712c330560eda3e7c2a2181031033a698e20626619765da94e31.json](graphify-out/cache/semantic/de90183da185712c330560eda3e7c2a2181031033a698e20626619765da94e31.json) |  | 2026-07-08 | 823B | `04e20c29` |
| [graphify-out/cache/semantic/df726ad9ade81a487a9b5b6b16e9e4302b12c8dcb0d173799bcc32600a4815e5.json](graphify-out/cache/semantic/df726ad9ade81a487a9b5b6b16e9e4302b12c8dcb0d173799bcc32600a4815e5.json) |  | 2026-07-08 | 320B | `c11d89c8` |
| [graphify-out/cache/semantic/dfacd77458134c8c7d00529c358abb86db3b6eb5baa6edd9b7fa432c9f20e650.json](graphify-out/cache/semantic/dfacd77458134c8c7d00529c358abb86db3b6eb5baa6edd9b7fa432c9f20e650.json) |  | 2026-07-08 | 349B | `29aef403` |
| [graphify-out/cache/semantic/dfada9efc7d5f2eda5389d2eeccb1f97d8e190c490090308ae311844336db000.json](graphify-out/cache/semantic/dfada9efc7d5f2eda5389d2eeccb1f97d8e190c490090308ae311844336db000.json) |  | 2026-07-08 | 356B | `5920a253` |
| [graphify-out/cache/semantic/e0460ffd40c3d9b57e7721db458c0162bf4e1c0e784452c3b8d200ecd2e9cf12.json](graphify-out/cache/semantic/e0460ffd40c3d9b57e7721db458c0162bf4e1c0e784452c3b8d200ecd2e9cf12.json) |  | 2026-07-08 | 1KB | `ecb7f318` |
| [graphify-out/cache/semantic/e124a2a7512d3bcf2953993fc5146ec830b958a77f3c6bd9bdd8c7e3a323ab2d.json](graphify-out/cache/semantic/e124a2a7512d3bcf2953993fc5146ec830b958a77f3c6bd9bdd8c7e3a323ab2d.json) |  | 2026-07-08 | 1KB | `5fa2030d` |
| [graphify-out/cache/semantic/e22d17a9f78d6c9e756ac1720e6f6e1f2b0434648fcf8cace8357a78a832482b.json](graphify-out/cache/semantic/e22d17a9f78d6c9e756ac1720e6f6e1f2b0434648fcf8cace8357a78a832482b.json) |  | 2026-07-08 | 2KB | `a387c5d9` |
| [graphify-out/cache/semantic/e3235f17922851e4f2c963f83a26101b9a764990bafc31e23c4aad1de53c62e1.json](graphify-out/cache/semantic/e3235f17922851e4f2c963f83a26101b9a764990bafc31e23c4aad1de53c62e1.json) |  | 2026-07-08 | 1KB | `de0a8f4e` |
| [graphify-out/cache/semantic/e329da8903930c9c56ebcf25db90bc203c0ae96e63d465ae06c99ccb0df1ecaf.json](graphify-out/cache/semantic/e329da8903930c9c56ebcf25db90bc203c0ae96e63d465ae06c99ccb0df1ecaf.json) |  | 2026-07-08 | 986B | `9ed3ea5b` |
| [graphify-out/cache/semantic/e334a0045a1532914d6943c6f29a376c07f42bdb6dcaacf9a1cb24af824e290a.json](graphify-out/cache/semantic/e334a0045a1532914d6943c6f29a376c07f42bdb6dcaacf9a1cb24af824e290a.json) |  | 2026-07-08 | 831B | `0c86e22e` |
| [graphify-out/cache/semantic/e54d4a4ee4dd584f7565c569ef9883dffb0e1417bd405de382ad16513ab905ae.json](graphify-out/cache/semantic/e54d4a4ee4dd584f7565c569ef9883dffb0e1417bd405de382ad16513ab905ae.json) |  | 2026-07-08 | 391B | `ce3eaa0e` |
| [graphify-out/cache/semantic/e652fede0dedb6bd293b752dbc6624a62d566abece97f161973c5b99e4b805a5.json](graphify-out/cache/semantic/e652fede0dedb6bd293b752dbc6624a62d566abece97f161973c5b99e4b805a5.json) |  | 2026-07-08 | 5KB | `54a76f5f` |
| [graphify-out/cache/semantic/e6633b165de4949a29345179bbe2219b976f801ed2636747deaf7c67e8e189b3.json](graphify-out/cache/semantic/e6633b165de4949a29345179bbe2219b976f801ed2636747deaf7c67e8e189b3.json) |  | 2026-07-08 | 384B | `86bc8661` |
| [graphify-out/cache/semantic/e8149c4e2782362c3173a38c09ccd7c8f81fd6f212cb8bccb588998f9284e714.json](graphify-out/cache/semantic/e8149c4e2782362c3173a38c09ccd7c8f81fd6f212cb8bccb588998f9284e714.json) |  | 2026-07-08 | 2KB | `1fbc5efa` |
| [graphify-out/cache/semantic/e9b71808f0b19b5a0afc730479d014fb6fe084ff631288274bfc411bd2a529f6.json](graphify-out/cache/semantic/e9b71808f0b19b5a0afc730479d014fb6fe084ff631288274bfc411bd2a529f6.json) |  | 2026-07-08 | 891B | `f5612e12` |
| [graphify-out/cache/semantic/ea07f2f163d3405507f072a04d10adfa8c149f015a1122abfd4d9388498d8263.json](graphify-out/cache/semantic/ea07f2f163d3405507f072a04d10adfa8c149f015a1122abfd4d9388498d8263.json) |  | 2026-07-08 | 945B | `ec4ec1db` |
| [graphify-out/cache/semantic/ea716e5082a551d5c8fe23201c28c7b2fe21d2291ff4170a299a23b7f0ea2c8a.json](graphify-out/cache/semantic/ea716e5082a551d5c8fe23201c28c7b2fe21d2291ff4170a299a23b7f0ea2c8a.json) |  | 2026-07-08 | 389B | `58dfd2d1` |
| [graphify-out/cache/semantic/ed287c78382f5fa8047f2bd49d4b548c63af6b27435e8b0c981ea91c1ed8b0af.json](graphify-out/cache/semantic/ed287c78382f5fa8047f2bd49d4b548c63af6b27435e8b0c981ea91c1ed8b0af.json) |  | 2026-07-08 | 3KB | `cc15cab9` |
| [graphify-out/cache/semantic/ed6f1639a65c3d20ebb7035ea1182abf37fa418c65f0764de74779ab324a966a.json](graphify-out/cache/semantic/ed6f1639a65c3d20ebb7035ea1182abf37fa418c65f0764de74779ab324a966a.json) |  | 2026-07-08 | 2KB | `a6e86a6d` |
| [graphify-out/cache/semantic/edb2005f33cdb4c2fb64ba074ee1217fd2b65d1fa85e0d4d806b4ae2d378ea29.json](graphify-out/cache/semantic/edb2005f33cdb4c2fb64ba074ee1217fd2b65d1fa85e0d4d806b4ae2d378ea29.json) |  | 2026-07-08 | 311B | `d5632ba7` |
| [graphify-out/cache/semantic/ee7a4d2be4f6018b6819a8d0c7311265f1813a20cb6919886ea75b2b57eae355.json](graphify-out/cache/semantic/ee7a4d2be4f6018b6819a8d0c7311265f1813a20cb6919886ea75b2b57eae355.json) |  | 2026-07-08 | 382B | `da045b27` |
| [graphify-out/cache/semantic/eeb27b936fee65178a3e7ad18a56240f49d5193116f1e58f7f82038fbe19c670.json](graphify-out/cache/semantic/eeb27b936fee65178a3e7ad18a56240f49d5193116f1e58f7f82038fbe19c670.json) |  | 2026-07-08 | 2KB | `d61e411f` |
| [graphify-out/cache/semantic/eebd8b17a1528bebeb50bf75a322069027f4fa9d87308233f4b88950ceb77ae4.json](graphify-out/cache/semantic/eebd8b17a1528bebeb50bf75a322069027f4fa9d87308233f4b88950ceb77ae4.json) |  | 2026-07-08 | 668B | `8fd7dd4a` |
| [graphify-out/cache/semantic/ef3d821f05430094ff3dc53acfaa299ba002cccfe07168bf1377b6091f96a5c7.json](graphify-out/cache/semantic/ef3d821f05430094ff3dc53acfaa299ba002cccfe07168bf1377b6091f96a5c7.json) |  | 2026-07-08 | 302B | `412a0534` |
| [graphify-out/cache/semantic/ef5e51443530e94c966cc48288ad33926aaa7884da511e39428f85af1a870ede.json](graphify-out/cache/semantic/ef5e51443530e94c966cc48288ad33926aaa7884da511e39428f85af1a870ede.json) |  | 2026-07-08 | 520B | `6ae849f4` |
| [graphify-out/cache/semantic/ef77100490f6dd423aa5739fa0e2cd62d64e2652f6641d37492edb1e650a00ba.json](graphify-out/cache/semantic/ef77100490f6dd423aa5739fa0e2cd62d64e2652f6641d37492edb1e650a00ba.json) |  | 2026-07-08 | 5KB | `980bb13e` |
| [graphify-out/cache/semantic/ef9da43571de2e52a9a39c62085628352f0d133c1e76b33c14b7b0c827e7e101.json](graphify-out/cache/semantic/ef9da43571de2e52a9a39c62085628352f0d133c1e76b33c14b7b0c827e7e101.json) |  | 2026-07-08 | 349B | `9da44d1c` |
| [graphify-out/cache/semantic/f0503202b9242d2a2e44505ab3ea6a6b5ce4522a385a3fc1fccd7fe7ffa1214b.json](graphify-out/cache/semantic/f0503202b9242d2a2e44505ab3ea6a6b5ce4522a385a3fc1fccd7fe7ffa1214b.json) |  | 2026-07-08 | 876B | `3e84e408` |
| [graphify-out/cache/semantic/f0af98641a7966b7c82d97fc45efe57398a458059849dcf010d0316c8740f231.json](graphify-out/cache/semantic/f0af98641a7966b7c82d97fc45efe57398a458059849dcf010d0316c8740f231.json) |  | 2026-07-08 | 777B | `9e8611ce` |
| [graphify-out/cache/semantic/f1cb339e02a483367c6c1d7034d2d26fdf95132f860bcc17a97a579ebbc6a01d.json](graphify-out/cache/semantic/f1cb339e02a483367c6c1d7034d2d26fdf95132f860bcc17a97a579ebbc6a01d.json) |  | 2026-07-08 | 853B | `92a4d04a` |
| [graphify-out/cache/semantic/f2d96f07c580dff86252cb9300bd3cb5f945ad87b9ed0370683ef8a67cf0c504.json](graphify-out/cache/semantic/f2d96f07c580dff86252cb9300bd3cb5f945ad87b9ed0370683ef8a67cf0c504.json) |  | 2026-07-08 | 695B | `aa854753` |
| [graphify-out/cache/semantic/f2f408d0de2feb49f1fa8d04bd24cff288aa955e63f0e53fe06d2c570f7da10e.json](graphify-out/cache/semantic/f2f408d0de2feb49f1fa8d04bd24cff288aa955e63f0e53fe06d2c570f7da10e.json) |  | 2026-07-08 | 855B | `046333d4` |
| [graphify-out/cache/semantic/f3a7112d82fd5e950f9f1359a9740f1bb9cf3b557bc6d38a00c90f8526f3fa5b.json](graphify-out/cache/semantic/f3a7112d82fd5e950f9f1359a9740f1bb9cf3b557bc6d38a00c90f8526f3fa5b.json) |  | 2026-07-08 | 625B | `2fa5669e` |
| [graphify-out/cache/semantic/f3bcbc962e81cc0be4c166ef60097b239dfb6ec9b2a8fd2b16ca77ddc16b6a33.json](graphify-out/cache/semantic/f3bcbc962e81cc0be4c166ef60097b239dfb6ec9b2a8fd2b16ca77ddc16b6a33.json) |  | 2026-07-08 | 305B | `bfc90369` |
| [graphify-out/cache/semantic/f46f5a7ce50bc21127a5b67d354a7232fd030965e7d57695ac0ea4bf21474f2b.json](graphify-out/cache/semantic/f46f5a7ce50bc21127a5b67d354a7232fd030965e7d57695ac0ea4bf21474f2b.json) |  | 2026-07-08 | 859B | `c4fb0a9a` |
| [graphify-out/cache/semantic/f4d72959474867140b9775544f455cbcde70ee9d0eb723d731f40436ce6f8335.json](graphify-out/cache/semantic/f4d72959474867140b9775544f455cbcde70ee9d0eb723d731f40436ce6f8335.json) |  | 2026-07-08 | 2KB | `53a19343` |
| [graphify-out/cache/semantic/f4fff66661ca240d2cdfc9840b0db4a44f955f2ded08cfcf27f1336bce665002.json](graphify-out/cache/semantic/f4fff66661ca240d2cdfc9840b0db4a44f955f2ded08cfcf27f1336bce665002.json) |  | 2026-07-08 | 1KB | `134ea0db` |
| [graphify-out/cache/semantic/f603536cf6bd3d3fc8b62f3e06b64fab3b74c4f4cbacacaf06eebe58a04d43bd.json](graphify-out/cache/semantic/f603536cf6bd3d3fc8b62f3e06b64fab3b74c4f4cbacacaf06eebe58a04d43bd.json) |  | 2026-07-08 | 350B | `83bdf1ec` |
| [graphify-out/cache/semantic/f7809745b98e6eef8cc5a51a9d6379a8663aef99563a6ba315b87b7bec53eb90.json](graphify-out/cache/semantic/f7809745b98e6eef8cc5a51a9d6379a8663aef99563a6ba315b87b7bec53eb90.json) |  | 2026-07-08 | 2KB | `b3886f9f` |
| [graphify-out/cache/semantic/f7b041e54cb1ca7b1afb5073c77d099c36c36bff96cd65562aa1266e33d4b272.json](graphify-out/cache/semantic/f7b041e54cb1ca7b1afb5073c77d099c36c36bff96cd65562aa1266e33d4b272.json) |  | 2026-07-08 | 1KB | `96eb1c82` |
| [graphify-out/cache/semantic/f899f6ce4651dd6c9880d682202016dbef15efd8d8ac430117b02d4f204279cc.json](graphify-out/cache/semantic/f899f6ce4651dd6c9880d682202016dbef15efd8d8ac430117b02d4f204279cc.json) |  | 2026-07-08 | 696B | `8a366ad4` |
| [graphify-out/cache/semantic/f9193906585a3e84934d0a1700e5478544708c07d5ea31b44671c5e5a3c8aaa5.json](graphify-out/cache/semantic/f9193906585a3e84934d0a1700e5478544708c07d5ea31b44671c5e5a3c8aaa5.json) |  | 2026-07-08 | 349B | `65c61129` |
| [graphify-out/cache/semantic/fa1be4d2ca4054426a1884b70cb5ff52c6e5ac6bdb7ff9c4f131708a7a412677.json](graphify-out/cache/semantic/fa1be4d2ca4054426a1884b70cb5ff52c6e5ac6bdb7ff9c4f131708a7a412677.json) |  | 2026-07-08 | 937B | `1882843f` |
| [graphify-out/cache/semantic/fa35ae103eabbb6a798f1d4f8b4794939b6d77efc391f6f285f84dc50a3be9e4.json](graphify-out/cache/semantic/fa35ae103eabbb6a798f1d4f8b4794939b6d77efc391f6f285f84dc50a3be9e4.json) |  | 2026-07-08 | 581B | `a0aaa7cd` |
| [graphify-out/cache/semantic/fa72d341871d8c52f3abfe9c82488983558280f22b0ec405eb8ad6a2395083e9.json](graphify-out/cache/semantic/fa72d341871d8c52f3abfe9c82488983558280f22b0ec405eb8ad6a2395083e9.json) |  | 2026-07-08 | 359B | `36248414` |
| [graphify-out/cache/semantic/faa2d7795ffa94d2c81d9b44ef82f41bae49d454ed4e7e768d1983939e369ed9.json](graphify-out/cache/semantic/faa2d7795ffa94d2c81d9b44ef82f41bae49d454ed4e7e768d1983939e369ed9.json) |  | 2026-07-08 | 809B | `0b256d25` |
| [graphify-out/cache/semantic/fab5b0811d7423af27be19da8a27a7d0f8832b442ff1b8552cba5f94d8fd3f6e.json](graphify-out/cache/semantic/fab5b0811d7423af27be19da8a27a7d0f8832b442ff1b8552cba5f94d8fd3f6e.json) |  | 2026-07-08 | 347B | `0ee08b0b` |
| [graphify-out/cache/semantic/fc2888b605b45bfa25766f7f7872a8501b427da66326672bb93ad8c484381da7.json](graphify-out/cache/semantic/fc2888b605b45bfa25766f7f7872a8501b427da66326672bb93ad8c484381da7.json) |  | 2026-07-08 | 1KB | `8010a7a5` |
| [graphify-out/cache/semantic/fda6dd1e848de0105792aa224da56ceeceef790c0ee73eeb0bc0e361c9108172.json](graphify-out/cache/semantic/fda6dd1e848de0105792aa224da56ceeceef790c0ee73eeb0bc0e361c9108172.json) |  | 2026-07-08 | 1KB | `ff11309b` |
| [graphify-out/cache/semantic/fe00a7da307a191424bc3b4131c6fd5cc30746b734cce55a5f05f173ad9d8c9b.json](graphify-out/cache/semantic/fe00a7da307a191424bc3b4131c6fd5cc30746b734cce55a5f05f173ad9d8c9b.json) |  | 2026-07-08 | 1KB | `32844157` |
| [graphify-out/cache/semantic/fe102a1b0713a5cd9caaab32e07003b1691d47cd9ac49508d64b1f2fdddf20d1.json](graphify-out/cache/semantic/fe102a1b0713a5cd9caaab32e07003b1691d47cd9ac49508d64b1f2fdddf20d1.json) |  | 2026-07-08 | 1KB | `a6e9559b` |
| [graphify-out/cache/semantic/fe3d92409531b4b292d611353bdfab0636930c49697a915655744d310f7a098a.json](graphify-out/cache/semantic/fe3d92409531b4b292d611353bdfab0636930c49697a915655744d310f7a098a.json) |  | 2026-07-08 | 465B | `f685c5a4` |
| [graphify-out/cache/semantic/feef455b6ec55286be781e0d24941054560341062043d78d60d9f74138ffb961.json](graphify-out/cache/semantic/feef455b6ec55286be781e0d24941054560341062043d78d60d9f74138ffb961.json) |  | 2026-07-08 | 370B | `e83bd433` |
| [graphify-out/cache/semantic/ffab892cca599aab64f9017529f1fbf09d183ff2bfb40cf6952e827231c66395.json](graphify-out/cache/semantic/ffab892cca599aab64f9017529f1fbf09d183ff2bfb40cf6952e827231c66395.json) |  | 2026-07-08 | 7KB | `ad83fc8b` |
| [graphify-out/cache/semantic/ffc0013009bda95d2ae73888908e50b640c9fc90a76b4415620853ed29333eee.json](graphify-out/cache/semantic/ffc0013009bda95d2ae73888908e50b640c9fc90a76b4415620853ed29333eee.json) |  | 2026-07-08 | 363B | `2d6402e9` |
| [opencode.json](opencode.json) |  | 2026-06-20 | 184B | `45617caa` |
| [package-lock.json](package-lock.json) |  | 2026-07-20 | 10KB | `f5f1777e` |
| [package.json](package.json) |  | 2026-07-20 | 60B | `50d532ca` |

