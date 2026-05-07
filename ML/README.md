# ML/

Обучение, оптимизация и оценка нейросетевых моделей для прогнозирования Up/Dn.

Подробная документация: [docs/ML/](../docs/ML/)

## Архитектура зависимостей

```
Слой 1 (Core)        losses.py, utils.py, data_loader.py, experiment_logger.py
Слой 2 (Models)      models/ (bilstm, cnn1d, transformer, hybrid_cnn_lstm)
Слой 3 (Training)    train.py → optimize.py
Слой 4 (Evaluation)  evaluate_test.py, threshold_analysis.py, compare_architectures.py
Отдельные модули     baseline/, conformal/, reproducibility_tests.py
```

## Скрипты

### Core (библиотека — импортируется остальными)

| Файл | Назначение | Статус |
|------|-----------|--------|
| [data_loader.py](data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ |
| [losses.py](losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ |
| [utils.py](utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ |
| [experiment_logger.py](experiment_logger.py) | CSV-логгер экспериментов | 🏁 |
| [lib_pic_feature_profiles.py](lib_pic_feature_profiles.py) | Профили признаков `lib_PIC` для диагностики и `entry_path_v1` | ✅ |

### Models

| Файл | Архитектура | Статус |
|------|-----------|--------|
| [models/transformer.py](models/transformer.py) | Transformer Encoder (лучшая) | ✅ |
| [models/bilstm.py](models/bilstm.py) | Bi-LSTM | 🏁 |
| [models/cnn1d.py](models/cnn1d.py) | 1D-CNN | 🏁 |
| [models/hybrid_cnn_lstm.py](models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 |
| [models/take_skip_dual_stream_transformer.py](models/take_skip_dual_stream_transformer.py) | Dual-stream Transformer для `take_skip_v2`: фракталы + признаки `lib_PIC` | ✅ |

### Training

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [train.py](train.py) | Обучение (--task regression_updn / triple_barrier) | DataLoader → checkpoints/, plots/ | ✅ |
| [optimize.py](optimize.py) | Optuna оптимизация гиперпараметров | DataLoader → reports/optuna_*.json | 🏁 |

### Evaluation

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [evaluate_test.py](evaluate_test.py) | OOS оценка на тестовой выборке | checkpoint + test CSV → reports/ | ✅ |
| [threshold_analysis.py](threshold_analysis.py) | Поиск оптимального θ для торговых сигналов | checkpoint + val CSV → reports/ | ✅ |
| [compare_architectures.py](compare_architectures.py) | Сравнение 4 архитектур | DataLoader → reports/ | 🏁 |
| [export_entry_path_predictions.py](export_entry_path_predictions.py) | Inference `entry_path_v1` / `entry_path_v1_quantile` на arbitrary labeled CSV без переобучения | labeled CSV + checkpoint → prediction CSV | ✅ |
| [run_entry_path_live_safe_retrain.py](run_entry_path_live_safe_retrain.py) | Multi-seed retrain/export/benchmark для `entry_path_v1_live_safe` с отдельными checkpoint-папками | `DATA/Nero_*` → reports/entry_path_v1_live_safe*/seed_*/ | ✅ |
| [run_entry_path_quantile_live_safe_retrain.py](run_entry_path_quantile_live_safe_retrain.py) | Multi-seed retrain/export/benchmark для `entry_path_v1_quantile` поверх CPU baseline `A @ 7.5%` | baseline reports + `DATA/Nero_*` → reports/entry_path_v1_quantile*/seed_*/ | ✅ |
| [entry_path_v1_quantile_ensemble.py](entry_path_v1_quantile_ensemble.py) | Агрегация quantile-прогнозов по нескольким seed для n-boost проверки | seed prediction CSVs → mean/vote masks | ✅ |
| [run_take_skip_lib_pic_feature_matrix.py](run_take_skip_lib_pic_feature_matrix.py) | Отдельная training matrix для `take_skip_v2` с профилями признаков `lib_PIC` внутри модели | labeled CSV → reports/take_skip_lib_pic_feature_matrix/ | 🚧 |
| [run_take_skip_original_contour_feature_matrix.py](run_take_skip_original_contour_feature_matrix.py) | Training matrix для старого single-tensor `take_skip_v2` контура, включая live-safe baseline без будущих row-признаков | labeled CSV → reports/take_skip_original_contour_feature_matrix/ / reports/take_skip_live_safe_baseline/ | 🚧 |
| [benchmark_take_skip_lib_pic_selection.py](benchmark_take_skip_lib_pic_selection.py) | Внешний отбор `take_skip_v2` по признакам `lib_PIC` без нового обучения | prediction CSV + source CSV → reports/take_skip_lib_pic_selection/ | ✅ |
| [benchmark_execution_policy_v2.py](benchmark_execution_policy_v2.py) | Сравнение вариантов выхода для готовых ML-сигналов | `ml_signals_*.csv` + OHLC → reports/execution_policy_v2/ | ✅ |
| [benchmark_signal_export_parity.py](benchmark_signal_export_parity.py) | Диагностика соответствия exported `ml_signals.csv` и MT4 tester log | `ml_signals.csv` + optional tester log → reports/signal_export_parity/ | ✅ |
| [benchmark_telemetry_frequency_calibration.py](benchmark_telemetry_frequency_calibration.py) | Калибровка частого diagnostic telemetry режима поверх take/skip score | prediction CSV → reports/telemetry_frequency_v1/calibration/ | ✅ |
| [telemetry_daily_reconciliation.py](telemetry_daily_reconciliation.py) | Ежедневная сверка telemetry `ml_signals.csv` с MT4 MLP open/close log | `ml_signals.csv` + MT4 log → daily reconciliation report | ✅ |
| [benchmark_cross_instrument_robustness.py](benchmark_cross_instrument_robustness.py) | Benchmark устойчивости при смене провайдера и переносе на новые инструменты | manifest JSON + signal CSV + OHLC + baseline reference → reports/cross_instrument_robustness/ | ✅ |
| [benchmark_system_correlation.py](benchmark_system_correlation.py) | Pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам | manifest JSON + trade CSV / entry_path predictions → reports/system_correlation_portfolio/ | ✅ |
| [live_safe_audit.py](live_safe_audit.py) | Core-типы и правила verdict для проверки признаков на online-безопасность | feature traces → PASS/FAIL/UNKNOWN | ✅ |
| [live_safe_audit_registry.py](live_safe_audit_registry.py) | Реестр прибыльных ML-систем, проверяемых live-safe audit | frozen artifacts → audit scope | ✅ |
| [run_live_safe_ml_audit.py](run_live_safe_ml_audit.py) | Полный live-safe audit: inventory, feature trace, legacy replay, verdict | registry + artifacts → reports/live_safe_ml_audit/ | ✅ |
| [reproducibility_tests.py](reproducibility_tests.py) | Тесты детерминизма seed | — → reports/ | 🏁 |

### Отдельные эксперименты

| Каталог | Назначение | Статус |
|---------|-----------|--------|
| [baseline/](baseline/) | Baseline-модели: XGBoost, LightGBM, RandomForest, SVM, LogReg | 🏁 |
| [conformal/](conformal/) | Split Conformal Prediction калибровка | 🏁 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

## Артефакты (генерируемые файлы)

| Каталог | Содержимое |
|---------|-----------|
| `checkpoints/` | Веса моделей (.pt) и параметры Optuna (.json) |
| `plots/` | Кривые обучения, scatter-графики |
| `reports/` | Отчёты экспериментов (.md, .json) |

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# удали кэш
rm DATA/*_train.npy DATA/*_val.npy DATA/*_mask_train.npy DATA/*_mask_val.npy 2>/dev/null; echo "ok"

# Обучение transformer (regression_updn)
python -m ML.train --model transformer --task regression_updn --epochs 100

# Optuna оптимизация
python -m ML.optimize --model transformer --task regression_updn --trials 50 --epochs 30 --seed 42

# Сравнение 4 архитектур
python -m ML.compare_architectures --task regression_updn

# OOS оценка
python -m ML.evaluate_test --task regression_updn --model transformer

# Threshold analysis
python -m ML.threshold_analysis --task regression_updn --horizon 12

# Triple Barrier (transfer learning обязателен!)
python -m ML.train --model transformer --task triple_barrier --epochs 100 --patience 20 \
  --encoder_ckpt ML/checkpoints/transformer_updn_best.pt

# Entry path с очищенным профилем признаков lib_PIC
python -m ML.train --model entry_path_dual_stream --task entry_path_v1 \
  --entry_path_feature_profile baseline_clean --seq_len 20 --clear_cache

# Entry path live-safe: multi-seed retrain/export/benchmark без перетирания checkpoint
# Обучение по умолчанию идёт на CPU; GPU для production retrain не использовать.
python -m ML.run_entry_path_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 --epochs 5 --batch-size 256 --clear-cache

# Entry path quantile live-safe: перепроверка поверх CPU baseline A @ 7.5%
python -m ML.run_entry_path_quantile_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline \
  --baseline-root ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 --epochs 5 --batch-size 256 --clear-cache

# Export entry_path predictions for frozen transfer/provider-drift benchmark
python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv DATA/Nero_XAUUSD_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt \
  --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_predictions.csv

# Take/skip v2: обучение с признаками lib_PIC внутри модели
MPLCONFIGDIR=/tmp/matplotlib python -m ML.run_take_skip_lib_pic_feature_matrix \
  --feature-profiles baseline_clean baseline_clean_path baseline_clean_geometry_path \
  --seq-lens 20 50 100 --epochs 10 --patience 4 --batch-size 256 \
  --jobs auto --torch-threads auto --cpu-load 0.5

# Take/skip v2: старый single-tensor контур + новые lib_PIC признаки
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib python -m ML.run_take_skip_original_contour_feature_matrix \
  --feature-modes original_baseline original_plus_path original_plus_geometry_path \
  --seq-lens 20 50 100 --epochs 10 --patience 4 --batch-size 256 \
  --jobs auto --torch-threads auto --cpu-load 0.5 --clear-cache

# Take/skip v2: live-safe контроль без predict/ret/fav/adv row-признаков
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib python -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_live_safe_baseline \
  --feature-modes live_safe_baseline \
  --seq-lens 50 --epochs 10 --patience 4 --batch-size 256 \
  --jobs 1 --torch-threads 4

# Take/skip v2: live-safe path-контроль для мощного сервера
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib python -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_live_safe_path \
  --feature-modes live_safe_path \
  --seq-lens 50 --epochs 10 --patience 4 --batch-size 256 \
  --seed 42 --min-pf 1.0 --min-trades-per-year 6.0 \
  --jobs 1 --torch-threads 16

# Parity: exported signals vs MT4 tester log
python -m ML.benchmark_signal_export_parity \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260420.log \
  --output-dir ML/reports/signal_export_parity/original_plus_path_20260420

# Cross-instrument robustness: provider drift + transfer matrix
python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/cross_instrument_robustness/manifest.json \
  --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/cross_instrument_robustness/full_matrix

# Telemetry frequency calibration
python -m ML.benchmark_telemetry_frequency_calibration \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --score-target take_24_x8 \
  --output-dir ML/reports/telemetry_frequency_v1/calibration

# Daily telemetry reconciliation
python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260427.log \
  --export-metadata ML/reports/telemetry_frequency_v1/export_metadata.json \
  --output-dir ML/reports/telemetry_frequency_v1/daily/2026-04-27
```

`run_take_skip_lib_pic_feature_matrix.py` сам ограничивает цели теми `trail_*_pnl_atr_x*`, которые есть в текущих labeled CSV. Для старых DATA это обычно `x2/x4/x8`; для расширенных DATA добавятся `x10/x12`.
`run_take_skip_original_contour_feature_matrix.py` делает то же ограничение по доступным целям, проверяет добавление новых признаков поверх старого single-tensor представления и имеет live-safe режимы без Python future-derived row-признаков. `live_safe_path` использует `Up/Dn` только как MT-накопленное состояние из `Nero.csv`; его полный прогон лучше запускать на мощном сервере.
`benchmark_cross_instrument_robustness.py` не меняет frozen rules и не ретюнит пороги: он только измеряет `provider_drift` и `cross_instrument_transfer` на уже зафиксированных системах.
`benchmark_system_correlation.py` не выбирает новые trading modes: он только нормализует существующие сделки и считает pairwise overlap/correlation verdicts.
`export_entry_path_predictions.py` нужен именно для frozen transfer-проверок: он не переобучает модели и ожидает полный entry-path labeled contract на входе.
`benchmark_telemetry_frequency_calibration.py` выбирает частоту, а не прибыльность; `telemetry_daily_reconciliation.py` нужен для ежедневной проверки demo/test исполнения по MLP-логам.
