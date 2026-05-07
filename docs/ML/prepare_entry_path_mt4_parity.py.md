# prepare_entry_path_mt4_parity.py

`ML/prepare_entry_path_mt4_parity.py` готовит MT4 parity export для текущего
главного кандидата `entry_path_v1_live_safe + A @ 7.5%`.

Цель: не дать случайно взять auto-winner `B` из seed-specific
`entry_path_trade_filter_selected_rule.json`. Для MT4 parity нужен именно
заранее выбранный простой baseline `A`.

## Входы

- validation predictions:
  `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv`
- test predictions:
  `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv`

Оба файла должны быть построены через CPU-only retrain runner.

## Выходы

По умолчанию пишет в `ML/reports/mt4_entry_path_v1_live_safe_parity/`:

- `entry_path_v1_live_safe_a075_rule.json` - frozen rule `A @ 7.5%`;
- `ml_signals.csv` - готовый `time;signal` файл для MT4;
- `metadata.json` - threshold, counts, sha256 и Python benchmark summary.

При `--copy-to-mt4` тот же `ml_signals.csv` копируется в:

- `MT/tester/files/ml_signals.csv`;
- `MT/MQL4/Files/ml_signals.csv`.

## Команда

```bash
./.venv/bin/python -m ML.prepare_entry_path_mt4_parity \
  --output-dir ML/reports/mt4_entry_path_v1_live_safe_parity \
  --copy-to-mt4
```

## MT4 контракт

Для сравнения с Python sequential check MT4 preset должен быть:

- `SymPer=XAUUSD60`;
- `iSignal=3`;
- `ML_ExitMode=0`;
- `ML_MaxPositions=1`;
- `ML_HoldBars=24`;
- `ML_TakeProfitATR=0`;
- `ML_BackStopATR=999`;
- `ML_AllowReversal=0`;
- `ML_UseScoreFilter=0`.

Смысл: один вход на сигнал, удержание 24 бара, без take-profit и без близкого
stop-loss, чтобы MT4 проверял тот же fixed-hold контракт, что и Python.
