# Fractal0 Rich Entry Quality

> **Дата**: 2026-07-21
> **Статус**: Completed
> **Вердикт**: RESEARCH_HINT_RICH_FEATURES
> **Result note**: SHORTLIST_FOR_REPLICATION
> **Цель**: Проверить, может ли pre-order ML-entry quality ranking улучшить выбранный `S2/E3/M0/X2` контур за счёт planned geometry, H1 price action и структуры `fractal*`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md`
> **Итоговый фокус**: формальный winner — `time_only / linear / target_entry_ev_regression / top30`, но практический research focus смещён на shortlist кандидатов из `ML/reports/fractal0_rich_entry_quality_summary.csv`.

> **Follow-up**: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md` reruns the same rich search with price-like inputs converted to ATR/unit features. Use that report and `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv` for final old-vs-normalized comparison.

## Context

Предыдущий `fractal0_entry_quality_filter` с узкими признаками провалился на `val_eval`: выбранный на `val_select` фильтр оказался слишком малым и хуже no-mask baseline по `BS_p05`. Этот этап расширил постановку: вместо одного узкого entry-quality score выполнен rich search по профилям признаков, моделям, целям и top-фильтрам.

Уровень этапа: поисковый research cycle. Это не проверочный freeze и не кандидат. `locked_test=not_opened`.

## What Was Done

Добавлен режим `--rich-entry-quality` в `ML/baseline/benchmark_fractal0_entry_quality_filter.py`. Runner переиспользует `ML/baseline/benchmark_fractal0_entry_exit_grid.py` для entry rows, M5 execution ordering, ML-exit scoring, симуляции сделок и метрик.

Реализованы:

- rich grids: 9 eligible feature profiles, 3 eligible models, 3 eligible targets, 3 primary filters;
- explicit feature allowlist по каждому профилю;
- rich labels с сохранением no-fill planned orders;
- winner selection только на `val_select`;
- fixed `val_eval` check только для выбранного rule;
- отдельные rich artifacts с prefix `ML/reports/fractal0_rich_entry_quality`.

## Multiple Testing Context

`current_search_budget`: 9 profiles x 3 models x 3 targets x 3 primary filters = 243 ranked configurations.

`n_total_executed_configs=243`. Diagnostic budget listed in JSON: `1143`, но default full run выполнил только eligible Phase A grid.

`top20`, `top10`, `structure_nearest_k80`, `structure_all100`, XGBoost и LightGBM не участвовали в выборе winner. Permutation scope сохранён как `selected_rule_only`, поэтому это diagnostic-only, не полная коррекция множественного перебора. Для rich full-selection permutation не выполнено ни одного null-повтора полного selection protocol: `permutation_null_repeats_executed_for_full_selection=0`, `_permutation.csv` содержит только заголовок. Параметр `--permutation-repeats 200` был настройкой запуска, но не даёт statistical gate для этого этапа.

Cumulative search budget:

| component | budget |
|---|---:|
| parent stop-grid current search | 288 selection cells; 576 expected completed without stress; 48 ML-exit model jobs |
| narrow entry-quality predecessor | 17 filters; 34 completed split summaries |
| current rich ranked search | 243 ranked configs |
| listed rich diagnostic configs | 1143 not executed by default run |

`allowed_max_verdict=RESEARCH_HINT_RICH_FEATURES`. Запрещённые интерпретации: trading candidate, live-ready, production evidence, permission to open `locked_test`.

## Changed Files

- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `tests/test_fractal0_entry_quality_filter.py`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Verification

Перед полным запуском:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
./.venv/bin/python -m pytest tests/ -q
```

Результат: `1361 passed, 52 warnings`.

Smoke run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 2 \
  --no-resume \
  --output-prefix /tmp/fractal0_rich_entry_quality_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --smoke-limit-filters 1 \
  --permutation-repeats 3
```

Smoke exited with code `0`; JSON status `completed`, `locked_test=not_opened`, budget `243`.

Full run:

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

Full run exited with code `0`, elapsed `3437.4 sec`, JSON status `completed`.

