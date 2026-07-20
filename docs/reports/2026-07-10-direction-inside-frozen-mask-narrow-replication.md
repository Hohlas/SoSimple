# Direction Inside Frozen Mask Narrow Replication

> **Дата**: 2026-07-10
> **Статус**: Completed
> **Вердикт**: FAIL / REJECT_DIRECTION_REPLICATION
> **Цель**: Проверить seed-stability слабого direction-effect внутри frozen movement-mask на заранее зафиксированной матрице `nearest_k60 / extra_trees / entry_log_ratio`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`

## Context

Этап продолжает full-grid результат от 2026-07-09:
`nearest_k60 / H3 / entry_log_ratio / extra_trees` дал
`val_select_inside_mask balanced_accuracy = 0.570170` и
`val_eval_inside_mask balanced_accuracy = 0.529056`, но получил только
`DIRECTION_REPLICATION_REQUIRED`.

Это проверочный follow-up на тех же данных, split-ах и frozen movement-mask.
Это не независимое открытие, не независимая репликация и не trading candidate.

Frozen movement-mask не менялась:

```text
simple_combined / extra_trees_small / H3 / top_fraction=0.05
seeds = [42, 43, 44]
rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf
```

## What Was Done

Добавлен narrow replication mode в rich-features runner:

- fixed profile: `nearest_k60`;
- fixed model: `extra_trees`;
- fixed target family: `entry_log_ratio`;
- planned horizons: `H3`, `H6`, `H9`;
- training seeds: `41`, `42`, `43`, `44`, `45`;
- output prefix:
  `ML/reports/direction_inside_frozen_movement_regime_narrow_replication`.

Runner теперь делает target preflight для H9. Если target columns отсутствуют,
H9 получает `SKIPPED_MISSING_TARGET_COLUMNS` и не считается провалом качества
модели.

Direction-модель обучалась на полном `train`. Frozen-mask применялась только
после fit для оценочных срезов.

## Changed Files

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/tests/tests.md`
- `docs/superpowers/roadmap.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
./.venv/bin/python -m pytest tests/ -q
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --replication-seeds 41 \
  --horizons 3 \
  --threads 24 \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime_narrow_replication_smoke \
  --no-resume
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --no-resume
```

Результаты:

- focused tests: `44 passed`;
- full tests: `1272 passed`;
- smoke artifact: `contract_status=PASS`, `progress=1/1`,
  `target_preflight=PASS`, `executed_search_budget=1`;
- full artifact: `contract_status=PASS`, `progress=10/10`, `failed_runs=0`.

Тесты выдают известные warnings на малых синтетических выборках и в старых
тестах проекта; отказов нет.

## Results

Structured artifacts:

- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_rows.csv`

Target preflight:

| Horizon | Status |
|---|---|
| H3 | `PASS` |
| H6 | `PASS` |
| H9 | `SKIPPED_MISSING_TARGET_COLUMNS` |

Multiple Testing Context:

| Field | Value |
|---|---:|
| Prior discovery search budget | 240 |
| Replication planned budget | 15 |
| Replication executed budget | 10 |
| Cumulative disclosed budget | 250 |

H3 seed table:

| Seed | val_select inside-mask BA | val_eval inside-mask BA | Gates |
|---:|---:|---:|---|
| 41 | 0.497336 | 0.499080 | PASS / PASS |
| 42 | 0.570170 | 0.529056 | PASS / PASS |
| 43 | 0.447807 | 0.522942 | PASS / PASS |
| 44 | 0.488184 | 0.475056 | PASS / PASS |
| 45 | 0.528344 | 0.480954 | PASS / PASS |

H3 aggregate:

- median `val_eval_inside_mask balanced_accuracy = 0.499080`;
- seeds with `val_eval_inside_mask >= 0.52`: `2/5`;
- seeds where `val_select` and `val_eval` are both above `0.50`: `1/5`;
- sample-size gates pass for all H3 seeds.

H6 seed table:

| Seed | val_select inside-mask BA | val_eval inside-mask BA | Gates |
|---:|---:|---:|---|
| 41 | 0.491391 | 0.503249 | PASS / PASS |
| 42 | 0.517381 | 0.528590 | PASS / PASS |
| 43 | 0.566764 | 0.501624 | PASS / PASS |
| 44 | 0.524854 | 0.552144 | PASS / PASS |
| 45 | 0.505361 | 0.556855 | PASS / PASS |

H6 aggregate:

- median `val_eval_inside_mask balanced_accuracy = 0.528590`;
- seeds with `val_eval_inside_mask >= 0.50`: `5/5`;
- H6 is secondary robustness only and cannot replace failed H3.

H9 table:

| Horizon | Status | Reason |
|---|---|---|
| H9 | `SKIPPED_MISSING_TARGET_COLUMNS` | Required target columns were absent in the real splits. |

Year diagnostics are report-only and do not affect verdict:

| Year | n | Accuracy | Balanced accuracy | Status |
|---:|---:|---:|---:|---|
| 2021 | 860 | 0.502326 | 0.500826 | PASS |
| 2022 | 1780 | 0.530337 | 0.526866 | PASS |
| 2023 | 690 | 0.505797 | 0.495048 | PASS |
| 2025 | 3330 | 0.512913 | 0.515193 | PASS |

Block diagnostics show instability inside runs. Example H3 seed 41 on
`val_eval`:

| Block | n | Accuracy | Balanced accuracy |
|---:|---:|---:|---:|
| 1 | 84 | 0.547619 | 0.531624 |
| 2 | 83 | 0.578313 | 0.565851 |
| 3 | 83 | 0.493976 | 0.495354 |
| 4 | 83 | 0.373494 | 0.401300 |

Validation Split Disclosure:

- `train`: used for fit on all active direction rows, not only frozen-selected
  rows;
- `val_select`: seed-stability comparison slice, not used to tune after the
  run;
- `val_eval`: confirmation slice for pre-registered rules;
- `low_n_disclosure`: not used for verdict or selection;
- `locked_test`: not opened.

## Conclusions

Verdict from pre-registered rules:

```text
REJECT_DIRECTION_REPLICATION
```

Reason:

- H3 median `val_eval_inside_mask balanced_accuracy = 0.499080`, below the
  reject threshold `0.515`;
- only `2/5` H3 seeds reached `val_eval_inside_mask >= 0.52`;
- only `1/5` H3 seeds had the same positive improvement sign on both
  `val_select` and `val_eval`;
- H6 was stronger, but H6 was secondary robustness and cannot replace H3
  after the result is known;
- H9 was skipped by preflight and gives no positive evidence.

Forbidden interpretations:

- no PnL/PF conclusion;
- no BUY/SELL trading conclusion;
- no spread, stop-loss or take-profit conclusion;
- no live or production claim;
- no reason to open `locked_test`;
- no reason to widen direction search around this family.

## Limitations / Open Questions

- This was still the same data, same split family and same frozen mask as the
  prior exploratory result, so it was not an independent replication.
- H9 target labels are absent in current real splits; H9 was skipped, not
  failed.
- Time diagnostics are descriptive only and are not a verdict gate.
- The H6 secondary result is interesting but cannot be promoted without a new
  pre-registered H6-first plan. Such a plan would still be research-only and
  would need a new rationale, not post-hoc reuse of this result.

## Next Step

Remove direction-inside-frozen-mask as a near-term branch. The next honest
research branch is execution-aware `fractal0_price` mechanics:

- exact `decision_time`;
- exact entry eligibility around `fractal0_price`;
- first executable price after feature availability;
- oracle-preflight for the mechanics;
- targets measured from actual executable entry;
- no `locked_test` until a frozen rule exists.

## Related Materials

- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
