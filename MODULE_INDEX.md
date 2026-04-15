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
| [lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, торговля | `ml_signals.csv` → `OPEN_BUY/SELL` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
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
| [entry_path_v1_quantile_task.py](ML/entry_path_v1_quantile_task.py) | Entry path v1 quantile task: export/report helpers и metrics | — | — | ✅ |
| [entry_path_trade_filter.py](ML/entry_path_trade_filter.py) | Entry path trade filter: candidate B score, weighted loss baseline | → filtered signals | — | ✅ |
| [export_entry_path_v1_quantile_predictions.py](ML/export_entry_path_v1_quantile_predictions.py) | Export train/validation/test predictions for entry_path_v1_quantile | checkpoint → `reports/entry_path_v1_quantile_*_predictions.csv` | — | ✅ |
| [benchmark_entry_path_v1_quantile_filter.py](ML/benchmark_entry_path_v1_quantile_filter.py) | Quantile filter benchmark on frozen A @ 7.5% baseline | prediction CSVs + frozen rule → reports | — | ✅ |
| [benchmark_entry_path_v1_frequency.py](ML/benchmark_entry_path_v1_frequency.py) | Frequency benchmark для базового entry_path_v1 selection layer | prediction CSVs → frequency verdict | — | 🏁 |
| [benchmark_entry_path_v2.py](ML/benchmark_entry_path_v2.py) | Расширенный selection benchmark с bounded candidate families и risk diagnostics | prediction CSVs → validation/test verdict | — | ✅ |
| [run_track_a_max_out_matrix.py](ML/run_track_a_max_out_matrix.py) | Оркестратор bounded matrix: train → export → benchmark_v2 для Track A | configs → `reports/track_a_max_out_matrix*` | — | ✅ |
| [models/entry_path_transformer.py](ML/models/entry_path_transformer.py) | EntryPathTransformer — специализированный Transformer для entry_path_v1 | (batch, 100, 20) → multi-head output | — | ✅ |
| [models/entry_path_dual_stream_transformer.py](ML/models/entry_path_dual_stream_transformer.py) | Dual-stream entry_path модель: sequence branch + engineered branch | (batch, seq, feat) + engineered → multi-head output | — | ✅ |
| [models/entry_path_v1_quantile_transformer.py](ML/models/entry_path_v1_quantile_transformer.py) | EntryPathV1QuantileTransformer — entry_path_v1 + q10/q90 heads | (batch, 100, 20) → multi-head output | — | ✅ |
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
| [test_entry_path_feature_bank.py](tests/test_entry_path_feature_bank.py) | `ML/entry_path_feature_bank.py` | — | ✅ |
| [test_entry_path_task.py](tests/test_entry_path_task.py) | `ML/entry_path_task.py` — target contract, export helpers | — | ✅ |
| [test_entry_path_v1_quantile_task.py](tests/test_entry_path_v1_quantile_task.py) | `ML/entry_path_v1_quantile_task.py` — export helpers и quantile metrics | — | ✅ |
| [test_entry_path_model.py](tests/test_entry_path_model.py) | `ML/models/entry_path_transformer.py` | — | ✅ |
| [test_entry_path_dual_stream_transformer.py](tests/test_entry_path_dual_stream_transformer.py) | `ML/models/entry_path_dual_stream_transformer.py` | — | ✅ |
| [test_entry_path_loader_seq_len.py](tests/test_entry_path_loader_seq_len.py) | `ML/data_loader.py` — `entry_path_v1` sequence length contract | — | ✅ |
| [test_entry_path_v1_quantile_model.py](tests/test_entry_path_v1_quantile_model.py) | `ML/models/entry_path_v1_quantile_transformer.py` | — | ✅ |
| [test_entry_path_training.py](tests/test_entry_path_training.py) | CLI plumbing для entry_path_v1 обучения | — | ✅ |
| [test_entry_path_trade_filter.py](tests/test_entry_path_trade_filter.py) | `ML/entry_path_trade_filter.py` | — | ✅ |
| [test_entry_path_reports.py](tests/test_entry_path_reports.py) | entry_path_v1 report generation | — | ✅ |
| [test_entry_path_v1_quantile_reports.py](tests/test_entry_path_v1_quantile_reports.py) | entry_path_v1_quantile export/test report CLI | — | ✅ |
| [test_entry_path_v1_quantile_filter.py](tests/test_entry_path_v1_quantile_filter.py) | entry_path_v1_quantile frozen-baseline filter benchmark | — | ✅ |
| [test_feature_screen_entry_path.py](tests/test_feature_screen_entry_path.py) | `ML/feature_screen_entry_path.py` | — | ✅ |
| [test_benchmark_entry_path_v1_frequency.py](tests/test_benchmark_entry_path_v1_frequency.py) | `ML/benchmark_entry_path_v1_frequency.py` | — | ✅ |
| [test_benchmark_entry_path_v2.py](tests/test_benchmark_entry_path_v2.py) | `ML/benchmark_entry_path_v2.py` | — | ✅ |
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
| [conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы |
| [lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC |
| [ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) |
| [trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() |

## Легенда статусов
✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

---
**Последнее обновление**: 2026-04-15
