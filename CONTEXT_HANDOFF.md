# Context Handoff

**Дата:** 2026-07-21

## Текущее состояние

Ветка: `fractal0-entry-exit-grid`.

Текущий завершённый этап:

- отчёт: `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- аудит: `docs/superpowers/audit.md`
- план: `docs/superpowers/plans/2026-07-21-fractal0-entry-quality-filter.md`
- module docs: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`

Предыдущие связанные этапы:

- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`

## Что изменено после аудита

Добавлен bounded runner:

- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `tests/test_fractal0_entry_quality_filter.py`

Также слегка расширен базовый runner:

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py` теперь сохраняет
  planned entry поля: `calculation_open`, `limit_price`,
  `planned_entry_price`, `planned_entry_bid_equivalent`,
  `planned_protective_stop_price`, `planned_r_value`.

Причина: ML-entry filter должен иметь pre-order feature contract, а не зависеть
от post-fill колонок.

Исправления аудита:

- simple topX cutoff считается только по finite score rows;
- `simple_stop_distance_top50` и `simple_r_value_top50` больше не дают 0
  сделок из-за NaN cutoff;
- JSON artifact содержит `status`, `verdict`, `lifecycle_status`,
  `split_roles`, `forbidden_interpretations`, `entry_feature_columns`,
  `entry_label_contract`, `filter_contract`;
- добавлен `ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv`.

## Артефакты entry-quality

- `ML/reports/fractal0_entry_quality_filter.json`
- `ML/reports/fractal0_entry_quality_filter_summary.csv`
- `ML/reports/fractal0_entry_quality_filter_trades.csv` — большой CSV, читать
  только через `nrows`/`usecols`/`chunksize`.
- `ML/reports/fractal0_entry_quality_filter_scores.csv`
- `ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv`
- `ML/reports/fractal0_entry_quality_filter_yearly.csv`
- `ML/reports/fractal0_entry_quality_filter_permutation.csv`

Команда воспроизведения:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_quality_filter \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

## Итог entry-quality после исправлений

Winner выбран только на `val_select`:

```text
entry_quality_top10
score_cutoff_on_val_select = 0.36753163277225726
```

`val_select`:

- `n_trades = 196`
- `PF = 5.496736`
- `BS_p05 = 3.937030`
- `selected_fraction = 0.085440`
- `SL-rate = 0.030612`

`val_eval` проверка того же cutoff:

- `n_trades = 53`
- `PF = 1.954347`
- `BS_p05 = 0.971312`
- `mean_pnl_r = 0.167059`
- `max_drawdown_r = 2.582476`
- `selected_fraction = 0.023064`
- `SL-rate = 0.094340`

No-mask baseline в том же run на `val_eval`:

- `n_trades = 2298`
- `PF = 2.531716`
- `BS_p05 = 2.286458`
- `mean_pnl_r = 0.263844`
- `max_drawdown_r = 9.135903`
- `SL-rate = 0.062663`

Previous S0/X0 baseline из stop-grid `val_eval`:

- `n_trades = 2298`
- `PF = 2.724686`
- `BS_p05 = 2.512015`
- `mean_pnl_r = 0.350482`
- `max_drawdown_r = 7.300000`

Вывод: selected `entry_quality_top10` не пережил `val_eval`. Artifact
`lifecycle_status = research_hint`, не `research_hypothesis`.

## Методические ограничения

- Verdict не выше `research_only`.
- `locked_test` не открыт.
- `val_select` выбирает filter family и cutoff; `val_eval` только проверяет.
- На `val_eval` нельзя пересчитывать topX по распределению `val_eval`.
- Фактическая доля selected на `val_eval` стала `2.31%`, а не `10%`.
- Diagnostic `val_eval` winners (`entry_avoid_sl_top50`, `entry_quality_top50`,
  `entry_quality_top30`) нельзя подставлять вместо selected winner.
- Simple baselines теперь валидны и конкурентны: `simple_r_value_top50`
  имеет `val_eval BS_p05=2.3350`.
- M5 используется только для порядка исполнения внутри H1-свечи, не как
  признак модели.

## Следующий допустимый шаг

Не открывать `locked_test`.

Текущий selected rule не должен идти в frozen rule. Следующий корректный шаг —
новый bounded shortlist/stress plan с заранее заданными контролями:

- `S0/E3/M0/X0_fixed_r_0_7`;
- `S2/E3/M0/X2/M0_no_mask`;
- selected failed disclosure `S2/E3/M0/X2/entry_quality_top10`;
- максимум небольшой заранее заданный diagnostic shortlist:
  `entry_avoid_sl_top50`, `entry_quality_top50`, `simple_r_value_top50`.

Новый план должен заранее задать minimum selected trades и calibration rule.
