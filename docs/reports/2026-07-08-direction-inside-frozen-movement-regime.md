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
- проверку join frozen mask к split-ам только по уникальному ключу `split + time`;
- построение direction target и leakage guards для future-derived колонок;
- простые direction baselines только если контракт прошёл;
- JSON/CSV artifacts даже при contract abort.

Канонический запуск остановился до обучения моделей: ключ `split + time` не уникален в текущем `entry_based_movement_filter_freeze_scores.csv` и в split-ах.

## Multiple Testing Context

Current search budget:

- direction baselines actually trained: `0`;
- selection split: `val_select`;
- `val_eval` и `low_n_disclosure` не использовались для выбора;
- `locked_test = not_opened`.

Cumulative lineage:

- entry-based amplitude / movement audit;
- simple movement filter design;
- frozen movement filter replication;
- current direction-inside-mask contract check.

Из-за `ABORT_CONTRACT_FAIL` текущий этап не добавил новый model search. Direction baseline metrics отсутствуют по методической причине: входной mask export не имеет уникального ключа для честного join.

## Changed Files

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- `tests/test_direction_inside_frozen_movement_regime.py`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
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

- focused tests: `23 passed`;
- canonical CLI: exit `0`, stdout `{"verdict": "ABORT_CONTRACT_FAIL"}`;
- full tests: `1224 passed, 30 warnings`;
- `graphify update .`: completed.

Artifact hashes:

- `freeze_report_sha256 = 9f3133cc1994428d28245c2a7cbb4d34d006633c93adddff9265e22cd07f6668`
- `freeze_scores_sha256 = 5d55be1e950c83dcda88f02050046f8b372185a1f162d0f695579935f9737af8`

## Results

Structured artifact: `ML/reports/direction_inside_frozen_movement_regime.json`.

Main result:

- `verdict = ABORT_CONTRACT_FAIL`
- `contract.status = ABORT_CONTRACT_FAIL`
- reasons:
  - `scores.duplicate_split_time`
  - `splits.train.duplicate_time`
  - `splits.validation.duplicate_time`
  - `splits.low_n_disclosure.duplicate_time`
  - `splits.val_select.duplicate_time`
  - `splits.val_eval.duplicate_time`
- `search_budget.direction_baselines_trained = 0`

Rows artifact: `ML/reports/direction_inside_frozen_movement_regime_rows.csv`.

Rows artifact is empty on contract fail, with schema:

```text
split,time,target_direction_3,target_is_tie_3,target_up_3,target_dn_3
```

## Conclusions

Direction-inside-mask experiment cannot be interpreted yet. The blocker is not weak direction quality; the blocker is that the frozen movement score export cannot be joined back to split rows by the planned unique key `split + time`.

The correct outcome is `ABORT_CONTRACT_FAIL`. No direction winner was selected, no robustness check was run, and no trading conclusion is allowed.

Invalidated assumption:

- `split + time` is not a unique row key for the current frozen score export.

## Limitations / Open Questions

- No direction baseline metrics exist for the canonical run.
- No block stability, class-balance verdict, or confidence interval can be interpreted.
- The frozen movement filter export needs a stable unique row key before this direction plan can be retried.
- Do not widen the movement mask, change `top_fraction`, or use direction outcome to repair the join.

Forbidden interpretations:

- not PnL;
- not PF;
- not a trading candidate;
- not a live rule;
- not permission to open `locked_test`.

## Split Disclosure

Split roles:

- `train`: contract checked only; not used because join contract failed;
- `val_select`: intended direction rule selection split, not reached;
- `val_eval`: intended check-only split, not reached;
- `low_n_disclosure`: disclosure-only, not used for selection;
- `locked_test`: `not_opened`.

Sample size after valid join and tie removal is not available because join contract failed before masked dataset construction.

## Next Step

Create a narrow repair plan for the frozen movement export contract:

- add a stable unique row identifier to the frozen score export and source split rows;
- regenerate frozen score artifacts without changing the frozen movement rule;
- rerun this direction-inside-mask plan only after the join contract passes.

Until then, close the current direction branch as contract-failed.

## Related Materials

- `docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
