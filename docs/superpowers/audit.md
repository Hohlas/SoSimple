# Audit: Fractal0 Fixed-11 Locked Test

Проверяемый документ: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`.

Итог: численные результаты отчёта совпадают с structured artifacts `ML/reports/fractal0_fixed11_rich_entry_locked_test*`. Все 11 fixed rules прошли locked-test PF/BS/sample-size gates.

## Проверенные Источники

- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_fixed11_rich_entry_locked_test.py`
- `ML/reports/leaderboard_closure_audit_rules.csv`
- `ML/reports/fractal0_stop_grid_m5.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`

## Замечания

### 1. Locked-test movement scores восстановлены, а не взяты из freeze scores artifact

- Важность: важно.
- Место: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, функция `compute_locked_movement_scores`; отчёт `Limitations / Open Questions`.
- Суть проблемы: source movement freeze scores artifact содержит train/validation scores, но не содержит `locked_test` scores. Для `movement_plus_time` правил harness восстанавливает scores через frozen movement protocol.
- Доказательство: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` содержит `movement_score_for_locked_test=retrained_from_frozen_movement_protocol_for_movement_plus_time_profiles`; отчёт раскрывает это ограничение.
- Почему это важно: для 4 movement-plus-time правил результат зависит от повторного обучения movement scorer-а на `train_core`.
- Рекомендуемое исправление: перед повышением статуса сохранить отдельный locked-test movement score artifact или model bundle и выполнить повторяемость score/PF.

### 2. Model checkpoints не сохранены как отдельный артефакт

- Важность: улучшение.
- Место: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`; отчёт `Limitations / Open Questions`.
- Суть проблемы: ML-exit и rich-entry модели обучаются заново на `train_core`, но checkpoint bundle не сохраняется.
- Доказательство: JSON содержит paths только для summary/trades/yearly/side/selection CSV; checkpoint path отсутствует.
- Почему это важно: воспроизводимость сейчас опирается на код, seed и окружение, а не на сохранённую модель.
- Рекомендуемое исправление: для candidate-stage добавить сохранение trained model bundle либо отдельную проверку повторяемости метрик.

### 3. MT4/tester parity ещё не выполнен

- Важность: важно.
- Место: отчёт `Conclusions`, `Limitations / Open Questions`, `Next Step`.
- Суть проблемы: offline locked-test PF высокий, но нет подтверждения соответствия MT4/tester execution.
- Доказательство: среди checked artifacts нет MT4/tester parity report для `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`.
- Почему это важно: методика не разрешает повышать статус до trading/live-ready только по offline PF.
- Рекомендуемое исправление: выполнить MT4/tester parity на frozen output и оформить отдельный parity report.

### 4. Stress-spread locked-test disclosure ещё не выполнен

- Важность: важно.
- Место: отчёт `Limitations / Open Questions`.
- Суть проблемы: текущий locked-test run использует canonical spread `0.20`, но stress-spread на `locked_test` не пересчитан.
- Доказательство: artifacts list содержит summary/trades/yearly/side/selection, но не содержит stress-spread CSV.
- Почему это важно: methodology требует проверять устойчивость к повышенным costs перед повышением статуса.
- Рекомендуемое исправление: выполнить заранее заданный stress-spread disclosure без изменения selection.

## Проверенные Числа

- rule_count: `11`
- kept_candidates: `11`
- best PF: `3.366672260628524`
- lowest PF: `2.674664`
- best BS p05: `2.923856656424035`
- lowest BS p05: `1.927254`
- BUY PF range: `3.619632` - `5.121813`
- SELL PF range: `1.948454` - `3.079799`
- weakest yearly PF: `1.993798`

## Verification

Команды:

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py --threads 24 --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv --source-artifact ML/reports/fractal0_stop_grid_m5.json --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py tests/test_fractal0_fixed11_rich_entry_locked_test.py -q
```

Результат тестов: `45 passed`.
