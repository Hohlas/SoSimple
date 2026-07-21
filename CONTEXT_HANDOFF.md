# Context Handoff

**Дата:** 2026-07-21

## Текущее состояние

Ветка: `fractal0-entry-exit-grid`.

Текущий завершённый этап:

- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- план: `docs/superpowers/plans/2026-07-21-fractal0-stop-grid-m5.md`

Предыдущий базовый этап:

- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- полный M5 baseline artifact: `ML/reports/fractal0_entry_exit_grid_m5_full.json`

## Что изменено

Основной runner расширен:

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`

Добавлено:

- stop-policy registry `S0`/`S1`/`S2`/`S3`;
- `stop_policy_id` в `run_config_hash`, `resume_key`, summary, trades, JSON,
  permutation, attribution, winner eval и rule matching;
- отдельное обучение ML-exit для каждой `stop_policy_id`;
- CLI:
  - `--stop-grid-mode full|current-only`;
  - `--exit-shortlist full|stop_grid`;
  - `--skip-stress-spread`;
- stop diagnostics CSV.

## Артефакты stop-grid

- `ML/reports/fractal0_stop_grid_m5.json`
- `ML/reports/fractal0_stop_grid_m5_summary.csv`
- `ML/reports/fractal0_stop_grid_m5_trades.csv` — большой файл, около `321M`,
  не читать целиком.
- `ML/reports/fractal0_stop_grid_m5_progress.json`
- `ML/reports/fractal0_stop_grid_m5_permutation.csv`
- `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv`
- `ML/reports/fractal0_stop_grid_m5_focused_stop_diagnostics.csv`
- `ML/reports/fractal0_stop_grid_m5_all_grid_yearly.csv`
- `ML/reports/fractal0_stop_grid_m5.log`

Итог запуска:

```text
completed = 576
failed = 0
stress_spread_status = deferred_shortlist_only
locked_test = not_opened
```

Команда воспроизведения:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_stop_grid_m5 \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-grid-mode full \
  --exit-shortlist stop_grid \
  --skip-stress-spread \
  --permutation-repeats 200
```

## Stop-grid winner

Winner выбран только на `val_select`:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50
```

`val_select`:

- `n_trades = 2294`
- `PF = 3.329117`
- `BS_p05 = 3.032558`
- `risk_distance_atr = 2.0`

`val_eval` проверка того же ключа:

- `n_trades = 2298`
- `PF = 2.787295`
- `BS_p05 = 2.508541`
- `mean_pnl_r = 0.288315`
- `max_drawdown_r = 8.385976`
- `pf_without_best_year = 2.742403`
- `effective_profit_years = 1.979596`
- `ambiguous_same_bar_rate = 0.0`

Permutation:

- `method = block_shuffled_val_select_pnl_r`
- `empirical_p_value = 0.004975`
- `status = PASS`
- `null_repeats = 200`

## Сравнение с предыдущим M5 baseline

Предыдущий полный M5 baseline winner:

```text
S0_current_0_5 /
E3_open_pullback_1_0atr /
M0_no_mask /
X0_fixed_r_0_7
```

Его `val_eval`:

- `PF = 2.724686`
- `BS_p05 = 2.486754`
- `stress_pf = 2.294511`

Новый stop-grid winner чуть лучше на canonical `val_eval`, но полный
stress-spread был намеренно отложен. По консервативной метрике `BS_p05` он
не лучше текущего S0/X0 baseline в этом же stop-grid summary:

```text
S2/E3/M0/X2 p0.50: BS_p05 = 2.508541
S0/E3/M0/X0:       BS_p05 = 2.512015
```

Это не frozen candidate.

## Методические ограничения

- Verdict не выше `research_only`.
- `locked_test` не открыт.
- `val_select` выбирает winner; `val_eval` только проверяет выбранный ключ.
- Полный stress-spread не выполнен: только `deferred_shortlist_only`.
- `ML/reports/fractal0_stop_grid_m5_spread_stress.csv` содержит status row,
  а не рассчитанные stress-метрики.
- `pnl_r` трактуется как одинаковый риск на сделку, а не одинаковый
  фиксированный лот; широкий stop меняет денежный риск при фиксированном лоте.
- M5 используется только для порядка исполнения внутри H1-свечи, не как
  признак модели.
- `M1_frozen_movement_top5` в этом прогоне low-N control: на `val_eval`
  минимум `9` сделок, медиана `11`; не сравнивать M1 с M0 на равных.
- `ML/reports/fractal0_stop_grid_m5_yearly.csv` — all-grid yearly aggregate,
  не winner yearly. Winner yearly: `fractal0_stop_grid_m5_winner_yearly.csv`.

## Следующий допустимый шаг

Shortlist-only stress-spread без расширения grid:

- `S2/E3/M0/X2_ml_opposite_any_p0_50` — текущий stop-grid winner;
- `S0/E3/M0/X0_fixed_r_0_7` — прежний M5 baseline;
- ближайшие `S1`/`S3` варианты вокруг того же entry/mask/exit family.

Открывать `locked_test` сейчас нельзя.
