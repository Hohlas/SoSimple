# MODULE INDEX
> Живой указатель модулей проекта SoSimple

---

## Processing

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [label_main.py](processing/label_main.py) | CLI оркестратор pipeline | `Nero.csv` → `*_labeled.csv` | [docs](docs/processing/label_main.py.md) | 🏁 |
| [label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | sorted CSV → labeled CSV | [docs](docs/processing/label_signals.py.md) | 🏁 |
| [normalize.py](processing/normalize.py) | Построчная нормализация признаков | labeled CSV → normalized CSV + `*.npy` | [docs](docs/processing/normalize.py.md) | 🏁 |

## Statistics

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | `Nero.csv` → `.json`, `.csv` | [docs](docs/statistics/statistics.py.md) | 🏁 |
| [EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | `Nero.csv` → `plots/`, `.csv` | [docs](docs/statistics/EDA.ipynb.md) | 🏁 |
| [signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | `ml_signals.csv` + `Nero_*_labeled.csv` + `*.npy` + log → dossiers, CSV | [docs](docs/statistics/signal_tracer.py.md) | ✅ |
| [analyze_path_ordering.py](statistics/analyze_path_ordering.py) | Path-ordering анализ: что бьёт первым — SL или TP? Сравнение с реальным MT4 | `all_trades.csv` + OHLC → отчёт | — | 🏁 |

## API

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | `Nero_*_labeled.csv` + checkpoint → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_entry_path_v1_signals.py](API/export_entry_path_v1_signals.py) | Применение frozen `entry_path_v1` rule к prediction CSV и экспорт `time;signal` | prediction CSV + selected_rule.json → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) | Применение frozen `entry_path_v1_quantile` rule к prediction CSV и экспорт `time;signal` | quantile prediction CSV + selected_rule.json → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [export_take_skip_trailing_stop_v2_signals.py](API/export_take_skip_trailing_stop_v2_signals.py) | Применение frozen take/skip v2 rule к prediction CSV и экспорт `time;signal` с optional metadata | prediction CSV + selected_rule.json → `ml_signals.csv` + optional metadata JSON | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| [api_server.py](API/api_server.py) | REST API сервер: приём фракталов из MT4, отдача ML-сигналов | HTTP → `ml_signals.csv` | — | 🏁 |
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
| [train.py](ML/train.py) | Обучение (--task regression_updn / triple_barrier) | DataLoader → `checkpoints/`, `plots/` | — | ✅ |
| [optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | DataLoader → `reports/optuna_*.json` | — | 🏁 |
| [compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | DataLoader → `reports/architecture_comparison.md` | — | 🏁 |
| [evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | checkpoint + test CSV → `reports/evaluate_test_*.md` | — | ✅ |
| [threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | checkpoint + val CSV → `reports/threshold_analysis.md` | — | ✅ |
| [reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | — → `reports/reproducibility_report.md` | — | 🏁 |
| [baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | `*_labeled.csv` → `baseline/reports/`, `baseline/plots/` | [docs](docs/ML/baseline_experiments.py.md) | 🏁 |
| [conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | val CSV + checkpoint → `conformal/conformal_quantiles.json` | [docs](docs/ML/conformal_prediction.md) | 🏁 |
| [tb_signal_logic.py](ML/tb_signal_logic.py) | Triple Barrier signal logic: parse TB targets, агрегация решений | TB probabilities → signal | — | ✅ |
| [tb_probability_calibration.py](ML/tb_probability_calibration.py) | Isotonic calibration для TB-вероятностей | val data → calibrated probabilities | — | 🏁 |
| [entry_path_task.py](ML/entry_path_task.py) | Entry path task: определения targets, метрики, export helpers | — | — | ✅ |
| [entry_path_feature_bank.py](ML/entry_path_feature_bank.py) | Entry path feature bank: оконные сводки строки и row-wise context features | labeled CSV → engineered feature columns | — | ✅ |
| [feature_screen_entry_path.py](ML/feature_screen_entry_path.py) | Диагностический feature screening для entry_path_v1 | labeled CSV / feature frame → MI ranking | — | ✅ |
| [feature_importance_diagnostics.py](ML/feature_importance_diagnostics.py) | Диагностика важности групп текущих fractal-признаков | `Nero_*_labeled.csv` → `reports/current_feature_importance/` | [docs](docs/ML/feature_importance_diagnostics.py.md) | ✅ |
| [feature_bank_comparison_diagnostics.py](ML/feature_bank_comparison_diagnostics.py) | Сравнение baseline/geometry/path feature-bank вариантов | `Nero_*_labeled.csv` → `reports/feature_bank_comparison/` | [docs](docs/ML/feature_bank_comparison_diagnostics.py.md) | ✅ |
| [lib_pic_feature_profiles.py](ML/lib_pic_feature_profiles.py) | Единая сборка профилей признаков `lib_PIC` для диагностики и `entry_path_v1` | fractal columns → feature profile columns | [docs](docs/ML/lib_pic_feature_profiles.py.md) | ✅ |
| [lib_pic_geometry_feature_bank.py](ML/lib_pic_geometry_feature_bank.py) | Производные признаки геометрии уровней `lib_PIC` | fractal columns → geometry feature columns | [docs](docs/ML/lib_pic_geometry_feature_bank.py.md) | ✅ |
| [lib_pic_path_reaction_feature_bank.py](ML/lib_pic_path_reaction_feature_bank.py) | Производные признаки исторической реакции цены `Up/Dn` после уровней | fractal columns → path-reaction feature columns | [docs](docs/ML/lib_pic_path_reaction_feature_bank.py.md) | ✅ |
| [entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | — | — | ✅ |
| [trailing_stop_target_task.py](ML/trailing_stop_target_task.py) | Trailing-stop target task: target contract, export helpers и metrics | — | — | ✅ |
| [trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | — | — | ✅ |
| [entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | → filtered signals | — | ✅ |
| [export_entry_path_predictions.py](ML/export_entry_path_predictions.py) | Inference `entry_path_v1` / `entry_path_v1_quantile` на arbitrary labeled CSV без переобучения | labeled CSV + checkpoint → prediction CSV | [docs](docs/ML/export_entry_path_predictions.py.md) | ✅ |
| [export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export train/validation/test predictions for entry_path_v1_quantile | checkpoint → `reports/entry_path_v1_quantile_*_predictions.csv` | — | ✅ |
| [benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | prediction CSVs + frozen rule → reports | — | ✅ |
| [benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | prediction CSVs → frequency verdict | — | 🏁 |
| [benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_trailing_stop_target.py](ML/benchmark_trailing_stop_target.py) | Validation-first benchmark для trailing-stop target exports | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | prediction CSVs → validation/test verdict | — | ✅ |
| [benchmark_take_skip_mt4_trailing_sequential.py](ML/benchmark_take_skip_mt4_trailing_sequential.py) | Read-only comparison of independent vs single-position trailing-stop execution for take/skip signals | `ml_signals_*.csv` + labeled CSV + OHLC → summary JSON | — | ✅ |
| [benchmark_take_skip_lib_pic_selection.py](ML/benchmark_take_skip_lib_pic_selection.py) | Внешний слой отбора `take_skip_v2` по признакам `lib_PIC` без нового обучения | prediction CSV + source CSV → `reports/take_skip_lib_pic_selection/` | [docs](docs/ML/benchmark_take_skip_lib_pic_selection.py.md) | ✅ |
| [benchmark_execution_policy_v2.py](ML/benchmark_execution_policy_v2.py) | Сравнение вариантов выхода для готовых ML-сигналов | `ml_signals_*.csv` + OHLC → `reports/execution_policy_v2/` | [docs](docs/ML/benchmark_execution_policy_v2.py.md) | ✅ |
| [benchmark_signal_export_parity.py](ML/benchmark_signal_export_parity.py) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log | `ml_signals.csv` + optional tester log → `reports/signal_export_parity/` | [docs](docs/ML/benchmark_signal_export_parity.py.md) | ✅ |
| [benchmark_telemetry_frequency_calibration.py](ML/benchmark_telemetry_frequency_calibration.py) | Калибровка частого diagnostic telemetry режима поверх take/skip score | prediction CSV → `reports/telemetry_frequency_v1/calibration/` | [docs](docs/ML/benchmark_telemetry_frequency_calibration.py.md) | ✅ |
| [telemetry_daily_reconciliation.py](ML/telemetry_daily_reconciliation.py) | Ежедневная сверка telemetry `ml_signals.csv` с MT4 MLP open/close log | `ml_signals.csv` + MT4 log → daily reconciliation report | [docs](docs/ML/telemetry_daily_reconciliation.py.md) | ✅ |
| [benchmark_cross_instrument_robustness.py](ML/benchmark_cross_instrument_robustness.py) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты | manifest JSON + signal CSV + OHLC + baseline reference → `reports/cross_instrument_robustness/` | [docs](docs/ML/benchmark_cross_instrument_robustness.py.md) | ✅ |
| [benchmark_system_correlation.py](ML/benchmark_system_correlation.py) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам | manifest JSON + trade CSV / entry_path predictions → `reports/system_correlation_portfolio/` | [docs](docs/ML/benchmark_system_correlation.py.md) | ✅ |
| [run_take_skip_lib_pic_feature_matrix.py](ML/run_take_skip_lib_pic_feature_matrix.py) | Training matrix для `take_skip_v2` с профилями признаков `lib_PIC` внутри модели | labeled CSV → `reports/take_skip_lib_pic_feature_matrix/` | [docs](docs/ML/run_take_skip_lib_pic_feature_matrix.py.md) | 🚧 |
| [run_take_skip_original_contour_feature_matrix.py](ML/run_take_skip_original_contour_feature_matrix.py) | Training matrix для проверки `lib_PIC` признаков в старом single-tensor `take_skip_v2` контуре | labeled CSV → `reports/take_skip_original_contour_feature_matrix/` | [docs](docs/ML/run_take_skip_original_contour_feature_matrix.py.md) | 🚧 |
| [run_trailing_stop_target_matrix.py](ML/run_trailing_stop_target_matrix.py) | Оркестратор bounded matrix для `trailing_stop_target_v1` | configs → `reports/trailing_stop_target_matrix` | — | ✅ |
| [run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | config → `reports/trailing_stop_target_quantile` | — | ✅ |
| [run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | configs → `reports/track_a_max_out_matrix*` | — | ✅ |
| [models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | (batch, 100, 20) → multi-head output | — | ✅ |
| [models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | (batch, seq, feat) + engineered → multi-head output | — | ✅ |
| [models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | (batch, 100, 20) → multi-head output | — | ✅ |
| [models/trailing_stop_target_quantile_transformer.py](ML/models/trailing_stop_target_quantile_transformer.py) | TrailingStopTargetQuantileTransformer — q10/q50/q90 heads для `trail_48_pnl_atr_x3` | (batch, seq, feat) → quantile dict | — | ✅ |
| [ablation_study.py](ML/ablation_study.py) | Ablation Study (ME-2): влияние длины истории на качество | DataLoader → отчёт | — | 🏁 |
| [benchmark_outcome_targets.py](ML/benchmark_outcome_targets.py) | Бенчмарк outcome targets: сравнение качества разных таргетов | DataLoader → JSON отчёт | — | 🏁 |
| [benchmark_entry_path_trade_filter.py](ML/benchmark_entry_path_trade_filter.py) | Бенчмарк entry_path_v1 trade filter | — → JSON отчёт | — | 🏁 |

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
| [test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | — | ✅ |
| [test_benchmark_trailing_stop_target.py](tests/test_benchmark_trailing_stop_target.py) | `ML/benchmark_trailing_stop_target.py` | — | ✅ |
| [test_run_trailing_stop_target_matrix.py](tests/test_run_trailing_stop_target_matrix.py) | `ML/run_trailing_stop_target_matrix.py` | — | ✅ |
| [test_benchmark_trailing_stop_target_quantile.py](tests/test_benchmark_trailing_stop_target_quantile.py) | `ML/benchmark_trailing_stop_target_quantile.py` | — | ✅ |
| [test_benchmark_execution_policy_v2.py](tests/test_benchmark_execution_policy_v2.py) | `ML/benchmark_execution_policy_v2.py` | — | ✅ |
| [test_export_entry_path_predictions.py](tests/test_export_entry_path_predictions.py) | `ML/export_entry_path_predictions.py` | — | ✅ |
| [test_export_entry_path_v1_signals.py](tests/test_export_entry_path_v1_signals.py) | `API/export_entry_path_v1_signals.py` | — | ✅ |
| [test_signal_export_parity.py](tests/test_signal_export_parity.py) | `ML/benchmark_signal_export_parity.py` | — | ✅ |
| [test_benchmark_telemetry_frequency_calibration.py](tests/test_benchmark_telemetry_frequency_calibration.py) | `ML/benchmark_telemetry_frequency_calibration.py` | — | ✅ |
| [test_telemetry_daily_reconciliation.py](tests/test_telemetry_daily_reconciliation.py) | `ML/telemetry_daily_reconciliation.py` | — | ✅ |
| [test_mql_telemetry_params_csv_contract.py](tests/test_mql_telemetry_params_csv_contract.py) | MQL telemetry `#.csv` / `EXTERN_VARS()` runtime contract | — | ✅ |
| [test_benchmark_cross_instrument_robustness.py](tests/test_benchmark_cross_instrument_robustness.py) | `ML/benchmark_cross_instrument_robustness.py` | — | ✅ |
| [test_benchmark_system_correlation.py](tests/test_benchmark_system_correlation.py) | `ML/benchmark_system_correlation.py` | — | ✅ |
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

## Docs

| Файл | Назначение |
|------|------------|
| [README.md](docs/README.md) | Карта артефактов `docs/` и правила обновления |
| [DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам |
| [dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv |
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора |
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
| [export_entry_path_predictions.py.md](docs/ML/export_entry_path_predictions.py.md) | Inference entry_path-моделей на arbitrary labeled CSV без переобучения |
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
**Последнее обновление**: 2026-04-27