Final full run exited with code `0`, final line `finished fractal0_rich_entry_quality`. JSON status `completed`, `locked_test=not_opened`, `allowed_max_verdict=RESEARCH_HINT_RICH_FEATURES`, `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.

Final artifact checks:

- `feature_distribution_flags`: 9 profiles, all `PASS`.
- `forbidden_column_audit`: 2025 profile-feature rows, forbidden count `0`.
- `score_diagnostics`: 486 rows, includes `rich_entry_score`.
- `selected_score_diagnostics`: 2 rows for `val_select` and `val_eval`.
- `target_distribution`: 294 rows, includes `year`.
- `diagnostic_best_val_eval_not_eligible=False`; diagnostic best equals selected fixed `val_eval`.

## Results

Primary table source: `ML/reports/fractal0_rich_entry_quality_summary.csv`. Файл должен храниться в git: это компактный источник всех 243 eligible configurations по `val_select` и их fixed `val_eval` строк.

Selected winner on `val_select`:

| field | value |
|---|---:|
| profile | `time_only` |
| model | `linear` |
| target | `target_entry_ev_regression` |
| filter | `top30` |
| n_trades | 625 |
| PF | 5.3059 |
| BS_p05 | 4.4198 |
| mean_pnl_r | 0.4447 |
| max_drawdown_r | 2.9656 |
| win_rate | 0.5680 |
| selected_fraction | 0.2724 |
| score_cutoff_on_val_select | -0.0263928491 |

Fixed `val_eval` check for the same selected rule:

| field | value |
|---|---:|
| n_trades | 660 |
| PF | 4.0268 |
| BS_p05 | 3.3955 |
| mean_pnl_r | 0.3397 |
| max_drawdown_r | 3.3906 |
| win_rate | 0.5273 |
| SL-rate | 0.0197 |
| selected_fraction | 0.2872 |

Baselines on `val_eval`:

| baseline | n_trades | PF | BS_p05 | mean_pnl_r | max_drawdown_r |
|---|---:|---:|---:|---:|---:|
| `S2/E3/M0/X2 no-mask` | 2298 | 2.7873 | 2.5085 | 0.2883 | 8.3860 |
| `S0/E3/M0/X0_fixed_r_0_7` | 2298 | 2.7247 | 2.5120 | 0.3505 | 7.3000 |

Candidate Shortlist:

Эти строки не являются новым winner selection. Это research shortlist для следующей заранее заданной проверки. Колонки `sel_*` показывают качество на `val_select`, где правило выбиралось; колонки `eval_*` показывают fixed check на следующем отрезке. `eval_status=PASS` означает: `val_eval` имеет `PF > 2.7873`, `BS_p05 > 2.5085`, `n_trades >= 300` и положительный `mean_pnl_r`.

| # | profile | model | target | filter | sel_frac | sel_PF | sel_BS_p05 | sel_mean | sel_DD | eval_n | eval_PF | eval_BS_p05 | eval_mean | eval_DD | eval_status |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `planned_geometry_only` | `extra_trees_shallow` | `target_entry_avoid_sl` | `top30` | 27.2% | 4.4560 | 3.7863 | 0.4585 | 6.7478 | 532 | 3.2069 | 2.6519 | 0.3577 | 5.3952 | PASS |
| 2 | `movement_plus_time` | `linear` | `target_entry_ev_regression` | `top50` | 47.2% | 4.0525 | 3.5705 | 0.3816 | 4.0928 | 1332 | 3.2690 | 2.7998 | 0.3173 | 5.6900 | PASS |
| 3 | `planned_geometry_only` | `extra_trees_shallow` | `target_entry_avoid_sl` | `top40` | 37.0% | 4.2409 | 3.5535 | 0.4277 | 7.0745 | 828 | 3.0329 | 2.5265 | 0.3178 | 6.6663 | PASS |
| 4 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top40` | 36.7% | 4.0203 | 3.4529 | 0.3733 | 4.5776 | 997 | 3.2496 | 2.7501 | 0.2970 | 5.6621 | PASS |
| 5 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top30` | 26.1% | 4.1523 | 3.3506 | 0.3878 | 4.3405 | 785 | 3.5465 | 3.0671 | 0.3126 | 4.3695 | PASS |
| 6 | `structure_nearest_k40` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top30` | 28.2% | 3.6348 | 3.0126 | 0.3703 | 3.9464 | 658 | 3.4858 | 2.9337 | 0.3599 | 6.5776 | PASS |
| 7 | `relative_geometry_k40` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top30` | 28.2% | 3.6348 | 3.0126 | 0.3703 | 3.9464 | 658 | 3.4858 | 2.9337 | 0.3599 | 6.5776 | PASS |
| 8 | `movement_plus_time` | `extra_trees_shallow` | `target_entry_good_0_5r` | `top40` | 38.6% | 3.4982 | 2.9923 | 0.3523 | 4.9535 | 916 | 3.3393 | 2.8512 | 0.3616 | 3.8051 | PASS |
| 9 | `structure_nearest_k40` | `linear` | `target_entry_good_0_5r` | `top30` | 30.1% | 3.1336 | 2.6120 | 0.3485 | 5.0244 | 643 | 3.3038 | 2.8030 | 0.3552 | 3.7064 | PASS |
| 10 | `relative_geometry_k40` | `linear` | `target_entry_good_0_5r` | `top30` | 30.1% | 3.1336 | 2.6120 | 0.3485 | 5.0244 | 643 | 3.3038 | 2.8030 | 0.3552 | 3.7064 | PASS |
| 11 | `planned_geometry_only` | `linear` | `target_entry_good_0_5r` | `top30` | 27.0% | 3.1865 | 2.7351 | 0.3304 | 5.2751 | 549 | 3.3574 | 2.7743 | 0.3325 | 3.9482 | PASS |

Critical read: shortlist содержит только варианты, которые сохраняют превышение no-mask baseline на `val_eval`. Приоритет следующей проверки: взять малый заранее заданный набор из разных семейств (`planned_geometry_only`, `movement_plus_time`, `structure_nearest_k40`/`relative_geometry_k40`) и не добавлять новый перебор.

Diagnostic Disclosure: Best Val Eval Row:

`diagnostic_best_val_eval` совпал с selected winner (`time_only / linear / target_entry_ev_regression / top30`) и имеет `not_eligible_for_winner=False`. Это не повышает статус не потому, что строка не eligible, а потому что сам этап выбран после wide validation search и не имеет полной коррекции множественного перебора.

Winner yearly disclosure on `val_eval`:

| year | n_trades | PF | mean_pnl_r | max_drawdown_r | win_rate |
|---:|---:|---:|---:|---:|---:|
| 2021 | 300 | 4.7567 | 0.3681 | 3.3906 | 0.5533 |
| 2022 | 360 | 3.5465 | 0.3160 | 3.3287 | 0.5056 |

Winner side disclosure on `val_eval`:

| side | n | sum_pnl_r | mean_pnl_r |
|---|---:|---:|---:|
| BUY | 303 | 125.2801 | 0.4135 |
| SELL | 357 | 98.9103 | 0.2771 |

`val_eval` покрывает 2021-03-08 05:00:00 - 2022-12-02 07:00:00, то есть фактически два календарных года, а не независимый современный период.

Feature distribution gate summary:

| profile | features | constant_features | non_constant_fraction | status |
|---|---:|---:|---:|---|
| `planned_geometry_only` | 5 | 0 | 1.0000 | PASS |
| `time_only` | 6 | 0 | 1.0000 | PASS |
| `structure_f0_only` | 22 | 12 | 0.4545 | PASS |
| `structure_nearest_k20` | 280 | 0 | 1.0000 | PASS |
| `structure_nearest_k40` | 560 | 0 | 1.0000 | PASS |
| `relative_geometry_k40` | 560 | 0 | 1.0000 | PASS |
| `price_action_h1` | 7 | 0 | 1.0000 | PASS |
| `movement_plus_time` | 7 | 0 | 1.0000 | PASS |
| `rich_combined_k40` | 578 | 0 | 1.0000 | PASS |

For `structure_f0_only`, constant fields on `train_core` are `fractal0_break`, `fractal0_shift`, `fractal0_up_*`, `fractal0_dn_*`. PASS means there is no gross pipeline contract break: `fractal0_price`, `fractal0_direction` and non-null `fractal0_shift` are present. It does not prove every field is informative.

## Conclusions

Rich-entry search дал честный, но более широкий вывод: формальный winner использует только календарные признаки (`time_only`). Однако это не единственный полезный результат: `summary.csv` содержит ряд non-time кандидатов, которые на fixed `val_eval` превысили no-mask baseline по `BS_p05`, PF и среднему PnL.

Structural/rich profiles теперь нельзя считать сломанными контрактно: они прошли gates, а `structure_nearest_k20/k40` сортируются по расстоянию до `planned_limit`. Они не победили формальный протокол selection, но часть из них достаточно сильна как shortlist для следующей заранее зарегистрированной проверки. Поэтому этот этап даёт research hint о полезности entry-quality фильтра и shortlist кандидатов, а не доказательство торговой пригодности fractal/rich признаков.

Главный риск вывода: и winner, и shortlist появились после широкого validation search из 243 ranked configurations на фоне предыдущих stop-grid и narrow entry-quality решений. Поэтому это не frozen rule и не trading candidate. Следующий честный шаг — отдельная заранее зарегистрированная replication/probe проверка малого shortlist, а не открытие `locked_test`.

## Limitations / Open Questions

- `locked_test` не открыт и не использовался.
- Полная коррекция множественного перебора не выполнена.
- `feature_importance_by_profile.csv` не произведён: runner не сохраняет обученные per-profile модели, а feature importance не участвовал в selection. Это сознательное ограничение, а не скрытый PASS.
- LogisticRegression на `rich_combined_k40` дал convergence warnings; selected winner этим не затронут.
- pandas `FutureWarning` по `fillna` не меняет текущий результат, но код стоит почистить перед следующей фазой.
- Feature distribution audit создан, но scale policy остаётся простым `fillna(0.0)` без отдельного scaler; `scale_contract=DIAGNOSTIC_ONLY`.
- No-fill rate около 51.4-51.7%; result metrics считаются по filled trades, planned-order diagnostics сохранены отдельно.

## Split Disclosure

| split | min_time | max_time | planned_orders | filled_trades | fill_rate |
|---|---|---|---:|---:|---:|
| train_core | 2004-07-06 20:00:00 | 2019-06-20 14:00:00 | 44159 | 21343 | 0.4833 |
| val_select | 2019-06-20 16:00:00 | 2021-03-08 03:00:00 | 4731 | 2294 | 0.4849 |
| val_eval | 2021-03-08 05:00:00 | 2022-12-02 07:00:00 | 4732 | 2298 | 0.4856 |

Split roles:

- `train_core`: trains ML-exit and ML-entry.
- `val_select`: selects exactly one eligible rule.
- `val_eval`: fixed selected rule only.
- `locked_test`: not opened.

Planned-order diagnostics:

| split | planned_orders | filled_orders | no_fill_orders | expected_pnl_per_filled_trade | expected_pnl_per_planned_order |
|---|---:|---:|---:|---:|---:|
| train_core | 44159 | 21343 | 22816 | -0.0518 | -0.0250 |
| val_select | 4731 | 2294 | 2437 | -0.0079 | -0.0038 |
| val_eval | 4732 | 2298 | 2434 | -0.0653 | -0.0317 |

## Next Step

Не открывать `locked_test`.

Допустимый следующий шаг: новый pre-registered replication/probe с малым заранее заданным shortlist. Предпочтительный набор для проверки без нового перебора:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /

1. planned_geometry_only / extra_trees_shallow / target_entry_avoid_sl / top30
2. movement_plus_time / linear / target_entry_ev_regression / top50
3. planned_geometry_only / extra_trees_shallow / target_entry_avoid_sl / top40
4. movement_plus_time / linear / target_entry_good_0_5r / top30
5. structure_nearest_k40 / hist_gradient_boosting / target_entry_good_0_5r / top30
```

Для повышения статуса нужны: заранее заданный split protocol, PASS/FAIL gates, yearly/side robustness, scale cleanup и явное решение, будет ли permutation повторять весь shortlist protocol или проверяться каждый заранее заданный кандидат отдельно. Только после этого возможна freeze decision.

## Related Materials

- `ML/reports/fractal0_rich_entry_quality.json`
- `ML/reports/fractal0_rich_entry_quality_summary.csv` — primary source for full candidate table; tracked despite global `*.csv` ignore.
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
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md`
