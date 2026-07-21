# Context Handoff

**Дата:** 2026-07-21

## Текущее состояние

Ветка `fractal0-entry-exit-grid` содержит research-runner, тесты, отчёт и
артефакты Fractal0 entry/exit grid.

Главный текущий structured artifact:

- `ML/reports/fractal0_entry_exit_grid_m5_full.json`

Сопутствующие:

- `ML/reports/fractal0_entry_exit_grid_m5_full_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_winner_yearly.csv`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`

Полный M5 rerun завершён: `progress.completed=1152`, `progress.failed=0`.

## Главный вывод

Текущий winner полного M5 grid:

```text
E3_open_pullback_1_0atr / M0_no_mask / X0_fixed_r_0_7
```

На `val_eval`:

- `n_trades = 2298`;
- `PF = 2.7246860862703013`;
- `BS_p05 = 2.486754106484057`;
- `stress_pf = 2.2945114989452584`;
- `ambiguous_same_bar_rate = 0.0073977371627502175`;
- `effective_profit_years = 1.985599875865133`.

Старый H1/full-grid artifact и M5 winner-only artifact остаются историей
этапа. Старый ML-exit winner
`E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_55` теперь
второй по M5 full-grid метрикам (`val_eval PF=1.9438`, `BS_p05=1.7601`).

## Контракты

- `locked_test` не открыт.
- `train_core` только для ML-exit training.
- `val_select` выбирает winner.
- `val_eval` проверяет выбранный winner.
- Canonical spread `0.20`, stress spread `0.40`.
- OHLC считается Bid; SELL exit учитывает Ask через spread.
- M5 `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` используется только для порядка
  исполнения внутри H1-свечи, не как признак модели.
- TP+SL в одной H1/M5-свече трактуется как `SL first`, но только если TP
  является реальным exit-условием.
- Результат остаётся `research_only`, не candidate.

## Следующий шаг

Не открывать `locked_test`.

Следующий честный follow-up — заранее зафиксированный stop-policy и entry
quality цикл:

- добавить stop-policy варианты, включая
  `fractal0 ± 0.5 ATR` с минимальной дистанцией от входа `1/2/3 ATR`;
- stress-spread можно пропустить в основном search и затем прогнать только
  для shortlist winners;
- отдельно спроектировать ML-entry quality filter для E3, обученный на
  PnL/SL-исходах конкретной E3-сделки.

## Читать следующему агенту

- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `ML/reports/fractal0_entry_exit_grid_m5_full.json`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `docs/superpowers/plans/2026-07-20-fractal0-entry-exit-grid.md`
- `docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md`

## Запрещённые направления

- Не открывать `locked_test`.
- Не делать trading/live-ready claims.
- Не добавлять M1/M5 в признаки модели в рамках execution refinement.
- Не тюнить по `val_eval`; новый цикл должен быть заранее зафиксирован.
