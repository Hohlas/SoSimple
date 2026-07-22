# Context Handoff

**Дата:** 2026-07-21

## Текущее состояние

Ветка: `fractal0-entry-exit-grid`.

Текущий завершённый этап:

- отчёт: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- план: `docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md`
- module docs: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- runner: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`

Связанные предыдущие этапы:

- `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`

## Что изменено

`benchmark_fractal0_entry_quality_filter.py` получил отдельный режим:

```bash
--rich-entry-quality
```

Rich mode расширяет старый entry-quality runner, но не копирует симулятор:

- entry rows, M5 execution ordering, ML-exit, simulation и метрики берутся из
  `ML/baseline/benchmark_fractal0_entry_exit_grid.py`;
- feature builder использует explicit allowlist;
- M5 остаётся только execution ordering, не источник признаков;
- `locked_test` не открывается.

Добавлены unit tests в `tests/test_fractal0_entry_quality_filter.py`, включая
контракты grids, labels, H1 closed-bar lookup, serialized fractal parsing,
winner eligibility, rich artifact schema, split/target diagnostics и bugfix
выравнивания features/labels по `position_id`.

## Артефакты rich-entry

- `ML/reports/fractal0_rich_entry_quality.json`
- `ML/reports/fractal0_rich_entry_quality_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_trades.csv` — большой CSV, читать
  только через `nrows`/`usecols`/`chunksize`.
- `ML/reports/fractal0_rich_entry_quality_scores.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_target_distribution.csv`
- `ML/reports/fractal0_rich_entry_quality_planned_order_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_split_manifest.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_distribution_flags.csv`
- `ML/reports/fractal0_rich_entry_quality_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_score_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_selected_score_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_winner_yearly.csv`

Команда воспроизведения:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Corrected full rerun после audit fixes завершился: `243/243`, code `0`,
final line `finished fractal0_rich_entry_quality`.

## Итог rich-entry

Winner выбран только на `val_select`:

```text
profile = time_only
model = linear
target = target_entry_ev_regression
filter = top30
score_cutoff_on_val_select = -0.026392849103777025
```

`val_select`:

- `n_trades = 625`
- `PF = 5.3059`
- `BS_p05 = 4.4198`
- `mean_pnl_r = 0.4447`
- `max_drawdown_r = 2.9656`
- `selected_fraction = 0.2724`

Fixed `val_eval`:

- `n_trades = 660`
- `PF = 4.0268`
- `BS_p05 = 3.3955`
- `mean_pnl_r = 0.3397`
- `max_drawdown_r = 3.3906`
- `selected_fraction = 0.2872`
- `SL-rate = 0.0197`

Baselines на `val_eval`:

- `S2/E3/M0/X2 no-mask`: `n_trades=2298`, `PF=2.7873`,
  `BS_p05=2.5085`, `mean_pnl_r=0.2883`, `max_drawdown_r=8.3860`.
- `S0/E3/M0/X0_fixed_r_0_7`: `n_trades=2298`, `PF=2.7247`,
  `BS_p05=2.5120`, `mean_pnl_r=0.3505`, `max_drawdown_r=7.3000`.

Audit update: первый full run был invalidated для structural/rich
интерпретации. Причина: `fractal0..fractal99` не переносились из source split
rows в `entry_cache`, поэтому structural profiles были почти нулевыми.
Исправленный full rerun выполнен; feature-contract gates прошли все 9
профилей, но winner всё равно остался `time_only`.

Внесены исправления:

- `base.build_entry_rows()` теперь сохраняет serialized `fractal*` snapshot;
- `structure_nearest_k20/k40` теперь сортируют уровни по расстоянию к planned
  limit, а не просто берут первые recent slots;
- rich score diagnostics включает `rich_entry_score`;
- target distribution содержит `year`;
- `diagnostic_best_val_eval_not_eligible` вычисляется из строки;
- movement provenance использует `movement_freeze_scores` hash и при проблемах
  исключает `movement_plus_time` из eligible grid.
- `forbidden_column_audit`, `feature_distribution_flags`,
  `selected_score_diagnostics` добавлены в артефакты.
- `feature_importance_by_profile.csv` не произведён: модели по профилям не
  сохраняются, feature importance не участвовал в выборе winner.
- JSON раскрывает cumulative search budget: parent stop-grid, narrow
  entry-quality predecessor, текущие `243` rich ranked configs и `1143`
  listed diagnostic configs.
- Full-selection permutation не запускался:
  `permutation_null_repeats_executed_for_full_selection=0`.

## Методические ограничения

- Это research hint, не frozen rule и не trading candidate.
- `locked_test=not_opened`.
- Search budget: `243` ranked configurations; full correction не выполнена.
- `diagnostic_best_val_eval` не должен влиять на verdict.
- `top20`, `top10`, `structure_nearest_k80`, `structure_all100`,
  XGBoost и LightGBM не участвовали в выборе Phase A winner.
- No-fill rate около `51.4-51.7%`; planned diagnostics сохранены отдельно.
- pandas `FutureWarning` по `fillna` и LogisticRegression convergence warnings
  на `rich_combined_k40` не меняют selected winner, но это cleanup item.

## Следующий допустимый шаг

Только pre-registered replication/probe одного заранее заданного rule или
малого shortlist. Это не freeze decision и не основание для `locked_test`.

Не открывать `locked_test`.

Следующий корректный шаг — отдельный pre-registered probe одного frozen rule:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30 /
score_cutoff_on_val_select=-0.026392849103777025
```

Перед повышением статуса нужны независимая проверка или полная correction,
yearly/side robustness, scale cleanup и явная freeze policy.
