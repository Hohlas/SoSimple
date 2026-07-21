# Context Handoff

**Дата:** 2026-07-21

## Текущее состояние

Ветка Fractal0 entry/exit grid выполнена как research-этап.
Добавлены runner, тесты, structured artifacts и отчёт:

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `ML/reports/fractal0_entry_exit_grid.json`
- `ML/reports/fractal0_entry_exit_grid_m5_winner.json`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`

Полная сетка завершена: `1152/1152`, `failed=0`. Post-review winner-only
пересчёт с M5 execution ordering завершён отдельно.

## Главный вывод

Winner на `val_select`:

```text
E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_55
```

На `val_eval`:

- `n_trades = 2298`;
- `PF = 1.943813746344068`;
- `BS_p05 = 1.7601441464181098`;
- `stress_pf = 1.5742797668285895`;
- `ambiguous_same_bar_rate = 0.0` после M5/bugfix winner-only пересчёта.

Итог: previous winner выглядит `research_only`, но не candidate. Старый
`diagnostic_only` cap в full-grid JSON был вызван ошибкой ambiguity-семантики:
для ML-exit считался гипотетический fixed TP, которого нет в exit rule.

## Контракты

- `locked_test` не открыт.
- `train_core` только для ML-exit training.
- `val_select` выбирает winner.
- `val_eval` проверяет frozen winner.
- Canonical spread `0.20`, stress spread `0.40`.
- OHLC считается Bid; SELL exit учитывает Ask через spread.
- M5 `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` используется только для порядка
  исполнения внутри H1-свечи, не как признак модели.
- TP+SL в одной H1/M5-свече трактуется как `SL first`, но только если TP
  является реальным exit-условием.
- Перестановочная коррекция исправлена: `permutation.csv` содержит `200`
  строк, method `block_shuffled_val_select_pnl_r`.

## Следующий шаг

Не продвигать result как candidate. Следующий честный шаг — полный rerun или
заранее ограниченный frozen subset с M5 `execution_ohlc_path` и исправленной
ambiguity-семантикой.

## Читать следующему агенту

- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `ML/reports/fractal0_entry_exit_grid.json`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `docs/superpowers/plans/2026-07-20-fractal0-entry-exit-grid.md`
- `docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md`

## Запрещённые направления

- Не открывать `locked_test`.
- Не делать trading/live-ready claims по H1-result.
- Не считать old full-grid JSON lifecycle актуальным без учёта M5/bugfix
  winner-only artifact.
- Не добавлять M1/M5 в признаки модели в рамках execution refinement.
- Не тюнить по `val_eval`; новый цикл должен быть заранее зафиксирован.
