# run_fractal0_fixed11_rich_entry_locked_test.py

## Назначение

Wrapper для воспроизводимого locked-test/rerun запуска 11 fixed normalized
rich-entry rules. Использует базовый Fractal0 entry/exit runner и rich-entry
filter code; сам не выбирает новые rules, profiles, models, targets, filters
или cutoffs.

## Команда

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --source-artifact ML/reports/fractal0_stop_grid_m5.json \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --diagnostic-only
```

## Входы

- `ML/reports/leaderboard_closure_audit_rules.csv`
- `ML/reports/fractal0_stop_grid_m5.json`
- `DATA/Nero_XAUUSD_test_labeled.csv`
- `DATA/XAUUSD_H1_OHLC.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- train/validation splits из базового `Fractal0EntryExitGridConfig`

## Выходы

Для заданного `--output-prefix` создаются:

- `<prefix>.json`
- `<prefix>_summary.csv`
- `<prefix>_trades.csv`
- `<prefix>_yearly.csv`
- `<prefix>_side.csv`
- `<prefix>_selection.csv`

## Контракт

- M5 используется только как execution ordering source: timestamp лимитного
  fill и порядок same-H1 событий после fill.
- M5 не используется как ML input, фильтр выбора сделок или источник нового
  winner.
- JSON пишет `execution_ohlc_usage`,
  `ml_exit_feature_contract_status`, `bars_since_fill_0_ml_exit_policy`,
  `ml_exit_timing_contract`, `fill_execution_time_contract` и
  `execution_chronology_counts`.
- При `--diagnostic-only` JSON сразу пишет `verdict=DIAGNOSTIC_ONLY`,
  `allowed_max_verdict=DIAGNOSTIC_ONLY` и сохраняет исходный runner verdict в
  `original_runner_verdict`.
- `movement_score_model_contract` раскрывает `RobustScaler`, fit только на
  `train_core`, transformed split `locked_test` и `scale_contract`.
- Если runner используется после изменения ML-exit feature contract или
  execution convention, результат должен быть помечен не выше
  `DIAGNOSTIC_ONLY`.

## Ограничения

- Исторический fixed11 locked-test был открыт до chronology-fix; повторный
  запуск с новым execution contract не является тем же frozen verification
  chain.
- Для MT4 parity нужен отдельный tester/reconciliation шаг. Python M5 ordering
  сам по себе не доказывает MT4 parity.
