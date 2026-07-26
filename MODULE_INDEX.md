# MODULE INDEX
> Живой указатель модулей проекта SoSimple

Компактный индекс модулей. Для навигации читать точечно: `rg <keyword> MODULE_INDEX.md`, затем открывать нужный файл или docs.

---

## Processing

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [label_main.py](processing/label_main.py) | CLI оркестратор pipeline | `Nero.csv` → `*_labeled.csv` | [docs](docs/processing/label_main.py.md) | 🏁 |
| [fractal_preprocessing.py](processing/fractal_preprocessing.py) | Общая сортировка фракталов внутри строки для training/online | DataFrame `fractal*` → отсортированный DataFrame | [docs](docs/processing/fractal_preprocessing.py.md) | ✅ |
| [online_causal_preprocessing.py](processing/online_causal_preprocessing.py) | Online-safe preprocessing | runtime snapshot → preprocessed snapshot | [docs](docs/processing/online_causal_preprocessing.py.md) | ✅ |
| [label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | sorted CSV → labeled CSV | [docs](docs/processing/label_signals.py.md) | 🏁 |
| [normalize.py](processing/normalize.py) | Построчная нормализация признаков | labeled CSV → normalized CSV + `*.npy` | [docs](docs/processing/normalize.py.md) | 🏁 |
| [purge_split.py](processing/purge_split.py) | Purge/embargo границ train/val/test | split CSV → purged split CSV | — | ✅ |
| [denormalize_updn.py](processing/denormalize_updn.py) | Восстановление Up/Dn из нормализованных величин | normalized Up/Dn → price Up/Dn | — | ✅ |
| [label_audit.py](processing/label_audit.py) | Аудит разметки и контрактов labels | labeled CSV → audit summary | — | ✅ |
| [rebuild_xauusd_top_level_updn.py](processing/rebuild_xauusd_top_level_updn.py) | Пересборка top-level Up/Dn для XAUUSD | labeled CSV → rebuilt CSV | — | ✅ |

## Statistics

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | `Nero.csv` → `.json`, `.csv` | [docs](docs/statistics/statistics.py.md) | 🏁 |
| [EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | `Nero.csv` → `plots/`, `.csv` | [docs](docs/statistics/EDA.ipynb.md) | 🏁 |
| [signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | `ml_signals.csv` + `Nero_*_labeled.csv` + `*.npy` + log → dossiers, CSV | [docs](docs/statistics/signal_tracer.py.md) | ✅ |
| [analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | `all_trades.csv` + OHLC → отчёт | — | 🏁 |
| [data_contract_smoke_check.py](statistics/data_contract_smoke_check.py) | Быстрая проверка контрактов данных | CSV → smoke verdict | — | ✅ |

## API

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | `Nero_*_labeled.csv` + checkpoint → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_entry_path_v1_signals.py](API/export_entry_path_v1_signals.py) | Экспорт frozen `entry_path_v1` signals | predictions + rule → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) | Экспорт frozen quantile signals | predictions + rule → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_take_skip_trailing_stop_v2_signals.py](API/export_take_skip_trailing_stop_v2_signals.py) | Экспорт take/skip v2 signals | predictions + rule → signals/metadata | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [telemetry_signal_watcher.py](API/telemetry_signal_watcher.py) | Online watcher telemetry-контура | `Nero.csv` + checkpoint → signals/state | [docs](docs/API/telemetry_signal_watcher.py.md) | ✅ |
| [api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, общий live-safe preprocessing, ML-сигнал | HTTP → ML prediction | [docs](docs/API/api_server.py.md) | 🔬 |
| [signal_research.py](API/signal_research.py) | Research CLI: качество ML-сигналов по реальным OHLC (Variant 2/3) | `ml_signals.csv` + OHLC → отчёт | — | 🏁 |
| [signal_path_atlas.py](API/signal_path_atlas.py) | Research CLI: ATR-normalized Signal Path Atlas, path archetypes, holdout validation | ML-сигналы → path tensor, archetypes | — | 🏁 |
| [signal_quality_research.py](API/signal_quality_research.py) | Signal Quality Filter Research (Variant 4): multi-horizon prediction features как фильтры | → отчёт, artifacts | — | 🏁 |
| [exit_policy_research.py](API/exit_policy_research.py) | Offline research: сравнение ML-политик выхода и position management | `ml_signals.csv` → отчёт | — | 🏁 |
| [test_api_client.py](API/test_api_client.py) | Интеграционный тест REST API-сервера (MT4) | — | — | 🏁 |

## MT/MQL4

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | Tick data → `Nero.csv` | [docs](docs/MT/lib_PIC.mqh.md) | ⚠️ |
| [lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, single/multi-position telemetry trading | `ml_signals.csv` → MLP open/close logs | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| `Вспомогательные .mqh` | Торговая логика и индикаторы | — | — | 📦 |

## ML

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | `*_labeled.csv` → in-memory tensors, `*.npy` cache | — | ✅ |
| [losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | — | — | ✅ |
| [utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | — | — | ✅ |
| [experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | results → `reports/experiments_log.csv` | — | 🏁 |
| [models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | ✅ |
| [models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [models/take_skip_dual_stream_transformer.py](ML/models/take_skip_dual_stream_transformer.py) | Dual-stream Transformer для `take_skip_v2`: sequence branch + `lib_PIC` feature branch | (batch, seq, 20) + engineered → (batch, 15) | — | ✅ |
| [train.py](ML/train.py) | Обучение ML-моделей; `--output-dir` изолирует checkpoint/result для seed/device аудита | DataLoader → `checkpoints/` или `--output-dir`, `plots/` | [docs](docs/ML/neural_networks.md) | ✅ |
| [optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | DataLoader → `reports/optuna_*.json` | — | 🏁 |
| [compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | DataLoader → `reports/architecture_comparison.md` | — | 🏁 |
| [evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | checkpoint + test CSV → `reports/evaluate_test_*.md` | — | ✅ |
| [threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | checkpoint + val CSV → `reports/threshold_analysis.md` | — | ✅ |
| [reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | — → `reports/reproducibility_report.md` | — | 🏁 |
| [benchmark_fractal_stop_breach.py](ML/baseline/benchmark_fractal_stop_breach.py) | Stage 1 Fractal Stop Breach | labeled CSV → breach reports | — | ✅ |
| [benchmark_fractal_stop_fav.py](ML/baseline/benchmark_fractal_stop_fav.py) | Stage 2 Fractal Stop Fav | labeled CSV → fav reports | — | ✅ |
| [oracle_fractal_stop_fav.py](ML/baseline/oracle_fractal_stop_fav.py) | Oracle Fractal Stop Fav | labeled CSV → oracle report | — | ✅ |
| [benchmark_fractal_stop_stage4.py](ML/baseline/benchmark_fractal_stop_stage4.py) | Stage 4 Fractal Stop benchmark | labeled CSV + OHLC → stage4 reports | — | ✅ |
| [benchmark_fractal_stop_stage4_1.py](ML/baseline/benchmark_fractal_stop_stage4_1.py) | Stage 4.1 controls | labeled CSV + OHLC → `stage4_1.json` | — | ✅ |
| [benchmark_fractal_stop_stage4_2.py](ML/baseline/benchmark_fractal_stop_stage4_2.py) | Stage 4.2 corrected diagnostic | labeled CSV + OHLC → `stage4_2_*` | — | ✅ |
| [diagnose_stage4_3.py](ML/baseline/diagnose_stage4_3.py) | Stage 4.3 loss decomposition | labeled CSV + OHLC → diagnostics JSON | [docs](docs/ML/diagnose_stage4_3.py.md) | ✅ |
| [diagnose_stage4_4.py](ML/baseline/diagnose_stage4_4.py) | Stage 4.4 micro-check | labeled CSV + OHLC → micro-check JSON | [docs](docs/ML/diagnose_stage4_4.py.md) | ✅ |
| [diagnose_stage5_prep.py](ML/baseline/diagnose_stage5_prep.py) | Stage 5 prep diagnostic | labeled CSV + OHLC → diagnostics JSON | [docs](docs/ML/diagnose_stage5_prep.py.md) | ✅ |
| [benchmark_stage5_transformer_breach.py](ML/baseline/benchmark_stage5_transformer_breach.py) | Stage 5 Transformer Breach | labeled CSV → `stage5_*` | [docs](docs/ML/benchmark_stage5_transformer_breach.py.md) | 🏁 |
| [benchmark_stage6_outcome_based.py](ML/baseline/benchmark_stage6_outcome_based.py) | Stage 6.0 outcome-based triple-barrier baseline | labeled CSV + OHLC → `stage6_0_*` | — | ✅ |
| [benchmark_stage6_1_relative_geometry.py](ML/baseline/benchmark_stage6_1_relative_geometry.py) | Stage 6.1 relative fractal geometry profiles | labeled CSV + OHLC → `stage6_1_*` | — | ✅ |
| [benchmark_stage6_2_price_action.py](ML/baseline/benchmark_stage6_2_price_action.py) | Stage 6.2 price-action family | labeled CSV + OHLC → `stage6_2_*` | [docs](docs/ML/benchmark_stage6_2_price_action.py.md) | ✅ |
| [analyze_stage6_2_range_w1_postmortem.py](ML/baseline/analyze_stage6_2_range_w1_postmortem.py) | Stage 6.2 post-mortem | Stage 6.2 JSON → postmortem report | [docs](docs/ML/analyze_stage6_2_range_w1_postmortem.py.md) | ✅ |
| [benchmark_stage6_3_h6_feature_parity.py](ML/baseline/benchmark_stage6_3_h6_feature_parity.py) | Stage 6.3 H6/H12 feature parity audit | Stage 6 features → `stage6_3_*` | — | ✅ |
| [benchmark_regression_updn_target_foundation.py](ML/baseline/benchmark_regression_updn_target_foundation.py) | Regression Up/Dn target foundation | labeled CSV → `regression_updn_target_foundation.json` | — | ✅ |
| [analyze_regression_updn_already_moved_audit.py](ML/baseline/analyze_regression_updn_already_moved_audit.py) | Audit: движение до next-open entry | foundation artifacts + OHLC → audit JSON/CSV | — | ✅ |
| [benchmark_next_open_entry_updn_foundation.py](ML/baseline/benchmark_next_open_entry_updn_foundation.py) | Next-open entry Up/Dn foundation | labeled CSV + OHLC → foundation JSON/CSV | — | ✅ |
| [benchmark_fractal0_price_entry_mechanics.py](ML/baseline/benchmark_fractal0_price_entry_mechanics.py) | Oracle-preflight входа через возврат цены к зоне `fractal0_price` | labeled CSV + OHLC → oracle JSON/CSV | [docs](docs/ML/benchmark_fractal0_price_entry_mechanics.py.md) | ✅ |
| [benchmark_fractal0_entry_exit_grid.py](ML/baseline/benchmark_fractal0_entry_exit_grid.py) | Fractal0 entry/exit grid со stop-policy grid, OHLC/M5 execution ordering, ML-exit и permutation correction | labeled CSV + H1/M5 OHLC + frozen movement scores → entry/exit/stop-grid JSON/CSV | [docs](docs/ML/benchmark_fractal0_entry_exit_grid.py.md) | ✅ |
| [benchmark_fractal0_entry_quality_filter.py](ML/baseline/benchmark_fractal0_entry_quality_filter.py) | ML-entry, rich-entry и normalized rich-entry quality фильтр для Fractal0 E3 поверх stop-grid winner без нового симулятора | stop-grid artifact + labeled CSV + H1/M5 OHLC + movement scores → entry-quality/rich-entry/normalized JSON/CSV | [docs](docs/ML/benchmark_fractal0_entry_quality_filter.py.md) | ✅ |
| [audit_time_only_robustness.py](ML/baseline/audit_time_only_robustness.py) | Validation-slice audit fixed normalized `time_only` winner без нового поиска и без `locked_test` | normalized rich-entry JSON/CSV → `time_only_robustness_audit*` JSON/CSV | [docs](docs/ML/audit_time_only_robustness.py.md) | ✅ |
| [audit_leaderboard_robustness.py](ML/baseline/audit_leaderboard_robustness.py) | Validation-slice audit 11 fixed normalized rich-entry leaderboard input rows без нового поиска и без `locked_test` | normalized rich-entry JSON/CSV → `leaderboard_robustness_audit*` JSON/CSV | [docs](docs/ML/audit_leaderboard_robustness.py.md) | ✅ |
| [audit_leaderboard_closure.py](ML/baseline/audit_leaderboard_closure.py) | Closure/disclosure audit для 11 fixed leaderboard rows: cost, calendar, timezone, sequential positions и multi-seed без нового поиска | normalized rich-entry JSON/CSV → `leaderboard_closure_audit*` JSON/CSV | [docs](docs/ML/audit_leaderboard_closure.py.md) | ✅ |
| [fractal0_fixed11_internal_closure_rerun.py](ML/baseline/fractal0_fixed11_internal_closure_rerun.py) | Producer-level fixed11 internal closure rerun: stress-cost, timezone/calendar и multi-seed без `locked_test` | normalized rich-entry JSON/CSV + saved fixed cutoffs → `fractal0_fixed11_internal_closure_rerun*` JSON/CSV | [docs](docs/ML/fractal0_fixed11_internal_closure_rerun.py.md) | ✅ |
| [audit_fractal0_fixed11_candidate.py](ML/baseline/audit_fractal0_fixed11_candidate.py) | Read-only candidate audit для `fractal0_fixed11_rich_entry_locked_test*` без нового выбора по `locked_test` | locked-test JSON/CSV → `fractal0_fixed11_candidate_audit*` JSON/CSV | [docs](docs/ML/audit_fractal0_fixed11_candidate.py.md) | ✅ |
| [benchmark_entry_based_updn_price_feature_matrix.py](ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py) | Entry-based Up/Dn price-feature matrix | foundation splits → matrix JSON/CSV | — | ✅ |
| [benchmark_entry_based_updn_fractal_selection_ablation.py](ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py) | Entry-based fractal ablation | foundation splits → ablation JSON/CSV | [docs][docs-entry-ablation] | ✅ |
| [benchmark_entry_based_next_open_closeout.py](ML/baseline/benchmark_entry_based_next_open_closeout.py) | Entry-based closeout runner | foundation splits → closeout JSON/CSV | [docs][docs-entry-closeout] | ✅ |
| [benchmark_entry_based_powerful_tabular.py](ML/baseline/benchmark_entry_based_powerful_tabular.py) | Entry-based tabular runner | foundation splits → tabular JSON/CSV | [docs](docs/ML/benchmark_entry_based_powerful_tabular.py.md) | ✅ |
| [benchmark_entry_based_sequence_transformer.py](ML/baseline/benchmark_entry_based_sequence_transformer.py) | Entry-based sequence Transformer runner | foundation splits → sequence JSON/CSV | [docs](docs/ML/benchmark_entry_based_sequence_transformer.py.md) | ✅ |
| [benchmark_entry_based_amplitude_movement.py](ML/baseline/benchmark_entry_based_amplitude_movement.py) | Entry-based amplitude movement-regime audit | foundation splits → amplitude movement JSON/CSV | [docs](docs/ML/benchmark_entry_based_amplitude_movement.py.md) | ✅ |
| [benchmark_entry_based_movement_filter.py](ML/baseline/benchmark_entry_based_movement_filter.py) | Entry-based simple movement filter | amplitude artifact → movement filter JSON/CSV | [docs](docs/ML/benchmark_entry_based_movement_filter.py.md) | ⚠️ |
| [benchmark_entry_based_movement_filter_freeze.py](ML/baseline/benchmark_entry_based_movement_filter_freeze.py) | Entry-based movement filter freeze runner | movement filter + amplitude artifacts → freeze JSON/CSV | [docs](docs/ML/benchmark_entry_based_movement_filter_freeze.py.md) | ✅ |
| [benchmark_direction_inside_frozen_movement_regime.py](ML/baseline/benchmark_direction_inside_frozen_movement_regime.py) | Direction check inside frozen movement mask | freeze JSON/CSV + entry-based splits → direction contract JSON/CSV | [docs](docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md) | ✅ |
| [benchmark_direction_inside_frozen_movement_regime_rich_features.py](ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py) | Rich feature direction check and narrow seed replication inside frozen movement mask with resume/progress | freeze scores + entry-based splits → rich direction JSON/CSV | [docs](docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md) | ✅ |
| [fractal_breach_transformer.py](ML/models/fractal_breach_transformer.py) | Stage 5 breach Transformer | — | [docs](docs/ML/fractal_breach_transformer.py.md) | 🏁 |
| [diagnose_stage4_5_exit_mechanics.py](ML/baseline/diagnose_stage4_5_exit_mechanics.py) | Stage 4.5 exit mechanics | labeled CSV + OHLC → exit JSON | [docs](docs/ML/diagnose_stage4_5_exit_mechanics.py.md) | ✅ |
| [benchmark_stage4_6_clean_cycle.py](ML/baseline/benchmark_stage4_6_clean_cycle.py) | Stage 4.6 clean cycle | labeled CSV + OHLC → cycle JSON | [docs](docs/ML/benchmark_stage4_6_clean_cycle.py.md) | ✅ |
| [baseline_candidate_source.py](ML/baseline_candidate_source.py) | Stage 07 baseline-first runner для candidate-source v2 | train/validation labeled CSV → `stage07_baselines.json` | [docs](docs/ML/baseline_candidate_source.py.md) | ✅ |
| [model_sweep_candidate_source.py](ML/model_sweep_candidate_source.py) | Stage 08 model sweep | labeled CSV → sweep reports | [docs](docs/ML/model_sweep_candidate_source.py.md) | ✅ |
| [stage09_stability_refreeze.py](ML/stage09_stability_refreeze.py) | Stage 09 stability refreeze | checkpoint + validation → frozen rule | [docs](docs/ML/stage09_stability_refreeze.py.md) | ✅ |
| [stage10_frozen_test_oos.py](ML/stage10_frozen_test_oos.py) | Stage 10 frozen OOS test | frozen rule + test split → OOS reports | [docs](docs/ML/stage10_frozen_test_oos.py.md) | ✅ |
| [validation_freeze.py](ML/validation_freeze.py) | Stage 09 — deterministic Transformer training + checkpoint + round-trip verification (does NOT generate frozen rule) | train/validation CSV → checkpoint + normalizer | — | ✅ |
| [baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | `*_labeled.csv` → `baseline/reports/`, `baseline/plots/` | [docs](docs/ML/baseline_experiments.py.md) | 🏁 |
| [conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | val CSV + checkpoint → `conformal/conformal_quantiles.json` | [docs](docs/ML/conformal_prediction.md) | 🏁 |
| [tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | TB probabilities → signal | — | ✅ |
| [tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | val data → calibrated probabilities | — | 🏁 |
| [entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | — | — | ✅ |
| [entry_path_feature_bank.py](ML/entry_path_feature_bank.py) | Entry path feature bank: оконные сводки строки и row-wise context features | labeled CSV → engineered feature columns | — | ✅ |
| [feature_screen_entry_path.py](ML/feature_screen_entry_path.py) | Диагностический feature screening для entry_path_v1 | labeled CSV / feature frame → MI ranking | — | ✅ |
| [feature_importance_diagnostics.py](ML/feature_importance_diagnostics.py) | Диагностика важности feature groups | labeled CSV → importance reports | [docs](docs/ML/feature_importance_diagnostics.py.md) | ✅ |
| [feature_bank_comparison_diagnostics.py](ML/feature_bank_comparison_diagnostics.py) | Сравнение feature-bank вариантов | labeled CSV → comparison reports | [docs](docs/ML/feature_bank_comparison_diagnostics.py.md) | ✅ |
| [lib_pic_feature_profiles.py](ML/lib_pic_feature_profiles.py) | Профили признаков `lib_PIC` | fractal columns → feature profiles | [docs](docs/ML/lib_pic_feature_profiles.py.md) | ✅ |
| [lib_pic_geometry_feature_bank.py](ML/lib_pic_geometry_feature_bank.py) | Производные признаки геометрии уровней `lib_PIC` | fractal columns → geometry feature columns | [docs](docs/ML/lib_pic_geometry_feature_bank.py.md) | ✅ |
| [lib_pic_path_reaction_feature_bank.py](ML/lib_pic_path_reaction_feature_bank.py) | Path-reaction признаки `lib_PIC` | fractal columns → feature columns | [docs](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | ✅ |
| [entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | — | — | ✅ |
| [trailing_stop_target_task.py](ML/trailing_stop_target_task.py) | Trailing-stop target task: target contract, export helpers и metrics | — | — | ✅ |
| [trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | — | — | ✅ |
| [entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | → filtered signals | — | ✅ |
| [export_entry_path_predictions.py](ML/export_entry_path_predictions.py) | Entry-path inference export | labeled CSV + checkpoint → predictions | [docs](docs/ML/export_entry_path_predictions.py.md) | ✅ |
| [run_entry_path_live_safe_retrain.py](ML/run_entry_path_live_safe_retrain.py) | Multi-seed live-safe retrain | `DATA/Nero_*` → seed reports | [docs](docs/ML/run_entry_path_live_safe_retrain.py.md) | ✅ |
| [run_entry_path_quantile_live_safe_retrain.py](ML/run_entry_path_quantile_live_safe_retrain.py) | Multi-seed quantile retrain | `DATA/Nero_*` → seed reports | [docs](docs/ML/run_entry_path_quantile_live_safe_retrain.py.md) | ✅ |
| [prepare_entry_path_mt4_parity.py](ML/prepare_entry_path_mt4_parity.py) | Entry-path MT4 parity export | predictions → rule/signals | [docs](docs/ML/prepare_entry_path_mt4_parity.py.md) | ✅ |
| [benchmark_entry_path_signal_only_ablation.py](ML/benchmark_entry_path_signal_only_ablation.py) | Signal-only ablation | prediction CSV → ablation report | [docs](docs/ML/benchmark_entry_path_signal_only_ablation.py.md) | ✅ |
| [benchmark_entry_path_all_rows_ranking.py](ML/benchmark_entry_path_all_rows_ranking.py) | All-rows ranking benchmark | source/predictions → ranking report | [docs](docs/ML/benchmark_entry_path_all_rows_ranking.py.md) | ✅ |
| [benchmark_entry_path_causal_surrogate.py](ML/benchmark_entry_path_causal_surrogate.py) | Causal surrogate benchmark | source/predictions → surrogate report | [docs](docs/ML/benchmark_entry_path_causal_surrogate.py.md) | ✅ |
| [benchmark_entry_path_direct_bar_model.py](ML/benchmark_entry_path_direct_bar_model.py) | Direct bar model benchmark | source/OHLC → direct-bar report | [docs](docs/ML/benchmark_entry_path_direct_bar_model.py.md) | ✅ |
| [export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export quantile predictions | checkpoint → predictions CSV | — | ✅ |
| [benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | prediction CSVs + frozen rule → reports | — | ✅ |
| [entry_path_v1_quantile_ensemble.py](ML/entry_path_v1_quantile_ensemble.py) | Агрегация quantile-прогнозов по нескольким seed для n-boost проверки | seed prediction CSVs → mean/vote masks | — | ✅ |
| [benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | prediction CSVs → frequency verdict | — | 🏁 |
| [benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_trailing_stop_target.py](ML/benchmark_trailing_stop_target.py) | Validation-first benchmark для trailing-stop target exports | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_take_skip_mt4_trailing_sequential.py](ML/benchmark_take_skip_mt4_trailing_sequential.py) | Take/skip MT4 trailing comparison | signals + OHLC → summary JSON | — | ✅ |
| [benchmark_take_skip_lib_pic_selection.py](ML/benchmark_take_skip_lib_pic_selection.py) | Take/skip selection by `lib_PIC` | predictions + source → selection report | [docs](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | ✅ |
| [benchmark_execution_policy_v2.py](ML/benchmark_execution_policy_v2.py) | Execution policy benchmark | signals + OHLC → policy report | [docs](docs/ML/benchmark_execution_policy_v2.py.md) | ✅ |
| [benchmark_signal_export_parity.py](ML/benchmark_signal_export_parity.py) | Signal export parity audit | signals + tester log → parity report | [docs](docs/ML/benchmark_signal_export_parity.py.md) | ✅ |
| [benchmark_telemetry_frequency_calibration.py](ML/benchmark_telemetry_frequency_calibration.py) | Telemetry frequency calibration | prediction CSV → calibration report | [docs][docs-telemetry-frequency] | ✅ |
| [telemetry_daily_reconciliation.py](ML/telemetry_daily_reconciliation.py) | Daily telemetry reconciliation | signals + MT4 log → daily report | [docs](docs/ML/telemetry_daily_reconciliation.py.md) | ✅ |
| [online_tester_reconciliation.py](ML/online_tester_reconciliation.py) | Online/tester reconciliation | signals + event log → reconciliation | [docs](docs/ML/online_tester_reconciliation.py.md) | ✅ |
| [benchmark_cross_instrument_robustness.py](ML/benchmark_cross_instrument_robustness.py) | Cross-instrument robustness | manifest + OHLC → robustness report | [docs](docs/ML/benchmark_cross_instrument_robustness.py.md) | ✅ |
| [benchmark_system_correlation.py](ML/benchmark_system_correlation.py) | System correlation benchmark | manifest + trades → correlation report | [docs](docs/ML/benchmark_system_correlation.py.md) | ✅ |
| [live_safe_audit.py](ML/live_safe_audit.py) | Core-типы live-safe audit и свод feature verdict → system verdict | feature traces → PASS/FAIL/UNKNOWN | [docs](docs/ML/live_safe_audit.py.md) | ✅ |
| [live_safe_audit_registry.py](ML/live_safe_audit_registry.py) | Реестр прибыльных ML-систем для повторного live-safe audit | frozen artifacts → audit scope | [docs](docs/ML/live_safe_audit_registry.py.md) | ✅ |
| [run_live_safe_ml_audit.py](ML/run_live_safe_ml_audit.py) | CLI для audit inventory, feature trace, legacy replay и verdict | registry + artifacts → `reports/live_safe_ml_audit/` | [docs](docs/ML/run_live_safe_ml_audit.py.md) | ✅ |
| [run_take_skip_lib_pic_feature_matrix.py](ML/run_take_skip_lib_pic_feature_matrix.py) | Take/skip `lib_PIC` feature matrix | labeled CSV → matrix reports | [docs](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | 🚧 |
| [run_take_skip_original_contour_feature_matrix.py](ML/run_take_skip_original_contour_feature_matrix.py) | Original-contour feature matrix | labeled CSV → matrix reports | [docs][docs-original-contour] | 🚧 |
| [run_trailing_stop_target_matrix.py](ML/run_trailing_stop_target_matrix.py) | Оркестратор bounded matrix для `trailing_stop_target_v1` | configs → `reports/trailing_stop_target_matrix` | — | ✅ |
| [run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | config → `reports/trailing_stop_target_quantile` | — | ✅ |
| [run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | configs → `reports/track_a_max_out_matrix*` | — | ✅ |
| [models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | (batch, 100, 20) → multi-head output | — | ✅ |
| [models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | (batch, seq, feat) + engineered → multi-head output | — | ✅ |
| [models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | (batch, 100, 20) → multi-head output | — | ✅ |
| [models/trailing_stop_target_quantile_transformer.py](ML/models/trailing_stop_target_quantile_transformer.py) | Trailing-stop quantile Transformer | sequence tensor → quantiles | — | ✅ |
| [ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | DataLoader → отчёт | — | 🏁 |
| [benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | DataLoader → JSON отчёт | — | 🏁 |
| [benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | — → JSON отчёт | — | 🏁 |
| [prepare_raw_features.py](ML/prepare_raw_features.py) | Извлечение сырых признаков из OHLC для direct-direction (Phase 0) | OHLC → raw features CSV | — | ✅ |
| [benchmark_buy_only_direction.py](ML/benchmark_buy_only_direction.py) | BUY-only RF с исправленными признаками (Phase A/B/D rebuild) | raw features + OHLC → benchmark report | — | ✅ |
| [benchmark_entry_path_binary_direction.py](ML/benchmark_entry_path_binary_direction.py) | Binary-direction benchmark для entry_path | source/prediction CSV → report | — | ✅ |
| [benchmark_entry_path_fractal_level_signal.py](ML/benchmark_entry_path_fractal_level_signal.py) | Fractal-level signal benchmark для entry_path | labeled CSV → report | — | ✅ |
| [benchmark_entry_path_fractal_level_direct_direction.py](ML/benchmark_entry_path_fractal_level_direct_direction.py) | Fractal-level direct-direction benchmark | labeled CSV → report | — | ✅ |
| [benchmark_entry_path_score_direction.py](ML/benchmark_entry_path_score_direction.py) | Score-direction benchmark для entry_path | prediction CSV → report | — | ✅ |
| [entry_path_direct_direction_targets.py](ML/entry_path_direct_direction_targets.py) | Target helpers для direct direction | labeled CSV → direction targets | — | ✅ |
| [entry_path_level_targets.py](ML/entry_path_level_targets.py) | Target helpers для fractal-level entry path | labeled CSV → level targets | — | ✅ |
| [fractal_level_feature_builder.py](ML/fractal_level_feature_builder.py) | Feature builder для fractal-level задач | fractal columns → feature frame | — | ✅ |
| [multi_scale_fractal_features.py](ML/multi_scale_fractal_features.py) | Multi-scale fractal feature bank | fractal columns → feature frame | — | ✅ |
| [export_take_skip_v2_predictions.py](ML/export_take_skip_v2_predictions.py) | Экспорт take/skip v2 predictions | checkpoint + CSV → predictions CSV | — | ✅ |
| [take_skip_trailing_stop_task.py](ML/take_skip_trailing_stop_task.py) | Task helpers для take/skip trailing stop | predictions → target/metrics | — | ✅ |
| [take_skip_trailing_stop_v2_task.py](ML/take_skip_trailing_stop_v2_task.py) | Task helpers для take/skip v2 | predictions → target/metrics | — | ✅ |
| [run_take_skip_trailing_stop_matrix.py](ML/run_take_skip_trailing_stop_matrix.py) | Matrix runner для take/skip trailing stop | configs → matrix reports | — | ✅ |
| [run_take_skip_trailing_stop_v2_matrix.py](ML/run_take_skip_trailing_stop_v2_matrix.py) | Matrix runner для take/skip v2 | configs → matrix reports | — | ✅ |
| **Legacy / auxiliary research scripts** | Старые и разовые research-скрипты: Stage 3, limit-order, TB, quantile, walk-forward, feature-ablation | code → reports | — | 📦 |
| **Direct Direction Rebuild** | Эксперименты завершены с честным отрицательным вердиктом: frozen test провален (PF < 0.8 на test). Направление признано бесперспективным в текущей постановке. | — | — | 🏁 |

## Tests

| Модуль | Тестирует | Docs | Статус |
|--------|-----------|------|--------|
| [test_label_updn.py](tests/test_label_updn.py) | `processing/label_signals.py` — parse_fractal, label_updn | [docs](docs/tests/tests.md) | ✅ |
| [test_inverse_piecewise.py](tests/test_inverse_piecewise.py) | `processing/normalize.py` + `statistics/signal_tracer.py` — round-trip piecewise | [docs](docs/tests/tests.md) | ✅ |
| [test_signal_research.py](tests/test_signal_research.py) | `API/signal_research.py` — ATR14, excursions, barriers, split | [docs](docs/tests/tests.md) | ✅ |
| [test_signal_path_atlas.py](tests/test_signal_path_atlas.py) | `API/signal_path_atlas.py` — calendar split, path tensor, archetypes, CLI | [docs](docs/tests/tests.md) | ✅ |
| [test_signal_quality_research.py](tests/test_signal_quality_research.py) | `API/signal_quality_research.py` — filter features, variance check, tree, holdout | [docs](docs/tests/tests.md) | ✅ |
| [test_trade_target_labels.py](tests/test_trade_target_labels.py) | `processing/label_signals.py` — trade target labels | — | ✅ |
| [test_entry_path_labels.py](tests/test_entry_path_labels.py) | `processing/label_signals.py` — entry_path_v1 helpers | — | ✅ |
| [test_trailing_stop_target_labels.py](tests/test_trailing_stop_target_labels.py) | `processing/label_signals.py` — trailing-stop target labels | — | ✅ |
| [test_entry_path_feature_bank.py](tests/test_entry_path_feature_bank.py) | `ML/entry_path_feature_bank.py` | — | ✅ |
| [test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | — | ✅ |
| [test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | — | ✅ |
| [test_trailing_stop_target_task.py](tests/test_trailing_stop_target_task.py) | `ML/trailing_stop_target_task.py` и trailing-stop export/evaluate wiring | — | ✅ |
| [test_trailing_stop_target_quantile_task.py](tests/test_trailing_stop_target_quantile_task.py) | `ML/trailing_stop_target_quantile_task.py` и train/evaluate/export wiring | — | ✅ |
| [test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | — | ✅ |
| [test_entry_path_dual_stream_transformer.py](tests/test_entry_path_dual_stream_transformer.py) | `ML/models/entry_path_dual_stream_transformer.py` | — | ✅ |
| [test_entry_path_loader_seq_len.py](tests/test_entry_path_loader_seq_len.py) | `ML/data_loader.py` — `entry_path_v1` sequence length contract | — | ✅ |
| [test_ml_fractal_parser_contract.py](tests/test_ml_fractal_parser_contract.py) | `ML/` — запрет использовать parser разметки как ML feature extractor | — | ✅ |
| [test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | — | ✅ |
| [test_trailing_stop_target_quantile_model.py](tests/test_trailing_stop_target_quantile_model.py) | `ML/models/trailing_stop_target_quantile_transformer.py` | — | ✅ |
| [test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | — | ✅ |
| [test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | — | ✅ |
| [test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | — | ✅ |
| [test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | — | ✅ |
| [test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | — | ✅ |
| [test_feature_screen_entry_path.py](tests/test_feature_screen_entry_path.py) | `ML/feature_screen_entry_path.py` | — | ✅ |
| [test_feature_importance_diagnostics.py](tests/test_feature_importance_diagnostics.py) | `ML/feature_importance_diagnostics.py` | — | ✅ |
| [test_feature_bank_comparison_diagnostics.py](tests/test_feature_bank_comparison_diagnostics.py) | `ML/feature_bank_comparison_diagnostics.py` | — | ✅ |
| [test_lib_pic_feature_profiles.py](tests/test_lib_pic_feature_profiles.py) | `ML/lib_pic_feature_profiles.py` | — | ✅ |
| [test_lib_pic_geometry_feature_bank.py](tests/test_lib_pic_geometry_feature_bank.py) | `ML/lib_pic_geometry_feature_bank.py` | — | ✅ |
| [test_lib_pic_path_reaction_feature_bank.py](tests/test_lib_pic_path_reaction_feature_bank.py) | `ML/lib_pic_path_reaction_feature_bank.py` | — | ✅ |
| [test_benchmark_take_skip_lib_pic_selection.py](tests/test_benchmark_take_skip_lib_pic_selection.py) | `ML/benchmark_take_skip_lib_pic_selection.py` | — | ✅ |
| [test_take_skip_lib_pic_feature_matrix.py](tests/test_take_skip_lib_pic_feature_matrix.py) | `ML/run_take_skip_lib_pic_feature_matrix.py` и `ML/models/take_skip_dual_stream_transformer.py` | — | ✅ |
| [test_take_skip_original_contour_feature_matrix.py](tests/test_take_skip_original_contour_feature_matrix.py) | `ML/run_take_skip_original_contour_feature_matrix.py` | — | ✅ |
| [test_benchmark_entry_path_v1_frequency.py](tests/test_benchmark_entry_path_v1_frequency.py) | `ML/benchmark_entry_path_v1_frequency.py` | — | ✅ |
| [test_benchmark_entry_path_signal_only_ablation.py](tests/test_benchmark_entry_path_signal_only_ablation.py) | `ML/benchmark_entry_path_signal_only_ablation.py` | — | ✅ |
| [test_benchmark_entry_path_all_rows_ranking.py](tests/test_benchmark_entry_path_all_rows_ranking.py) | `ML/benchmark_entry_path_all_rows_ranking.py` | — | ✅ |
| [test_benchmark_entry_path_causal_surrogate.py](tests/test_benchmark_entry_path_causal_surrogate.py) | `ML/benchmark_entry_path_causal_surrogate.py` | — | ✅ |
| [test_benchmark_entry_path_direct_bar_model.py](tests/test_benchmark_entry_path_direct_bar_model.py) | `ML/benchmark_entry_path_direct_bar_model.py` | — | ✅ |
| [test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | — | ✅ |
| [test_benchmark_trailing_stop_target.py](tests/test_benchmark_trailing_stop_target.py) | `ML/benchmark_trailing_stop_target.py` | — | ✅ |
| [test_run_trailing_stop_target_matrix.py](tests/test_run_trailing_stop_target_matrix.py) | `ML/run_trailing_stop_target_matrix.py` | — | ✅ |
| [test_benchmark_trailing_stop_target_quantile.py](tests/test_benchmark_trailing_stop_target_quantile.py) | `ML/benchmark_trailing_stop_target_quantile.py` | — | ✅ |
| [test_benchmark_execution_policy_v2.py](tests/test_benchmark_execution_policy_v2.py) | `ML/benchmark_execution_policy_v2.py` | — | ✅ |
| [test_export_entry_path_predictions.py](tests/test_export_entry_path_predictions.py) | `ML/export_entry_path_predictions.py` | — | ✅ |
| [test_export_entry_path_v1_signals.py](tests/test_export_entry_path_v1_signals.py) | `API/export_entry_path_v1_signals.py` | — | ✅ |
| [test_prepare_entry_path_mt4_parity.py](tests/test_prepare_entry_path_mt4_parity.py) | `ML/prepare_entry_path_mt4_parity.py` | — | ✅ |
| [test_signal_export_parity.py](tests/test_signal_export_parity.py) | `ML/benchmark_signal_export_parity.py` | — | ✅ |
| [test_benchmark_telemetry_frequency_calibration.py](tests/test_benchmark_telemetry_frequency_calibration.py) | `ML/benchmark_telemetry_frequency_calibration.py` | — | ✅ |
| [test_telemetry_daily_reconciliation.py](tests/test_telemetry_daily_reconciliation.py) | `ML/telemetry_daily_reconciliation.py` | — | ✅ |
| [test_mql_telemetry_params_csv_contract.py](tests/test_mql_telemetry_params_csv_contract.py) | MQL telemetry `#.csv` / `EXTERN_VARS()` runtime contract | — | ✅ |
| [test_telemetry_signal_watcher.py](tests/test_telemetry_signal_watcher.py) | `API/telemetry_signal_watcher.py` | — | ✅ |
| [test_online_causal_preprocessing.py](tests/test_online_causal_preprocessing.py) | `processing/online_causal_preprocessing.py` | — | ✅ |
| [test_api_server_preprocessing.py](tests/test_api_server_preprocessing.py) | `API/api_server.py` shared online preprocessing contract | — | ✅ |
| [test_benchmark_cross_instrument_robustness.py](tests/test_benchmark_cross_instrument_robustness.py) | `ML/benchmark_cross_instrument_robustness.py` | — | ✅ |
| [test_benchmark_system_correlation.py](tests/test_benchmark_system_correlation.py) | `ML/benchmark_system_correlation.py` | — | ✅ |
| [test_live_safe_audit.py](tests/test_live_safe_audit.py) | `ML/live_safe_audit.py`, `ML/live_safe_audit_registry.py`, `ML/run_live_safe_ml_audit.py` | — | ✅ |
| [test_run_trailing_stop_target_quantile.py](tests/test_run_trailing_stop_target_quantile.py) | `ML/run_trailing_stop_target_quantile.py` | — | ✅ |
| [test_track_a_max_out_matrix.py](tests/test_track_a_max_out_matrix.py) | `ML/run_track_a_max_out_matrix.py` | — | ✅ |
| [test_benchmark_outcome_targets.py](tests/test_benchmark_outcome_targets.py) | `ML/benchmark_outcome_targets.py` | — | ✅ |
| [test_outcome_tasks.py](tests/test_outcome_tasks.py) | outcome tasks в `ML/data_loader.py` | — | ✅ |
| [test_exit_policy_research.py](tests/test_exit_policy_research.py) | `API/exit_policy_research.py` | — | ✅ |
| [test_generate_signals_research.py](tests/test_generate_signals_research.py) | TB signal selection в `API/generate_signals.py` | — | ✅ |
| [test_signal_tracer_tb.py](tests/test_signal_tracer_tb.py) | TB-specific parsing в `statistics/signal_tracer.py` | — | ✅ |
| [test_triple_barrier_calibration.py](tests/test_triple_barrier_calibration.py) | EV/calibration helper для Triple Barrier | — | ✅ |
| [test_triple_barrier_first_touch.py](tests/test_triple_barrier_first_touch.py) | first-touch helper для Triple Barrier разметки | — | ✅ |
| [test_triple_barrier_training.py](tests/test_triple_barrier_training.py) | transfer-learning kwargs для TB обучения | — | ✅ |
| [test_fractal_stop_breach_labels.py](tests/processing/test_fractal_stop_breach_labels.py) | `processing/label_signals.py` — Stage 1 breach-разметка `fractal0` | — | ✅ |
| [test_fractal_stop_fav.py](tests/processing/test_fractal_stop_fav.py) | `processing/label_signals.py` — Stage 2 fav-разметка и симулятор Fractal Stop Fav | — | ✅ |
| [test_stage5_transformer_breach.py](tests/test_stage5_transformer_breach.py) | Stage 5.0 Transformer Breach: профили признаков, tensor shapes, corridor validation, модель, split guard | — | ✅ |
| [test_entry_based_updn_fractal_selection_ablation.py](tests/test_entry_based_updn_fractal_selection_ablation.py) | entry-based fractal ablation runner | [docs](docs/tests/tests.md) | ✅ |
| [test_entry_based_next_open_closeout.py](tests/test_entry_based_next_open_closeout.py) | entry-based closeout runner | [docs](docs/tests/tests.md) | ✅ |
| [test_entry_based_powerful_tabular.py](tests/test_entry_based_powerful_tabular.py) | entry-based powerful tabular runner | [docs](docs/tests/tests.md) | ✅ |
| [test_entry_based_sequence_transformer.py](tests/test_entry_based_sequence_transformer.py) | entry-based sequence Transformer runner | [docs](docs/tests/tests.md) | ✅ |
| [test_entry_based_amplitude_movement.py](tests/test_entry_based_amplitude_movement.py) | entry-based amplitude movement-regime audit | [docs](docs/tests/tests.md) | ✅ |
| [test_regression_updn_target_foundation.py](tests/test_regression_updn_target_foundation.py) | `ML/baseline/benchmark_regression_updn_target_foundation.py` | — | ✅ |
| [test_regression_updn_already_moved_audit.py](tests/test_regression_updn_already_moved_audit.py) | `ML/baseline/analyze_regression_updn_already_moved_audit.py` | — | ✅ |
| [test_next_open_entry_updn_foundation.py](tests/test_next_open_entry_updn_foundation.py) | `ML/baseline/benchmark_next_open_entry_updn_foundation.py` | — | ✅ |
| [test_fractal0_price_entry_mechanics.py](tests/test_fractal0_price_entry_mechanics.py) | `ML/baseline/benchmark_fractal0_price_entry_mechanics.py` | — | ✅ |
| [test_fractal0_entry_exit_grid.py](tests/test_fractal0_entry_exit_grid.py) | `ML/baseline/benchmark_fractal0_entry_exit_grid.py` | — | ✅ |
| [test_entry_based_updn_price_feature_matrix.py](tests/test_entry_based_updn_price_feature_matrix.py) | `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py` | — | ✅ |
| [test_stage6_1_relative_geometry.py](tests/test_stage6_1_relative_geometry.py) | `ML/baseline/benchmark_stage6_1_relative_geometry.py` | — | ✅ |
| [test_stage6_2_price_action.py](tests/test_stage6_2_price_action.py) | `ML/baseline/benchmark_stage6_2_price_action.py` | — | ✅ |
| [test_stage6_2_range_w1_postmortem.py](tests/test_stage6_2_range_w1_postmortem.py) | `ML/baseline/analyze_stage6_2_range_w1_postmortem.py` | — | ✅ |
| [test_stage6_3_h6_feature_parity.py](tests/test_stage6_3_h6_feature_parity.py) | `ML/baseline/benchmark_stage6_3_h6_feature_parity.py` | — | ✅ |
| [test_stage6_outcome_based.py](tests/test_stage6_outcome_based.py) | `ML/baseline/benchmark_stage6_outcome_based.py` | — | ✅ |
| [test_entry_based_movement_filter.py](tests/test_entry_based_movement_filter.py) | `ML/baseline/benchmark_entry_based_movement_filter.py` | — | ⚠️ |
| [test_entry_based_movement_filter_freeze.py](tests/test_entry_based_movement_filter_freeze.py) | `ML/baseline/benchmark_entry_based_movement_filter_freeze.py` | — | ✅ |
| [test_direction_inside_frozen_movement_regime.py](tests/test_direction_inside_frozen_movement_regime.py) | `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py` | — | ✅ |
| [test_direction_inside_frozen_movement_regime_rich_features.py](tests/test_direction_inside_frozen_movement_regime_rich_features.py) | `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py` | — | ✅ |
| **Legacy / auxiliary tests** | Старые и разовые тесты для grouped research scripts | — | — | 📦 |

## Docs

| Файл | Назначение |
|------|------------|
| [README.md](docs/README.md) | Карта артефактов `docs/` и правила обновления |
| [DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам |
| [dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv |
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [audit/README.md](docs/audit/README.md) | Карта audit-артефактов и правил их обновления |
| [2026-06-09-fractal-stop-fav-target-spec-audit.md](docs/audit/2026-06-09-fractal-stop-fav-target-spec-audit.md) | Вердикт по спецификации Fractal Stop + Fav Target |
| [2026-05-24-methodology-review-notes.md](docs/audit/2026-05-24-methodology-review-notes.md) | Замечания по `docs/methodology/` и trigger-у `ml-methodology` |
| [methodology/README.md](docs/methodology/README.md) | Методика разработки и аудита ML-моделей ТС (16 этапов + oracle-preflight + приложения) |
| [methodology/06b-oracle-preflight.md](docs/methodology/06b-oracle-preflight.md) | Предварительная oracle-проверка теоретического потолка торговой постановки |
| [methodology/A5-post-mortem-diagnostics.md](docs/methodology/A5-post-mortem-diagnostics.md) | Post-mortem диагностика FAIL/reject |
| [methodology/A6-fractal-feature-profile-catalog.md](docs/methodology/A6-fractal-feature-profile-catalog.md) | Каталог fractal feature profiles |
| [next.md](docs/audit/next.md) | Текущий research-план после Stage 4.3 |
| [2026-06-08-fractal-stop-fav-target-design.md](docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md) | Спецификация Fractal Stop + Fav Target: этап только на пробой уровня и торговый слой |
| [2026-06-10-fractal-stop-breach-plan.md](docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md) | План Stage 1 Fractal Stop Breach: разметка пробоя уровня, baseline и frozen test |
| [2026-06-10-fractal-stop-fav-plan.md](docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md) | План Stage 2 Fractal Stop + Fav Target: торговый слой поверх breach-сигнала |
| [2026-06-16-stage5_0-transformer-breach-holdout.md](docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md) | План Stage 5.0 Transformer Breach |
| [2026-06-18-stage5_0a-feature-preflight.md](docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md) | План Stage 5.0a Feature Preflight: A7-аудит профилей признаков до повторного обучения Transformer |
| [2026-06-18-stage5_0a-corridor-full-preflight.md](docs/superpowers/plans/2026-06-18-stage5_0a-corridor-full-preflight.md) | План Stage 5.0a Corridor Full Preflight |
| [2026-06-10-fractal-stop-breach-stage1.md](docs/reports/2026-06-10-fractal-stop-breach-stage1.md) | Итоговый отчёт Stage 1: breach-разметка, baseline, frozen test и переход к Stage 2 |
| [2026-06-10-fractal-stop-fav-stage2.md](docs/reports/2026-06-10-fractal-stop-fav-stage2.md) | Итоговый отчёт Stage 2: fav-разметка, торговый слой, RF FAIL и oracle-диагностика |
| [2026-07-08-entry-based-movement-filter-replication-freeze.md](docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md) | Итоговый отчёт freeze-репликации одного entry-based movement-filter без direction/PnL/PF и без открытия `locked_test` |
| [2026-05-14-entry-path-all-rows-level-signal-design.md](docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md) | Спецификация поиска live-safe `signal_candidate` по всей строке фракталов |
| [2026-05-15-entry-path-all-rows-level-signal.md](docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md) | План реализации live-safe `signal_candidate` по всей строке фракталов |
| [2026-05-15-entry-path-fractal-level-direct-direction-design.md](docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md) | Спецификация direct `SELL/SKIP/BUY` модели по всей строке фракталов |
| [2026-05-15-entry-path-fractal-level-direct-direction.md](docs/superpowers/plans/2026-05-15-entry-path-fractal-level-direct-direction.md) | План реализации direct `SELL/SKIP/BUY` модели по всей строке фракталов |
| [label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора |
| [fractal_preprocessing.py.md](docs/processing/fractal_preprocessing.py.md) | Документация общей сортировки фракталов |
| [online_causal_preprocessing.py.md](docs/processing/online_causal_preprocessing.py.md) | Документация online-safe preprocessing |
| [api_server.py.md](docs/API/api_server.py.md) | Документация экспериментального REST API inference-пути |
| [label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict |
| [normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков |
| [statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике |
| [EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу |
| [signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF |
| [neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики |
| [benchmark_take_skip_lib_pic_selection.py.md](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | Внешний отбор `take_skip_v2` по признакам `lib_PIC` |
| [run_take_skip_lib_pic_feature_matrix.py.md](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | Training matrix для `take_skip_v2` с признаками `lib_PIC` внутри модели |
| [run_take_skip_original_contour_feature_matrix.py.md](docs/ML/run_take_skip_original_contour_feature_matrix.py.md) | Training matrix для старого single-tensor `take_skip_v2` контура + `lib_PIC` признаки |
| [benchmark_execution_policy_v2.py.md](docs/ML/benchmark_execution_policy_v2.py.md) | Benchmark вариантов выхода для готовых ML-сигналов |
| [benchmark_signal_export_parity.py.md](docs/ML/benchmark_signal_export_parity.py.md) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log |
| [benchmark_telemetry_frequency_calibration.py.md](docs/ML/benchmark_telemetry_frequency_calibration.py.md) | Калибровка частого diagnostic telemetry режима |
| [telemetry_daily_reconciliation.py.md](docs/ML/telemetry_daily_reconciliation.py.md) | Ежедневная сверка telemetry ML-сигналов и MT4 MLP-логов |
| [benchmark_cross_instrument_robustness.py.md](docs/ML/benchmark_cross_instrument_robustness.py.md) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты |
| [benchmark_system_correlation.py.md](docs/ML/benchmark_system_correlation.py.md) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам |
| [live_safe_audit.py.md](docs/ML/live_safe_audit.py.md) | Core-типы live-safe audit и свод feature verdict → system verdict |
| [live_safe_audit_registry.py.md](docs/ML/live_safe_audit_registry.py.md) | Реестр прибыльных ML-систем для повторного live-safe audit |
| [run_live_safe_ml_audit.py.md](docs/ML/run_live_safe_ml_audit.py.md) | CLI для audit inventory, feature trace, legacy replay и verdict |
| [export_entry_path_predictions.py.md](docs/ML/export_entry_path_predictions.py.md) | Inference entry_path-моделей на arbitrary labeled CSV без переобучения |
| [prepare_entry_path_mt4_parity.py.md](docs/ML/prepare_entry_path_mt4_parity.py.md) | Подготовка frozen `entry_path_v1_live_safe + A @ 7.5%` export для MT4 parity |
| [benchmark_entry_path_signal_only_ablation.py.md](docs/ML/benchmark_entry_path_signal_only_ablation.py.md) | Ablation benchmark вклада offline `signal != 0` |
| [benchmark_entry_path_all_rows_ranking.py.md](docs/ML/benchmark_entry_path_all_rows_ranking.py.md) | All-rows ranking benchmark без offline `signal != 0` gate |
| [benchmark_entry_path_causal_surrogate.py.md](docs/ML/benchmark_entry_path_causal_surrogate.py.md) | Causal surrogate benchmark для offline `label_all().signal` |
| [benchmark_entry_path_direct_bar_model.py.md](docs/ML/benchmark_entry_path_direct_bar_model.py.md) | Direct BUY/SELL/SKIP benchmark для каждого бара |
| [feature_importance_diagnostics.py.md](docs/ML/feature_importance_diagnostics.py.md) | Диагностика важности групп текущих fractal-признаков |
| [feature_bank_comparison_diagnostics.py.md](docs/ML/feature_bank_comparison_diagnostics.py.md) | Сравнение baseline/geometry/path feature-bank вариантов |
| [lib_pic_feature_profiles.py.md](docs/ML/lib_pic_feature_profiles.py.md) | Единая сборка профилей признаков `lib_PIC` |
| [lib_pic_geometry_feature_bank.py.md](docs/ML/lib_pic_geometry_feature_bank.py.md) | Производные признаки геометрии уровней `lib_PIC` |
| [lib_pic_path_reaction_feature_bank.py.md](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | Производные признаки исторической реакции цены `Up/Dn` после уровней |
| [conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы |
| [lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC |
| [ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) |
| [trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() |

## Легенда статусов
✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

---
**Последнее обновление**: 2026-07-06

[docs-entry-ablation]: docs/ML/benchmark_entry_based_updn_fractal_selection_ablation.py.md
[docs-entry-closeout]: docs/ML/benchmark_entry_based_next_open_closeout.py.md
[docs-telemetry-frequency]: docs/ML/benchmark_telemetry_frequency_calibration.py.md
[docs-original-contour]: docs/ML/run_take_skip_original_contour_feature_matrix.py.md
