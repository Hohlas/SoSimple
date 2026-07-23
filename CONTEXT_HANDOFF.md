# Context Handoff

**Дата:** 2026-07-22

## Текущее состояние

Ветка: `fractal0-entry-exit-grid`.

Текущий завершённый этап:

- отчёт: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- план: `docs/superpowers/plans/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- runner: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- module docs: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`

Связанные предыдущие отчёты:

- `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`

## Что изменено

`benchmark_fractal0_entry_quality_filter.py` получил отдельный режим:

```bash
--normalized-rich-features
```

Он работает только вместе с:

```bash
--rich-entry-quality
```

Normalized rich mode:

- не перезаписывает legacy rich artifacts;
- использует prefix `ML/reports/fractal0_rich_entry_quality_normalized`;
- запрещает raw price-like inputs;
- переводит price-like признаки в ATR-координаты;
- fit-ит unit scaler только на `train_core`;
- применяет тот же scaler к `val_select` и `val_eval`;
- требует finite final model inputs в `[0,1]`;
- держит missing indicators как fixed schema;
- исключает padded fractal token values из scaler fit через `fractalN_present`.

Добавлены diagnostic-only controls:

- `atr_only`
- `time_plus_atr`
- `planned_geometry_no_atr`

Они исполняются, но не eligible для winner selection.

## Артефакты normalized rerun

Основные:

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv` — большой CSV, читать через `usecols`/`nrows`/`chunksize`.
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv` — большой CSV, читать через `usecols`/`nrows`/`chunksize`.
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv`

Команда воспроизведения:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --normalized-rich-features \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Full run завершился: `finished fractal0_rich_entry_quality`, exit code `0`.

## Итог normalized rerun

Winner выбран только на `val_select`:

```text
profile = time_only
model = linear
target = target_entry_ev_regression
filter = top30
score_cutoff_on_val_select = -0.026718184259660646
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

Main comparison:

- formal winner stayed `time_only`;
- normalized protocol improved `rich_combined_k40` by `+0.3994 BS_p05` and `+0.3009 PF` versus old rich protocol comparison;
- `price_action_h1` and `structure_f0_only` also improved;
- `relative_geometry_k40` and `structure_nearest_k40` did not improve enough and still trail `time_only`.

## Verification

Final checks after all code changes:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result:

```text
1376 passed, 52 warnings
```

Artifact contract check:

```text
normalized full artifact contract PASS
```

Confirmed:

- `status=completed`
- `locked_test=not_opened`
- `feature_contract_variant=normalized_atr_unit`
- `normalization_config.fit_split=train_core`
- `ranked_search_budget.n_total_ranked_configs=243`
- `active_search_budget.n_total_ranked_configs=243`
- `n_total_executed_configs=324`
- final normalized audit has `below_zero_rate.max=0.0`
- final normalized audit has `above_one_rate.max=0.0`
- forbidden column audit has `forbidden.sum=0`
- Up/Dn provenance gate `PASS`

## Methodological Constraints

- This is `RESEARCH_HINT_RICH_FEATURES`, not candidate.
- `locked_test=not_opened`.
- Ranked budget is `243`; executed jobs are `324` because diagnostic controls were run.
- Full-selection permutation was not run:
  `permutation_null_repeats_executed_for_full_selection=0`,
  `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.
- `normalized_feature_distribution_audit` has `WARNING` rows due constant/near-constant columns.
- `token_coverage` has `WARNING` rows due truncation rate `1.0`; no zero-token rows.
- pandas `PerformanceWarning` appeared during scaling; this is performance debt, not a result invalidation.

## Next Step

Do not open `locked_test`.

Recommended next step: a new pre-registered shortlist replication/probe with a small fixed set:

```text
1. time_only / linear / target_entry_ev_regression / top30
2. rich_combined_k40 normalized control
3. one compact normalized control: structure_f0_only or price_action_h1
```

Do not add new profiles, filters or targets inside that probe. Before any freeze/candidate claim, require yearly/side robustness and a clear decision on token truncation warnings.
