# Fractal0 Rich Entry Quality

> **Дата**: 2026-07-21
> **Статус**: Completed
> **Вердикт**: RESEARCH_HINT_RICH_FEATURES
> **Result note**: TIME_ONLY_WINNER
> **Цель**: Проверить, может ли pre-order ML-entry quality ranking улучшить выбранный `S2/E3/M0/X2` контур за счёт planned geometry, H1 price action и структуры `fractal*`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-21-fractal0-rich-entry-quality.md`
> **Audit update**: первый full run был invalidated для structural/rich интерпретации: `fractal0..fractal99` не переносились в `entry_cache`. Исправленный full rerun завершён с кодом `0`; structural/rich profiles прошли feature-contract gates, но winner остался `time_only / linear / target_entry_ev_regression / top30`.

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

Результат после bugfix индексации labels/features: `1361 passed, 52 warnings`.

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

Corrected full rerun after audit fixes:

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

Corrected rerun exited with code `0`, final line `finished fractal0_rich_entry_quality`. JSON status `completed`, `locked_test=not_opened`, `allowed_max_verdict=RESEARCH_HINT_RICH_FEATURES`, `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.

Post-rerun artifact checks:

- `feature_distribution_flags`: 9 profiles, all `PASS`.
- `forbidden_column_audit`: 2025 profile-feature rows, forbidden count `0`.
- `score_diagnostics`: 486 rows, includes `rich_entry_score`.
- `selected_score_diagnostics`: 2 rows for `val_select` and `val_eval`.
- `target_distribution`: 294 rows, includes `year`.
- `diagnostic_best_val_eval_not_eligible=False`; diagnostic best equals selected fixed `val_eval`.

## Results

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

Corrected rich-entry search дал честный, но более узкий вывод: после исправления переноса `fractal0..fractal99` и проверки feature contracts лучший rule всё равно использует только календарные признаки (`time_only`). Он выбран на `val_select` и на fixed `val_eval` превысил оба baseline по `BS_p05`, PF и drawdown.

Structural/rich profiles теперь нельзя считать сломанными контрактно: они прошли gates, а `structure_nearest_k20/k40` сортируются по расстоянию до `planned_limit`. Но они не победили выбранный заранее протокол selection. Поэтому этот этап даёт research hint о полезности entry-quality фильтра, а не доказательство полезности fractal/rich признаков.

Главный риск вывода: winner выбран после широкого validation search из 243 ranked configurations на фоне предыдущих stop-grid и narrow entry-quality решений. Поэтому это не frozen rule и не trading candidate. Следующий честный шаг — отдельная заранее зарегистрированная replication/probe проверка одного правила или малого shortlist, а не открытие `locked_test`.

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

Допустимый следующий шаг: новый pre-registered replication/probe с одним заранее заданным rule:

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

Для повышения статуса нужны: заранее заданный split protocol, PASS/FAIL gates, yearly/side robustness, scale cleanup и явное решение, будет ли permutation повторять весь selection protocol или проверяться ровно одно заранее заданное правило. Только после этого возможна freeze decision.

## Related Materials

- `ML/reports/fractal0_rich_entry_quality.json`
- `ML/reports/fractal0_rich_entry_quality_summary.csv`
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

## Audit Resolution

- Согласен: `fractal0..fractal99` терялись в `build_entry_rows()`. Исправлено, покрыто тестом, corrected full rerun выполнен.
- Согласен: `structure_nearest_k20/k40` раньше брали recent slots, а не ближайшие к `planned_limit`. Исправлено и покрыто тестом.
- Согласен: `diagnostic_best_val_eval_not_eligible=True` было неверным при совпадении diagnostic best и selected winner. Исправлено; теперь `False`, `diagnostic_best_val_eval_is_selected_winner=True`.
- Согласен: score diagnostics были пустыми для score. Исправлено; `rich_entry_score` включён.
- Согласен: full-selection permutation gate не запускался. Формулировки снижены до `NOT_RUN_FOR_FULL_SELECTION`.
- Согласен: feature distribution audit должен быть gate. Добавлен `feature_distribution_flags`; corrected run прошёл `PASS`.
- Согласен частично: movement provenance требовал правильного hash key. Исправлено. Но `movement_plus_time` не победил, поэтому вывод не зависит от этого профиля.
- Согласен: нужны `forbidden_column_audit`, selected score diagnostics и target distribution с year. Добавлено.
- Не согласен с требованием считать constant `fractal0_shift` автоматическим fail для `structure_f0_only`: в текущем контракте достаточно живых `fractal0_price`, `fractal0_direction` и non-null `fractal0_shift`; constant поля раскрыты в distribution audit.
- `feature_importance_by_profile.csv` не добавлен: без сохранённых fitted estimators он не восстанавливается честно post-hoc. Отмечено как `NOT_PRODUCED`, не как выполненный artifact.
- Согласен: верхний verdict должен быть каноническим `RESEARCH_HINT_RICH_FEATURES`; `TIME_ONLY_WINNER` перенесён в result note.
- Согласен: старый заголовок `Diagnostic Disclosure: Not Eligible For Winner` стал неверным; заменён на `Best Val Eval Row`.
- Согласен: PASS feature-distribution gate не доказывает полезность rich/fractal полей; добавлена таблица constant features и ограничение интерпретации.
- Согласен: фраза `frozen rule` для следующего шага преждевременна; заменено на pre-registered replication/probe.
