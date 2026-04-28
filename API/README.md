# API/

Генерация ML-сигналов для MT4 и REST API сервер.

Подробная документация: [docs/MT/ml_signal_integration.md](../docs/MT/ml_signal_integration.md)

## Скрипты

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [generate_signals.py](generate_signals.py) | Генерация CSV с ML-сигналами для MT4 тестера | checkpoints + labeled CSV → `MT/MQL4/Files/ml_signals.csv` | ✅ |
| [export_entry_path_v1_signals.py](export_entry_path_v1_signals.py) | Применение frozen `entry_path_v1` rule к prediction CSV и экспорт `time;signal` | prediction CSV + selected_rule.json → `ml_signals.csv` | ✅ |
| [export_entry_path_v1_quantile_signals.py](export_entry_path_v1_quantile_signals.py) | Применение frozen `entry_path_v1_quantile` rule к prediction CSV и экспорт `time;signal` | quantile prediction CSV + selected_rule.json → `ml_signals.csv` | ✅ |
| [export_take_skip_trailing_stop_v2_signals.py](export_take_skip_trailing_stop_v2_signals.py) | Применение frozen take/skip v2 rule к prediction CSV и экспорт `time;signal` с optional metadata | prediction CSV + selected_rule.json → `ml_signals.csv` + optional metadata JSON | ✅ |
| [telemetry_signal_watcher.py](telemetry_signal_watcher.py) | Фоновый watcher для online telemetry-контура `Nero.csv -> prediction CSV -> ml_signals.csv` | `Nero.csv` + checkpoint + rule → runtime `ml_signals.csv` | ✅ |
| [exit_policy_research.py](exit_policy_research.py) | Validation-first offline research для ML exit / position management | `ml_signals.csv` + OHLC + split catalogs → stdout ranking / frozen policy JSON | 🔬 |
| [api_server.py](api_server.py) | REST API (FastAPI) для приёма фракталов от MT4 в реальном времени | HTTP request → ML prediction | 🔬 |
| [test_api_client.py](test_api_client.py) | Тестовый клиент для api_server.py | test CSV → HTTP requests | 🔬 |
| [signal_path_atlas.py](signal_path_atlas.py) | ATR-normalized discovery/holdout path atlas for ML signals | `ml_signals.csv` + OHLC -> stdout tables / optional CSV export | 🔬 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания | 🔬 Экспериментальный

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# Генерация сигналов (дефолт: θ=2.665, horizon=12)
python -m API.generate_signals

# Кастомные параметры
python -m API.generate_signals --theta 3.0 --horizon 24

# Применение frozen entry_path_v1 rule к prediction CSV
python -m API.export_entry_path_v1_signals \
  --predictions ML/reports/entry_path_test_predictions.csv \
  --rule-path ML/reports/entry_path_trade_filter_selected_rule.json \
  --output MT/tester/files/ml_signals.csv

# Применение frozen entry_path_v1_quantile rule к prediction CSV
python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_007 \
  --split test \
  --rule-path ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output MT/tester/files/ml_signals.csv

# Применение frozen take/skip v2 rule к готовому prediction CSV
python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json \
  --output MT/tester/files/ml_signals.csv

# Telemetry export с metadata для daily reconciliation
python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/export_metadata.json \
  --label telemetry_frequency_v1

# Diagnostic all-rows export для raw online Nero.csv:
# направление берётся из fractal0.direction, а не из offline predict.
python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/telemetry_frequency_v1/runtime/runtime_predictions.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv \
  --base-csv ML/reports/telemetry_frequency_v1/runtime/runtime_input_snapshot.csv \
  --diagnostic-all-rows \
  --diagnostic-target-signals-per-year 500 \
  --diagnostic-direction-source fractal0_direction

# Online watcher: один проход
python -m API.telemetry_signal_watcher --once --verbose

# Online watcher: основной interactive-режим в tmux
mkdir -p ML/reports/telemetry_frequency_v1/runtime
tmux new -s telemetry-watcher

# Внутри окна tmux
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --max-runtime-rows 12000 \
  --verbose
```

# С Conformal Prediction
python -m API.generate_signals --conformal

# Triple Barrier сигналы
python -m API.generate_signals --task triple_barrier --theta 0.6

# Path atlas research
python -m API.signal_path_atlas --test-only
python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas

# Exit policy research
python -m API.exit_policy_research --split-profile validation_research
python -m API.exit_policy_research --split-profile test_final --policy ML/reports/frozen_exit_policy.json
```
