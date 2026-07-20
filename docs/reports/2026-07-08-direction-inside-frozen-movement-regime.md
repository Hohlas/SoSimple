# Direction Inside Frozen Movement Regime

> **Дата**: 2026-07-08
> **Статус**: Completed
> **Вердикт**: FAIL
> **Цель**: Проверить, можно ли обучать direction baseline только внутри заранее замороженной movement-mask.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md`

## Context

Предыдущий этап заморозил movement segmentation rule:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`

Этот этап должен был использовать frozen mask как входной контракт и проверить направление `entry_up_3 > entry_dn_3` / `entry_dn_3 > entry_up_3` только внутри выбранных строк. Frozen movement rule не менялся.

Уровень этапа: `RESEARCH_ONLY`. Результат не может быть торговым кандидатом.

## What Was Done

Создан runner `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py` и тесты `tests/test_direction_inside_frozen_movement_regime.py`.

Runner делает:

- проверку frozen rule, hash, `locked_test=not_opened` и schema score export;
- проверку join frozen mask к split-ам по уникальному ключу `split + split_row_id`;
- построение direction target и leakage guards для future-derived колонок;
- простые direction baselines только если контракт прошёл;
- JSON/CSV artifacts даже при contract abort.

Во время расследования выяснилось, что исходное предположение плана было неверным:
`split + time` не является уникальным ключом. Причина не в случайной ошибке
экспорта, а в контракте данных: один бар может дать несколько entry-строк.
MT4-export может записать и новый максимум, и новый минимум на одном баре;
Python-разметка также явно различает фракталы по `(time, price, direction)`, а
не только по `time`.

Repair в этом же этапе добавил `split_row_id` в frozen score export и перевёл
direction join на `split + split_row_id`. После этого canonical direction run
дошёл до обучения baseline-моделей и завершился честным reject:
`REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

## Multiple Testing Context

Current search budget:

- direction baselines actually trained: `3`;
- selection split: `val_select`;
- `val_eval` и `low_n_disclosure` не использовались для выбора;
- `locked_test = not_opened`.

Cumulative lineage:

- entry-based amplitude / movement audit;
- simple movement filter design;
- frozen movement filter replication;
- current direction-inside-mask contract check.

Search space был узким и фиксированным: `majority_class`, `logistic_regression`,
`random_forest_small`, `extra_trees_small`; winner выбирался только на
`val_select`. `val_eval` и `low_n_disclosure` использовались только как проверка
и раскрытие, не как источник выбора.

## Changed Files

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- `tests/test_direction_inside_frozen_movement_regime.py`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
MPLCONFIGDIR=/tmp/mplconfig ./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime.py \
  --freeze-report ML/reports/entry_based_movement_filter_freeze.json \
  --freeze-scores ML/reports/entry_based_movement_filter_freeze_scores.csv \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime
./.venv/bin/python -m pytest tests/ -q
```

Результаты:

- focused direction/freeze tests: `45 passed`;
- canonical freeze CLI: exit `0`, regenerated score export with `split_row_id`;
- canonical direction CLI: exit `0`, stdout `{"verdict": "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"}`;
- full tests: `1224 passed, 30 warnings`;
- `graphify update .`: completed.

Artifact hashes:

- `freeze_report_sha256 = 52c3340150dde391e94db3d9023150275d94777ac76da6647505b4741155abaa`
- `freeze_scores_sha256 = 385dc1c125e9b2ba9ec9a278e4a56f60fe3f2c10a66a425ff92fd5b9cb105eae`

## Results

Structured artifact: `ML/reports/direction_inside_frozen_movement_regime.json`.

Main result:

- `verdict = REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`
- `contract.status = PASS`
- `search_budget.direction_baselines_trained = 3`
- selected winner by `val_select`: `extra_trees_small`

Winner metrics:

| split | rows | balanced_accuracy | mcc | up_support | dn_support |
|---|---:|---:|---:|---:|---:|
| `val_select` | 333 | 0.5792 | 0.1701 | 155 | 178 |
| `val_eval` | 333 | 0.5287 | 0.0579 | 167 | 166 |
| `low_n_disclosure` | 59 | 0.4747 | -0.0506 | 30 | 29 |

Robustness failed:

- `val_eval` has only one active year: `2025`;
- `val_eval.balanced_accuracy` is below the predeclared `0.56` gate;
- `val_eval.mcc` is below the predeclared `0.08` gate;
- balanced accuracy lower confidence bound is `0.4535`, below the `0.52` gate;
- block stability was not implemented in this plan and remains `NOT_RUN`.

Rows artifact: `ML/reports/direction_inside_frozen_movement_regime_rows.csv`.

Rows artifact contains `2932` selected rows after frozen movement mask and tie
removal, with schema:

```text
split,time,target_direction_3,target_is_tie_3,target_up_3,target_dn_3
```

## Conclusions

The original blocker was real: `split + time` is not a unique row key. The root
cause is that one bar can produce multiple entry rows, often because both high
and low fractal events are present on the same bar. Some duplicated bars also
repeat the same visible `fractal0` identity, so `time` alone is fundamentally too
weak as a row key.

After adding `split_row_id`, the join contract passed and the direction baseline
could be interpreted. The correct final outcome is
`REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`: there is no robust direction signal
inside the frozen movement mask under this narrow baseline search.

Invalidated assumption:

- `split + time` is not a unique row key for the current frozen score export.
- `val_select` uplift is not enough: the selected rule did not survive
  `val_eval` and disclosure checks.

## Limitations / Open Questions

- Block stability is still not implemented in this runner.
- `low_n_disclosure` has only `59` supervised rows after mask and tie removal.
- This does not disprove all possible direction modelling; it rejects only this
  fixed, narrow direction-inside-mask baseline.
- Do not widen the movement mask, change `top_fraction`, or tune against
  `val_eval`/`low_n_disclosure`.

Forbidden interpretations:

- not PnL;
- not PF;
- not a trading candidate;
- not a live rule;
- not permission to open `locked_test`.

## Split Disclosure

Split roles:

- `train`: model fit split, `2207` supervised rows after mask/tie removal;
- `val_select`: direction rule selection split, `333` supervised rows;
- `val_eval`: check-only split, `333` supervised rows;
- `low_n_disclosure`: disclosure-only, not used for selection;
- `locked_test`: `not_opened`.

`val_eval` active year disclosure: all `333` rows are in `2025`, so yearly
stability failed the minimum active-year check.

## Next Step

Close this direction-inside-mask branch as rejected. The next useful work is not
to tune this direction baseline, but to decide whether a different predeclared
research question is worth a new plan.

## Related Materials

- `docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
